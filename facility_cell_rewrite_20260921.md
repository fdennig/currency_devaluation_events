# Rewriting the Facility cell: the cover level, and the Asian put

*Proposal for cell 7 of `notebooks/draft.ipynb` ("The emergency liquidity facility"). Notation follows the draft's own cells 2-3: window $w=(i,\underline{t})$, maturity $\bar{t}=\underline{t}+n$, sums $\sum_{t=\underline{t}+1}^{\bar{t}}$, discount exponent $t-\underline{t}$, $D=A_{n,r}\bar\delta$.*

Three things drive the rewrite.

1. **The strike gets a name, $K_w$, and its own paragraph.** It is currently written out longhand as $X_{i,\underline{t}}$ in six places and never named. Naming it costs one symbol and buys the observation that the *same* number sizes the debt, sets the trigger and strikes the option — one observation doing three jobs, which is the structural fact the instrument rests on.
2. **The Asian put is promoted from an aside to the hinge of the section**, with the weights normalised so the identity is exact, the notional given its economic reading, and the physical/risk-neutral distinction stated before a derivatives reader raises it.
3. **Each claim is landed twice**, once in the insurance register and once in the finance register, with a short concordance table so neither audience has to take the other's word for what the object is.

Two corrections are folded in; see §3.

---

## 1. The proposed cell

