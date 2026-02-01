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


def build_card_component(
    card_id: str,
    title: str,
    items: list[dict],
    variant: str = "default",
) -> dict:
    """
    Build a generic card component for displaying key-value pairs.
    
    Args:
        card_id: Unique ID for the card
        title: Card title
        items: List of dicts with 'label', 'value', and optional 'highlight' keys
        variant: Card style variant (default, primary, success, destructive)
    
    Returns:
        A2UI component dict
    """
    # Build text component with structured content
    # Format as a clean table-like display
    content_lines = [f"**{title}**", ""]
    
    for item in items:
        label = item.get("label", "")
        value = item.get("value", "")
        highlight = item.get("highlight", False)
        
        if highlight:
            content_lines.append(f"**{label}:** *{value}*")
        else:
            content_lines.append(f"{label}: {value}")
    
    content = "\n".join(content_lines)
    
    component = {
        "Text": {
            "text": _literal_string(content),
            "usageHint": "body"
        }
    }
    
    return {"id": card_id, "component": component}


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


# ============================================================================
# Location Comparison (Area Summary) UI
# ============================================================================

def build_location_comparison_ui(
    areas: list[dict],
    winners: dict,
) -> list[dict]:
    """
    Build A2UI message sequence for comparing 2-3 locations using ScanSan area summary.

    DataModel paths:
    - /comparison/areas: list of normalized area summary objects
    - /comparison/winners: computed "best" area per metric
    """
    messages: list[dict] = []
    components: list[dict] = []

    # Root layout for comparison tab
    components.append(build_column_component("comparison_root", [
        "comparison_summary",
        "comparison_ranges",
        "comparison_listings",
    ]))

    components.append({
        "id": "comparison_summary",
        "component": {
            "LocationComparisonSummaryCard": {
                "areasPath": _data_path("/comparison/areas"),
                "winnersPath": _data_path("/comparison/winners"),
            }
        }
    })

    components.append({
        "id": "comparison_ranges",
        "component": {
            "LocationComparisonRanges": {
                "areasPath": _data_path("/comparison/areas"),
            }
        }
    })

    components.append({
        "id": "comparison_listings",
        "component": {
            "LocationComparisonListings": {
                "areasPath": _data_path("/comparison/areas"),
            }
        }
    })

    messages.append(build_surface_update(components))

    messages.append(build_data_model_update(
        [{"key": "areas", "valueArray": areas}],
        path="/comparison",
    ))
    messages.append(build_data_model_update(
        [{"key": "winners", "valueMap": winners}],
        path="/comparison",
    ))

    messages.append(build_begin_rendering("comparison_root"))

    return messages


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
    
    # Data model update for carbon data
    messages.append(build_data_model_update([
        {"key": "location", "valueString": location},
        {"key": "current_emissions", "valueNumber": current_emissions},
        {"key": "potential_emissions", "valueNumber": potential_emissions},
        {"key": "emissions_metric", "valueString": emissions_metric},
        {"key": "energy_rating", "valueString": energy_rating},
        {"key": "potential_rating", "valueString": potential_rating},
        {"key": "property_size", "valueNumber": property_size},
        {"key": "property_type", "valueString": property_type},
        {"key": "current_consumption", "valueNumber": current_consumption},
        {"key": "potential_consumption", "valueNumber": potential_consumption},
        {"key": "consumption_metric", "valueString": consumption_metric},
        {"key": "current_energy_cost", "valueNumber": current_energy_cost},
        {"key": "potential_energy_cost", "valueNumber": potential_energy_cost},
        {"key": "currency", "valueString": currency},
        {"key": "environmental_score", "valueNumber": environmental_score},
        {"key": "potential_environmental_score", "valueNumber": potential_environmental_score},
        {"key": "efficiency_features", "valueString": ", ".join(efficiency_features) if efficiency_features else "Standard efficiency"},
        {"key": "embodied_carbon_total", "valueNumber": embodied_carbon_total},
        {"key": "embodied_carbon_per_m2", "valueNumber": embodied_carbon_per_m2},
        {"key": "embodied_carbon_annual", "valueNumber": embodied_carbon_annual},
        {"key": "embodied_carbon_a1_a3", "valueNumber": embodied_carbon_a1_a3},
        {"key": "embodied_carbon_a4", "valueNumber": embodied_carbon_a4},
        {"key": "embodied_carbon_a5", "valueNumber": embodied_carbon_a5},
    ], path="/carbon"))
    
    # Build carbon card component
    carbon_component = {
        "id": "carbon_card",
        "component": {
            "CarbonCard": {
                "location": _data_path("carbon/location"),
                "currentEmissions": _data_path("carbon/current_emissions"),
                "potentialEmissions": _data_path("carbon/potential_emissions"),
                "emissionsMetric": _data_path("carbon/emissions_metric"),
                "energyRating": _data_path("carbon/energy_rating"),
                "potentialRating": _data_path("carbon/potential_rating"),
                "propertySize": _data_path("carbon/property_size"),
                "propertyType": _data_path("carbon/property_type"),
                "currentConsumption": _data_path("carbon/current_consumption"),
                "potentialConsumption": _data_path("carbon/potential_consumption"),
                "consumptionMetric": _data_path("carbon/consumption_metric"),
                "currentEnergyCost": _data_path("carbon/current_energy_cost"),
                "potentialEnergyCost": _data_path("carbon/potential_energy_cost"),
                "currency": _data_path("carbon/currency"),
                "environmentalScore": _data_path("carbon/environmental_score"),
                "potentialEnvironmentalScore": _data_path("carbon/potential_environmental_score"),
                "efficiencyFeatures": _data_path("carbon/efficiency_features"),
                "embodiedCarbonTotal": _data_path("carbon/embodied_carbon_total"),
                "embodiedCarbonPerM2": _data_path("carbon/embodied_carbon_per_m2"),
                "embodiedCarbonAnnual": _data_path("carbon/embodied_carbon_annual"),
                "embodiedCarbonA1A3": _data_path("carbon/embodied_carbon_a1_a3"),
                "embodiedCarbonA4": _data_path("carbon/embodied_carbon_a4"),
                "embodiedCarbonA5": _data_path("carbon/embodied_carbon_a5"),
            }
        }
    }
    
    # Surface update with carbon component
    messages.append(build_surface_update([carbon_component]))
    
    # Begin rendering
    messages.append(build_begin_rendering("carbon_card"))
    
    print(f"[CARBON A2UI] Returning {len(messages)} messages:")
    for i, msg in enumerate(messages):
        print(f"[CARBON A2UI]   Message {i}: {list(msg.keys())}")
    
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
    
    # Prediction data for auto-switching and investment calculator
    messages.append(build_data_model_update([
        {"key": "p50", "valueNumber": prediction.p50},
        {"key": "p10", "valueNumber": prediction.p10},
        {"key": "p90", "valueNumber": prediction.p90},
    ], path="/prediction"))
    
    # Location data
    messages.append(build_data_model_update([
        {"key": "location", "valueString": location.display_name or location.area_code},
    ], path="/"))
    
    # Begin rendering
    messages.append(build_begin_rendering("root"))
    
    return messages


