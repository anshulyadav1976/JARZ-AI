"""
Investment-specific Data Preparation
Extends the rental model data with investment metrics and historical returns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple

# Paths
DATA_DIR = Path("../../data/raw")  # Read-only - original rental data
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Input files (from rental model) - READ ONLY
DISTRICT_FEATURES = DATA_DIR / "district_training_data.parquet"
GROWTH_TIMESERIES = DATA_DIR / "district_growth_timeseries.parquet"

# Output files - investment model's own data (won't touch original)
INVESTMENT_FEATURES = OUTPUT_DIR / "investment_training_data.parquet"
INVESTMENT_TIMESERIES = OUTPUT_DIR / "investment_timeseries.parquet"


def calculate_historical_roi(df_growth: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate historical ROI for various time horizons from growth data.
    
    For each district, compute:
    - 1yr, 3yr, 5yr property value appreciation
    - Estimated rental yield (rent/price)
    - Total ROI (appreciation + rental income)
    """
    roi_records = []
    
    for district in df_growth['district'].unique():
        ts = df_growth[df_growth['district'] == district].sort_values(['year', 'month'])
        
        if len(ts) < 12:  # Need at least 1 year of data
            continue
        
        # Get price data
        prices = ts['avg_price'].values
        dates = pd.to_datetime(ts[['year', 'month']].rename(columns={'month': 'month', 'year': 'year'}).assign(day=1))
        
        record = {'district': district}
        
        # Calculate appreciation over different horizons
        if len(prices) >= 12:  # 1 year
            start_price = prices[-12]
            end_price = prices[-1]
            if start_price > 0:
                record['1yr_appreciation'] = ((end_price - start_price) / start_price) * 100
                record['1yr_price_start'] = start_price
                record['1yr_price_end'] = end_price
        
        if len(prices) >= 36:  # 3 years
            start_price = prices[-36]
            end_price = prices[-1]
            if start_price > 0:
                record['3yr_appreciation'] = ((end_price - start_price) / start_price) * 100
                record['3yr_annual_avg'] = record['3yr_appreciation'] / 3
        
        if len(prices) >= 60:  # 5 years
            start_price = prices[-60]
            end_price = prices[-1]
            if start_price > 0:
                record['5yr_appreciation'] = ((end_price - start_price) / start_price) * 100
                record['5yr_annual_avg'] = record['5yr_appreciation'] / 5
        
        # Volatility (important for risk assessment)
        pct_changes = ts['pct_change'].dropna()
        if len(pct_changes) > 0:
            record['price_volatility'] = pct_changes.std()
            record['max_drawdown'] = pct_changes.min()
            record['best_month'] = pct_changes.max()
        
        # Trend strength (momentum indicator)
        if len(prices) >= 24:
            recent_12mo = prices[-12:].mean()
            previous_12mo = prices[-24:-12].mean()
            if previous_12mo > 0:
                record['momentum'] = ((recent_12mo - previous_12mo) / previous_12mo) * 100
        
        roi_records.append(record)
    
    return pd.DataFrame(roi_records)


