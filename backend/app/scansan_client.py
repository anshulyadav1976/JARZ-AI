"""ScanSan API client - Always uses real API, no mock fallback."""
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
# ScanSan Client Class
# ============================================================================

class ScanSanClient:
    """Async client for ScanSan API - Always uses real API."""
    
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
                    "X-Auth-Token": self.api_key,
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
            print(f"[SCANSAN] ERROR: API disabled. Set USE_SCANSAN=true in .env")
            return None
        
        # Check cache
        cache_key = _cache_key(endpoint, params=params)
        cached = _get_cached(cache_key)
        if cached is not None:
            print(f"[SCANSAN] Cache hit for {endpoint}")
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
        
        print(f"[SCANSAN] API error after {retries} attempts: {last_error}")
        return None
    
    async def search_area_codes(self, query: str) -> Optional[ResolvedLocation]:
        """Search for area codes matching query."""
        print(f"[SCANSAN] GET /v1/area_codes/search?area_name={query}")
        data = await self._request("GET", "/v1/area_codes/search", {"area_name": query})
        
        if data and "data" in data and len(data["data"]) > 0:
            # data[0] is an array of area code objects
            first_array = data["data"][0]
            if isinstance(first_array, list) and len(first_array) > 0:
                result = first_array[0]
                area_code_data = result.get("area_code", {})
                district = area_code_data.get("area_code_district", "")
                area_code_list = area_code_data.get("area_code_list", [])
                first_area_code = area_code_list[0] if area_code_list else query.upper()
                
                ward = result.get("ward", [])
                ward_name = ward[0] if ward else query
                
                print(f"[SCANSAN] Found area: {ward_name} - District: {district}, First code: {first_area_code}")
                
                return ResolvedLocation(
                    area_code=district,  # Use district (e.g., UB8) as the area code
                    area_code_district=district,
                    display_name=f"{ward_name}, {district}",
                    lat=None,
                    lon=None,
                )
        
        print(f"[SCANSAN] No results found for: {query}")
        print(f"[SCANSAN] Response: {data}")
        return None
    
    async def get_area_summary(self, area_code: str) -> Optional[dict]:
        """Get summary statistics for area code."""
        print(f"[SCANSAN] GET /v1/area_codes/{area_code}/summary")
        data = await self._request("GET", f"/v1/area_codes/{area_code}/summary")
        
        if data and "data" in data:
            print(f"[SCANSAN] Summary data found for {area_code}")
            print(f"[SCANSAN] Summary: {data['data']}")
            return data
        
        print(f"[SCANSAN] No summary data found for {area_code}")
        return None
    
    async def get_rent_listings(
        self,
        area_code: str,
        min_beds: Optional[int] = None,
        max_beds: Optional[int] = None,
        property_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Get rent listings for area code."""
        params = {}
        if min_beds:
            params["min_beds"] = min_beds
        if max_beds:
            params["max_beds"] = max_beds
        if property_type:
            params["property_type"] = property_type
        
        print(f"[SCANSAN] GET /v1/area_codes/{area_code}/rent/listings")
        data = await self._request("GET", f"/v1/area_codes/{area_code}/rent/listings", params)
        
        if data and "data" in data:
            listings = data["data"].get("rent_listings", [])
            print(f"[SCANSAN] Rent listings found for {area_code}: {len(listings)} listings")
            return data
        
        print(f"[SCANSAN] No rent listings found for {area_code}")
        return None
    
    async def get_sale_listings(
        self,
        area_code: str,
        min_beds: Optional[int] = None,
        max_beds: Optional[int] = None,
        property_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Get sale listings for area code."""
        params = {}
        if min_beds:
            params["min_beds"] = min_beds
        if max_beds:
            params["max_beds"] = max_beds
        if property_type:
            params["property_type"] = property_type
        
        print(f"[SCANSAN] GET /v1/area_codes/{area_code}/sale/listings")
        data = await self._request("GET", f"/v1/area_codes/{area_code}/sale/listings", params)
        
        if data and "data" in data:
            listings = data["data"].get("sale_listings", [])
            print(f"[SCANSAN] Sale listings found for {area_code}: {len(listings)} listings")
            return data
        
        print(f"[SCANSAN] No sale listings found for {area_code}")
        return None
    
    async def get_district_demand(
        self,
        district: str,
        period: Optional[str] = None,
    ) -> Optional[dict]:
        """Get demand data for district."""
        params = {}
        if period:
            params["period"] = period
        
        print(f"[SCANSAN] GET /v1/district/{district}/rent/demand")
        data = await self._request("GET", f"/v1/district/{district}/rent/demand", params)
        
        if data and "data" in data:
            print(f"[SCANSAN] Demand data found for {district}")
            print(f"[SCANSAN] Demand info: {data.get('data', {}).get('rental_demand', [])}")
            return data
        
        print(f"[SCANSAN] No demand data found for {district}")
        return None
    
    async def get_district_growth(self, district: str) -> Optional[dict]:
        """Get growth data for district."""
        print(f"[SCANSAN] GET /v1/district/{district}/growth")
        data = await self._request("GET", f"/v1/district/{district}/growth")
        
        if data and "data" in data:
            print(f"[SCANSAN] Growth data found for {district}")
            monthly = data.get('data', {}).get('monthly_data', [])
            print(f"[SCANSAN] Growth: {len(monthly)} months of data")
            return data
        
        print(f"[SCANSAN] No growth data found for {district}")
        return None
    
    async def get_neighbors(
        self,
        area_code: str,
        k: int = 5,
        radius_km: Optional[float] = None,
    ) -> list[Neighbor]:
        """Get neighboring areas.
        
        Note: ScanSan API doesn't have a dedicated neighbors endpoint.
        This method returns an empty list.
        """
        print(f"[SCANSAN] WARNING: neighbors endpoint not available in ScanSan API")
        print(f"[SCANSAN] Returning empty neighbors list for {area_code}")
        return []
    
    async def get_postcode_addresses(self, postcode: str) -> Optional[dict]:
        """Get addresses for a postcode."""
        # Clean postcode (remove spaces)
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/addresses")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/addresses")
        
        if data and "data" in data:
            property_addresses = data["data"].get("property_address", [])
            if len(property_addresses) > 0:
                print(f"[SCANSAN] Found {len(property_addresses)} addresses")
                return data
        
        print(f"[SCANSAN] No addresses found for {postcode}")
        return None
    
    async def get_property_energy_performance(self, uprn: str) -> Optional[dict]:
        """Get energy performance data for a property by UPRN."""
        print(f"[SCANSAN] GET /v1/property/{uprn}/energy/performance")
        data = await self._request("GET", f"/v1/property/{uprn}/energy/performance")
        
        if data and "data" in data and len(data["data"]) > 0:
            # Return first property data
            print(f"[SCANSAN] Energy performance data found")
            print(f"[SCANSAN] Energy data: {data}")
            return data["data"][0]
        
        print(f"[SCANSAN] No energy performance data found")
        return None
    
    async def get_postcode_energy_performance(self, postcode: str) -> Optional[dict]:
        """Get energy performance data for a postcode (returns first property)."""
        # Clean postcode (remove spaces)
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/energy/performance")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/energy/performance")
        
        if data and "data" in data and len(data["data"]) > 0:
            # Return first property data
            print(f"[SCANSAN] Energy performance data found ({len(data['data'])} properties)")
            print(f"[SCANSAN] Energy data: {data['data'][0]}")
            return data["data"][0]
        
        print(f"[SCANSAN] No energy performance data found")
        return None
    
    async def get_uprn_from_postcode(self, postcode: str) -> Optional[str]:
        """Get UPRN from postcode by fetching addresses."""
        print(f"[SCANSAN] Looking up UPRN for postcode: {postcode}")
        addresses_data = await self.get_postcode_addresses(postcode)
        
        if addresses_data and "data" in addresses_data:
            property_addresses = addresses_data["data"].get("property_address", [])
            if len(property_addresses) > 0:
                # Return first address UPRN
                uprn = str(property_addresses[0].get("uprn"))
                address = property_addresses[0].get("property_address", postcode)
                print(f"[SCANSAN] Using first address: {address}")
                print(f"[SCANSAN] UPRN: {uprn}")
                return uprn
        
        print(f"[SCANSAN] No UPRN found for postcode: {postcode}")
        return None


# Singleton client
_client: Optional[ScanSanClient] = None


def get_scansan_client() -> ScanSanClient:
    """Get singleton ScanSan client."""
    global _client
    if _client is None:
        _client = ScanSanClient()
    return _client
