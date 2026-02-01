"""
Spatio-Temporal Rental Valuation Model Training
Trains quantile regression for P10/P50/P90 rent predictions with SHAP explainability.
"""

import pickle
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from sklearn.model_selection import train_test_split

import numpy as np
import pandas as pd
import shap
from scipy.spatial.distance import cdist
from sklearn.metrics import mean_absolute_error, mean_squared_error
import lightgbm as lgb
USE_LIGHTGBM = True

warnings.filterwarnings('ignore')

# ============ CONFIGURATION ============
DATA_DIR = Path("data/raw")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

FEATURES_PATH = DATA_DIR / "district_training_data.parquet"
TIMESERIES_PATH = DATA_DIR / "district_growth_timeseries.parquet"
MODEL_PATH = MODEL_DIR / "rent_quantile_model.pkl"

TARGET_COL = "rent_demand_mean_pcm"
FALLBACK_TARGET = "rent_avg_pcm"
QUANTILES = [0.1, 0.5, 0.9]

# UK district coordinates (lat, lon)
DISTRICT_COORDS = {
    # London
    "E1": (51.515, -0.073), "E2": (51.529, -0.056), "E3": (51.528, -0.021), "E4": (51.628, -0.007),
    "E5": (51.556, -0.052), "E6": (51.522, 0.052), "E7": (51.546, 0.023), "E8": (51.543, -0.055),
    "E9": (51.547, -0.040), "E10": (51.565, -0.013), "E11": (51.572, 0.008), "E14": (51.507, -0.024),
    "EC1": (51.525, -0.099), "EC2": (51.519, -0.085), "EC3": (51.513, -0.083), "EC4": (51.514, -0.103),
    "N1": (51.539, -0.102), "N2": (51.588, -0.165), "N3": (51.602, -0.191), "N4": (51.568, -0.104),
    "N5": (51.555, -0.097), "N6": (51.573, -0.146), "N7": (51.556, -0.116), "N8": (51.586, -0.118),
    "NW1": (51.534, -0.147), "NW2": (51.560, -0.224), "NW3": (51.550, -0.177), "NW4": (51.585, -0.229),
    "NW5": (51.554, -0.142), "NW6": (51.545, -0.199), "NW7": (51.613, -0.244), "NW8": (51.531, -0.171),
    "NW9": (51.588, -0.259), "NW10": (51.539, -0.245), "NW11": (51.577, -0.197),
    "SE1": (51.501, -0.089), "SE2": (51.487, 0.101), "SE3": (51.464, 0.017), "SE4": (51.454, -0.040),
    "SE5": (51.474, -0.089), "SE6": (51.441, -0.018), "SE7": (51.482, 0.037), "SE8": (51.478, -0.027),
    "SE9": (51.446, 0.071), "SE10": (51.483, 0.006), "SE11": (51.491, -0.107),
    "SW1": (51.495, -0.141), "SW2": (51.452, -0.120), "SW3": (51.489, -0.168), "SW4": (51.457, -0.138),
    "SW5": (51.491, -0.189), "SW6": (51.475, -0.204), "SW7": (51.495, -0.177), "SW8": (51.476, -0.129),
    "SW9": (51.468, -0.114), "SW10": (51.483, -0.188), "SW11": (51.463, -0.164),
    "W1": (51.515, -0.144), "W2": (51.514, -0.181), "W3": (51.510, -0.267), "W4": (51.490, -0.262),
    "W5": (51.510, -0.307), "W6": (51.492, -0.229), "W7": (51.508, -0.321), "W8": (51.501, -0.194),
    "W9": (51.526, -0.189), "W10": (51.524, -0.211), "W11": (51.515, -0.206), "W12": (51.504, -0.239),
    "WC1": (51.521, -0.123), "WC2": (51.512, -0.122),
    # Major cities
    "M1": (53.481, -2.243), "M2": (53.480, -2.248), "M3": (53.484, -2.253), "M4": (53.484, -2.230),
    "M14": (53.453, -2.217), "M15": (53.464, -2.261), "M16": (53.457, -2.284), "M20": (53.428, -2.227),
    "B1": (52.480, -1.900), "B2": (52.477, -1.896), "B3": (52.483, -1.891), "B4": (52.485, -1.888),
    "B5": (52.473, -1.897), "B15": (52.461, -1.930),
    "L1": (53.408, -2.992), "L2": (53.406, -2.986), "L3": (53.410, -2.981),
    "LS1": (53.800, -1.549), "LS2": (53.801, -1.539), "LS6": (53.820, -1.556),
    "BS1": (51.455, -2.588), "BS2": (51.462, -2.569), "BS3": (51.442, -2.594),
    "G1": (55.861, -4.251), "G2": (55.864, -4.253), "G3": (55.868, -4.261),
    "EH1": (55.951, -3.192), "EH2": (55.951, -3.201), "EH3": (55.946, -3.212),
}

