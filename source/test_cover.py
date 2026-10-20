"""Tests for source/cover.py.

Three kinds of assertion, in increasing order of how long they should survive:

1. **Closed forms.** Arithmetic that can be checked by hand.
2. **Equivalence to the code being replaced.** `_reference_wdi` below is
   `compute_terminal_residuals_wdi` copied verbatim out of paper_draft.ipynb,
   and `compute_indexed_residuals` in data_analysis_functions is an
   independently written path over the same windows. Both are temporary: they
   go when the migration finishes.
3. **Paper anchors.** The numbers the draft actually quotes. These are the ones
   that must outlive the refactor -- moving V from a fraction of principal to
   years of debt service touched eleven call sites, and nothing in the
   repository would have caught a missed one.

Run it directly (pytest is not installed in .venv, and the file also works
unchanged under pytest if you add it):

    .venv/Scripts/python.exe source/test_cover.py
"""

import doctest
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cover

ROOT = Path(__file__).resolve().parents[1]
D = 0.05          # the Facility's valuation rate, as the draft sets it
N = 15            # tenor
A15 = cover.annuity(N, D)

PANEL = cover.load_panel()


# ---------------------------------------------------------------------------
# the code being replaced, copied verbatim from paper_draft.ipynb
# ---------------------------------------------------------------------------

def _reference_wdi(df, years=N, discount_rate=D, window_mode="rolling",
                   col="X", start_year=None):
    if start_year is not None:
        df = df[df["year"] >= start_year]

    n_obs = years + 1
    out = []

    for iso3, g in df.dropna(subset=[col]).groupby("iso3"):
        g = g.sort_values("year").reset_index(drop=True)
        n = len(g)
        if n < n_obs:
            continue

        if window_mode == "two_non_overlapping":
            starts = list(range(0, n - n_obs + 1, years))[:2]
        elif window_mode == "rolling":
            starts = list(range(0, n - n_obs + 1))
        else:
            raise ValueError("window_mode must be 'two_non_overlapping' or 'rolling'")

        for i0 in starts:
            win = g.iloc[i0:i0 + n_obs]
            if win[col].isna().any():
                continue

            base = float(win[col].iloc[0])
            R_it = (win[col].to_numpy()[1:] / base) - 1.0
            t = np.arange(1, years + 1, dtype=float)
            dfactors = (1.0 + discount_rate) ** (-t)

            V = float(np.sum(R_it * dfactors))
            out.append({
                "iso3": iso3,
                "country": win["country"].iloc[0],
                "window_start": int(win["year"].iloc[0]),
                "window_end": int(win["year"].iloc[-1]),
                "baseline": base,
                "V": V,
                "loss": min(V, 0.0),
            })

    return pd.DataFrame(out)


def _reference_drawings(data, years=N, col="X", start_year=None):
    """`window_drawings` from paper_draft.ipynb, verbatim."""
    if start_year is not None:
        data = data[data["year"] >= start_year]
    n_obs = years + 1
    rows = []
    for iso3, g in data.dropna(subset=[col]).groupby("iso3"):
        g = g.sort_values("year").reset_index(drop=True)
        for i0 in range(0, len(g) - n_obs + 1):
            win = g.iloc[i0:i0 + n_obs]
            if win[col].isna().any():
                continue
            R_wt = win[col].to_numpy()[1:] / float(win[col].iloc[0]) - 1.0
            rows.append({"iso3": iso3, "window_start": int(win["year"].iloc[0]),
                         "any_draw": bool((R_wt < 0).any()),
                         "n_draw_years": int((R_wt < 0).sum()),
                         "worst_year": float(R_wt.min())})
    return pd.DataFrame(rows)


def balance(df=None, n=N, rho=D, col="X", start_year=None, mode="rolling", carry=None):
    """The two steps the tests use over and over."""
    wp = cover.window_panel(PANEL if df is None else df, n=n, col=col,
                            start_year=start_year, mode=mode)
    return cover.window_balance(wp, rho, carry=carry)


# ---------------------------------------------------------------------------
# 1. closed forms
# ---------------------------------------------------------------------------

def test_annuity():
    assert abs(A15 - 10.379658) < 1e-6
    assert cover.annuity(15, 0.0) == 15.0
    assert abs(cover.annuity(1, 0.05) - 1 / 1.05) < 1e-14


def test_flat_series_has_zero_balance():
    assert cover.cover_balance([1.0] * 16, D) == 0.0
    assert cover.cover_balance([7.3] * 16, D) == 0.0


