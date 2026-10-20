# Moneyness, and the case for two triggers

*Companion to `notation_review_20260916.md` — proposal, not yet in the draft*

Two things. §1–§2 restate the Facility as an average-rate put and make the DSCR assumption a statement about **moneyness** rather than an apology. §3–§6 take up the separate-triggers idea: an advance trigger and an escrow trigger with a wedge between them, absorbed by the project's own buffer. It turns out to be standard, to be cheap, and to have one structural constraint that decides how wide the wedge can be. §7 records the fixing-count decision that every number here rests on.

All notation follows the migrated cells: window $w=(i,\underline{t})$, maturity $\bar{t}=\underline{t}+n$, sums $\sum_{t=\underline{t}+1}^{\bar{t}}$ with discount exponent $t-\underline{t}$.

---

## 1. The Facility is an average-rate put, and the strike is the DSCR

Write the annuity factor as what it is, a sum of discount factors, and normalise:

$$
A_{n,\rho}=\sum_{k=1}^{n}(1+\rho)^{-k},
\qquad
\omega_t=\frac{(1+\rho)^{-(t-\underline{t})}}{A_{n,\rho}},
\qquad
\sum_{t=\underline{t}+1}^{\bar{t}}\omega_t=1 .
$$

The weights are a probability distribution over the tenor, so

$$
V_w=\sum_{t=\underline{t}+1}^{\bar{t}}\omega_t\left(\frac{X_{i,t}}{X_{i,\underline{t}}}-1\right)
=\frac{\bar{X}^{\,\omega}_{w}}{X_{i,\underline{t}}}-1,
\qquad
\bar{X}^{\,\omega}_{w}\equiv\sum_t\omega_t X_{i,t},
$$

and therefore

$$
L_w=D\max(-V_w,0)=\frac{D}{X_{i,\underline{t}}}\max\!\big(X_{i,\underline{t}}-\bar{X}^{\,\omega}_{w},\,0\big).
$$

> **The Facility is short $D/X_{i,\underline{t}}$ arithmetic average-rate puts on $X$, struck at the level of $X$ at financial close, with annual fixings and discount-factor averaging weights.**

### Moneyness *is* the DSCR

Let $d\equiv\mathrm{DSCR}_{\underline{t}}=\mathrm{CF}^{\$}_{w,\underline{t}}/\bar\delta$ be the coverage the deal is actually sized to. Then realised coverage in year $t$ is

$$
c_{w,t}\;\equiv\;\frac{\mathrm{CF}^{\$}_{w,t}}{\bar\delta}\;=\;d\,\frac{X_{i,t}}{X_{i,\underline{t}}},
$$

the project is short of cash exactly when $c_{w,t}<1$, i.e. when $X_{i,t}<X_{i,\underline{t}}/d$, and

$$
L_w=\frac{D\,d}{X_{i,\underline{t}}}\max\!\Big(\frac{X_{i,\underline{t}}}{d}-\bar{X}^{\,\omega}_{w},\;0\Big)
\;=\;D\max\!\Big(1-\frac{d\,\bar{X}^{\,\omega}_{w}}{X_{i,\underline{t}}},\;0\Big).
$$

So $d$ is the moneyness, and nothing else:

| Object in the draft | Derivatives statement |
|---|---|
| Underlying | $X_{i,t}=P_{i,t}/S_{i,t}$, the dollar unit-revenue index |
| Strike $K$ | $X_{i,\underline{t}}/d$ |
| $\mathrm{DSCR}_{\underline{t}}=1$ | The put is struck **at-the-money-spot** |
| $\mathrm{DSCR}_{\underline{t}}=1.20$ | Struck **16.7% out-of-the-money**; notional grows $\propto d$, strike falls $\propto 1/d$, and $\max(1-d\,\bar X^\omega/X_{\underline t},0)$ is decreasing in $d$ |
| The tilt (§2 of the notation review) | The forward on $X$ sits above spot, so the put is also **out-of-the-money-forward** |
| Averaging window, fixings | The annual observation dates $t=\underline{t}+1,\dots,\bar{t}$ |
| Notional | $D\,d/X_{i,\underline{t}}$ baskets |
| Short the put | The Facility. The project is long it. |

