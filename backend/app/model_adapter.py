"""
Model adapter with stub, pickle, and HTTP implementations.

=============================================================================
PLACEHOLDER MODULE - FOR TEAMMATE INTEGRATION
=============================================================================

This entire module contains PLACEHOLDER implementations for the ML model.
The actual trained spatio-temporal model will be built by a teammate.

HOW TO INTEGRATE YOUR MODEL:
1. If providing a pickle file:
   - Set MODEL_PROVIDER=local_pickle in .env
   - Set MODEL_PATH to your model file path
   - Ensure your model has a predict_quantiles() method returning {"p10", "p50", "p90"}

2. If providing an HTTP service:
   - Set MODEL_PROVIDER=http in .env  
   - Set MODEL_HTTP_URL to your service endpoint
   - Your endpoint should accept POST with ModelFeatures JSON
   - Return {"p10": float, "p50": float, "p90": float, "unit": str}

3. If you want to replace the adapter directly:
   - Create a new class extending ModelAdapter
   - Implement predict_quantiles() method
   - Update get_model_adapter() factory function

The StubModelAdapter is a deterministic placeholder that returns plausible
rent values based on feature hashing. It should be replaced with the real
model for production use.
=============================================================================
"""
import hashlib
import math
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

from .config import get_settings
from .schemas import ModelFeatures, PredictionResult, PredictionMetadata


class ModelAdapter(ABC):
    """
    Abstract base class for model adapters.
    
    This interface defines the contract between the agent and the ML model.
    Teammate should implement this interface or use one of the existing adapters.
    """
    
    @abstractmethod
    def predict_quantiles(self, features: ModelFeatures) -> PredictionResult:
        """
        Predict rent quantiles (P10, P50, P90).
        
        Args:
            features: Model input features (see ModelFeatures schema)
            
        Returns:
            PredictionResult with quantile predictions
        """
        pass
    
    def predict_quantiles_batch(
        self, features_list: list[ModelFeatures]
    ) -> list[PredictionResult]:
        """Batch prediction (default: sequential)."""
        return [self.predict_quantiles(f) for f in features_list]


# =============================================================================
# PLACEHOLDER: StubModelAdapter
# =============================================================================
# This is a PLACEHOLDER model that returns deterministic pseudo-random values.
# Replace with actual trained model from teammate.
# =============================================================================

class StubModelAdapter(ModelAdapter):
    """
    PLACEHOLDER: Deterministic stub model for development.
    
    !!! THIS IS A PLACEHOLDER - NOT A REAL ML MODEL !!!
    
    Uses feature hash for reproducible pseudo-random outputs.
    Returns plausible London rent values for demo purposes.
    
    TODO: Replace with actual trained spatio-temporal model from teammate.
    """
    
    def __init__(self):
        self.base_rent = 2000  # Base rent in GBP
        self.version = "placeholder-stub-v1"  # Marked as placeholder
    
    def _feature_hash(self, features: ModelFeatures) -> int:
        """Generate deterministic hash from features."""
        # Create string representation of key features
        key_parts = [
            features.area_code,
            str(features.month),
            str(features.horizon_months),
            str(features.median_rent or 0),
            str(features.demand_index or 0),
        ]
        key_string = "|".join(key_parts)
        hash_bytes = hashlib.md5(key_string.encode()).digest()
        return int.from_bytes(hash_bytes[:4], "big")
    
    def predict_quantiles(self, features: ModelFeatures) -> PredictionResult:
        """Generate deterministic prediction based on features."""
        seed = self._feature_hash(features)
        
        # Use median rent as base if available
        base = features.median_rent or self.base_rent
        
        # Apply modifiers based on features
        modifiers = 1.0
        
        # Demand effect
        if features.demand_index:
            demand_factor = (features.demand_index - 75) / 100  # Centered at 75
            modifiers += demand_factor * 0.15
        
        # Growth effect
        if features.rent_growth_yoy:
            modifiers += features.rent_growth_yoy / 100 * 0.5
        
        # Neighbor effect
        if features.neighbor_avg_rent:
            neighbor_diff = (features.neighbor_avg_rent - base) / base
            modifiers += neighbor_diff * 0.2
        
        # Horizon effect (slight increase for longer horizons)
        horizon_factor = 1 + (features.horizon_months - 1) * 0.005
        modifiers *= horizon_factor
        
        # Calculate P50
        p50 = base * modifiers
        
        # Add pseudo-random variation for P10/P90 spread
        variation = ((seed % 1000) / 1000) * 0.1 + 0.15  # 15-25% spread
        
        p10 = p50 * (1 - variation)
        p90 = p50 * (1 + variation)
        
        # Round to realistic values
        p10 = round(p10 / 25) * 25  # Round to nearest £25
        p50 = round(p50 / 25) * 25
        p90 = round(p90 / 25) * 25
        
        return PredictionResult(
            p10=float(p10),
            p50=float(p50),
            p90=float(p90),
            unit="GBP/month",
            horizon_months=features.horizon_months,
            metadata=PredictionMetadata(
                model_version=self.version,
                feature_version="v1",
                timestamp=datetime.utcnow(),
            ),
        )