def test_permanent_shortfall_costs_shock_times_annuity():
    """R_k = g at every fixing, so V = g * A_{n,rho}. This is the sense in which
    V is in years of debt service: a permanent 10% shortfall costs a tenth of
    the annuity, 1.04 years."""
    levels = [1.0] + [0.90] * N
    assert abs(cover.cover_balance(levels, D) - (-0.10 * A15)) < 1e-12


def test_zero_rate_is_the_undiscounted_sum():
    assert abs(cover.cover_balance([1.0, 1.1, 0.9, 1.3], 0.0) - 0.3) < 1e-12


def test_close_year_is_not_a_fixing():
    """The close sets the strike and cannot move the balance: scaling every
    level leaves V untouched."""
    levels = np.array([1.0, 0.8, 1.2, 1.05])
    assert abs(cover.cover_balance(levels, D) - cover.cover_balance(2 * levels, D)) < 1e-15


def test_carry_rate_collapses_to_the_closed_form_when_c_equals_d():
    levels = [1.0, 0.8, 1.2, 0.95, 1.4]
    assert abs(cover.cover_balance(levels, D, carry=D) - cover.cover_balance(levels, D)) < 1e-15
    k = np.arange(1, 5)
    assert np.abs(cover.weight(k, 4, D, carry=D) - cover.weight(k, 4, D)).max() < 1e-15


def test_carry_above_the_valuation_rate_deepens_an_unrepaid_deficit():
    """Relative to discounting at rho, a carry of carry weights a flow at k by
    ((1+carry)/(1+rho))^(n-k): above rho that shifts weight from the late flows to the
    early ones. The Facility advances early and recovers late, so carry > rho makes
    a losing window cost it MORE -- it is charging interest on advances the
    later surpluses never repay -- and carry < rho makes it cost less."""
    drawn = [1.0, 0.8, 0.85, 0.9, 0.95]                  # short throughout
    assert cover.cover_balance(drawn, D, carry=0.08) < cover.cover_balance(drawn, D)
    assert cover.cover_balance(drawn, D, carry=0.02) > cover.cover_balance(drawn, D)
    # and on the real panel it is the premium that moves, in the same direction
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    theta = lambda carry: cover.price(cover.window_balance(wp, D, carry=carry), N, D)["theta"]
    assert theta(0.08) > theta(D) > theta(0.02)


def test_window_panel_shape():
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    assert len(wp) == 1055 * N                      # one row per fixing
    assert (wp.groupby(cover.KEY)["k"].max() == N).all()
    assert wp["k"].min() == 1                       # the close year is not in the frame
    one = wp[(wp["iso3"] == "NGA") & (wp["window_start"] == 1998)]
    assert list(one["year"]) == list(range(1999, 2014))
    assert one["window_end"].unique().tolist() == [2013]


def test_two_non_overlapping_windows_share_an_endpoint():
    wp = cover.window_panel(PANEL[PANEL["iso3"] == "NGA"], n=N,
                            start_year=1985, mode="two_non_overlapping")
    starts = sorted(wp["window_start"].unique())
    ends = sorted(wp["window_end"].unique())
    assert starts == [1985, 2000] and ends == [2000, 2015]


# ---------------------------------------------------------------------------
# 2. equivalence to the code being replaced
# ---------------------------------------------------------------------------

def _assert_same(new, old, tol=1e-12):
    assert len(new) == len(old), "%d windows vs %d" % (len(new), len(old))
    key = ["iso3", "window_start"]
    a = new.set_index(key).sort_index()
    b = old.set_index(key).sort_index()
    assert (a.index == b.index).all()
    pairs = [("window_end", "window_end"), ("base", "baseline"), ("V", "V"), ("loss", "loss")]
    for mine, theirs in pairs:
        if theirs not in b.columns:      # compute_indexed_residuals carries no baseline
            continue
        assert np.abs(a[mine].to_numpy(float) - b[theirs].to_numpy(float)).max() < tol, mine


