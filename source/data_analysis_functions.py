"""
fxrisk.py

Core functions for FX risk research paper.
"""

# Load data, extract exchange rates, and normalize them
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import altair as alt
# alt.data_transformers.enable('default')

# Load the CSV file into a pandas DataFrame
file_path = '../data/priceIndex_and_exchangeRate_series_2025_SP.csv'  # Replace with your CSV file path
data = pd.read_csv(file_path, index_col=0)

african_countries = [
    'DZA', 'AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CMR', 'CPV', 'CAF', 'TCD', 'COM', 'COG', 'CIV',
    'COD', 'DJI', 'EGY', 'GNQ', 'ERI', 'SWZ', 'ETH', 'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN',
    'LBY', 'LSO', 'LBR', 'MDG', 'MWI', 'MLI', 'MRT', 'MUS', 'MAR', 'MOZ', 'NAM', 'NER', 'NGA',
    'RWA', 'STP', 'SEN', 'SYC', 'SLE', 'SOM', 'ZAF', 'SSD', 'SDN', 'TZA', 'TGO', 'TUN', 'UGA',
    'ZMB', 'ZWE'
]

# Exchange rate regime classification (based on IMF AREAER, predominant arrangement 2000-2023)
# Three groups:
#   "EUR-linked"  — CFA franc zone (WAEMU+CEMAC) plus Comoros and Cape Verde, all pegged to EUR
#   "ZAR-linked"  — Common Monetary Area members pegged 1:1 to South African rand
#   "Flexible"    — managed floats, crawling pegs, and market-determined rates
fx_regime = {
    # CFA Franc Zone — WAEMU (pegged to EUR via French Treasury)
    'BEN': 'EUR-linked', 'BFA': 'EUR-linked', 'CIV': 'EUR-linked', 'GNB': 'EUR-linked',
    'MLI': 'EUR-linked', 'NER': 'EUR-linked', 'SEN': 'EUR-linked', 'TGO': 'EUR-linked',
    # CFA Franc Zone — CEMAC (pegged to EUR via French Treasury)
    'CMR': 'EUR-linked', 'CAF': 'EUR-linked', 'TCD': 'EUR-linked', 'COG': 'EUR-linked',
    'GNQ': 'EUR-linked', 'GAB': 'EUR-linked',
    # Other EUR-pegged (separate monetary authorities, same anchor)
    'COM': 'EUR-linked', 'CPV': 'EUR-linked',
    # Common Monetary Area — pegged 1:1 to ZAR
    'LSO': 'ZAR-linked', 'NAM': 'ZAR-linked', 'SWZ': 'ZAR-linked',
    # All others default to 'Flexible' — see classify_regime()
}

def build_hybrid_index_and_ma_df(
    start="1990-01-01",
    end="2023-01-01",
    ma_window=5,
    countries=african_countries,
    df=data
):
    """
    Build a hybrid real exchange rate index and its moving average for specified countries.
    
    This function creates a real exchange rate index by dividing the local price index
    by the nominal exchange rate, normalized to 100 at the first valid observation. A falling 
    index indicates currency depreciation/devaluation.
    
    Parameters
    ----------
    start : str, default "1990-01-01"
        Start date for the analysis period in YYYY-MM-DD format.
    end : str, default "2023-01-01"
        End date for the analysis period in YYYY-MM-DD format.
    ma_window : int, default 5
        Window size in years for the moving average baseline calculation.
    countries : list, default african_countries
        List of 3-letter ISO country codes to process.
    df : pd.DataFrame, default data
        Input DataFrame with exchange rate and price data. Expected columns:
        - {COUNTRY}PANUSATLS: Nominal exchange rate (LCU per USD)
        - {COUNTRY}NECONPRVTXN: Consumer price index
        
    Returns
    -------
    pd.DataFrame
        Tidy DataFrame with columns:
        - country: 3-letter ISO country code
        - year: Year as integer
        - fx_index: Real exchange rate index (normalized to 100)
        - baseline: Moving average of fx_index over ma_window years
        
    Notes
    -----
    - Countries with missing data columns are skipped with a warning
    - The function requires ma_window years of data before start date for MA calculation
    - All rows with NaN values are dropped from the final result
    - Index normalization ensures cross-country comparability
    
    Examples
    --------
    >>> # Get data for 2000-2020 with 3-year moving average
    >>> df = build_hybrid_index_and_ma_df(
    ...     start="2000-01-01", 
    ...     end="2020-01-01", 
    ...     ma_window=3
    ... )
    """

    start_date = pd.to_datetime(start)
    sd_minus_window = start_date - pd.DateOffset(years=ma_window-1) 
    df.index = pd.to_datetime(df.index)
    df = df[(df.index >= sd_minus_window) & (df.index <= end)]
    
    records = []

    for country in countries:
        panusatls_col = f"{country}PANUSATLS"
        price_level_col = f"{country}NECONPRVTXN"

        if panusatls_col not in df.columns or price_level_col not in df.columns:
            print(f"Missing columns for {country}")
            continue

        series = df[price_level_col] / df[panusatls_col]
        first_valid = series.first_valid_index()
        if first_valid is None:
            print(f"No data for {country}")
            continue

        # normalize to 100 at first valid point
        series_norm = series / series.loc[first_valid] * 100
        series_ma = series_norm.rolling(window=ma_window, min_periods=ma_window).mean()

        # Also keep the nominal exchange rate (PANUSATLS) for the output
        nominal_fx_series = 1/df[panusatls_col]

        for date, index_val, ma_val, nominal_fx in zip(
            series_norm.index, series_norm.values, series_ma.values, nominal_fx_series.values
        ):
            if date >= start_date and not pd.isna(index_val):
                records.append({
                    "country": country,
                    "year": date.year,
                    "fx_index": float(index_val),
                    "baseline": float(ma_val) if not pd.isna(ma_val) else np.nan,
                    "nominal_fx": float(nominal_fx) if not pd.isna(nominal_fx) else np.nan
                })
                
    tidy_df = pd.DataFrame(records).sort_values(["country", "year"]).reset_index(drop=True)
    return tidy_df.dropna()

