# Emergency Liquidity for Hard Currency Debt Service: Findings Summary

## Motivation

Currency mismatch between local-currency revenues (from electricity sales) and hard-currency debt service obligations is a major barrier to infrastructure finance in developing countries. When exchange rates depreciate, utilities face debt service shortfalls that increase offtaker risk and raise the cost of capital. This analysis proposes and prices an **emergency liquidity insurance instrument** that absorbs the real exchange rate risk, allowing projects to meet their USD debt obligations even during periods of local currency weakness.

## Analytical Framework

### The Hybrid Index H

The core variable is:

$$H_{i,t} = \frac{P_{i,t}}{X_{i,t}}$$

where $P_{i,t}$ is the domestic price level and $X_{i,t}$ is the nominal exchange rate (USD/LCU) for country $i$. This index measures the USD value of a fixed basket of local goods. If electricity tariffs are inflation-adjusted, $H$ also tracks the USD value of a MWh of electricity over time.

### Stylised Project

A project with inflation-indexed local revenues and constant USD debt service of 100/year. Dollar cash flows available for debt service (CFADS) equal $H_{i,t} \cdot (r-c) \cdot E = 100$ at inception. Any decline in $H$ creates a debt service shortfall; any increase creates a surplus.

### The Instrument

A financial institution $\Gamma$ provides emergency liquidity loans when $H$ falls below its starting value, and collects repayments from an escrow funded by surpluses. The net present value of the lifetime position is:

$$\pi_{i,t_0 \to T} = \sum_{t=t_0}^{T} \frac{g_{i,t}}{(1+\rho)^t}$$

where $g_{i,t} = H_{i,t}/H_{i,t_0} - 1$. When $\pi < 0$, $\Gamma$ incurs a loss. The actuarially fair annual premium as a fraction of the debt stock is:

$$\Delta r = \frac{\mathbb{E}[\pi_{i,t_0 \to T}]}{\alpha^2_{\rho, T-t_0}}$$

where $\alpha_{\rho,t}$ is the present value of a unit annuity.

---

## Data

- **Source**: World Bank Development Indicators (PANUSATLS for exchange rates, NECONPRVTXN for price levels)
- **Coverage**: 52 African countries (all except Sao Tome and Principe and South Sudan due to missing data), 1990-2023
- **Variables constructed**: Hybrid index $H_{i,t}$, 5-year backward-looking moving average baseline, nominal exchange rate

---

## Key Results

### 1. Terminal Liability Analysis (Consolidated Notebook)

Using 15-year rolling windows across all countries (452 windows, 52 countries), with a 10% discount rate:

| Metric | Value |
|--------|-------|
| **Annual premium (as % of debt stock)** | **0.19%** |
| **Probability of loss for provider** | **16%** |
| **Number of country-windows** | 452 |

**Interpretation**: In 84% of 15-year windows, the project's surpluses fully repay the liquidity provider. The diversified portfolio-level cost of providing this insurance is remarkably low at ~19 basis points per year on the outstanding debt.

### 2. Solvency / Inverse Analysis

Using the same framework with $\rho = 0.1$ and tenor = 15 years (891 rolling windows, 1990-2023):

| Metric | Value |
|--------|-------|
| Annual premium as fraction of debt stock | 0.45% |
| Annual premium as fraction of annual debt service | 3.45% |

**Worst-case countries** (largest real depreciation over 15 years): Sudan (1991-2005), Nigeria (1998-2012), Ethiopia (1991-2005), Lesotho (1995-2009).

**Best-case countries** (strongest real appreciation): Ghana showed net PV gains of up to 200% of debt stock in several windows.

### 3. Event-Based Analysis

Depreciation events are identified as periods where $H$ falls more than 10% below its 5-year moving average baseline, ending when $H$ returns to within 10% of the baseline.

| Metric | Value |
|--------|-------|
| Total events detected | 86-93 (depending on parameters) |
| Countries experiencing events | 49 of 52 |
| Average event duration | 5.9 years |
| Pooled annual frequency | 0.059 events per country-year |
| Pooled mean event severity | 213.8% (area under curve) |
| Annual prevalence rate | 42% of country-years |
| Mean annual severity (when in event) | 21.6% below baseline |

**Top countries by expected annual loss**: Lesotho, Nigeria, Sudan, Ethiopia, Ghana.