This is the cleanest available fix for the weakest sentence in cell 5. "Without loss of generality, since the result is only strengthened if $\mathrm{DSCR}_t>1$" is currently an assertion. As a moneyness statement it is a one-line proof: raising $d$ moves the strike down and the payoff $\max(1-d\,\bar{X}^{\,\omega}_w/X_{i,\underline{t}},0)$ is monotonically decreasing in $d$, so $\mathrm{DSCR}_{\underline{t}}=1$ is the worst case and every real deal is cheaper to cover.

> **Drop-in replacement for the closing paragraph of cell 5.**
>
> Project finance structures usually require a DSCR above 120% as a buffer against the other risks the cash flows carry. Setting $\mathrm{DSCR}_{\underline{t}}=1$ is therefore conservative rather than restrictive. Writing $d=\mathrm{DSCR}_{\underline{t}}$, coverage in year $t$ is $c_{w,t}=d\,X_{i,t}/X_{i,\underline{t}}$ and the Facility's terminal exposure is $D\max\!\big(1-d\,\bar{X}^{\,\omega}_w/X_{i,\underline{t}},0\big)$, which is decreasing in $d$: in option terms, $d$ is the moneyness of the strike, and $d=1$ is the at-the-money case. Any project sized to a real covenant is struck out of the money and costs strictly less to cover.

### One consequence worth stating

Under a driftless random walk the variance of an arithmetic average over $n$ fixings is roughly $\sigma^2 n/3$, not $\sigma^2 n$. **Averaging suppresses volatility**, and a material part of the affordability result is that mechanical effect rather than mean reversion. Better to name it and separate it from the mean-reversion claim than to let a referee find it. It also sets up §6 below: the wedge is the one part of the structure that does *not* get the averaging discount.

---

## 2. Two triggers, and what the wedge does to the algebra

Currently one threshold does two jobs: it decides when the Facility advances cash, and it decides when the project sweeps surplus into escrow. Split them.

Let $\theta^{a}\le\theta^{e}$ and define the Facility by

- **advance (drawing):** when $c_{w,t}<\theta^{a}$, the Facility advances $\bar\delta(\theta^{a}-c_{w,t})$;
- **sweep (escrow):** when $c_{w,t}>\theta^{e}$, the project escrows $\bar\delta(c_{w,t}-\theta^{e})$;
- **the band $\theta^{a}\le c_{w,t}\le\theta^{e}$:** nothing moves. The project's own buffer — DSRA, cash trap, working capital — carries it.

The current design is $\theta^{a}=\theta^{e}=1$. The terminal net balance per unit of debt becomes

$$
B_w=\sum_{t=\underline{t}+1}^{\bar{t}}\omega_t\Big[(c_{w,t}-\theta^{e})^{+}-(\theta^{a}-c_{w,t})^{+}\Big],
\qquad L_w=D\max(-B_w,0).
$$

### Why the single trigger gives an Asian option and two triggers do not

With $\theta^{a}=\theta^{e}=\theta$ the bracket collapses, because $(x)^{+}-(-x)^{+}=x$, to the linear $c_{w,t}-\theta$. Linearity is the whole trick: it lets the sum pass through to the average, which is why the structure is an option on the average rather than a sum of options. Separate the triggers and the per-fixing payoff is a **collar** — slope 1, slope 0, slope 1 — and linearity is gone.

The exact decomposition is clean. Since $f(c)=(c-\theta^{e})^{+}-(\theta^{a}-c)^{+}=(c-\theta^{e})+(\theta^{e}-c)^{+}-(\theta^{a}-c)^{+}$,

$$
B_w=\underbrace{\Big(\bar{c}^{\,\omega}_{w}-\theta^{e}\Big)}_{\text{Asian core, struck at }\theta^{e}}
\;+\;\underbrace{\sum_{t}\omega_t\Big[(\theta^{e}-c_{w,t})^{+}-(\theta^{a}-c_{w,t})^{+}\Big]}_{\text{strip of per-fixing put spreads, the retained band}} ,
$$

with $\bar{c}^{\,\omega}_{w}=\sum_t\omega_t c_{w,t}$. The second term is the project's retention, credited back to the Facility, and each summand lies in $[0,\theta^{e}-\theta^{a}]$.

