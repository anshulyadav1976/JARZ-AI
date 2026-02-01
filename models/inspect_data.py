"""
Quick script to inspect the collected parquet data.
Shows columns, sample data, and basic statistics.
"""
import pandas as pd
from pathlib import Path

# Path to data
DATA_DIR = Path("../../data/raw")
FEATURES_FILE = DATA_DIR / "district_training_data.parquet"
TIMESERIES_FILE = DATA_DIR / "district_growth_timeseries.parquet"

print("=" * 80)
print("DISTRICT TRAINING DATA INSPECTION")
print("=" * 80)

# Load features dataset
if FEATURES_FILE.exists():
    df = pd.read_parquet(FEATURES_FILE)
    
    print(f"\n📊 SHAPE: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"💾 File size: {FEATURES_FILE.stat().st_size / 1024 / 1024:.2f} MB")
    
    print("\n" + "=" * 80)
    print("COLUMNS (Parameters)")
    print("=" * 80)
    for i, col in enumerate(df.columns, 1):
        print(f"{i:3d}. {col}")
    
    print("\n" + "=" * 80)
    print("SAMPLE DATA (first 5 districts)")
    print("=" * 80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df.head())
    
    print("\n" + "=" * 80)
    print("DATA SUMMARY")
    print("=" * 80)
    print(df.describe())
    
    print("\n" + "=" * 80)
    print("NON-NULL COUNTS")
    print("=" * 80)
    print(df.count().sort_values(ascending=False))
    
else:
    print(f"\n❌ Features file not found: {FEATURES_FILE}")

# Load time series dataset
if TIMESERIES_FILE.exists():
    print("\n\n" + "=" * 80)
    print("TIME SERIES DATA")
    print("=" * 80)
    
    ts = pd.read_parquet(TIMESERIES_FILE)
    print(f"\n📊 SHAPE: {ts.shape[0]} rows × {ts.shape[1]} columns")
    print(f"📍 Districts: {ts['district'].nunique()}")
    
    print("\nColumns:")
    for col in ts.columns:
        print(f"  - {col}")
    
    print("\nSample:")
    print(ts.head(10))
else:
    print(f"\n⚠️  Time series file not found: {TIMESERIES_FILE}")

print("\n" + "=" * 80)
print("HOW TO USE THIS DATA")
print("=" * 80)
print("""
# Load the data:
import pandas as pd
df = pd.read_parquet('../../data/raw/district_training_data.parquet')

# Access specific columns:
districts = df['district']
rent_prices = df['rent_demand_mean_pcm']
crime_total = df['crime_total_incidents']

# Filter by district:
nw1_data = df[df['district'] == 'NW1']

# Get all available features:
features = df.columns.tolist()

# Check for missing values:
df.isnull().sum()
""")