def test_matches_the_notebook_across_the_grid():
    """One case per dimension rather than the full cross-product: the series
    priced, the sample start, the tenor and the window mode."""
    cases = [
        dict(col="X", start_year=None, n=15, mode="rolling"),
        dict(col="X", start_year=1985, n=15, mode="rolling"),
        dict(col="X", start_year=1995, n=15, mode="rolling"),
        dict(col="Q", start_year=1985, n=15, mode="rolling"),
        dict(col="usd_per_lcu", start_year=1985, n=15, mode="rolling"),
        dict(col="X", start_year=1985, n=5, mode="rolling"),
        dict(col="X", start_year=1985, n=25, mode="rolling"),
        dict(col="X", start_year=1985, n=15, mode="two_non_overlapping"),
    ]
    for case in cases:
        old = _reference_wdi(PANEL, years=case["n"], col=case["col"],
                             window_mode=case["mode"], start_year=case["start_year"])
        _assert_same(balance(**case), old)


def test_matches_the_notebook_drawings():
    new = balance(start_year=1985).set_index(["iso3", "window_start"]).sort_index()
    old = (_reference_drawings(PANEL, start_year=1985)
           .set_index(["iso3", "window_start"]).sort_index())
    assert (new["any_draw"] == old["any_draw"]).all()
    assert (new["n_draw_years"] == old["n_draw_years"]).all()
    assert np.abs(new["worst_year"] - old["worst_year"]).max() < 1e-12


def test_gaps_drop_no_fixing():
    """Windows are cut on positions in the non-missing series, not on calendar
    years: a hole moves window_end out, it does not shorten the window."""
    g = PANEL[PANEL["iso3"] == "NGA"].copy()
    g.loc[g["year"] == 2000, "X"] = np.nan
    new = balance(g)
    _assert_same(new, _reference_wdi(g, col="X"))
    spans = new["window_end"] - new["window_start"]
    assert (spans > N).any() and (spans >= N).all()
    assert (new["n_fixings"] == N).all()


def test_matches_compute_indexed_residuals_at_full_indexation():
    """`compute_indexed_residuals` is an independently written path over the
    same windows (upsampling, applied index, offtaker tier). At its default
    rule on an annual grid it prices X itself, so it must agree exactly."""
    daf = _import_daf()
    if daf is None:
        return "skipped: data_analysis_functions needs cwd=notebooks/"
    old = daf.compute_indexed_residuals(PANEL, years=N, discount_rate=D,
                                        start_year=1995, steps_per_year=1)
    _assert_same(balance(start_year=1995), old, tol=1e-9)


def _import_daf():
    """data_analysis_functions reads a CSV at import time, relative to cwd."""
    cwd = os.getcwd()
    try:
        os.chdir(ROOT / "notebooks")
        import data_analysis_functions as daf
        return daf
    except Exception:
        return None
    finally:
        os.chdir(cwd)


# ---------------------------------------------------------------------------
# 3. paper anchors
# ---------------------------------------------------------------------------

def test_algeria_segments():
    """The two shaded areas of the Algeria panel, each valued at the start of
    its own segment, and the full 1998 window. Unequal-length segments: under
    the old normalisation these were divided by a 15-year annuity factor
    whatever their length."""
    dza = PANEL[(PANEL["iso3"] == "DZA") & (PANEL["year"] >= 1995)].dropna(subset=["X"])

    def seg(t0, t1, col="X"):
        w = dza[(dza["year"] >= t0) & (dza["year"] <= t1)].sort_values("year")
        return cover.cover_balance(w[col].to_numpy(), D)

    assert abs(seg(1998, 2006) - (-0.7615)) < 5e-4
    assert abs(seg(2006, 2013) - (+1.1488)) < 5e-4
    assert abs(seg(1998, 2013) - (-0.0320)) < 5e-4
    assert abs(seg(1998, 2013, "usd_per_lcu") - (-2.0650)) < 5e-4
    # the gain carried back eight years nearly offsets the earlier shortfall
    assert abs(seg(2006, 2013) * (1 + D) ** -8 - 0.7776) < 5e-4


def test_nigeria_1985_pool():
    bal = balance(PANEL[PANEL["iso3"] == "NGA"], start_year=1985)
    q = cover.price(bal, N, D)
    assert q["n_windows"] == 25
    assert (bal["V"] < 0).sum() == 4
    assert abs(q["theta"] - 0.7180) < 5e-4          # years of debt service
    assert abs(q["psi"] - 0.0692) < 5e-4            # share of each payment
    assert abs(1e4 * q["delta_r"] - 101) < 0.6      # bp on the margin
    assert abs(q["worst_V"] - (-6.111)) < 5e-3


