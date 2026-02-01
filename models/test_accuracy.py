"""
Test model accuracy on new/test data.
"""
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error

MODEL_PATH = Path("src/models/rent_quantile_model.pkl")
DATA_PATH = Path("../data/raw/district_training_data.parquet")

# Load model and data
with open(MODEL_PATH, "rb") as f:
    artifact = pickle.load(f)

df = pd.read_parquet(DATA_PATH)

# Get target
target_col = artifact['target_col']
y_true = df[target_col].dropna()

# Prepare features
feature_names = artifact['feature_names']
X = df.loc[y_true.index, feature_names].fillna(0)

# Predict
model_p50 = artifact['models']['q50']
y_pred = model_p50.predict(X)

# Calculate metrics
mae = mean_absolute_error(y_true, y_pred)
rmse = np.sqrt(mean_squared_error(y_true, y_pred))
mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

print("=" * 80)
print("MODEL ACCURACY ON TEST DATA")
print("=" * 80)
print(f"\nSamples tested: {len(y_true)}")
print(f"\n🎯 Accuracy Metrics:")
print(f"   MAE:  £{mae:.2f}")
print(f"   RMSE: £{rmse:.2f}")
print(f"   MAPE: {mape:.2f}%")

# Show some examples
print("\n" + "=" * 80)
print("SAMPLE PREDICTIONS")
print("=" * 80)
sample_idx = np.random.choice(y_true.index, min(5, len(y_true)), replace=False)
for idx in sample_idx:
    actual = y_true.loc[idx]
    predicted = y_pred[list(y_true.index).index(idx)]
    error = predicted - actual
    error_pct = (error / actual) * 100
    
    district = df.loc[idx, 'district'] if 'district' in df.columns else 'Unknown'
    print(f"\nDistrict: {district}")
    print(f"  Actual:    £{actual:,.0f}/month")
    print(f"  Predicted: £{predicted:,.0f}/month")
    print(f"  Error:     £{error:+,.0f} ({error_pct:+.1f}%)")

# Distribution of errors
errors = y_pred - y_true
print("\n" + "=" * 80)
print("ERROR DISTRIBUTION")
print("=" * 80)
print(f"Mean error: £{errors.mean():.0f}")
print(f"Median error: £{errors.median():.0f}")
print(f"Std dev: £{errors.std():.0f}")
print(f"\nPercentage within ±10%: {(np.abs(errors/y_true) <= 0.1).mean()*100:.1f}%")
print(f"Percentage within ±20%: {(np.abs(errors/y_true) <= 0.2).mean()*100:.1f}%")
