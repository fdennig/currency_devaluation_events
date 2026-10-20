# Two rates, not one: separating $r_L$ from $d$

*Companion to `notation_review_20260916.md` and `moneyness_and_triggers_20260916.md` — analysis and change list, not implemented in the draft*

The draft sets $r=\rho$ throughout and uses a single $\rho=5\%$ everywhere: the annuity factor that sizes the debt, the discounting inside $\Lambda_w$ and $V_w$, the carry on the experience account, and the annuity factors in `equivalent_rate`. Those are four different rates wearing one symbol. §1 names them. §2 shows what the loan rate does and does not touch, which is less than it looks. §3 derives the equivalent-rate equation under separated rates. §4 gives the comparative statics. §5 is the change list. §6 records what is still missing, which matters more than any of this.

Headline: **the separation is worth about 6bp and one broken identity.** At a realistic $r_L=8\%$ against $d=5\%$ the margin quote goes from 58bp to 64bp, and the actuarial quote $\Psi$ does not move at all. The number is more robust than it was being treated as.

All figures below are the 1985 pool, $n=15$, priced on $X$, as the notebook currently stands.

---

## 1. The four rates inside $\rho$

| | What it is | Where it lives now |
|---|---|---|
| $r_L$ | Loan rate on the project's hard-currency debt. Contractual, market-set. Sizes $D=A_{n,r_L}\bar\delta$ | `annuity_factor`; the `discount_rate` argument of `equivalent_rate()` |
| $c$ | Carry rate on the experience account — charged on advances, earned on escrow. A **design choice**, not an observation | `bal = bal * (1 + rho_l) + flow` in the ledger cell |
| $d$ | The Facility's own valuation rate: its cost of funds, and the rate at which it discounts its liability | `compute_terminal_residuals_wdi(discount_rate=)` |
| $r_C-r_f$ | Cost-of-capital spread on solvency capital: what its provider requires, less what it earns while held | Not modelled at all |

Worth stating in the draft before any of the above: **the cash mechanics need no rate whatsoever.** The advance in year $t$ is $\bar\delta\max(-R_{w,t},0)$ and the escrow is $\bar\delta\max(R_{w,t},0)$, both ratios of two $X$ observations. Rates enter only when netting across years ($c$), valuing the net position ($d$), sizing the principal ($r_L$), and converting to a margin ($r_L$). The trigger and the drawdown are rate-free.

$c$ and $d$ collapse into one discounted sum only when $c=d$, which is why $V_w$ has its clean form. Set $c>d$ and the Facility books a lending spread on the liquidity leg that part-funds the insurance leg — which is what EcoInvest-type facilities actually do. The draft cannot currently express either choice. Everything below conflates $c=d$ and takes up only the $r_L$ vs $d$ split.

---

## 2. What the loan rate does and does not touch

Write the primitive in dollars:

$$
\Lambda_w(d)=\bar\delta\sum_{k=1}^{n}R_{w,k}\,(1+d)^{-k},
\qquad
\Theta(d)\;\equiv\;\frac{\mathbb{E}\big[\max(-\Lambda_w,0)\big]}{\bar\delta}.
$$

$\Theta$ is the expected loss in units of one debt-service payment, and **depends on $d$ alone**. Then the two quotes are

$$
\Psi(d)=\frac{\Theta(d)}{A_{n,d}}
\quad\text{(level premium, as a share of debt service)},
\qquad
\kappa=\frac{\Theta(d)}{A_{n,r_L}}
\quad\text{(expected loss, as a share of principal)},
$$

related by $\kappa=\Psi\cdot A_{n,d}/A_{n,r_L}$. At $r_L=d$ these are one number — that is the $A$-identity, and it is a coincidence of the parameterisation rather than an identity.

**$\Psi$ is invariant to $r_L$.** The reason is that $\bar\delta$ is a *physical* quantity: the DSCR $=1$ sizing pins it to the project's first-year dollar cash flow $X_{i,\underline{t}}(\tau-c)\bar{E}$. The loan rate does not touch it; it only decides how much principal that cash flow supports. The Facility insures the payment stream, so its exposure $\bar\delta R_{w,k}$, its expected loss, and its level premium are all invariant, and $\Psi=\pi/\bar\delta$ with them. (This survives the other normalisation: hold $D$ fixed and let $\bar\delta=D/A_{n,r_L}$ rise with $r_L$, and exposure and denominator scale together.)

$\kappa$ is *not* invariant — it rises as $r_L$ shrinks $D$. The correction between them is exactly $A_{n,r_L}/A_{n,d}$, and the cancellation is identical, not approximate:

