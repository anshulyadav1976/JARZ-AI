"""Explainability module for prediction drivers."""
from typing import Optional
from .schemas import ModelFeatures, PredictionResult, ExplanationResult, Driver
from .config import get_settings


def explain_stub(features: ModelFeatures) -> ExplanationResult:
    """
    Generate heuristic explanation for stub model.
    
    Creates plausible driver contributions based on feature values.
    """
    drivers = []
    
    # Demand impact
    if features.demand_index is not None:
        demand_base = 75.0
        demand_diff = features.demand_index - demand_base
        if abs(demand_diff) > 1:
            drivers.append(Driver(
                name="Rental Demand Index",
                contribution=round(demand_diff * 5, 1),  # ~5 GBP per point
                direction="positive" if demand_diff > 0 else "negative",
            ))
    
    # Growth impact
    if features.rent_growth_yoy is not None and abs(features.rent_growth_yoy) > 0.1:
        growth_contribution = features.rent_growth_yoy * 50  # Scale factor
        drivers.append(Driver(
            name="Year-over-Year Growth",
            contribution=round(abs(growth_contribution), 1),
            direction="positive" if features.rent_growth_yoy > 0 else "negative",
        ))
    
    # Neighbor effect
    if features.neighbor_avg_rent is not None and features.median_rent is not None:
        diff = features.neighbor_avg_rent - features.median_rent
        if abs(diff) > 50:
            drivers.append(Driver(
                name="Neighboring Area Rents",
                contribution=round(abs(diff) * 0.2, 1),
                direction="positive" if diff > 0 else "negative",
            ))
    
    # Seasonal effect
    if features.month in [6, 7, 8, 9]:  # Peak rental season
        drivers.append(Driver(
            name="Seasonal Demand (Summer)",
            contribution=round(50 + features.month * 5, 1),
            direction="positive",
        ))
    elif features.month in [12, 1, 2]:  # Low season
        drivers.append(Driver(
            name="Seasonal Effect (Winter)",
            contribution=round(30 + (12 - features.month) * 3, 1),
            direction="negative",
        ))
    
    # Horizon effect
    if features.horizon_months > 3:
        drivers.append(Driver(
            name="Forecast Horizon",
            contribution=round(features.horizon_months * 10, 1),
            direction="positive",
        ))
    
    # Neighbor count effect
    if features.neighbor_count > 0:
        drivers.append(Driver(
            name="Spatial Connectivity",
            contribution=round(features.neighbor_count * 8, 1),
            direction="positive",
        ))
    
    # Listing count effect (market liquidity)
    if features.listing_count is not None:
        if features.listing_count > 200:
            drivers.append(Driver(
                name="Market Liquidity",
                contribution=round((features.listing_count - 200) * 0.1, 1),
                direction="positive",
            ))
        elif features.listing_count < 100:
            drivers.append(Driver(
                name="Limited Supply",
                contribution=round((100 - features.listing_count) * 0.2, 1),
                direction="positive",  # Limited supply = higher rents
            ))
    
    # Sort by absolute contribution and take top 8
    drivers.sort(key=lambda d: abs(d.contribution), reverse=True)
    drivers = drivers[:8]
    
    # Calculate base value (estimated baseline rent)
    base_value = features.median_rent or 2000.0
    
    return ExplanationResult(
        drivers=drivers,
        base_value=base_value,
    )


def explain_shap(
    model,
    features: ModelFeatures,
    feature_names: Optional[list[str]] = None,
) -> ExplanationResult:
    """
    Compute SHAP values for real model.
    
    Requires shap package and a tree-based model.
    """
    try:
        import shap
        import numpy as np
        
        # Convert features to array
        feature_dict = features.model_dump(exclude_none=True)
        
        # Filter numeric features
        numeric_features = {
            k: v for k, v in feature_dict.items()
            if isinstance(v, (int, float)) and k not in ["area_code", "area_code_district"]
        }
        
        if feature_names is None:
            feature_names = list(numeric_features.keys())
        
        feature_array = np.array([[numeric_features.get(f, 0) for f in feature_names]])
        
        # Create explainer (TreeExplainer for tree models)
        if hasattr(model, "predict"):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(feature_array)
            
            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # Take first output
            
            shap_values = shap_values.flatten()
            
            # Create drivers from SHAP values
            drivers = []
            for i, (name, value) in enumerate(zip(feature_names, shap_values)):
                if abs(value) > 1:  # Only significant contributions
                    drivers.append(Driver(
                        name=name.replace("_", " ").title(),
                        contribution=round(abs(value), 1),
                        direction="positive" if value > 0 else "negative",
                    ))
            
            # Sort and limit
            drivers.sort(key=lambda d: abs(d.contribution), reverse=True)
            drivers = drivers[:8]
            
            return ExplanationResult(
                drivers=drivers,
                base_value=float(explainer.expected_value) if hasattr(explainer, "expected_value") else None,
            )
    
    except ImportError:
        print("SHAP not installed, falling back to heuristic explanation")
    except Exception as e:
        print(f"SHAP computation failed: {e}, falling back to heuristic")
    
    # Fallback to stub explanation
    return explain_stub(features)


def explain_prediction(
    features: ModelFeatures,
    prediction: PredictionResult,
    model=None,
) -> ExplanationResult:
    """
    Generate explanation for prediction.
    
    Uses SHAP if real model available, otherwise heuristic.
    """
    settings = get_settings()
    
    # If we have a real model and SHAP is available, use it
    if model is not None and settings.model_provider != "stub":
        return explain_shap(model, features)
    
    # Otherwise use heuristic
    return explain_stub(features)
