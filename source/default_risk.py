"""Project default and the Facility: what annuitising the premium really risks.

Standalone companion to `cover.py`, written so it can be absorbed later. It
answers two questions the draft currently waves through:

1. **Annuitisation risk.** The premium is quoted as a level annuity
   ``psi = Theta / A(n, rho)`` at the Facility's rate rho, not at the project's
   cost of capital r. That is fair only if every window runs to maturity. If
   the project fails at year tau for reasons the cover does not price, the
   Facility has collected tau premiums and is left holding whatever deficit
   the experience account carries at tau.

2. **Credit risk on the liquidity leg.** An advance is a loan to a project
   that can fail for other reasons. How much of the gross liquidity is really
   Facility money at risk, once (a) drawings met out of the project's own
   escrow and (b) premiums already collected are netted off?

THE ONE IDENTITY THAT MAKES THIS TRACTABLE
    Default does not add a loss on top of the terminal one -- it *replaces*
    it. A project that fails at tau extinguishes the cover: the Facility keeps
    the premiums it has, writes off the deficit it has, and owes nothing at
    maturity. So its PV at close, for a window stopped at tau, is

        Pi(w, tau) = psi * A(tau, rho)  -  L(w, tau),

        L(w, tau)  = sum_{k<=tau} (1+rho)^-k (draw_facility_k - repaid_k),

    the PV of the Facility's net lending up to tau. With the account carried at
    rho, L(w, tau) = (1+rho)^-tau max(-B_tau, 0) = max(-V_tau, 0), where V_tau is
    the net cover balance of the same window *truncated* at tau. At tau = n it
    is the paper's loss. So E[L(., tau)] = Theta_tau is exactly "the ultimate
    net loss over a shorter window", and both questions above reduce to how
    Theta_tau compares with psi * A(tau, rho).

THE BOUND
    With a default time independent of the X path, the break-even premium is

        psi*(h) = sum_tau f_tau Theta_tau / sum_tau f_tau A_tau
                = sum_tau omega_tau Psi_tau,   omega_tau ∝ f_tau A_tau,

    a weighted average of the truncated-tenor premiums Psi_tau = Theta_tau /
    A_tau, with weights summing to one. Hence for ANY default distribution

        min_tau Psi_tau  <=  psi*  <=  max_tau Psi_tau,

    and the shorter-tenor curve the paper already estimates bounds the cost of
    annuitising at rho. Wrong-way default (hazard higher when X is down)
    breaks the independence and is handled by simulation-free reweighting in
    `fair_premium` with a per-window, per-year hazard matrix.

Run as a script for the full analysis on the 1985 pool:

    .venv/Scripts/python.exe source/default_risk.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cover  # noqa: E402


# ---------------------------------------------------------------------------
# the book, vectorised over windows
# ---------------------------------------------------------------------------

def flow_matrix(wp, flow="R"):
    """Pivot a window panel to a (windows x n) matrix of flows.

    Only full windows are kept (every window from `cover.window_panel` is
    full). Returns the KEY frame, one row per window, and the matrix.
    """
    n = int(wp["k"].max())
    wide = wp.pivot_table(index=cover.KEY, columns="k", values=flow, aggfunc="first")
    wide = wide.dropna()
    wide = wide[list(range(1, n + 1))]
    return wide.index.to_frame(index=False), wide.to_numpy(dtype=float)


def run_book(F, rho, c_neg=None, c_pos=None):
    """Run the experience account for every window at once.

    The account accrues at ``c_neg`` while in deficit (the rate the Facility
    charges on its advances) and at ``c_pos`` while in surplus (what the
    project's escrow earns). Both default to rho, which reproduces `cover`.

    Each year: accrue, then the year's flow lands. A drawing is met first out
    of a positive balance (the project's own escrow) and only the excess is
    Facility money; a surplus first repays an outstanding deficit and only the
    excess is escrowed.

    Returns a dict of (W x n) arrays:

    ``B``        balance at year end
    ``D``        Facility deficit at year end, ``max(-B, 0)``, accreted
    ``draw``     gross drawing, ``max(-flow, 0)``
    ``own``      part of the drawing met out of the project's escrow
    ``fac``      part met with Facility money
    ``rep``      surplus applied to the Facility's deficit
    ``L``        PV at close of the Facility's net lending up to and including
                 year k: the loss if the cover stops at k (see module doc)
    ``gross``    a naive lender's exposure: every drawing funded as a loan,
                 nothing netted against escrow, accreted at c_neg

    Examples
    --------
    >>> F = np.array([[-0.2, 0.1, 0.3], [0.2, -0.1, -0.3]])
    >>> b = run_book(F, rho=0.0)
    >>> b["own"][1].tolist(), b["fac"][1].round(2).tolist()
    ([0.0, 0.1, 0.1], [0.0, 0.0, 0.2])
    >>> b["L"].round(2).tolist()                 # window 1 repaid, window 2 short
    [[0.2, 0.1, 0.0], [0.0, 0.0, 0.2]]
    """
    c_neg = rho if c_neg is None else c_neg
    c_pos = rho if c_pos is None else c_pos
    W, n = F.shape
    out = {key: np.zeros((W, n)) for key in ("B", "D", "draw", "own", "fac", "rep", "L", "gross")}
    B = np.zeros(W)
    G = np.zeros(W)
    L = np.zeros(W)
    for j in range(n):
        Bo = np.where(B < 0, B * (1 + c_neg), B * (1 + c_pos))
        f = F[:, j]
        d = np.maximum(-f, 0.0)
        own = np.minimum(d, np.maximum(Bo, 0.0))
        fac = d - own
        s = np.maximum(f, 0.0)
        rep = np.minimum(s, np.maximum(-Bo, 0.0))
        B = Bo + f
        G = G * (1 + c_neg) + d
        L = L + (1 + rho) ** -(j + 1) * (fac - rep)
        for key, val in (("B", B), ("D", np.maximum(-B, 0.0)), ("draw", d), ("own", own),
                         ("fac", fac), ("rep", rep), ("L", L), ("gross", G)):
            out[key][:, j] = val
    return out


# ---------------------------------------------------------------------------
# default timing
# ---------------------------------------------------------------------------

def stop_weights(H):
    """Probability that the cover stops at the end of year tau, tau = 1..n.

    ``H`` is a hazard: a scalar, or a (W x n) matrix of per-window, per-year
    default probabilities (year k's hazard applying after year k's payment).
    A project alive at the end of year n-1 reaches maturity, so the final
    column carries the survivors as well as any year-n default: the two are
    the same event for the Facility.

    Returns a (W x n) matrix whose rows sum to one.

    >>> stop_weights(np.full((1, 3), 0.1)).round(3).tolist()
    [[0.1, 0.09, 0.81]]
    """
    H = np.asarray(H, dtype=float)
    alive_before = np.cumprod(np.hstack([np.ones((H.shape[0], 1)), 1 - H[:, :-1]]), axis=1)
    f = alive_before * H
    f[:, -1] = alive_before[:, -1]
    return f


def fair_premium(L, n, rho, H=0.0):
    """Break-even level premium, per unit of debt service, under default.

    Solves ``E[psi * A(tau, rho) - L(w, tau)] = 0`` over windows and stop
    times, i.e. ``psi* = E[L_tau] / E[A_tau]``. With ``H = 0`` it is the
    paper's Psi = Theta / A(n, rho).

    The premium for year tau is taken as paid when the project is still alive
    at year tau's payment date -- it pays the lender that year, with the
    Facility's help, and the Facility alongside.
    """
    W = L.shape[0]
    Hm = np.broadcast_to(np.asarray(H, dtype=float), (W, n)) if np.ndim(H) < 2 else H
    f = stop_weights(Hm)
    A = np.array([cover.annuity(t, rho) for t in range(1, n + 1)])
    return float((f * L).sum() / (f * A).sum())


def implied_rate(theta, psi, n):
    """The annuitisation rate d at which ``theta / A(n, d) = psi``.

    The rate the Facility is *effectively* charging on the deferred premium
    once default is priced in. Compare with rho (what it uses) and with r (what
    the project would pay to finance theta up front).
    """
    if psi <= theta / n:
        return 0.0
    return float(brentq(lambda d: theta / cover.annuity(n, d) - psi, 1e-9, 5.0))


def truncated_curve(L, rho):
    """Theta_tau and Psi_tau on the same windows, stopped at tau = 1..n."""
    n = L.shape[1]
    A = np.array([cover.annuity(t, rho) for t in range(1, n + 1)])
    theta = L.mean(axis=0)
    return pd.DataFrame({"tau": np.arange(1, n + 1), "A": A, "theta": theta,
                         "psi": theta / A, "p_short": (L > 1e-12).mean(axis=0)})


def stressed_hazard(stress, h_bar, m):
    """Two-state wrong-way hazard with a fixed pool-average hazard.

    Default is ``m`` times as likely in a stressed window-year (``stress`` is a
    boolean (W x n) matrix: R < 0, say, or the account in deficit) as in an
    unstressed one, and the base level is chosen so that the hazard averaged
    over every window-year in the pool is still ``h_bar``. So m moves *when*
    projects fail, not how many do. ``m = inf`` puts every default in a
    stressed year.
    """
    p = stress.mean()
    if np.isinf(m):
        return np.where(stress, min(h_bar / p, 1.0), 0.0)
    h0 = h_bar / (1 - p + m * p)
    return np.where(stress, np.minimum(m * h0, 1.0), h0)


def lapse_hazard(B, x, p):
    """Voluntary exit: a project leaves the cover (refinances, prepays, stops
    paying) with probability ``p`` a year once its escrow stands at ``x`` years
    of debt service or more. It takes its escrow with it and owes nothing, so
    the Facility loses only the premiums the good windows would have paid --
    which is what was funding the bad ones. Feed to `fair_premium` as ``H``.
    """
    return np.where(B >= x, p, 0.0)


def worst_timing_premium(L, n, rho, q):
    """Break-even premium when default timing is chosen by an adversary.

    Each project fails before maturity with probability ``q``, independently
    of its X path, but *when* it fails is the year of its window that costs
    the Facility most: ``argmax_tau (L_tau - psi * A_tau)``. No hazard law,
    however correlated with X, can do worse for a given incidence q, so this
    is a hard upper bound on the premium.
    """
    A = np.array([cover.annuity(t, rho) for t in range(1, n)])
    Ln = L[:, -1]
    An = cover.annuity(n, rho)

    def gap(psi):
        worst = (L[:, :-1] - psi * A).max(axis=1)
        return float(((1 - q) * (psi * An - Ln) - q * worst).mean())

    return float(brentq(gap, 0.0, 1.0))


# ---------------------------------------------------------------------------
# the analysis
# ---------------------------------------------------------------------------

def stopped_curve(wp, rho, flow="R"):
    """The pool's loss and premium if every window's cover stopped at tau.

    For each tau = 1..n, ``theta`` is the average over the windows of
    ``L(w, tau) = max(-V_{w,tau}, 0)``, the net cover balance of the window
    truncated at tau -- the experience account's deficit at tau, discounted
    to close. ``psi`` is ``theta / A(tau, rho)``: the level premium that would
    break even if every project in the pool stopped paying, and the Facility
    stopped covering, at the end of year tau. At tau = n these are the
    draft's Theta and Psi.

    Examples
    --------
    >>> wp = cover.window_panel(cover.load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> c = stopped_curve(wp, rho=0.05)
    >>> round(float(c.theta.iloc[-1]), 4), round(float(c.psi.iloc[-1]), 4)   # the draft's Theta, Psi
    (0.718, 0.0692)
    """
    _, F = flow_matrix(wp, flow)
    return truncated_curve(run_book(F, rho)["L"], rho)


def price_with_default(wp, n, rho, r, hazards=(0.01, 0.02, 0.03, 0.05), flow="R"):
    """The level premium once projects can fail for reasons the cover does not price.

    Each project fails with annual probability h, independently of its X
    path. A failure in year tau ends both the premium stream and the cover:
    the Facility keeps the tau premiums it has collected and writes off the
    experience account's deficit at tau, if there is one. The premium that
    breaks even over the pool is

        psi*(h) = sum_tau f_tau Theta_tau / sum_tau f_tau A_tau
                = sum_tau omega_tau Psi_tau,      omega_tau ∝ f_tau A_tau,

    where f_tau is the probability that the cover stops at tau (tau = n
    includes survival). See `stopped_curve` for Theta_tau, Psi_tau.

    Returns
    -------
    DataFrame, one row per hazard, with ``h = 0`` (the draft's Psi) first:

    ``p_fail``    probability a project fails before maturity
    ``omega_n``   weight on the maturity premium Psi in the average
    ``psi``       psi*(h), share of debt service
    ``uplift``    ``psi / Psi - 1``
    ``bound``     upper bound on uplift from the curve alone,
                  ``(1 - omega_n) * (max Psi_tau / Psi - 1)``
    ``delta_r``   margin-equivalent spread on a loan at r

    Plus, as attributes: ``out.attrs["psi_min"]``, ``["psi_max"]``, the range of
    psi* over every possible law for the failure year.

    Examples
    --------
    >>> wp = cover.window_panel(cover.load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> t = price_with_default(wp, 15, 0.05, 0.10, hazards=(0.03,))
    >>> t[["h", "psi"]].round(4).to_dict("list")
    {'h': [0.0, 0.03], 'psi': [0.0692, 0.0706]}
    """
    curve = stopped_curve(wp, rho, flow)
    A, theta = curve.A.to_numpy(), curve.theta.to_numpy()
    psi_n = theta[-1] / A[-1]
    rows = []
    for h in (0.0,) + tuple(hazards):
        f = stop_weights(np.full((1, n), h))[0]
        omega_n = f[-1] * A[-1] / (f * A).sum()
        psi = float((f * theta).sum() / (f * A).sum())
        rows.append({"h": h, "p_fail": 1 - (1 - h) ** (n - 1), "omega_n": omega_n,
                     "psi": psi, "uplift": psi / psi_n - 1 if psi_n > 0 else 0.0,
                     "bound": (1 - omega_n) * (curve.psi.max() / psi_n - 1) if psi_n > 0 else 0.0,
                     "delta_r": cover.equivalent_rate(psi, r, n) - r})
    out = pd.DataFrame(rows)
    out.attrs.update(psi_min=float(curve.psi.min()), psi_max=float(curve.psi.max()),
                     tau_max=int(curve.tau[curve.psi.idxmax()]))
    return out


def describe_default(t):
    """A few lines summarising `price_with_default`, for printing in a notebook."""
    psi_n = t.psi.iloc[0]
    lines = [f"Psi at maturity = {psi_n:.2%};  any law for the failure year: "
             f"{t.attrs['psi_min']:.2%} <= psi* <= {t.attrs['psi_max']:.2%} "
             f"(max at tau = {t.attrs['tau_max']})"]
    for _, row in t.iloc[1:].iterrows():
        lines.append(f"h = {row.h:.0%}: P(fail before maturity) = {row.p_fail:.0%};  "
                     f"psi* = {row.psi:.2%} ({row.uplift:+.1%}, bound {row.bound:+.1%});  "
                     f"delta_r = {1e4 * row.delta_r:.0f}bp")
    return "\n".join(lines)


def analysis(n=15, rho=0.05, r=0.10, start_year=1985, hazards=(0.01, 0.02, 0.03, 0.05, 0.08),
             multipliers=(1, 3, 10, np.inf), verbose=True):
    """Everything in one pass on the pool; returns the tables as a dict."""
    df = cover.load_panel(drop=("LSO",))
    wp = cover.window_panel(df, n=n, start_year=start_year)
    keys, F = flow_matrix(wp)
    book = run_book(F, rho)
    L = book["L"]

    # the identity that everything rests on
    bal = cover.window_balance(wp, rho).merge(keys, on=cover.KEY)
    bal = keys.merge(bal, on=cover.KEY, how="left")
    assert np.allclose(L[:, -1], -bal["loss"].to_numpy(), atol=1e-12)

    A_n = cover.annuity(n, rho)
    theta = float(L[:, -1].mean())
    psi = theta / A_n
    out = {"W": len(keys), "theta": theta, "psi": psi,
           # the raw objects, for charts and follow-up work
           "keys": keys, "F": F, "book": book}

    # ---- 1. annuitisation risk: truncated-tenor curve and independent default
    curve = truncated_curve(L, rho)
    curve["gap"] = curve.theta - psi * curve.A      # Facility shortfall if stopped at tau
    out["curve"] = curve

    rows = []
    for h in hazards:
        p_star = fair_premium(L, n, rho, h)
        rows.append({"h": h, "P(fail<n)": 1 - (1 - h) ** (n - 1),
                     "psi*": p_star, "uplift": p_star / psi - 1,
                     "d_eff": implied_rate(theta, p_star, n),
                     "lender_rate": (1 + rho) / (1 - h) - 1})
    indep = pd.DataFrame(rows)
    out["independent"] = indep

    # ---- 2. wrong-way default, three definitions of the stressed state, plus
    #         the adversarial bound that no hazard law can exceed
    k = np.arange(1, n + 1)
    prem_acc = psi * ((1 + rho) ** k - 1) / rho          # premiums collected, FV at k
    states = {"R<0": F < 0,
              "deficit": book["D"] > 0,
              "deficit>premiums": book["D"] > prem_acc}
    rows = []
    for h in hazards:
        for name, st in states.items():
            for m in multipliers:
                p_star = fair_premium(L, n, rho, stressed_hazard(st, h, m))
                rows.append({"h": h, "state": name, "m": m, "psi*": p_star,
                             "uplift": p_star / psi - 1, "d_eff": implied_rate(theta, p_star, n)})
        q = 1 - (1 - h) ** (n - 1)
        p_star = worst_timing_premium(L, n, rho, q)
        rows.append({"h": h, "state": "adversarial", "m": np.nan, "psi*": p_star,
                     "uplift": p_star / psi - 1, "d_eff": implied_rate(theta, p_star, n)})
    wrong = pd.DataFrame(rows)
    out["wrong_way"] = wrong

    # ---- 3. the liquidity leg: whose money, and how much is already paid for
    drawing = book["draw"] > 0
    D = book["D"]
    net = np.maximum(D - prem_acc, 0.0)
    lent_this_year = book["fac"] > 0
    ex = {
        "drawing window-years": drawing.mean(),
        "  met wholly from escrow": (drawing & (book["fac"] == 0)).sum() / drawing.sum(),
        "  gross drawn $ met from escrow": book["own"].sum() / book["draw"].sum(),
        "window-years with Facility deficit": (D > 0).mean(),
        "  of which deficit <= premiums collected": ((D > 0) & (D <= prem_acc)).sum() / (D > 0).sum(),
        "Facility lends new money this year": lent_this_year.mean(),
        "  and deficit then exceeds premiums": (lent_this_year & (D > prem_acc)).sum() / lent_this_year.sum(),
        "mean naive exposure (all draws as loans)": book["gross"].mean(),
        "mean Facility deficit D": D.mean(),
        "mean deficit net of premiums": net.mean(),
        "  as share of naive exposure": net.mean() / book["gross"].mean(),
        "  as share of deficit D": net.mean() / D.mean(),
    }
    short = L[:, -1] > 1e-12
    ex.update({
        "deficit window-years in windows ending short": (D > 0)[short].sum() / (D > 0).sum(),
        "deficit $-years in windows ending short": D[short].sum() / D.sum(),
        "Facility cash advanced in windows ending short": book["fac"][short].sum() / book["fac"].sum(),
        "Facility cash repaid inside the window": book["rep"].sum() / book["fac"].sum(),
    })
    out["exposure"] = ex
    prof = pd.DataFrame({"k": k, "P(draw)": drawing.mean(0), "P(D>0)": (D > 0).mean(0),
                         "P(D>prem)": (D > prem_acc).mean(0),
                         "naive": book["gross"].mean(0), "D": D.mean(0),
                         "prem": prem_acc, "net": net.mean(0)})
    out["exposure_by_year"] = prof

    # A naive lender's required spread is h * LGD on its exposure. Scale it by
    # the share of that exposure the Facility actually has net of what it has
    # been paid: an *upper-bound* heuristic, since it ignores that default also
    # cancels the terminal loss (which section 1 does price).
    out["spread_heuristic"] = pd.DataFrame(
        [{"h": h, "naive spread": h / (1 - h),
          "facility spread": h / (1 - h) * net.mean() / book["gross"].mean()} for h in hazards])

    # ---- 4. a spread on advances instead of a higher premium
    rows = []
    for h in hazards:
        def gap(c):
            Lc = run_book(F, rho, c_neg=c)["L"]
            f = stop_weights(np.full(F.shape, h))
            A = np.array([cover.annuity(t, rho) for t in k])
            return float((f * (psi * A - Lc)).sum())
        lo, hi = gap(rho), gap(1.0)
        c_star = brentq(gap, rho, 1.0) if lo < 0 < hi else (rho if lo >= 0 else np.nan)
        rows.append({"h": h, "c_neg*": c_star, "gap_at_rho": lo / len(F), "gap_at_100%": hi / len(F)})
    out["advance_rate"] = pd.DataFrame(rows)

    # ---- 5. escrow earning less than rho (remaining-problem check)
    rows = []
    for c_pos in (rho, 0.04, 0.03, 0.02, 0.0):
        Lc = run_book(F, rho, c_pos=c_pos)["L"]
        rows.append({"c_pos": c_pos, "theta": Lc[:, -1].mean(), "psi": Lc[:, -1].mean() / A_n})
    out["escrow_rate"] = pd.DataFrame(rows)

    # ---- 6. robustness: truncated curve vs independent tenor-tau samples
    rows = []
    for t in (3, 5, 8, 10, 12, 15):
        b = cover.window_balance(cover.window_panel(df, n=t, start_year=start_year), rho)
        rows.append({"tau": t, "psi_truncated": curve.psi[t - 1],
                     "psi_all_tau_windows": -b.loss.mean() / cover.annuity(t, rho),
                     "N_tau": len(b)})
    out["tenor_check"] = pd.DataFrame(rows)

    # ---- 7. lapse: the good windows walking away
    rows = []
    for x in (0.5, 1.0, 2.0):
        for p in (0.2, 1.0):
            p_star = fair_premium(L, n, rho, lapse_hazard(book["B"], x, p))
            rows.append({"escrow >=": x, "p/yr": p, "psi*": p_star, "uplift": p_star / psi - 1,
                         "delta_r": cover.equivalent_rate(p_star, r, n) - r})
    out["lapse"] = pd.DataFrame(rows)

    # ---- 8. what annuitising at r would charge
    out["psi_at_r"] = theta / cover.annuity(n, r)
    out["dr_at_rho"] = cover.equivalent_rate(psi, r, n) - r
    out["dr_at_r"] = cover.equivalent_rate(out["psi_at_r"], r, n) - r
    out["dr_star"] = {h: cover.equivalent_rate(p, r, n) - r
                      for h, p in zip(indep.h, indep["psi*"])}

    if verbose:
        _report(out, n, rho, r)
    return out


def _report(o, n, rho, r):
    pct = lambda v: f"{100 * v:.2f}%"
    print(f"POOL: {o['W']} windows, n={n}, rho={rho:.0%}, r={r:.0%}")
    print(f"Theta = {o['theta']:.4f} yrs;  Psi = {pct(o['psi'])};  "
          f"annuitised at r instead: {pct(o['psi_at_r'])}")
    print(f"Delta r: {1e4 * o['dr_at_rho']:.0f}bp annuitised at rho, "
          f"{1e4 * o['dr_at_r']:.0f}bp at r\n")

    print("1. Same windows stopped at tau (Theta_tau, Psi_tau = Theta_tau/A_tau, "
          "gap = Theta_tau - Psi*A_tau):")
    print(o["curve"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    c = o["curve"]
    print(f"   bound for ANY independent default law: {pct(c.psi.min())} <= psi* <= {pct(c.psi.max())}"
          f";  max gap = {c.gap.max():.3f} yrs at tau={int(c.tau[c.gap.idxmax()])}\n")

    print("   Independent default, annual hazard h:")
    print(o["independent"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("   Delta r with psi*: " + ", ".join(f"h={h:.0%}: {1e4 * v:.0f}bp"
                                             for h, v in o["dr_star"].items()) + "\n")

    print("2. Wrong-way default (m = hazard ratio stressed vs unstressed years; "
          "pool-average hazard fixed). Premium uplift / implied annuitisation rate:")
    w = o["wrong_way"].copy()
    w["col"] = w.state + np.where(w.m.isna(), "", " m=" + w.m.astype(str))
    for v, fmt in (("uplift", lambda x: f"{100 * x:+.1f}%"), ("d_eff", lambda x: f"{100 * x:.2f}%")):
        print(w.pivot(index="h", columns="col", values=v)[w.col.unique()].T
              .to_string(float_format=fmt))
    print()

    print("3. Liquidity leg exposure (all window-years):")
    for key, v in o["exposure"].items():
        print(f"   {key:45s} {v:8.3f}")
    print(o["exposure_by_year"].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(o["spread_heuristic"].to_string(index=False, float_format=lambda v: f"{100 * v:.2f}%"))
    print()
    print("4. Spread on advances (carry on deficit c_neg) that breaks even at the h=0 premium:")
    print(o["advance_rate"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print()
    print("5. Escrow earning c_pos < rho:")
    print(o["escrow_rate"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print()
    print("6. Truncated-window Psi_tau vs all tenor-tau windows:")
    print(o["tenor_check"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print()
    print("7. Lapse: exit with prob p/yr once escrow >= x yrs of debt service:")
    print(o["lapse"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=False)
    analysis()
