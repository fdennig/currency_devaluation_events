# Notation & terminology review

*Pricing Real Exchange Rate Cover for African Infrastructure Finance — markdown cells*

Four things below: a set of naming changes, the risk-layering that the notation should make visible, a comparison of the Facility against an average-rate (Asian) put, and a list of inconsistencies that are substantive rather than cosmetic.

---

## 1. $Q$ is not the real exchange rate

$Q_{i,t}=P_{i,t}/S_{i,t}$ is the nominal exchange rate deflated by *domestic* prices only. Getting to the real exchange rate requires dividing by the US price level as well. Cell 4 says this correctly — "equal to the real exchange rate times the USD price level" — and then the rest of the draft forgets it.

This is not pedantry, for two reasons. First, $Q$ and $q$ *are* the standard symbols for the real exchange rate in international macro, so using them for something else guarantees the misreading among exactly the readers you most want. Second, the choice to stop one deflation short is a deliberate design decision — the paper's core scoping argument — and it is currently invisible.

> **Proposal.** Rename the main series to $X_{i,t}=P_{i,t}/S_{i,t}$, with $x\equiv\ln X=p-s$. Reserve $\theta_{i,t}=X_{i,t}/P^{*}_{t}$ for the actual real exchange rate, used only in the pricing decomposition. Migration cost is one code line, one chart label, and eight markdown cells.

**In words.** $X$ translates a kWh into nominal USD: it is the **dollar unit-revenue index**. In technical passages, "domestically deflated exchange rate" is precise. What it must never be called is the real exchange rate.

Every current instance needs to change — including the title. *"Real Exchange Rate Cover"* describes cover on $\theta$; the product triggers on $X$.

|  Location  |                                                       Current                                                        |
|------------|----------------------------------------------------------------------------------------------------------------------|
| raw cell 0 | Title: "Pricing Real Exchange Rate Cover…"                                                                           |
| cell 2     | `# real exchange rate, USD per local basket`                                                                         |
| cell 3     | "the residual - real - currency risk"; "cyclicality of the real exchange rate"; "exposed to real exchange rate risk" |
| cell 4     | "A rise is a real *appreciation*" — true only if $\pi^{*}=0$                                                         |
| cell 8     | "rebalancing of the real exchange rate" ×2                                                                           |
| cell 13    | Section header: "The real exchange rate: measuring the risk the project actually bears"                              |

---

## 2. The risk layering, and who bears what

Deflating by domestic prices only is the right call, and the reason deserves to be stated rather than left implicit. There are three macro layers, and only one of them lacks a market:

|            Layer            |  Removed from the USD chain by   |                  Rests with                 |                                   How they handle it                                  |
|-----------------------------|----------------------------------|---------------------------------------------|---------------------------------------------------------------------------------------|
| Domestic inflation $\pi$    | Indexed tariff clause in the PPA | Consumer                                    | Nominal tariff escalation; real tariff flat                                           |
| US inflation $\pi^{*}$      | Nothing — never transferred      | **Lender**, short via a fixed nominal claim | Priced into the nominal coupon; hedged with liquid instruments in the ordinary course |
| Real exchange rate $\theta$ | Nothing — no market exists       | **The Facility**                            | Long-horizon capital; mean reversion over 5–10 years                                  |

The middle row is the one to state explicitly in the draft, in roughly these terms: *we deflate by domestic prices only, because the US inflation component of the exposure rests with the USD lender, who prices and hedges it in the ordinary course; the residual real exchange rate risk is what has no market.*

### Full allocation, with and without the Facility

**Panel A — borrower and lender only**

|                   Risk factor                   |  Consumer |       Project       |                 Lender                 |
|-------------------------------------------------|-----------|---------------------|----------------------------------------|
| Domestic inflation $\pi$ (nominal pass-through) | **bears** | —                   | —                                      |
| $X=P/S$ composite                               | —         | **long, unfloored** | **long, indirectly**                   |
| US inflation $\pi^{*}$                          | —         | —                   | **short**                              |
| Real exchange rate $\theta$                     | —         | **long**            | **long, indirectly**                   |
| Liquidity / technical default                   | —         | **bears in full**   | bears via covenant breach, refinancing |
| Ultimate credit loss                            | —         | bears to equity     | **bears beyond equity**                |

The lender's indirect $X$ exposure is the crux of the whole paper. A fixed nominal USD claim is only fixed if it gets paid; when $X$ falls below $X_{i,0}$ the borrower cannot service, so the lender is short a put on $X$ whether it wants one or not — it has sold currency protection without pricing it. That is precisely the induced offtaker risk cell 3 describes, and it is why the deal does not clear. Worth making this table the formal statement of that paragraph.

