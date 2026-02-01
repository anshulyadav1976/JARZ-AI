"""A2UI message builders following v0.8 spec."""
import json
from datetime import datetime, timedelta
from typing import Any, Optional
from .schemas import (
    PredictionResult,
    ExplanationResult,
    ResolvedLocation,
    Neighbor,
    HistoricalDataPoint,
    ForecastDataPoint,
)


def _literal_string(value: str) -> dict:
    """Create A2UI literalString bound value."""
    return {"literalString": value}


def _literal_number(value: float) -> dict:
    """Create A2UI literalNumber bound value."""
    return {"literalNumber": value}


def _data_path(path: str) -> dict:
    """Create A2UI path bound value."""
    return {"path": path}


# ============================================================================
# Component Builders
# ============================================================================

def build_text_component(
    id: str,
    text: str,
    usage_hint: Optional[str] = None,
) -> dict:
    """Build A2UI Text component."""
    component = {
        "Text": {
            "text": _literal_string(text),
        }
    }
    if usage_hint:
        component["Text"]["usageHint"] = usage_hint
    
    return {"id": id, "component": component}


def build_column_component(id: str, children: list[str]) -> dict:
    """Build A2UI Column component."""
    return {
        "id": id,
        "component": {
            "Column": {
                "children": {"explicitList": children}
            }
        }
    }


def build_row_component(
    id: str,
    children: list[str],
    alignment: str = "center",
) -> dict:
    """Build A2UI Row component."""
    return {
        "id": id,
        "component": {
            "Row": {
                "alignment": alignment,
                "children": {"explicitList": children}
            }
        }
    }


def build_card_component(id: str, child: str) -> dict:
    """Build A2UI Card component."""
    return {
        "id": id,
        "component": {
            "Card": {
                "child": child
            }
        }
    }


# ============================================================================
# Custom Component Builders (for our catalog)
# ============================================================================

def build_summary_card(
    prediction: PredictionResult,
    location: ResolvedLocation,
) -> list[dict]:
    """Build SummaryCard A2UI component."""
    takeaway = _generate_takeaway(prediction, location)
    
    components = [
        {
            "id": "summary_card",
            "component": {
                "SummaryCard": {
                    "location": _literal_string(location.display_name),
                    "p50": _literal_number(prediction.p50),
                    "p10": _literal_number(prediction.p10),
                    "p90": _literal_number(prediction.p90),
                    "unit": _literal_string(prediction.unit),
                    "horizon_months": _literal_number(prediction.horizon_months),
                    "takeaway": _literal_string(takeaway),
                }
            }
        }
    ]
    return components


def _generate_takeaway(prediction: PredictionResult, location: ResolvedLocation) -> str:
    """Generate takeaway text for summary."""
    spread_pct = ((prediction.p90 - prediction.p10) / prediction.p50) * 100
    
    if spread_pct < 20:
        confidence = "high confidence"
    elif spread_pct < 35:
        confidence = "moderate confidence"
    else:
        confidence = "wider uncertainty"
    
    return (
        f"Expected rent in {location.display_name} is £{prediction.p50:,.0f}/month "
        f"with {confidence} (range: £{prediction.p10:,.0f} - £{prediction.p90:,.0f})."
    )


def build_forecast_chart(
    prediction: PredictionResult,
    location: ResolvedLocation,
) -> list[dict]:
    """Build RentForecastChart A2UI component."""
    # Generate historical data (mock for demo)
    historical = _generate_mock_historical(prediction)
    
    # Generate forecast data
    forecast = _generate_forecast_points(prediction)
    
    return [
        {
            "id": "forecast_chart",
            "component": {
                "RentForecastChart": {
                    "location": _literal_string(location.display_name),
                    "unit": _literal_string(prediction.unit),
                    "historicalPath": _data_path("/chart/historical"),
                    "forecastPath": _data_path("/chart/forecast"),
                }
            }
        }
    ]


def _generate_mock_historical(prediction: PredictionResult) -> list[dict]:
    """Generate mock historical data."""
    today = datetime.now()
    base_rent = prediction.p50 * 0.95  # Start slightly lower
    
    historical = []
    for i in range(6, 0, -1):
        date = today - timedelta(days=30 * i)
        # Slight upward trend
        rent = base_rent * (1 + (6 - i) * 0.01)
        historical.append({
            "date": date.strftime("%Y-%m-%d"),
            "rent": round(rent, 0),
        })
    
    return historical