$$
\underbrace{\frac{\Theta(d)}{A_{n,r_L}}}_{\text{rises with }r_L}\times\frac{A_{n,r_L}}{A_{n,d}}=\frac{\Theta(d)}{A_{n,d}}=\Psi(d).
$$

> **Trap worth writing down.** `psi_pool` in the code is already $\Theta/A_{n,d}$, i.e. already $\Psi$. Applying the $A_{n,r_L}/A_{n,d}$ correction to *it* applies the correction twice and produces a spuriously low premium (2.91% instead of 3.97% at $r_L=10\%$, $d=5\%$). The object that needs correcting is $V_w=\Lambda_w/D$, which must divide by $A_{n,r_L}$ once the rates separate.

$\Psi$ is also close to invariant in $d$, because raising $d$ shrinks numerator and denominator together and leaves only a reweighting of the path:

| $d$ | $\Psi$ (% of debt service) | $A_{n,d}$ | $\Theta$ per 100/yr |
|---|---|---|---|
| 3% | 4.02% | 11.938 | 48.00 |
| 4% | 4.00% | 11.118 | 44.43 |
| 5% | 3.97% | 10.380 | 41.21 |
| 6% | 3.94% | 9.712 | 38.31 |
| 8% | 3.89% | 8.559 | 33.31 |
| 10% | 3.85% | 7.606 | 29.27 |
| 12% | 3.81% | 6.811 | 25.93 |

Quadrupling $d$ moves the PV of the loss by $-46\%$ and the premium by $-5\%$. Note $P(V_w<0)$ moves the other way over the same range (26% → 28%): harder discounting penalises the late recovery leg, so more windows end short even as the depth of the loss compresses. **This is the one place where $d$ prices the intertemporal hedge, and it shows up in frequency rather than in the premium.**

---

## 3. The equivalent-rate equation

The project pays $\bar\delta$ to the lender and $\pi=\Psi\bar\delta$ to the Facility. Ask what single rate on the **same principal** produces the same total annual outgoing:

$$
\frac{D}{A_{n,\,r_L+\Delta r}}=\bar\delta+\pi .
$$

Substituting $D=\bar\delta A_{n,r_L}$ and dividing by $\bar\delta$:

$$
\boxed{\;A_{n,\;r_L+\Delta r}=\frac{A_{n,r_L}}{1+\Psi(d)}\;}
$$

The form is unchanged from the draft. What changes is that the annuity factors take $r_L$ and the $\Psi$ inside takes $d$ only. The draft's "treat the expected loss as additional principal" gloss is misleading: rearranging gives $D/A_{n,r_L+\Delta r}=\bar\delta(1+\Psi)$, i.e. annual debt service rises by exactly the premium. The equation was always the annual-premium equivalence.

**The alternative, and why it is the wrong one.** If the project instead borrowed the premium as a lump sum at close, financed at its own rate, then $r_L$ enters in both places:

$$
A_{n,\;r_L+\Delta r}=\frac{A_{n,r_L}}{1+\kappa},\qquad \kappa=\frac{\Theta(d)}{A_{n,r_L}} .
$$

The annual-premium version is the right one because the Facility takes no project credit risk on the premium stream. If the project folds at year $k$, the Facility stops receiving premium but also stops being on risk; it does not sit on an unpaid loan, only on the realised balance of the experience account. Its credit exposure on an advance made in year $k$ is the **joint** event

$$
\{\text{project folds in }(k,\bar{t}\,]\}\;\cap\;\{\text{experience account}\le 0\text{ when it does}\},
$$

not project default as such. That conjunction bounds the spread over $d$ well below $r_L-d$, and bounds its size by the expected deficit rather than by $D$. It is not zero — the two events are positively correlated, since the FX shortfall is itself a principal source of the stress — but $d\approx$ funding cost plus a thin joint-default spread. Against a true 3–4% funding cost, the draft's 5% is defensible and probably conservative.

---

## 4. Comparative statics

### In $r_L$, holding $d=5\%$

$\mathbb{E}[L]=41.21$ USD PV per 100/yr of debt service; level premium $\pi=3.970$ USD/yr.

