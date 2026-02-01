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
from ..a2ui_builder import build_complete_ui, build_listings_cards
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


@dataclass
class EmbodiedCarbonResult:
    """Result from embodied carbon calculation."""
    success: bool
    location: str
    current_emissions: Optional[float]
    potential_emissions: Optional[float]
    emissions_metric: Optional[str]
    energy_rating: Optional[str]
    property_size: Optional[float]
    property_type: Optional[str]
    recommendations: list[dict]
    a2ui_messages: list[dict]
    summary: str


@dataclass
class PropertyListingsResult:
    """Result from property listings search."""
    success: bool
    location: str
    area_code: str
    rent_listings: list[dict]
    sale_listings: list[dict]
    amenities: Optional[dict]
    a2ui_messages: list[dict]
    summary: str


@dataclass
class InvestmentAnalysisResult:
    """Result from investment analysis."""
    success: bool
    location: str
    property_value: float
    predicted_rent_pcm: float
    rental_yield: float
    gross_yield: float
    net_yield: float
    monthly_mortgage: float
    monthly_costs: float
    monthly_cash_flow: float
    annual_roi: float
    break_even_years: float
    total_investment: float
    market_metrics: dict
    a2ui_messages: list[dict]
    summary: str


# Tool definitions for the LLM (OpenAI function calling format)
TOOL_DEFINITIONS = [
    {
        "name": "get_rent_forecast",
        "description": "Get rental price prediction and forecast for a UK location. Returns P10/P50/P90 values, market drivers, and visual charts. ALWAYS use this when user asks about: expected rent, rental prices, rent forecast, how much rent costs, what rent should be, rent predictions, rental valuation, or 'how much for a X bedroom in Y'. This is the PRIMARY tool for any rent-related questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to forecast rent for. Can be a UK postcode (e.g., 'NW1', 'E14', 'SW1A 2TL'), area name (e.g., 'Camden', 'Canary Wharf'), or district."
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
        "description": "ONLY use to resolve ambiguous or unknown locations. Most UK postcodes can be used directly in other tools without searching first.",
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
    },
    {
        "name": "get_embodied_carbon",
        "description": "Calculate embodied carbon emissions for a property at a given location. Uses ScanSan API to fetch property details including energy performance data and calculates carbon footprint. Use this when the user asks about carbon emissions, environmental impact, or sustainability of a property.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get carbon data for. Can be a UK postcode (e.g., 'NW1 2BU', 'E14 5AB') or UPRN (Unique Property Reference Number)."
                },
                "property_type": {
                    "type": "string",
                    "description": "Type of property (flat, house, studio). Optional if UPRN is provided.",
                    "enum": ["flat", "house", "studio"],
                    "default": "flat"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "get_property_listings",
        "description": "Get property listings (for rent and/or sale) in a specific area along with nearby amenities. Use this when the user asks about available properties, listings, what's for rent/sale, or properties in an area.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to search for properties. Can be a UK postcode district (e.g., 'NW1', 'E14') or area name."
                },
                "listing_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["rent", "sale"]
                    },
                    "description": "Types of listings to fetch. Default is both rent and sale.",
                    "default": ["rent", "sale"]
                },
                "include_amenities": {
                    "type": "boolean",
                    "description": "Whether to include nearby amenities. Default is true.",
                    "default": True
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "get_investment_analysis",
        "description": "Calculate comprehensive investment analysis including ROI, rental yield, cash flow projections, and market metrics. Use when user asks about investment potential, ROI, returns, rental yield, or buying a property.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to analyze. Can be a UK postcode or area name."
                },
                "property_value": {
                    "type": "number",
                    "description": "The purchase price of the property in GBP. Optional - if not provided, will use market average."
                },
                "deposit_percent": {
                    "type": "number",
                    "description": "Deposit percentage (default 25%).",
                    "default": 25
                },
                "mortgage_rate": {
                    "type": "number",
                    "description": "Annual mortgage interest rate percentage (default 4.5%).",
                    "default": 4.5
                },
                "mortgage_years": {
                    "type": "number",
                    "description": "Mortgage term in years (default 25).",
                    "default": 25
                }
            },
            "required": ["location"]
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
        f"{area_name} {horizon_months}mo forecast: "
        f"£{prediction.p50:,.0f} (P10: £{prediction.p10:,.0f}, P90: £{prediction.p90:,.0f})"
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


