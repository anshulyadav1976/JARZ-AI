"""
Investment Model Evaluation - Metrics That Actually Matter
Evaluates model usefulness for investment decisions, not just prediction accuracy
"""
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from scipy.stats import spearmanr, kendalltau
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

INPUT_DATA = DATA_DIR / "investment_training_data.parquet"
MODEL_PATH = MODEL_DIR / "investment_roi_model.pkl"


def calculate_rank_correlation(y_true, y_pred):
    """Calculate Spearman and Kendall rank correlation."""
    spearman_corr, spearman_p = spearmanr(y_true, y_pred)
    kendall_corr, kendall_p = kendalltau(y_true, y_pred)
    
    return {
        'spearman': spearman_corr,
        'spearman_pvalue': spearman_p,
        'kendall': kendall_corr,
        'kendall_pvalue': kendall_p,
    }


def calculate_decile_performance(y_true, y_pred, n_deciles=10):
    """
    Compare performance of top vs bottom deciles.
    This is what matters for investment selection.
    """
    df = pd.DataFrame({
        'actual': y_true,
        'predicted': y_pred
    })
    
    # Sort by predicted values and create deciles
    df['decile'] = pd.qcut(df['predicted'], q=n_deciles, labels=False, duplicates='drop')
    
    # Calculate mean actual return for each decile
    decile_performance = df.groupby('decile')['actual'].agg(['mean', 'median', 'std', 'count'])
    
    # Top vs bottom
    top_decile = decile_performance.loc[decile_performance.index.max()]
    bottom_decile = decile_performance.loc[decile_performance.index.min()]
    
    return {
        'decile_performance': decile_performance,
        'top_decile_mean': top_decile['mean'],
        'bottom_decile_mean': bottom_decile['mean'],
        'top_bottom_spread': top_decile['mean'] - bottom_decile['mean'],
        'spread_ratio': top_decile['mean'] / bottom_decile['mean'] if bottom_decile['mean'] != 0 else np.nan,
    }


