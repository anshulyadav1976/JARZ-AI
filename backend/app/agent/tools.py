"""
Agent tools for the chat-based LangGraph agent.

These tools allow the LLM to interact with the rental valuation system.
The LLM decides when to call these tools based on user queries.
Tool results are cached so repeated requests (same args) return fast for demos.
"""
import random
import re
from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..schemas import UserQuery, PredictionResult, ExplanationResult, ResolvedLocation, Neighbor, Driver, PredictionMetadata
from ..feature_builder import build_features
from ..model_adapter import get_model_adapter
from ..explain import explain_prediction
from ..a2ui_builder import build_complete_ui, build_listings_cards, build_location_comparison_ui
from ..scansan_client import get_scansan_client
from .. import cache as tool_cache


# =============================================================================
# MOCK DATA SETS (3 rotating sets for demo when model isn't available)
# =============================================================================
# Each set contains complete data for: prediction, explanation, location,
# neighbors, and is used to generate full A2UI visuals for demos.
# =============================================================================

def _get_mock_data_sets():
    """Return 3 complete mock data sets for rent forecast demos."""
    
    # Set 1: Camden (NW1) - High-demand central London
    set_1 = {
        "location": ResolvedLocation(
            area_code="NW1",
            area_code_district="NW1",
            display_name="Camden, NW1",
            lat=51.5388,
            lon=-0.1426,
        ),
        "prediction": PredictionResult(
            p10=2150.0,
            p50=2650.0,
            p90=3200.0,
            unit="GBP/month",
            horizon_months=6,
            metadata=PredictionMetadata(
                model_version="mock-demo-v1",
                feature_version="v1",
                timestamp=datetime.utcnow(),
            ),
        ),
        "explanation": ExplanationResult(
            drivers=[
                Driver(name="Rental Demand Index", contribution=185.0, direction="positive"),
                Driver(name="Year-over-Year Growth", contribution=120.0, direction="positive"),
                Driver(name="Neighboring Area Rents", contribution=95.0, direction="positive"),
                Driver(name="Seasonal Demand (Summer)", contribution=75.0, direction="positive"),
                Driver(name="Transport Links", contribution=60.0, direction="positive"),
                Driver(name="Market Liquidity", contribution=45.0, direction="positive"),
            ],
            base_value=2200.0,
        ),
        "neighbors": [
            Neighbor(area_code="NW3", display_name="Hampstead", lat=51.5565, lon=-0.1782, avg_rent=2800.0, demand_index=82.0, distance_km=2.1),
            Neighbor(area_code="NW5", display_name="Kentish Town", lat=51.5508, lon=-0.1411, avg_rent=2200.0, demand_index=78.0, distance_km=1.4),
            Neighbor(area_code="N1", display_name="Islington", lat=51.5362, lon=-0.1033, avg_rent=2500.0, demand_index=85.0, distance_km=2.8),
            Neighbor(area_code="WC1", display_name="Bloomsbury", lat=51.5246, lon=-0.1217, avg_rent=2750.0, demand_index=80.0, distance_km=1.9),
            Neighbor(area_code="NW8", display_name="St John's Wood", lat=51.5344, lon=-0.1747, avg_rent=3100.0, demand_index=76.0, distance_km=2.3),
        ],
        "summary_template": "Camden (NW1) 6mo forecast: £2,650 (P10: £2,150, P90: £3,200). Key factors: Rental Demand Index (increasing rent by ~185 GBP), Year-over-Year Growth (increasing rent by ~120 GBP), Neighboring Area Rents (increasing rent by ~95 GBP).",
    }
    
    # Set 2: Canary Wharf (E14) - Financial district, high-rise
    set_2 = {
        "location": ResolvedLocation(
            area_code="E14",
            area_code_district="E14",
            display_name="Canary Wharf, E14",
            lat=51.5054,
            lon=-0.0235,
        ),
        "prediction": PredictionResult(
            p10=1850.0,
            p50=2350.0,
            p90=2900.0,
            unit="GBP/month",
            horizon_months=6,
            metadata=PredictionMetadata(
                model_version="mock-demo-v1",
                feature_version="v1",
                timestamp=datetime.utcnow(),
            ),
        ),
        "explanation": ExplanationResult(
            drivers=[
                Driver(name="Corporate Demand", contribution=165.0, direction="positive"),
                Driver(name="Transport Links (Jubilee/Elizabeth)", contribution=140.0, direction="positive"),
                Driver(name="New Build Premium", contribution=110.0, direction="positive"),
                Driver(name="Year-over-Year Growth", contribution=85.0, direction="positive"),
                Driver(name="Amenities Score", contribution=70.0, direction="positive"),
                Driver(name="Limited Supply", contribution=55.0, direction="positive"),
            ],
            base_value=1950.0,
        ),
        "neighbors": [
            Neighbor(area_code="E1", display_name="Whitechapel", lat=51.5152, lon=-0.0597, avg_rent=2100.0, demand_index=79.0, distance_km=3.2),
            Neighbor(area_code="SE10", display_name="Greenwich", lat=51.4769, lon=-0.0005, avg_rent=1900.0, demand_index=75.0, distance_km=2.8),
            Neighbor(area_code="E16", display_name="Royal Docks", lat=51.5077, lon=0.0469, avg_rent=1750.0, demand_index=72.0, distance_km=3.5),
            Neighbor(area_code="SE16", display_name="Rotherhithe", lat=51.4978, lon=-0.0522, avg_rent=1850.0, demand_index=74.0, distance_km=2.4),
            Neighbor(area_code="E3", display_name="Bow", lat=51.5287, lon=-0.0186, avg_rent=1950.0, demand_index=77.0, distance_km=2.9),
        ],
        "summary_template": "Canary Wharf (E14) 6mo forecast: £2,350 (P10: £1,850, P90: £2,900). Key factors: Corporate Demand (increasing rent by ~165 GBP), Transport Links (increasing rent by ~140 GBP), New Build Premium (increasing rent by ~110 GBP).",
    }
    
    # Set 3: Chelsea (SW3) - Prime central London, luxury
    set_3 = {
        "location": ResolvedLocation(
            area_code="SW3",
            area_code_district="SW3",
            display_name="Chelsea, SW3",
            lat=51.4875,
            lon=-0.1687,
        ),
        "prediction": PredictionResult(
            p10=3200.0,
            p50=4100.0,
            p90=5200.0,
            unit="GBP/month",
            horizon_months=6,
            metadata=PredictionMetadata(
                model_version="mock-demo-v1",
                feature_version="v1",
                timestamp=datetime.utcnow(),
            ),
        ),
        "explanation": ExplanationResult(
            drivers=[
                Driver(name="Prime Location Premium", contribution=420.0, direction="positive"),
                Driver(name="International Demand", contribution=280.0, direction="positive"),
                Driver(name="Neighboring Area Rents", contribution=195.0, direction="positive"),
                Driver(name="Property Quality Index", contribution=150.0, direction="positive"),
                Driver(name="Year-over-Year Growth", contribution=110.0, direction="positive"),
                Driver(name="School Catchment Premium", contribution=85.0, direction="positive"),
            ],
            base_value=3400.0,
        ),
        "neighbors": [
            Neighbor(area_code="SW1", display_name="Belgravia", lat=51.4975, lon=-0.1505, avg_rent=4500.0, demand_index=88.0, distance_km=1.5),
            Neighbor(area_code="SW7", display_name="South Kensington", lat=51.4941, lon=-0.1749, avg_rent=3800.0, demand_index=85.0, distance_km=0.9),
            Neighbor(area_code="SW10", display_name="West Brompton", lat=51.4803, lon=-0.1885, avg_rent=2900.0, demand_index=78.0, distance_km=1.8),
            Neighbor(area_code="W8", display_name="Kensington", lat=51.5009, lon=-0.1925, avg_rent=3600.0, demand_index=84.0, distance_km=2.1),
            Neighbor(area_code="SW5", display_name="Earl's Court", lat=51.4903, lon=-0.1950, avg_rent=2650.0, demand_index=76.0, distance_km=1.6),
        ],
        "summary_template": "Chelsea (SW3) 6mo forecast: £4,100 (P10: £3,200, P90: £5,200). Key factors: Prime Location Premium (increasing rent by ~420 GBP), International Demand (increasing rent by ~280 GBP), Neighboring Area Rents (increasing rent by ~195 GBP).",
    }
    
    return [set_1, set_2, set_3]