def _generate_forecast_points(prediction: PredictionResult) -> list[dict]:
    """Generate forecast data points."""
    today = datetime.now()
    
    forecast = []
    for i in range(prediction.horizon_months + 1):
        date = today + timedelta(days=30 * i)
        
        # Interpolate from current to final prediction
        progress = i / max(prediction.horizon_months, 1)
        
        # Start closer to current, end at prediction
        start_p50 = prediction.p50 * 0.98
        p50 = start_p50 + (prediction.p50 - start_p50) * progress
        
        start_p10 = prediction.p10 * 0.98
        p10 = start_p10 + (prediction.p10 - start_p10) * progress
        
        start_p90 = prediction.p90 * 0.98
        p90 = start_p90 + (prediction.p90 - start_p90) * progress
        
        forecast.append({
            "date": date.strftime("%Y-%m-%d"),
            "p10": round(p10, 0),
            "p50": round(p50, 0),
            "p90": round(p90, 0),
        })
    
    return forecast


def build_neighbor_map(
    location: ResolvedLocation,
    neighbors: list[Neighbor],
) -> list[dict]:
    """Build NeighbourHeatmapMap A2UI component."""
    return [
        {
            "id": "neighbor_map",
            "component": {
                "NeighbourHeatmapMap": {
                    "centerLat": _literal_number(location.lat or 51.5),
                    "centerLon": _literal_number(location.lon or -0.1),
                    "selectedAreaCode": _literal_string(location.area_code),
                    "neighborsPath": _data_path("/map/neighbors"),
                }
            }
        }
    ]


def build_drivers_bar(explanation: ExplanationResult) -> list[dict]:
    """Build DriversBar A2UI component."""
    return [
        {
            "id": "drivers_bar",
            "component": {
                "DriversBar": {
                    "driversPath": _data_path("/explanation/drivers"),
                    "baseValue": _literal_number(explanation.base_value or 2000),
                }
            }
        }
    ]


def build_what_if_controls(
    current_horizon: int = 6,
    current_k_neighbors: int = 5,
) -> list[dict]:
    """Build WhatIfControls A2UI component."""
    return [
        {
            "id": "what_if_controls",
            "component": {
                "WhatIfControls": {
                    "horizonOptions": _literal_string("1,3,6,12"),
                    "currentHorizon": _literal_number(current_horizon),
                    "kNeighborsOptions": _literal_string("3,5,7,10"),
                    "currentKNeighbors": _literal_number(current_k_neighbors),
                }
            }
        }
    ]


def build_carbon_card(
    location: str,
    current_emissions: float,
    potential_emissions: float,
    emissions_metric: str,
    energy_rating: str,
    potential_rating: str,
    property_size: float,
    property_type: str,
    current_consumption: float,
    potential_consumption: float,
    consumption_metric: str,
    current_energy_cost: float,
    potential_energy_cost: float,
    currency: str,
    environmental_score: int,
    potential_environmental_score: int,
    efficiency_features: list[str],
    embodied_carbon_total: float,
    embodied_carbon_per_m2: float,
    embodied_carbon_annual: float,
    embodied_carbon_a1_a3: float,
    embodied_carbon_a4: float,
    embodied_carbon_a5: float,
) -> list[dict]:
    """Build CarbonCard A2UI component for sustainability assessment."""
    messages = []
    
    # Build carbon card component
    carbon_component = {
        "id": "carbon_card",
        "component": {
            "CarbonCard": {
                "location": _literal_string(location),
                "currentEmissions": _literal_number(current_emissions),
                "potentialEmissions": _literal_number(potential_emissions),
                "emissionsMetric": _literal_string(emissions_metric),
                "energyRating": _literal_string(energy_rating),
                "potentialRating": _literal_string(potential_rating),
                "propertySize": _literal_number(property_size),
                "propertyType": _literal_string(property_type),
                "currentConsumption": _literal_number(current_consumption),
                "potentialConsumption": _literal_number(potential_consumption),
                "consumptionMetric": _literal_string(consumption_metric),
                "currentEnergyCost": _literal_number(current_energy_cost),
                "potentialEnergyCost": _literal_number(potential_energy_cost),
                "currency": _literal_string(currency),
                "environmentalScore": _literal_number(environmental_score),
                "potentialEnvironmentalScore": _literal_number(potential_environmental_score),
                "efficiencyFeatures": _literal_string(", ".join(efficiency_features) if efficiency_features else "Standard efficiency"),
                "embodiedCarbonTotal": _literal_number(embodied_carbon_total),
                "embodiedCarbonPerM2": _literal_number(embodied_carbon_per_m2),
                "embodiedCarbonAnnual": _literal_number(embodied_carbon_annual),
                "embodiedCarbonA1A3": _literal_number(embodied_carbon_a1_a3),
                "embodiedCarbonA4": _literal_number(embodied_carbon_a4),
                "embodiedCarbonA5": _literal_number(embodied_carbon_a5),
            }
        }
    }
    
    # Surface update with carbon component
    messages.append(build_surface_update([carbon_component]))
    
    # Begin rendering (if needed)
    messages.append(build_begin_rendering("carbon_card"))
    
    return messages