# Rental profiles for synthetic data generation
RENTAL_PROFILES = {
    "prime_london": {"mean": 4500, "std": 1500, "min": 2000, "max": 15000},
    "central_london": {"mean": 2800, "std": 800, "min": 1500, "max": 6000},
    "outer_london": {"mean": 1800, "std": 500, "min": 1000, "max": 3500},
    "major_city": {"mean": 1200, "std": 400, "min": 600, "max": 2500},
    "suburban": {"mean": 1000, "std": 300, "min": 500, "max": 2000},
}

DISTRICT_PROFILES = {
    "W1": "prime_london", "SW1": "prime_london", "SW3": "prime_london", "SW7": "prime_london",
    "W8": "prime_london", "NW8": "prime_london", "WC1": "prime_london", "WC2": "prime_london",
    "NW1": "central_london", "NW3": "central_london", "W2": "central_london", "W11": "central_london",
    "SW5": "central_london", "SW6": "central_london", "SW10": "central_london", "N1": "central_london",
    "E1": "central_london", "SE1": "central_london", "EC1": "central_london", "EC2": "central_london",
    "NW2": "outer_london", "NW4": "outer_london", "NW5": "outer_london", "NW6": "outer_london",
    "NW10": "outer_london", "SW4": "outer_london", "SW11": "outer_london", "W4": "outer_london",
    "W6": "outer_london", "W12": "outer_london", "N4": "outer_london", "N5": "outer_london",
    "N7": "outer_london", "E2": "outer_london", "E3": "outer_london", "E8": "outer_london",
    "E14": "outer_london", "SE5": "outer_london", "SE10": "outer_london", "SE11": "outer_london",
    "M1": "major_city", "M14": "major_city", "M20": "major_city", "LS1": "major_city", "LS6": "major_city",
}


# ============ DATA LOADING ============
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load training data from parquet files."""
    print("Loading data...")
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Run Get_Data.py first. Missing: {FEATURES_PATH}")
    
    df = pd.read_parquet(FEATURES_PATH)
    print(f"  Loaded {len(df)} districts")
    
    df_ts = pd.read_parquet(TIMESERIES_PATH) if TIMESERIES_PATH.exists() else pd.DataFrame()
    if not df_ts.empty:
        print(f"  Loaded {len(df_ts)} time points")
    return df, df_ts


# ============ FEATURE ENGINEERING ============
def add_spatial_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Add K-nearest neighbor spatial features and return neighbor details."""
    print("Adding spatial features...")
    df = df.copy()
    df["lat"] = df["district"].map(lambda x: DISTRICT_COORDS.get(x, (None, None))[0])
    df["lon"] = df["district"].map(lambda x: DISTRICT_COORDS.get(x, (None, None))[1])

    has_coords = df["lat"].notna()
    neighbor_details = {}
    if has_coords.sum() < 5:
        df["region"] = df["district"].str.extract(r'^([A-Z]+)', expand=False)
        for col in ["rent_demand_mean_pcm", "rent_avg_pcm", "growth_latest_avg_price"]:
            if col in df.columns:
                df[f"spatial_{col}_region_avg"] = df.groupby("region")[col].transform("mean")
        return df, neighbor_details

    coords = df.loc[has_coords, ["lat", "lon"]].values
    districts = df.loc[has_coords, "district"].values
    if len(coords) > 1:
        dist_matrix = cdist(coords, coords, metric="euclidean")
        K = min(5, len(coords) - 1)

        for i, idx in enumerate(df.loc[has_coords].index):
            nearest_idx = np.argsort(dist_matrix[i])[1:K+1]
            neighbor_list = []
            for nidx in nearest_idx:
                neighbor_row = df.loc[has_coords].iloc[nidx]
                neighbor_list.append({
                    "district": neighbor_row["district"],
                    "distance": float(dist_matrix[i, nidx]),
                    **{col: neighbor_row[col] for col in df.columns if col not in ["lat", "lon"]}
                })
            neighbor_details[df.loc[idx, "district"]] = neighbor_list
            # For backward compatibility, keep the avg features
            for col in ["rent_demand_mean_pcm", "rent_avg_pcm", "growth_latest_avg_price"]:
                if col in df.columns:
                    vals = df.loc[has_coords].iloc[nearest_idx][col].dropna()
                    if len(vals) > 0:
                        df.loc[idx, f"spatial_{col}_neighbor_avg"] = vals.mean()

    print(f"  Added spatial features for {has_coords.sum()} districts")
    return df, neighbor_details


