"""Pydantic schemas for data contracts."""
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# User Query
# ============================================================================

class UserQuery(BaseModel):
    """User query for rental valuation."""
    location_input: str = Field(..., description="User-entered location (e.g., 'NW1', 'Camden')")
    area_code: Optional[str] = Field(None, description="Resolved area code")
    horizon_months: int = Field(default=6, ge=1, le=24, description="Forecast horizon in months")
    view_mode: Literal["single", "compare"] = Field(default="single")
    radius_km: Optional[float] = Field(default=5.0, description="Radius for neighbor search")
    k_neighbors: Optional[int] = Field(default=5, description="Number of neighbors to consider")


# ============================================================================
# Model Features
# ============================================================================

class ModelFeatures(BaseModel):
    """Features passed to the prediction model."""
    # Location identifiers
    area_code: str
    area_code_district: Optional[str] = None
    
    # Temporal features
    month: int = Field(ge=1, le=12)
    quarter: int = Field(ge=1, le=4)
    rent_growth_mom: Optional[float] = None  # Month-over-month growth
    rent_growth_yoy: Optional[float] = None  # Year-over-year growth
    demand_index: Optional[float] = None
    demand_index_lag1: Optional[float] = None
    
    # Spatial features
    neighbor_avg_rent: Optional[float] = None
    neighbor_avg_demand: Optional[float] = None
    neighbor_avg_growth: Optional[float] = None
    neighbor_count: int = 0
    
    # Area statistics
    median_rent: Optional[float] = None
    avg_rent: Optional[float] = None
    listing_count: Optional[int] = None
    
    # Horizon
    horizon_months: int = 6
    
    # Allow extra fields for flexibility
    class Config:
        extra = "allow"


# ============================================================================
# Prediction Result
# ============================================================================

class PredictionMetadata(BaseModel):
    """Metadata about the prediction."""
    model_version: str = "stub-v1"
    feature_version: str = "v1"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PredictionResult(BaseModel):
    """Quantile prediction result."""
    p10: float = Field(..., description="10th percentile rent prediction")
    p50: float = Field(..., description="50th percentile (median) rent prediction")
    p90: float = Field(..., description="90th percentile rent prediction")
    unit: str = Field(default="GBP/month")
    horizon_months: int
    metadata: Optional[PredictionMetadata] = None


# ============================================================================
# Explanation Result
# ============================================================================

class Driver(BaseModel):
    """A single driver/feature contribution."""
    name: str
    contribution: float = Field(..., description="SHAP value or heuristic contribution")
    direction: Literal["positive", "negative"]


class ExplanationResult(BaseModel):
    """Explanation of prediction drivers."""
    drivers: list[Driver] = Field(default_factory=list)
    base_value: Optional[float] = Field(None, description="SHAP base value")


# ============================================================================
# Location Data
# ============================================================================

class ResolvedLocation(BaseModel):
    """Resolved location with coordinates."""
    area_code: str
    area_code_district: Optional[str] = None
    display_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class Neighbor(BaseModel):
    """Neighbor area data."""
    area_code: str
    display_name: str
    lat: float
    lon: float
    avg_rent: Optional[float] = None
    demand_index: Optional[float] = None
    distance_km: Optional[float] = None


# ============================================================================
# Historical and Forecast Data
# ============================================================================

class HistoricalDataPoint(BaseModel):
    """Historical rent data point."""
    date: str  # ISO date string
    rent: float
    p10: Optional[float] = None
    p90: Optional[float] = None


class ForecastDataPoint(BaseModel):
    """Forecast data point with quantiles."""
    date: str  # ISO date string
    p10: float
    p50: float
    p90: float


# ============================================================================
# A2UI Message Types (following A2UI v0.8 spec)
# ============================================================================

class A2UIBoundValue(BaseModel):
    """A2UI bound value - can be literal or data-bound."""
    literalString: Optional[str] = None
    literalNumber: Optional[float] = None
    literalBoolean: Optional[bool] = None
    path: Optional[str] = None


class A2UIComponent(BaseModel):
    """A2UI component definition."""
    id: str
    component: dict[str, Any]


class A2UISurfaceUpdate(BaseModel):
    """A2UI surfaceUpdate message."""
    surfaceId: str = "main"
    components: list[A2UIComponent]


class A2UIDataModelEntry(BaseModel):
    """Single entry in data model update."""
    key: str
    valueString: Optional[str] = None
    valueNumber: Optional[float] = None
    valueBoolean: Optional[bool] = None
    valueMap: Optional[list[dict]] = None
    valueArray: Optional[list[Any]] = None


class A2UIDataModelUpdate(BaseModel):
    """A2UI dataModelUpdate message."""
    surfaceId: str = "main"
    path: Optional[str] = None
    contents: list[A2UIDataModelEntry]


class A2UIBeginRendering(BaseModel):
    """A2UI beginRendering message."""
    surfaceId: str = "main"
    root: str
    catalogId: Optional[str] = None


# ============================================================================
# API Request/Response
# ============================================================================

class QueryRequest(BaseModel):
    """API request for rental valuation."""
    query: UserQuery


class QueryResponse(BaseModel):
    """Full API response."""
    location: ResolvedLocation
    prediction: PredictionResult
    explanation: ExplanationResult
    neighbors: list[Neighbor]
    historical: list[HistoricalDataPoint]
    forecast: list[ForecastDataPoint]


class StreamMessage(BaseModel):
    """Wrapper for streaming messages."""
    type: Literal["surfaceUpdate", "dataModelUpdate", "beginRendering", "error"]
    data: dict[str, Any]