def _get_random_mock_forecast(location_input: str, horizon_months: int = 6) -> dict:
    """
    Get a random mock forecast data set and adapt it to the requested location.
    
    Returns a dict with: prediction, explanation, location, neighbors, summary
    """
    mock_sets = _get_mock_data_sets()
    mock = random.choice(mock_sets)
    
    # Adapt location name to user input if it looks like a postcode
    location_input_upper = location_input.strip().upper()
    
    # Create adapted location
    adapted_location = ResolvedLocation(
        area_code=mock["location"].area_code,
        area_code_district=mock["location"].area_code_district,
        display_name=f"{location_input_upper} (demo data)",
        lat=mock["location"].lat,
        lon=mock["location"].lon,
    )
    
    # Adapt prediction horizon
    adapted_prediction = PredictionResult(
        p10=mock["prediction"].p10,
        p50=mock["prediction"].p50,
        p90=mock["prediction"].p90,
        unit=mock["prediction"].unit,
        horizon_months=horizon_months,
        metadata=PredictionMetadata(
            model_version="mock-demo-v1",
            feature_version="v1",
            timestamp=datetime.utcnow(),
        ),
    )
    
    # Generate summary
    area_name = adapted_location.display_name
    top_drivers = mock["explanation"].drivers[:3]
    driver_text = ""
    if top_drivers:
        driver_parts = []
        for d in top_drivers:
            direction = "increasing" if d.direction == "positive" else "decreasing"
            driver_parts.append(f"{d.name} ({direction} rent by ~{d.contribution:.0f} GBP)")
        driver_text = f" Key factors: {', '.join(driver_parts)}."
    
    summary = (
        f"{area_name} {horizon_months}mo forecast: "
        f"£{adapted_prediction.p50:,.0f} (P10: £{adapted_prediction.p10:,.0f}, P90: £{adapted_prediction.p90:,.0f})"
        f"{driver_text}"
    )
    
    return {
        "prediction": adapted_prediction,
        "explanation": mock["explanation"],
        "location": adapted_location,
        "neighbors": mock["neighbors"],
        "summary": summary,
    }