def add_temporal_features(df: pd.DataFrame, df_ts: pd.DataFrame) -> pd.DataFrame:
    """Add temporal trend features from time series."""
    print("Adding temporal features...")
    if df_ts.empty:
        print("  No time series data available")
        return df
    
    ts_features = []
    for district in df["district"].unique():
        ts = df_ts[df_ts["district"] == district].sort_values(["year", "month"])
        if len(ts) < 3:
            continue
        
        feats = {"district": district}
        if len(ts) >= 12:
            recent, previous = ts["avg_price"].tail(6).mean(), ts["avg_price"].iloc[-12:-6].mean()
            if previous and previous > 0:
                feats["temporal_6mo_growth"] = (recent - previous) / previous * 100
        
        pct = ts["pct_change"].dropna()
        if len(pct) > 0:
            feats["temporal_volatility"] = pct.std()
            feats["temporal_avg_monthly_change"] = pct.mean()
        
        if len(ts) >= 6:
            recent_price, long_avg = ts["avg_price"].tail(3).mean(), ts["avg_price"].mean()
            if long_avg and long_avg > 0:
                feats["temporal_momentum"] = (recent_price - long_avg) / long_avg * 100
        
        ts_features.append(feats)
    
    if ts_features:
        df = df.merge(pd.DataFrame(ts_features), on="district", how="left")
        print(f"  Added temporal features for {len(ts_features)} districts")
    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """Prepare feature matrix with advanced feature engineering."""
    print("Preparing feature matrix...")
    exclude = {"district", "area_code_type", "error", TARGET_COL, FALLBACK_TARGET, "lat", "lon", "region"}
    
    cols = [c for c in df.columns if c not in exclude and df[c].dtype in ["float64", "int64", "float32", "int32"]]
    X = df[cols].copy()
    
    # Add derived features for better predictions
    if "rent_pcm_max" in X.columns and "rent_pcm_min" in X.columns:
        X["rent_price_spread"] = X["rent_pcm_max"] - X["rent_pcm_min"]
    if "sale_demand_mean_price" in X.columns and "rent_demand_mean_pcm" in X.columns:
        X["rental_yield_estimate"] = (X["rent_demand_mean_pcm"] * 12) / X["sale_demand_mean_price"].replace(0, np.nan) * 100
    if "current_rent_listings" in X.columns and "total_properties" in X.columns:
        X["rent_supply_ratio"] = X["current_rent_listings"] / X["total_properties"].replace(0, np.nan) * 100
    
    # Fill missing values with median (more robust than mean)
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median() if not pd.isna(X[col].median()) else 0)
    
    # Cap extreme outliers (beyond 99.5th percentile)
    for col in X.columns:
        if X[col].std() > 0:
            upper = X[col].quantile(0.995)
            X[col] = X[col].clip(upper=upper)
    
    print(f"  Feature matrix: {X.shape[0]} × {X.shape[1]}")
    return X, cols


