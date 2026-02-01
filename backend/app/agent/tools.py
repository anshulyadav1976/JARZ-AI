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


async def execute_get_embodied_carbon(
    location: str,
    property_type: str = "flat",
) -> EmbodiedCarbonResult:
    """
    Execute the embodied carbon calculation tool.
    
    This fetches property energy performance data from ScanSan API
    and calculates embodied carbon emissions.
    
    Args:
        location: Location string (postcode with optional house number, or UPRN)
        property_type: Type of property (flat, house, studio)
        
    Returns:
        EmbodiedCarbonResult with carbon data and UI components
    """
    from ..a2ui_builder import build_carbon_card
    import re
    
    client = get_scansan_client()
    
    try:
        # Get real data from ScanSan API (no fallback to mock)
        energy_data = None
        uprn = None
        
        # Check if location is a UPRN (numeric) or postcode
        if location.replace(" ", "").isdigit():
            # It's a UPRN
            uprn = location
            print(f"\n[CARBON] Using provided UPRN: {uprn}")
        else:
            # It's a postcode - get all addresses and match house number if provided
            print(f"\n[CARBON] Parsing location: {location}")
            
            # Extract house number from location string (e.g., "6 UB10 0GH" or "6, NICHOLSON WALK, UB10 0GH")
            house_number_match = re.search(r'^(\d+[\w]?)', location.strip())
            house_number = house_number_match.group(1) if house_number_match else None
            
            # Extract postcode (UK postcode format)
            postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})', location.upper())
            postcode = postcode_match.group(1) if postcode_match else location
            
            print(f"[CARBON] Extracted house number: {house_number}")
            print(f"[CARBON] Extracted postcode: {postcode}")
            
            # Get all addresses for this postcode
            addresses_data = await client.get_postcode_addresses(postcode)
            
            if not addresses_data or "data" not in addresses_data:
                raise ValueError(f"Could not find any properties for postcode: {postcode}")
            
            property_addresses = addresses_data["data"].get("property_address", [])
            
            if len(property_addresses) == 0:
                raise ValueError(f"No properties found for postcode: {postcode}")
            
            print(f"[CARBON] Found {len(property_addresses)} properties in {postcode}")
            
            # If house number provided, find matching property
            if house_number:
                print(f"[CARBON] Searching for house number: {house_number}")
                matched_property = None
                
                for prop in property_addresses:
                    prop_address = prop.get("property_address", "")
                    # Check if address starts with the house number
                    if prop_address.strip().startswith(house_number):
                        matched_property = prop
                        print(f"[CARBON] Matched property: {prop_address}")
                        break
                
                if matched_property:
                    uprn = str(matched_property.get("uprn"))
                    property_address = matched_property.get("property_address", location)
                else:
                    # House number not found - list available properties
                    available = "\n".join([f"  - {p.get('property_address', 'Unknown')}" for p in property_addresses[:10]])
                    raise ValueError(
                        f"Could not find property number '{house_number}' in {postcode}.\n\n"
                        f"Available properties:\n{available}\n\n"
                        f"Please specify the exact house number from the list above."
                    )
            else:
                # No house number provided - list all and ask user to specify
                available = "\n".join([f"  - {p.get('property_address', 'Unknown')}" for p in property_addresses[:10]])
                raise ValueError(
                    f"Multiple properties found in {postcode}. Please specify which property:\n\n"
                    f"{available}\n\n"
                    f"Example: 'What's the carbon footprint for 6 {postcode}?'"
                )
            
            print(f"[CARBON] Using UPRN: {uprn} for {property_address}")
        
        # Store the matched address before API call
        matched_address = property_address if 'property_address' in locals() else None
        
        # Now fetch energy performance data using the UPRN
        print(f"[CARBON] Fetching energy performance for UPRN: {uprn}")
        energy_data = await client.get_property_energy_performance(uprn)
        
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
            # Use matched address if we have it, otherwise use API address
            property_address = matched_address or energy_data.get("property_address", location)
            property_size = energy_data.get("property_size",0.0)
            property_size_metric = energy_data.get("property_size_metric", "sqm")
            
            epc_data = energy_data.get("EPC", {})
            energy_rating = epc_data.get("current_rating", "C")
            potential_rating = epc_data.get("potential_rating", "B")
            energy_score = epc_data.get("current_score", 0)
            potential_score = epc_data.get("potential_score", 0)
            
            co2_data = energy_data.get("annual_CO2_emissions", {})
            current_emissions = co2_data.get("current_emissions", 1.8)
            potential_emissions = co2_data.get("potential_emissions", 1.2)
            emissions_metric = co2_data.get("emissions_metric", "tonnes CO2/year")
            
            # Energy consumption data
            consumption_data = energy_data.get("energy_consumption", {})
            current_consumption = consumption_data.get("current_annual_energy_consumption", 0)
            potential_consumption = consumption_data.get("potential_annual_energy_consumption", 0)
            consumption_metric = consumption_data.get("energy_consumption_metric", "kWh/m2")
            
            # Energy costs
            costs_data = energy_data.get("annual_energy_costs", {})
            current_heating_cost = costs_data.get("current_annual_heating_cost", 0)
            potential_heating_cost = costs_data.get("potential_annual_heating_cost", 0)
            current_lighting_cost = costs_data.get("current_annual_lighting_cost", 0)
            potential_lighting_cost = costs_data.get("potential_annual_lighting_cost", 0)
            current_hotwater_cost = costs_data.get("current_annual_hot_water_cost", 0)
            potential_hotwater_cost = costs_data.get("potential_annual_hot_water_cost", 0)
            currency = costs_data.get("currency", "GBP")
            
            total_current_cost = current_heating_cost + current_lighting_cost + current_hotwater_cost
            total_potential_cost = potential_heating_cost + potential_lighting_cost + potential_hotwater_cost
            
            # Environmental impact score
            env_impact_data = energy_data.get("environmental_impact", {})
            env_current_score = env_impact_data.get("current_score", 0)
            env_potential_score = env_impact_data.get("potential_score", 0)
            
            # Property efficiency features
            efficiency_data = energy_data.get("property_efficiency", {})
            
            # Extract key efficiency ratings
            heating_efficiency = efficiency_data.get("property_main_heating_energy_efficiency", "")
            windows_efficiency = efficiency_data.get("property_windows_energy_efficiency", "")
            walls_efficiency = efficiency_data.get("property_walls_energy_efficiency", "")
            lighting_efficiency = efficiency_data.get("property_lighting_energy_efficiency", "")
            
            # Create efficiency features list
            efficiency_features = []
            if heating_efficiency:
                efficiency_features.append(f"Heating: {heating_efficiency}")
            if windows_efficiency:
                efficiency_features.append(f"Windows: {windows_efficiency}")
            if walls_efficiency:
                efficiency_features.append(f"Walls: {walls_efficiency}")
            if lighting_efficiency:
                efficiency_features.append(f"Lighting: {lighting_efficiency}")
            
            # Infer property type from API data if available
            api_property_type = energy_data.get("property_type", property_type)
            if api_property_type:
                property_type = api_property_type.lower()
            
            print(f"[SUSTAINABILITY] Processed data successfully:")
            print(f"[SUSTAINABILITY]   - Current emissions: {current_emissions} {emissions_metric}")
            print(f"[SUSTAINABILITY]   - Potential emissions: {potential_emissions} {emissions_metric}")
            print(f"[SUSTAINABILITY]   - EPC rating: {energy_rating} (score: {energy_score})")
            print(f"[SUSTAINABILITY]   - Energy consumption: {current_consumption} {consumption_metric}")
            print(f"[SUSTAINABILITY]   - Annual energy cost: {currency}{total_current_cost}")
            print(f"[SUSTAINABILITY]   - Environmental score: {env_current_score}")
        
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
        
        # Calculate savings potential
        emissions_savings = current_emissions - potential_emissions
        cost_savings = total_current_cost - total_potential_cost
        consumption_savings = current_consumption - potential_consumption
        
        print(f"\n[SUSTAINABILITY] Savings Potential:")
        print(f"[SUSTAINABILITY]   - CO2 reduction: {emissions_savings:.2f} tonnes/year")
        print(f"[SUSTAINABILITY]   - Cost savings: {currency}{cost_savings:.0f}/year")
        print(f"[SUSTAINABILITY]   - Energy reduction: {consumption_savings:.0f} {consumption_metric}")
        
        # ======================================================================
        # EMBODIED CARBON CALCULATION (EN 15978 / RICS Whole Life Carbon)
        # ======================================================================
        print(f"\n[EMBODIED CARBON] Calculating whole life carbon (A1-A5)...")
        print(f"[EMBODIED CARBON] Standards: EN 15978:2011, RICS WLC 2nd Ed (2023)")
        print(f"[EMBODIED CARBON] Property: {property_size} m² {property_type}")
        
        # Material quantities estimation (BoQ) based on property type and size
        # Values based on UK typical residential construction
        material_intensities = {
            "flat": {
                "concrete_m3_per_m2": 0.25,      # Less structural demand (shared walls/floors)
                "rebar_kg_per_m2": 15,
                "steel_kg_per_m2": 8,
                "brick_units_per_m2": 45,
                "timber_m3_per_m2": 0.02,
            },
            "apartment": {
                "concrete_m3_per_m2": 0.25,
                "rebar_kg_per_m2": 15,
                "steel_kg_per_m2": 8,
                "brick_units_per_m2": 45,
                "timber_m3_per_m2": 0.02,
            },
            "terraced": {
                "concrete_m3_per_m2": 0.35,
                "rebar_kg_per_m2": 20,
                "steel_kg_per_m2": 12,
                "brick_units_per_m2": 60,
                "timber_m3_per_m2": 0.04,
            },
            "semi-detached": {
                "concrete_m3_per_m2": 0.4,
                "rebar_kg_per_m2": 22,
                "steel_kg_per_m2": 15,
                "brick_units_per_m2": 70,
                "timber_m3_per_m2": 0.045,
            },
            "detached": {
                "concrete_m3_per_m2": 0.5,       # Full external envelope
                "rebar_kg_per_m2": 25,
                "steel_kg_per_m2": 18,
                "brick_units_per_m2": 80,
                "timber_m3_per_m2": 0.05,
            },
        }
        
        # Get material intensities for property type (default to flat)
        intensities = material_intensities.get(property_type.lower(), material_intensities["flat"])
        
        # Calculate material quantities
        concrete_m3 = property_size * intensities["concrete_m3_per_m2"]
        rebar_kg = property_size * intensities["rebar_kg_per_m2"]
        steel_kg = property_size * intensities["steel_kg_per_m2"]
        brick_units = property_size * intensities["brick_units_per_m2"]
        timber_m3 = property_size * intensities["timber_m3_per_m2"]
        
        print(f"[EMBODIED CARBON] Material quantities (BoQ):")
        print(f"[EMBODIED CARBON]   - Concrete: {concrete_m3:.1f} m³")
        print(f"[EMBODIED CARBON]   - Rebar steel: {rebar_kg:.1f} kg")
        print(f"[EMBODIED CARBON]   - Structural steel: {steel_kg:.1f} kg")
        print(f"[EMBODIED CARBON]   - Brick: {brick_units:.0f} units")
        print(f"[EMBODIED CARBON]   - Timber: {timber_m3:.2f} m³")
        
        # A1-A3 Emission factors (kg CO₂e per unit) - from ICE Database v3.0 / EPDs
        # These include raw material extraction + processing + manufacturing
        emission_factors_a1_a3 = {
            "concrete": 280,              # kg CO₂e/m³ (General Purpose)
            "rebar": 1.20,                # kg CO₂e/kg (reinforcement steel)
            "structural_steel": 1.70,     # kg CO₂e/kg
            "brick": 0.22,                # kg CO₂e/unit (clay brick)
            "timber": 110,                # kg CO₂e/m³ (softwood, construction grade)
        }
        
        # A1-A3: Product stage (raw material + manufacturing)
        a1_a3_concrete = concrete_m3 * emission_factors_a1_a3["concrete"]
        a1_a3_rebar = rebar_kg * emission_factors_a1_a3["rebar"]
        a1_a3_steel = steel_kg * emission_factors_a1_a3["structural_steel"]
        a1_a3_brick = brick_units * emission_factors_a1_a3["brick"]
        a1_a3_timber = timber_m3 * emission_factors_a1_a3["timber"]
        
        a1_a3_total = a1_a3_concrete + a1_a3_rebar + a1_a3_steel + a1_a3_brick + a1_a3_timber
        
        print(f"\n[EMBODIED CARBON] A1-A3 (Product stage - includes mining/smelting/quarrying):")
        print(f"[EMBODIED CARBON]   - Concrete: {a1_a3_concrete:.0f} kg CO₂e")
        print(f"[EMBODIED CARBON]   - Rebar: {a1_a3_rebar:.0f} kg CO₂e")
        print(f"[EMBODIED CARBON]   - Steel: {a1_a3_steel:.0f} kg CO₂e")
        print(f"[EMBODIED CARBON]   - Brick: {a1_a3_brick:.0f} kg CO₂e")
        print(f"[EMBODIED CARBON]   - Timber: {a1_a3_timber:.0f} kg CO₂e")
        print(f"[EMBODIED CARBON]   A1-A3 Total: {a1_a3_total:.0f} kg CO₂e")
        
        # A4: Transportation to site
        # Assumption: Average 120 km, truck transport 0.1 kg CO₂e / t·km
        transport_distance_km = 120
        transport_factor = 0.1  # kg CO₂e / t·km
        
        # Total mass transported (convert to tonnes)
        total_mass_tonnes = (rebar_kg + steel_kg) / 1000 + concrete_m3 * 2.4 + brick_units * 0.0025 + timber_m3 * 0.5
        
        a4_transport = total_mass_tonnes * transport_distance_km * transport_factor
        
        print(f"\n[EMBODIED CARBON] A4 (Transportation):")
        print(f"[EMBODIED CARBON]   - Distance: {transport_distance_km} km")
        print(f"[EMBODIED CARBON]   - Total mass: {total_mass_tonnes:.1f} tonnes")
        print(f"[EMBODIED CARBON]   A4 Total: {a4_transport:.0f} kg CO₂e")
        
        # A5: Construction & installation (on-site energy, waste, temporary works)
        # RICS default: 5% of A1-A3
        a5_construction = a1_a3_total * 0.05
        
        print(f"\n[EMBODIED CARBON] A5 (Construction/installation - 5% of A1-A3):")
        print(f"[EMBODIED CARBON]   A5 Total: {a5_construction:.0f} kg CO₂e")
        
        # Total embodied carbon (A1-A5)
        embodied_carbon_total_kg = a1_a3_total + a4_transport + a5_construction
        embodied_carbon_total_tonnes = embodied_carbon_total_kg / 1000
        
        # Embodied carbon per m² (normalized)
        embodied_carbon_per_m2 = embodied_carbon_total_kg / property_size
        
        # Annualized embodied carbon (60-year reference study period)
        reference_study_period_years = 60
        embodied_carbon_annual_tonnes = embodied_carbon_total_tonnes / reference_study_period_years
        
        print(f"\n[EMBODIED CARBON] Summary (EN 15978 compliant):")
        print(f"[EMBODIED CARBON]   - Total A1-A5: {embodied_carbon_total_tonnes:.1f} tonnes CO₂e")
        print(f"[EMBODIED CARBON]   - Per m² (GIA): {embodied_carbon_per_m2:.0f} kg CO₂e/m²")
        print(f"[EMBODIED CARBON]   - Annualized (60 yrs): {embodied_carbon_annual_tonnes:.2f} tonnes CO₂e/year")
        print(f"[EMBODIED CARBON]   - Reference study period: {reference_study_period_years} years")
        print(f"[EMBODIED CARBON]   - Standards: EN 15978:2011 / RICS WLC")
        
        # Breakdown for reporting
        embodied_carbon_breakdown = {
            "a1_a3_total": a1_a3_total / 1000,  # tonnes
            "a4_transport": a4_transport / 1000,
            "a5_construction": a5_construction / 1000,
            "total": embodied_carbon_total_tonnes,
            "per_m2": embodied_carbon_per_m2,
            "annualized": embodied_carbon_annual_tonnes,
        }
        
        # Build A2UI messages
        a2ui_messages = build_carbon_card(
            location=property_address,
            current_emissions=current_emissions,
            potential_emissions=potential_emissions,
            emissions_metric=emissions_metric,
            energy_rating=energy_rating,
            potential_rating=potential_rating,
            property_size=property_size,
            property_type=property_type,
            current_consumption=current_consumption,
            potential_consumption=potential_consumption,
            consumption_metric=consumption_metric,
            current_energy_cost=total_current_cost,
            potential_energy_cost=total_potential_cost,
            currency=currency,
            environmental_score=env_current_score,
            potential_environmental_score=env_potential_score,
            efficiency_features=efficiency_features,
            embodied_carbon_total=embodied_carbon_total_tonnes,
            embodied_carbon_per_m2=embodied_carbon_per_m2,
            embodied_carbon_annual=embodied_carbon_annual_tonnes,
            embodied_carbon_a1_a3=a1_a3_total / 1000,
            embodied_carbon_a4=a4_transport / 1000,
            embodied_carbon_a5=a5_construction / 1000,
        )
        
        # Generate summary
        reduction_percent = ((current_emissions - potential_emissions) / current_emissions) * 100 if current_emissions > 0 else 0
        cost_reduction_percent = ((total_current_cost - total_potential_cost) / total_current_cost) * 100 if total_current_cost > 0 else 0
        total_annual_carbon = current_emissions + embodied_carbon_annual_tonnes
        
        summary = (
            f"Sustainability Assessment for {property_address} ({property_size:.0f} m² {property_type}):\n\n"
            f"🌱 **Energy Performance:** EPC {energy_rating} (Score: {energy_score}/100) → Potential: {potential_rating} ({potential_score}/100)\n"
            f"🌍 **Environmental Impact Score:** {env_current_score}/100 → Potential: {env_potential_score}/100\n\n"
            f"⚡ **Energy Consumption:** {current_consumption} {consumption_metric} → {potential_consumption} {consumption_metric} ({consumption_savings:.0f} {consumption_metric} reduction)\n"
            f"💰 **Annual Energy Costs:** {currency}{total_current_cost:.0f} → {currency}{total_potential_cost:.0f} (Save {currency}{cost_savings:.0f}/year, {cost_reduction_percent:.0f}% reduction)\n"
            f"🏭 **CO2 Emissions (Operational):** {current_emissions:.1f} tonnes/year → {potential_emissions:.1f} tonnes/year ({reduction_percent:.0f}% reduction)\n\n"
            f"🏗️ **Embodied Carbon (EN 15978):**\n"
            f"   • Total (A1-A5): {embodied_carbon_total_tonnes:.1f} tonnes CO₂e\n"
            f"   • Intensity: {embodied_carbon_per_m2:.0f} kg CO₂e/m² (GIA)\n"
            f"   • Annualized (60 yrs): {embodied_carbon_annual_tonnes:.2f} tonnes/year\n"
            f"   • Total Annual Footprint: {total_annual_carbon:.2f} tonnes CO₂e/year\n\n"
            f"✨ **Key Features:** {', '.join(efficiency_features[:3]) if efficiency_features else 'Standard efficiency'}"
        )
        
        return EmbodiedCarbonResult(
            success=True,
            location=property_address,
            current_emissions=current_emissions,
            potential_emissions=potential_emissions,
            emissions_metric=emissions_metric,
            energy_rating=energy_rating,
            property_size=property_size,
            property_type=property_type,
            recommendations=[],
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
    
    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
