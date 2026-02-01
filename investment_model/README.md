# Investment ROI Prediction Model

Predicts investment performance metrics for UK property investments.

## What This Model Predicts

1. **ROI over X years** - Total return on investment after 1, 5, 10 years
2. **Property value appreciation** - Expected property value growth
3. **Annual cash flow** - Net rental income after costs
4. **Break-even point** - How many years until investment pays off
5. **Rental yield trends** - Gross and net yield projections

## Model Architecture

**Approach**: Time-series forecasting with gradient boosting
- **Input**: Current property/area features + historical growth data
- **Output**: Multi-horizon predictions (1yr, 3yr, 5yr, 10yr)
- **Method**: XGBoost/LightGBM with temporal features

## Key Features Used

### Property Metrics
- Purchase price / current valuation
- Property type, size, condition
- Current rental income

### Market Data
- Historical price growth (5yr, 10yr trends)
- Rental demand trends
- Days on market / inventory levels
- Sale transaction volumes

### Location Factors
- Area price growth momentum
- Spatial features (neighbor performance)
- Crime rates
- Transport links / amenities

### Financial Metrics
- Mortgage rates
- Operating costs (maintenance, management, insurance)
- Void periods
- Capital gains tax considerations

## Training Data

Uses same district-level data as rental model (`../data/raw/`) plus:
- Historical property value growth time series
- Sale price trends
- Rental yield history
- Market cycle indicators

## Usage

```bash
# 1. Prepare data (reuses rental model data + adds investment metrics)
python src/get_investment_data.py

# 2. Train investment prediction models
python src/train_investment_model.py

# 3. Check accuracy
python check_investment_accuracy.py
```

## Model Outputs

For a given property/district, predicts:

```python
{
    "1yr_roi": 4.2,           # % return after 1 year
    "3yr_roi": 15.8,          # % return after 3 years
    "5yr_roi": 28.5,          # % return after 5 years
    "10yr_roi": 62.3,         # % return after 10 years
    "property_value_1yr": 385000,   # Expected value in 1 year
    "property_value_5yr": 465000,   # Expected value in 5 years
    "annual_cash_flow": 4200,       # Net annual income
    "break_even_years": 6.8,        # Years to break even
    "gross_yield": 5.2,             # Current gross yield
    "net_yield": 3.8,               # Current net yield
}
```

## Compared to Rental Model

| Aspect | Rental Model | Investment Model |
|--------|--------------|------------------|
| **Predicts** | Current rent (P10/P50/P90) | Future ROI, value, cash flow |
| **Time horizon** | Now | 1-10 years |
| **Type** | Cross-sectional | Time-series forecasting |
| **Target** | Rent PCM | ROI %, property value |
| **Use case** | "What rent can I get?" | "Should I invest? What returns?" |