def compute_terminal_residuals(
    df,
    years=15,
    discount_rate=0.05,
    window_mode="two_non_overlapping"  # or "rolling"
):
    """
    Compute terminal residuals (PV of net normalized deviations) for fixed-horizon windows.
    
    df must have: 'country', 'year', 'hybrid_index'

    Returns DataFrame with:
      country, window_start, window_end, baseline_value, net_pv, loss
    """
    out = []
    af = (1 - (1 + discount_rate) ** -years) / discount_rate
    
    for country, g in df.groupby("country"):
        g = g.sort_values("year").reset_index(drop=True)
        n = len(g)
        
        if n < years:
            continue

        # choose window starts
        if window_mode == "two_non_overlapping":
            starts = list(range(0, n - years + 1, years))[:2]  # up to 2 per run
        elif window_mode == "rolling":
            starts = list(range(0, n - years + 1))
        else:
            raise ValueError("window_mode must be 'two_non_overlapping' or 'rolling'")

        for i0 in starts:
            win = g.iloc[i0:i0+years].copy()

            # skip windows with missing values in fx_index
            if win["fx_index"].isna().any():
                continue

            base = float(win["fx_index"].iloc[0])
            base_nominal = float(win["nominal_fx"].iloc[0])

            # signed normalized deviation
            git = (win["fx_index"].to_numpy() / base) - 1.0
            # git_nominal = (win["nominal_fx"].to_numpy() / base_nominal) - 1.0

            # discount factors to start of window (year-end cashflows)
            t = np.arange(1, years + 1, dtype=float)
            dfactors = (1.0 + discount_rate) ** (-t)

            piit = float(np.sum(git * dfactors))
            # net_pv_nominal= float(np.sum(git_nominal * dfactors))
            net_pv_per_debt_stock = piit / af**2
            loss   = min(net_pv_per_debt_stock, 0.0)

            out.append({
                "country": country,
                "window_start": int(win["year"].iloc[0]),
                "window_end": int(win["year"].iloc[-1]),
                "baseline": base,
                "net_pv_by_debt_stock": net_pv_per_debt_stock,
                "loss": loss,    
            })

    return pd.DataFrame(out)
# Example usage:
# residuals = compute_terminal_residuals(df, years=15, discount_rate=0.05,
#                                        window_mode="two_non_overlapping")
# expected_loss = residuals["loss"].mean()
# prob_positive = (residuals["loss"] > 0).mean()