> **The wedge = Asian put struck at the sweep trigger, plus a strip of vanilla put spreads of width $\theta^{e}-\theta^{a}$.** The strip is priced fixing by fixing, so it is the one component that sees dispersion *within* the tenor rather than only the tenor average — it does not inherit the $\sigma^2 n/3$ discount.

### A sandwich bound you can compute with the code you already have

Because each put spread is bounded by $[0,\theta^{e}-\theta^{a}]$,

$$
\bar{c}^{\,\omega}_{w}-\theta^{e}\;\le\;B_w\;\le\;\bar{c}^{\,\omega}_{w}-\theta^{a},
\qquad\text{hence}\qquad
\Psi^{(\theta^{a})}\;\le\;\Psi\;\le\;\Psi^{(\theta^{e})},
$$

where $\Psi^{(\theta)}$ is the single-trigger premium at threshold $\theta$. And because $V_w=\bar{c}^{\,\omega}_w-1$ exactly, that single-trigger premium is a pure shift of the residuals you already store:

$$
\Psi^{(\theta)}=\mathbb{E}_N\big[\max(\theta-1-V_w,\,0)\big].
$$

No new machinery: `compute_terminal_residuals_wdi` output plus one line brackets the premium for any wedge. The exact figure needs a per-fixing loop, which is a dozen lines.

---

## 3. What the wedge is worth

Computed on the pipeline as it now stands — `years` = $n$ = 15, window of $n+1$ observations — so these sit directly alongside the draft's revised 6.9% Nigeria and 2.03% pooled. Premia are shares of annual debt service; $\Delta r$ is the amortising-loan margin equivalent.

**Pooled, 668 rolling 15-year windows, 50 countries, from 1995**

| $\theta^{a}$ | $\theta^{e}$ | $\Psi$ | bracket $[\Psi^{(\theta^a)},\Psi^{(\theta^e)}]$ | $\Delta r$ | P(loss) | drawing years per window |
|---|---|---|---|---|---|---|
| 1.000 | 1.000 | **2.03%** | — | 30.0bp | 16.0% | 3.54 |
| 0.975 | 1.000 | 1.75% | [1.67%, 2.03%] | 25.8bp | 14.2% | 3.04 |
| 0.950 | 1.000 | **1.52%** | [1.38%, 2.03%] | 22.4bp | 12.9% | 2.63 |
| 0.900 | 1.000 | 1.14% | [0.97%, 2.03%] | 16.8bp | 10.8% | 1.86 |
| 0.950 | 1.050 | 1.63% | [1.38%, 3.04%] | 24.1bp | 15.6% | 2.63 |
| 1.000 | 1.050 | 2.21% | [2.03%, 3.04%] | 32.6bp | 19.8% | 3.54 |

**Nigeria, 25 rolling windows from 1985**

| $\theta^{a}$ | $\theta^{e}$ | $\Psi$ | $\Delta r$ | P(loss) |
|---|---|---|---|---|
| 1.000 | 1.000 | **6.92%** | 101bp | 16.0% (4/25) |
| 0.950 | 1.000 | 6.22% | 91bp | 16.0% |
| 0.900 | 1.000 | 5.53% | 81bp | 16.0% |

Three readings:

1. **A five-point wedge on the advance side is worth a quarter of the pooled premium** — 2.03% → 1.52%, 30.0bp → 22.4bp — for a retention the project barely notices. That is a large return on a small structural concession.
2. **Direction is everything.** A wedge below the sweep trigger ($\theta^{a}<\theta^{e}=1$) is a per-fixing deductible and lowers the premium. A wedge above the drawing trigger ($\theta^{a}=1<\theta^{e}$) gives up recoveries in good years and *raises* it: 2.03% → 2.21%. The payoff comparison is pathwise, so this is a theorem, not a finding. The interesting design is the first.
3. **Nigeria barely moves.** The four losing windows are deep — they straddle the 1999 unification — so shaving 5 points off each year's advance does little. P(loss) does not move at all. The wedge is an efficiency device for the ordinary case, not protection against the tail, and the draft should say so before a reader hopes otherwise.

---

## 4. Is it standard? Yes, in four separate literatures