# ============ SYNTHETIC DATA GENERATION ============
def generate_synthetic_data(X: pd.DataFrame, y: pd.Series, n: int = 100) -> Tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic training data with realistic feature correlations."""
    np.random.seed(42)
    profiles = list(RENTAL_PROFILES.keys())
    weights = [0.1, 0.25, 0.3, 0.2, 0.15]
    
    # Learn correlations from real data if available
    valid = y.notna() & (y > 0)
    if valid.sum() > 0:
        real_X = X[valid]
        real_y = y[valid]
        # Calculate mean ratios from real data
        rent_to_sale_ratio = (real_y / real_X["sale_demand_mean_price"]).median() if "sale_demand_mean_price" in real_X.columns and real_X["sale_demand_mean_price"].notna().sum() > 0 else 0.05
        rent_range_ratio = (real_X["rent_pcm_max"] / real_X["rent_pcm_min"]).median() if "rent_pcm_min" in real_X.columns and (real_X["rent_pcm_min"] > 0).sum() > 0 else 2.0
    else:
        rent_to_sale_ratio, rent_range_ratio = 0.05, 2.0
    
    synthetic_X, synthetic_y = [], []
    for _ in range(n):
        profile = np.random.choice(profiles, p=weights)
        p = RENTAL_PROFILES[profile]
        rent = np.clip(np.random.normal(p["mean"], p["std"]), p["min"], p["max"])
        
        # More realistic property value based on yield
        yield_rate = np.random.uniform(0.03, 0.06)  # 3-6% rental yield
        prop_value = (rent * 12) / yield_rate
        
        features = {
            "growth_latest_avg_price": prop_value * np.random.uniform(0.95, 1.05),
            "sale_demand_mean_price": prop_value * np.random.uniform(0.9, 1.1),
            "sold_price_min_5yrs": prop_value * np.random.uniform(0.7, 0.9),
            "sold_price_max_5yrs": prop_value * np.random.uniform(1.1, 1.4),
            "rent_demand_mean_pcm": rent * np.random.uniform(0.95, 1.05),
            "rent_avg_pcm": rent * np.random.uniform(0.9, 1.1),
            "rent_pcm_min": rent / rent_range_ratio,
            "rent_pcm_max": rent * (rent_range_ratio - 1),
            "total_properties": int(np.random.lognormal(9, 0.8)),  # Log-normal for realistic distribution
            "current_rent_listings": int(np.random.lognormal(4, 1.2)),
            "current_sale_listings": int(np.random.lognormal(4.5, 1.2)),
            "rent_listing_count": int(np.random.lognormal(3.5, 1)),
            "sale_listing_count": int(np.random.lognormal(4, 1)),
            "rent_demand_days_on_market": int(np.random.gamma(3, 10)),  # Skewed distribution
            "rent_demand_months_inventory": np.random.gamma(2, 1),
            "sale_demand_days_on_market": int(np.random.gamma(4, 15)),
            "growth_5yr_total_pct": np.random.normal(25, 20),
            "crime_total_incidents": int(np.random.gamma(3, 150 if profile in ["prime_london", "central_london"] else 80)),
        }
        features["growth_avg_yearly_pct"] = features["growth_5yr_total_pct"] / 5
        for col in X.columns:
            features.setdefault(col, 0)
        
        synthetic_X.append(features)
        synthetic_y.append(rent)
    
    valid = y.notna() & (y > 0)
    if valid.sum() > 0:
        df_syn = pd.DataFrame(synthetic_X)[X.columns]
        return pd.concat([X[valid], df_syn], ignore_index=True), pd.concat([y[valid], pd.Series(synthetic_y)], ignore_index=True)
    return pd.DataFrame(synthetic_X)[X.columns], pd.Series(synthetic_y)


# ============ MODEL TRAINING ============
def train_quantile_model(X: pd.DataFrame, y: pd.Series, min_samples: int = 20) -> Dict[str, Any]:
    """Train quantile regression models for P10/P50/P90."""
    print(f"\nTraining quantile models...")
    
    valid = y.notna() & (y > 0)
    X_train, y_train = X[valid].copy(), y[valid].copy()
    print(f"  Training samples: {len(X_train)}")
    
    if len(X_train) < min_samples:
        print(f"  ⚠️ Augmenting with synthetic data...")
        X_train, y_train = generate_synthetic_data(X, y)
        print(f"  Augmented to {len(X_train)} samples")
    
    models = {}
    for q in QUANTILES:
        print(f"    Training Q{int(q*100)}...")
        if USE_LIGHTGBM:
            # Optimized hyperparameters for better accuracy
            model = lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=150, max_depth=5,
                                       learning_rate=0.05, num_leaves=31, min_child_samples=5,
                                       subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
                                       random_state=42, verbose=-1)
        else:
            # Optimized sklearn fallback
            model = GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=150, max_depth=4,
                                               learning_rate=0.05, min_samples_leaf=5, subsample=0.8,
                                               random_state=42)
        model.fit(X_train, y_train)
        models[f"q{int(q*100)}"] = model
    
    return {
        "models": models, "feature_names": list(X_train.columns), "quantiles": QUANTILES,
        "target_col": TARGET_COL, "n_train_samples": len(X_train),
        "train_target_stats": {"mean": float(y_train.mean()), "std": float(y_train.std()),
                               "min": float(y_train.min()), "max": float(y_train.max())}
    }


def evaluate_model(artifact: Dict, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
    """Evaluate model performance."""
    print("\nEvaluating model...")
    valid = y.notna() & (y > 0)
    if valid.sum() == 0:
        return {}
    
    X_eval, y_eval = X[valid], y[valid]
    preds = {name: model.predict(X_eval) for name, model in artifact["models"].items()}
    
    metrics = {}
    if "q50" in preds:
        metrics["mae"] = mean_absolute_error(y_eval, preds["q50"])
        metrics["rmse"] = np.sqrt(mean_squared_error(y_eval, preds["q50"]))
        metrics["mape"] = np.mean(np.abs((y_eval - preds["q50"]) / y_eval)) * 100
        print(f"  MAE: £{metrics['mae']:.0f}, RMSE: £{metrics['rmse']:.0f}, MAPE: {metrics['mape']:.1f}%")
    
    if "q10" in preds and "q90" in preds:
        metrics["coverage_80"] = np.mean((y_eval >= preds["q10"]) & (y_eval <= preds["q90"]))
        metrics["avg_interval_width"] = np.mean(preds["q90"] - preds["q10"])
        print(f"  Coverage: {metrics['coverage_80']*100:.1f}%, Interval: £{metrics['avg_interval_width']:.0f}")
    
    return metrics


def compute_shap(artifact: Dict, X: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Compute SHAP feature importance."""
    print("\nComputing SHAP values...")
    model = artifact["models"].get("q50")
    if not model:
        return None
    
    try:
        X_sample = X.sample(min(100, len(X)), random_state=42) if len(X) > 100 else X
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_sample)
        
        importance = pd.DataFrame({"feature": X_sample.columns, "importance": np.abs(shap_vals).mean(axis=0)})
        importance = importance.sort_values("importance", ascending=False)
        
        print("\n  Top 10 Features:")
        for _, r in importance.head(10).iterrows():
            print(f"    {r['feature']:40s} {r['importance']:.2f}")
        
        return importance
    except Exception as e:
        print(f"  SHAP failed: {e}")
        return None