def generate_synthetic_roi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate ROI estimates from REAL API growth data.
    Uses actual historical growth metrics from ScanSan API.
    """
    roi_records = []
    
    for idx, row in df.iterrows():
        district = row.get('district')
        if not district:
            continue
        
        record = {'district': district}
        
        # Use REAL growth metrics from API
        growth_5yr = row.get('growth_5yr_total_pct')  # Actual 5-year growth from API
        growth_latest_pct = row.get('growth_latest_pct_change')  # Recent trend
        growth_latest_price = row.get('growth_latest_avg_price')
        growth_start_price = row.get('growth_5yr_start_price')
        
        # Calculate appreciation based on REAL historical data
        if pd.notna(growth_5yr) and pd.notna(growth_start_price) and growth_start_price > 0:
            # Use actual 5-year growth
            record['5yr_appreciation'] = growth_5yr
            record['5yr_annual_avg'] = growth_5yr / 5
            
            # Estimate 1yr and 3yr based on recent momentum
            if pd.notna(growth_latest_pct):
                # Recent trend indicates current market
                record['1yr_appreciation'] = growth_latest_pct
            else:
                # Use average annual rate
                record['1yr_appreciation'] = growth_5yr / 5
            
            record['3yr_appreciation'] = record['1yr_appreciation'] * 3
            
            # Price data for validation
            if pd.notna(growth_latest_price):
                record['1yr_price_end'] = growth_latest_price
                record['1yr_price_start'] = growth_latest_price / (1 + record['1yr_appreciation']/100)
        
        elif pd.notna(growth_latest_pct):
            # Only have recent data - extrapolate
            record['1yr_appreciation'] = growth_latest_pct
            record['3yr_appreciation'] = growth_latest_pct * 3
            record['5yr_appreciation'] = growth_latest_pct * 5
            record['5yr_annual_avg'] = growth_latest_pct
        
        else:
            # No growth data - skip this district
            continue
        
        # Volatility from growth data
        if 'growth_avg_yearly_pct' in row.index and pd.notna(row.get('growth_avg_yearly_pct')):
            avg_growth = row['growth_avg_yearly_pct']
            record['price_volatility'] = abs(record['1yr_appreciation'] - avg_growth)
        else:
            record['price_volatility'] = abs(record['1yr_appreciation']) * 0.2
        
        # Momentum (recent vs historical average)
        record['momentum'] = record['1yr_appreciation'] - record['5yr_annual_avg']
        
        roi_records.append(record)
    
    df_roi = pd.DataFrame(roi_records)
    print(f"  Using REAL API growth data for {len(df_roi)} districts")
    return df_roi


def add_investment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add investment-specific derived features.
    
    Features:
    - Price-to-rent ratio (affordability indicator)
    - Rental yield estimates
    - Cash flow potential
    - Investment risk scores
    """
    df = df.copy()
    
    # Price-to-rent ratio (lower = better rental yield)
    if 'sale_demand_mean_price' in df.columns and 'rent_demand_mean_pcm' in df.columns:
        annual_rent = df['rent_demand_mean_pcm'] * 12
        df['price_to_rent_ratio'] = df['sale_demand_mean_price'] / annual_rent.replace(0, np.nan)
        
        # Gross rental yield
        df['gross_rental_yield'] = (annual_rent / df['sale_demand_mean_price'].replace(0, np.nan)) * 100
        
        # Estimated net yield (assuming 25% costs)
        df['net_rental_yield'] = df['gross_rental_yield'] * 0.75
        
        # Annual cash flow estimate (with typical mortgage at 75% LTV, 4.5% rate)
        mortgage_amount = df['sale_demand_mean_price'] * 0.75
        monthly_rate = 0.045 / 12
        num_payments = 25 * 12
        monthly_mortgage = mortgage_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        monthly_costs = df['rent_demand_mean_pcm'] * 0.25  # Operating costs
        monthly_cash_flow = df['rent_demand_mean_pcm'] - monthly_mortgage - monthly_costs
        df['estimated_annual_cash_flow'] = monthly_cash_flow * 12
    
    # Market liquidity (how quickly can you sell?)
    if 'sale_demand_days_on_market' in df.columns:
        # Lower days = more liquid market
        df['market_liquidity_score'] = 100 / (1 + df['sale_demand_days_on_market'] / 30)
    
    # Supply/demand balance
    if 'current_sale_listings' in df.columns and 'sale_demand_avg_transactions' in df.columns:
        df['months_of_supply'] = df['current_sale_listings'] / df['sale_demand_avg_transactions'].replace(0, np.nan)
        # Lower = seller's market (better for appreciation)
        df['seller_market_indicator'] = 100 / (1 + df['months_of_supply'])
    
    # Capital growth potential (from 5yr trends)
    if 'growth_5yr_total_pct' in df.columns:
        df['capital_growth_score'] = df['growth_5yr_total_pct'].clip(lower=0)
    
    # Total investment attractiveness score (composite)
    score_components = []
    if 'gross_rental_yield' in df.columns:
        score_components.append(df['gross_rental_yield'].fillna(0) * 10)  # Weight yields highly
    if 'capital_growth_score' in df.columns:
        score_components.append(df['capital_growth_score'].fillna(0) * 2)
    if 'market_liquidity_score' in df.columns:
        score_components.append(df['market_liquidity_score'].fillna(0))
    
    if score_components:
        df['investment_score'] = sum(score_components) / len(score_components)
    
    return df