| Construct | Where it lives | What it does | Fit |
|---|---|---|---|
| **Distribution lock-up trigger above the event-of-default trigger** | project finance credit agreements; lock-up typically 0.10–0.15x above default, e.g. 1.20x vs 1.10x | two DSCR thresholds with a band in which cash is trapped but nothing is cured | exact — this is the same object, on the same ratio |
| **DSRA**, ~6 months of debt service, lender-controlled | project finance | drawn to cure a covenant shortfall without an event of default | *this is the buffer the wedge hands the work to* |
| **Cash-sweep trigger vs lock-up trigger** | leveraged and project finance | surplus shared only above a threshold distinct from the distress threshold | exact analogue of splitting advance from sweep |
| **Corridor SIR** ("bikini deductible") | (re)insurance | an insured-retained layer sitting *between* a primary layer and the excess layer | exact — the band is a corridor retention |
| **Franchise deductible** | insurance | nothing below the threshold, then payment *in full* — as against an ordinary deductible, which is retained at every loss size | the alternative shape for the wedge (see §6) |
| **Aggregate / annual aggregate deductible** | reinsurance | retention defined over a period rather than per occurrence | the DSRA-compatible shape (see §6) |
| **Collar** (long put at $K_p$, short call at $K_c$) | options | flat payoff between two strikes | exact payoff identity with $f(c)$ above |
| **Threshold + Minimum Transfer Amount** | ISDA CSA collateral | a no-transfer band to suppress trivial and churning flows | the operational motive, stated in derivatives language |
| **Liquidity extension guarantee** | GuarantCo and the DFI market | back-up liquidity for operating-phase revenue shortfalls | precedent for the liquidity leg of the instrument itself |
| **IBRD partial risk guarantee on LC draws** | World Bank | guarantee standing behind a revolving letter of credit drawn on offtaker default | precedent for reversible, revolving cover |

So the answer for the draft is: the wedge is not an innovation and should not be presented as one. It is the project-finance lock-up band, with the Facility rather than the equity distribution sitting on the far side of it. Saying so is a credibility gain, not a loss — it means the structure can be documented with clauses a project-finance lawyer already writes.

> **One term to avoid.** "Dual trigger" is taken. In insurance it means cover contingent on a *second, non-insurance* contingency — a hazard loss plus, say, a commodity price condition. Using it for two thresholds on one variable will be read as something else entirely.

---

## 5. Naming

| Threshold | Name | Why |
|---|---|---|
| $\theta^{a}$ | **drawing trigger** | already the review's term; "drawing" is the finance register for a reversible utilisation and carries no loss content |
| $\theta^{e}$ | **sweep trigger** | cash sweep is the standard project-finance name for surplus diverted from equity |
| $[\theta^{a},\theta^{e}]$ | **retained corridor**, or **the project's retention** | "corridor" imports the (re)insurance meaning precisely; "band" is vaguer but reads more easily in prose |
| the whole design | **two-trigger** or **split-trigger** | never "dual trigger" |

In the insurance register the corridor is the insured's retention and the escrow remains the **experience account**; in the finance register it is the project's first-loss layer ahead of the facility.

---

## 6. The constraint that sets the width: the DSRA is a stock, the wedge is a flow

This is the part that decides whether the idea survives contact with a term sheet.

The wedge asks the project to fund $\bar\delta(\theta^{e}-c_{w,t})$ in **every** year the path sits in the corridor. The DSRA is a fixed stock — conventionally six months of debt service, $0.5\bar\delta$ — replenished out of subsequent cash flow. A corridor that binds for one year is trivially absorbed. A corridor that binds for eight consecutive years is a different instrument.

Cumulative retained shortfall over the tenor, in years of debt service, present-valued:

| $\theta^{a}$ (with $\theta^{e}=1$) | pooled mean | p90 | worst window |
|---|---|---|---|
| 0.975 | 0.06 | 0.17 | 0.26 |
| 0.950 | 0.11 | 0.32 | 0.52 |
| 0.900 | 0.19 | 0.56 | 1.04 |

Per-year retention is capped at $(\theta^{e}-\theta^{a})\bar\delta$ by construction — 5% or 10% of one payment — so no single year is ever a problem. The cumulative column is where the constraint bites, and it is sharp:

