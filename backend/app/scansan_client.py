"""ScanSan API client with caching and fallback mock data."""
import asyncio
import hashlib
import time
from typing import Any, Optional
import httpx
from .config import get_settings
from .schemas import ResolvedLocation, Neighbor


# In-memory cache
_cache: dict[str, tuple[float, Any]] = {}


def _cache_key(method: str, *args, **kwargs) -> str:
    """Generate cache key from method and arguments."""
    key_data = f"{method}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cached(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    settings = get_settings()
    if not settings.enable_cache:
        return None
    if key in _cache:
        timestamp, value = _cache[key]
        if time.time() - timestamp < settings.cache_ttl_seconds:
            return value
        del _cache[key]
    return None


def _set_cached(key: str, value: Any) -> None:
    """Set value in cache."""
    settings = get_settings()
    if settings.enable_cache:
        _cache[key] = (time.time(), value)


# ============================================================================
# Mock Data for Fallback
# ============================================================================

MOCK_AREA_CODES = {
    "NW1": {
        "area_code": "NW1",
        "area_code_district": "Camden",
        "display_name": "Camden Town, NW1",
        "lat": 51.5390,
        "lon": -0.1426,
    },
    "E14": {
        "area_code": "E14",
        "area_code_district": "Tower Hamlets",
        "display_name": "Canary Wharf, E14",
        "lat": 51.5054,
        "lon": -0.0235,
    },
    "SW1": {
        "area_code": "SW1",
        "area_code_district": "Westminster",
        "display_name": "Westminster, SW1",
        "lat": 51.4975,
        "lon": -0.1357,
    },
    "SE1": {
        "area_code": "SE1",
        "area_code_district": "Southwark",
        "display_name": "Southwark, SE1",
        "lat": 51.5030,
        "lon": -0.0870,
    },
    "W1": {
        "area_code": "W1",
        "area_code_district": "Westminster",
        "display_name": "West End, W1",
        "lat": 51.5145,
        "lon": -0.1445,
    },
    "EC1": {
        "area_code": "EC1",
        "area_code_district": "Islington",
        "display_name": "Clerkenwell, EC1",
        "lat": 51.5246,
        "lon": -0.1020,
    },
    "N1": {
        "area_code": "N1",
        "area_code_district": "Islington",
        "display_name": "Islington, N1",
        "lat": 51.5362,
        "lon": -0.1030,
    },
    "E1": {
        "area_code": "E1",
        "area_code_district": "Tower Hamlets",
        "display_name": "Whitechapel, E1",
        "lat": 51.5150,
        "lon": -0.0553,
    },
}

MOCK_AREA_SUMMARY = {
    "NW1": {
        "median_rent": 2200,
        "avg_rent": 2350,
        "min_rent": 1400,
        "max_rent": 4500,
        "listing_count": 245,
        "property_types": {"flat": 180, "house": 45, "studio": 20},
    },
    "E14": {
        "median_rent": 2400,
        "avg_rent": 2600,
        "min_rent": 1600,
        "max_rent": 5000,
        "listing_count": 320,
        "property_types": {"flat": 280, "house": 20, "studio": 20},
    },
}

MOCK_DEMAND = {
    "Camden": {"demand_index": 78.5, "trend": "increasing", "yoy_change": 5.2},
    "Tower Hamlets": {"demand_index": 82.3, "trend": "stable", "yoy_change": 2.1},
    "Westminster": {"demand_index": 85.0, "trend": "increasing", "yoy_change": 6.8},
    "Southwark": {"demand_index": 75.0, "trend": "increasing", "yoy_change": 4.5},
    "Islington": {"demand_index": 80.0, "trend": "stable", "yoy_change": 3.0},
}

MOCK_GROWTH = {
    "Camden": {
        "mom_growth": 0.8,
        "yoy_growth": 4.5,
        "historical": [
            {"period": "2025-01", "growth": 0.5},
            {"period": "2025-02", "growth": 0.7},
            {"period": "2025-03", "growth": 0.6},
            {"period": "2025-04", "growth": 0.9},
            {"period": "2025-05", "growth": 0.8},
            {"period": "2025-06", "growth": 0.7},
        ],
    },
    "Tower Hamlets": {
        "mom_growth": 0.5,
        "yoy_growth": 3.2,
        "historical": [
            {"period": "2025-01", "growth": 0.3},
            {"period": "2025-02", "growth": 0.4},
            {"period": "2025-03", "growth": 0.5},
            {"period": "2025-04", "growth": 0.6},
            {"period": "2025-05", "growth": 0.5},
            {"period": "2025-06", "growth": 0.4},
        ],
    },
}