# =============================================================================


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
    interest_coverage_ratio: float  # NEW: ICR percentage (125% = lender standard)
    icr_pass: bool  # NEW: Whether ICR meets 125% threshold
    min_rent_for_icr: float  # NEW: Minimum rent needed for 125% ICR
    min_deposit_percent_for_icr: float  # NEW: Minimum deposit % for 125% ICR
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
        "description": "Compare 2-3 UK areas using ScanSan area summary. Use when the user says 'compare', 'vs', or asks which area is better. Compares total properties, sold price range (last 5y), current valuation range, current rent listings (and rent pcm range if available), and current sale listings (and sale price range if available).",
        "parameters": {
            "type": "object",
            "properties": {
                "areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2-3 area codes/postcodes to compare (e.g. ['NW1','E14','SW1A']). If provided, this is used instead of location1/location2.",
                },
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
            "required": []
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
                    "description": "Annual mortgage interest rate percentage. If not provided, will fetch real-time UK mortgage rates from Bank of England."
                },
                "mortgage_years": {
                    "type": "number",
                    "description": "Mortgage term in years (default 25).",
                    "default": 25
                },
                "mortgage_type": {
                    "type": "string",
                    "description": "Mortgage type: 'interest_only' (default, recommended for BTL) or 'repayment'. Interest-only maximizes cash flow by only paying interest, not principal.",
                    "enum": ["interest_only", "repayment"],
                    "default": "interest_only"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "get_market_data",
        "description": "Open the Market Data tab and load growth, rent demand, sale demand, valuations, and sale history for a UK location. Use when the user asks for: market data, growth data, rent demand, sale demand, valuations, sale history, or to 'show me market data for X', 'give me market data on postcode Y', 'load market data for NW1', etc. Resolves the location to a district (for growth/demand) and postcode (for valuations/sale history) and instructs the UI to switch to Market Data and load.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The UK location: postcode (e.g. 'NW1 0BH', 'NW1'), district (e.g. 'NW1'), or area name (e.g. 'Camden'). Will be resolved via search to get district; if a full postcode is provided, valuations and sale history will load for that postcode."
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
    
    If the pipeline fails (model not available, location not resolved, etc.),
    falls back to one of 3 rotating mock data sets to show UI mockups for demos.
    
    Args:
        location: Location string (postcode, area name)
        horizon_months: Forecast horizon (1, 3, 6, or 12)
        k_neighbors: Number of spatial neighbors
        
    Returns:
        RentForecastResult with prediction, explanation, and UI components
    """
    try:
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
    
    except Exception as e:
        # =====================================================================
        # FALLBACK: Use mock data for demo when real pipeline fails
        # =====================================================================
        print(f"[RENT_FORECAST] Pipeline error, using mock data: {e}")
        
        mock = _get_random_mock_forecast(location, horizon_months)
        mock_prediction = mock["prediction"]
        mock_explanation = mock["explanation"]
        mock_location = mock["location"]
        mock_neighbors = mock["neighbors"]
        mock_summary = mock["summary"]
        
        # Build A2UI messages from mock data
        a2ui_messages = build_complete_ui(
            prediction=mock_prediction,
            explanation=mock_explanation,
            location=mock_location,
            neighbors=mock_neighbors,
            horizon_months=horizon_months,
            k_neighbors=k_neighbors,
        )
        
        return RentForecastResult(
            prediction=mock_prediction.model_dump() if hasattr(mock_prediction, 'model_dump') else mock_prediction.__dict__,
            explanation=mock_explanation.model_dump() if hasattr(mock_explanation, 'model_dump') else mock_explanation.__dict__,
            location=mock_location.model_dump() if hasattr(mock_location, 'model_dump') else mock_location.__dict__,
            neighbors=[n.model_dump() if hasattr(n, 'model_dump') else n.__dict__ for n in mock_neighbors],
            a2ui_messages=a2ui_messages,
            summary=mock_summary,
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
    location1: str | None = None,
    location2: str | None = None,
    areas: Optional[list[str]] = None,
    horizon_months: int = 6,
) -> dict:
    """
    Compare 2-3 areas based on ScanSan area summary.
    """
    client = get_scansan_client()

    area_inputs: list[str] = []
    if areas:
        area_inputs = [a for a in areas if a]
    else:
        if location1:
            area_inputs.append(location1)
        if location2:
            area_inputs.append(location2)

    # Normalize / dedupe
    normalized_inputs = []
    for a in area_inputs:
        a = a.strip()
        if not a:
            continue
        if a.upper() not in [x.upper() for x in normalized_inputs]:
            normalized_inputs.append(a)

    if len(normalized_inputs) < 2:
        return {
            "success": False,
            "summary": "Please provide at least 2 area codes/postcodes to compare.",
            "a2ui_messages": [],
        }
    if len(normalized_inputs) > 3:
        normalized_inputs = normalized_inputs[:3]

    # Resolve area codes and fetch summaries
    areas_out: list[dict] = []
    for user_input in normalized_inputs:
        resolved = await client.search_area_codes(user_input)
        area_code = (resolved.area_code if resolved else user_input).upper()
        display_name = resolved.display_name if resolved and resolved.display_name else area_code

        raw_summary = await client.get_area_summary(area_code)
        summary_row = None
        if isinstance(raw_summary, dict):
            data = raw_summary.get("data")
            if isinstance(data, list) and data:
                summary_row = data[0]
        if summary_row is None:
            summary_row = {}

        sold_range = summary_row.get("sold_price_range_in_last_5yrs") or [None, None]
        valuation_range = summary_row.get("current_valuation_range") or [None, None]
        rent_pcm_range = summary_row.get("current_rent_listings_pcm_range") or [None, None]
        sale_price_range = summary_row.get("current_sale_listings_price_range") or [None, None]

        def _mid(rng):
            try:
                lo, hi = rng
                if lo is None or hi is None:
                    return None
                return (float(lo) + float(hi)) / 2.0
            except Exception:
                return None

        area_obj = {
            "area_code": area_code,
            "display_name": display_name,
            "total_properties": summary_row.get("total_properties"),
            "total_properties_sold_in_last_5yrs": summary_row.get("total_properties_sold_in_last_5yrs"),
            "sold_price_min": sold_range[0],
            "sold_price_max": sold_range[1],
            "valuation_min": valuation_range[0] if isinstance(valuation_range, list) else None,
            "valuation_max": valuation_range[1] if isinstance(valuation_range, list) else None,
            "rent_listings": summary_row.get("current_rent_listings"),
            "rent_pcm_min": rent_pcm_range[0],
            "rent_pcm_max": rent_pcm_range[1],
            "sale_listings": summary_row.get("current_sale_listings"),
            "sale_price_min": sale_price_range[0],
            "sale_price_max": sale_price_range[1],
            # Derived
            "rent_pcm_mid": _mid(rent_pcm_range),
            "sale_price_mid": _mid(sale_price_range),
            "sold_price_mid": _mid(sold_range),
            "valuation_mid": _mid(valuation_range) if isinstance(valuation_range, list) else None,
        }
        areas_out.append(area_obj)

    # Compute winners (simple, practical)
    def _winner(key: str, mode: str) -> Optional[str]:
        vals = [(a.get(key), a["area_code"]) for a in areas_out if a.get(key) is not None]
        if not vals:
            return None
        vals.sort(key=lambda x: x[0], reverse=(mode == "max"))
        return vals[0][1]

    winners = {
        "cheapest_rent_mid": _winner("rent_pcm_mid", "min"),
        "most_rent_listings": _winner("rent_listings", "max"),
        "cheapest_sale_mid": _winner("sale_price_mid", "min"),
        "most_sale_listings": _winner("sale_listings", "max"),
        "most_total_properties": _winner("total_properties", "max"),
    }

    a2ui_messages = build_location_comparison_ui(areas=areas_out, winners=winners)

    # Natural summary for the LLM / UI
    summary = (
        f"Compared {', '.join([a['area_code'] for a in areas_out])}. "
        f"Cheapest rent (midpoint) looks like {winners.get('cheapest_rent_mid') or 'N/A'}, "
        f"and the most rent listings is {winners.get('most_rent_listings') or 'N/A'}. "
        f"Cheapest sale (midpoint) looks like {winners.get('cheapest_sale_mid') or 'N/A'}."
    )

    return {
        "success": True,
        "areas": areas_out,
        "winners": winners,
        "a2ui_messages": a2ui_messages,
        "summary": summary,
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
        print(f"[CARBON] Received {len(a2ui_messages)} messages from build_carbon_card")
        for i, msg in enumerate(a2ui_messages):
            print(f"[CARBON]   Message {i}: {list(msg.keys())}")
        
        # Generate summary (balanced length ~130 words)
        reduction_percent = ((current_emissions - potential_emissions) / current_emissions) * 100 if current_emissions > 0 else 0
        total_annual_carbon = current_emissions + embodied_carbon_annual_tonnes
        
        summary = (
            f"This {property_size:.0f}m² {property_type} has an EPC rating of {energy_rating} (score {energy_score}/100) with current operational emissions "
            f"of {current_emissions:.1f} tonnes CO₂ per year. Through energy efficiency improvements, emissions could be reduced by {reduction_percent:.0f}% "
            f"to {potential_emissions:.1f} tonnes/year, achieving a potential {potential_rating} rating. "
            f"The property's embodied carbon footprint totals {embodied_carbon_total_tonnes:.1f} tonnes CO₂e from construction materials and processes, "
            f"which translates to approximately {embodied_carbon_annual_tonnes:.2f} tonnes/year when amortized over a 60-year lifespan. "
            f"Combined with operational emissions, the total annual carbon footprint is {total_annual_carbon:.2f} tonnes CO₂e/year. "
            f"See the Sustainability tab for detailed breakdowns, energy costs, and improvement recommendations."
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


async def execute_get_market_data(location: str) -> dict[str, Any]:
    """
    Resolve location and return a market_data_request payload so the frontend
    switches to the Market Data tab and loads growth, demand, valuations, sale history.
    """
    client = get_scansan_client()
    resolved = await client.search_area_codes(location.strip())
    district = None
    postcode = None
    if resolved:
        district = (resolved.area_code_district or resolved.area_code or "").strip().upper()
    # Normalize user input for postcode check
    raw = (location or "").strip().upper().replace(" ", "")
    # UK full postcode: outward (e.g. NW1) + inward (e.g. 0BH = digit + 2 letters)
    if re.match(r"^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$", raw):
        postcode = raw
    elif " " in location or len(raw) > 4:
        # User may have typed "NW1 0BH" or "NW10BH"
        postcode = raw if len(raw) >= 5 else None
    if not district and not postcode:
        # Fallback: use first part of location as district (e.g. "NW1" from "NW1 something")
        first_part = (location or "").strip().upper().split()[0] or location
        if re.match(r"^[A-Z]{1,2}\d[A-Z\d]?$", first_part.replace(" ", "")):
            district = first_part.replace(" ", "")
    if not district:
        district = postcode[:4] if postcode and len(postcode) >= 4 else (location or "").strip().upper()[:4]
    summary = f"Opening Market Data for {district}" + (f" (postcode {postcode})" if postcode else "") + ". The Market Data tab will load growth, rent and sale demand, and—if a full postcode was given—valuations and sale history."
    return {
        "success": True,
        "summary": summary,
        "market_data_request": {
            "district": district or None,
            "postcode": postcode or None,
        },
    }


def _cache_key(tool_name: str, arguments: dict[str, Any]) -> str:
    """Build a stable cache key for tool + args."""
    return tool_cache._make_key("tool", tool_name, arguments)


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a tool by name with given arguments.
    Results are cached so repeated calls with same args return fast (for demos).
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        
    Returns:
        Tool execution result as a dict
    """
    cache_key = _cache_key(tool_name, arguments)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    if tool_name == "get_rent_forecast":
        result = await execute_get_rent_forecast(
            location=arguments["location"],
            horizon_months=arguments.get("horizon_months", 6),
            k_neighbors=arguments.get("k_neighbors", 5),
        )
        out = {
            "success": True,
            "prediction": result.prediction,
            "explanation": result.explanation,
            "location": result.location,
            "neighbors": result.neighbors,
            "a2ui_messages": result.a2ui_messages,
            "summary": result.summary,
        }
        tool_cache.set_(cache_key, out)
        return out

    elif tool_name == "search_location":
        result = await execute_search_location(
            query=arguments["query"]
        )
        out = {
            "success": result.found,
            "location": result.location,
            "message": result.message,
        }
        tool_cache.set_(cache_key, out)
        return out

    elif tool_name == "compare_areas":
        result = await execute_compare_areas(
            location1=arguments.get("location1"),
            location2=arguments.get("location2"),
            areas=arguments.get("areas"),
            horizon_months=arguments.get("horizon_months", 6),
        )
        tool_cache.set_(cache_key, result)
        return result

    elif tool_name == "get_embodied_carbon":
        result = await execute_get_embodied_carbon(
            location=arguments["location"],
            property_type=arguments.get("property_type", "flat"),
        )
        out = {
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
        tool_cache.set_(cache_key, out)
        return out

    elif tool_name == "get_property_listings":
        result = await execute_get_property_listings(
            location=arguments["location"],
            listing_types=arguments.get("listing_types", ["rent", "sale"]),
            include_amenities=arguments.get("include_amenities", True),
        )
        out = {
            "success": result.success,
            "location": result.location,
            "area_code": result.area_code,
            "rent_listings": result.rent_listings,
            "sale_listings": result.sale_listings,
            "amenities": result.amenities,
            "a2ui_messages": result.a2ui_messages,
            "summary": result.summary,
        }
        tool_cache.set_(cache_key, out)
        return out

    elif tool_name == "get_investment_analysis":
        from .investment import execute_get_investment_analysis
        result = await execute_get_investment_analysis(
            location=arguments["location"],
            property_value=arguments.get("property_value"),
            deposit_percent=arguments.get("deposit_percent", 25),
            mortgage_rate=arguments.get("mortgage_rate"),
            mortgage_years=arguments.get("mortgage_years", 25),
            mortgage_type=arguments.get("mortgage_type", "interest_only"),
        )
        out = {
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
        tool_cache.set_(cache_key, out)
        return out

    elif tool_name == "get_market_data":
        out = await execute_get_market_data(location=arguments["location"])
        tool_cache.set_(cache_key, out)
        return out
    
    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