async def execute_get_embodied_carbon(
    location: str,
    property_type: str = "flat",
) -> EmbodiedCarbonResult:
    """
    Execute the embodied carbon calculation tool.
    
    This fetches property energy performance data from ScanSan API
    and calculates embodied carbon emissions.
    
    Args:
        location: Location string (postcode or UPRN)
        property_type: Type of property (flat, house, studio)
        
    Returns:
        EmbodiedCarbonResult with carbon data and UI components
    """
    from ..a2ui_builder import build_carbon_card
    
    client = get_scansan_client()
    
    try:
        # Get real data from ScanSan API (no fallback to mock)
        energy_data = None
        uprn = None
        
        # Check if location is a UPRN (numeric) or postcode
        if location.replace(" ", "").isdigit():
            # It's a UPRN
            uprn = location
            print(f"\n[CARBON] Fetching energy performance for UPRN: {uprn}")
            energy_data = await client.get_property_energy_performance(uprn)
        else:
            # It's a postcode - try direct postcode endpoint first (simpler)
            print(f"\n[CARBON] Fetching energy performance for postcode: {location}")
            energy_data = await client.get_postcode_energy_performance(location)
            
            # If that fails, try the UPRN lookup method
            if not energy_data:
                print(f"[CARBON] Direct postcode lookup failed, trying UPRN lookup...")
                uprn = await client.get_uprn_from_postcode(location)
                print(f"[CARBON] Found UPRN: {uprn}")
                
                if uprn:
                    print(f"[CARBON] Fetching energy performance for UPRN: {uprn}")
                    energy_data = await client.get_property_energy_performance(uprn)
                else:
                    raise ValueError(f"Could not find UPRN for postcode: {location}")
        
        # Debug: Print what we got from the API
        print(f"\n[CARBON] Energy Performance Data Response:")
        print(f"[CARBON] {'='*60}")
        if energy_data:
            import json
            print(json.dumps(energy_data, indent=2))
        else:
            print("[CARBON] No data returned from API")
        print(f"[CARBON] {'='*60}\n")
        
        # Process real data - fail if not available
        if not energy_data:
            raise ValueError(f"No energy performance data returned from ScanSan API for UPRN: {uprn}")
        
        if "annual_CO2_emissions" in energy_data:
            # Real ScanSan data
            property_address = energy_data.get("property_address", location)
            property_size = energy_data.get("property_size", 75)
            property_size_metric = energy_data.get("property_size_metric", "sqm")
            
            epc_data = energy_data.get("EPC", {})
            energy_rating = epc_data.get("current_rating", "C")
            
            co2_data = energy_data.get("annual_CO2_emissions", {})
            current_emissions = co2_data.get("current_emissions", 1.8)
            potential_emissions = co2_data.get("potential_emissions", 1.2)
            emissions_metric = co2_data.get("emissions_metric", "tonnes CO2/year")
            
            # Get recommendations from API
            savings_data = energy_data.get("savings_and_recommendations", {})
            api_recommendations = savings_data.get("energy_saving_recommendations", [])
            
            recommendations = []
            for rec in api_recommendations[:5]:  # Limit to top 5
                rec_text = rec.get("recommendations", "")
                min_cost = rec.get("min_installation_cost", 0)
                max_cost = rec.get("max_installation_cost", 0)
                
                # Estimate carbon reduction (simplified calculation)
                # Assuming each recommendation contributes proportionally to potential savings
                total_reduction = current_emissions - potential_emissions
                estimated_reduction = total_reduction / max(len(api_recommendations), 1)
                
                cost_str = f"£{min_cost:,}" if min_cost == max_cost else f"£{min_cost:,} - £{max_cost:,}"
                
                recommendations.append({
                    "recommendation": rec_text,
                    "potential_reduction": round(estimated_reduction, 2),
                    "cost_estimate": cost_str,
                })
            
            # Infer property type from API data if available
            api_property_type = energy_data.get("property_type", property_type)
            if api_property_type:
                property_type = api_property_type.lower()
            
            print(f"[CARBON] Processed data successfully:")
            print(f"[CARBON]   - Current emissions: {current_emissions} {emissions_metric}")
            print(f"[CARBON]   - Potential emissions: {potential_emissions} {emissions_metric}")
            print(f"[CARBON]   - EPC rating: {energy_rating}")
            print(f"[CARBON]   - Recommendations: {len(recommendations)}")
        
        else:
            # No CO2 emissions data in response - this is required
            raise ValueError(
                f"Energy performance data for UPRN {uprn} does not contain CO2 emissions data. "
                f"Available fields: {list(energy_data.keys())}"
            )
        
        # Validate data
        if current_emissions is None or current_emissions <= 0:
            raise ValueError("Invalid current emissions data")
        
        if potential_emissions is None or potential_emissions < 0:
            potential_emissions = current_emissions * 0.7  # Assume 30% reduction potential
        
        # Build A2UI messages
        a2ui_messages = build_carbon_card(
            location=property_address,
            current_emissions=current_emissions,
            potential_emissions=potential_emissions,
            emissions_metric=emissions_metric,
            energy_rating=energy_rating,
            property_size=property_size,
            property_type=property_type,
            recommendations=recommendations,
        )
        
        # Generate summary
        reduction_percent = ((current_emissions - potential_emissions) / current_emissions) * 100
        summary = (
            f"For {property_address}, the property currently emits {current_emissions:.1f} tonnes of CO2 per year "
            f"with an EPC rating of {energy_rating}. "
            f"With recommended improvements, emissions could be reduced to {potential_emissions:.1f} tonnes/year "
            f"(a {reduction_percent:.0f}% reduction). "
        )
        
        if recommendations:
            summary += f"Top recommendations include: {', '.join([r['recommendation'] for r in recommendations[:2]])}."
        
        return EmbodiedCarbonResult(
            success=True,
            location=property_address,
            current_emissions=current_emissions,
            potential_emissions=potential_emissions,
            emissions_metric=emissions_metric,
            energy_rating=energy_rating,
            property_size=property_size,
            property_type=property_type,
            recommendations=recommendations,
            a2ui_messages=a2ui_messages,
            summary=summary,
        )
        
    except ValueError as e:
        # Data validation error
        return EmbodiedCarbonResult(
            success=False,
            location=location,
            current_emissions=None,
            potential_emissions=None,
            emissions_metric=None,
            energy_rating=None,
            property_size=None,
            property_type=property_type,
            recommendations=[],
            a2ui_messages=[],
            summary=f"Invalid data for {location}: {str(e)}. Please try a different property or postcode.",
        )
    
    except Exception as e:
        # General error - provide helpful message
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            summary = f"No energy performance data found for {location}. This property may not have an EPC certificate on record."
        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            summary = f"Unable to connect to property database for {location}. Please try again later."
        else:
            summary = f"Error calculating embodied carbon for {location}: {error_msg}"
        
        return EmbodiedCarbonResult(
            success=False,
            location=location,
            current_emissions=None,
            potential_emissions=None,
            emissions_metric=None,
            energy_rating=None,
            property_size=None,
            property_type=property_type,
            recommendations=[],
            a2ui_messages=[],
            summary=summary,
        )