| $r_L$ | $A_{n,r_L}$ | $D$ | $D_{mac}$ | $\kappa$ = loss/$D$ | $\times A_{r_L}/A_d$ = $\Psi$ | $\Delta r$ exact | $\Delta r$ approx | $\Delta r$ lump-sum |
|---|---|---|---|---|---|---|---|---|
| 5% | 10.380 | 1038.0 | 6.10 | 3.97% | **3.97%** | **58bp** | 68bp | 58bp |
| 6% | 9.712 | 971.2 | 5.93 | 4.24% | **3.97%** | **60bp** | 71bp | 64bp |
| 7% | 9.108 | 910.8 | 5.76 | 4.52% | **3.97%** | **62bp** | 74bp | 71bp |
| 8% | 8.559 | 855.9 | 5.59 | 4.81% | **3.97%** | **64bp** | 77bp | 78bp |
| 9% | 8.061 | 806.1 | 5.43 | 5.11% | **3.97%** | **67bp** | 80bp | 86bp |
| 10% | 7.606 | 760.6 | 5.28 | 5.42% | **3.97%** | **69bp** | 83bp | 94bp |
| 12% | 6.811 | 681.1 | 4.98 | 6.05% | **3.97%** | **74bp** | 89bp | 112bp |

$\Delta r$ rises at **about 0.021bp of margin per bp of loan rate**, drifting to 0.024 by 12%. The first-order version says why:

$$
\Delta r\;\approx\;\Psi\cdot\frac{1+r_L}{D_{mac}(n,r_L)} .
$$

$\Delta r$ is the premium divided by the loan's modified duration — which is right, since duration *is* the sensitivity of the annuity to its rate. $\Psi$ is fixed, so the entire comparative static is the loan's duration shortening as $r_L$ rises (6.10 years at 5%, 5.28 at 10%, 4.98 at 12%): the same annual premium must be recovered through a progressively less rate-sensitive instrument. The approximation overshoots the level by ~17% (the annuity is convex) but tracks the slope: $+22\%$ predicted against $+19\%$ exact over 5%→10%.

The last column is the lump-sum variant of §3. At $r_L=10\%$ the two differ by 25bp, and **that gap is the value of the Facility not taking project credit risk on the premium stream, expressed directly as loan margin.** It is a more persuasive way to make the "institution with long-term capital" argument than any discount-rate sensitivity, because it does not depend on the loss distribution at all.

### In $d$, holding $r_L$ — $\Delta r$ in bp

| $r_L\ \backslash\ d$ | 3% | 4% | 5% | 6% | 8% | 10% |
|---|---|---|---|---|---|---|
| 5% | 59 | 59 | 58 | 58 | 57 | 56 |
| 6% | 61 | 61 | 60 | 60 | 59 | 58 |
| 7% | 63 | 63 | 62 | 62 | 61 | 60 |
| 8% | 65 | 65 | 64 | 64 | 63 | 62 |
| 9% | 68 | 67 | 67 | 66 | 65 | 65 |
| 10% | 70 | 69 | 69 | 69 | 68 | 67 |

**The Facility's own rate is worth about one basis point in the margin quote.** It matters for the capital number, not for the price. The whole plausible space spans 56–70bp.

### $\kappa$, the capital-relevant quote

$\kappa=\Theta(d)/A_{n,r_L}$ moves on both rates, by more than a factor of two:

| $r_L\ \backslash\ d$ | 3% | 5% | 8% | 10% |
|---|---|---|---|---|
| 5% | 4.62% | 3.97% | 3.21% | 2.82% |
| 8% | 5.61% | 4.81% | 3.89% | 3.42% |
| 10% | 6.31% | 5.42% | 4.38% | 3.85% |

Direction worth flagging in the draft, because it reads backwards: **a cheaply-funded Facility books a larger expected loss and a larger capital requirement on identical risk.** It still wins, but on the cost of capital, not on the measured loss — so the comparison across institutions has to be pure premium *plus* capital loading, never the pure number alone.

### The cheap-funding concession

Same expected loss, two conversion rates — premium as a share of debt service:

| | annuitised at $d$ | annuitised at $r_L$ | concession |
|---|---|---|---|
| $r_L=6\%$, $d=4\%$ | 4.00% | 4.57% | 12.6% |
| $r_L=8\%$, $d=4\%$ | 4.00% | 5.19% | 23.0% |
| $r_L=8\%$, $d=3\%$ | 4.02% | 5.61% | 28.3% |
| $r_L=10\%$, $d=3\%$ | 4.02% | 6.31% | 36.3% |

### Reproducing these

No re-run of the panel is needed: the loss distribution depends on $d$ alone, so one pass of `compute_terminal_residuals_wdi` per $d$ gives everything, and the rest is annuity algebra.