def calculate_quartile_hit_rate(y_true, y_pred):
    """
    What % of predicted top-quartile actually end up in top-quartile?
    This measures ranking accuracy.
    """
    df = pd.DataFrame({
        'actual': y_true,
        'predicted': y_pred
    })
    
    # Create quartiles based on actual and predicted
    df['actual_quartile'] = pd.qcut(df['actual'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')
    df['predicted_quartile'] = pd.qcut(df['predicted'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')
    
    # Hit rate: % of predicted Q4 that are actually Q4
    predicted_top = df[df['predicted_quartile'] == 'Q4']
    hit_rate = (predicted_top['actual_quartile'] == 'Q4').sum() / len(predicted_top) if len(predicted_top) > 0 else 0
    
    # Avoid rate: % of predicted Q1 that are actually Q1
    predicted_bottom = df[df['predicted_quartile'] == 'Q1']
    avoid_rate = (predicted_bottom['actual_quartile'] == 'Q1').sum() / len(predicted_bottom) if len(predicted_bottom) > 0 else 0
    
    return {
        'top_quartile_hit_rate': hit_rate,
        'bottom_quartile_avoid_rate': avoid_rate,
        'avg_accuracy': (hit_rate + avoid_rate) / 2,
    }


def calculate_long_short_return(y_true, y_pred, long_pct=0.2, short_pct=0.2):
    """
    Simulate long-short strategy: go long top 20%, short bottom 20%.
    This is the ultimate test of investment utility.
    """
    df = pd.DataFrame({
        'actual': y_true,
        'predicted': y_pred
    })
    
    # Identify long and short positions based on predictions
    n_long = int(len(df) * long_pct)
    n_short = int(len(df) * short_pct)
    
    df_sorted = df.sort_values('predicted', ascending=False)
    
    long_positions = df_sorted.head(n_long)
    short_positions = df_sorted.tail(n_short)
    
    # Calculate returns
    long_return = long_positions['actual'].mean()
    short_return = short_positions['actual'].mean()
    long_short_return = long_return - short_return
    
    return {
        'long_return': long_return,
        'short_return': short_return,
        'long_short_spread': long_short_return,
        'long_positions': len(long_positions),
        'short_positions': len(short_positions),
    }


def check_directional_bias(y_true, y_pred):
    """
    Check if errors are systematically biased (always over/under-predicting).
    """
    errors = y_pred - y_true
    
    return {
        'mean_error': errors.mean(),
        'median_error': errors.median(),
        'positive_errors_pct': (errors > 0).sum() / len(errors),
        'is_biased': abs(errors.mean()) > errors.std() * 0.1,  # Arbitrary threshold
    }


def evaluate_investment_utility(y_true, y_pred, target_name='ROI'):
    """Comprehensive investment-focused evaluation."""
    
    print(f"\n{'='*80}")
    print(f"INVESTMENT UTILITY EVALUATION: {target_name}")
    print(f"{'='*80}")
    
    # Traditional metrics (for reference)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n📊 Traditional Metrics (for reference only):")
    print(f"   R² Score: {r2:.4f}")
    print(f"   MAE: {mae:.2f}")
    
    # Rank correlation (MOST IMPORTANT)
    rank_corr = calculate_rank_correlation(y_true, y_pred)
    print(f"\n🎯 Rank Correlation (KEY METRIC):")
    print(f"   Spearman ρ: {rank_corr['spearman']:.4f} (p={rank_corr['spearman_pvalue']:.4f})")
    print(f"   Kendall τ: {rank_corr['kendall']:.4f} (p={rank_corr['kendall_pvalue']:.4f})")
    
    if rank_corr['spearman'] > 0.3:
        print(f"   ✓ STRONG ranking ability - useful for investment decisions")
    elif rank_corr['spearman'] > 0.15:
        print(f"   ✓ MODERATE ranking ability - some investment value")
    else:
        print(f"   ✗ WEAK ranking ability - limited investment value")
    
    # Decile analysis
    decile_perf = calculate_decile_performance(y_true, y_pred)
    print(f"\n📈 Top vs Bottom Decile Performance:")
    print(f"   Top 10% avg return: {decile_perf['top_decile_mean']:.2f}%")
    print(f"   Bottom 10% avg return: {decile_perf['bottom_decile_mean']:.2f}%")
    print(f"   Spread: {decile_perf['top_bottom_spread']:.2f}%")
    
    if decile_perf['top_bottom_spread'] > 0:
        print(f"   ✓ Model correctly identifies better investments")
    else:
        print(f"   ✗ Model fails to separate good from bad investments")
    
    # Quartile hit rate
    quartile_hit = calculate_quartile_hit_rate(y_true, y_pred)
    print(f"\n🎲 Quartile Accuracy:")
    print(f"   Top quartile hit rate: {quartile_hit['top_quartile_hit_rate']*100:.1f}%")
    print(f"   Bottom quartile avoid rate: {quartile_hit['bottom_quartile_avoid_rate']*100:.1f}%")
    
    if quartile_hit['top_quartile_hit_rate'] > 0.4:
        print(f"   ✓ Good at identifying top performers (>40% accuracy)")
    elif quartile_hit['top_quartile_hit_rate'] > 0.25:
        print(f"   ~ Baseline performance (random = 25%)")
    else:
        print(f"   ✗ Worse than random selection")
    
    # Long-short strategy
    long_short = calculate_long_short_return(y_true, y_pred)
    print(f"\n💰 Long-Short Strategy (Top 20% vs Bottom 20%):")
    print(f"   Long portfolio return: {long_short['long_return']:.2f}%")
    print(f"   Short portfolio return: {long_short['short_return']:.2f}%")
    print(f"   Long-short spread: {long_short['long_short_spread']:.2f}%")
    
    if long_short['long_short_spread'] > 2:
        print(f"   ✓ PROFITABLE strategy - model is valuable")
    elif long_short['long_short_spread'] > 0:
        print(f"   ~ Marginally profitable")
    else:
        print(f"   ✗ Unprofitable - model not useful")
    
    # Directional bias
    bias = check_directional_bias(y_true, y_pred)
    print(f"\n⚖️  Prediction Bias:")
    print(f"   Mean error: {bias['mean_error']:.2f}%")
    print(f"   Positive errors: {bias['positive_errors_pct']*100:.1f}%")
    
    if not bias['is_biased']:
        print(f"   ✓ No systematic bias")
    else:
        if bias['mean_error'] > 0:
            print(f"   ! Model tends to OVER-predict")
        else:
            print(f"   ! Model tends to UNDER-predict")
    
    # Overall verdict
    print(f"\n{'='*80}")
    print(f"INVESTMENT UTILITY VERDICT")
    print(f"{'='*80}")
    
    score = 0
    
    # Scoring system
    if rank_corr['spearman'] > 0.3:
        score += 3
    elif rank_corr['spearman'] > 0.15:
        score += 2
    elif rank_corr['spearman'] > 0:
        score += 1
    
    if decile_perf['top_bottom_spread'] > 5:
        score += 2
    elif decile_perf['top_bottom_spread'] > 2:
        score += 1
    
    if long_short['long_short_spread'] > 2:
        score += 2
    elif long_short['long_short_spread'] > 0:
        score += 1
    
    if quartile_hit['top_quartile_hit_rate'] > 0.4:
        score += 2
    elif quartile_hit['top_quartile_hit_rate'] > 0.25:
        score += 1
    
    print(f"\nUtility Score: {score}/9")
    
    if score >= 7:
        verdict = "HIGHLY USEFUL"
        emoji = "🚀"
    elif score >= 5:
        verdict = "USEFUL"
        emoji = "✓"
    elif score >= 3:
        verdict = "MODERATELY USEFUL"
        emoji = "~"
    else:
        verdict = "LIMITED UTILITY"
        emoji = "✗"
    
    print(f"\n{emoji} {verdict} for investment decisions")
    
    return {
        'r2': r2,
        'mae': mae,
        'rank_correlation': rank_corr,
        'decile_performance': decile_perf,
        'quartile_accuracy': quartile_hit,
        'long_short': long_short,
        'bias': bias,
        'utility_score': score,
        'verdict': verdict,
    }


def main():
    print("="*80)
    print("INVESTMENT MODEL EVALUATION")
    print("Metrics That Actually Matter for Investment Decisions")
    print("="*80)
    
    # Load data
    df = pd.read_parquet(INPUT_DATA)
    
    # Load model
    with open(MODEL_PATH, 'rb') as f:
        artifact = pickle.load(f)
    
    print(f"\nModel: {MODEL_PATH.name}")
    print(f"Data: {len(df)} districts")
    
    # Evaluate each target
    targets = {
        '1yr_total_roi': '1-Year Total ROI',
        '3yr_total_roi': '3-Year Total ROI',
        '5yr_total_roi': '5-Year Total ROI',
    }
    
    results = {}
    
    for target_col, target_label in targets.items():
        if target_col not in df.columns:
            continue
        
        # Prepare data (same as training)
        exclude = {
            'district', 'area_code_type', 'error', 'lat', 'lon', 'region',
            '1yr_total_roi', '3yr_total_roi', '5yr_total_roi',
            '1yr_appreciation', '3yr_appreciation', '5yr_appreciation',
            '1yr_price_start', '1yr_price_end', '3yr_annual_avg', '5yr_annual_avg',
            'is_good_investment',
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
        for col in X.columns:
            if X[col].isna().any():
                X[col] = X[col].fillna(X[col].median())
        X = X.fillna(0)
        
        X = X[valid_idx]
        y = y[valid_idx]
        
        # Get model predictions
        model_data = artifact['models'][target_col]
        if 'models' in model_data:  # Ensemble
            # Average predictions
            preds = []
            for model in model_data['models'].values():
                preds.append(model.predict(X))
            y_pred = np.mean(preds, axis=0)
        else:  # Single model
            model = model_data['model']
            y_pred = model.predict(X)
        
        # Evaluate
        result = evaluate_investment_utility(y, y_pred, target_label)
        results[target_col] = result
    
    # Summary comparison
    print(f"\n\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")
    
    print(f"\n{'Target':<25} {'R²':<10} {'Spearman':<12} {'L/S Spread':<12} {'Verdict'}")
    print("-"*80)
    
    for target_col, target_label in targets.items():
        if target_col in results:
            r = results[target_col]
            print(f"{target_label:<25} {r['r2']:<10.4f} {r['rank_correlation']['spearman']:<12.4f} "
                  f"{r['long_short']['long_short_spread']:<12.2f} {r['verdict']}")
    
    print(f"\n{'='*80}")
    print("KEY INSIGHT")
    print(f"{'='*80}")
    print(f"\nR² measures prediction accuracy.")
    print(f"Spearman/Long-Short measure INVESTMENT UTILITY.")
    print(f"\nA model with low R² but high Spearman is MORE VALUABLE")
    print(f"than high R² with low Spearman for investment decisions.")
    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
