"""Cover-account arithmetic for the emergency liquidity facility.

Plain functions over pandas frames, in four steps:

    >>> df  = load_panel()                       # country-year panel
    >>> wp  = window_panel(df, n=15)             # window-year panel, one row per fixing
    >>> bal = window_balance(wp, rho=0.05)         # one row per window: V, loss, drawings
    >>> p   = price(bal, n=15, rho=0.05)           # the pool's price, as a dict

The object in the middle, ``wp``, is a tidy long frame -- one row per (window,
year) -- and it is deliberately the centre of the design. Anything you want to
do to the cash flows is a column on it: a different index for the revenue, an
attachment point, a merged covariate, a dropped year. It is also a
regression-ready panel, so econometrics on the same windows needs no separate
pipeline.

Every example in this module is a doctest and is checked by
``source/test_cover.py``, so nothing here can drift away from what the code does.

THE QUANTITY
    The net cover balance

        V_w = sum_{k=1..n} R_{w,k} (1+rho)^-k,      R_{w,k} = X_k / X_0 - 1,

    is the terminal balance of the experience account in YEARS OF DEBT SERVICE
    (V_w = Lambda_w / delta_bar). It carries no annuity factor. Dividing by
    A_{n,rho} is what turns a loss into a *premium*, so that happens once, in
    `price`, and nowhere else.

THE WINDOW
    A window of tenor n spans n+1 consecutive observations of a country's
    series. The first is financial close: it sets the strike (R = 0 there by
    construction, because the debt is sized to close-year cash flow) and is NOT
    a fixing. The n that follow are the fixings, discounted at elapsed years
    k = 1..n. ``wp`` holds one row per fixing, with the close-year level in the
    ``base`` column. Windows are cut on positions in the country's non-missing
    series, so a gap in the data drops no fixing; it only pushes ``window_end``
    further from ``window_start``.

THE RATES
    Four distinct rates hide behind a single rho in the draft, and each enters
    in exactly one place here:

    rho
        The facility discount rate -- what the Facility values its own
        liability at, and annuitises its expected loss at.
        ``window_balance(wp, rho)``. Theta depends on rho alone.
    carry
        The rate on the experience account: charged on advances, earned on
        escrow. A design choice, not an observation, and named `carry` rather
        than `c` because the draft already spends c on the project's real unit
        cost. ``window_balance(wp, rho, carry=...)``; carry = rho collapses to
        the usual closed form. Raising it above rho tilts weight from the late
        flows to the early ones, and since the Facility's pattern is
        advance-early recover-late, that *raises* the expected loss: it is
        charging interest on advances the later surpluses may never repay. The
        lending-spread story -- carry > rho part-funding the insurance leg --
        is Facility income booked outside V, and needs the asymmetric ledger
        to model honestly.
    r
        The project's loan rate: sizes the principal D = A_{n,r} delta_bar,
        and converts the premium to a margin. ``price(..., r=...)``.
    r_C - r_f
        The cost of solvency capital. Not modelled: it is a loading on top of
        the pure premium returned here.

    Asymmetric carry -- one rate while the account is in deficit, another while
    it is in surplus -- is the one thing the closed form cannot express, since
    the balance then depends on its own sign. See `window_balance`.

THE CONTRACT
    What flows into the account each year is a column, so changing the contract
    changes no function here. `corridor` covers the common shapes: a deductible
    the project absorbs before the Facility advances, a threshold below which
    surpluses are not escrowed, or both at once.

No plotting, no notebook state: importable from a script or a notebook alike.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

DATA = Path(__file__).resolve().parents[1] / "data" / "wdi_africa_long.csv"

#: The columns that identify one window.
KEY = ["iso3", "country", "window_start", "window_end"]


# ---------------------------------------------------------------------------
# the data
# ---------------------------------------------------------------------------

def load_panel(path=DATA, drop=("LSO",)):
    """Read the country-year panel and add the indices the analysis uses.

    Parameters
    ----------
    path : str or Path
        The WDI extract. Defaults to ``data/wdi_africa_long.csv``.
    drop : tuple of str
        ISO3 codes to exclude. Lesotho is dropped by default: its CPI has
        uncorrected basket and base-year breaks in 1999, 2002 and 2009.

    Returns
    -------
    DataFrame
        The input columns plus:

        X
            ``cpi / exchange_rate``, the dollar unit-revenue index: the USD
            value of a fixed local basket, i.e. what a kWh of inflation-indexed
            local revenue is worth in dollars. NOT the real exchange rate -- it
            is deflated by domestic prices only.
        Q
            ``X / us_cpi``, the real exchange rate: X deflated a second time by
            the US price level.
        usd_per_lcu
            ``1 / exchange_rate``, the nominal rate the market quotes.
        dlnX
            Annual log change in X, for correlations and regressions.

    Examples
    --------
    >>> df = load_panel()
    >>> sorted(set(df.columns) - {"iso3", "country", "year"})
    ['Q', 'X', 'cpi', 'dlnX', 'exchange_rate', 'us_cpi', 'usd_per_lcu']
    >>> int(df.year.min()), int(len(df[df.iso3 == "NGA"]))
    (1985, 40)
    """
    df = pd.read_csv(path)
    df = df[~df["iso3"].isin(drop)].sort_values(["iso3", "year"]).reset_index(drop=True)
    df["usd_per_lcu"] = 1.0 / df["exchange_rate"]
    df["X"] = df["cpi"] / df["exchange_rate"]
    df["Q"] = df["X"] / df["us_cpi"]
    df["dlnX"] = df.groupby("iso3")["X"].transform(lambda s: np.log(s).diff())
    return df


# ---------------------------------------------------------------------------
# windows
# ---------------------------------------------------------------------------

def window_panel(df, n=15, col="X", start_year=None, mode="rolling"):
    """Build the window-year panel: one row per (window, fixing).

    Parameters
    ----------
    df : DataFrame
        A country-year panel, as returned by `load_panel`.
    n : int
        Tenor: the number of debt-service payments, and equally the number of
        fixings. A window therefore spans n+1 observations.
    col : str
        The series being priced: "X" for the dollar unit-revenue index, "Q" for
        the real exchange rate, "usd_per_lcu" for the nominal rate.
    start_year : int, optional
        Drop observations before this year outright, so that no window can see
        them. This is the sample control the draft uses.
    mode : {"rolling", "two_non_overlapping"}
        "rolling" opens a window at every available close year.
        "two_non_overlapping" takes at most two per country, the second opening
        at the first's maturity, since consecutive tenors share an endpoint.

    Returns
    -------
    DataFrame
        One row per fixing, with columns

        ==============  ==================================================
        iso3, country   who
        window_start    year of financial close
        window_end      year of maturity
        year, k         the fixing: calendar year, and elapsed year 1..n
        base            the level at close -- the strike
        level           the level at this fixing
        R               ``level / base - 1``, the cumulative return
        ==============  ==================================================

        The close-year row is deliberately absent: R = 0 there by construction
        and it is not a fixing. Its level is carried in ``base``.

    See Also
    --------
    window_balance : collapses this frame to one row per window.
    corridor : reshape the flows before pricing them.

    Examples
    --------
    >>> df = load_panel()
    >>> wp = window_panel(df[df.iso3 == "NGA"], n=15, start_year=1985)
    >>> len(wp), int(wp.window_start.nunique())
    (375, 25)
    >>> one = wp[wp.window_start == 1998]
    >>> one.k.tolist()[:3], one.year.tolist()[:3]
    ([1, 2, 3], [1999, 2000, 2001])
    >>> one.R.round(3).tolist()[:3]           # the naira's collapse, from close
    [-0.747, -0.754, -0.734]
    """
    frames = []
    for iso3, g in df.dropna(subset=[col]).groupby("iso3"):
        g = g.sort_values("year")
        if start_year is not None:
            g = g[g["year"] >= start_year]
        g = g.reset_index(drop=True)

        n_obs = n + 1                      # close, then n fixings
        if len(g) < n_obs:
            continue
        if mode == "rolling":
            starts = range(0, len(g) - n_obs + 1)
        elif mode == "two_non_overlapping":
            starts = list(range(0, len(g) - n_obs + 1, n))[:2]
        else:
            raise ValueError("mode must be 'rolling' or 'two_non_overlapping'")

        for i0 in starts:
            w = g.iloc[i0:i0 + n_obs]
            frames.append(pd.DataFrame({
                "iso3": iso3,
                "country": w["country"].iloc[0],
                "window_start": int(w["year"].iloc[0]),
                "window_end": int(w["year"].iloc[-1]),
                "year": w["year"].to_numpy()[1:],        # the close year is not a fixing
                "k": np.arange(1, n + 1),
                "base": float(w[col].iloc[0]),
                "level": w[col].to_numpy()[1:],
            }))

    if not frames:
        return pd.DataFrame(columns=KEY + ["year", "k", "base", "level", "R"])

    wp = pd.concat(frames, ignore_index=True)
    wp["R"] = wp["level"] / wp["base"] - 1.0
    return wp


# ---------------------------------------------------------------------------
# the contract: what actually flows into the account
# ---------------------------------------------------------------------------

def corridor(R, lower=0.0, upper=0.0):
    """Flow into the experience account when the cover has a corridor.

    The Facility advances only what a shortfall exceeds ``lower``, and the
    project escrows only what a surplus exceeds ``upper``. Between the two
    nothing moves in either direction: the project keeps its own small
    shortfalls and its own small gains.

    The two terms each handle one side and are zero on the other, so they
    simply add:

    - ``minimum(R + lower, 0)`` is the shortfall net of the deductible, or 0;
    - ``maximum(R - upper, 0)`` is the surplus net of the threshold, or 0.

    Parameters
    ----------
    R : array-like or Series
        Cumulative returns at the fixings, i.e. the ``R`` column of a window
        panel.
    lower : float
        Deductible: the project absorbs the first ``lower`` of any shortfall
        itself. ``lower=0.05`` is the attachment theta^a = 0.95 of
        ``moneyness_and_triggers_20260916.md``, written as a return rather
        than a level.
    upper : float
        Escrow threshold: surpluses smaller than this stay with the project
        instead of repaying earlier advances.

    Returns
    -------
    Same type as `R`
        The per-fixing flow, to be passed to ``window_balance(..., flow=...)``.

    Notes
    -----
    The two sides pull the premium in opposite directions. A deductible cuts
    it, as less is covered. A threshold on the escrow *raises* it, because the
    escrow is the recovery leg the instrument leans on -- the Facility advances
    early and recovers late -- so letting the project keep its early gains
    leaves more windows ending short.

    Examples
    --------
    >>> R = pd.Series([-0.20, -0.06, -0.03, 0.05, 0.20])
    >>> corridor(R, lower=0.05, upper=0.07).round(3).tolist()
    [-0.15, -0.01, 0.0, 0.0, 0.13]

    A 20-point shortfall draws 15, the project having absorbed 5; a 3-point one
    draws nothing at all; a 20-point surplus escrows 13. With both thresholds
    at zero -- the cover the paper prices -- the flow is R itself:

    >>> bool((corridor(R) == R).all())
    True

    Priced on Nigeria's 25 windows, the deductible is worth about six basis
    points of expected loss:

    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> wp["flow"] = corridor(wp.R, lower=0.05, upper=0.07)
    >>> round(price(window_balance(wp, rho=0.05), 15, 0.05)["theta"], 4)
    0.718
    >>> round(price(window_balance(wp, rho=0.05, flow="flow"), 15, 0.05)["theta"], 4)
    0.6616
    """
    return np.minimum(R + lower, 0.0) + np.maximum(R - upper, 0.0)


# ---------------------------------------------------------------------------
# pricing
# ---------------------------------------------------------------------------

def weight(k, n, rho, carry=None):
    """Present value at close of one unit of flow at elapsed year k.

    The flow sits in the experience account from year k to maturity, accruing
    at the carry rate carry, and the whole balance is valued at the Facility's rate
    rho: ``(1+carry)**(n-k) * (1+rho)**-n``. When carry = rho the two collapse to the
    familiar ``(1+rho)**-k``, which is why V has its simple form in the draft.

    Parameters
    ----------
    k : int or array-like
        Elapsed years, 1..n.
    n : int or array-like
        Tenor of the window each flow belongs to. May be one number, or one
        per row when pricing a panel of windows of different lengths.
    rho : float
        The Facility's valuation rate.
    carry : float, optional
        The carry on the experience account. Defaults to rho.

    Examples
    --------
    >>> np.round(weight([1, 2, 3], 3, rho=0.05), 4).tolist()
    [0.9524, 0.907, 0.8638]
    >>> np.round(weight([1, 2, 3], 3, rho=0.05, carry=0.05), 4).tolist()
    [0.9524, 0.907, 0.8638]

    A carry above the valuation rate shifts weight onto the early flows, which
    is why it raises the price of a book that advances early and recovers late:

    >>> np.round(weight([1, 2, 3], 3, rho=0.05, carry=0.08), 4).tolist()
    [1.0076, 0.9329, 0.8638]
    """
    k = np.asarray(k, dtype=float)
    n = np.asarray(n, dtype=float)       # may be one number, or one per row
    if carry is None or carry == rho:
        return (1.0 + rho) ** -k
    return (1.0 + carry) ** (n - k) * (1.0 + rho) ** -n


def cover_balance(levels, rho, carry=None):
    """V for a single stretch of series, in years of debt service.

    For arbitrary segments -- the shaded areas of the Algeria panel, say --
    where building a whole window panel would be beside the point.

    Parameters
    ----------
    levels : array-like
        The close-year level first, then one per fixing.
    rho, carry : float
        Valuation rate and carry; see `weight`.

    Examples
    --------
    A flat series costs nothing, whatever its level:

    >>> cover_balance([1.0] * 16, rho=0.05)
    0.0

    A permanent 10% shortfall costs a tenth of the annuity, about 1.04 years of
    debt service:

    >>> round(cover_balance([1.0] + [0.9] * 15, rho=0.05), 4)
    -1.038
    """
    v = np.asarray(levels, dtype=float)
    R = v[1:] / v[0] - 1.0
    n = R.size
    return float(R @ weight(np.arange(1, n + 1), n, rho, carry))


def window_balance(wp, rho, carry=None, flow="R"):
    """Collapse the window panel to one row per window: both legs of the cover.

    The risk leg and the liquidity leg come off the same rows, so how often the
    Facility *lends* and how often it *loses* cannot drift apart.

    Parameters
    ----------
    wp : DataFrame
        A window panel from `window_panel`.
    rho, carry : float
        Valuation rate and carry; see `weight`.
    flow : str
        The column paid into (or drawn out of) the account at each fixing.
        Defaults to ``"R"``, the cover the paper prices: the Facility meets the
        whole shortfall and banks the whole surplus. To price a different
        contract, add a column -- `corridor` builds the usual ones -- and name
        it here. ``R`` itself is untouched, so the frame still carries the raw
        returns for anything else.

    Returns
    -------
    DataFrame
        One row per window:

        ==============  ==================================================
        V               net cover balance at maturity, years of debt service
        loss            ``min(V, 0)``: the Facility absorbs every deficit in
                        full and takes none of the surplus
        n_draw_years    fixings at which the Facility advanced
        any_draw        did it ever
        worst_year      deepest single-year shortfall, as a fraction of one
                        debt-service payment (rate-free: an advance is a
                        ratio of two observations of the index)
        n_fixings       fixings in the window, normally n
        base            the level at close
        ==============  ==================================================

        The two liquidity columns follow ``flow``, so under a deductible a year
        the project absorbs itself is correctly not a drawing.

    Notes
    -----
    For asymmetric carry, replace the ``pv`` column below with a per-window
    loop over the ledger, ``bal = bal * (1 + rate_given_sign(bal)) + flow``,
    and take the final balance discounted at rho. Nothing else changes.

    Examples
    --------
    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> bal = window_balance(wp, rho=0.05)
    >>> len(bal), int((bal.V < 0).sum())            # 4 of the 25 windows end short
    (25, 4)
    >>> round(float(bal.V.min()), 3), round(float(bal.n_draw_years.mean()), 2)
    (-6.112, 3.24)

    A deductible cuts both the loss and the number of drawing years:

    >>> wp["flow"] = corridor(wp.R, lower=0.05)
    >>> net = window_balance(wp, rho=0.05, flow="flow")
    >>> round(float(-net.loss.mean()), 4), round(float(net.n_draw_years.mean()), 2)
    (0.6461, 3.04)
    """
    n = wp.groupby(KEY)["k"].transform("max")
    pv = wp[flow] * weight(wp["k"].to_numpy(), n.to_numpy(), rho, carry)

    bal = (wp.assign(pv=pv, flow=wp[flow])
             .groupby(KEY, as_index=False)
             .agg(V=("pv", "sum"),
                  n_fixings=("k", "size"),
                  n_draw_years=("flow", lambda s: int((s < 0).sum())),
                  worst_year=("flow", "min"),
                  base=("base", "first")))
    bal["loss"] = bal["V"].clip(upper=0.0)
    bal["any_draw"] = bal["n_draw_years"] > 0
    return bal


# ---------------------------------------------------------------------------
# the price -- the only place an annuity factor appears
# ---------------------------------------------------------------------------

def annuity(n, r):
    """A_{n,r} = sum_{k=1..n} (1+r)^-k, the present value of a unit annuity.

    Examples
    --------
    >>> round(annuity(15, 0.05), 4)
    10.3797
    >>> annuity(15, 0.0)
    15.0
    """
    return float(n) if r == 0 else float((1.0 - (1.0 + r) ** -int(n)) / r)


def equivalent_rate(psi, r, n):
    """The loan rate that carries the premium.

    Solves ``A(n, r) = A(n, r) / (1 + psi)``: annual debt service rises by
    exactly the premium. That is the right equivalence because the Facility
    takes no project credit risk on the premium stream -- if the project folds
    it stops receiving premium and stops being on risk.

    Parameters
    ----------
    psi : float
        The premium as a share of each debt-service payment. Already
        annuitised: passing theta, which is ``-bal.loss.mean()`` and is in
        years of debt service, would overstate the spread by a factor of A.
    r : float
        The project's loan rate.
    n : int
        Tenor.

    Returns
    -------
    float
        The rate itself. The margin add-on is that less ``r``.

    Examples
    --------
    Nigeria's 6.92% premium is 101bp on the margin of a 15-year amortising loan:

    >>> round(equivalent_rate(0.0692, r=0.05, n=15), 6)
    0.060069
    >>> round(equivalent_rate(0.0, r=0.05, n=15), 9)      # no premium, no spread
    0.05
    """
    target = annuity(n, r) / (1.0 + abs(float(psi)))
    return float(brentq(lambda r: annuity(n, r) - target, 1e-9, 5.0))


def price(bal, n, rho, r=None, delta_bar=1.0):
    """Price a pool of windows.

    Parameters
    ----------
    bal : DataFrame
        Window balances from `window_balance`.
    n : int
        Tenor.
    rho : float
        The Facility's valuation rate -- the one that made the V column.
    r : float, optional
        The project's loan rate. Defaults to rho.
    delta_bar : float
        Level annual debt service. Everything here is per unit of it, so the
        default of 1.0 leaves the dimensionless quotes alone and reports the
        two money amounts -- the pure premium and the level annual premium --
        in units of one debt-service payment. Pass the draft's 100/yr to read
        them in its units.

    Returns
    -------
    dict
        Every entry below is the same expected loss in a different unit, and
        the annuity factor is what separates them.

        theta
            Expected loss in years of debt service, ``E[max(-V, 0)]``. The
            primitive; depends on rho alone.
        E_L
            ``delta_bar * theta``: the expected ultimate net loss in money,
            i.e. the pure premium, estimating ``E[L_w]``.
        phi
            ``delta_bar * psi``: the level annual premium in money.
        psi
            The same premium as a fraction of the level annual debt service,
            ``theta / A(n, rho)`` -- equivalently ``phi / delta_bar``. The
            underwriter's quote, and a pure number: a flow over a flow, where
            theta is a present value over a flow and so is measured in years.
        kappa
            The same loss as a share of the original principal,
            ``theta / A(n, r)``. The capital-relevant quote. Equal to psi
            only when r = rho -- the "A-identity" of the draft.
        psi_debt
            The premium restated against the original principal,
            ``psi / A(n, r)``: a flat annual fee, and the correct spread only
            on a bullet loan.
        delta_r
            Margin-equivalent add-on on an annuity-amortising loan: the
            investor's quote, about half again psi_debt because a margin
            accrues on a balance that amortises to zero.

        Plus the shape of the distribution it came from: ``p_loss``,
        ``mean_V``, ``median_V``, ``worst_V``, and the counts.

    Examples
    --------
    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> p = price(window_balance(wp, rho=0.05), n=15, rho=0.05)
    >>> round(p["theta"], 4), round(p["psi"], 4), round(1e4 * p["delta_r"])
    (0.718, 0.0692, 101)

    The premium is invariant to the loan rate -- delta_bar is pinned by the
    project's cash flow, so r only decides how much principal that supports
    -- while the capital quote is not:

    >>> q = price(window_balance(wp, rho=0.05), n=15, rho=0.05, r=0.08)
    >>> round(q["psi"], 4), round(q["kappa"], 4)
    (0.0692, 0.0839)

    On the draft's stylised project, 100 of debt service a year:

    >>> m = price(window_balance(wp, rho=0.05), n=15, rho=0.05, delta_bar=100)
    >>> round(m["E_L"], 2), round(m["phi"], 2)
    (71.8, 6.92)

    A sensitivity table is one line, because the return value is a plain dict:

    >>> grid = [0.03, 0.05, 0.08]
    >>> tbl = pd.DataFrame([price(window_balance(wp, rho=rho), 15, rho) for rho in grid])
    >>> tbl[["rho", "theta", "psi"]].round(4).to_dict("records")
    [{'rho': 0.03, 'theta': 0.8261, 'psi': 0.0692}, {'rho': 0.05, 'theta': 0.718, \
'psi': 0.0692}, {'rho': 0.08, 'theta': 0.5895, 'psi': 0.0689}]

    Harder discounting compresses the loss by nearly a third and barely moves
    the premium: numerator and denominator shrink together.
    """
    r = rho if r is None else r
    V = bal["V"].to_numpy(dtype=float)
    theta = float(-bal["loss"].mean()) + 0.0 if len(bal) else 0.0   # + 0.0 kills -0.0
    psi = theta / annuity(n, rho)
    return {
        "n": int(n), "rho": float(rho), "r": float(r),
        "n_windows": int(len(bal)),
        "n_countries": int(bal["iso3"].nunique()) if "iso3" in bal else 0,
        "theta": theta,
        "E_L": delta_bar * theta,
        "phi": delta_bar * psi,
        "psi": psi,
        "kappa": theta / annuity(n, r),
        "psi_debt": psi / annuity(n, r),
        "delta_r": equivalent_rate(psi, r, n) - r,
        "p_loss": float((V < 0).mean()) if V.size else 0.0,
        "mean_V": float(V.mean()) if V.size else 0.0,
        "median_V": float(np.median(V)) if V.size else 0.0,
        "worst_V": float(V.min()) if V.size else 0.0,
    }


def price_by(bal, by, n, rho, r=None):
    """The same price per group: by country, by regime, by close cohort, ...

    Expectation is linear in the pool, so these average back to `price`:
    grouping shows where the pooled price comes from, it cannot create or
    destroy premium.

    Parameters
    ----------
    bal : DataFrame
        Window balances from `window_balance`.
    by : str or list of str
        Grouping columns.
    n, rho, r
        As in `price`.

    Returns
    -------
    DataFrame
        One row per group, the `price` fields as columns, most expensive first.

    Examples
    --------
    >>> df = load_panel().query("iso3 in ['NGA', 'KEN']")
    >>> bal = window_balance(window_panel(df, n=15, start_year=1985), rho=0.05)
    >>> out = price_by(bal, "country", n=15, rho=0.05)
    >>> out[["country", "n_windows", "theta", "psi"]].round(4).to_dict("records")
    [{'country': 'Nigeria', 'n_windows': 25, 'theta': 0.718, 'psi': 0.0692}, \
{'country': 'Kenya', 'n_windows': 25, 'theta': 0.0, 'psi': 0.0}]

    Kenya prices at exactly zero: no window since 1985 ends below its close.
    """
    by = [by] if isinstance(by, str) else list(by)
    rows = []
    for key, sub in bal.groupby(by, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        rows.append({**dict(zip(by, key)), **price(sub, n, rho, r)})
    return pd.DataFrame(rows).sort_values("theta", ascending=False).reset_index(drop=True)


def describe(p):
    """Three lines summarising a `price` dict, for printing in a notebook.

    Examples
    --------
    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> print(describe(price(window_balance(wp, rho=0.05), n=15, rho=0.05)))
    N = 25 windows / 1 country, n = 15, rho = 5.00%, r = 5.00%
    theta = 0.7180 yrs of debt service;  psi = 0.0692 of debt service;  kappa = 0.0692 of principal
    psi/A = 67bp flat;  delta_r = 101bp on the margin;  P(V<0) = 16.0%;  E[V] = +6.05
    """
    return (
        "N = {n_windows} windows / {n_countries} {countries}, n = {n}, "
        "rho = {rho:.2%}, r = {r:.2%}\n"
        "theta = {theta:.4f} yrs of debt service;  psi = {psi:.4f} of debt service;  "
        "kappa = {kappa:.4f} of principal\n"
        "psi/A = {bp_debt:.0f}bp flat;  delta_r = {bp_margin:.0f}bp on the margin;  "
        "P(V<0) = {p_loss:.1%};  E[V] = {mean_V:+.2f}"
    ).format(bp_debt=1e4 * p["psi_debt"], bp_margin=1e4 * p["delta_r"],
             countries="country" if p["n_countries"] == 1 else "countries", **p)


# ---------------------------------------------------------------------------
# the liquidity leg: whose money is it
# ---------------------------------------------------------------------------
#
# Everything above collapses a window to one number and never forms a running
# balance: `window_balance` PV-weights each fixing and sums. That is enough for
# the risk leg, but it throws the path away, and the path is what says whose
# money went out the door. An advance made while the experience account is in
# surplus is the project's own escrow handed back to it; the same advance made
# on an empty or negative account is the Facility's balance sheet. Two windows
# with identical V can differ entirely in that mix.
#
# The ledger below is not a second model. With the account accruing at `carry`,
#
#     B_n = sum_k flow_k (1+carry)^(n-k)     and     V_w = B_n (1+rho)^-n,
#
# for ANY carry, because that is exactly what `weight` does -- so the terminal
# balance of the ledger reproduces V to machine precision, and the residual
# outstanding at maturity discounted back is exactly `loss`. The new columns
# are a decomposition of the existing number, not an alternative to it.
#
# One convention, stated because it is a choice: accrual on a negative balance
# is capitalised interest, not new liquidity. `draw_facility` counts cash out
# the door only. So the advances less the repayments do not tie to the closing
# outstanding -- the difference is the accrued interest, reported separately.


def _run_account(k, flow, n, rho, carry):
    """Run the experience account over one window's fixings.

    The private core of `ledger` and `liquidity_profile`: plain floats and a
    FIFO list, one pass over the fixings in order. Returns the per-fixing
    columns as a dict of arrays, plus the window-level totals.

    The FIFO holds one entry per Facility-funded advance,
    ``[k_opened, original_remaining, accreted_outstanding]``. Both amounts are
    carried because they answer different questions: repayments retire the
    accreted face (that is what ties to the balance), while the average life is
    weighted by the cash originally advanced (that is what went out the door).
    A partial repayment retires the same fraction of each.
    """
    c = rho if carry is None else carry
    m = len(k)
    z = lambda: np.zeros(m, dtype=float)
    bal_open, bal, interest = z(), z(), z()
    draw, draw_own, draw_fac = z(), z(), z()
    repaid, escrowed, outstanding = z(), z(), z()

    B = 0.0
    tranches = []          # FIFO; entries before `head` are fully retired
    head = 0
    fac_years = 0.0        # dollar-years of Facility money, original units
    repaid_orig = 0.0
    repaid_years = 0.0

    for i in range(m):
        # 1. accrue. The tranches accrete with the balance they make up, so
        #    sum(accreted) == -bal_open whenever the account is in deficit.
        Bo = B * (1.0 + c)
        interest[i] = Bo - B
        for tr in tranches[head:]:
            tr[2] *= 1.0 + c
        bal_open[i] = Bo

        f = float(flow[i])
        ki = float(k[i])

        # 2. a drawing, split at the zero line. A year is either a drawing or a
        #    surplus, never both, so the two branches cannot interact.
        d = -f if f < 0.0 else 0.0
        own = min(d, Bo) if Bo > 0.0 else 0.0
        fac = d - own
        draw[i], draw_own[i], draw_fac[i] = d, own, fac
        if fac > 0.0:
            tranches.append([ki, fac, fac])

        # 3. a surplus repays the outstanding advances first, FIFO, and only
        #    what is left over builds the project's escrow back up.
        s = f if f > 0.0 else 0.0
        rep = min(s, -Bo) if Bo < 0.0 else 0.0
        repaid[i], escrowed[i] = rep, s - rep
        left = rep
        while left > 1e-15 and head < len(tranches):
            tr = tranches[head]
            take = min(left, tr[2])
            o = tr[1] * (take / tr[2]) if tr[2] > 0.0 else tr[1]
            repaid_orig += o
            repaid_years += o * (ki - tr[0])
            fac_years += o * (ki - tr[0])
            tr[1] -= o
            tr[2] -= take
            left -= take
            if tr[2] <= 1e-15:
                head += 1

        B = Bo + f
        bal[i] = B
        outstanding[i] = -B if B < 0.0 else 0.0

    # 4. whatever is still open at maturity is censored there: the dollars the
    #    later surplus never came back for. Their accreted face is the loss.
    never = 0.0
    for tr in tranches[head:]:
        never += tr[1]
        fac_years += tr[1] * (n - tr[0])

    cols = {"balance_open": bal_open, "balance": bal, "accrued_interest": interest,
            "draw": draw, "draw_own": draw_own, "draw_facility": draw_fac,
            "repaid": repaid, "escrowed": escrowed, "outstanding": outstanding}
    tot = {"liq_gross": float(draw.sum()),
           "liq_own": float(draw_own.sum()),
           "liq_facility": float(draw_fac.sum()),
           "liq_facility_years": fac_years,
           "repaid_facility": repaid_orig,
           "repaid_facility_years": repaid_years,
           "never_repaid": never,
           "n_draw_years": int((draw > 0.0).sum()),
           "n_facility_years": int((draw_fac > 0.0).sum()),
           "peak_outstanding": float(outstanding.max()) if m else 0.0,
           "peak_at": int(outstanding.argmax()) if m else -1,
           "outstanding_final": float(outstanding[-1]) if m else 0.0,
           "balance_final": B}
    return cols, tot


def ledger(wp, rho, carry=None, flow="R"):
    """The experience account year by year: one row per (window, fixing).

    The path behind `window_balance`. Each year the account accrues at the
    carry, the year's flow lands on it, and a drawing is split according to the
    sign of the balance it lands on: money taken out of a surplus is the
    project's own escrow coming back, money taken out of an empty or negative
    account is the Facility's.

    Parameters
    ----------
    wp : DataFrame
        A window panel from `window_panel`.
    rho, carry : float
        Valuation rate and carry; see `weight`. The account accrues at `carry`
        (defaulting to rho); rho only discounts the terminal balance.
    flow : str
        The column paid into (or drawn out of) the account, as in
        `window_balance`. A `corridor` column works here unchanged: a shortfall
        the project absorbs itself is correctly not a drawing at all.

    Returns
    -------
    DataFrame
        The identifying columns of `wp` (KEY, ``year``, ``k``, ``flow``) plus

        ================  ================================================
        balance_open      the account after accrual, before the year's flow
        balance           the account at the end of the year
        accrued_interest  ``balance_open`` less last year's ``balance``
        draw              gross liquidity provided, ``max(-flow, 0)``
        draw_own          the part met out of a positive balance: the
                          project's own escrow, returned to it
        draw_facility     the part met out of an empty or negative balance:
                          cash off the Facility's balance sheet
        repaid            surplus applied to outstanding advances
        escrowed          surplus retained in the account
        outstanding       Facility exposure at year end, ``max(-balance, 0)``,
                          accreted, so it includes capitalised interest
        ================  ================================================

    See Also
    --------
    liquidity_profile : collapses this frame to one row per window.
    window_balance : the risk leg, off the same rows.

    Examples
    --------
    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> lg = ledger(wp, rho=0.05)
    >>> len(lg) == len(wp)
    True

    The 1985 window: the naira falls away from its close level and the account
    goes straight into deficit, so nothing is met out of escrow at first.

    >>> one = lg[lg.window_start == 1985]
    >>> one[["year", "draw", "draw_own", "draw_facility"]].head(3).round(3).to_dict("list")
    {'year': [1986, 1987, 1988], 'draw': [0.255, 0.355, 0.272], 'draw_own': [0.0, 0.0, 0.0], 'draw_facility': [0.255, 0.355, 0.272]}

    Later, once the surpluses have rebuilt the balance, a shortfall is met by
    the project's own money and costs the Facility nothing:

    >>> late = one[one.draw_own > 0]
    >>> bool((late.draw_facility == 0).all())
    True
    """
    n_by = wp.groupby(KEY)["k"].transform("max")
    parts = []
    for key, g in wp.groupby(KEY, sort=False):
        g = g.sort_values("k")
        n = int(n_by.loc[g.index].iloc[0])
        cols, _ = _run_account(g["k"].to_numpy(), g[flow].to_numpy(dtype=float),
                               n, rho, carry)
        parts.append(pd.DataFrame(cols, index=g.index))

    if not parts:
        return pd.DataFrame(columns=KEY + ["year", "k", "flow", "balance_open",
                                           "balance", "accrued_interest", "draw",
                                           "draw_own", "draw_facility", "repaid",
                                           "escrowed", "outstanding"])

    out = pd.concat(parts).reindex(wp.index)
    keep = wp[KEY + ["year", "k"]].assign(flow=wp[flow].astype(float))
    return pd.concat([keep, out], axis=1)


def liquidity_profile(wp, rho, carry=None, flow="R"):
    """Collapse the ledger to one row per window: how much, whose, how long.

    Joins on KEY to the output of `window_balance`, and carries ``V`` itself so
    it can stand alone. The two agree to machine precision by construction --
    ``V`` here is the ledger's terminal balance discounted at rho, which is the
    same sum `window_balance` forms in closed form.

    Parameters
    ----------
    wp : DataFrame
        A window panel from `window_panel`.
    rho, carry, flow
        As in `ledger`.

    Returns
    -------
    DataFrame
        One row per window:

        =====================  ===========================================
        liq_gross              total liquidity provided, undiscounted, in
                               years of debt service
        liq_own                the part met out of the project's escrow
        liq_facility           the part met off the Facility's balance sheet
        share_facility         ``liq_facility / liq_gross``
        liq_facility_years     dollar-years of Facility money: the numerator
                               of any weighted average life
        wal_facility           weighted average life of that money, in years,
                               with money still out at maturity censored
                               there. NaN where nothing was advanced
        repaid_facility        Facility money recovered inside the window
        wal_repaid             its weighted average life
        never_repaid           Facility money never recovered, original cash
        share_never_repaid     ``never_repaid / liq_facility``
        peak_outstanding       largest year-end exposure, accreted: what the
                               liquidity line has to be able to fund
        peak_year              the calendar year of that peak
        outstanding_final      exposure at maturity; times ``(1+rho)**-n``
                               this is exactly ``-loss``
        n_draw_years           years with any drawing
        n_facility_years       years with a drawing the Facility funded
        liq_gross_pv,          the same three amounts on the valuation basis
        liq_own_pv,            of V, for quoting alongside theta
        liq_facility_pv
        V, loss                as in `window_balance`
        =====================  ===========================================

    Notes
    -----
    ``liq_gross`` is undiscounted -- nominal cash, in units of one annual
    debt-service payment -- because that is the right unit for a funding
    question. It is therefore not comparable with theta, which is a present
    value; the ``_pv`` columns are there for when the sentence needs that basis
    instead.

    Examples
    --------
    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> prof = liquidity_profile(wp, rho=0.05)
    >>> bal = window_balance(wp, rho=0.05)
    >>> bool(np.allclose(prof.V, bal.V))
    True

    The residual outstanding at maturity is the loss, undiscounted:

    >>> bool(np.allclose(prof.outstanding_final * 1.05 ** -15, -prof.loss))
    True

    Kenya prices at exactly zero -- no window ends below its close -- and still
    draws a full year of debt service in liquidity, every dollar of it repaid
    inside the tenor. That gap is the whole point of the column:

    >>> ken = liquidity_profile(window_panel(load_panel().query("iso3 == 'KEN'"),
    ...                                      n=15, start_year=1985), rho=0.05)
    >>> round(float(ken.liq_gross.sum()), 4), float(ken.never_repaid.sum())
    (1.0812, 0.0)

    A window that never drew has no average life to report, so the ratio
    columns are NaN there rather than zero:

    >>> int(ken.wal_facility.isna().sum()), len(ken)
    (17, 25)
    """
    n_by = wp.groupby(KEY)["k"].transform("max")
    rows = []
    for key, g in wp.groupby(KEY, sort=False):
        g = g.sort_values("k")
        n = int(n_by.loc[g.index].iloc[0])
        k = g["k"].to_numpy()
        cols, tot = _run_account(k, g[flow].to_numpy(dtype=float), n, rho, carry)

        w = weight(k, n, rho, carry)
        peak_at = tot.pop("peak_at")
        rows.append({
            **dict(zip(KEY, key if isinstance(key, tuple) else (key,))),
            "n_fixings": len(k),
            **tot,
            "peak_year": int(g["year"].to_numpy()[peak_at]) if peak_at >= 0 else -1,
            "liq_gross_pv": float(cols["draw"] @ w),
            "liq_own_pv": float(cols["draw_own"] @ w),
            "liq_facility_pv": float(cols["draw_facility"] @ w),
            "V": tot["balance_final"] * (1.0 + rho) ** -n,
        })

    cols_order = KEY + [
        "n_fixings", "liq_gross", "liq_own", "liq_facility", "share_facility",
        "liq_facility_years", "wal_facility", "repaid_facility",
        "repaid_facility_years", "wal_repaid", "never_repaid",
        "share_never_repaid", "peak_outstanding", "peak_year",
        "outstanding_final", "n_draw_years", "n_facility_years",
        "liq_gross_pv", "liq_own_pv", "liq_facility_pv", "V", "loss"]

    if not rows:
        return pd.DataFrame(columns=cols_order)

    out = pd.DataFrame(rows)
    # Ratios last, so that a window that never drew is NaN rather than 0/0: an
    # average life of nothing is not zero years, and a mean over the pool must
    # not be dragged towards zero by windows that never happened.
    safe = lambda a, b: np.where(b > 0.0, a / np.where(b > 0.0, b, 1.0), np.nan)
    out["share_facility"] = safe(out.liq_facility, out.liq_gross)
    out["wal_facility"] = safe(out.liq_facility_years, out.liq_facility)
    out["wal_repaid"] = safe(out.repaid_facility_years, out.repaid_facility)
    out["share_never_repaid"] = safe(out.never_repaid, out.liq_facility)
    out["loss"] = out["V"].clip(upper=0.0)
    return out[cols_order]


def liquidity_summary(prof):
    """Pool-level liquidity quotes from a `liquidity_profile` frame.

    Every ratio is formed on pool totals rather than as a mean of the
    per-window ratios: the question is what share of every dollar the Facility
    put out is its own, so the dollars must be added before the division.

    Parameters
    ----------
    prof : DataFrame
        Window profiles from `liquidity_profile`.

    Returns
    -------
    dict
        liq_gross, liq_own, liq_facility
            Pool totals, undiscounted, in years of debt service.
        share_facility
            The headline: uncovered liquidity as a share of all liquidity
            provided.
        wal_facility
            Dollar-weighted average life of the Facility-funded money, in
            years, with money still out at maturity censored at the window end.
        wal_repaid
            The same for the part recovered inside the window.
        share_never_repaid
            The share of Facility-funded cash the window never gave back.
        p_any_draw, p_any_facility
            Share of windows that drew at all, and that drew the Facility's own
            money.
        mean_peak, max_peak
            Year-end exposure per window: the average and the worst, which is
            what sizes the liquidity line rather than the premium.
        share_facility_pv
            The same headline share on the valuation basis of V.

    Examples
    --------
    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> s = liquidity_summary(liquidity_profile(wp, rho=0.05))
    >>> sorted(s)[:4]
    ['liq_facility', 'liq_gross', 'liq_own', 'max_peak']
    >>> bool(0.0 <= s["share_facility"] <= 1.0), bool(0.0 <= s["wal_facility"] <= 15.0)
    (True, True)
    """
    tot = lambda col: float(prof[col].sum()) if len(prof) else 0.0
    div = lambda a, b: a / b if b > 0 else float("nan")
    g, own, fac = tot("liq_gross"), tot("liq_own"), tot("liq_facility")
    return {
        "n_windows": int(len(prof)),
        "n_countries": int(prof["iso3"].nunique()) if "iso3" in prof else 0,
        "liq_gross": g, "liq_own": own, "liq_facility": fac,
        "share_facility": div(fac, g),
        "wal_facility": div(tot("liq_facility_years"), fac),
        "wal_repaid": div(tot("repaid_facility_years"), tot("repaid_facility")),
        "share_never_repaid": div(tot("never_repaid"), fac),
        "p_any_draw": float((prof.liq_gross > 0).mean()) if len(prof) else 0.0,
        "p_any_facility": float((prof.liq_facility > 0).mean()) if len(prof) else 0.0,
        "mean_peak": float(prof.peak_outstanding.mean()) if len(prof) else 0.0,
        "max_peak": float(prof.peak_outstanding.max()) if len(prof) else 0.0,
        "share_facility_pv": div(tot("liq_facility_pv"), tot("liq_gross_pv")),
    }


def describe_liquidity(s):
    """Three lines summarising a `liquidity_summary` dict, for a notebook.

    Examples
    --------
    >>> wp = window_panel(load_panel().query("iso3 == 'NGA'"), n=15, start_year=1985)
    >>> print(describe_liquidity(liquidity_summary(liquidity_profile(wp, rho=0.05))))
    N = 25 windows / 1 country;  liquidity provided = 32.05 yrs of debt service
    of which the Facility's own = 28.14 (87.8%);  the project's own escrow = 3.91 (12.2%)
    average life 7.15 yrs (5.22 on the part repaid);  91.2% never repaid;  peak exposure 1.61 avg / 12.71 worst
    """
    return (
        "N = {n_windows} windows / {n_countries} {countries};  "
        "liquidity provided = {liq_gross:.2f} yrs of debt service\n"
        "of which the Facility's own = {liq_facility:.2f} ({share_facility:.1%});  "
        "the project's own escrow = {liq_own:.2f} ({share_own:.1%})\n"
        "average life {wal_facility:.2f} yrs ({wal_repaid:.2f} on the part repaid);  "
        "{share_never_repaid:.1%} never repaid;  "
        "peak exposure {mean_peak:.2f} avg / {max_peak:.2f} worst"
    ).format(countries="country" if s["n_countries"] == 1 else "countries",
             share_own=1.0 - s["share_facility"], **s)
