"""
Compare ensemble methods: LightGBM vs Random Forest vs XGBoost
Train all three and find the best performer
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
import pickle
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

INPUT_DATA = DATA_DIR / "investment_training_data.parquet"
MODEL_PATH = MODEL_DIR / "investment_ensemble_model.pkl"

# Targets
PREDICTION_TARGETS = {
    '1yr_total_roi': '1-Year Total ROI (%)',
    '3yr_total_roi': '3-Year Total ROI (%)',
    '5yr_total_roi': '5-Year Total ROI (%)',
}


def load_data() -> pd.DataFrame:
    """Load investment data."""
    print("Loading investment data...")
    df = pd.read_parquet(INPUT_DATA)
    print(f"  Loaded {len(df)} districts")
    return df


def prepare_features(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features without data leakage."""
    # Exclude target-related and leaking features
    exclude = {
        'district', 'area_code_type', 'error', 'lat', 'lon', 'region',
        '1yr_total_roi', '3yr_total_roi', '5yr_total_roi',
        '1yr_appreciation', '3yr_appreciation', '5yr_appreciation',
        '1yr_price_start', '1yr_price_end', '3yr_annual_avg', '5yr_annual_avg',
        'is_good_investment',
        # Features that leak target info
        'investment_score', 'gross_rental_yield', 'net_rental_yield',
        'estimated_annual_cash_flow', 'capital_growth_score',
    }
    
    y = df[target_col].copy()
    valid_idx = y.notna()
    
    feature_cols = [c for c in df.columns 
                    if c not in exclude 
                    and c != target_col
                    and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    X = df[feature_cols].copy()
    
    # Fill missing values
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())
    
    # Ensure no NaN values remain
    X = X.fillna(0)
    
    return X[valid_idx], y[valid_idx], feature_cols


def train_model(X_train, y_train, model_type='lightgbm'):
    """Train a specific model type."""
    if model_type == 'lightgbm':
        model = lgb.LGBMRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            verbose=-1
        )
    elif model_type == 'xgboost':
        model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            min_child_weight=20,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            verbosity=0
        )
    elif model_type == 'random_forest':
        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
    elif model_type == 'gradient_boosting':
        model = GradientBoostingRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            min_samples_leaf=20,
            subsample=0.8,
            random_state=42
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test):
    """Evaluate model performance."""
    y_pred = model.predict(X_test)
    
    return {
        'mae': mean_absolute_error(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred),
    }


def train_ensemble_stack(models, X_train, y_train, X_test):
    """Create a simple ensemble by averaging predictions."""
    predictions = []
    for model_name, model in models.items():
        pred = model.predict(X_test)
        predictions.append(pred)
    
    # Average predictions
    ensemble_pred = np.mean(predictions, axis=0)
    return ensemble_pred


