# Kenya Case Study: Forward Hedge vs Emergency Liquidity Instrument

## Why Kenya?

Kenya is a representative case for the currency mismatch problem in African infrastructure finance. The Kenyan shilling has depreciated steadily against the US dollar over the past three decades -- from 22.9 KES/USD in 1990 to 139.8 KES/USD in 2023. A project with USD debt financed during this period faces obvious nominal currency risk. The conventional response is a forward hedge, but as this case study shows, the forward hedge is prohibitively expensive because it hedges a risk that largely does not need hedging.

## The data

Using World Bank data (1990-2023, 34 annual observations for Kenya), we construct:

- **Nominal exchange rate** X (USD/KES): declined from 0.0436 in 1990 to 0.0072 in 2023 -- an 84% cumulative nominal depreciation.
- **Hybrid (real) index** H = P/X: rose from 99.0 in 1990 to 444.5 in 2023 -- a 349% cumulative real appreciation.

The divergence between these two series is the central insight: Kenyan inflation has more than offset the nominal depreciation, so the USD value of inflation-indexed local-currency revenues has *increased* over time.

### Kenya exchange rate data (selected years)

| Year | H (real index) | X (USD/KES) | H relative to 1990 | X relative to 1990 |
|------|----------------|-------------|--------------------|--------------------|
| 1990 |           99.0 |      0.0436 |               1.00 |               1.00 |
| 1993 |           67.3 |      0.0172 |               0.68 |               0.40 |
| 1997 |          151.9 |      0.0170 |               1.53 |               0.39 |
| 2005 |          167.0 |      0.0132 |               1.69 |               0.30 |
| 2010 |          312.3 |      0.0126 |               3.15 |               0.29 |
| 2015 |          390.0 |      0.0102 |               3.94 |               0.23 |
| 2020 |          477.8 |      0.0094 |               4.83 |               0.22 |
| 2023 |          444.5 |      0.0072 |               4.49 |               0.16 |

## The problem with forward hedges

### How forwards are priced

Under covered interest parity (CIP), the forward rate is determined by the interest rate differential:

$$F_t = S_t \times \frac{1 + r_{KES}}{1 + r_{USD}}$$

For Kenya, where KES interest rates have historically been 8-14% and USD rates 1-5%, the **forward premium is approximately 5-10% per year**. This is a *certain* cost the project must pay every year for the life of the loan, regardless of what actually happens to the exchange rate.

Even using the most conservative estimate -- the average observed annual nominal depreciation of 2.8%/year from the data -- the cost is substantial.

### Forward hedge cost for a stylised 15-year project

Consider a project with 100 USD/year in debt service over 15 years (discount rate 10%).

|       Forward premium assumption      | Annual cost (% of DS) | PV of total cost | As % of debt stock |
|---------------------------------------|-----------------------|------------------|--------------------|
| 2.8%/year (observed avg depreciation) | 2.8%                  | 21.3 USD         | 2.8%               |
| 5.0%/year (moderate CIP estimate)     | 5.0%                  | 38.0 USD         | 5.0%               |
| 8.0%/year (high CIP estimate)         | 8.0%                  | 60.8 USD         | 8.0%               |

At 5% per year, the project surrenders 38 USD in present value -- **5% of the total debt stock** -- as certain cost. This directly erodes the debt service coverage ratio from day one and makes many projects unfinanceable. At 8%, the cost is 60.8 USD, or **8% of the debt stock**.

### What the forward hedge actually protects against

The forward hedge protects against *nominal* depreciation -- the entire movement in X. But for a project with inflation-indexed local-currency revenues, the relevant risk is not the full nominal depreciation but only the *real* component. The inflation component is naturally hedged by the tariff structure.

**Decomposition for Kenya (15-year windows):**

| Window | Nominal dep (annual) | Real appreciation (annual) | Cumulative inflation offset |
|--------|---------------------|---------------------------|---------------------------|
| 1990-2004 | -7.93% | +2.94% | x0.45 |
| 1995-2009 | -2.68% | +7.69% | x2.02 |
| 2000-2014 | -0.95% | +7.46% | x2.55 |
| 2005-2019 | -1.98% | +7.21% | x2.11 |
| 2009-2023 | -3.87% | +2.56% | x0.81 |

In every single 15-year window, inflation more than offset the nominal depreciation -- the real index H *appreciated*. The forward hedge pays to eliminate a risk that, for a project with inflation-indexed tariffs, does not materialise.

## The emergency liquidity instrument

### How it works

Instead of locking in a forward rate (certain cost, eliminates all FX exposure), the emergency liquidity instrument:

1. Lets the project keep its inflation-indexed local-currency revenues
2. Converts them to USD at the spot rate each year
3. When the *real* exchange rate H falls below its starting value, the facility provides a loan to cover the shortfall
4. When H is above the starting value, the surplus goes to an escrow to repay the facility
5. At maturity, the net position determines the gain or loss

