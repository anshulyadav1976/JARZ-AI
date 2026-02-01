"""ScanSan API client - Always uses real API, no mock fallback.
API responses are cached via backend/app/cache.py (persisted to backend/cache.json)
so repeated calls and backend restarts stay fast for demos.
"""
import asyncio
import hashlib
from typing import Any, Optional
import re
import httpx
from .config import get_settings
from .schemas import ResolvedLocation, Neighbor
from . import cache as persistent_cache


def _scansan_cache_key(endpoint: str, params: Optional[dict] = None) -> str:
    """Stable cache key for ScanSan request (endpoint + params)."""
    key_data = f"{endpoint}:{sorted((params or {}).items())}"
    return "scansan:" + hashlib.md5(key_data.encode()).hexdigest()


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
            # Offline mode: return None and let higher-level helpers provide fallbacks.
            print("[SCANSAN] API disabled (USE_SCANSAN=false). Using offline fallbacks where possible.")
            return None
        
        # Check persistent cache (API response – survives restarts, makes demos fast)
        settings = get_settings()
        cache_key = _scansan_cache_key(endpoint, params=params) if settings.enable_cache else None
        if cache_key:
            cached = persistent_cache.get(cache_key)
            if cached is not None:
                print(f"[SCANSAN] Cache hit for {endpoint}")
                return cached

        client = await self._get_client()
        endpoint = self._normalize_endpoint(endpoint)
        last_error = None

        for attempt in range(retries):
            try:
                if method.upper() == "GET":
                    response = await client.get(endpoint, params=params)
                else:
                    response = await client.post(endpoint, json=params)

                response.raise_for_status()
                data = response.json()
                if cache_key:
                    persistent_cache.set_(cache_key, data, ttl_seconds=settings.cache_ttl_seconds)
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

    def _normalize_endpoint(self, endpoint: str) -> str:
        """
        Normalize endpoint path so we don't accidentally hit /v1/v1/... .

        The ScanSan docs use paths like `/v1/...` (see:
        `https://docs.scansan.com/v1/docs#tag/area-code/GET/v1/area_codes/{area_code}/summary`).

        In this repo, `SCANSAN_BASE_URL` may be configured as either:
        - `https://api.scansan.com`
        - `https://api.scansan.com/v1`

        We accept either, and ensure the final request path is correct.
        """
        base = (self.base_url or "").rstrip("/")
        ep = (endpoint or "").strip()
        if not ep.startswith("/"):
            ep = "/" + ep

        # If base already ends with /v1 and endpoint also starts with /v1/, strip one.
        if base.endswith("/v1") and ep.startswith("/v1/"):
            return ep[len("/v1"):]

        return ep
    
    async def search_area_codes(self, query: str) -> Optional[ResolvedLocation]:
        """Search for area codes matching query."""
        print(f"[SCANSAN] GET /v1/area_codes/search?area_name={query}")
        data = await self._request("GET", "/v1/area_codes/search", {"area_name": query})

        # Offline fallback: if ScanSan is disabled, still resolve common UK postcodes/outward codes
        if data is None and not self.use_api:
            raw = (query or "").strip().upper()
            if not raw:
                return None

            # Prefer outward code if full postcode supplied (e.g. "SW1A 2TL" -> "SW1A")
            outward = raw.split()[0]

            # Very lightweight outward-code validation:
            # Examples: NW1, E14, SW1A, EC2A, W1, SE1
            if re.fullmatch(r"[A-Z]{1,2}\d{1,2}[A-Z]?", outward):
                return ResolvedLocation(
                    area_code=outward,
                    area_code_district=outward,
                    display_name=outward,
                    lat=None,
                    lon=None,
                )
        
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

        # Offline fallback
        if data is None and not self.use_api:
            return {
                "median_rent": None,
                "avg_rent": None,
                "listing_count": None,
            }
        
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
        additional_data: bool = False,
    ) -> Optional[dict]:
        """Get rental demand data for district."""
        params = {}
        if period:
            params["period"] = period
        if additional_data:
            params["additional_data"] = additional_data

        print(f"[SCANSAN] GET /v1/district/{district}/rent/demand")
        data = await self._request("GET", f"/v1/district/{district}/rent/demand", params or None)
        
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
    
    async def get_crime_summary(self, area_code: str) -> Optional[dict]:
        """Get crime summary for area code."""
        print(f"[SCANSAN] GET /v1/area_codes/{area_code}/crime/summary")
        data = await self._request("GET", f"/v1/area_codes/{area_code}/crime/summary")
        
        if data and "data" in data:
            print(f"[SCANSAN] Crime summary found for {area_code}")
            return data
        
        print(f"[SCANSAN] No crime summary found for {area_code}")
        return None
    
    async def get_crime_detail(self, area_code: str) -> Optional[dict]:
        """Get detailed crime data for area code."""
        print(f"[SCANSAN] GET /v1/area_codes/{area_code}/crime/detail")
        data = await self._request("GET", f"/v1/area_codes/{area_code}/crime/detail")
        
        if data and "data" in data:
            print(f"[SCANSAN] Crime detail found for {area_code}: {len(data['data'])} incidents")
            return data
        
        print(f"[SCANSAN] No crime detail found for {area_code}")
        return None
    
    async def get_sale_demand(
        self,
        district: str,
        period: Optional[str] = None,
        additional_data: bool = False,
    ) -> Optional[dict]:
        """Get sales demand data for district."""
        params = {}
        if period:
            params["period"] = period
        if additional_data:
            params["additional_data"] = additional_data
        
        print(f"[SCANSAN] GET /v1/district/{district}/sale/demand")
        data = await self._request("GET", f"/v1/district/{district}/sale/demand", params)
        
        if data and "data" in data:
            print(f"[SCANSAN] Sale demand data found for {district}")
            return data
        
        print(f"[SCANSAN] No sale demand data found for {district}")
        return None
    
    async def get_sale_history(self, postcode: str) -> Optional[dict]:
        """Get sale history for properties on given postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/sale/history")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/sale/history")
        
        if data and "data" in data:
            print(f"[SCANSAN] Sale history found: {len(data['data'])} properties")
            return data
        
        print(f"[SCANSAN] No sale history found for {postcode}")
        return None
    
    async def get_classification(self, postcode: str) -> Optional[dict]:
        """Get classification data for postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/classification")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/classification")
        
        if data and "data" in data:
            print(f"[SCANSAN] Classification data found for {postcode}")
            return data
        
        print(f"[SCANSAN] No classification data found for {postcode}")
        return None
    
    async def get_regeneration(self, postcode: str) -> Optional[dict]:
        """Get regeneration data for postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/regeneration")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/regeneration")
        
        if data and "data" in data:
            print(f"[SCANSAN] Regeneration data found for {postcode}")
            return data
        
        print(f"[SCANSAN] No regeneration data found for {postcode}")
        return None
    
    async def get_current_valuations(self, postcode: str) -> Optional[dict]:
        """Get current valuations for properties in postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/valuations/current")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/valuations/current")
        
        if data and "data" in data:
            print(f"[SCANSAN] Current valuations found: {len(data['data'])} properties")
            return data
        
        print(f"[SCANSAN] No current valuations found for {postcode}")
        return None
    
    async def get_historical_valuations(self, postcode: str) -> Optional[dict]:
        """Get historical valuations for properties in postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/valuations/historical")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/valuations/historical")
        
        if data and "data" in data:
            print(f"[SCANSAN] Historical valuations found: {len(data['data'])} properties")
            return data
        
        print(f"[SCANSAN] No historical valuations found for {postcode}")
        return None
    
    async def get_census(self, postcode: str) -> Optional[dict]:
        """Get census data for postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/census")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/census")
        
        if data and "data" in data:
            print(f"[SCANSAN] Census data found for {postcode}")
            return data
        
        print(f"[SCANSAN] No census data found for {postcode}")
        return None
    
    async def get_amenities(self, postcode: str) -> Optional[dict]:
        """Get nearest amenities for postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/amenities")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/amenities")
        
        if data and "data" in data:
            print(f"[SCANSAN] Amenities data found for {postcode}")
            return data
        
        print(f"[SCANSAN] No amenities data found for {postcode}")
        return None
    
    async def get_lha(self, postcode: str) -> Optional[dict]:
        """Get Local Housing Allowance (LHA) data for postcode."""
        clean_postcode = postcode.replace(" ", "").upper()
        print(f"[SCANSAN] GET /v1/postcode/{clean_postcode}/lha")
        data = await self._request("GET", f"/v1/postcode/{clean_postcode}/lha")
        
        if data and "data" in data:
            print(f"[SCANSAN] LHA data found for {postcode}")
            return data
        
        print(f"[SCANSAN] No LHA data found for {postcode}")
        return None
    
    async def get_planning_permission(self, uprn: str) -> Optional[dict]:
        """Get planning permission data for property by UPRN."""
        print(f"[SCANSAN] GET /v1/property/{uprn}/planning_permission")
        data = await self._request("GET", f"/v1/property/{uprn}/planning_permission")
        
        if data and "data" in data:
            print(f"[SCANSAN] Planning permission data found for UPRN {uprn}")
            return data
        
        print(f"[SCANSAN] No planning permission data found for UPRN {uprn}")
        return None
    
    async def get_property_addresses(self, uprn: str) -> Optional[dict]:
        """Get addresses for property by UPRN."""
        print(f"[SCANSAN] GET /v1/property/{uprn}/addresses")
        data = await self._request("GET", f"/v1/property/{uprn}/addresses")
        
        if data and "data" in data:
            print(f"[SCANSAN] Address data found for UPRN {uprn}")
            return data
        
        print(f"[SCANSAN] No address data found for UPRN {uprn}")
        return None


# Singleton client
_client: Optional[ScanSanClient] = None


def get_scansan_client() -> ScanSanClient:
    """Get singleton ScanSan client."""
    global _client
    if _client is None:
        _client = ScanSanClient()
    return _client