> **A five-point corridor is about DSRA-sized; a ten-point corridor is twice it.** At $\theta^{a}=0.95$ the worst window in the whole panel demands 0.52 years of debt service cumulatively — essentially exactly a six-month DSRA, and that is on the deliberately harsh assumption of no replenishment at all across fifteen years, so in practice it clears comfortably. At $\theta^{a}=0.90$ the worst window demands 1.04 years, double the reserve — and it demands it in precisely the windows where the project is already stressed, so assuming replenishment there is assuming away the problem.

That gives a defensible default: **$\theta^{a}=0.95$, $\theta^{e}=1.00$**, a five-point corridor, which buys a 25% premium reduction against a retention the standard reserve covers, to within rounding, even in the worst historical window with no replenishment.

### The alternative shape

If you want a wider retention without the stock/flow mismatch, define the corridor as an **aggregate deductible** rather than a per-year one: the Facility advances nothing until cumulative shortfall over the tenor exceeds $\Delta\bar\delta$, then advances in full. That is a stock against a stock, so it sizes directly against the DSRA, and it is exactly the reinsurance aggregate-deductible construct. It costs the sandwich bound — the payoff is no longer separable across fixings — and it introduces a path-dependent state variable, so the Monte Carlo in `new_event_analysis.ipynb` would have to carry it. Worth a robustness row, probably not the base case.

---

## 7. Resolved: the fixing count, and what it moved

*Settled 2026-09-16. Recorded here because every figure above and in the draft depends on it.*

There were two live conventions. The paper said a window runs $t=\underline{t},\dots,\bar{t}$ with $\bar{t}=\underline{t}+n$, $n$ live fixings over $n+1$ observations, and $R_{w,\underline{t}}=0$ outside the sum. The code took $n=15$ **observations** at offsets $0,\dots,14$ and discounted them at exponents $1,\dots,15$, putting the identically-zero close-year return *inside* the sum at the heaviest weight — 14 live fixings over 15 years, which is why Nigeria had 26 windows and not 25.

**The paper's convention was adopted, and the code moved to match.** `years` is now the tenor $n$ everywhere — in `compute_terminal_residuals_wdi`, in `source/data_analysis_functions.py::compute_terminal_residuals` and `::compute_indexed_residuals` — and a window spans $n+1$ annual observations. The default stays 15. One number, one meaning, in the paper and in the code.

The decisive argument was not aesthetic. Under the old convention $A^{-1}(1+\rho)^{-1} \approx 9.2\%$ of the averaging weight rested on a return that cannot move, which made the first debt-service year riskless by assumption — a devaluation immediately after financial close, not a rare event, was invisible. That single dead fixing shrank $|V|$ by roughly 9% toward zero and systematically understated the premium.

### What moved

| | old | new |
|---|---|---|
| Pooled windows | 718 | 668 (one fewer per country; no country dropped) |
| Pooled $\mathbb{E}[V]$ | +0.243 | +0.293 |
| Pooled expected loss | 1.95% | 2.03% |
| Pooled P(loss) | 17.8% | 16.0% |
| Pooled $\Delta r$ | 28.6bp | **30.0bp** |
| Pooled $\Psi/D$ | 18.7bp | 19.6bp |
| Nigeria windows (from 1985) | 26 | 25 |
| Nigeria $\Psi$ | 6.18% | 6.92% |
| Nigeria gains range | 17%–136% | 19%–150% |
| Nigeria worst window | −55% | −59% |
| Nigeria $\Delta r$ (pooled sample) | 145bp | 166bp |
| Full-indexation baseline, monthly grid | 17.5bp | 18.1bp |
| Full-indexation baseline, annual grid | 18.7bp | 19.6bp |
| Worst single-year shortfall | −75.4% | −75.4% (unchanged) |
| Kenya expected loss | 0 | 0 (unchanged) |

Two headline claims need rewording rather than renumbering. "Under 30bp pooled" is now exactly 30.0bp, so it has become "about 30bp". And the abstract's "under 150 basis points for the worst single country" was never right on either convention: Nigeria is the worst *named* country at 145bp old / 166bp new, but Libya (318bp), the DRC (198bp) and the Gambia (168bp) all price above it. The draft now says "about 165 basis points for Nigeria"; whether to quote a genuine worst-country figure, exclude thin-coverage countries, or quote a percentile is a separate decision.

