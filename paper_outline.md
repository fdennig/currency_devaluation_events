# Pricing Real Exchange Rate Cover for African Infrastructure Finance

## Paper outline

*(Each heading carries a one-line description of its content; **Fig:** lines propose the graphs, most of which already exist in `wdi_hybrid_analysis.ipynb` / `consolidated_currency_analysis.ipynb`.)*

---

## 1. Motivation: the currency mismatch that blocks the deal

Hard-currency debt against local-currency revenues holds up African infrastructure transactions; dollarised PPAs "solve" it by dumping the FX risk on already-fragile offtakers, raising offtaker risk and capital costs twice over.

### 1.1 A stylised project

A plant earning inflation-indexed local tariffs worth $100/yr in USD at close, with USD debt service of exactly $100/yr (DSCR = 1 without loss of generality): any fall in the USD value of the local revenue basket is a debt-service shortfall and technical default.

### 1.2 The wrong decomposition and the right one

The market treats the exposure as *nominal* FX risk; but nominal depreciation = inflation differential + real depreciation, and an inflation-indexed tariff already passes the inflation component straight through to revenues — the project's true exposure is only the *real* residual.

---

## 2. The hybrid index: measuring the risk the project actually bears

Define H = P/X (local CPI over LCU-per-USD): the USD value of the local goods basket, hence of indexed revenues; in growth rates, ΔH ≈ local inflation − depreciation = US inflation − real depreciation, so H *is* the real exchange rate up to US prices.

- **Fig 2.1:** Two-panel country chart, USD/LCU (nominal) vs H (real), showing how much of the nominal collapse the index strips out — Kenya and Nigeria (`country_chart`, cell 2 of `wdi_hybrid_analysis.ipynb`; also `NGA/KEN_nominal_vs_real.png`).
- **Fig 2.2 (motivating fact):** Nigeria 2014–2024 — exchange rate ×9.4, price level ×4.8, H bottoms at 51 not 11: half the "currency collapse" was inflation the tariff repriced automatically.

---

## 3. Why the standard fixes overcharge: hedging is an inflation bet

Refinancing into local currency and rolling NDF hedges are the same trade (covered interest parity pins forwards to the rate differential), and both charge the *full* differential — expected inflation differential + expected real depreciation + risk premium — to shed an exposure of which the project only ever bore the real part.

### 3.1 The parity accounting

CIP (mechanical: forwards ≡ differential) vs UIP (behavioural: differential ≈ expected depreciation + premium); measured in revenue units, the extra cost of the local-currency loan over the USD loan collapses to the risk premium *if expectations are realised* — the inflation component is a wash in PV, paid as a certain coupon against an uncertain erosion of the nominal liability.

### 3.2 The hedger's residual risk position: long local inflation

The refinanced borrower's cash-flow health is CPI_t/CPI_0 against a liability fixed in local currency — only realised inflation pays back the prepaid differential, so the hedge does not remove risk but *rotates* it, turning a currency exposure into a forced long position in local inflation whose losing branch is a stable, low-inflation currency (the Kenya path, §8.3).

### 3.3 The position survives any repayment schedule

The obvious objection — negotiate a schedule that escalates with inflation instead of a level annuity — fixes coverage but not the exposure: a level annuity puts the weakness at the start, escalation removes every DSCR breach but settles more of the liability at future exchange rates, widening the dispersion of realised USD cost by ~10% across the Nigerian and Kenyan paths. Structuring relocates the bet between coverage and cost; only genuine CPI indexation removes it, and that instrument does not exist at tenor in these markets.

- **Fig 3.1:** Level vs escalating local-currency schedules on both realised paths — min DSCR, years below 1.0, and realised USD PV (from §8.2, `tbl-schedule-bet`), against the facility's flat DSCR = 1 and flat premium.

---

## 4. The instrument: an emergency liquidity facility for the real residual

Whenever H falls below its close-date level, the facility Γ lends the project exactly the debt-service shortfall; surplus years repay via an escrow; if the discounted net position at maturity T is negative, Γ absorbs it — insurance on the terminal PV of real-depreciation shortfalls, nothing more.

### 4.1 Risk positions compared

The facility client holds *no* inflation position at all, keeps the upside of real appreciation (terminal surplus returned), and is insured against real depreciation — versus the hedger, who must root for inflation, and the naked USD borrower, who defaults on real depreciation.

- **Fig 4.1 (schematic):** Three-row payoff diagram (naked / hedged / facility) against the two shocks (inflation, real depreciation), showing the facility as the only structure orthogonal to inflation.

---

## 5. Data and method

WDI CPI and exchange-rate series for ~50 African countries, 1995–2024 (Lesotho excluded for CPI breaks); for every country and every rolling 15-year window, compute the discounted sum of deviations g_t = H_t/H_0 − 1 — the terminal residual π — normalised by the annuity factor α into a PV per unit of debt stock.