def create_investment_targets(df: pd.DataFrame, df_roi: pd.DataFrame) -> pd.DataFrame:
    """
    Create target variables for training.
    
    Targets to predict:
    - 1yr_roi, 3yr_roi, 5yr_roi (total return including appreciation + rental income)
    - property_value_future (for different horizons)
    - is_good_investment (binary classification)
    """
    # Merge historical ROI data
    df = df.merge(df_roi, on='district', how='left')
    
    # Calculate total ROI (appreciation + rental income)
    for horizon in ['1yr', '3yr', '5yr']:
        appreciation_col = f'{horizon}_appreciation'
        if appreciation_col in df.columns and 'gross_rental_yield' in df.columns:
            # Total ROI = capital gain + rental income
            years = int(horizon[0])
            rental_return = df['gross_rental_yield'] * years
            df[f'{horizon}_total_roi'] = df[appreciation_col] + rental_return
    
    # Binary classification: good investment or not
    # Good = positive cash flow OR >5% annual ROI
    if 'estimated_annual_cash_flow' in df.columns and '5yr_annual_avg' in df.columns:
        df['is_good_investment'] = (
            (df['estimated_annual_cash_flow'] > 0) | 
            (df['5yr_annual_avg'] > 5)
        ).astype(int)
    
    return df


def prepare_investment_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main function to prepare investment training data.
    
    Returns:
        (features_df, timeseries_df)
    """
    print("=" * 80)
    print("INVESTMENT DATA PREPARATION")
    print("=" * 80)
    
    # Load base data
    print("\nLoading rental model data...")
    df_features = pd.read_parquet(DISTRICT_FEATURES)
    
    # Load growth timeseries if it exists
    if GROWTH_TIMESERIES.exists():
        df_growth = pd.read_parquet(GROWTH_TIMESERIES)
        print(f"  Districts: {len(df_features)}")
        print(f"  Time points: {len(df_growth)}")
    else:
        print(f"  Districts: {len(df_features)}")
        print("  ⚠️  No timeseries data found - will use synthetic growth estimates")
        # Create minimal synthetic growth data
        districts = df_features['district'].unique()
        prices = df_features.set_index('district')['sale_demand_mean_price']
        
        rows = []
        for district in districts:
            price = prices.get(district)
            if pd.notna(price) and price > 0:
                rows.append({
                    'district': district,
                    'year': 2023,
                    'month': 12,
                    'avg_price': price,
                    'pct_change': 0.5,
                    'transactions': 50,
                })
        df_growth = pd.DataFrame(rows)
    
    # Calculate historical ROI
    print("\nCalculating historical ROI metrics...")
    df_roi = calculate_historical_roi(df_growth)
    
    if len(df_roi) == 0:
        print("  No historical ROI data - generating estimates from current metrics")
        # Generate synthetic ROI based on current growth rates
        df_roi = generate_synthetic_roi(df_features)
    
    print(f"  Districts with ROI data: {len(df_roi)}")
    
    # Add investment features
    print("\nEngineering investment features...")
    df_features = add_investment_features(df_features)
    
    # Create targets
    print("\nCreating target variables...")
    df_investment = create_investment_targets(df_features, df_roi)
    
    # Summary
    print("\n" + "=" * 80)
    print("DATA SUMMARY")
    print("=" * 80)
    
    investment_cols = [c for c in df_investment.columns if 'roi' in c.lower() or 'yield' in c.lower() or 'cash_flow' in c.lower()]
    print(f"\nInvestment features: {len(investment_cols)}")
    print(f"Sample columns: {investment_cols[:10]}")
    
    # Show some statistics
    if '5yr_total_roi' in df_investment.columns:
        valid_roi = df_investment['5yr_total_roi'].dropna()
        if len(valid_roi) > 0:
            print(f"\n5-Year Total ROI Statistics:")
            print(f"  Mean: {valid_roi.mean():.1f}%")
            print(f"  Median: {valid_roi.median():.1f}%")
            print(f"  Std Dev: {valid_roi.std():.1f}%")
            print(f"  Range: {valid_roi.min():.1f}% to {valid_roi.max():.1f}%")
    
    return df_investment, df_growth


if __name__ == "__main__":
    # Prepare data
    df_features, df_timeseries = prepare_investment_data()
    
    # Save
    print("\n" + "=" * 80)
    print("SAVING DATA")
    print("=" * 80)
    
    df_features.to_parquet(INVESTMENT_FEATURES, index=False)
    print(f"✅ Saved features: {INVESTMENT_FEATURES}")
    print(f"   {len(df_features)} rows × {len(df_features.columns)} columns")
    
    df_timeseries.to_parquet(INVESTMENT_TIMESERIES, index=False)
    print(f"✅ Saved timeseries: {INVESTMENT_TIMESERIES}")
    print(f"   {len(df_timeseries)} rows")
    
    print("\n✅ Investment data preparation complete!")
    print("\nNext step: python src/train_investment_model.py")