def identify_events(
    df, 
    trigger_threshold = 0.1,
    end_threshold = 0.1,
    countries = african_countries
):
    """
    Identify currency devaluation events using peak detection and threshold analysis.
    
    This function detects significant currency devaluation episodes by:
    1. Finding local troughs in the real exchange rate index
    2. Identifying events where troughs exceed trigger_threshold below baseline
    3. Determining event end when index returns to end_threshold within baseline
    4. Filtering overlapping events to select the most severe ones
    5. Augmenting the input DataFrame with event indicators and annual loss calculations
    
    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame from build_hybrid_index_and_ma_df with columns:
        - country: 3-letter ISO country code
        - year: Year as integer  
        - fx_index: Real exchange rate index
        - baseline: Moving average baseline
    trigger_threshold : float, default 0.1
        Minimum deviation below baseline (as fraction) to trigger an event.
        E.g., 0.1 = 10% below baseline.
    end_threshold : float, default 0.1
        Maximum deviation from baseline (as fraction) to end an event.
        E.g., 0.0 = return to baseline level.
    countries : list, default african_countries
        List of 3-letter ISO country codes to analyze.
        
    Returns
    -------
    events : pd.DataFrame
        DataFrame of identified devaluation events with columns:
        - Country: 3-letter ISO country code
        - Start_Date: Year when event began (first point below trigger)
        - End_Date: Year when event ended (return back above end threshold) or last data year
        - Peak_Date: Year of maximum devaluation during event
        - Duration: Event length in years
        - Peak_Devaluation: Maximum percentage deviation from baseline during event
        - Devaluation_at_End: Percentage deviation from baseline at event end
        - Drawdown_Area: Cumulative percentage-point loss over event duration
    df_events : pd.DataFrame
        Augmented input DataFrame with additional columns:
        - in_event: Binary indicator (1 if country-year is in a devaluation event, 0 otherwise)
        - annual_loss: Annual loss as fraction relative to event start baseline (negative values only)
        
    Notes
    -----
    Algorithm Details:
    - Uses scipy.signal.argrelextrema to find local minima (troughs)
    - Requires "clean" fall: no intermediate peaks above trigger during run-up
    - For overlapping events, selects those with greatest drawdown area first,
      then lowest peak devaluation as tiebreaker
    - Ongoing events (no return to threshold) use end of sample as event end
    - Drawdown area calculated as cumulative deviation from baseline over time
    
    Event Quality Filters:
    - Skips events with intermediate peaks during fall phase
    - Handles incomplete events that don't return to baseline
    - Prevents double-counting of overlapping episodes
    
    Annual Loss Calculation:
    - annual_loss calculated as (fx_index - event_start_baseline) / event_start_baseline
    - Only negative deviations (actual losses below baseline) are recorded
    - Uses baseline from event start date as reference for entire event duration
    - Non-event years have annual_loss = 0.0
    
    Event Marking:
    - in_event = 1 for all country-years within identified event periods
    - in_event = 0 for country-years outside of events
    - Allows for easy calculation of annual prevalence rates
    
    Examples
    --------
    >>> # Detect major devaluation events (>20% trigger, return to baseline)
    >>> events, df_events = identify_events(
    ...     df, 
    ...     trigger_threshold=0.20,
    ...     end_threshold=0.0
    ... )
    
    >>> # Check annual prevalence
    >>> prevalence = df_events['in_event'].mean()
    >>> print(f"Annual prevalence: {prevalence:.1%}")
    
    >>> # Calculate total annual losses
    >>> total_annual_loss = df_events['annual_loss'].sum()
    >>> total_event_loss = events['Drawdown_Area'].sum()
    """

    # Add in_event column to dataframe
    if 'in_event' not in df.columns:
        df['in_event'] = 0
    # If annual_loss column doesn't exist, create it
    if 'annual_loss' not in df.columns:
        df['annual_loss'] = 0.0
    results = []

    for country in countries:
        country_data = df[df.country == country]

        # Check if country has any data in the filtered dataframe
        if len(country_data) == 0:
            continue  # Skip countries with no data
        
        year         = country_data["year"].values
        fx_index     = country_data["fx_index"].values
        baseline     = country_data["baseline"].values

        troughs_new_indices = argrelextrema(fx_index, np.less)[0]
        if len(fx_index) >= 2 and fx_index[-1] < fx_index[-2]:
            troughs_new_indices = np.append(troughs_new_indices, len(fx_index) - 1)

        # Store events for this country to filter overlaps
        country_events = []

        for p_new_idx in np.arange(len(year)):
            trigger_level = baseline[p_new_idx] * (1. - trigger_threshold)  # Use trigger threshold
            end_level     = baseline[p_new_idx] * (1. - end_threshold)  # This changes with end_threshold!

            possible_event_troughs = troughs_new_indices[troughs_new_indices > p_new_idx]
            if possible_event_troughs.size == 0:
                continue

            for t_new_idx in possible_event_troughs:

                if fx_index[t_new_idx] <= trigger_level:
                    end_date = None
                    event_duration = None
                    max_drop = None
                    max_devaluation = None
                    drawdown_area = None
                    
                    intermediate_troughs = 0
                    for i in range(p_new_idx+1, t_new_idx):
                        if fx_index[i] > trigger_level:  # Check against trigger level
                            intermediate_troughs += 1
                    if intermediate_troughs > 0:
                        continue # skip this event if there are intermediate troughs, as it is not a clean rise and fall

                    for idx in range(t_new_idx+1, len(fx_index)):
                        if fx_index[idx] >= end_level:
                            # time measures
                            end_date = year[idx]
                            event_duration = year[idx] - year[p_new_idx] + 1    # inclusive of both start and end years

                            # max amplitude
                            max_drop = t_new_idx
                            for i in troughs_new_indices[(troughs_new_indices>t_new_idx) & (troughs_new_indices<idx)]:
                                if fx_index[i] < fx_index[max_drop]:
                                    max_drop = i
                            max_devaluation = (fx_index[max_drop] - baseline[p_new_idx]) / baseline[p_new_idx] * 100

                            # total dollar loss in percent of CFADS
                            integrand = np.minimum(fx_index/baseline[p_new_idx] - 1, 0.0) * 100 # percentage deviation from baseline at event start date
                            drawdown_area = np.sum(integrand[p_new_idx:idx+1]) #sum of integrand over event period
                            break

                    else: # if return condition not met, repeat with end period
                        idx = len(fx_index) -1
                        end_date = year[idx]
                        event_duration = year[idx] - year[p_new_idx] + 1    # inclusive of both start and end years
                        max_drop = t_new_idx
                        for i in troughs_new_indices[(troughs_new_indices>t_new_idx)]:
                            if fx_index[i] > fx_index[max_drop]:
                                max_drop = i
                        max_devaluation = (fx_index[max_drop] - baseline[p_new_idx]) / baseline[p_new_idx] * 100
                        integrand = np.minimum(fx_index/baseline[p_new_idx] - 1, 0.0) * 100 # percentage deviation from baseline at event start date
                        drawdown_area = np.sum(integrand[p_new_idx:idx+1]) #sum of integrand over event period

                    country_events.append({
                        "Country": country, 
                        "Start_Date": year[p_new_idx],
                        "End_Date": end_date,
                        "Peak_Date": year[max_drop],
                        "Duration": event_duration,
                        "Peak_Devaluation": max_devaluation,
                        "Devaluation_at_End": (fx_index[idx] - baseline[p_new_idx]) / baseline[p_new_idx] * 100,
                        "Drawdown_Area": drawdown_area
                    })

        # Filter overlapping events for this country
        selected = []
        if country_events:
            # Sort by Drawdown_Area ascending, then by Peak_Devaluation ascending
            country_events.sort(key=lambda x: (x['Drawdown_Area'], x['Peak_Devaluation'])) # , reverse=True
            
            
            used_intervals = []
            for event in country_events:
                start = event['Start_Date']
                end = event['End_Date']
                # Check for overlap
                overlap = False
                for s, e in used_intervals:
                    if not (end < s or start > e):
                        overlap = True
                        break
                if not overlap:
                    selected.append(event)
                    used_intervals.append((start, end))
            
            results.extend(selected)

            
        # Mark country-years as being in an event
        for event in selected:
            start = event['Start_Date']
            end = event['End_Date']
            event_years_mask = (
                (df['country'] == country) & 
                (df['year'] >= start) & 
                (df['year'] <= end)
            )
            # Mark rows as being in an event
            df.loc[event_years_mask, 'in_event'] = 1
            
            # Get baseline at event start date for reference
            start_baseline = df.loc[(df['country'] == country) & (df['year'] == start), 'baseline'].values[0]
            
            # Calculate annual loss for each year in the event
            for idx in df.loc[event_years_mask].index:
                current_fx = df.loc[idx, 'fx_index']
                loss = (current_fx - start_baseline) / start_baseline
                # Only record negative deviations (actual losses)
                df.loc[idx, 'annual_loss'] = min(loss, 0.0)

    return pd.DataFrame(results), df