# ============================================================================
# Message Builders
# ============================================================================

def build_surface_update(
    components: list[dict],
    surface_id: str = "main",
) -> dict:
    """Build surfaceUpdate message."""
    return {
        "surfaceUpdate": {
            "surfaceId": surface_id,
            "components": components,
        }
    }


def build_data_model_update(
    contents: list[dict],
    path: Optional[str] = None,
    surface_id: str = "main",
) -> dict:
    """Build dataModelUpdate message."""
    update = {
        "dataModelUpdate": {
            "surfaceId": surface_id,
            "contents": contents,
        }
    }
    if path:
        update["dataModelUpdate"]["path"] = path
    return update


def build_begin_rendering(
    root_id: str,
    surface_id: str = "main",
    catalog_id: Optional[str] = None,
) -> dict:
    """Build beginRendering message."""
    msg = {
        "beginRendering": {
            "surfaceId": surface_id,
            "root": root_id,
        }
    }
    if catalog_id:
        msg["beginRendering"]["catalogId"] = catalog_id
    return msg


# ============================================================================
# Full UI Builder
# ============================================================================

def build_complete_ui(
    prediction: PredictionResult,
    explanation: ExplanationResult,
    location: ResolvedLocation,
    neighbors: list[Neighbor],
    horizon_months: int = 6,
    k_neighbors: int = 5,
) -> list[dict]:
    """
    Build complete A2UI message sequence for rental valuation.
    
    Returns list of JSONL messages to stream.
    """
    messages = []
    
    # Build all components
    all_components = []
    
    # Root layout
    all_components.append(build_column_component("root", [
        "summary_card",
        "forecast_chart",
        "content_row",
    ]))
    
    # Content row with map and drivers
    all_components.append(build_row_component("content_row", [
        "neighbor_map",
        "drivers_bar",
    ]))
    
    # Add custom components
    all_components.extend(build_summary_card(prediction, location))
    all_components.extend(build_forecast_chart(prediction, location))
    all_components.extend(build_neighbor_map(location, neighbors))
    all_components.extend(build_drivers_bar(explanation))
    all_components.extend(build_what_if_controls(horizon_months, k_neighbors))
    
    # Surface update with all components
    messages.append(build_surface_update(all_components))
    
    # Data model updates
    # Chart data
    historical = _generate_mock_historical(prediction)
    forecast = _generate_forecast_points(prediction)
    
    messages.append(build_data_model_update([
        {"key": "historical", "valueArray": historical},
    ], path="/chart"))
    
    messages.append(build_data_model_update([
        {"key": "forecast", "valueArray": forecast},
    ], path="/chart"))
    
    # Map data
    neighbor_data = [
        {
            "area_code": n.area_code,
            "display_name": n.display_name,
            "lat": n.lat,
            "lon": n.lon,
            "avg_rent": n.avg_rent,
            "demand_index": n.demand_index,
        }
        for n in neighbors
    ]
    
    messages.append(build_data_model_update([
        {"key": "neighbors", "valueArray": neighbor_data},
    ], path="/map"))
    
    # Explanation data
    driver_data = [
        {
            "name": d.name,
            "contribution": d.contribution,
            "direction": d.direction,
        }
        for d in explanation.drivers
    ]
    
    messages.append(build_data_model_update([
        {"key": "drivers", "valueArray": driver_data},
    ], path="/explanation"))
    
    # Begin rendering
    messages.append(build_begin_rendering("root"))
    
    return messages


def messages_to_jsonl(messages: list[dict]) -> str:
    """Convert messages to JSONL string."""
    return "\n".join(json.dumps(m) for m in messages)
