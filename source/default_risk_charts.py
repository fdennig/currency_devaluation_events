"""Charts for default_risk_20261004.md. Writes PNGs to output/.

    .venv/Scripts/python.exe source/default_risk_charts.py
"""

import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cover  # noqa: E402
import default_risk as dr  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output"
N, RHO, R = 15, 0.05, 0.10
INK, BLUE, ORANGE, RED, GREEN, GREY, PURPLE = (
    "#333333", "#4c78a8", "#e8820c", "#c0392b", "#2e8b57", "#9a9a9a", "#8c6bb1")


@alt.theme.register("paper", enable=True)
def _paper_theme():
    return {"config": {
        "background": "white", "view": {"strokeWidth": 0},
        "title": {"color": INK, "anchor": "start", "fontSize": 14},
        "axis": {"labelColor": INK, "titleColor": INK, "tickColor": INK,
                 "domainColor": INK, "gridColor": "#eeeeee"},
        "legend": {"labelColor": INK, "titleColor": INK, "orient": "bottom"},
        "text": {"color": INK}}}


def save(chart, name):
    chart.save(str(OUT / f"{name}.png"), scale_factor=2.0)
    print("wrote", name)


def main():
    o = dr.analysis(n=N, rho=RHO, r=R, verbose=False)
    keys, F, book = o["keys"], o["F"], o["book"]
    L, psi = book["L"], o["psi"]
    k = np.arange(1, N + 1)
    A = np.array([cover.annuity(t, RHO) for t in k])

    # ---- fig 1: truncated curve, pool and fixed cohort -----------------------
    coh = (keys.window_start <= 1999).to_numpy()
    rows = []
    for label, m in (("pool: closes 1985-2009", np.ones(len(keys), bool)),
                     ("fixed cohort: closes 1985-1999", coh)):
        th = L[m].mean(0)
        p_n = th[-1] / A[-1]
        for t in k:
            rows.append({"sample": label, "tau": int(t), "psi_tau": th[t - 1] / A[t - 1],
                         "psi_n": p_n, "gap": th[t - 1] - p_n * A[t - 1]})
    cur = pd.DataFrame(rows)
    col = alt.Color("sample:N", scale=alt.Scale(range=[BLUE, ORANGE]), title=None)
    x = alt.X("tau:Q", title="τ, year in which the cover stops", scale=alt.Scale(domain=[1, 15]),
              axis=alt.Axis(values=list(k)))
    top = (alt.Chart(cur).mark_line(point=True).encode(
               x=x, y=alt.Y("psi_tau:Q", title="Ψ_τ = Θ_τ / A_τ", axis=alt.Axis(format=".1%"),
                            scale=alt.Scale(zero=False)), color=col)
           + alt.Chart(cur).mark_rule(strokeDash=[4, 4]).encode(y="mean(psi_n):Q", color=col)
           ).properties(width=520, height=220,
                        title="Premium that would break even on windows stopped at τ")
    bot = (alt.Chart(cur).mark_bar(opacity=0.75).encode(
               x=alt.X("tau:O", title="τ"), xOffset="sample:N",
               y=alt.Y("gap:Q", title="Θ_τ − Ψ·A_τ  (yrs of debt service)"), color=col)
           ).properties(width=520, height=160,
                        title="Facility shortfall if every project stopped at τ (premium priced at maturity)")
    save(alt.vconcat(top, bot).resolve_scale(color="shared"), "default_risk_fig1_truncated")

    # ---- fig 2: two windows from the draft, year by year ---------------------
    prem = psi * ((1 + RHO) ** k - 1) / RHO
    rows = []
    for iso, y, name in (("DZA", 1998, "Algeria, close 1998 (bridge)"),
                         ("NGA", 1998, "Nigeria, close 1998 (terminal loss)")):
        i = keys[(keys.iso3 == iso) & (keys.window_start == y)].index[0]
        for t in k:
            rows += [{"w": name, "tau": int(t), "series": "loss if stopped at τ:  L_τ", "v": L[i, t - 1]},
                     {"w": name, "tau": int(t), "series": "premiums collected:  Ψ·A_τ", "v": psi * A[t - 1]},
                     {"w": name, "tau": int(t), "series": "experience account:  B_τ (PV)",
                      "v": book["B"][i, t - 1] * (1 + RHO) ** -t}]
    ex = pd.DataFrame(rows)
    sc = alt.Color("series:N", title=None,
                   scale=alt.Scale(domain=["loss if stopped at τ:  L_τ", "premiums collected:  Ψ·A_τ",
                                           "experience account:  B_τ (PV)"],
                                   range=[RED, GREEN, GREY]))

    def panel(w):
        d = ex[ex.w == w]
        return (alt.Chart(d[d.series.str.startswith("exp")]).mark_bar(opacity=0.35).encode(
                    x=alt.X("tau:O", title="τ"), y=alt.Y("v:Q", title="years of debt service, PV at close"),
                    color=sc)
                + alt.Chart(d[~d.series.str.startswith("exp")]).mark_line(point=True).encode(
                    x="tau:O", y="v:Q", color=sc)).properties(width=300, height=230, title=w)
    save(alt.hconcat(*[panel(w) for w in ex.w.unique()]).resolve_scale(y="independent"),
         "default_risk_fig2_examples")

    # ---- fig 3: wrong-way stresses -------------------------------------------
    ww = o["wrong_way"]
    st = ww[ww.state != "adversarial"].copy()
    st["m"] = st.m.map(lambda v: "∞" if np.isinf(v) else f"{int(v)}")
    adv = ww[ww.state == "adversarial"]
    charts = []
    for h in (0.01, 0.03, 0.05):
        d = st[st.h == h]
        a = float(adv.loc[adv.h == h, "uplift"].iloc[0])
        charts.append(
            (alt.Chart(d).mark_line(point=True).encode(
                x=alt.X("m:O", sort=["1", "3", "10", "∞"], title="m, hazard ratio stressed / unstressed"),
                y=alt.Y("uplift:Q", title="ψ* / Ψ − 1", axis=alt.Axis(format="+.0%"),
                        scale=alt.Scale(domain=[-0.5, 0.75])),
                color=alt.Color("state:N", title="stressed state",
                                scale=alt.Scale(range=[BLUE, ORANGE, PURPLE])))
             + alt.Chart(pd.DataFrame({"y": [a]})).mark_rule(color=RED, strokeDash=[5, 3]).encode(y="y:Q")
             + alt.Chart(pd.DataFrame({"y": [a], "t": [f"adversarial timing {a:+.0%}"]})).mark_text(
                 color=RED, align="left", dx=-80, dy=-7).encode(y="y:Q", text="t:N")
             + alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=INK).encode(y="y:Q")
             ).properties(width=200, height=240, title=f"pool-average hazard h = {h:.0%}"))
    save(alt.hconcat(*charts).resolve_scale(color="shared"), "default_risk_fig3_wrong_way")

    # ---- fig 4: the rates ----------------------------------------------------
    ind, adr = o["independent"], o["advance_rate"]
    rr = pd.concat([
        pd.DataFrame({"h": ind.h, "rate": ind.d_eff, "series": "annuitisation rate, independent default"}),
        pd.DataFrame({"h": adv.h.values, "rate": adv.d_eff.values, "series": "annuitisation rate, adversarial timing"}),
        pd.DataFrame({"h": adr.h, "rate": adr["c_neg*"], "series": "rate on advances instead of premium"}),
        pd.DataFrame({"h": ind.h, "rate": ind.lender_rate, "series": "lender to the project, LGD 100%"}),
    ])
    rules = pd.DataFrame({"y": [RHO, R], "t": ["ρ = 5%  Facility", "r = 10%  project"]})
    save((alt.Chart(rr).mark_line(point=True).encode(
              x=alt.X("h:Q", title="annual project default hazard h",
                      axis=alt.Axis(format=".0%", values=list(ind.h))),
              y=alt.Y("rate:Q", title="break-even rate", axis=alt.Axis(format=".0%")),
              color=alt.Color("series:N", title=None,
                              legend=alt.Legend(columns=2, labelLimit=400),
                              scale=alt.Scale(domain=list(rr.series.unique()),
                                              range=[BLUE, RED, ORANGE, GREY])))
          + alt.Chart(rules).mark_rule(strokeDash=[3, 3], color=INK).encode(y="y:Q")
          + alt.Chart(rules).mark_text(align="left", x=5, dy=-7).encode(y="y:Q", text="t:N")
          ).properties(width=520, height=320,
                       title="What rate does the deferred premium really need?"),
         "default_risk_fig4_rates")

    # ---- fig 5: liquidity-leg exposure by year --------------------------------
    pr = o["exposure_by_year"]
    lp = pr.melt(id_vars="k", value_vars=["naive", "D", "prem", "net"])
    lab = {"naive": "naive: every drawing a loan", "D": "Facility deficit D_k",
           "prem": "premiums collected (FV)", "net": "deficit net of premiums"}
    lp["series"] = lp.variable.map(lab)
    save(alt.Chart(lp).mark_line(point=True).encode(
             x=alt.X("k:O", title="year of the tenor"),
             y=alt.Y("value:Q", title="mean over windows, years of debt service"),
             color=alt.Color("series:N", title=None, sort=list(lab.values()),
                             scale=alt.Scale(range=[GREY, RED, GREEN, PURPLE])))
         .properties(width=520, height=280, title="Credit exposure on the liquidity leg, pool average"),
         "default_risk_fig5_exposure")

    # ---- fig 6: what moves the price ----------------------------------------
    lap = o["lapse"]
    bars = [("base: no default, no lapse", o["dr_at_rho"], "base")]
    bars += [(f"independent default h = {h:.0%}", v, "default") for h, v in o["dr_star"].items()
             if h in (0.01, 0.05)]
    bars += [("upper bound, any independent default law",
              cover.equivalent_rate(o["curve"].psi.max(), R, N) - R, "default")]
    bars += [(f"adversarial timing h = {h:.0%}", cover.equivalent_rate(p, R, N) - R, "adversarial")
             for h, p in zip(adv.h, adv["psi*"]) if h in (0.01, 0.03)]
    bars += [("annuitise at r instead of ρ", o["dr_at_r"], "convention")]
    bars += [(f"lapse: escrow ≥ {x:g} yrs, {p:.0%}/yr", v, "lapse")
             for x, p, v in zip(lap["escrow >="], lap["p/yr"], lap.delta_r)]
    bd = pd.DataFrame(bars, columns=["case", "dr", "kind"])
    bd["bp"] = 1e4 * bd.dr
    save((alt.Chart(bd).mark_bar().encode(
              y=alt.Y("case:N", sort=None, title=None, axis=alt.Axis(labelLimit=400)),
              x=alt.X("bp:Q", title="Δr, bp on a 15-year amortising loan at r = 10%"),
              color=alt.Color("kind:N", title=None, scale=alt.Scale(
                  domain=["base", "default", "adversarial", "convention", "lapse"],
                  range=[INK, BLUE, RED, GREY, ORANGE])))
          + alt.Chart(bd).mark_text(align="left", dx=3).encode(
              y=alt.Y("case:N", sort=None), x="bp:Q", text=alt.Text("bp:Q", format=".0f"))
          ).properties(width=420, height=330, title="What each risk does to the margin quote"),
         "default_risk_fig6_margin")


if __name__ == "__main__":
    main()
