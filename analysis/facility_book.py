"""Calendar-time book of a Facility writing k-year covers every year.

Programme A ("fixed"): base dates 1985-2009 for every tenor, the windows the
paper prices. Programme B ("going concern"): every base date for which a k-year
window exists, 1985 to 2024-k, so short tenors keep writing into the 2010s.

Each base date and country gets a cohort of size 1/k, so every tenor puts one
unit of debt service per country in force at steady state. Premium is the fair
pool premium Psi(k) of the programme's own windows. Facility cash flow per
cover-year: premium - drawings it funds (own escrow first) + surpluses that
repay its advances; a deficit outstanding at maturity is never repaid.
"""
import sys
sys.path.insert(0, r"C:\code\currency_devaluation_events\source")
import numpy as np
import pandas as pd
import cover
import default_risk as dr

n, rho = 15, 0.05
df = cover.load_panel(drop=("LSO",))
YEARS = np.arange(1985, 2025)
KEYS15 = cover.window_balance(cover.window_panel(df, n=n), rho)[["iso3", "window_start"]]


def windows(k, programme):
    keys, F = dr.flow_matrix(cover.window_panel(df, n=k))
    if programme == "fixed":
        m = keys.merge(KEYS15.assign(_in=True), how="left")["_in"].fillna(False).to_numpy(bool)
        keys, F = keys[m].reset_index(drop=True), F[m]
    return keys, F


def book(k, programme="fixed", rho_book=rho):
    keys, F = windows(k, programme)
    b = keys.window_start.to_numpy()
    bk = dr.run_book(F, rho)
    L = bk["L"][:, -1]                              # PV at close of the Facility's net lending = loss
    psi = L.mean() / cover.annuity(k, rho)
    w = 1.0 / k
    cols = ["prem", "fac", "rep", "writeoff", "adv", "in_force"]
    out = pd.DataFrame(0.0, index=YEARS, columns=cols)
    for j in range(k):
        yr = b + j + 1
        for col, val in (("prem", np.full(len(b), psi)), ("fac", bk["fac"][:, j]),
                         ("rep", bk["rep"][:, j]), ("adv", bk["D"][:, j]),
                         ("in_force", np.ones(len(b)))):
            out[col] += pd.Series(w * val).groupby(yr).sum().reindex(YEARS, fill_value=0).to_numpy()
    wo = pd.Series(w * bk["D"][:, -1]).groupby(b + k).sum()
    out.loc[wo.index, "writeoff"] += wo.to_numpy()
    out["cf"] = out.prem - out.fac + out.rep
    out["reserve"] = accumulate(out.cf, rho_book)
    out["realised"] = accumulate(out.prem - out.writeoff, rho_book)   # ignores advances until written off
    end = int(b.max() + k)
    cohort = pd.DataFrame({"base": b, "iso3": keys.iso3, "loss": L, "prem_pv": psi * cover.annuity(k, rho),
                           "fac_pv": (bk["fac"] * (1 + rho) ** -np.arange(1, k + 1)).sum(1),
                           "rep_pv": (bk["rep"] * (1 + rho) ** -np.arange(1, k + 1)).sum(1)})
    return psi, out.loc[:end], cohort


def accumulate(cf, r):
    s, res = 0.0, []
    for c in cf:
        s = s * (1 + r) + c
        res.append(s)
    return np.array(res)


def metrics(k, programme="fixed", rho_book=rho):
    psi, o, coh = book(k, programme, rho_book)
    scale = o.in_force[o.in_force > 0].mean()        # average debt service in force
    s = pd.Series(o.reserve / scale, index=o.index)
    t = s.idxmin()
    neg = s[s < 0]
    first = int(neg.index.min()) if len(neg) else None
    back = s[(s.index > t) & (s >= 0)].index.min()
    back = None if pd.isna(back) else int(back)
    disc = (1 + rho_book) ** -(o.index - 1985)
    npv = float((o.cf * disc).sum())
    prem_pv = float((o.prem * disc).sum())
    by_cohort = coh.groupby("base")[["loss", "prem_pv"]].mean()
    lr = by_cohort.loss / by_cohort.prem_pv           # cohort loss ratio
    return dict(k=k, psi=psi, end=int(o.index.max()), trough=s.min(), trough_year=int(t),
                first_neg=first, back_above=back, end_reserve=float(s.iloc[-1]),
                trough_in_prem_years=s.min() / (psi * 1.0),   # years of premium income on the in-force book
                peak_adv=float((o.adv / scale).max()),
                realised_trough=float((o.realised / scale).min()),
                within_cover_recovery=float(coh.rep_pv.sum() / coh.fac_pv.sum()),
                psi_calendar=psi * (1 - npv / prem_pv),
                lr_sd=float(lr.std()), lr_ac1=float(lr.autocorr()),
                lr_first_half=float(lr.loc[:1997].mean()), lr_second_half=float(lr.loc[1998:].mean()))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    for prog in ("fixed", "going"):
        t = pd.DataFrame([metrics(k, prog) for k in (1, 2, 3, 5, 8, 10, 15)])
        print(f"===== programme: {prog}")
        print(t.round(3).to_string(index=False))
