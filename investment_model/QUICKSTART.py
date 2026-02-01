"""
Investment Model - Quick Start Guide
"""

print("=" * 80)
print("INVESTMENT MODEL SETUP")
print("=" * 80)

print("""
This model predicts investment performance for UK property districts:
  • ROI over 1, 3, 5 years
  • Annual cash flow
  • Rental yields
  • Property value appreciation

STEP-BY-STEP GUIDE
==================

1. PREPARE DATA
   cd investment_model
   python src/get_investment_data.py
   
   This will:
   - Load the rental model's district data
   - Calculate historical ROI metrics
   - Engineer investment-specific features
   - Create target variables (1yr/3yr/5yr ROI)
   
2. TRAIN MODELS
   python src/train_investment_model.py
   
   This will:
   - Train separate models for each prediction target
   - Split data into train/test sets
   - Evaluate model performance
   - Save models to models/investment_roi_model.pkl
   
3. CHECK ACCURACY
   python check_investment_accuracy.py
   
   This will:
   - Load the trained models
   - Show test set accuracy for each target
   - Display feature importance
   - Explain what the metrics mean

EXAMPLE USAGE IN CODE
======================

```python
import pickle
import pandas as pd

# Load model
with open('models/investment_roi_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Prepare features for a district
features = {
    'sale_demand_mean_price': 350000,
    'rent_demand_mean_pcm': 1800,
    'growth_5yr_total_pct': 25.5,
    'crime_total_incidents': 150,
    # ... all other features
}

X = pd.DataFrame([{
    name: features.get(name, 0) 
    for name in model['feature_names']
}])

# Predict each target
for target, desc in model['targets'].items():
    prediction = model['models'][target]['model'].predict(X)[0]
    print(f"{desc}: {prediction:.2f}")

# Output example:
# 1-Year Total ROI (%): 8.5
# 3-Year Total ROI (%): 28.2
# 5-Year Total ROI (%): 52.3
# Annual Cash Flow (£): 3200
# Gross Rental Yield (%): 6.2
```

WHAT THE MODEL PREDICTS
========================

For each district, you get:

1. **1yr_total_roi**: Total return after 1 year (%)
   - Includes: rental income + property appreciation
   - Use for: Short-term flip or quick return strategies

2. **3yr_total_roi**: Total return after 3 years (%)
   - Use for: Medium-term investment planning

3. **5yr_total_roi**: Total return after 5 years (%)
   - Use for: Long-term buy-and-hold strategy evaluation

4. **estimated_annual_cash_flow**: Net annual income (£)
   - After: mortgage, maintenance, void periods, management
   - Use for: Assessing if property is cash-flow positive

5. **gross_rental_yield**: Annual rent / property value (%)
   - Use for: Comparing rental returns across districts

INTEGRATING WITH YOUR API
==========================

In backend/app/agent/tools.py, add:

```python
from pathlib import Path
import pickle

# Load investment model
INVESTMENT_MODEL_PATH = Path("../../investment_model/models/investment_roi_model.pkl")

async def predict_investment_returns(district: str, features: dict) -> dict:
    with open(INVESTMENT_MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    X = pd.DataFrame([{
        name: features.get(name, 0)
        for name in model['feature_names']
    }])
    
    predictions = {}
    for target in model['targets'].keys():
        pred = model['models'][target]['model'].predict(X)[0]
        predictions[target] = float(pred)
    
    return predictions
```

QUESTIONS THIS ANSWERS
=======================

✓ "How much will my investment be worth in 5 years?"
✓ "What ROI can I expect in district NW1?"
✓ "Will this property generate positive cash flow?"
✓ "Which district has the best rental yield?"
✓ "Should I invest in E14 or SW6?"

""")

print("=" * 80)
print("Ready to start? Run: python src/get_investment_data.py")
print("=" * 80)