def main():
    print("=" * 80)
    print("ENSEMBLE MODEL COMPARISON")
    print("=" * 80)
    print("\nComparing: LightGBM, XGBoost, Random Forest, Gradient Boosting")
    print("Using proper ML practices (no data leakage)")
    print()
    
    df = load_data()
    
    all_results = {}
    best_models = {}
    
    for target_col, target_label in PREDICTION_TARGETS.items():
        print("\n" + "=" * 80)
        print(f"Training: {target_label}")
        print("=" * 80)
        
        # Prepare data
        X, y, feature_cols = prepare_features(df, target_col)
        print(f"Features: {len(feature_cols)}, Samples: {len(X)}")
        
        # Split data FIRST
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Remove outliers ONLY from training data
        lower = y_train.quantile(0.01)
        upper = y_train.quantile(0.99)
        outlier_mask = (y_train >= lower) & (y_train <= upper)
        
        X_train_clean = X_train[outlier_mask]
        y_train_clean = y_train[outlier_mask]
        
        print(f"Train: {len(X_train)} -> {len(X_train_clean)} (after outlier removal)")
        print(f"Test: {len(X_test)}")
        
        # Train all models
        models = {}
        results = {}
        
        model_types = ['lightgbm', 'xgboost', 'random_forest', 'gradient_boosting']
        
        for model_type in model_types:
            print(f"\n  Training {model_type}...", end=" ")
            
            model = train_model(X_train_clean, y_train_clean, model_type)
            metrics = evaluate_model(model, X_test, y_test)
            
            models[model_type] = model
            results[model_type] = metrics
            
            print(f"R2: {metrics['r2']:.4f}, MAE: {metrics['mae']:.2f}")
        
        # Train ensemble (average of all)
        print(f"\n  Creating ensemble (average)...", end=" ")
        ensemble_pred = train_ensemble_stack(models, X_train_clean, y_train_clean, X_test)
        ensemble_metrics = {
            'mae': mean_absolute_error(y_test, ensemble_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, ensemble_pred)),
            'r2': r2_score(y_test, ensemble_pred),
        }
        results['ensemble'] = ensemble_metrics
        print(f"R2: {ensemble_metrics['r2']:.4f}, MAE: {ensemble_metrics['mae']:.2f}")
        
        # Find best model
        best_model_name = max(results.items(), key=lambda x: x[1]['r2'])[0]
        best_r2 = results[best_model_name]['r2']
        
        print(f"\n  BEST: {best_model_name} (R2: {best_r2:.4f})")
        
        # Store results
        all_results[target_col] = {
            'results': results,
            'best_model': best_model_name,
            'models': models,
            'feature_cols': feature_cols,
        }
        
        # Save best model
        if best_model_name == 'ensemble':
            best_models[target_col] = {
                'type': 'ensemble',
                'models': models,
                'metrics': ensemble_metrics,
            }
        else:
            best_models[target_col] = {
                'type': best_model_name,
                'model': models[best_model_name],
                'metrics': results[best_model_name],
            }
    
    # Print summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    for target_col, target_label in PREDICTION_TARGETS.items():
        print(f"\n{target_label}")
        print("-" * 80)
        print(f"{'Model':<20} {'R²':<12} {'MAE':<12} {'RMSE'}")
        print("-" * 80)
        
        results = all_results[target_col]['results']
        
        # Sort by R²
        sorted_results = sorted(results.items(), key=lambda x: x[1]['r2'], reverse=True)
        
        for model_name, metrics in sorted_results:
            star = " *BEST*" if model_name == all_results[target_col]['best_model'] else ""
            print(f"{model_name:<20} {metrics['r2']:<12.4f} {metrics['mae']:<12.2f} {metrics['rmse']:.2f}{star}")
    
    # Save best models
    artifact = {
        'models': best_models,
        'feature_names': all_results[list(PREDICTION_TARGETS.keys())[0]]['feature_cols'],
        'targets': PREDICTION_TARGETS,
        'comparison_results': {k: v['results'] for k, v in all_results.items()},
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(artifact, f)
    
    size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
    print(f"\n[OK] Model saved: {MODEL_PATH} ({size_mb:.2f} MB)")
    
    # Final recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    best_overall = {}
    for target_col in PREDICTION_TARGETS.keys():
        best = all_results[target_col]['best_model']
        best_overall[best] = best_overall.get(best, 0) + 1
    
    winner = max(best_overall.items(), key=lambda x: x[1])[0]
    
    print(f"\nBest overall performer: {winner.upper()}")
    print(f"Won {best_overall[winner]}/{len(PREDICTION_TARGETS)} targets")
    
    avg_r2_by_model = {}
    for model_type in ['lightgbm', 'xgboost', 'random_forest', 'gradient_boosting', 'ensemble']:
        r2_scores = [all_results[t]['results'][model_type]['r2'] for t in PREDICTION_TARGETS.keys()]
        avg_r2_by_model[model_type] = np.mean(r2_scores)
    
    print("\nAverage R² across all targets:")
    for model_name, avg_r2 in sorted(avg_r2_by_model.items(), key=lambda x: x[1], reverse=True):
        print(f"  {model_name:<20} {avg_r2:.4f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