```markdown
## The emergency liquidity facility

Let the **Facility** offer cover that, in return for an annual premium, supplies emergency liquidity to a project with hard currency debt service obligations when the currency moves against it. In the insurance register the Facility is the underwriter and the project the insured; in the finance register the Facility is a protection seller, and the project its beneficiary during the tenor and its obligor once it has drawn. The cover has two legs, and keeping them apart is what makes it priceable:

- a **liquidity leg** --- gross, reversible, paid out year by year during the tenor, and carrying no loss content of its own;
- a **risk leg** --- net, terminal, settled once at maturity, and where the loss actually lives.

Consider again a project with inflation-indexed local currency revenues and constant hard currency debt service $\bar\delta$, sized at close so that $\text{DSCR}_{\underline{t}} = 1$.

**The cover level.** Everything in the contract is written against a single observed number: the level of the dollar unit-revenue index in the year of financial close. Give it a label,
$$
K_w \;\equiv\; X_{i,\underline{t}} ,
$$
and call it the **cover level**. It is fixed once, at close, and never revised. It does three jobs at once. It *sizes the debt*, since $\bar\delta = K_w(\tau-c)\bar{E}$ is the dollar cash flow the lender lent against. It *defines the trigger*, since the project is short of dollars in year $t$ exactly when $X_{i,t}<K_w$. And it is the *level the whole path is measured against*, since the cumulative return on which the cover settles is
$$
R_{w,t} \;=\; \frac{X_{i,t}}{K_w}-1 ,
\qquad t=\underline{t}+1,\dots,\bar{t} .
$$
That $K_w$ does all three is not a modelling convenience, it is the point: strike, trigger and notional come from one observation, so there is no gap between the level the deal was underwritten at and the level the cover responds to. And $K_w$ is not a forecast, a model output or a dealer quote. It is a published CPI divided by a published exchange rate in a stated year, which is what makes the cover writable at all --- neither side can argue about where it was struck.

Readers will each have their own name for it. To an option trader $K_w$ is the **strike**, and because the cover is struck at the prevailing level of the underlying rather than above or below it, the cover starts life **at the money**: at close, $R_{w,\underline{t}}=0$ and the cover has no intrinsic value, only time value. To an underwriter it is the **attachment level**, the point at which cover begins to respond. To anyone who has drafted a PPA it is the **base-date level**, the reference against which every later escalation is computed.

**The liquidity leg.** The condition $X_{i,t}<K_w$ --- equivalently $R_{w,t}<0$ --- is the **drawing trigger**: whenever a devaluation puts the dollar value of revenue below the cover level, the Facility **advances** $\bar\delta\,|R_{w,t}|$ and the project meets its debt service to its original creditors in full. No covenant is breached and no payment is missed, so the trigger is a currency movement and never a credit event: the lender continues to see a performing loan, which is the whole purpose of the leg. Whenever $X_{i,t}>K_w$ the project pays the surplus into an interest-bearing USD **experience account** --- a pledged reserve, or cash sweep, whose running balance stands against the advances outstanding.

Note what the trigger is not. It is an index, not a claim: cover responds to the published path of $P$ and $S$, and not to the project's own accounts. This is *parametric* cover, with the usual bargain --- no loss adjustment, no verification, no scope for the insured to influence the payout, in exchange for basis risk if the project's realised dollar revenue drifts from $X$. That basis risk is exactly the imperfect-indexation question, and we return to it below.

In the 15-year Algerian window starting in 1998, the Facility would have advanced 0.76 years of debt service between 1998 and 2006, and the experience account would have taken in 1.15 years between 2006 and 2013 (the red and green areas in @fig-algeria, each valued at the start of its own segment).

**The risk leg.** At maturity $\bar{t}$ the position is **commuted**: the two sides settle net once and every obligation is extinguished. A positive experience account balance is returned to the project; a negative one --- advances that the later surpluses did not repay --- is the loss borne by the Facility. Advances are therefore repayable solely out of subsequent favourable movements: limited recourse during the tenor, non-recourse at maturity. The experience account is the project's money throughout, which is what makes this cover an option rather than a swap --- the project keeps its upside and the Facility is left with the downside alone. An underwriter will recognise the shape from finite-risk reinsurance, where an experience fund absorbs the ordinary years and the commutation at term is the moment the genuine risk transfer is revealed.

**Equivalently, an Asian put.** The risk leg has an exact counterpart in derivatives, and it is worth getting the identity rather than the analogy. Write the annuity factor as the sum of discount factors it is and normalise them,
$$
A_{n,\rho}=\sum_{k=1}^{n}(1+\rho)^{-k},
\qquad
\omega_t=\frac{(1+\rho)^{-(t-\underline{t})}}{A_{n,\rho}},
\qquad
\sum_{t=\underline{t}+1}^{\bar{t}}\omega_t=1 .
$$
The weights now sum to one, so they define a genuine weighted average of the index over the tenor,
$$
\bar{X}_{w}\;\equiv\;\sum_{t=\underline{t}+1}^{\bar{t}}\omega_t\,X_{i,t},
$$
the **settlement level**. Substituting into the net cover balance collapses the whole path to that one number:
$$
V_w \;=\; A_{n,\rho}\left(\frac{\bar{X}_{w}}{K_w}-1\right),
\qquad\text{so}\qquad
L_w \;=\; \bar\delta\max(-V_w,0) \;=\; \underbrace{A_{n,\rho}\,(\tau-c)\bar{E}}_{\text{notional}}\cdot\max\big(K_w-\bar{X}_{w},\,0\big) .
$$
That is the payoff of an arithmetic average-rate put --- an **Asian put** --- and the Facility is short it, the project long. What the Facility owes at commutation turns not on where $X$ ends up but on its average level over the tenor, and it owes anything at all only if that average finishes below the cover level.

| Object in the contract | In the option |
|---|---|
| The dollar unit-revenue index $X_{i,t}=P_{i,t}/S_{i,t}$ | the underlying |
| The cover level $K_w=X_{i,\underline{t}}$ | the strike, struck at the money spot |
| The settlement level $\bar{X}_{w}$ | the arithmetic average of the fixings |
| The annual observations of $X$ over $t=\underline{t}+1,\dots,\bar{t}$ | the fixings, $n$ of them |
| The discount factors, normalised, $\omega_t$ | the averaging weights |
| $A_{n,\rho}(\tau-c)\bar{E}$ baskets | the notional |
| The Facility | short the put; the project is long it |

Three readings follow, and they are worth separating because they are usually run together.

*The notional is the project's own output.* $(\tau-c)\bar{E}$ is the project's annual margin measured in baskets rather than dollars, so the notional is simply that margin stream discounted over the loan life. The Facility is short one put per basket the project will sell. Equivalently it is $A_{n,\rho}\bar\delta/K_w$, which is the debt stock converted into baskets at the cover level whenever the Facility discounts at the loan rate.

*The weights are not flat, and they lean the right way.* Because $\omega_t$ declines in $t$, the early fixings count for more than the late ones. This is what a discount rate does, but it also happens to line up with where the problem is: a devaluation in year 3 is both more expensive to the Facility and more dangerous to the project than the same devaluation in year 13.

*Averaging is cheap, and mean reversion is cheaper still --- but they are two effects, not one.* Even for a driftless random walk, the variance of an arithmetic average over $n$ fixings is of order $\sigma^2n/3$ rather than $\sigma^2n$: cover written on the whole path costs materially less than cover on the terminal level, mechanically, before any economics is invoked. On top of that sits the claim this paper actually makes, that $X$ reverts within a 15-year tenor. Naming both keeps the second from doing work the first is already doing.

A last point for anyone tempted to price this off a screen. A dealer quoting an Asian put quotes it under the risk-neutral measure, from an implied volatility, with no mean reversion assumed and a hedging cost embedded; and for most African currencies there is no screen to quote from. The Facility is not quoting a tradable price. It holds the position to commutation, cannot hedge it, and prices the *physical* distribution of $X$ --- which is why the premia computed below sit well under what the derivative would be marked at, and why nothing here is an arbitrage claim.

**Reading it from either side.** The same seven objects, in the two registers the readership arrives with:

| | Insurance / guarantee | Finance / derivatives |
|---|---|---|
| $K_w$ | attachment level | strike |
| $X_{i,t}<K_w$ | trigger, parametric | in the money |
| The advance | claim payment, reversible | drawing under a revolver |
| The experience account | experience fund | pledged reserve, cash sweep |
| Commutation at $\bar{t}$ | commutation | final net settlement, non-recourse |
| $L_w$ | ultimate net loss | terminal payoff of the short put |
| $\Psi$ | pure premium, rate on line | running margin, $\Delta r$ in bp |

Neither column is a metaphor for the other. The contract is one object and both columns describe it exactly, which is the useful thing about it: it can be underwritten by an insurer, booked by a treasury, and priced off a macroeconomic panel.

Look at the path of $X$ in Nigeria to understand the loss profile of such cover. @fig-windows-nga shows the liquidity leg in the upper panel and the risk leg in the lower panel.

The upper panel traces all 15-year windows in the Nigerian data with a horizontal line at that window's cover level $K_w$. Whenever $X$ is below a window's line, as it is between 1985 and 1993 for the window closing in 1985, a project servicing debt during that window is short of dollars and draws on the Facility. Whenever $X$ is above the line, as it is between 1993 and 1999 for the same window, the project runs a dollar surplus and pays into the experience account. The cumulative discounted area between the line and $X$ is the discounted loan-life P&L over the window; per unit of annual debt service, it is the net cover balance $V_w$. Where it is negative the commutation leaves the Facility short and the line is drawn in red; where it is positive the balance is commuted back to the project and the line is green. The lines darken with the close date, and a dot in the same shade marks $X$ at the window's maturity.

The lower panel plots $V_w$ in years of debt service, valued at close, beneath the maturity dot of its own window.

Between 1985 and 2024 there are 25 such windows. Twenty-one commute with a positive net cover balance, ranging from 2.0 to 15.6 years of debt service. Four --- those closing immediately before the 1999 abandonment of the dollar peg and the devaluation that followed --- commute short, the worst at 6.1 years. As we show below, and as the theory predicts, this pattern of many shallow gains against few deep losses is general across the African sample.
```