### Two things cleared in the same pass

`compute_terminal_residuals` in `source/data_analysis_functions.py` normalised by `af**2` rather than `af` — the squared-annuity leftover flagged in §7 of the notation review, which returned $V/A$, about a tenth of the intended quantity. Now fixed. Fed the same series, it and `compute_terminal_residuals_wdi` agree to machine zero across all 1055 windows, so the "mirror" claim in its docstring is finally true. The MFMOD-path notebooks (`consolidated_currency_analysis`, `SolvencyAnalysis`, `SolvencyInverse`, `regime_and_diversification_analysis`, `nominal_vs_real_comparison`) each read `net_pv_by_debt_stock` straight through with no compensating multiplication, so every figure they stored scales up by $A_{15}=10.38$ and their outputs need regenerating.

The estimator definitions also moved to the top of `paper_draft.ipynb`. They had sat at cell 21 while cells 10 and 11 called them, so the notebook could not execute top to bottom at all — which is why its stored outputs came from an out-of-order run and why the `start_year` leak from the windows chart had gone unnoticed. It now runs clean in order.

---

## 8. Open questions

1. **Is the corridor a covenant or a contract term?** If the drawing trigger is $0.95$ while the lenders' event-of-default DSCR is $1.05$, the Facility does not advance until the project is already in breach — the cover fails at exactly the moment it is sold to prevent. The corridor has to sit *above* the default trigger, which means the relevant band is $[\theta^{a},\theta^{e}]$ with $\theta^{a}>\mathrm{DSCR}^{\text{default}}$, and in a real deal sized to $d=1.2$ there is ample room. Under the paper's $d=1$ normalisation there is none. This may be the strongest argument for carrying $d$ explicitly through §1 rather than normalising it away.
2. **Does the sweep trigger want to be above 1 after all?** §3 shows $\theta^{e}>1$ raises the premium. But it also leaves the project holding its own surplus, which is what a sponsor will ask for, and it may be what makes the product sellable. If so, it should be priced and quoted as an option the project buys, not absorbed silently.
3. **Interest on the corridor.** Advances outside the corridor accrue funding cost; retained amounts inside it do not. As §6 of the notation review notes, $\Psi$ prices the option and not the carry on the liquidity leg at all. The wedge shrinks the liquidity leg — drawing years fall from 3.5 to 2.6 per window — so it improves the unpriced term as well. Worth one sentence once that leg is scoped.
4. **Does the corridor change the tilt decomposition?** The Asian core is struck at $\theta^{e}$ and carries the tilt as before; the put-spread strip is per-fixing and its exposure to $P^{*}$ has not been checked. Probably second order, but it is not zero, and the "trigger on $X$, price on $\theta$" proposal interacts with it.

---

**Sources**

- [Distribution lock-up in project finance · Stonewake](https://stonewake.ai/blog/distribution-lock-up)
- [What Is a DSRA? Meaning & Project Finance Guide · Pivotal180](https://pivotal180.com/what-is-a-dsra-what-it-is-and-how-it-works-in-project-finance/)
- [What Is the Debt Service Coverage Ratio (DSCR) in Project Finance? · Forvis Mazars](https://financialmodelling.forvismazars.com/resources/debt-service-coverage-ratio-dscr/)
- [The Corridor Self-Insured Retention · IRMI](https://www.irmi.com/articles/expert-commentary/the-corridor-self-insured-retention)
- [Franchise deductible · IRMI](https://www.irmi.com/term/insurance-definitions/franchise-deductible)
- [Dual trigger insurance · Wikipedia](https://en.wikipedia.org/wiki/Dual_trigger_insurance)
- [Products and Benefits · GuarantCo](https://guarantco.com/products-and-benefits/)
- [World Bank guarantees for private projects · Norton Rose Fulbright](https://www.projectfinance.law/publications/2016/april/world-bank-guarantees-for-private-projects)
- [IBRD Financial Products: Credit Enhancement · World Bank Treasury](https://treasury.worldbank.org/en/about/unit/treasury/ibrd-financial-products/creditenhancement)
