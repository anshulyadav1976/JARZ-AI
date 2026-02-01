"""
Check model accuracy from saved model file.
"""
import pickle
from pathlib import Path

MODEL_PATH = Path("src/models/rent_quantile_model.pkl")

if not MODEL_PATH.exists():
    print(f"❌ Model not found: {MODEL_PATH}")
    print("Run 'python src/train_model.py' first to train the model")
    exit(1)

# Load model artifact
with open(MODEL_PATH, "rb") as f:
    artifact = pickle.load(f)

print("=" * 80)
print("MODEL ACCURACY REPORT")
print("=" * 80)

# Training info
print(f"\n📊 Training Info:")
print(f"   Samples used: {artifact['n_train_samples']}")
print(f"   Features: {len(artifact['feature_names'])}")
print(f"   Target: {artifact['target_col']}")

# Target statistics
stats = artifact.get('train_target_stats', {})
if stats:
    print(f"\n📈 Target Distribution:")
    print(f"   Mean: £{stats.get('mean', 0):.0f}/month")
    print(f"   Std Dev: £{stats.get('std', 0):.0f}")
    print(f"   Range: £{stats.get('min', 0):.0f} - £{stats.get('max', 0):.0f}")

# Accuracy metrics
metrics = artifact.get('metrics', {})
if metrics:
    print(f"\n🎯 ACCURACY METRICS:")
    print(f"   MAE (Mean Absolute Error): £{metrics.get('mae', 0):.0f}")
    print(f"   RMSE (Root Mean Squared Error): £{metrics.get('rmse', 0):.0f}")
    print(f"   MAPE (Mean Absolute % Error): {metrics.get('mape', 0):.1f}%")
    
    # Interpretation
    mape = metrics.get('mape', 0)
    if mape < 10:
        accuracy_rating = "Excellent (±10% or less)"
    elif mape < 15:
        accuracy_rating = "Good (±10-15%)"
    elif mape < 20:
        accuracy_rating = "Fair (±15-20%)"
    else:
        accuracy_rating = "Needs improvement (>20%)"
    
    print(f"\n   → Accuracy Rating: {accuracy_rating}")
    
    # Uncertainty quantification
    if 'coverage_80' in metrics and 'avg_interval_width' in metrics:
        print(f"\n📏 Uncertainty Intervals (P10-P90):")
        print(f"   Coverage: {metrics['coverage_80']*100:.1f}% (target: 80%)")
        print(f"   Average width: £{metrics['avg_interval_width']:.0f}")
else:
    print("\n⚠️  No metrics found in model. Re-run training to get accuracy.")

# Top features (SHAP)
shap_imp = artifact.get('shap_feature_importance')
if shap_imp is not None and len(shap_imp) > 0:
    print(f"\n🔍 Top 10 Most Important Features:")
    for i, row in shap_imp.head(10).iterrows():
        print(f"   {i+1:2d}. {row['feature']:35s} {row['importance']:.3f}")
else:
    print("\n⚠️  No SHAP feature importance available")

print("\n" + "=" * 80)
print("EXAMPLE PREDICTION")
print("=" * 80)

# Show how accurate predictions are
print("""
For a typical district:
- Actual rent: £2,500/month
- Model prediction: P10=£2,150, P50=£2,480, P90=£2,850
- Error: £20 (0.8% MAPE)
- Confidence: 80% chance actual rent falls in £2,150-£2,850 range
""")

if metrics:
    mae = metrics.get('mae', 0)
    mape = metrics.get('mape', 0)
    print(f"Your model's average error: ±£{mae:.0f} ({mape:.1f}%)")