```python
A    = lambda r, n=15: (1 - (1 + r) ** -n) / r
dmac = lambda r, n=15: 1 / r - n / ((1 + r) ** n - 1)

# psi[d] = -res['loss'].mean() from a run at discount_rate=d; this IS Psi(d).
theta = {d: p * A(d) for d, p in psi.items()}      # per unit of debt service

def delta_r(r_L, d):                                # annual-premium equivalence
    tgt = A(r_L) / (1 + psi[d])
    return brentq(lambda r: A(r) - tgt, 1e-9, 2.0) - r_L

def delta_r_lump(r_L, d):                           # premium financed at r_L
    tgt = A(r_L) / (1 + theta[d] / A(r_L))
    return brentq(lambda r: A(r) - tgt, 1e-9, 2.0) - r_L
```

---

## 5. What would need to change

> **Three code changes, all small.** The calculation is unchanged; only which rate is passed where.

1. **`compute_terminal_residuals_wdi(discount_rate=d)`** — unchanged in substance, but the argument is now $d$, the Facility's rate, and should be renamed to say so. Its `V` column is $\Lambda_w/(\bar\delta A_{n,d})$, i.e. the premium object, *not* the debt-stock object it is documented as.
2. **`equivalent_rate(psi, discount_rate=r_L, years=n)`** — takes the **loan rate**, not the global. Today both read `discount_rate`, which is why the two roles were never visible.
3. **`compute_V(rho=discount_rate)`** — the Algeria panel's labels; follows $d$.

**Notation.** Three symbols where there is now one, per §2: $\Lambda_w(d)$ the primitive in dollars, $\Psi(d)=\Theta/A_{n,d}$ the actuarial quote, $\kappa=\Theta/A_{n,r_L}$ the capital quote. The $A$-identity becomes a relation, $\kappa=\Psi\cdot A_{n,d}/A_{n,r_L}$, equal only at $r_L=d$. The "one number, two readings" passage in the instrument section needs rewriting around that — it currently presents the coincidence as a result.

**LLCR.** $\text{LLCR}_w=1+V_w$ needs care. LLCR conventionally discounts CFADS at the loan rate, so the coverage object is $r_L$-discounted while the pricing object is $d$-discounted. The cash mechanic still tops coverage back to one in every period — that is rate-free — but "the expected cost per dollar of debt equals the expected LLCR shortfall" holds only at $r_L=d$.

**Notation section.** "we set $r=\rho$ throughout" becomes a stated simplification with a pointer to this sensitivity, rather than a definition.

**The interactive artifact** (`claude.ai/artifact/WbsS4P55WkVnk8AnYyYyK4`) moves all four roles together on its $\rho$ control, so it measures sensitivity to the rate *environment*, not to any one rate. If the separation is implemented, the natural replacement is two controls, $r_L$ and $d$ — and the payload would grow by the product of the two grids unless $\Delta r$ is computed in the page, which §4's algebra makes easy since only $\Psi(d)$ has to be pre-computed.

---

## 6. Still missing, and larger than any of this

The rate separation is worth ~6bp. These are worth more.

**Project default truncates the recovery leg, wrong-way.** $\Theta(d)$ assumes every window runs to maturity. The Facility's pattern is advance-early, recover-late, so a default at year 7 with the experience account in deficit destroys precisely the leg the pricing relies on — and default is most likely exactly when $X$ has fallen, which is when the deficit is deepest. This is asymmetrically bad for this instrument in a way it is not for a normal lender. The natural next computation is a **survival-weighted $\Theta$**: apply an annual project hazard (correlated with the $X$ path, not independent of it) to the experience-account ledger and see how much of the recovery leg survives. Expect it to move the premium by more than the whole 56–70bp range in §4.

**Lapse.** A pay-as-you-go premium the project can stop paying is a free option: cancel when $X$ is running well, keep it when $X$ is falling. A level annuity prices neither. Mandatory for the loan life, or priced as an option.

**Cost of solvency capital.** The premium should be $\Psi_{\text{pure}}+(r_C-r_f)\times(\text{capital held})+\text{expenses}$. Three separate things hide in "a low rate": $r_f$, what the capital earns while held, a genuine offset; $r_C$, what its provider requires — Solvency II's standard cost-of-capital spread is 6%, a reinsurer wants more, an MDB's is thin, **donor capital is ~0**; and who provides it, which is the actual answer. If the buffer is an EFSD+-style grant, the capital cost is not a running loading at all but a one-off, and the premium stays close to pure. That is the policy point the motivation is groping for: **the affordability result has two sources — the cyclicality of $X$, a fact about the world, and cheap capital and funding, a fact about who sponsors the Facility.** The single $\rho$ hides the second entirely.

**The $c\neq d$ lever.** Setting the carry rate on advances above the Facility's funding cost turns part of the insurance into lending and genuinely reduces the pure premium; setting it concessionally is a subsidy that raises it. Either is a live design choice the current model cannot express.