def annuity_factor(n_years=15, r=0.05):
    """
    Calculate present value annuity factor for converting lump sum to annual payments.
    
    Parameters
    ----------
    n_years : int, default 15
        Number of years for the annuity
    r : float, default 0.05
        Annual discount rate
        
    Returns
    -------
    float
        Present value annuity factor
    """
    if r == 0:
        return n_years
    return (1 - (1 + r) ** (-n_years)) / r

def build_decomposition_df(
    start="2000-01-01",
    end="2023-12-31",
    ma_window=5,
    countries=african_countries,
    df=data
):
    """
    Build nominal, real, and PPP-expected FX indices for decomposition analysis.

    Decomposes the nominal exchange rate movement into:
    - The PPP-expected (forward-implied) depreciation path, driven by inflation differentials
    - The real exchange rate index (the residual, which is what matters for inflation-adjusted revenues)

    Under covered interest parity with equal real rates, the forward rate prices in
    depreciation equal to the inflation differential. The PPP-expected path is thus:
        ppp_expected(t) = 100 × [CPI_US(t)/CPI_US(t0)] / [CPI_local(t)/CPI_local(t0)]

    Key identity: real_fx_index(t) = nominal_fx_index(t) × CPI_local(t)/CPI_local(t0)

    Parameters
    ----------
    start : str, default "2000-01-01"
        Start date for the analysis period.
    end : str, default "2023-12-31"
        End date for the analysis period.
    ma_window : int, default 5
        Window size in years for the moving average baseline.
    countries : list, default african_countries
        List of 3-letter ISO country codes to process.
    df : pd.DataFrame, default data
        Input DataFrame with exchange rate and price data.

    Returns
    -------
    pd.DataFrame
        Tidy DataFrame with columns:
        - country, year
        - nominal_fx_index: Nominal USD/LCU index, normalized to 100
        - nominal_fx_baseline: 5-year MA of nominal index
        - real_fx_index: Real exchange rate H=P/X, normalized to 100
        - real_fx_baseline: 5-year MA of real index
        - ppp_expected_path: Forward-implied nominal path under PPP
    """
    start_date = pd.to_datetime(start)
    sd_minus_window = start_date - pd.DateOffset(years=ma_window - 1)
    df.index = pd.to_datetime(df.index)
    df = df[(df.index >= sd_minus_window) & (df.index <= end)]

    us_cpi = df["USANECONPRVTXN"]
    records = []

    for country in countries:
        panusatls_col = f"{country}PANUSATLS"
        price_level_col = f"{country}NECONPRVTXN"

        if panusatls_col not in df.columns or price_level_col not in df.columns:
            print(f"Missing columns for {country}")
            continue

        local_cpi = df[price_level_col]
        nominal_fx_raw = 1.0 / df[panusatls_col]       # USD per LCU
        real_fx_raw = local_cpi / df[panusatls_col]     # H = P / X

        # Find first valid point where all series are available
        combined = pd.concat(
            [nominal_fx_raw, real_fx_raw, local_cpi, us_cpi], axis=1
        ).dropna()
        if len(combined) == 0:
            print(f"No valid data for {country}")
            continue
        first_valid = combined.index[0]

        # Normalize all indices to 100 at first valid date
        nominal_fx_norm = nominal_fx_raw / nominal_fx_raw.loc[first_valid] * 100
        real_fx_norm = real_fx_raw / real_fx_raw.loc[first_valid] * 100

        # PPP-expected path: where nominal rate would be under relative PPP
        # Forward rates price in depreciation = inflation differential
        ppp_expected = 100.0 * (
            (us_cpi / us_cpi.loc[first_valid]) /
            (local_cpi / local_cpi.loc[first_valid])
        )

        # Moving average baselines
        nominal_fx_ma = nominal_fx_norm.rolling(
            window=ma_window, min_periods=ma_window
        ).mean()
        real_fx_ma = real_fx_norm.rolling(
            window=ma_window, min_periods=ma_window
        ).mean()

        for date, nom, nom_ma, real_v, real_ma, ppp in zip(
            nominal_fx_norm.index,
            nominal_fx_norm.values, nominal_fx_ma.values,
            real_fx_norm.values, real_fx_ma.values,
            ppp_expected.values,
        ):
            if date < start_date:
                continue
            if any(pd.isna(v) for v in [nom, nom_ma, real_v, real_ma, ppp]):
                continue
            records.append({
                "country": country,
                "year": date.year,
                "nominal_fx_index": float(nom),
                "nominal_fx_baseline": float(nom_ma),
                "real_fx_index": float(real_v),
                "real_fx_baseline": float(real_ma),
                "ppp_expected_path": float(ppp),
            })

    return (
        pd.DataFrame(records)
        .sort_values(["country", "year"])
        .reset_index(drop=True)
    )