---

## 2. What changed, and why

| Change | Reason |
|---|---|
| $K_w$ defined, named the **cover level**, given its own paragraph before either leg | The user-facing ask. It also lets the trigger be stated as $X_{i,t}<K_w$, a statement about a *level*, rather than $R_{w,t}<0$, a statement about a derived quantity --- the first is what a term sheet would say |
| "Three jobs at once" | Converts a notational choice into the structural claim that there is no basis between the sizing of the debt and the strike of the cover |
| Strike named in three registers (strike / attachment level / base-date level) | The stated goal of carrying option, insurance and PPA readers through the same sentence |
| "At the money, no intrinsic value at close" | Explains $R_{w,\underline{t}}=0$ in language a derivatives reader already owns, and pre-empts "where is it struck relative to forward?" (see §4.2) |
| $\bar{X}_w$ named the **settlement level** and promoted to a defined object | It is the second of only two numbers that determine the payoff. Leaving it as an unlabelled $\bar{X}$ inside one display understates it |
| The $\omega_t$ normalisation shown explicitly | Makes the Asian identity exact rather than suggestive; see §3.1 |
| The notional reread as $A_{n,\rho}(\tau-c)\bar{E}$ baskets | Corrects §3.1 and yields a genuinely nice reading: one put per basket sold |
| Parametric-vs-indemnity paragraph | The first question any underwriter or guarantee reader asks, and it sets up the indexation sensitivity later |
| "Never a credit event" | Restored from `paper_draft.ipynb` cell 11. It is the sentence that matters most to a lender and it had dropped out of the concise draft |
| Finite-risk reinsurance named | Gives insurance readers a contract shape they already know, and it is the closest real precedent to the experience-account-plus-commutation structure |
| Averaging variance and mean reversion explicitly separated | Prevents a referee discovering that $\sigma^2n/3$ is doing part of the work attributed to reversion |
| Physical vs risk-neutral paragraph | Pre-empts "then quote me the Black-Scholes price". The existing sentence gestures at this; naming the measure closes it |
| Two-register concordance table | Does in one glance what would otherwise take a paragraph per reader type |

---

## 3. Two corrections