**Panel B — with the Facility**

|          Risk factor          |  Consumer |            Project             |   Lender  |           Facility           |
|-------------------------------|-----------|--------------------------------|-----------|------------------------------|
| Domestic inflation $\pi$      | **bears** | —                              | —         | —                            |
| $X=P/S$ composite             | —         | long, **floored at $X_{i,0}$** | —         | **short the floor**          |
| US inflation $\pi^{*}$        | —         | —                              | **short** | long, *via tilt*             |
| Real exchange rate $\theta$   | —         | long, floored                  | —         | **long** (dominant exposure) |
| Liquidity / technical default | —         | — (advances cover)             | —         | **bears, reversibly**        |
| Ultimate credit loss          | —         | bears to equity                | —         | **bears $D\max(-V_w,0)$**    |
| Facility counterparty risk    | —         | **new**                        | **new**   | —                            |

The transformation in one line: the lender's unpriced short put becomes the Facility's priced short put, and the project's unfloored long position becomes a floored one while keeping its upside.

Note the last row is a *new* risk, not a transferred one. The lender's insulation in Panel B is conditional on the Facility's solvency, which is why the "sufficiently long-term capital" claim in cell 3 is doing structural work and not merely economic work.

### The Facility is *almost*, but not exactly, long $\theta$ alone

Substituting $X_{t}/X_{0}=(\theta_{t}/\theta_{0})(P^{*}_{t}/P^{*}_{0})$ into $V_w$, and imposing Fisher on the discount rate so that $(1+\rho)^{-t}(P^{*}_{t}/P^{*}_{0})=(1+\rho^{r})^{-t}$, the US price level cancels from the numerator but not the denominator:

$$
V_w \;=\; \frac{1}{A_{n,\rho}}\sum_{t=1}^{n}(1+\rho^{r})^{-t}\,\frac{\theta_{i,t}}{\theta_{i,0}}\;-\;1
$$

Numerator purely real; denominator the *nominal* annuity factor, which shrinks as $\pi^{*}$ rises. So $V_w$ is increasing in US inflation. Holding $\theta$ perfectly flat and letting only $P^{*}$ run:

| $\pi^{*}$ | $V$ with $\rho$ fixed at 5% | $V$ with Fisher-consistent $\rho$ |
|---|---|---|
| 0% | +0.000 | +0.000 |
| 2.0% | +0.132 | +0.136 |
| 2.8% (1985–2024 realised) | **+0.192** | **+0.192** |
| 4.0% | +0.288 | +0.278 |

The exposure survives Fisher adjustment essentially unchanged, so it is not a discounting artefact. It is the **tilt**: revenue is real, debt service is nominal and level, so US inflation erodes the real burden of $\bar\delta$ across the tenor. The lender's loss is the borrower's gain, and the Facility — paying only when coverage is short — captures a slice of that gain as reduced payouts. Modigliani and Lessard named the effect in the 1975 mortgage context; it is why price-level-adjusted mortgages exist.

Practically: against reported window values of 17% to 136%, roughly 19 points of the positive side is tilt rather than real appreciation. This does not break the result — the four red windows are real and the 55% loss is real — but it inflates the measured cushion, and a referee will find it. Suggested handling: report $\Psi$ computed on $X$ and on $\theta$ side by side, and present the gap as the value of the tilt. That converts your strongest objection into a result, and costs one extra WDI series.

> **A design observation this exposes.** The drawing trigger is defined on $X$, one layer above the risk the Facility intends to underwrite, so $P^{*}$ enters the loss distribution even though nobody in the structure treats it as part of the risk transfer. Three options: leave it and disclose; move the trigger to $\theta$ (cleaner pricing, but the project can be cash-short on $X$ while $\theta$ reads flat, so the liquidity leg stops working); or **trigger on $X$, price on $\theta$**. The third looks right — drawings follow actual cash need, the premium is quoted against the real cycle, and the tilt shows up as an explicit credit.

---

## 3. Indexing and the estimator

The draft carries four subscripts on its central object. Cell 5 writes $V_{i,\underline{t},\bar{t},\rho}$; cell 12 escalates to $V_{i_j,\underline{t}_j,\bar{t}_j,\rho}$ inside a sum over $j\in\mathcal{J}$, with $i_j$ a country-lookup on a project index. Two of the four are global constants — $n=15$ and $\rho=0.05$ — and should be stated once as parameters, not carried as subscripts. The remaining two are the actual unit of observation.