def _get_mock_area_code(query: str) -> Optional[dict]:
    """Find area code from mock data."""
    query_upper = query.upper().strip()
    
    # Direct match
    if query_upper in MOCK_AREA_CODES:
        return MOCK_AREA_CODES[query_upper]
    
    # Partial match
    for code, data in MOCK_AREA_CODES.items():
        if query_upper in code or query_upper in data["display_name"].upper():
            return data
        if query_upper in data["area_code_district"].upper():
            return data
    
    # Default fallback to NW1
    return MOCK_AREA_CODES["NW1"]


def _get_mock_summary(area_code: str) -> dict:
    """Get mock summary for area code."""
    if area_code in MOCK_AREA_SUMMARY:
        return MOCK_AREA_SUMMARY[area_code]
    # Return default values
    return {
        "median_rent": 2000,
        "avg_rent": 2150,
        "min_rent": 1200,
        "max_rent": 4000,
        "listing_count": 150,
        "property_types": {"flat": 120, "house": 20, "studio": 10},
    }


def _get_mock_demand(district: str) -> dict:
    """Get mock demand for district."""
    if district in MOCK_DEMAND:
        return MOCK_DEMAND[district]
    return {"demand_index": 75.0, "trend": "stable", "yoy_change": 3.0}


def _get_mock_growth(district: str) -> dict:
    """Get mock growth for district."""
    if district in MOCK_GROWTH:
        return MOCK_GROWTH[district]
    return {
        "mom_growth": 0.5,
        "yoy_growth": 3.0,
        "historical": [],
    }


def _get_mock_neighbors(area_code: str, k: int = 5) -> list[dict]:
    """Get mock neighbors for area code."""
    neighbors = []
    current = MOCK_AREA_CODES.get(area_code)
    if not current:
        return []
    
    for code, data in MOCK_AREA_CODES.items():
        if code == area_code:
            continue
        # Simple distance calculation
        dlat = data["lat"] - current["lat"]
        dlon = data["lon"] - current["lon"]
        dist = (dlat**2 + dlon**2) ** 0.5 * 111  # Approximate km
        neighbors.append({
            "area_code": code,
            "display_name": data["display_name"],
            "lat": data["lat"],
            "lon": data["lon"],
            "distance_km": round(dist, 2),
            "avg_rent": _get_mock_summary(code).get("avg_rent", 2000),
            "demand_index": _get_mock_demand(data["area_code_district"]).get("demand_index", 75),
        })
    
    # Sort by distance and return top k
    neighbors.sort(key=lambda x: x["distance_km"])
    return neighbors[:k]


# ============================================================================
# ScanSan Client Class
# ============================================================================