def messages_to_jsonl(messages: list[dict]) -> str:
    """Convert messages to JSONL string."""
    return "\n".join(json.dumps(m) for m in messages)


def build_listings_cards(
    rent_listings: list[dict],
    sale_listings: list[dict],
    amenities_by_postcode: Optional[dict],
    location: str,
) -> list[dict]:
    """
    Build A2UI messages for property listings with amenities.
    
    Args:
        rent_listings: List of rent listing dicts from ScanSan API
        sale_listings: List of sale listing dicts from ScanSan API
        amenities_by_postcode: Optional dict mapping postcodes to amenity lists
        location: Location name/description
        
    Returns:
        List of A2UI messages
    """
    messages = []
    all_components = []
    
    # Combine all listings
    all_listings = []
    
    # Log first listing to see available fields
    if rent_listings and len(rent_listings) > 0:
        print(f"[A2UI] Sample rent listing fields: {list(rent_listings[0].keys())}")
        print(f"[A2UI] Sample rent listing data: {rent_listings[0]}")
    if sale_listings and len(sale_listings) > 0:
        print(f"[A2UI] Sample sale listing fields: {list(sale_listings[0].keys())}")
        print(f"[A2UI] Sample sale listing data: {sale_listings[0]}")
    
    for listing in rent_listings:
        postcode = listing.get("area_code", "")
        property_amenities = []
        
        # Get amenities for this specific property's postcode
        if amenities_by_postcode and postcode in amenities_by_postcode:
            property_amenities = amenities_by_postcode[postcode]
        
        # Get URL from listing data (listing_url field from ScanSan API)
        url = listing.get("listing_url") or "#"
        
        # Extract location - try to find postcode in street address or use area name
        street_address = listing.get("street_address", "Unknown Address")
        # UK postcode pattern at end of string
        import re
        postcode_match = re.search(r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b', street_address)
        if postcode_match:
            display_location = postcode_match.group(1)
        else:
            # Use the area name passed to this function instead of district code
            display_location = location
        
        # Get URL from listing data (listing_url field from ScanSan API)
        url = listing.get("listing_url") or "#"
        
        # Get property size and convert to sqft if needed
        property_size = listing.get("property_size")
        size_metric = listing.get("property_size_metric")
        sqft = 0
        
        if property_size:
            try:
                # Convert string to float
                size_value = float(property_size)
                
                if size_metric == "sqm" or size_metric == "sq_m":
                    # Convert square meters to square feet (1 sqm = 10.764 sqft)
                    sqft = int(size_value * 10.764)
                elif size_metric == "sqft" or size_metric == "sq_ft":
                    sqft = int(size_value)
                else:
                    # Assume sqft if no metric specified
                    sqft = int(size_value)
            except (ValueError, TypeError):
                sqft = 0
        
        all_listings.append({
            "id": f"rent_{listing.get('street_address', '')}_{listing.get('rent_pcm', 0)}",
            "title": street_address,
            "price": listing.get("rent_pcm", 0),
            "type": "rent",
            "location": display_location,
            "beds": listing.get("bedrooms", 0) or 0,
            "baths": listing.get("bathrooms", 0) or 0,
            "sqft": sqft,
            "url": url,
            "amenities": property_amenities,
        })
    
    for listing in sale_listings:
        postcode = listing.get("area_code", "")
        property_amenities = []
        
        # Get amenities for this specific property's postcode
        if amenities_by_postcode and postcode in amenities_by_postcode:
            property_amenities = amenities_by_postcode[postcode]
        
        # Get URL from listing data (listing_url field from ScanSan API)
        url = listing.get("listing_url") or "#"
        
        # Extract location - try to find postcode in street address or use area name
        street_address = listing.get("street_address", "Unknown Address")
        # UK postcode pattern at end of string
        import re
        postcode_match = re.search(r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b', street_address)
        if postcode_match:
            display_location = postcode_match.group(1)
        else:
            # Use the area name passed to this function instead of district code
            display_location = location
        
        # Get URL from listing data (listing_url field from ScanSan API)
        url = listing.get("listing_url") or "#"
        
        # Get property size and convert to sqft if needed
        property_size = listing.get("property_size")
        size_metric = listing.get("property_size_metric")
        sqft = 0
        
        if property_size:
            try:
                # Convert string to float
                size_value = float(property_size)
                
                if size_metric == "sqm" or size_metric == "sq_m":
                    # Convert square meters to square feet (1 sqm = 10.764 sqft)
                    sqft = int(size_value * 10.764)
                elif size_metric == "sqft" or size_metric == "sq_ft":
                    sqft = int(size_value)
                else:
                    # Assume sqft if no metric specified
                    sqft = int(size_value)
            except (ValueError, TypeError):
                sqft = 0
        
        all_listings.append({
            "id": f"sale_{listing.get('street_address', '')}_{listing.get('sale_price', 0)}",
            "title": street_address,
            "price": listing.get("sale_price", 0),
            "type": "sale",
            "location": display_location,
            "beds": listing.get("bedrooms", 0) or 0,
            "baths": listing.get("bathrooms", 0) or 0,
            "sqft": sqft,
            "url": url,
            "amenities": property_amenities,
        })
    
    # Build header
    all_components.append(build_text_component(
        "listings_header",
        f"Property Listings in {location}",
        usage_hint="heading1"
    ))
    
    # Build detailed summary text
    rent_count = len(rent_listings)
    sale_count = len(sale_listings)
    total_count = rent_count + sale_count
    
    summary_parts = []
    if rent_count > 0:
        summary_parts.append(f"**{rent_count}** {'property' if rent_count == 1 else 'properties'} available for rent")
    if sale_count > 0:
        summary_parts.append(f"**{sale_count}** {'property' if sale_count == 1 else 'properties'} for sale")
    
    summary_text = f"I found {summary_parts[0]}"
    if len(summary_parts) == 2:
        summary_text = f"I found {summary_parts[0]} and {summary_parts[1]}"
    summary_text += f" in {location}."
    
    if amenities_by_postcode:
        summary_text += " Each property listing includes nearby amenities such as schools, transport, and shops."
    
    all_components.append(build_text_component(
        "listings_summary",
        summary_text,
        usage_hint="body"
    ))
    
    # Surface update with components
    messages.append(build_surface_update(all_components))
    
    # Data model updates for listings (amenities are now embedded in each property)
    messages.append(build_data_model_update([
        {"key": "properties", "valueArray": all_listings},
    ], path="/listings"))
    
    # Begin rendering
    messages.append(build_begin_rendering("root"))
    
    return messages

