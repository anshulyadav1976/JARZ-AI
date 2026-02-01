"""Feature engineering for spatio-temporal model."""
from datetime import datetime
from typing import Optional
from .schemas import UserQuery, ModelFeatures, ResolvedLocation, Neighbor
from .scansan_client import get_scansan_client


async def resolve_location(location_input: str) -> Optional[ResolvedLocation]:
    """Resolve user input to standardized location."""
    client = get_scansan_client()
    return await client.search_area_codes(location_input)


async def build_temporal_features(
    district: str,
    horizon_months: int = 6,
) -> dict:
    """Build temporal features from growth and demand data."""
    client = get_scansan_client()
    
    # Get growth data
    growth_data = await client.get_district_growth(district)
    
    # Get demand data
    demand_data = await client.get_district_demand(district)
    
    # Current date info
    now = datetime.now()
    
    features = {
        "month": now.month,
        "quarter": (now.month - 1) // 3 + 1,
        "rent_growth_mom": (growth_data or {}).get("mom_growth", 0.0),
        "rent_growth_yoy": (growth_data or {}).get("yoy_growth", 0.0),
        "demand_index": (demand_data or {}).get("demand_index", 75.0),
        "demand_index_lag1": (demand_data or {}).get("demand_index", 75.0) * 0.98,  # Simulated lag
        "horizon_months": horizon_months,
    }
    
    return features


async def build_spatial_features(
    area_code: str,
    k_neighbors: int = 5,
    radius_km: Optional[float] = None,
) -> tuple[dict, list[Neighbor]]:
    """Build spatial features from neighbor data."""
    client = get_scansan_client()
    
    neighbors = await client.get_neighbors(area_code, k=k_neighbors, radius_km=radius_km)
    
    if not neighbors:
        return {
            "neighbor_avg_rent": None,
            "neighbor_avg_demand": None,
            "neighbor_avg_growth": None,
            "neighbor_count": 0,
        }, []
    
    # Calculate averages
    avg_rent = sum(n.avg_rent or 0 for n in neighbors) / len(neighbors)
    avg_demand = sum(n.demand_index or 75 for n in neighbors) / len(neighbors)
    
    # Estimate growth from demand trend (simplified)
    avg_growth = sum((n.demand_index or 75) / 100 * 0.5 for n in neighbors) / len(neighbors)
    
    features = {
        "neighbor_avg_rent": round(avg_rent, 2),
        "neighbor_avg_demand": round(avg_demand, 2),
        "neighbor_avg_growth": round(avg_growth, 4),
        "neighbor_count": len(neighbors),
    }
    
    return features, neighbors


async def build_features(query: UserQuery) -> tuple[ModelFeatures, ResolvedLocation, list[Neighbor]]:
    """
    Build complete feature set for prediction.
    
    Returns:
        - ModelFeatures for prediction
        - ResolvedLocation with area info
        - List of Neighbor areas
    """
    client = get_scansan_client()
    
    # Resolve location
    location = await resolve_location(query.location_input)
    if not location:
        raise ValueError(f"Could not resolve location: {query.location_input}")
    
    # Get area summary
    summary = await client.get_area_summary(location.area_code)
    
    # Build temporal features
    district = location.area_code_district or location.area_code
    temporal_features = await build_temporal_features(
        district=district,
        horizon_months=query.horizon_months,
    )
    
    # Build spatial features
    spatial_features, neighbors = await build_spatial_features(
        area_code=location.area_code,
        k_neighbors=query.k_neighbors or 5,
        radius_km=query.radius_km,
    )
    
    # Combine all features
    features = ModelFeatures(
        area_code=location.area_code,
        area_code_district=location.area_code_district,
        # Temporal
        month=temporal_features["month"],
        quarter=temporal_features["quarter"],
        rent_growth_mom=temporal_features["rent_growth_mom"],
        rent_growth_yoy=temporal_features["rent_growth_yoy"],
        demand_index=temporal_features["demand_index"],
        demand_index_lag1=temporal_features["demand_index_lag1"],
        horizon_months=temporal_features["horizon_months"],
        # Spatial
        neighbor_avg_rent=spatial_features["neighbor_avg_rent"],
        neighbor_avg_demand=spatial_features["neighbor_avg_demand"],
        neighbor_avg_growth=spatial_features["neighbor_avg_growth"],
        neighbor_count=spatial_features["neighbor_count"],
        # Area stats
        median_rent=(summary or {}).get("median_rent"),
        avg_rent=(summary or {}).get("avg_rent"),
        listing_count=(summary or {}).get("listing_count"),
    )
    
    return features, location, neighbors