def test_all_africa_1985_pool():
    bal = balance(start_year=1985)
    q = cover.price(bal, N, D)
    assert (q["n_windows"], q["n_countries"]) == (1055, 50)
    assert abs(q["theta"] - 0.4121) < 5e-4
    assert abs(q["psi"] - 0.0397) < 5e-4
    assert abs(1e4 * q["psi_debt"] - 38) < 0.6
    assert abs(1e4 * q["delta_r"] - 58) < 0.6
    assert abs(q["mean_V"] - 2.2673) < 5e-4
    assert abs(q["median_V"] - 1.8395) < 5e-4
    assert abs(q["worst_V"] - (-7.8329)) < 5e-4
    assert abs(q["p_loss"] - 0.263) < 5e-4
    # the liquidity leg: the Facility lends far more often than it loses
    assert abs(bal["any_draw"].mean() - 0.674) < 5e-4
    assert abs(bal["n_draw_years"].mean() - 4.7) < 0.05
    assert abs(bal.loc[bal["any_draw"], "n_draw_years"].mean() - 6.9) < 0.05


def test_all_africa_1995_pool():
    q = cover.price(balance(start_year=1995), N, D)
    assert (q["n_windows"], q["n_countries"]) == (668, 50)
    assert abs(q["theta"] - 0.2112) < 5e-4
    assert abs(q["psi"] - 0.0203) < 5e-4
    assert abs(1e4 * q["delta_r"] - 30) < 0.6


def test_real_exchange_rate_pool():
    """Where the affordability comes from: on Q the cover is close to a fair
    bet, and the gap to X is the US price level."""
    q = cover.price(balance(col="Q", start_year=1985), N, D)
    assert abs(q["theta"] - 1.0328) < 5e-4
    assert abs(q["psi"] - 0.0995) < 5e-4
    assert abs(1e4 * q["delta_r"] - 144) < 0.6
    assert abs(q["p_loss"] - 0.533) < 5e-4


def test_country_quotes():
    bal = balance(start_year=1985)
    by = cover.price_by(bal, ["iso3", "country"], N, D)
    assert len(by) == 50
    assert (by["theta"] == 0).sum() == 8            # eight countries never end short
    assert by.iloc[0]["country"] == "Libya"
    assert abs(1e4 * by.iloc[0]["delta_r"] - 274) < 0.6
    assert abs(1e4 * by["delta_r"].median() - 40) < 0.6
    assert abs(1e4 * by.loc[by["iso3"] == "NGA", "delta_r"].iloc[0] - 101) < 0.6
    # pooling only averages: expectation is linear in the pool
    weighted = (by["theta"] * by["n_windows"]).sum() / by["n_windows"].sum()
    assert abs(weighted - cover.price(bal, N, D)["theta"]) < 1e-12


# ---------------------------------------------------------------------------
# 4. the quote layer, and the rates
# ---------------------------------------------------------------------------

def test_one_annuity_division_separates_the_quotes():
    q = cover.price(balance(start_year=1985), N, D)
    assert abs(q["psi"] * A15 - q["theta"]) < 1e-15
    assert abs(q["psi_debt"] * A15 - q["psi"]) < 1e-15
    # the A-identity: kappa and psi are one number only because r = rho here
    assert abs(q["kappa"] - q["psi"]) < 1e-15


def test_psi_is_invariant_to_the_loan_rate_and_kappa_is_not():
    """delta_bar is a physical quantity, pinned by the project's close-year
    cash flow, so the loan rate cannot move the premium -- only how much
    principal that cash flow supports."""
    bal = balance(start_year=1985)
    base = cover.price(bal, N, D)
    for r in (0.06, 0.08, 0.10, 0.12):
        q = cover.price(bal, N, D, r=r)
        assert abs(q["psi"] - base["psi"]) < 1e-15
        assert q["kappa"] > base["kappa"]
        assert abs(q["kappa"] - q["psi"] * A15 / cover.annuity(N, r)) < 1e-15
    # separating the loan rate from the Facility's own is worth single digits
    assert abs(1e4 * cover.price(bal, N, D, r=0.08)["delta_r"] - 64) < 1.0


def test_equivalent_rate_round_trips():
    for psi in (0.0, 0.0203, 0.0397, 0.1937):
        r = cover.equivalent_rate(psi, D, N)
        assert abs(cover.annuity(N, r) * (1 + psi) - A15) < 1e-10
    assert abs(cover.equivalent_rate(0.0, D, N) - D) < 1e-9