def calculate_simple_risk_premium(df_events):
    """
    Calculate prevalence, annual severity, and pure risk premium from df_events.
    
    Parameters
    ----------
    df_events : pd.DataFrame
        DataFrame from identify_events() with columns:
        - country: 3-letter ISO country code
        - year: Year as integer
        - in_event: Binary indicator (1 if in event, 0 otherwise)
        - annual_loss: Annual loss as fraction (negative values)
        
    Returns
    -------
    dict
        Dictionary with:
        - prevalence: Proportion of country-years in events
        - mean_annual_severity: Mean annual loss when losses occur (%)
        - pure_risk_premium: Expected annual loss per country-year (%)
        - total_exposure: Total country-year observations
        - event_exposure: Number of country-years in events
    """
    
    # Total exposure (all country-years)
    total_exposure = len(df_events)
    
    if total_exposure == 0:
        return {
            'prevalence': 0.0,
            'mean_annual_severity': 0.0,
            'pure_risk_premium': 0.0,
            'total_exposure': 0,
            'event_exposure': 0
        }
    
    # Event exposure (country-years in events)
    event_years = df_events[df_events['in_event'] == 1]
    event_exposure = len(event_years)
    
    # Prevalence rate
    prevalence = event_exposure / total_exposure
    
    if event_exposure == 0:
        return {
            'prevalence': 0.0,
            'mean_annual_severity': 0.0,
            'pure_risk_premium': 0.0,
            'total_exposure': total_exposure,
            'event_exposure': 0
        }
    
    # Annual severity (convert to percentage and take absolute value)
    annual_losses = event_years['annual_loss'].abs() * 100
    mean_annual_severity = annual_losses.mean()
    
    # Pure risk premium (expected annual loss per country-year)
    pure_risk_premium = prevalence * mean_annual_severity
    
    return {
        'prevalence': prevalence,
        'mean_annual_severity': mean_annual_severity,
        'pure_risk_premium': pure_risk_premium,
        'total_exposure': total_exposure,
        'event_exposure': event_exposure
    }