> **Proposal.** Let a *window* be $w=(i,t_0)$: country $i$, financial close at $t_0$, maturity $t_0+n$. Let $\mathcal{W}$ be the pool and $N=|\mathcal{W}|$. Write $V_w$, $L_w$, $R_{w,t}$. This retires $j$, $\mathcal{J}$, $i_j$, $\underline{t}$ and $\bar{t}$ entirely.

### The estimator

Cell 12 has $\mathbb{E}[L_j]_{[j\in \mathcal{J}]}$ and $\hat{\mathbb{E}}[L_j]$. The bracketed index after the closing bracket is non-standard, and the hat is redundant once the sample size sits on the operator:

$$
\mathbb{E}_N[L_w] \;=\; \frac{1}{N}\sum_{w\in\mathcal{W}} L_w, \qquad N=|\mathcal{W}|
$$

Reserve unadorned $\mathbb{E}[\cdot]$ for the population target. The two then read as target and estimator rather than as two spellings of one thing.

> **Weighting.** $\mathbb{E}_N$ over all windows weights each country by its number of windows, so countries with longer WDI coverage dominate the pooled premium. Equal country weighting gives
> $$
> \frac{1}{|\mathcal{C}|}\sum_{i\in\mathcal{C}}\frac{1}{N_i}\sum_{t_0}L_{(i,t_0)}
> $$
> instead. These differ whenever coverage is unbalanced, which it is. Moot for the Nigeria figure, load-bearing for the pooled headline.

---

## 4. Symbol collisions

| Current | Problem | Proposed |
|---|---|---|
| $Q_{i,t}$ | Standard symbol for the real exchange rate; this is not that | $X_{i,t}$, with $\theta_{i,t}$ for the true RER |
| $\Pi_i$ — loan-life P&L | Collides with $\pi$ = inflation, defined four lines earlier in the same cell | $\Lambda_w$, or spell it $\mathrm{PL}_w$ |
| $DS_t$ — debt service | Reads as $D\times S$, and $S$ is the exchange rate. Genuinely ambiguous in $DS_t\cdot R_{i,t}$ | $\bar\delta$ (level), $\delta_t$ (time-varying) |
| $\mathbb{C}$ — constant debt service | Blackboard bold is reserved for number fields; $\mathbb{C}$ is the complex plane | $\bar\delta$ |
| $\rho$ — loan rate *and* discount rate | Cell 5: "borrowed at an interest rate $\rho$" and "given a discount rate $\rho$" | $r$ = loan rate, $\rho$ = discount rate, plus one sentence setting $r=\rho$. Add $\rho^{r}$ for the real rate (§2). |
| $E$ — energy output | One glyph from $\mathbb{E}$, and they appear in adjacent displays | $\bar{E}$ or $\mathcal{E}$ |
| $A_{n,\rho}$ / $A_{\rho,n}$ | Argument order flips between cells 4, 5 and cell 12 | Fix on $A_{n,\rho}$ |
| $L_i$ vs $L_j$ vs LLCR | Two indices for one object; LLCR defined and never used | $L_w$; cut LLCR |
| $1/S_{i,t}$ | Written inline throughout; code names it `usd_per_lcu` | Define $\varsigma\equiv 1/S$ once, or always say "USD per LCU" |
| $G$ — the Facility | Declared, used once, never enters a formula | Drop the symbol; keep **Facility** as a capitalised defined term |

### "Macro value to debt ratio"

The name undersells the object and slightly misdescribes it. $V_w$ is not a value; it is a discounted, annuity-normalised P&L per unit of debt — and, per §6, the terminal balance of the cover account as a fraction of principal. Candidates: **net cover balance** (ties symbol to mechanism, travels in both dialects); **macro P&L ratio** (minimal migration cost). I would take the first — it makes the sign convention self-evident and sets up the settlement language below.

---

## 5. Terminology: the two dialects

The draft's instincts are right — it already says "advances" rather than "pays a claim". Worth systematising, because the two-leg distinction is what a credit committee will probe:

- a **liquidity leg** — gross, reversible, intra-tenor, no loss content
- a **risk leg** — net, terminal, where the loss lives