def test_theta_depends_on_d_alone():
    """Harder discounting compresses the depth of the loss but pushes more
    windows below zero: rho prices the intertemporal hedge in frequency rather
    than in the premium."""
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    qs = [cover.price(cover.window_balance(wp, rho), N, rho) for rho in (0.03, 0.05, 0.08, 0.12)]
    thetas = [q["theta"] for q in qs]
    p_losses = [q["p_loss"] for q in qs]
    psis = [q["psi"] for q in qs]
    assert thetas == sorted(thetas, reverse=True)
    assert p_losses == sorted(p_losses)
    assert max(psis) - min(psis) < 0.003            # psi barely moves: 4.02% -> 3.81%


def test_a_deductible_is_a_column_on_the_window_panel():
    """The extension path. A deductible -- the project absorbs the first `a` of
    any shortfall itself, and the Facility advances only what is left -- is a
    new column on `wp` plus `flow=` on the call. Nothing in cover.py changes.

        R = -0.20  ->  -0.15   Facility covers 15 points, project the first 5
        R = -0.03  ->   0      project absorbs the lot; not a drawing at all
        R = +0.10  ->  +0.10   surplus still escrowed in full

    This is the corridor of moneyness_and_triggers_20260916.md written as a
    return rather than a level: a = 0.05 is the attachment theta^a = 0.95.
    """
    a = 0.05
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    wp["net_of_deductible"] = cover.corridor(wp["R"], lower=a)

    mapped = cover.corridor(pd.Series([-0.20, -0.03, 0.10]), lower=a)
    assert np.abs(mapped - np.array([-0.15, 0.0, 0.10])).max() < 1e-12

    full = cover.price(cover.window_balance(wp, D), N, D)
    net = cover.price(cover.window_balance(wp, D, flow="net_of_deductible"), N, D)
    assert net["theta"] < full["theta"]
    # and the liquidity leg follows the flow: fewer years count as a drawing
    bal_full = cover.window_balance(wp, D)
    bal_net = cover.window_balance(wp, D, flow="net_of_deductible")
    assert bal_net["n_draw_years"].sum() < bal_full["n_draw_years"].sum()


def test_a_cap_is_the_same_move_in_the_other_direction():
    """A cap -- the Facility advances at most `a` in any one year and the
    project keeps the rest of the tail -- is the clip. Both shrink the premium,
    but they take it from opposite ends of the shortfall distribution: the
    deductible drops the small years, the cap truncates the big ones."""
    a = 0.05
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    wp["capped"] = wp["R"].clip(lower=-a)        # not a corridor: a limit per year

    full = cover.window_balance(wp, D)
    capped = cover.window_balance(wp, D, flow="capped")
    assert cover.price(capped, N, D)["theta"] < cover.price(full, N, D)["theta"]
    assert (capped["worst_year"] >= -a - 1e-12).all()
    # every year that drew before still draws: the cap changes size, not count
    assert (capped["n_draw_years"] == full["n_draw_years"]).all()


def test_an_empty_corridor_changes_nothing():
    wp = cover.window_panel(PANEL[PANEL["iso3"] == "NGA"], n=N, start_year=1985)
    wp["same"] = cover.corridor(wp["R"])
    a = cover.window_balance(wp, D)
    b = cover.window_balance(wp, D, flow="same")
    assert np.abs(a["V"] - b["V"]).max() < 1e-15


def test_an_escrow_threshold_raises_the_premium():
    """The other side of the corridor, and the counter-intuitive one: letting
    the project keep its small surpluses weakens the recovery leg the Facility
    relies on, so the cover gets more expensive, not less."""
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    wp["kept"] = cover.corridor(wp["R"], upper=0.07)
    full = cover.price(cover.window_balance(wp, D), N, D)
    kept = cover.price(cover.window_balance(wp, D, flow="kept"), N, D)
    assert kept["theta"] > full["theta"]
    assert kept["p_loss"] > full["p_loss"]
    # but the trigger is untouched, so the Facility lends exactly as often
    bal_full = cover.window_balance(wp, D)
    bal_kept = cover.window_balance(wp, D, flow="kept")
    assert (bal_kept["n_draw_years"] == bal_full["n_draw_years"]).all()


# ---------------------------------------------------------------------------
# 4b. the liquidity leg: the ledger decomposes V, it does not replace it
# ---------------------------------------------------------------------------

