"""LangGraph agent state definition."""
from typing import Any, Optional, TypedDict
from ..schemas import (
    UserQuery,
    ModelFeatures,
    PredictionResult,
    ExplanationResult,
    ResolvedLocation,
    Neighbor,
)


class AgentState(TypedDict, total=False):
    """State passed through the agent workflow."""
    
    # Input
    query: UserQuery
    
    # Resolved data
    resolved_location: Optional[ResolvedLocation]
    
    # Raw fetched data from ScanSan
    raw_data: Optional[dict[str, Any]]
    
    # Built features
    features: Optional[ModelFeatures]
    
    # Model outputs
    prediction: Optional[PredictionResult]
    
    # Explanation
    explanation: Optional[ExplanationResult]
    
    # Neighbors for spatial visualization
    neighbors: list[Neighbor]
    
    # A2UI messages to stream
    ui_messages: list[dict[str, Any]]
    
    # Error state
    error: Optional[str]
    
    # Processing status
    status: str