**3.1 The notional in the current payoff formula is off by $A_{n,\rho}/A_{n,r}$.** The cell currently states
$$\text{payoff}=\frac{D}{X_{i,\underline{t}}}\max\big(X_{i,\underline{t}}-\bar{X}_{w},0\big),$$
with $\bar{X}_w$ described as an average under weights that are "the discount factors". Two issues. Unnormalised discount factors sum to $A_{n,\rho}$, not 1, so $\bar{X}_w$ as described is not an average and the identity does not close. And with the weights normalised, working through from $L_w=\bar\delta\max(-V_w,0)$ gives a notional of $A_{n,\rho}\bar\delta/K_w$, whereas cell 2 sets $D=A_{n,r}\bar\delta$ --- the *loan* rate sizes the principal. So $D/K_w$ is right only when $\rho=r$. Writing the notional as $A_{n,\rho}(\tau-c)\bar{E}$ is exact under either convention and reads better. Full derivation:
$$-V_w=A_{n,\rho}\Big(1-\tfrac{\bar{X}_w}{K_w}\Big)
\;\Rightarrow\;
L_w=\tfrac{\bar\delta A_{n,\rho}}{K_w}\max(K_w-\bar{X}_w,0)
=A_{n,\rho}(\tau-c)\bar{E}\max(K_w-\bar{X}_w,0),$$
using $\bar\delta=K_w(\tau-c)\bar{E}$ from cell 3. Dimensions check: baskets per year, times years, times dollars per basket.

**3.2 $V_w$ carries an annuity factor that the Asian reading needs made visible.** $V_w=A_{n,\rho}(\bar{X}_w/K_w-1)$, not $\bar{X}_w/K_w-1$. `moneyness_and_triggers_20260916.md` §1 works with the normalised version and so drops the $A_{n,\rho}$; the draft's $V_w$ is unnormalised. Both are internally consistent, but they are not the same object, and the factor is exactly the one that later turns $\Theta$ into $\Psi$. Worth stating once, in this cell, so the $A_{n,\rho}$ in cell 9 arrives as a recurrence rather than a novelty.

---

## 4. Other references worth giving prominence

Ranked by what they buy, against what they cost in words.

### 4.1 LLCR $=1$ --- the reference the lenders in the room already use

From `paper_draft.ipynb` cell 34: $\text{LLCR}_w = 1+V_w/A_{n,\rho}$, so with §3.1's identity, $\text{LLCR}_w = \bar{X}_w/K_w$ exactly. **The loan life coverage ratio is the settlement level divided by the cover level.** The Facility therefore attaches at $\text{LLCR}=1$ and tops the ratio back to one:
$$\frac{\mathbb{E}[L_w]}{D}=\mathbb{E}\big[(1-\text{LLCR}_w)^{+}\big].$$
This is the single highest-value addition after the strike. DSCR and LLCR are the two numbers a project finance audience thinks in, DSCR already appears in cell 3, and LLCR is currently absent from `draft.ipynb` entirely despite the identity being one line. It gives the credit committee a sentence in its own language: *cover on the loan life coverage ratio, attaching at 1.00x*.

### 4.2 The forward level --- struck at the money spot, out of the money forward

$X=QP^{*}$, so even with the real rate $Q$ flat, $X$ drifts up at US inflation. The forward level at horizon $t$ is around $K_w(1+\pi^{*})^{t-\underline{t}}$, above the strike. So the cover is at the money *spot* but out of the money *forward* --- a strictly cheaper place to be struck, and a free one, because the drift is a fact about the numeraire rather than a view. For a derivatives reader this is the natural follow-up to "struck at the money" and going unanswered it reads as an omission. One sentence, cross-referenced, would do it. Flagged with care: the tilt section was dropped in `e90d474`, and the point here is the *moneyness* consequence, not the tilt machinery --- so resist it expanding back into a section.

### 4.3 The moneyness reference $K_w/d$ --- makes "without loss of generality" a proof

With $d\equiv\text{DSCR}_{\underline{t}}$, coverage is $c_{w,t}=d\,X_{i,t}/K_w$, the strike becomes $K_w/d$ and the payoff $D\max(1-d\bar{X}_w/K_w,0)$ is decreasing in $d$. So $d$ *is* the moneyness: $d=1$ is at the money, $d=1.20$ is struck 16.7% out of the money, and every real deal is cheaper to cover than the one priced here. This is `moneyness_and_triggers_20260916.md` §1 and it belongs in cell 3, where the claim is currently asserted, rather than in the Facility cell. But once it is there, the Facility cell can say "struck at the money because $d=1$, and out of the money on any real deal" and be understood.