| Concept in the draft | Insurance register | Finance / guarantee register |
|---|---|---|
| The Facility | Insurer, underwriter | Facility provider, protection seller |
| The project / borrower | Insured, policyholder | Beneficiary; obligor once drawn |
| Advance of $\bar\delta\lvert R_{w,t}\rvert$ when $R_{w,t}<0$ | Provisional payment, payment on account | **Drawing**, drawdown, utilisation |
| $R_{w,t}<0$ | — | **Drawing trigger** (not a claim trigger) |
| The escrow account | **Experience account** | Reserve / collateral account |
| Running position | Experience account balance | Net facility balance |
| End-of-tenor reconciliation | **Commutation** | Close-out, terminal net settlement |
| $L_w=D\max(-V_w,0)$ | **Ultimate net loss** (UNL) | Terminal shortfall, net payout |
| $\mathbb{E}[L_w]$ | Pure premium, risk premium | Expected loss |
| $\Psi$ | Level annual premium, net premium | Running fee |
| $\Delta r$ | — | **Spread**, margin add-on |

Two terms are worth using deliberately. **Experience account** is the precise insurance name for a notional balance that accumulates favourable experience and reverts to the cedant; it comes from finite reinsurance, the closest existing cousin to this structure. **Commutation** is the term for a terminal settlement extinguishing all obligations, which is what the maturity reconciliation does. Using both pre-empts the "so it's just a guarantee" objection.

> **Avoid "credit event."** It is ISDA-defined and means default. The trigger here is a currency movement.

### One structural point to state explicitly

Cell 9 says the Facility returns any positive terminal balance to the project. That single sentence is what makes this an option rather than a swap — the project keeps the upside, the Facility bears only the downside. A reader who misses it will assume symmetric risk-sharing and conclude the fair price is near zero. Suggested framing: *drawings are repayable solely out of subsequent favourable movements — limited recourse during the tenor, non-recourse at maturity.* It also means the escrow is economically the project's money throughout: a pledged reserve, not a premium.

---

## 6. The Facility is an Asian put — exactly

Write the annuity factor as what it is, a sum of discount factors:

$$
A_{n,\rho}=\frac{1-(1+\rho)^{-n}}{\rho}=\sum_{t=1}^{n}(1+\rho)^{-t}
$$

Define normalised weights $\omega_t=(1+\rho)^{-t}/A_{n,\rho}$. By construction $\sum_t \omega_t=1$ — the weights are a probability distribution over the tenor. Then

$$
V_w \;=\; \frac{1}{A_{n,\rho}}\sum_{t=1}^{n}\frac{R_{w,t}}{(1+\rho)^{t}}
\;=\; \sum_{t=1}^{n}\omega_t\!\left(\frac{X_{i,t}}{X_{i,0}}-1\right)
\;=\; \frac{\bar{X}^{\,\omega}_{w}}{X_{i,0}}-1
$$

where $\bar{X}^{\,\omega}_{w}=\sum_t\omega_t X_{i,t}$ is the discount-weighted *arithmetic* average of $X$ over the tenor. Therefore

$$
L_w \;=\; D\max(-V_w,0) \;=\; \frac{D}{X_{i,0}}\,\max\!\big(X_{i,0}-\bar{X}^{\,\omega}_{w},\,0\big)
$$

> **The Facility is short $D/X_{i,0}$ arithmetic average-rate puts on $X$, struck at the money-spot at financial close, with annual fixings and discount-factor averaging weights.** Verified numerically against the `compute_terminal_residuals_wdi` weights; agrees to machine precision.

### Language you can port directly

| Asian option term | Your object |
|---|---|
| Underlying | $X_{i,t}=P_{i,t}/S_{i,t}$, the dollar unit-revenue index |
| **Strike** $K$ | $X_{i,0}$, the level at financial close |
| **At-the-money-spot** | The $\mathrm{DSCR}_0=1$ assumption. The cleanest way to state it. |
| **Out-of-the-money-forward** | Because $X$ carries the tilt drift (§2), the forward sits above spot. This is the precise derivatives statement of the $\pi^{*}$ exposure. |
| **Moneyness** | $\mathrm{DSCR}_0>1$ shifts the strike to $X_{i,0}/\mathrm{DSCR}_0$. The "without loss of generality, only strengthened if $\mathrm{DSCR}_t>1$" remark *is* the statement that the option is struck OTM — say it that way and the claim becomes self-evident rather than asserted. |
| **Averaging window**, **fixings** | The $n$ annual observation dates. $t=0$ contributes identically zero, so there are effectively $n-1$ live fixings. |
| **Notional** | $D/X_{i,0}$ baskets, or $D$ in ratio terms |
| **Tenor** | $n$ — already correct in the draft |
| **Payoff**, **intrinsic value** | $\max(K-\bar{X}^{\omega},0)$ |
| **Short the put** | The Facility. The project is long it. |