def _hand_panel(levels, iso3="ZZZ"):
    """A one-country window panel from a hand-written path of the index.

    `levels[0]` is the close, the rest are the fixings, so the frame has the
    same shape `window_panel` would produce -- but the path is chosen rather
    than observed, which is what lets the ledger be checked by hand.
    """
    levels = np.asarray(levels, dtype=float)
    n = len(levels) - 1
    return pd.DataFrame({
        "iso3": iso3, "country": iso3,
        "window_start": 2000, "window_end": 2000 + n,
        "year": np.arange(2001, 2001 + n),
        "k": np.arange(1, n + 1),
        "base": levels[0],
        "level": levels[1:],
        "R": levels[1:] / levels[0] - 1.0,
    })


def test_the_ledger_reproduces_V():
    """The terminal balance, discounted, is exactly the closed form's V.

    The whole design rests on this: `liquidity_profile` is a decomposition of
    the number `window_balance` already reports, not a second model of it. If
    this drifts, every share below is a share of something else.
    """
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    for rho in (0.0, 0.03, D, 0.08):
        prof = cover.liquidity_profile(wp, rho=rho)
        bal = cover.window_balance(wp, rho=rho)
        merged = bal.merge(prof, on=cover.KEY, suffixes=("_bal", "_led"))
        assert len(merged) == len(bal) == len(prof)
        assert np.allclose(merged.V_bal, merged.V_led, atol=1e-12), rho
        assert np.allclose(merged.loss_bal, merged.loss_led, atol=1e-12), rho


def test_the_ledger_reproduces_V_under_a_carry_wedge():
    """Same identity when the account accrues at something other than rho.

    V = B_n (1+rho)^-n holds for any carry, because that is what `weight`
    computes -- so a wedge must move both sides together or neither.
    """
    wp = cover.window_panel(PANEL.query("iso3 in ['NGA', 'DZA', 'KEN']"),
                            n=N, start_year=1985)
    for carry in (0.02, D, 0.09):
        prof = cover.liquidity_profile(wp, rho=D, carry=carry)
        bal = cover.window_balance(wp, rho=D, carry=carry)
        merged = bal.merge(prof, on=cover.KEY, suffixes=("_bal", "_led"))
        assert np.allclose(merged.V_bal, merged.V_led, atol=1e-12), carry


def test_the_residual_at_maturity_is_the_loss():
    """What is still outstanding at maturity, discounted, is -loss.

    The liquidity leg and the risk leg are two readings of the same account:
    the money the later surpluses never came back for IS the ultimate net loss.
    """
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    prof = cover.liquidity_profile(wp, rho=D)
    assert np.allclose(prof.outstanding_final * (1 + D) ** -N, -prof.loss, atol=1e-12)
    # and a window that ends in surplus has nothing outstanding at all
    assert (prof.loc[prof.V > 0, "outstanding_final"] == 0).all()


def test_the_two_legs_agree_on_when_the_facility_lends():
    """`n_draw_years` off the ledger matches the one off the closed form."""
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    prof = cover.liquidity_profile(wp, rho=D)
    bal = cover.window_balance(wp, rho=D)
    merged = bal.merge(prof, on=cover.KEY, suffixes=("_bal", "_led"))
    assert (merged.n_draw_years_bal == merged.n_draw_years_led).all()


def test_the_liquidity_splits_into_two_and_only_two_parts():
    """Every dollar drawn is either the project's escrow or the Facility's."""
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    lg = cover.ledger(wp, rho=D)
    assert np.allclose(lg.draw, lg.draw_own + lg.draw_facility, atol=1e-12)
    assert (lg.draw_own >= -1e-12).all() and (lg.draw_facility >= -1e-12).all()
    # a drawing and a surplus are mutually exclusive in a year
    assert ((lg.draw > 0) & (lg.repaid + lg.escrowed > 0)).sum() == 0
    # the profile is the ledger, summed
    prof = cover.liquidity_profile(wp, rho=D)
    per_window = lg.groupby(cover.KEY, as_index=False)[
        ["draw", "draw_own", "draw_facility"]].sum()
    merged = prof.merge(per_window, on=cover.KEY)
    assert np.allclose(merged.liq_gross, merged.draw, atol=1e-12)
    assert np.allclose(merged.liq_own, merged.draw_own, atol=1e-12)
    assert np.allclose(merged.liq_facility, merged.draw_facility, atol=1e-12)


def test_the_balance_is_the_running_sum_of_the_flows():
    """The account recursion, checked against the ledger's own columns."""
    wp = cover.window_panel(PANEL.query("iso3 == 'NGA'"), n=N, start_year=1985)
    lg = cover.ledger(wp, rho=D)
    for _, g in lg.groupby(cover.KEY, sort=False):
        prev = np.concatenate([[0.0], g.balance.to_numpy()[:-1]])
        assert np.allclose(g.balance_open, prev * (1 + D), atol=1e-12)
        assert np.allclose(g.balance, g.balance_open + g.flow, atol=1e-12)
        assert np.allclose(g.accrued_interest, g.balance_open - prev, atol=1e-12)


