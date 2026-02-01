"""
Investment ROI Prediction Model Training
Trains models to predict investment returns over multiple time horizons.
"""

import pickle
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

try:
    import lightgbm as lgb
    USE_LIGHTGBM = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor
    USE_LIGHTGBM = False

warnings.filterwarnings('ignore')

# Paths
DATA_DIR = Path("data")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

INPUT_DATA = DATA_DIR / "investment_training_data.parquet"
MODEL_PATH = MODEL_DIR / "investment_roi_model.pkl"

# Targets to predict
PREDICTION_TARGETS = {
    '1yr_total_roi': '1-Year Total ROI (%)',
    '3yr_total_roi': '3-Year Total ROI (%)',
    '5yr_total_roi': '5-Year Total ROI (%)',
    'estimated_annual_cash_flow': 'Annual Cash Flow (£)',
    'gross_rental_yield': 'Gross Rental Yield (%)',
}


def load_investment_data() -> pd.DataFrame:
    """Load prepared investment data."""
    print("Loading investment data...")
    if not INPUT_DATA.exists():
        raise FileNotFoundError(
            f"Run 'python src/get_investment_data.py' first.\n"
            f"Missing: {INPUT_DATA}"
        )
    
    df = pd.read_parquet(INPUT_DATA)
    print(f"  Loaded {len(df)} districts")
    print("  Note: Outlier removal will happen AFTER train/test split to prevent data leakage")
    
    return df