The most useful sentence to borrow: *averaging suppresses volatility.* Under a driftless random walk the variance of an arithmetic average over the tenor is roughly $\sigma^{2}n/3$ rather than $\sigma^{2}n$, so an Asian put is materially cheaper than a European put on the terminal value. Part of the affordability result is this mechanical effect; better to name it than to let a referee discover it.

### Where the analogy breaks — and why that is the contribution

**Measure.** You compute a historical average of realised payoffs: an expected loss under the physical measure. An option desk quotes under the risk-neutral measure and embeds a risk premium, so a traded Asian FX put on the same payoff would cost multiples of $\Psi$. This is the first objection you will get, and it has a good answer: a long-horizon, diversified, solvency-capitalised holder can *earn* the risk premium rather than pay it. Make that argument explicitly rather than leaving $\Psi$ to be read as a price. Note also that the market forward on $X$ embeds the interest differential via covered interest parity — so it already prices expected depreciation, while the backtest does not.

> **Notation warning.** The risk-neutral measure is conventionally $\mathbb{Q}$. Now that the series is $X$ rather than $Q$ this clash is gone — one more reason for the rename in §1.

**Mean reversion.** Asian pricing under geometric Brownian motion assumes no mean reversion. Your central claim is that $\theta$ mean-reverts on a 5–10 year cycle. A standard pricer would therefore *overprice* this cover, treating terminal-average variance as growing linearly in $n$ when yours flattens. Framed that way, "the option model overprices this by construction" is a headline result, not a caveat.

**Incomplete market, no replication.** $X$ embeds CPI, which is not traded and publishes with a lag. There is no delta hedge, so the no-arbitrage price is not unique and there is no cost-of-replication floor. Actuarial pricing is the appropriate method here, not a shortcoming.

**The liquidity leg has no option analogue.** A vanilla Asian put pays once, at expiry. The Facility advances cash during the tenor and is repaid from later surpluses. That leg carries no loss content but does carry funding cost: outstanding drawings must be financed, while interest on escrowed balances accrues to the project. As constructed, $\Psi$ prices the option and omits the carry on the liquidity leg. So: **Facility = Asian put + revolving liquidity facility**, and $\Psi$ currently prices only the first term. Either price the second or explicitly scope it out.

**Discrete annual monitoring.** Covenant breaches happen on observation dates, not continuously. Standard for Asians — they are natively discretely monitored — so it costs nothing, but it is also why the liquidity leg is tractable.

---

## 7. Non-naming issues worth fixing while you are in there

### The paper's $V$ and the code's `V_i` are different objects

Cell 5 defines $V$ *with* the $1/A_{n,\rho}$ normalisation. Cell 10 has `V_i = np.sum(R_it * dfactors)`, the un-normalised sum, with the normalised quantity called `net_pv_per_debt_stock`. Same name, two meanings, one notebook; `compute_V` in cell 2 has the same issue. Rename the code variable to `V_raw` and `net_pv_by_debt_stock` to `V`.

### $\Psi$ carries two different units

Cell 12 first defines $\Psi=\mathbb{E}_N[L]/(\bar\delta\,A_{n,\rho})$, a dimensionless share of annual debt service, and derives $\Psi=\mathbb{E}_N[\max(-V,0)]=6.1\%$. The later fragment writes $\Psi/D=-\mathbb{E}[V_i]/A^{2}$, treating $\Psi$ as a currency amount. Two further problems on that line: the annuity factor appears squared where the first derivation has it once, and $-\mathbb{E}[V_i]$ has lost the $\max(\cdot,0)$, so it nets gains against losses and understates the premium. Looks like a survivor from an earlier draft; rewrite from the $\Psi$ you actually derived.

### Algeria: 11% or 19%?

Cell 7 reports a net gain of 11% of principal between 2006 and 2013. Cell 9 reports 19% escrowed over the same period on the same series. If one is gross and one net of the 7% shortfall, the arithmetic still does not close (19 − 7 = 12). Recompute and label both as gross or net.

### The consumer row has an unpriced tail

Indexation leaves the consumer's real tariff flat, so in nominal terms they are insulated. But a real devaluation cuts real incomes while the real tariff holds, so electricity gets more expensive relative to earnings — precisely when $\theta$ falls and the Facility is drawing. The historical failure mode of indexed tariffs is regulatory freeze under exactly those conditions. That is correlated with the loss windows and is not in the model. Worth a paragraph, because a reader who sees "when inflation is borne by the consumer" will ask whether it actually is.