# =============================================================================
# PLACEHOLDER: PickleModelAdapter  
# =============================================================================
# This adapter is READY for teammate's pickle model file.
# Set MODEL_PROVIDER=local_pickle and MODEL_PATH in .env to use.
# =============================================================================

class PickleModelAdapter(ModelAdapter):
    """
    PLACEHOLDER: Load model from pickle file.
    
    Ready for teammate's trained model. Set environment variables:
    - MODEL_PROVIDER=local_pickle
    - MODEL_PATH=./path/to/your/model.pkl
    
    Expected model interface:
    - model.predict_quantiles(features_dict) -> {"p10", "p50", "p90"}
    - OR model.predict(feature_array) -> point prediction (quantiles estimated)
    """
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.version = "placeholder-pickle-v1"
        self._load_model()
    
    def _load_model(self):
        """Load model from pickle file."""
        try:
            import joblib
            self.model = joblib.load(self.model_path)
            print(f"Loaded model from {self.model_path}")
        except Exception as e:
            print(f"Failed to load model from {self.model_path}: {e}")
            print("Falling back to stub model")
            self.model = None
    
    def predict_quantiles(self, features: ModelFeatures) -> PredictionResult:
        """Predict using loaded model."""
        if self.model is None:
            # Fallback to stub
            return StubModelAdapter().predict_quantiles(features)
        
        try:
            # Convert features to model input format
            # This depends on actual model implementation
            feature_dict = features.model_dump(exclude_none=True)
            
            # Assume model has predict_quantiles method or similar
            if hasattr(self.model, "predict_quantiles"):
                result = self.model.predict_quantiles(feature_dict)
                return PredictionResult(
                    p10=result["p10"],
                    p50=result["p50"],
                    p90=result["p90"],
                    unit="GBP/month",
                    horizon_months=features.horizon_months,
                    metadata=PredictionMetadata(
                        model_version=self.version,
                        feature_version="v1",
                    ),
                )
            elif hasattr(self.model, "predict"):
                # If only point prediction, estimate quantiles
                pred = self.model.predict([list(feature_dict.values())])[0]
                return PredictionResult(
                    p10=pred * 0.85,
                    p50=pred,
                    p90=pred * 1.15,
                    unit="GBP/month",
                    horizon_months=features.horizon_months,
                    metadata=PredictionMetadata(
                        model_version=self.version,
                        feature_version="v1",
                    ),
                )
        except Exception as e:
            print(f"Model prediction failed: {e}")
            return StubModelAdapter().predict_quantiles(features)
        
        return StubModelAdapter().predict_quantiles(features)


# =============================================================================
# PLACEHOLDER: HTTPModelAdapter
# =============================================================================
# This adapter is READY for teammate's model HTTP service.
# Set MODEL_PROVIDER=http and MODEL_HTTP_URL in .env to use.
# =============================================================================

class HTTPModelAdapter(ModelAdapter):
    """
    PLACEHOLDER: Call remote model service via HTTP.
    
    Ready for teammate's model service. Set environment variables:
    - MODEL_PROVIDER=http
    - MODEL_HTTP_URL=http://your-model-service/predict
    
    Expected API:
    - POST with JSON body containing ModelFeatures
    - Response: {"p10": float, "p50": float, "p90": float, "unit": str}
    """
    
    def __init__(self, model_url: str):
        self.model_url = model_url
        self.version = "placeholder-http-v1"
    
    def predict_quantiles(self, features: ModelFeatures) -> PredictionResult:
        """Call remote model service."""
        import httpx
        
        try:
            response = httpx.post(
                self.model_url,
                json=features.model_dump(exclude_none=True),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            return PredictionResult(
                p10=data["p10"],
                p50=data["p50"],
                p90=data["p90"],
                unit=data.get("unit", "GBP/month"),
                horizon_months=features.horizon_months,
                metadata=PredictionMetadata(
                    model_version=data.get("model_version", self.version),
                    feature_version="v1",
                ),
            )
        except Exception as e:
            print(f"HTTP model call failed: {e}")
            # Fallback to stub
            return StubModelAdapter().predict_quantiles(features)


# Factory function
_adapter: Optional[ModelAdapter] = None


def get_model_adapter() -> ModelAdapter:
    """Get model adapter based on configuration."""
    global _adapter
    
    if _adapter is not None:
        return _adapter
    
    settings = get_settings()
    provider = settings.model_provider.lower()
    
    if provider == "local_pickle":
        _adapter = PickleModelAdapter(settings.model_path)
    elif provider == "http":
        _adapter = HTTPModelAdapter(settings.model_http_url)
    else:  # Default to stub
        _adapter = StubModelAdapter()
    
    return _adapter
