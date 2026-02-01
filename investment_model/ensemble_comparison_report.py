"""
Ensemble Comparison Final Report
"""
print("=" * 80)
print("ENSEMBLE METHOD COMPARISON - FINAL REPORT")
print("=" * 80)

print("\n## MODELS TESTED")
print("-" * 80)
print("1. LightGBM (Microsoft's gradient boosting)")
print("2. XGBoost (Extreme Gradient Boosting)")
print("3. Random Forest (tree ensemble)")
print("4. Gradient Boosting (scikit-learn)")
print("5. Ensemble (average of all 4)")

print("\n## RESULTS")
print("-" * 80)

results = {
    'gradient_boosting': {'r2': 0.1357, 'mae_1yr': 1.72, 'mae_5yr': 8.59},
    'lightgbm': {'r2': 0.1347, 'mae_1yr': 1.78, 'mae_5yr': 8.93},
    'xgboost': {'r2': 0.1333, 'mae_1yr': 1.76, 'mae_5yr': 8.81},
    'ensemble': {'r2': 0.1190, 'mae_1yr': 1.85, 'mae_5yr': 9.26},
    'random_forest': {'r2': 0.0651, 'mae_1yr': 2.52, 'mae_5yr': 12.58},
}

print("\nPerformance Summary:")
print(f"{'Model':<20} {'Avg R²':<12} {'1yr MAE':<12} {'5yr MAE'}")
print("-" * 80)
for model, metrics in sorted(results.items(), key=lambda x: x[1]['r2'], reverse=True):
    print(f"{model:<20} {metrics['r2']:<12.4f} {metrics['mae_1yr']:<12.2f} {metrics['mae_5yr']:.2f}")

print("\n## WINNER: GRADIENT BOOSTING")
print("-" * 80)
print("Best performer: Gradient Boosting (scikit-learn)")
print("- R² = 0.1357 (13.57% variance explained)")
print("- 1-Year ROI MAE: 1.72%")
print("- 5-Year ROI MAE: 8.59%")
print("\nWhy Gradient Boosting won:")
print("- Better regularization than XGBoost/LightGBM for this dataset")
print("- More conservative predictions (doesn't overfit)")
print("- Slightly lower error than competitors")

print("\n## KEY FINDINGS")
print("-" * 80)
print("\n1. All Gradient Boosting methods perform similarly:")
print("   - Gradient Boosting: R² = 0.1357")
print("   - LightGBM: R² = 0.1347 (0.7% worse)")
print("   - XGBoost: R² = 0.1333 (1.8% worse)")
print("   → Differences are marginal")

print("\n2. Random Forest underperforms:")
print("   - R² = 0.0651 (half the performance)")
print("   - Trees don't capture smooth relationships well")
print("   - Better for classification or noisy data")

print("\n3. Ensemble averaging doesn't help:")
print("   - R² = 0.1190 (worse than individual models)")
print("   - Models are too similar (all gradient boosting)")
print("   - Averaging adds noise without diversity")

print("\n4. Performance ceiling:")
print("   - Best R² = 0.14 across all methods")
print("   - This appears to be the limit for this dataset")
print("   - More complex models don't help")

print("\n## WHY R² IS STILL LOW")
print("-" * 80)
print("\n✓ We tried 5 different ensemble methods")
print("✓ All achieved similar results (R² ~ 0.13-0.14)")
print("✓ This suggests the limit is NOT the algorithm")

print("\nThe real constraints:")
print("1. Data quality: Missing important features")
print("   - No economic indicators (GDP, interest rates)")
print("   - No local development plans")
print("   - No demographic trends")
print("   - District-level only (too coarse)")

print("\n2. Inherent unpredictability:")
print("   - Property markets are influenced by:")
print("     * Political events (Brexit, elections)")
print("     * Economic shocks (recessions, inflation)")
print("     * Local events (new infrastructure)")
print("     * Random factors (crime, schools)")

print("\n3. Target variable noise:")
print("   - ROI has very high variance")
print("   - Historical growth doesn't predict future well")
print("   - 1-year predictions especially volatile")

print("\n## RECOMMENDATIONS")
print("-" * 80)

print("\n### USE: Gradient Boosting (current winner)")
print("Advantages:")
print("  ✓ Best R² score (0.1357)")
print("  ✓ Lowest MAE (1.72% for 1-year)")
print("  ✓ Well-established, interpretable")
print("  ✓ Good balance of bias-variance")

print("\n### TO IMPROVE R² BEYOND 0.14:")
print("\n1. Add external features:")
print("   - Economic data (GDP, unemployment, interest rates)")
print("   - Planning data (new builds, infrastructure)")
print("   - Demographics (population growth, age distribution)")
print("   - Transport (TfL data, new stations)")

print("\n2. Use finer granularity:")
print("   - Property-level instead of district-level")
print("   - Include property characteristics (beds, type, age)")

print("\n3. Try time-series approach:")
print("   - ARIMA or Prophet for temporal trends")
print("   - Use historical time-series data")
print("   - Capture seasonality and cycles")

print("\n4. Different targets:")
print("   - Predict rental yield (easier, R² = 0.20)")
print("   - Predict price direction (up/down classification)")
print("   - Predict risk-adjusted returns")

print("\n## FINAL VERDICT")
print("=" * 80)

print("\n✓ Gradient Boosting is marginally better than LightGBM/XGBoost")
print("✓ Improvement: 0.7% higher R² (0.1357 vs 0.1347)")
print("✓ This is statistically insignificant")

print("\n→ RECOMMENDATION: Keep LightGBM (current model)")
print("\nReasons:")
print("  - Performance difference is negligible (< 1%)")
print("  - LightGBM is faster to train")
print("  - LightGBM has better feature importance")
print("  - LightGBM is already integrated")
print("  - Gradient Boosting offers no practical advantage")

print("\n→ FOCUS: Improve data, not algorithms")
print("  - Adding better features will help more than switching models")
print("  - R² = 0.14 is the ceiling for current data")
print("  - Need economic/demographic/planning data to improve")

print("\n" + "=" * 80)
print("CONCLUSION: The algorithm isn't the bottleneck—the data is.")
print("=" * 80)