### Quotation conventions

Three bases appear: $\Psi$ as a share of annual debt service (6.1%), $\Psi/D$ as a share of original principal, and $\Delta r$ in basis points on the loan margin (<30bp in the abstract). The abstract quotes pooled $\Delta r$ while the body quotes Nigeria-only $\Psi$, inviting a reader to compare 6.1% against 30bp and conclude something is badly wrong. A short conventions box early — naming all three, stating the conversion, and flagging that amortisation makes $\Delta r\neq\Psi/D$ except on a bullet — heads that off. The instinct is already there at the end of cell 12; it just needs to come earlier and cover all three.

### Standard errors

The 26 Nigerian windows overlap heavily — consecutive 15-year windows share 14 years — so $N=26$ overstates the information content by roughly an order of magnitude. The 6.1% point estimate rests on 4 loss windows that are one episode, the 1999 peg abandonment, seen four times. A block bootstrap over countries, or an explicit statement that the pooled estimate is driven by a small number of distinct devaluation episodes, would be more defensible than the simple average.

### Loose ends in the prose

- Cell 12 ends mid-sentence: "One could measure the a"
- "## The equivalent interest rate spread" opens with a fragment, then a gap, then "Dividing by $A_{\rho,n}$ a second time" — with no antecedent for the first division
- "risk group" appears once, undefined, in the $D_j$ assumption
- Integrals $\int_0^T$ throughout, discrete sums in the code. The data is annual — switch the paper to $\sum_{t=1}^{n}$, which also makes the $\omega_t$ weights visible
- $T$ and $\bar t$ both denote maturity; pick one
- Typos: *shrotfalls, born* (borne), *incurrs* ×2, *assumtion, incresingly, subsequend, aa simple, the the, and and*

---

## Suggested notation block, rewritten

For cell 4:

**Parameters (fixed throughout):** tenor $n=15$; nominal discount rate $\rho=0.05$; real discount rate $\rho^{r}$; annuity factor $A_{n,\rho}=\sum_{t=1}^{n}(1+\rho)^{-t}$.

**Index:** $w=(i,t_0)\in\mathcal{W}$ — a window: country $i$, financial close at $t_0$, maturity $t_0+n$. $N=|\mathcal{W}|$.

- $P_{i,t}$ — domestic CPI in LCU; $p\equiv\ln P$, inflation $\pi=\dot p$
- $P^{*}_{t}$ — US price level; $\pi^{*}$ — US inflation
- $S_{i,t}$ — nominal exchange rate, LCU per USD; $s\equiv\ln S$, so $\dot s>0$ is a depreciation of the local currency
- $X_{i,t}\equiv P_{i,t}/S_{i,t}$ — **dollar unit-revenue index**: the nominal USD value of a fixed domestic basket, i.e. what a kWh of indexed local revenue is worth in dollars. $x\equiv\ln X=p-s$, $\dot x=\pi-\dot s$
- $\theta_{i,t}\equiv X_{i,t}/P^{*}_{t}$ — real exchange rate. Used in the pricing decomposition only
- $R_{w,t}\equiv X_{i,t}/X_{i,t_0}-1$ — cumulative (holding-period) return on $X$ since close
- $\tau,\ c,\ \bar{E}$ — real tariff, real unit cost, constant energy output
- $A_{n,\rho}$ — annuity factor, PV of a unit annuity over $n$ periods at rate $\rho$
- $D$ — debt stock; $\bar\delta$ — level annual debt service, with $D=A_{n,\rho}\,\bar\delta$
- $\Lambda_w$ — discounted loan-life P&L; $V_w\equiv\Lambda_w/D$ — **net cover balance** per unit of debt
- $L_w\equiv D\max(-V_w,0)$ — ultimate net loss to the Facility
- $\Psi$ — level annual premium as a share of debt service; $\Delta r$ — margin-equivalent interest-rate add-on
- $\mathbb{E}[\cdot]$ — expectation; $\mathbb{E}_N[\cdot]$ — sample mean over $\mathcal{W}$
- **Tilt** — the real amortisation of level nominal debt service against inflation-indexed revenue

In the code, the DataFrame column `X` holds $X_{i,t}$ (computed as `cpi / exchange_rate`) and `exchange_rate` holds $S_{i,t}$.