class ScanSanClient:
    """Async client for ScanSan API with caching and fallback."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.scansan_base_url
        self.api_key = self.settings.scansan_api_key
        self.use_api = self.settings.use_scansan and bool(self.api_key)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        retries: int = 3,
    ) -> Optional[dict]:
        """Make API request with retries."""
        if not self.use_api:
            return None
        
        # Check cache
        cache_key = _cache_key(endpoint, params=params)
        cached = _get_cached(cache_key)
        if cached is not None:
            return cached
        
        client = await self._get_client()
        last_error = None
        
        for attempt in range(retries):
            try:
                if method.upper() == "GET":
                    response = await client.get(endpoint, params=params)
                else:
                    response = await client.post(endpoint, json=params)
                
                response.raise_for_status()
                data = response.json()
                _set_cached(cache_key, data)
                return data
                
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    # Rate limited - exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    break
            except httpx.RequestError as e:
                last_error = e
                await asyncio.sleep(1)
        
        print(f"ScanSan API error after {retries} attempts: {last_error}")
        return None
    
    async def search_area_codes(self, query: str) -> Optional[ResolvedLocation]:
        """Search for area codes matching query."""
        # Try API first
        if self.use_api:
            data = await self._request("GET", "/area_codes/search", {"search_term": query})
            if data and "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                return ResolvedLocation(
                    area_code=result.get("area_code", query.upper()),
                    area_code_district=result.get("district"),
                    display_name=result.get("display_name", query),
                    lat=result.get("lat"),
                    lon=result.get("lon"),
                )
        
        # Fallback to mock data
        mock = _get_mock_area_code(query)
        if mock:
            return ResolvedLocation(**mock)
        return None
    
    async def get_area_summary(self, area_code: str) -> dict:
        """Get summary statistics for area code."""
        if self.use_api:
            data = await self._request("GET", f"/area_codes/{area_code}/summary")
            if data:
                return data
        
        return _get_mock_summary(area_code)
    
    async def get_rent_listings(
        self,
        area_code: str,
        min_beds: Optional[int] = None,
        max_beds: Optional[int] = None,
        property_type: Optional[str] = None,
    ) -> dict:
        """Get rent listings for area code."""
        params = {}
        if min_beds:
            params["min_beds"] = min_beds
        if max_beds:
            params["max_beds"] = max_beds
        if property_type:
            params["property_type"] = property_type
        
        if self.use_api:
            data = await self._request("GET", f"/v1/area_codes/{area_code}/rent/listings", params)
            if data:
                return data
        
        # Return mock listings summary
        summary = _get_mock_summary(area_code)
        return {
            "area_code": area_code,
            "listings_count": summary["listing_count"],
            "stats": {
                "median_rent": summary["median_rent"],
                "avg_rent": summary["avg_rent"],
                "min_rent": summary["min_rent"],
                "max_rent": summary["max_rent"],
            },
        }
    
    async def get_sale_listings(
        self,
        area_code: str,
        min_beds: Optional[int] = None,
        max_beds: Optional[int] = None,
        property_type: Optional[str] = None,
    ) -> dict:
        """Get sale listings for area code."""
        params = {}
        if min_beds:
            params["min_beds"] = min_beds
        if max_beds:
            params["max_beds"] = max_beds
        if property_type:
            params["property_type"] = property_type
        
        if self.use_api:
            data = await self._request("GET", f"/v1/area_codes/{area_code}/sale/listings", params)
            if data:
                return data
        
        # Return mock sale listings
        return {
            "area_code": area_code,
            "listings": [
                {
                    "id": "1",
                    "title": f"Modern 2 Bed Apartment in {area_code}",
                    "price": 450000,
                    "type": "sale",
                    "location": f"{area_code}, London",
                    "beds": 2,
                    "baths": 1,
                    "sqft": 850,
                    "url": "https://rightmove.co.uk/property-1",
                },
                {
                    "id": "2",
                    "title": f"Luxury 3 Bed Flat in {area_code}",
                    "price": 675000,
                    "type": "sale",
                    "location": f"{area_code}, London",
                    "beds": 3,
                    "baths": 2,
                    "sqft": 1200,
                    "url": "https://rightmove.co.uk/property-2",
                },
            ],
            "stats": {
                "median_price": 550000,
                "avg_price": 575000,
                "min_price": 350000,
                "max_price": 850000,
            },
        }
    
    async def get_district_demand(
        self,
        district: str,
        period: Optional[str] = None,
    ) -> dict:
        """Get demand data for district."""
        params = {}
        if period:
            params["period"] = period
        
        if self.use_api:
            data = await self._request("GET", f"/district/{district}/rent/demand", params)
            if data:
                return data
        
        return _get_mock_demand(district)
    
    async def get_district_growth(self, district: str) -> dict:
        """Get growth data for district."""
        if self.use_api:
            data = await self._request("GET", f"/district/{district}/growth")
            if data:
                return data
        
        return _get_mock_growth(district)
    
    async def get_neighbors(
        self,
        area_code: str,
        k: int = 5,
        radius_km: Optional[float] = None,
    ) -> list[Neighbor]:
        """Get neighboring areas."""
        if self.use_api:
            params = {"k": k}
            if radius_km:
                params["radius_km"] = radius_km
            data = await self._request("GET", f"/area_codes/{area_code}/neighbors", params)
            if data and "neighbors" in data:
                return [Neighbor(**n) for n in data["neighbors"]]
        
        # Fallback to mock
        mock_neighbors = _get_mock_neighbors(area_code, k)
        return [Neighbor(**n) for n in mock_neighbors]


# Singleton client
_client: Optional[ScanSanClient] = None


def get_scansan_client() -> ScanSanClient:
    """Get singleton ScanSan client."""
    global _client
    if _client is None:
        _client = ScanSanClient()
    return _client