# ============ MODEL I/O ============
def save_model(artifact: Dict, metrics: Dict, shap_importance: Optional[pd.DataFrame]):
    """Save model to disk."""
    artifact["metrics"] = metrics
    if shap_importance is not None:
        artifact["shap_feature_importance"] = shap_importance
    
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(artifact, f)
    print(f"\n✅ Model saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")


def load_model(path: Path = MODEL_PATH) -> Dict:
    """Load model from disk."""
    with open(path, "rb") as f:
        return pickle.load(f)


def predict(artifact: Dict, features: Dict[str, float]) -> Dict[str, float]:
    """Make prediction with trained model."""
    X = pd.DataFrame([{name: features.get(name, 0) for name in artifact["feature_names"]}])
    preds = {name: float(model.predict(X)[0]) for name, model in artifact["models"].items()}
    return {"p10": preds.get("q10", 0), "p50": preds.get("q50", 0), "p90": preds.get("q90", 0), "unit": "GBP/month"}


# ============ MAIN ============
if __name__ == "__main__":
    print("=" * 60)
    print("SPATIO-TEMPORAL RENTAL VALUATION MODEL")
    print("=" * 60)
    
    # Load and prepare data
    df, df_ts = load_data()
    df, neighbor_details = add_spatial_features(df)
    df = add_temporal_features(df, df_ts)
    
    # Find target column
    target_col = None
    for col in [TARGET_COL, FALLBACK_TARGET] + [c for c in df.columns if "rent" in c.lower() and "pcm" in c.lower()]:
        if col in df.columns and df[col].notna().sum() > 5:
            target_col = col
            break
    if not target_col:
        raise ValueError("No suitable target column found")
    
    print(f"\n📊 Target: {target_col} (n={df[target_col].notna().sum()}, mean=£{df[target_col].mean():.0f})")
    
    # Prepare features and target
    X, _ = prepare_features(df)
    y = df[target_col]

    # Only use valid rows for splitting
    valid = y.notna() & (y > 0)
    X_valid, y_valid = X[valid], y[valid]

    # Split into train/test sets (80/20 split)
    X_train, X_test, y_train, y_test = train_test_split(
        X_valid, y_valid, test_size=0.2, random_state=42
    )

    # Train on train set only
    artifact = train_quantile_model(X_train, y_train)
    artifact["neighbors"] = neighbor_details

    print("\n--- Train set evaluation ---")
    train_metrics = evaluate_model(artifact, X_train, y_train)
    print("\n--- Test set evaluation ---")
    test_metrics = evaluate_model(artifact, X_test, y_test)

    shap_imp = compute_shap(artifact, X_train)
    save_model(artifact, test_metrics, shap_imp)

    # Demo
    print("\n" + "=" * 60)
    print("DEMO PREDICTION")
    idx = X_test.index[0] if len(X_test) > 0 else X_train.index[0]
    pred = predict(artifact, X.loc[idx].to_dict())
    print(f"District: {df.loc[idx, 'district']}")
    print(f"Actual: £{y.loc[idx]:.0f} | Predicted: £{pred['p10']:.0f} - £{pred['p50']:.0f} - £{pred['p90']:.0f}")
    print("\n✅ Training complete!")