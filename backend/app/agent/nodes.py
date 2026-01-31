"""LangGraph agent nodes."""
from typing import Any
from .state import AgentState
from ..schemas import UserQuery, ResolvedLocation, Neighbor
from ..scansan_client import get_scansan_client
from ..feature_builder import build_features
from ..model_adapter import get_model_adapter
from ..explain import explain_prediction
from ..a2ui_builder import build_complete_ui


async def resolve_location_node(state: AgentState) -> dict[str, Any]:
    """
    Resolve user location input to standardized area code.
    """
    try:
        query = state["query"]
        client = get_scansan_client()
        
        location = await client.search_area_codes(query.location_input)
        
        if location is None:
            return {
                "error": f"Could not resolve location: {query.location_input}",
                "status": "error",
            }
        
        return {
            "resolved_location": location,
            "status": "location_resolved",
        }
    
    except Exception as e:
        return {
            "error": f"Location resolution failed: {str(e)}",
            "status": "error",
        }


async def fetch_data_node(state: AgentState) -> dict[str, Any]:
    """
    Fetch data from ScanSan API.
    """
    try:
        location = state.get("resolved_location")
        if not location:
            return {"error": "No resolved location", "status": "error"}
        
        client = get_scansan_client()
        
        # Fetch all data in parallel would be ideal, but for simplicity:
        summary = await client.get_area_summary(location.area_code)
        
        district = location.area_code_district or location.area_code
        demand = await client.get_district_demand(district)
        growth = await client.get_district_growth(district)
        
        raw_data = {
            "summary": summary,
            "demand": demand,
            "growth": growth,
        }
        
        return {
            "raw_data": raw_data,
            "status": "data_fetched",
        }
    
    except Exception as e:
        return {
            "error": f"Data fetch failed: {str(e)}",
            "status": "error",
        }


async def build_features_node(state: AgentState) -> dict[str, Any]:
    """
    Build model features from raw data.
    """
    try:
        query = state["query"]
        
        # Build complete features (includes location resolution + neighbor fetch)
        features, location, neighbors = await build_features(query)
        
        return {
            "features": features,
            "resolved_location": location,
            "neighbors": neighbors,
            "status": "features_built",
        }
    
    except Exception as e:
        return {
            "error": f"Feature building failed: {str(e)}",
            "status": "error",
        }


def predict_node(state: AgentState) -> dict[str, Any]:
    """
    Run model prediction.
    """
    try:
        features = state.get("features")
        if not features:
            return {"error": "No features available", "status": "error"}
        
        adapter = get_model_adapter()
        prediction = adapter.predict_quantiles(features)
        
        return {
            "prediction": prediction,
            "status": "predicted",
        }
    
    except Exception as e:
        return {
            "error": f"Prediction failed: {str(e)}",
            "status": "error",
        }


def explain_node(state: AgentState) -> dict[str, Any]:
    """
    Generate explanation for prediction.
    """
    try:
        features = state.get("features")
        prediction = state.get("prediction")
        
        if not features or not prediction:
            return {"error": "Missing features or prediction", "status": "error"}
        
        explanation = explain_prediction(features, prediction)
        
        return {
            "explanation": explanation,
            "status": "explained",
        }
    
    except Exception as e:
        return {
            "error": f"Explanation failed: {str(e)}",
            "status": "error",
        }


def render_a2ui_node(state: AgentState) -> dict[str, Any]:
    """
    Build A2UI messages for frontend.
    """
    try:
        prediction = state.get("prediction")
        explanation = state.get("explanation")
        location = state.get("resolved_location")
        neighbors = state.get("neighbors", [])
        query = state["query"]
        
        if not all([prediction, explanation, location]):
            return {"error": "Missing data for UI rendering", "status": "error"}
        
        messages = build_complete_ui(
            prediction=prediction,
            explanation=explanation,
            location=location,
            neighbors=neighbors,
            horizon_months=query.horizon_months,
            k_neighbors=query.k_neighbors or 5,
        )
        
        return {
            "ui_messages": messages,
            "status": "complete",
        }
    
    except Exception as e:
        return {
            "error": f"UI rendering failed: {str(e)}",
            "status": "error",
        }


# Node registry for easy lookup
NODES = {
    "resolve_location": resolve_location_node,
    "fetch_data": fetch_data_node,
    "build_features": build_features_node,
    "predict": predict_node,
    "explain": explain_node,
    "render_a2ui": render_a2ui_node,
}