def calculate_event_based_risk_premium(events, df_events):
    """
    Calculate event-based frequency, severity, and pure risk premium.
    
    Parameters
    ----------
    events : pd.DataFrame
        Event-level data from identify_events() with columns:
        - Country: 3-letter ISO country code
        - Start_Date, End_Date: Event dates
        - Duration: Event length in years
        - Drawdown_Area: Total event loss (%)
    df_events : pd.DataFrame
        Country-year data with columns:
        - country: 3-letter ISO country code
        - year: Year as integer
        
    Returns
    -------
    dict
        Dictionary with:
        - frequency: Events per country-year at risk (time-at-risk adjusted)
        - mean_severity: Mean total event loss when events occur (%)
        - pure_risk_premium: Expected event loss per country-year at risk (%)
        - total_exposure: Total country-years in dataset
        - time_at_risk: Country-years not in events (exposure for new events)
        - total_events: Number of events detected
    """
    
    # Total exposure (all country-years in dataset)
    total_exposure = len(df_events)
    
    if total_exposure == 0 or len(events) == 0:
        return {
            'frequency': 0.0,
            'mean_severity': 0.0,
            'pure_risk_premium': 0.0,
            'total_exposure': total_exposure,
            'time_at_risk': total_exposure,
            'total_events': 0
        }
    
    # Calculate time at risk (exclude country-years already in events)
    total_event_duration = events['Duration'].sum()
    time_at_risk = total_exposure - total_event_duration
    
    # Number of events
    total_events = len(events)
    
    # Event-based frequency (events per country-year at risk)
    if time_at_risk > 0:
        frequency = total_events / time_at_risk
    else:
        frequency = 0.0
    
    # Event-based severity (mean total event loss)
    mean_severity = events['Drawdown_Area'].mean()
    
    # Pure risk premium (expected event loss per country-year at risk)
    pure_risk_premium = frequency * mean_severity
    
    return {
        'frequency': frequency,
        'mean_severity': mean_severity,
        'pure_risk_premium': pure_risk_premium,
        'total_exposure': total_exposure,
        'time_at_risk': time_at_risk,
        'total_events': total_events
    }



# ---------------------------------------------------------------------------
# Tariff indexation
#
# The baseline model assumes the PPA tariff is indexed continuously and
# contemporaneously to the domestic price level, so that dollar revenue tracks
# Q = P/S exactly. Real contracts do not work that way. The functions below
# replace P with an *applied* index P~ -- the index actually embedded in the
# tariff -- and leave everything downstream (R, V, LLCR, premium, delta r)
# unchanged, since the project's dollar revenue index is then Q~ = P~/S.
#
# Five knobs, each drawn from an observed mechanism:
#
#   lag             periods between the index reference date and the date it is
#                   applied. Inflation-linked bonds: 3 months (Canada/US), 8
#                   months (old UK). REIPPPP: about 9 months.
#   reset_every     periods the nominal tariff is held flat between
#                   adjustments; 1 = continuous. Ghana PURC AAF: quarterly.
#                   Nigeria MYTO minor review: biannual. REIPPPP: annual.
#   ref_window      periods averaged to form the reference index. REIPPPP uses
#                   the preceding calendar year's average CPI, not a point read.
#   threshold       log movement required before a reset is executed. MYTO
#                   adjusts only on a material variation of plus/minus 5%.
#   share           fraction of the index movement passed through (partial
#                   indexation); 1.0 = full.
#
# plus an optional true-up, which is a different animal from the five above:
#
#   arrears_recovery  fraction of accumulated under-recovery repaid later, as
#                   in Eskom's Regulatory Clearing Account. A hold with no
#                   recovery is a permanent level loss; a true-up turns the
#                   same event into a timing gap. Recovery in practice runs
#                   3-6 years behind the cost.
#
# DEFAULTS REPRODUCE THE CURRENT MODEL EXACTLY. With steps_per_year=1, lag=0,
# reset_every=1, ref_window=1, threshold=0, share=1 the applied index is the
# raw annual price level and Q~ is identical to Q, element for element.
#
# Sub-annual rules (quarterly, biannual) need steps_per_year > 1, which
# interpolates the annual period-averages onto a finer grid and averages the
# resulting dollar revenue back up over the year. That re-aggregation is not
# free: it moves the pooled premium by roughly 2bp on its own, more than the
# effect of any realistic timing lag. Compare like with like -- read a
# sensitivity against a full-indexation baseline computed at the same
# steps_per_year, never against the annual headline number.
# ---------------------------------------------------------------------------

