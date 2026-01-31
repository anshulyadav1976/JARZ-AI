"""
Agent tools for the chat-based LangGraph agent.

These tools allow the LLM to interact with the rental valuation system.
The LLM decides when to call these tools based on user queries.
"""
from typing import Any, Optional
from dataclasses import dataclass

from ..schemas import UserQuery, PredictionResult, ExplanationResult, ResolvedLocation, Neighbor
from ..feature_builder import build_features
from ..model_adapter import get_model_adapter
from ..explain import explain_prediction
from ..a2ui_builder import build_complete_ui
from ..scansan_client import get_scansan_client


@dataclass
class RentForecastResult:
    """Result from the rent forecast tool."""
    prediction: dict
    explanation: dict
    location: dict
    neighbors: list[dict]
    a2ui_messages: list[dict]
    summary: str


@dataclass
class LocationSearchResult:
    """Result from location search tool."""
    found: bool
    location: Optional[dict]
    message: str


# Tool definitions for the LLM (OpenAI function calling format)
TOOL_DEFINITIONS = [
    {
        "name": "get_rent_forecast",
        "description": "Get a rental price forecast for a specific location in the UK. This tool analyzes the area, considers spatial neighbors, and predicts P10/P50/P90 rent values. Use this when the user asks about rent prices, rental forecasts, property valuations, or wants to know how much rent costs in an area.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to forecast rent for. Can be a UK postcode (e.g., 'NW1', 'E14', 'SW1A'), area name (e.g., 'Camden', 'Canary Wharf'), or district."
                },
                "horizon_months": {
                    "type": "integer",
                    "description": "Forecast horizon in months (1, 3, 6, or 12). Default is 6 months.",
                    "enum": [1, 3, 6, 12],
                    "default": 6
                },
                "k_neighbors": {
                    "type": "integer",
                    "description": "Number of spatial neighbors to consider for spatial dependency analysis. Default is 5.",
                    "default": 5
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "search_location",
        "description": "Search for a location to get its area code and basic information. Use this to validate or disambiguate a location before running a forecast.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The location query to search for (postcode, area name, etc.)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "compare_areas",
        "description": "Compare rental forecasts between two different areas. PLACEHOLDER - not yet implemented.",
        "parameters": {
            "type": "object",
            "properties": {
                "location1": {
                    "type": "string",
                    "description": "First location to compare"
                },
                "location2": {
                    "type": "string",
                    "description": "Second location to compare"
                },
                "horizon_months": {
                    "type": "integer",
                    "description": "Forecast horizon in months",
                    "enum": [1, 3, 6, 12],
                    "default": 6
                }
            },
            "required": ["location1", "location2"]
        }
    }
]


async def execute_get_rent_forecast(
    location: str,
    horizon_months: int = 6,
    k_neighbors: int = 5,
) -> RentForecastResult:
    """
    Execute the rent forecast tool.
    
    This runs the full valuation pipeline:
    1. Resolve location to area code
    2. Build spatio-temporal features
    3. Run prediction model
    4. Generate explanation
    5. Build A2UI components
    
    Args:
        location: Location string (postcode, area name)
        horizon_months: Forecast horizon (1, 3, 6, or 12)
        k_neighbors: Number of spatial neighbors
        
    Returns:
        RentForecastResult with prediction, explanation, and UI components
    """
    # Build query
    query = UserQuery(
        location_input=location,
        horizon_months=horizon_months,
        view_mode="single",
        k_neighbors=k_neighbors,
        radius_km=5.0,
    )
    
    # Build features (includes location resolution and neighbor fetch)
    features, resolved_location, neighbors = await build_features(query)
    
    # Run prediction
    adapter = get_model_adapter()
    prediction = adapter.predict_quantiles(features)
    
    # Generate explanation
    explanation = explain_prediction(features, prediction)
    
    # Build A2UI messages
    a2ui_messages = build_complete_ui(
        prediction=prediction,
        explanation=explanation,
        location=resolved_location,
        neighbors=neighbors,
        horizon_months=horizon_months,
        k_neighbors=k_neighbors,
    )
    
    # Generate text summary for the LLM to use
    summary = _generate_forecast_summary(
        prediction=prediction,
        location=resolved_location,
        explanation=explanation,
        horizon_months=horizon_months,
    )
    
    return RentForecastResult(
        prediction=prediction.model_dump() if hasattr(prediction, 'model_dump') else prediction.__dict__,
        explanation=explanation.model_dump() if hasattr(explanation, 'model_dump') else explanation.__dict__,
        location=resolved_location.model_dump() if hasattr(resolved_location, 'model_dump') else resolved_location.__dict__,
        neighbors=[n.model_dump() if hasattr(n, 'model_dump') else n.__dict__ for n in neighbors],
        a2ui_messages=a2ui_messages,
        summary=summary,
    )