### 5.1 The α-identity (the pivot between quotes)

π/α is simultaneously the PV loss as a fraction of the *debt stock* and the premium annuity as a fraction of *annual debt service*; π/α² is the flat annuity as a fraction of principal — which equals the interest-rate spread only for a bullet loan, while the true margin-equivalent on an amortising loan is ~1.5× larger (spread accrues on the declining balance).

- **Fig 5.1:** Single-country windows chart — H path with each 15-year window's start level and its residual bar, green/red by sign (`country_windows_styled`, cells 5–6).

---

## 6. Results: the cover costs basis points

Pooled over 718 windows in 50 countries (ρ = 5%): expected loss = 1.95% of debt stock in PV, only 17.8% of windows produce any loss — quoted three ways: **1.9% of each debt-service payment** (the actuarial quote), **19bp of principal per year flat**, or **29bp on the loan margin** of a 15-year annuity loan (19bp bullet).

- **Fig 6.1:** Histogram of terminal residuals across all windows, loss tail in red (cell 7).
- **Fig 6.2:** By-country expected loss, dual axis (fraction of annuity / fraction of debt stock), sorted worst-to-best (cell 8).
- **Fig 6.3:** Equivalent margin uplift by country, in bp, computed with `equivalent_rate` (cell 9) — the honest investor-facing number.

---

## 7. Country variation, regimes, and diversification

Expected loss ranges from exactly zero (Kenya, 16/16 windows non-negative) to ~97bp of principal per year (Nigeria, all losing windows straddling the 1999 unification); regime groups (EUR-linked / ZAR-linked / flexible) and cross-country correlations determine how far pooling compresses the premium below the standalone worst case.

- **Fig 7.1:** Correlation heatmap of annual ΔH ordered by regime (consolidated notebook, cell 17).
- **Fig 7.2:** Premium distribution by regime, box + strip (cell 13).
- **Fig 7.3:** Bootstrap distribution of the pooled premium, country-block resampling (cell 20) — the confidence band around "under 30bp".

---

## 8. Worked examples: how the cover pans out for an investor

### 8.1 Nigeria 2014: the path the refinance-minded investor fears

Full year-by-year ledger of a 2014 financial close through both devaluations (2015–16 and the 2023 float): the facility bridges every shortfall (drawdowns peak at 49% of one year's debt service in 2024), zero missed payments, cumulative facility balance ~24% of principal absorbed by Γ if H does not recover.

- **Fig 8.1:** Ledger table / stacked bar — revenue in USD, debt service, facility flow, running facility balance, 2014–2024.

### 8.2 Nigeria 2014, refinanced: right in PV, dead in year two

Honest counterfactual: the naira loan is ex-post *cheaper* in USD PV ($524 vs $772 — depreciation outran the priced differential), so the case against it is not expected cost but the exposure it creates. The level annuity breaches DSCR immediately (0.77 in 2015, 0.89 in 2016) — a purely structural breach, since after refinancing the exchange rate is irrelevant to coverage (2015 inflation was 9.0%, and 1.090/1.423 = 0.77). Escalating the schedule at the UIP-implied 8% removes the breach and *widens* the best-worst cost spread by ~10% (§3.3).

- **Fig 8.2:** DSCR paths, facility structure vs naira refinance, with the sub-1.0 zone shaded.

### 8.3 Kenya 2009: the certain coupon with no offset

The shilling refinance pays a 7-point differential against realised depreciation of ~2.7%/yr: ex-post overpayment of ~200bp of principal per year for a decade, while H never PV-net fell below any window start since 1995 — the facility client paid 19bp and never drew.

### 8.4 Scenario matrix

One table: {naked USD, USD + facility, local refinance, rolling NDF} × {certain cost, Nigeria path, Kenya path, failure mode} — the facility is the only row with no failure mode on any observed path.

---

## 9. Solvency: what capital the insurer actually needs

The *liquidity* commitment is bounded by one year of debt service (H > 0 caps the annual advance; worst observed single-year shortfall 75%), cheap for a AAA institution like AfDB to stand behind; the *solvency* capital must instead be sized off the terminal-loss tail (worst window 55% of debt stock, pooled 1st/5th percentile 39%/13%, far smaller for the diversified book via the §7 bootstrap).

---

## 10. Policy design and conclusion

Under 30bp pooled — but adverse selection (Nigerias buy, Kenyas don't) unravels pooled pricing toward the ~150bp standalone worst case, arguing for embedding the cover in DFI lending terms or tiering premia by country (Fig 6.3); caveats: post-1995 sample starts just after the 1994 CFA devaluation, and overlapping windows are handled by the block bootstrap.

---

## Appendix candidates

- Derivation of the α-identity and the bullet-vs-annuity spread correction.
- Revenue-numeraire derivation: extra cost of local refinance = risk premium when expectations are realised.
- All-country H panels (cell 11 grid); event-based robustness (`events_From_baseline.ipynb`).