INDEXATION_FULL = dict(lag=0, reset_every=1, ref_window=1, threshold=0.0, share=1.0)


def _upsample_log(values, steps_per_year=1):
    """Log-linear interpolation of an annual period-average series onto a
    sub-annual grid, anchoring each annual observation at the middle of its
    year. steps_per_year=1 returns log(values) unchanged.

    The ends are held flat rather than extrapolated (np.interp clamps), so the
    first and last half-year are approximated by the annual figure itself.
    Extrapolating to NaN instead would silently drop the most recent window for
    every country.
    """
    v = np.log(np.asarray(values, dtype=float))
    if steps_per_year == 1:
        return v
    m = int(steps_per_year)
    ok = np.isfinite(v)
    anchors = np.arange(len(v)) * m + (m - 1) / 2.0
    return np.interp(np.arange(len(v) * m), anchors[ok], v[ok])


def applied_log_index(log_price, t0, n_steps, lag=0, reset_every=1,
                      ref_window=1, threshold=0.0, share=1.0):
    """Log of the index actually embedded in the tariff, step by step.

    log_price : log price index on the working grid
    t0        : grid position of financial close (the contract's base date)
    n_steps   : contract length in grid steps

    The base is the reference index observed at close, so the escalation factor
    is 1 at t0 by construction and a constant offset in log_price cancels out
    of R = Q~/Q~[0] - 1.
    """
    def reference(t):
        end = max(0, t - lag)
        start = max(0, end - ref_window + 1)
        seg = log_price[start:end + 1]
        return float(np.mean(seg)) if len(seg) else float(log_price[0])

    base = applied = reference(t0)
    path = np.empty(n_steps)
    for k in range(n_steps):
        if k > 0 and reset_every > 0 and k % reset_every == 0:
            candidate = base + share * (reference(t0 + k) - base)
            if abs(candidate - applied) >= threshold:
                applied = candidate
        path[k] = applied
    return path


def indexed_revenue_path(log_price, log_fx, t0, n_steps,
                         arrears_recovery=0.0, recovery_periods=None,
                         arrears_rate=0.0, **rule):
    """Dollar revenue index over a contract: exp(applied index - log fx), plus
    an optional true-up surcharge amortising accumulated under-recovery."""
    applied = applied_log_index(log_price, t0, n_steps, **rule)
    revenue = np.exp(applied - log_fx[t0:t0 + n_steps])
    if arrears_recovery <= 0.0:
        return revenue

    allowed = np.exp(log_price[t0:t0 + n_steps] - log_fx[t0:t0 + n_steps])
    horizon = int(recovery_periods or rule.get('reset_every', 1) or 1)
    surcharge = np.zeros(n_steps)
    balance = 0.0
    for k in range(n_steps):
        # accrue the shortfall net of any surcharge already being paid
        balance = balance * (1.0 + arrears_rate) + (allowed[k] - revenue[k] - surcharge[k])
        if k > 0 and k % horizon == 0:
            claim = arrears_recovery * balance
            balance -= claim
            surcharge[k:k + horizon] += claim / horizon
    return revenue + surcharge