The cost is the actuarially fair premium to cover the expected net loss across all possible outcomes.

### Kenya results: 20 rolling 15-year windows (1990-2023)

| Metric | Value |
|--------|-------|
| Windows analysed | 20 |
| Windows with real depreciation (H < starting value) | **0 of 20** |
| Kenya-specific premium | **0.00%** |
| Mean real appreciation over 15 years | +115% |
| Mean annual real appreciation | +6.3% |

**In every single 15-year window in the Kenya data, the project would have been fully repaid with surplus.** The emergency liquidity facility would never have been activated.

### Year-by-year CFADS comparison (Window 2005-2019)

| Year | H_t/H_0 (real) | X_t/X_0 (nominal) | CFADS (real, USD) | CFADS (nominal, USD) | Nominal shortfall |
|------|----------------|-------------------|--------------------|---------------------|--------------------|
| 2005 | 1.00 | 1.00 | 100 | 100 | 0 |
| 2006 | 1.27 | 1.05 | 127 | 105 | 0 |
| 2008 | 1.68 | 1.09 | 168 | 109 | 0 |
| 2010 | 1.87 | 0.95 | 187 | 95 | -5 |
| 2012 | 2.19 | 0.89 | 219 | 89 | -11 |
| 2015 | 2.34 | 0.77 | 234 | 77 | -23 |
| 2019 | 2.84 | 0.74 | 284 | 74 | -26 |
| **Total** | | | **3,082** | **1,341** | |
| **PV** | | | **1,404** | **716** | |
| **PV of DS** | | | **761** | **761** | |

Under the real (inflation-indexed) framework, the project generates **1,404 USD in PV** -- nearly double its debt service obligations. Under a pure nominal framework (without tariff indexation or hedging), it generates only 716 USD in PV against 761 USD of obligations -- a shortfall.

The forward hedge eliminates the nominal shortfall but at a cost of ~5% of debt stock per year. The emergency liquidity instrument achieves the same protection at 0% cost for Kenya specifically, or 0.46% at the diversified portfolio level.

## The cost comparison

|                             |              Forward hedge               |          Emergency liquidity          |
|-----------------------------|------------------------------------------|---------------------------------------|
| **What it covers**          | Full nominal depreciation                | Real depreciation only                |
| **Cost structure**          | Certain annual premium                   | Contingent; only paid if H declines   |
| **Annual cost (Kenya)**     | 2.8-8.0% of debt stock                   | 0.00% (Kenya-specific)                |
| **Annual cost (portfolio)** | 2.8-8.0% of debt stock                   | 0.46% of debt stock                   |
| **Cost ratio**              | **6-17x** more expensive                 | 1x (baseline)                         |
| **Effect on DSCR**          | Reduces by 2.8-8.0% from day one         | Reduces by 0.46% (portfolio)          |
| **Upside participation**    | None (locked in)                         | Full (keeps real appreciation)        |
| **Track record (Kenya)**    | Would have cost 2.8-8.0%/yr for 34 years | Never activated in any 15-year window |

## Why the forward hedge is too expensive

The forward premium compensates the hedge provider for the full expected nominal depreciation. But for a project with inflation-indexed tariffs, only the *real* component of that depreciation is a risk. The forward hedge is paying to eliminate a risk that the tariff structure already handles.

The decomposition is:

$$\underbrace{\text{Nominal depreciation}}_{\text{What forwards hedge}} = \underbrace{\text{Inflation}}_{\text{Naturally hedged by tariffs}} + \underbrace{\text{Real depreciation}}_{\text{What EL instrument hedges}}$$

For Kenya, inflation has averaged 5-10% per year, while the real exchange rate has *appreciated* at 2.6-9.0% per year. The forward hedge charges for the entire left-hand side. The emergency liquidity instrument charges only for the residual on the right -- which in Kenya's case has been zero.

This explains why forward-based currency hedges in developing countries have only been taken up when heavily subsidised: the premium is so large relative to project cash flows that it renders the project unviable. The emergency liquidity instrument resolves this by correctly identifying that the relevant risk is much smaller than the nominal depreciation suggests.

## Portfolio-level pricing

Even at the diversified portfolio level across all 52 African countries (where some countries *do* experience real depreciation), the premium is only **0.46% of debt stock per year**. This reflects:

- Only 27% of 15-year windows across Africa result in a net loss
- Diversification across countries and time periods sharply reduces the expected loss
- The probability of loss for Kenya specifically is 0%

The contrast is stark: a forward hedge for Kenya would cost 6-17x more than the portfolio-level emergency liquidity premium, while protecting against a risk that has never materialised in the historical record.