def test_a_window_that_only_falls_is_all_facility_money():
    """No surplus ever arrives, so the project's escrow funds none of it.

    Every advance is censored at maturity, so the average life is the mean of
    (n - k) weighted by the advance made at k -- checkable by hand.
    """
    levels = [1.0] + [1.0 - 0.02 * k for k in range(1, N + 1)]
    wp = _hand_panel(levels)
    prof = cover.liquidity_profile(wp, rho=D)
    row = prof.iloc[0]
    assert row.liq_own == 0.0
    assert row.share_facility == 1.0
    assert np.isclose(row.share_never_repaid, 1.0)
    assert row.repaid_facility == 0.0
    assert np.isnan(row.wal_repaid)

    # by hand. R is a CUMULATIVE return, so the flow in year k is the whole
    # shortfall to date, 0.02k, not its increment -- the project is short that
    # much of its debt service that year. Each advance stays out to maturity.
    k = np.arange(1, N + 1)
    adv = 0.02 * k
    assert np.isclose(row.liq_facility, adv.sum())
    assert np.isclose(row.wal_facility, (adv * (N - k)).sum() / adv.sum())


def test_a_window_that_only_rises_never_draws():
    """Nothing to fund, so the ratios are NaN rather than zero."""
    levels = [1.0] + [1.0 + 0.02 * k for k in range(1, N + 1)]
    prof = cover.liquidity_profile(_hand_panel(levels), rho=D)
    row = prof.iloc[0]
    assert row.liq_gross == 0.0 and row.liq_facility == 0.0
    assert np.isnan(row.share_facility) and np.isnan(row.wal_facility)
    assert row.peak_outstanding == 0.0 and row.V > 0


def test_a_second_dip_is_funded_by_the_project_once_the_escrow_is_rebuilt():
    """The distinction the whole exercise is about.

    The path dips, recovers far past its close level, then dips again by the
    same amount. The first dip is the Facility's money; the second is the
    project's own escrow handed back, and costs the Facility nothing.
    """
    levels = [1.0, 0.9, 1.6, 1.6, 0.9, 1.0]
    lg = cover.ledger(_hand_panel(levels), rho=D)
    first, second = lg.iloc[0], lg.iloc[3]     # the two -0.1 years
    assert np.isclose(first.flow, -0.1) and np.isclose(second.flow, -0.1)
    assert np.isclose(first.draw_facility, 0.1) and first.draw_own == 0.0
    assert np.isclose(second.draw_own, 0.1) and second.draw_facility == 0.0

    prof = cover.liquidity_profile(_hand_panel(levels), rho=D)
    row = prof.iloc[0]
    assert np.isclose(row.liq_gross, 0.2)
    assert np.isclose(row.liq_facility, 0.1) and np.isclose(row.liq_own, 0.1)
    assert np.isclose(row.share_facility, 0.5)
    # the first advance is retired by the surplus one year later
    assert np.isclose(row.wal_facility, 1.0)
    assert row.never_repaid == 0.0


def test_a_partial_repayment_retires_the_tranche_pro_rata():
    """Half the advance comes back after one year, half is censored at maturity.

    The advance of 0.2 at k=1 is met by a surplus at k=2 worth half of the
    accreted face; the rest stays out to k=3. Weighting is on the cash
    originally advanced, so the average life is 0.5*1 + 0.5*2.
    """
    accreted = 0.2 * (1 + D)                   # face of the advance at k=2
    levels = [1.0, 0.8, 1.0 + accreted / 2, 1.0]
    prof = cover.liquidity_profile(_hand_panel(levels), rho=D)
    row = prof.iloc[0]
    assert np.isclose(row.liq_facility, 0.2)
    assert np.isclose(row.repaid_facility, 0.1)
    assert np.isclose(row.never_repaid, 0.1)
    assert np.isclose(row.wal_repaid, 1.0)
    assert np.isclose(row.wal_facility, 0.5 * 1 + 0.5 * 2)