def _generate_forecast_summary(
    prediction: PredictionResult,
    location: ResolvedLocation,
    explanation: ExplanationResult,
    horizon_months: int,
) -> str:
    """Generate a text summary of the forecast for the LLM."""
    area_name = location.display_name or location.area_code
    
    # Format drivers
    top_drivers = explanation.drivers[:3] if explanation.drivers else []
    driver_text = ""
    if top_drivers:
        driver_parts = []
        for d in top_drivers:
            direction = "increasing" if d.direction == "positive" else "decreasing"
            driver_parts.append(f"{d.name} ({direction} rent by ~{d.contribution:.0f} GBP)")
        driver_text = f" Key factors: {', '.join(driver_parts)}."
    
    summary = (
        f"For {area_name}, the {horizon_months}-month rental forecast shows: "
        f"P50 (median) rent of {prediction.p50:,.0f} {prediction.unit}, "
        f"with a confidence band from {prediction.p10:,.0f} (P10) to {prediction.p90:,.0f} (P90) {prediction.unit}."
        f"{driver_text}"
    )
    
    return summary


async def execute_search_location(query: str) -> LocationSearchResult:
    """
    Execute the location search tool.
    
    Args:
        query: Location search query
        
    Returns:
        LocationSearchResult with found location or error message
    """
    client = get_scansan_client()
    
    try:
        location = await client.search_area_codes(query)
        
        if location:
            return LocationSearchResult(
                found=True,
                location=location.model_dump() if hasattr(location, 'model_dump') else location.__dict__,
                message=f"Found location: {location.display_name or location.area_code}"
            )
        else:
            return LocationSearchResult(
                found=False,
                location=None,
                message=f"Could not find a location matching '{query}'. Try a UK postcode like NW1, E14, or SW1."
            )
    except Exception as e:
        return LocationSearchResult(
            found=False,
            location=None,
            message=f"Error searching for location: {str(e)}"
        )


async def execute_compare_areas(
    location1: str,
    location2: str,
    horizon_months: int = 6,
) -> dict:
    """
    PLACEHOLDER: Compare two areas.
    
    This is a placeholder for future implementation.
    Currently returns a message indicating the feature is not yet available.
    """
    return {
        "status": "not_implemented",
        "message": (
            f"Area comparison between '{location1}' and '{location2}' is not yet implemented. "
            "This feature will be available in a future update. "
            "For now, you can run separate forecasts for each location."
        )
    }


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a tool by name with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        
    Returns:
        Tool execution result as a dict
    """
    if tool_name == "get_rent_forecast":
        result = await execute_get_rent_forecast(
            location=arguments["location"],
            horizon_months=arguments.get("horizon_months", 6),
            k_neighbors=arguments.get("k_neighbors", 5),
        )
        return {
            "success": True,
            "prediction": result.prediction,
            "explanation": result.explanation,
            "location": result.location,
            "neighbors": result.neighbors,
            "a2ui_messages": result.a2ui_messages,
            "summary": result.summary,
        }
    
    elif tool_name == "search_location":
        result = await execute_search_location(
            query=arguments["query"]
        )
        return {
            "success": result.found,
            "location": result.location,
            "message": result.message,
        }
    
    elif tool_name == "compare_areas":
        result = await execute_compare_areas(
            location1=arguments["location1"],
            location2=arguments["location2"],
            horizon_months=arguments.get("horizon_months", 6),
        )
        return result
    
    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