### 4.4 The peak drawn balance --- the facility's *size*, as distinct from its *loss*

The paper prices expected loss. It never states how much liquidity has to be *committed*, which is the first question from anyone who has to reserve the line. The reference is the maximum of the running advances-outstanding balance over the tenor --- 0.76 years of debt service in Algeria on the cumulative measure, but the running peak is the number that sizes the commitment. `window_balance()` already carries the liquidity leg off the same rows, so this is a column, not a project. Naming **committed size** against **expected loss** separates the balance sheet question from the pricing question, and it is the distinction that makes the affordability result land with a guarantee provider rather than merely with an actuary.

### 4.5 A limit, and the rate on line

The cover as written is unlimited: the Facility eats the whole of $\max(-V_w,0)$ however deep. Every insurance reader will look for the limit, and finding none will either assume an error or price it as unlimited. Two options, both cheap: state that the cover is uncapped and that this is deliberate, since capping it at the point of a 1999-Nigeria event would remove cover exactly where it is wanted; or introduce an aggregate limit $\bar{L}$ in years of debt service and quote the **rate on line**, $\Psi A_{n,\rho}/\bar{L}$, which is the number a reinsurer would benchmark. Even the first sentence, stated plainly, is worth having.

### 4.6 The covenant levels, 1.20x lock-up and 1.10x default

Cells 3 and 6 already reach for "DSCR in excess of 120%" and "in excess of 150%". Making the standard pair explicit --- distribution lock-up around 1.20x, event of default around 1.10x --- anchors the drawing trigger in clauses that already exist, and sets up the two-trigger design in `moneyness_and_triggers_20260916.md` §4 as a variation on the lock-up band rather than as an invention. Reference, not section.

### 4.7 A floating strike, as the robustness alternative

The legacy event work struck cover against a 5-year trailing moving average of $H=P/X$ rather than against a fixed close-year level. In option terms that is a *floating-strike* Asian, and the current design is the *fixed-strike* one. Worth a footnote where the cover level is defined, because it shows the choice was made rather than defaulted into, and because a reader who knows the earlier work will otherwise wonder where the baseline went. The economics of the choice: a fixed strike insures the deal as underwritten, a floating strike insures against sharp moves but lets a slow grind reset the protection away.

### 4.8 Market precedents worth naming in one line each

EcoInvest Brazil is already in cell 1. Three more, from the table in `moneyness_and_triggers_20260916.md` §4: **GuarantCo liquidity extension guarantees**, back-up liquidity for operating-phase revenue shortfalls; **the IBRD partial risk guarantee standing behind a revolving letter of credit**, precedent for reversible cover that replenishes; and **finite-risk reinsurance with an experience fund**, precedent for the commutation. One clause each, in the opening paragraph, and the instrument stops reading as novel --- which for this readership is the objective.

### 4.9 One term to avoid

Not "dual trigger". In insurance it already means cover contingent on a *second, non-insurance* event, and using it for two thresholds on one variable will be read as something else entirely. "Two-trigger" or "split-trigger" if the design in `moneyness_and_triggers_20260916.md` ever lands in the draft.

---

## 5. Knock-on edits if the rewrite is taken

1. **Cell 2 (Notation).** Add `$K_w \equiv X_{i,\underline{t}}$ --- the **cover level**: the strike of the cover, fixed at close`, immediately above the $R_{w,t}$ line, and restate that line as $R_{w,t}=X_{i,t}/K_w-1$. Add $\bar{X}_w$ and $\omega_t$ beneath $V_w$. Optionally add $\text{LLCR}_w$ if §4.1 is taken.
2. **Cell 3 (A stylised project).** $\bar\delta=K_w(\tau-c)\bar{E}$, and the closing "without loss of generality" paragraph replaced by the moneyness argument of §4.3 --- the drop-in is already written in `moneyness_and_triggers_20260916.md` §1.
3. **Cell 4 (`fig-algeria` caption).** "the 1998 close-year level each series is struck at" becomes "the cover level $K_w$".
4. **Cell 8 (`fig-windows-nga` caption).** "a horizontal bar at its close-year level $X_{i,\underline{t}}$" becomes "at its cover level $K_w$".
5. **`source/cover.py`.** `window_panel` already documents `base` as "the level at close -- the strike". Change it to "the cover level $K_w$: the level at close, and the strike of the cover" so the code and the paper share one name.
6. **Cells 9-10.** Unchanged, but the $A_{n,\rho}$ in $\Psi=\Theta/A_{n,\rho}$ can now be introduced as the same factor that appeared in the Asian identity, rather than as a fresh conversion.