def test_a_deductible_is_not_a_drawing():
    """Under a corridor, a shortfall the project absorbs draws nothing.

    `flow` is honoured the same way it is in `window_balance`, so the contract
    and the ledger cannot describe different instruments.
    """
    wp = cover.window_panel(PANEL.query("iso3 == 'NGA'"), n=N, start_year=1985)
    wp["kept"] = cover.corridor(wp.R, lower=0.05)
    full = cover.liquidity_profile(wp, rho=D)
    net = cover.liquidity_profile(wp, rho=D, flow="kept")
    assert net.liq_gross.sum() < full.liq_gross.sum()
    assert net.liq_facility.sum() < full.liq_facility.sum()
    assert np.allclose(net.V, cover.window_balance(wp, rho=D, flow="kept").V,
                       atol=1e-12)


def test_liquidity_is_not_solvency_on_the_african_pool():
    """The paper anchor: the pool lends far more than it ever loses.

    Gross liquidity, the Facility's own share of it and its average life are
    the three numbers the draft quotes off this machinery. They move only if
    the data or the contract moves.
    """
    wp = cover.window_panel(PANEL, n=N, start_year=1985)
    prof = cover.liquidity_profile(wp, rho=D)
    s = cover.liquidity_summary(prof)
    assert s["n_windows"] == 1055, s["n_windows"]
    # more is lent than is lost, by a wide margin
    theta = cover.price(cover.window_balance(wp, rho=D), N, D)["theta"]
    assert s["liq_facility"] / s["n_windows"] > theta
    # the shares are shares
    assert np.isclose(s["liq_own"] + s["liq_facility"], s["liq_gross"])
    assert 0.0 < s["share_facility"] < 1.0
    assert 0.0 < s["share_never_repaid"] < 1.0
    assert 0.0 < s["wal_facility"] <= N
    assert s["wal_repaid"] < s["wal_facility"]      # the censored part is older


def test_kenya_lends_without_losing():
    """A country that prices at exactly zero still needs a liquidity line.

    This is the cleanest case of the two legs coming apart: Kenya's pure
    premium is zero -- the draft says so -- and yet the Facility advances a
    full year of debt service across the sample, every dollar repaid inside
    the tenor.
    """
    wp = cover.window_panel(PANEL.query("iso3 == 'KEN'"), n=N, start_year=1985)
    s = cover.liquidity_summary(cover.liquidity_profile(wp, rho=D))
    assert cover.price(cover.window_balance(wp, rho=D), N, D)["theta"] == 0.0
    assert s["liq_gross"] > 1.0
    assert s["liq_facility"] > 0.0
    assert s["share_never_repaid"] == 0.0
    assert s["wal_facility"] == s["wal_repaid"]


def test_an_empty_panel_gives_empty_frames_not_an_error():
    empty = cover.window_panel(PANEL.query("iso3 == 'NOPE'"), n=N)
    assert len(cover.ledger(empty, rho=D)) == 0
    prof = cover.liquidity_profile(empty, rho=D)
    assert len(prof) == 0
    assert "share_facility" in prof.columns
    s = cover.liquidity_summary(prof)
    assert s["n_windows"] == 0 and np.isnan(s["share_facility"])


# ---------------------------------------------------------------------------
# 5. the docstrings
# ---------------------------------------------------------------------------

def test_docstring_examples():
    """Every `>>>` in cover.py is executed, so no example can go stale.

    This is the point of writing them as doctests rather than as prose: the
    module's documentation and its behaviour are checked against each other on
    every run.
    """
    result = doctest.testmod(cover, optionflags=doctest.NORMALIZE_WHITESPACE,
                             verbose=False, report=True)
    assert result.failed == 0, "%d of %d docstring examples failed" % (
        result.failed, result.attempted)
    assert result.attempted >= 45, "only %d examples ran -- did some get lost?" % (
        result.attempted)


# ---------------------------------------------------------------------------
# standalone runner
# ---------------------------------------------------------------------------

def main():
    tests = [(k, v) for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = skipped = 0
    for name, fn in tests:
        try:
            note = fn()
        except AssertionError as exc:
            failed += 1
            print("FAIL %-55s %s" % (name, exc))
        except Exception as exc:
            failed += 1
            print("ERROR %-54s %s: %s" % (name, type(exc).__name__, exc))
        else:
            if isinstance(note, str) and note.startswith("skipped"):
                skipped += 1
                print("SKIP %-55s %s" % (name, note))
            else:
                print("ok   %s" % name)
    print("\n%d passed, %d failed, %d skipped, of %d"
          % (len(tests) - failed - skipped, failed, skipped, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