def prepare_features(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare feature matrix and target for a specific prediction target.
    """
    # Exclude columns that shouldn't be features
    exclude = {
        'district', 'area_code_type', 'error', 'lat', 'lon', 'region',
        # Don't use other targets as features
        '1yr_total_roi', '3yr_total_roi', '5yr_total_roi',
        '1yr_appreciation', '3yr_appreciation', '5yr_appreciation',
        '1yr_price_start', '1yr_price_end', '3yr_annual_avg', '5yr_annual_avg',
        'is_good_investment',
        # Exclude features that leak target information (correlation > 0.99)
        'investment_score', 'gross_rental_yield', 'net_rental_yield',
        'estimated_annual_cash_flow', 'capital_growth_score',
    }
    
    # Get target
    y = df[target_col].copy()
    valid_idx = y.notna()
    
    if valid_idx.sum() == 0:
        raise ValueError(f"No valid data for target: {target_col}")
    
    # Get features
    feature_cols = [c for c in df.columns 
                    if c not in exclude 
                    and c != target_col
                    and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    X = df[feature_cols].copy()
    
    # Fill missing values
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median() if not pd.isna(X[col].median()) else 0)
    
    # Filter to valid samples
    X, y = X[valid_idx], y[valid_idx]
    
    print(f"  Features: {X.shape[1]}, Samples: {len(X)}")
    return X, y, feature_cols


def train_model_for_target(
    X: pd.DataFrame, 
    y: pd.Series, 
    target_name: str,
    test_size: float = 0.2
) -> Dict[str, Any]:
    """
    Train a model for a specific target.
    """
    print(f"\nTraining model for: {target_name}")
    
    # Split data FIRST (before any outlier removal)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # Remove outliers ONLY from training data (prevents data leakage)
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")
    lower = y_train.quantile(0.01)
    upper = y_train.quantile(0.99)
    outlier_mask = (y_train >= lower) & (y_train <= upper)
    
    X_train_clean = X_train[outlier_mask]
    y_train_clean = y_train[outlier_mask]
    
    outliers_removed = len(X_train) - len(X_train_clean)
    print(f"  Removed {outliers_removed} training outliers ({outliers_removed/len(X_train)*100:.1f}%)")
    print(f"  Final train size: {len(X_train_clean)}")
    
    # Train model
    if USE_LIGHTGBM:
        model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            verbose=-1
        )
    else:
        model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            min_samples_leaf=10,
            subsample=0.8,
            random_state=42
        )
    
    model.fit(X_train_clean, y_train_clean)
    
    # Evaluate
    train_pred = model.predict(X_train_clean)
    test_pred = model.predict(X_test)
    
    metrics = {
        'train_mae': mean_absolute_error(y_train_clean, train_pred),
        'test_mae': mean_absolute_error(y_test, test_pred),
        'train_rmse': np.sqrt(mean_squared_error(y_train_clean, train_pred)),
        'test_rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
        'train_r2': r2_score(y_train_clean, train_pred),
        'test_r2': r2_score(y_test, test_pred),
    }
    
    print(f"  Test MAE: {metrics['test_mae']:.2f}")
    print(f"  Test RMSE: {metrics['test_rmse']:.2f}")
    print(f"  Test R²: {metrics['test_r2']:.3f}")
    
    # Feature importance
    if USE_LIGHTGBM:
        importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
    else:
        importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
    
    return {
        'model': model,
        'metrics': metrics,
        'feature_importance': importance,
        'target_stats': {
            'mean': float(y.mean()),
            'std': float(y.std()),
            'min': float(y.min()),
            'max': float(y.max()),
        }
    }


def train_all_models() -> Dict[str, Any]:
    """
    Train models for all investment targets.
    """
    print("=" * 80)
    print("INVESTMENT MODEL TRAINING")
    print("=" * 80)
    
    # Load data
    df = load_investment_data()
    
    # Train models for each target
    models = {}
    all_feature_names = None
    
    for target_col, target_desc in PREDICTION_TARGETS.items():
        if target_col not in df.columns:
            print(f"\n⚠️  Skipping {target_desc} - column not found")
            continue
        
        try:
            X, y, feature_names = prepare_features(df, target_col)
            if all_feature_names is None:
                all_feature_names = feature_names
            
            model_artifact = train_model_for_target(X, y, target_desc)
            models[target_col] = model_artifact
            
        except Exception as e:
            print(f"\n❌ Error training {target_desc}: {e}")
    
    if not models:
        raise ValueError("No models were trained successfully")
    
    # Create final artifact
    artifact = {
        'models': models,
        'feature_names': all_feature_names,
        'targets': PREDICTION_TARGETS,
        'model_type': 'LightGBM' if USE_LIGHTGBM else 'GradientBoosting',
    }
    
    return artifact


def save_model(artifact: Dict[str, Any]):
    """Save model artifact to disk."""
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(artifact, f)
    
    size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
    print(f"\n[OK] Model saved: {MODEL_PATH} ({size_mb:.2f} MB)\")")


def print_summary(artifact: Dict[str, Any]):
    """Print training summary."""
    print("\n" + "=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)
    
    print(f"\nModels trained: {len(artifact['models'])}")
    print(f"Features used: {len(artifact['feature_names'])}")
    
    print("\n" + "=" * 80)
    print("MODEL PERFORMANCE")
    print("=" * 80)
    
    for target, model_data in artifact['models'].items():
        desc = PREDICTION_TARGETS.get(target, target)
        metrics = model_data['metrics']
        stats = model_data['target_stats']
        
        print(f"\n{desc}")
        print(f"  Range: {stats['min']:.1f} to {stats['max']:.1f} (mean: {stats['mean']:.1f})")
        print(f"  Test MAE: {metrics['test_mae']:.2f}")
        print(f"  Test R²: {metrics['test_r2']:.3f}")
        
        # Top 3 features
        top_features = model_data['feature_importance'].head(3)
        print(f"  Top features:")
        for _, row in top_features.iterrows():
            print(f"    - {row['feature']}")


def demo_prediction(artifact: Dict[str, Any], df: pd.DataFrame):
    """Run a demo prediction."""
    print("\n" + "=" * 80)
    print("DEMO PREDICTION")
    print("=" * 80)
    
    # Find a district with all targets available
    for idx in df.index:
        district = df.loc[idx, 'district'] if 'district' in df.columns else 'Unknown'
        
        # Check if this district has data for all targets
        has_all = all(
            target in df.columns and pd.notna(df.loc[idx, target])
            for target in artifact['targets'].keys()
        )
        
        if has_all:
            print(f"\nDistrict: {district}")
            print("\nPredictions:")
            
            # Prepare features
            feature_names = artifact['feature_names']
            X = pd.DataFrame([{
                name: df.loc[idx, name] if name in df.columns else 0
                for name in feature_names
            }])
            
            # Fill missing
            for col in X.columns:
                if X[col].isna().any():
                    X[col] = X[col].fillna(0)
            
            # Predict for each target
            for target, desc in artifact['targets'].items():
                if target in artifact['models']:
                    model = artifact['models'][target]['model']
                    pred = model.predict(X)[0]
                    actual = df.loc[idx, target]
                    
                    print(f"  {desc:30s} Actual: {actual:8.1f}  Predicted: {pred:8.1f}")
            
            break


if __name__ == "__main__":
    # Train models
    artifact = train_all_models()
    
    # Save
    save_model(artifact)
    
    # Summary
    print_summary(artifact)
    
    # Demo
    df = load_investment_data()
    demo_prediction(artifact, df)
    
    print("\n✅ Training complete!")
    print("\nNext steps:")
    print("  1. Check accuracy: python check_investment_accuracy.py")
    print("  2. Use in API: Load model and call predict()")
