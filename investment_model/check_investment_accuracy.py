"""
Check accuracy of the trained investment model.
"""
import pickle
from pathlib import Path

MODEL_PATH = Path("models/investment_roi_model.pkl")

if not MODEL_PATH.exists():
    print(f"❌ Model not found: {MODEL_PATH}")
    print("Run 'python src/train_investment_model.py' first")
    exit(1)

# Load model
with open(MODEL_PATH, "rb") as f:
    artifact = pickle.load(f)

print("=" * 80)
print("INVESTMENT MODEL ACCURACY REPORT")
print("=" * 80)

print(f"\n📊 Model Type: {artifact.get('model_type', 'Unknown')}")
print(f"   Features: {len(artifact.get('feature_names', []))}")
print(f"   Trained models: {len(artifact.get('models', {}))}")

print("\n" + "=" * 80)
print("PREDICTION TARGETS & ACCURACY")
print("=" * 80)

for target, desc in artifact.get('targets', {}).items():
    if target not in artifact['models']:
        continue
    
    model_data = artifact['models'][target]
    metrics = model_data['metrics']
    stats = model_data['target_stats']
    
    print(f"\n{desc}")
    print(f"{'=' * 60}")
    
    # Target statistics
    print(f"\n📈 Target Distribution:")
    print(f"   Mean: {stats['mean']:.2f}")
    print(f"   Std Dev: {stats['std']:.2f}")
    print(f"   Range: {stats['min']:.2f} to {stats['max']:.2f}")
    
    # Accuracy metrics
    print(f"\n🎯 Accuracy (Test Set):")
    print(f"   MAE (Mean Absolute Error): {metrics['test_mae']:.2f}")
    print(f"   RMSE (Root Mean Squared Error): {metrics['test_rmse']:.2f}")
    print(f"   R² Score: {metrics['test_r2']:.3f}")
    
    # Interpretation
    r2 = metrics['test_r2']
    if r2 > 0.8:
        rating = "Excellent (explains >80% variance)"
    elif r2 > 0.6:
        rating = "Good (explains 60-80% variance)"
    elif r2 > 0.4:
        rating = "Fair (explains 40-60% variance)"
    else:
        rating = "Needs improvement (<40% variance)"
    
    print(f"   → Model Quality: {rating}")
    
    # MAPE if applicable
    if stats['mean'] > 0:
        mape = (metrics['test_mae'] / stats['mean']) * 100
        print(f"   MAPE: {mape:.1f}%")
    
    # Top features
    importance = model_data.get('feature_importance')
    if importance is not None and len(importance) > 0:
        print(f"\n🔍 Top 5 Predictive Features:")
        for i, (_, row) in enumerate(importance.head(5).iterrows(), 1):
            print(f"   {i}. {row['feature']:35s} (importance: {row['importance']:.2f})")

print("\n" + "=" * 80)
print("WHAT THIS MEANS")
print("=" * 80)

print("""
These models predict investment performance for UK property districts:

1. **1-Year ROI**: Short-term return (appreciation + rental income)
2. **3-Year ROI**: Medium-term return projection  
3. **5-Year ROI**: Long-term return projection
4. **Annual Cash Flow**: Net rental income after all costs
5. **Rental Yield**: Current gross rental return rate

Higher R² scores (closer to 1.0) = more reliable predictions
Lower MAE = smaller average prediction error

Use these predictions to:
- Compare investment opportunities across districts
- Estimate expected returns for financial planning
- Identify high-yield vs high-appreciation markets
- Assess investment risk (via cash flow predictions)
""")