def utility_buffered_payment_path(ppa, retail, buffer_capacity=np.inf,
                                  passthrough=1.0, arrears_rate=0.0):
    """What the IPP is actually paid, once the offtaker's balance sheet is put
    between the PPA obligation and the retail tariff.

    The two tiers are different kinds of object. The PPA tariff is contractual:
    it escalates by whatever the contract says, and the offtaker owes it whether
    or not the regulator has let the retail tariff keep up. The retail tariff is
    political. The difference lands on the utility, which can carry it for a
    while and not indefinitely -- which is why Africa's state utilities look the
    way they do.

    ppa, retail : per-period LCU obligation and revenue, normalised internally
                  so that retail exactly covers the PPA payment at close (the
                  utility's analogue of the project's DSCR = 1 assumption)
    buffer_capacity : how large a cumulative deficit the balance sheet can
                  carry, in periods of PPA payment. np.inf = the offtaker is
                  never the binding constraint, which is the model's default
                  and reduces this function to the identity.
    passthrough : share of the un-absorbed deficit that lands on the IPP as
                  non-payment. The remainder is a sovereign bailout -- Nigeria's
                  NBET payment-assurance facility, Kenya's Treasury letters of
                  support -- which is the ad hoc version of the instrument this
                  paper prices.
    arrears_rate : interest accruing on amounts owed to the IPP but unpaid.

    Returns the per-period payment actually received, on the same normalisation
    as `ppa`. Arrears are repaid out of later surpluses, so a temporary squeeze
    is a timing gap and only a persistent one is a loss.
    """
    ppa = np.asarray(ppa, dtype=float) / float(ppa[0])
    retail = np.asarray(retail, dtype=float) / float(retail[0])
    paid = np.empty(len(ppa))
    carried = 0.0    # deficit sitting on the utility balance sheet
    arrears = 0.0    # owed to the IPP and unpaid

    for k in range(len(ppa)):
        arrears *= (1.0 + arrears_rate)
        gap = ppa[k] - retail[k]
        if gap >= 0.0:
            absorbed = min(gap, max(0.0, buffer_capacity - carried))
            carried += absorbed
            unpaid = (gap - absorbed) * passthrough
            arrears += unpaid
            paid[k] = ppa[k] - unpaid
        else:
            surplus = -gap
            repaid = min(surplus, arrears)
            arrears -= repaid
            carried = max(0.0, carried - (surplus - repaid))
            paid[k] = ppa[k] + repaid
    return paid


def compute_indexed_residuals(df, years=15, discount_rate=0.05, start_year=None,
                              price_col='cpi', fx_col='exchange_rate',
                              group_col='iso3', name_col='country',
                              steps_per_year=1, retail_rule=None,
                              buffer_capacity=np.inf, buffer_passthrough=1.0,
                              buffer_arrears_rate=0.0, **rule):
    """Rolling-window PV of lifetime P&L per unit of debt stock, under a given
    indexation rule. Mirrors compute_terminal_residuals but with the applied
    index in place of the raw price level.

    `rule` is the PPA's own indexation -- what the IPP is contractually owed.
    Pass `retail_rule` to add the offtaker tier: the retail tariff is then
    indexed by that second rule, and the IPP is paid in full only while the
    utility's balance sheet can carry the difference. `buffer_capacity` is in
    years of PPA payment. Leaving `retail_rule` at None assumes the offtaker
    always pays, which is what the model does today.

    At the default rule this returns exactly what the current model returns on
    Q = P/S, so any deviation is the indexation rule and not the plumbing.
    """
    af = (1 - (1 + discount_rate) ** -years) / discount_rate
    m = int(steps_per_year)
    out = []

    for key, g in df.dropna(subset=[price_col, fx_col]).groupby(group_col):
        g = g.sort_values('year').reset_index(drop=True)
        n = len(g)
        if n < years:
            continue
        log_price = _upsample_log(g[price_col].to_numpy(), m)
        log_fx = _upsample_log(g[fx_col].to_numpy(), m)

        for i0 in range(0, n - years + 1):
            win = g.iloc[i0:i0 + years]
            if start_year is not None and int(win['year'].iloc[0]) < start_year:
                continue
            t0, n_steps = i0 * m, years * m
            if retail_rule is None:
                revenue = indexed_revenue_path(log_price, log_fx, t0, n_steps, **rule)
            else:
                ppa = np.exp(applied_log_index(log_price, t0, n_steps, **rule))
                retail = np.exp(applied_log_index(log_price, t0, n_steps, **retail_rule))
                paid = utility_buffered_payment_path(
                    ppa, retail, buffer_capacity=buffer_capacity * m,
                    passthrough=buffer_passthrough, arrears_rate=buffer_arrears_rate)
                revenue = paid * np.exp(-log_fx[t0:t0 + n_steps])
            annual = revenue.reshape(years, m).mean(axis=1)
            if not np.isfinite(annual).all() or annual[0] <= 0:
                continue

            R_it = annual / annual[0] - 1.0
            t = np.arange(1, years + 1, dtype=float)
            V_i = float(np.sum(R_it * (1.0 + discount_rate) ** (-t)))
            out.append({
                group_col: key,
                name_col: win[name_col].iloc[0] if name_col in win else key,
                'window_start': int(win['year'].iloc[0]),
                'window_end': int(win['year'].iloc[-1]),
                'net_pv_by_debt_stock': V_i / af,
                'loss': min(V_i / af, 0.0),
            })

    return pd.DataFrame(out)