async def execute_get_property_listings(
    location: str,
    listing_types: list[str] = None,
    include_amenities: bool = True,
) -> PropertyListingsResult:
    """
    Execute the property listings tool.
    
    Fetches rent and/or sale listings for an area and optionally includes
    nearby amenities information.
    
    Args:
        location: Location string (postcode district or area name)
        listing_types: List of listing types to fetch ("rent" and/or "sale")
        include_amenities: Whether to fetch nearby amenities
        
    Returns:
        PropertyListingsResult with listings and amenities data
    """
    from ..a2ui_builder import build_listings_cards
    
    if listing_types is None:
        listing_types = ["rent", "sale"]
    
    client = get_scansan_client()
    
    try:
        # Resolve location to area code
        resolved_location = await client.search_area_codes(location)
        
        if not resolved_location:
            raise ValueError(f"Could not find location: {location}")
        
        area_code = resolved_location.area_code_district or resolved_location.area_code
        
        # Fetch listings
        rent_listings = []
        sale_listings = []
        
        if "rent" in listing_types:
            print(f"[LISTINGS] Fetching rent listings for {area_code}")
            rent_data = await client.get_rent_listings(area_code)
            if rent_data and "data" in rent_data:
                rent_listings = rent_data["data"].get("rent_listings", [])
                print(f"[LISTINGS] Found {len(rent_listings)} rent listings")
        
        if "sale" in listing_types:
            print(f"[LISTINGS] Fetching sale listings for {area_code}")
            sale_data = await client.get_sale_listings(area_code)
            if sale_data and "data" in sale_data:
                sale_listings = sale_data["data"].get("sale_listings", [])
                print(f"[LISTINGS] Found {len(sale_listings)} sale listings")
        
        # Fetch amenities per property if requested
        amenities_by_postcode = {}
        if include_amenities:
            # Collect unique postcodes from all listings
            unique_postcodes = set()
            for listing in rent_listings:
                postcode = listing.get("area_code")
                if postcode:
                    unique_postcodes.add(postcode)
            for listing in sale_listings:
                postcode = listing.get("area_code")
                if postcode:
                    unique_postcodes.add(postcode)
            
            # Fetch amenities for each unique postcode (limit to first 5 to avoid too many requests)
            for postcode in list(unique_postcodes)[:5]:
                print(f"[LISTINGS] Fetching amenities for {postcode}")
                try:
                    amenities_data = await client.get_amenities(postcode)
                    if amenities_data and "data" in amenities_data:
                        # Process amenities into simple list
                        amenities_list = []
                        for amenity_group in amenities_data["data"]:
                            if isinstance(amenity_group, list):
                                for amenity in amenity_group:
                                    amenities_list.append({
                                        "type": amenity.get("amenity_type", "Unknown"),
                                        "name": amenity.get("name", "Unknown"),
                                        "distance": amenity.get("distance_miles", 0),
                                    })
                        amenities_by_postcode[postcode] = amenities_list[:10]  # Limit to 10 amenities per property
                        print(f"[LISTINGS] Found {len(amenities_list)} amenities for {postcode}")
                except Exception as e:
                    print(f"[LISTINGS] Error fetching amenities for {postcode}: {str(e)}")
        
        # Build A2UI messages (cards for listings)
        a2ui_messages = build_listings_cards(
            rent_listings=rent_listings,
            sale_listings=sale_listings,
            amenities_by_postcode=amenities_by_postcode,
            location=resolved_location.display_name or area_code,
        )
        
        # Generate summary
        total_listings = len(rent_listings) + len(sale_listings)
        summary_parts = []
        
        if rent_listings:
            summary_parts.append(f"{len(rent_listings)} properties for rent")
        if sale_listings:
            summary_parts.append(f"{len(sale_listings)} properties for sale")
        
        summary = f"{resolved_location.display_name or area_code}: "
        summary += " and ".join(summary_parts)
        
        return PropertyListingsResult(
            success=True,
            location=resolved_location.display_name or area_code,
            area_code=area_code,
            rent_listings=rent_listings,
            sale_listings=sale_listings,
            amenities=list(amenities_by_postcode.values())[0] if amenities_by_postcode else None,  # For backward compatibility
            a2ui_messages=a2ui_messages,
            summary=summary,
        )
        
    except Exception as e:
        print(f"[LISTINGS] Error: {str(e)}")
        return PropertyListingsResult(
            success=False,
            location=location,
            area_code="",
            rent_listings=[],
            sale_listings=[],
            amenities=None,
            a2ui_messages=[],
            summary=f"Error fetching property listings for {location}: {str(e)}",
        )


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
    
    elif tool_name == "get_embodied_carbon":
        result = await execute_get_embodied_carbon(
            location=arguments["location"],
            property_type=arguments.get("property_type", "flat"),
        )
        return {
            "success": result.success,
            "location": result.location,
            "current_emissions": result.current_emissions,
            "potential_emissions": result.potential_emissions,
            "emissions_metric": result.emissions_metric,
            "energy_rating": result.energy_rating,
            "property_size": result.property_size,
            "property_type": result.property_type,
            "recommendations": result.recommendations,
            "a2ui_messages": result.a2ui_messages,
            "summary": result.summary,
        }
    
    elif tool_name == "get_property_listings":
        result = await execute_get_property_listings(
            location=arguments["location"],
            listing_types=arguments.get("listing_types", ["rent", "sale"]),
            include_amenities=arguments.get("include_amenities", True),
        )
        return {
            "success": result.success,
            "location": result.location,
            "area_code": result.area_code,
            "rent_listings": result.rent_listings,
            "sale_listings": result.sale_listings,
            "amenities": result.amenities,
            "a2ui_messages": result.a2ui_messages,
            "summary": result.summary,
        }
    
    elif tool_name == "get_investment_analysis":
        from .investment import execute_get_investment_analysis
        result = await execute_get_investment_analysis(
            location=arguments["location"],
            property_value=arguments.get("property_value"),
            deposit_percent=arguments.get("deposit_percent", 25),
            mortgage_rate=arguments.get("mortgage_rate", 4.5),
            mortgage_years=arguments.get("mortgage_years", 25),
        )
        return {
            "success": result.success,
            "location": result.location,
            "property_value": result.property_value,
            "predicted_rent_pcm": result.predicted_rent_pcm,
            "rental_yield": result.rental_yield,
            "gross_yield": result.gross_yield,
            "net_yield": result.net_yield,
            "monthly_mortgage": result.monthly_mortgage,
            "monthly_costs": result.monthly_costs,
            "monthly_cash_flow": result.monthly_cash_flow,
            "annual_roi": result.annual_roi,
            "break_even_years": result.break_even_years,
            "total_investment": result.total_investment,
            "market_metrics": result.market_metrics,
            "a2ui_messages": result.a2ui_messages,
            "summary": result.summary,
        }
    
    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