### 4. Twenty-Year Rolling Integral Analysis

For 20-year project lives (455 windows across 45 countries):

| Metric | Value |
|--------|-------|
| Mean 20-year integral | -417.3% |
| Median 20-year integral | -484.4% |
| Standard deviation | 493.1% |
| Positive integrals (net appreciation) | ~10% of cases |

**Comparison with project finance coverage ratios**:

| Coverage Threshold | Probability of Breach |
|---|---|
| Conservative/AAA (200%) | 6.2% |
| Investment Grade (150%) | 7.3% |
| Sub-Investment Grade (100%) | 8.6% |
| High Risk (50%) | 9.5% |

### 5. Insurance Pricing (Event-Based Approach)

|     Rating Tier      | Activation Prob. | Expected Payout | Annual Fee | Economic Capital |
|----------------------|------------------|-----------------|------------|------------------|
| Conservative (AAA)   | 6.2%             | 38.6%           | 13.0%      | 1349.7%          |
| Investment Grade     | 7.3%             | 42.0%           | 13.7%      | 1399.7%          |
| Sub-Investment Grade | 8.6%             | 46.0%           | 14.3%      | 1449.7%          |
| High Risk            | 9.5%             | 50.5%           | 15.0%      | 1499.7%          |

### 6. Annual Prevalence Premium Sensitivity

| Confidence Level | Diversification Credit | Gross Premium | Premium Multiple |
|------------------|------------------------|---------------|------------------|
| 95%              | 0%                     | 15.5%         | 1.70x            |
| 95%              | 10%                    | 14.9%         | 1.65x            |
| 95%              | 20%                    | 14.4%         | 1.59x            |
| 99%              | 0%                     | 16.1%         | 1.77x            |

### 7. Monte Carlo Portfolio Simulation

Using a Poisson-Lognormal model ($\lambda = 0.062$ events/country/year, lognormal severity with $\mu_{log} = 4.50$, $\sigma_{log} = 1.26$):

| Portfolio Metric (52 countries) | Value  |
|---------------------------------|--------|
| Expected portfolio loss         | 17,181 |
| Standard deviation              | 4,083  |
| VaR (95%)                       | 24,329 |
| TVaR (95%)                      | 27,677 |
| VaR (99%)                       | 31,925 |
| TVaR (99%)                      | 36,852 |

---

## Key Takeaways

1. **The instrument is affordable at the portfolio level**: When diversified across the African continent, the actuarially fair premium for the emergency liquidity facility is approximately **0.19-0.45% of the debt stock per year** (depending on the methodology and discount rate). This is far lower than the currency risk premium currently embedded in project finance rates.

2. **Diversification is powerful**: Only 16% of 15-year country-windows result in a net loss for the liquidity provider. The majority of the time, real appreciation offsets temporary depreciations.

3. **Events are infrequent but severe**: Depreciation events occur at a rate of ~6% per country-year but last an average of 6 years and involve substantial cumulative losses (mean severity ~214% of baseline).

4. **Tail risk is concentrated**: Sudan, Nigeria, Ethiopia, and Lesotho account for the most extreme outcomes. A geographically diversified portfolio significantly reduces exposure to individual country tail events.

5. **The real exchange rate is far less volatile than the nominal rate**: Inflation partially offsets nominal depreciation, which is the core insight enabling affordable pricing. All 891 rolling windows for the nominal exchange rate showed net depreciation, whereas only ~40% showed real depreciation.

---

## Notebooks Overview

|                Notebook                |                                         Purpose                                         |
|----------------------------------------|-----------------------------------------------------------------------------------------|
| `consolidated_currency_analysis.ipynb` | Main analysis: motivation, model, data description, terminal liability calculation       |
| `SolvencyAnalysis.ipynb`               | Earlier version of terminal liability calculation with hybrid index                     |
| `SolvencyInverse.ipynb`                | Refined solvency analysis with both real and nominal comparisons                        |
| `events_From_baseline.ipynb`           | Event detection from MA baseline, actuarial pricing, 20-year rolling integrals          |
| `events_From_trough.ipynb`             | Alternative event detection measuring from trough, choropleth visualisation              |
| `new_event_analysis.ipynb`             | Annual prevalence approach, Bayesian modelling (PyMC), Monte Carlo portfolio simulation |
| `currency_v2.ipynb`                    | (Empty/developmental notebook)                                                          |
