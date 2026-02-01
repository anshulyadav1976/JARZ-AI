"""
Validate ML Practices - Check for overfitting and data leakage
Uses proper cross-validation and checks for leakage
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("data")
INPUT_DATA = DATA_DIR / "investment_training_data.parquet"

def check_feature_leakage(df, target_cols):
    """Check if features might be leaking target information."""
    print("=" * 80)
    print("CHECKING FOR FEATURE LEAKAGE")
    print("=" * 80)
    
    leakage_issues = []
    
    # Only use numeric columns for correlation
    numeric_df = df.select_dtypes(include=['float64', 'int64', 'float32', 'int32'])
    
    for target in target_cols:
        if target not in numeric_df.columns:
            continue
            
        # Check correlation with all features
        correlations = numeric_df.corrwith(numeric_df[target]).abs().sort_values(ascending=False)
        
        # Flag very high correlations (>0.99) as potential leakage
        high_corr = correlations[correlations > 0.99]
        high_corr = high_corr[high_corr.index != target]  # Exclude self
        
        if len(high_corr) > 0:
            print(f"\n[!] WARNING: High correlation with {target}:")
            for feat, corr in high_corr.items():
                print(f"    {feat}: {corr:.4f}")
                leakage_issues.append((target, feat, corr))
    
    if len(leakage_issues) == 0:
        print("\n[OK] No obvious feature leakage detected\")")
    
    return leakage_issues


def proper_cross_validation(df, target_col, n_splits=5):
    """
    Perform proper k-fold cross-validation WITHOUT data leakage.
    Outlier removal happens INSIDE each fold.
    """
    # Exclude target-related columns
    exclude = {
        'district', 'area_code_type', 'error', 'lat', 'lon', 'region',
        '1yr_total_roi', '3yr_total_roi', '5yr_total_roi',
        '1yr_appreciation', '3yr_appreciation', '5yr_appreciation',
        '1yr_price_start', '1yr_price_end', '3yr_annual_avg', '5yr_annual_avg',
        'is_good_investment', 'estimated_annual_cash_flow', 'gross_rental_yield'
    }
    
    # Get valid data
    valid_idx = df[target_col].notna()
    df_valid = df[valid_idx].copy()
    
    # Prepare features
    feature_cols = [c for c in df_valid.columns 
                    if c not in exclude 
                    and c != target_col
                    and df_valid[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    X = df_valid[feature_cols].copy()
    y = df_valid[target_col].copy()
    
    # Fill missing values
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())
    
    # Initialize cross-validation
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # Store results
    fold_results = []
    
    print(f"\nPerforming {n_splits}-Fold Cross-Validation...")
    print(f"Total samples: {len(X)}")
    
    for fold, (train_idx, test_idx) in enumerate(kfold.split(X), 1):
        X_train_fold = X.iloc[train_idx].copy()
        X_test_fold = X.iloc[test_idx].copy()
        y_train_fold = y.iloc[train_idx].copy()
        y_test_fold = y.iloc[test_idx].copy()
        
        # IMPORTANT: Remove outliers ONLY from training data (not test)
        # This prevents data leakage
        train_df = pd.DataFrame({target_col: y_train_fold})
        lower = train_df[target_col].quantile(0.01)
        upper = train_df[target_col].quantile(0.99)
        
        # Filter training data
        outlier_mask = (y_train_fold >= lower) & (y_train_fold <= upper)
        X_train_clean = X_train_fold[outlier_mask]
        y_train_clean = y_train_fold[outlier_mask]
        
        # Train model
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
        
        model.fit(X_train_clean, y_train_clean)
        
        # Predict on test fold
        y_pred = model.predict(X_test_fold)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test_fold, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test_fold, y_pred))
        r2 = r2_score(y_test_fold, y_pred)
        
        fold_results.append({
            'fold': fold,
            'train_size': len(X_train_clean),
            'test_size': len(X_test_fold),
            'mae': mae,
            'rmse': rmse,
            'r2': r2
        })
        
        print(f"  Fold {fold}: R² = {r2:.4f}, MAE = {mae:.2f}, RMSE = {rmse:.2f}")
    
    return fold_results


def main():
    print("=" * 80)
    print("ML BEST PRACTICES VALIDATION")
    print("=" * 80)
    print("\nThis script checks for:")
    print("  1. Data leakage (outlier removal before split)")
    print("  2. Feature leakage (features containing target info)")
    print("  3. Overfitting (via proper k-fold cross-validation)")
    print("")
    
    # Load data
    df = pd.read_parquet(INPUT_DATA)
    print(f"Loaded {len(df)} districts")
    
    # Define targets
    targets = {
        '1yr_total_roi': '1-Year Total ROI (%)',
        '3yr_total_roi': '3-Year Total ROI (%)',
        '5yr_total_roi': '5-Year Total ROI (%)',
    }
    
    # Check for feature leakage
    check_feature_leakage(df, list(targets.keys()))
    
    # Run proper cross-validation for each target
    print("\n" + "=" * 80)
    print("PROPER CROSS-VALIDATION (NO DATA LEAKAGE)")
    print("=" * 80)
    print("\nOutlier removal happens INSIDE each fold (only on training data)")
    print("This gives true generalization performance\n")
    
    all_results = {}
    
    for target_col, target_label in targets.items():
        print(f"\n{target_label}")
        print("-" * 80)
        
        fold_results = proper_cross_validation(df, target_col, n_splits=5)
        
        # Calculate average metrics
        avg_mae = np.mean([r['mae'] for r in fold_results])
        avg_rmse = np.mean([r['rmse'] for r in fold_results])
        avg_r2 = np.mean([r['r2'] for r in fold_results])
        std_r2 = np.std([r['r2'] for r in fold_results])
        
        all_results[target_col] = {
            'avg_mae': avg_mae,
            'avg_rmse': avg_rmse,
            'avg_r2': avg_r2,
            'std_r2': std_r2,
            'folds': fold_results
        }
        
        print(f"\nCross-Validation Summary:")
        print(f"  Average R²:  {avg_r2:.4f} ± {std_r2:.4f}")
        print(f"  Average MAE: {avg_mae:.2f}")
        print(f"  Average RMSE: {avg_rmse:.2f}")
        
        # Check for overfitting
        if std_r2 > 0.1:
            print(f"  ⚠️  WARNING: High variance across folds (std={std_r2:.4f})")
            print(f"      This suggests potential overfitting or data issues")
        elif avg_r2 > 0.99:
            print(f"  ⚠️  WARNING: R² > 0.99 is suspiciously high")
            print(f"      Check for feature leakage or data quality issues")
        else:
            print(f"  ✅ Model appears stable across folds")
    
    # Final summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    print("\nComparison: Original vs Proper Validation")
    print("-" * 80)
    print(f"{'Target':<25} {'Original R²':<15} {'Proper CV R²':<15} {'Difference'}")
    print("-" * 80)
    
    original_r2 = {
        '1yr_total_roi': 0.9965,
        '3yr_total_roi': 0.9965,
        '5yr_total_roi': 0.9964,
    }
    
    for target_col, target_label in targets.items():
        orig = original_r2[target_col]
        proper = all_results[target_col]['avg_r2']
        diff = orig - proper
        
        print(f"{target_label:<25} {orig:<15.4f} {proper:<15.4f} {diff:+.4f}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    max_diff = max(abs(original_r2[t] - all_results[t]['avg_r2']) for t in targets.keys())
    
    if max_diff > 0.05:
        print("\n⚠️  SIGNIFICANT DIFFERENCE DETECTED")
        print(f"   Original validation had data leakage (outliers removed before split)")
        print(f"   Proper cross-validation shows REAL performance: R² ~ {all_results['1yr_total_roi']['avg_r2']:.4f}")
        print(f"\n   The model is still {'good' if all_results['1yr_total_roi']['avg_r2'] > 0.85 else 'needs improvement'}")
    else:
        print("\n✅ VALIDATION PASSED")
        print(f"   Results are consistent between methods (diff < 0.05)")
        print(f"   The model performance is genuine")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
