"""
ScanSan API Data Fetcher for AI Training
Fetches all UK DISTRICTS (not full postcodes) and their properties.
Districts (e.g., NW1, SW6, E14) have much better data coverage than full postcodes.
Includes temporal growth data for time-series modeling.
Stores results in a Parquet file for ML training.
"""

import http.client
import urllib.parse
import json
import time
from pathlib import Path
from typing import Optional
import pandas as pd
from tqdm import tqdm

# ============ CONFIGURATION ============
API_KEY = "80f47a79-ced9-422a-9ffb-435750329429"
BASE_HOST = "api.scansan.com"
OUTDIR = Path("data/raw")
OUTDIR.mkdir(parents=True, exist_ok=True)
PARQUET_PATH = OUTDIR / "district_training_data.parquet"
GROWTH_PARQUET_PATH = OUTDIR / "district_growth_timeseries.parquet"
REQUEST_DELAY = 0.5  # seconds between requests - increased to avoid rate limits


# ============ API HELPER FUNCTIONS ============
def api_get(path: str, retries: int = 3) -> dict:
    """Make GET request to ScanSan API with retry logic."""
    headers = {"X-Auth-Token": API_KEY}
    for attempt in range(retries):
        try:
            conn = http.client.HTTPSConnection(BASE_HOST, timeout=30)
            conn.request("GET", path, headers=headers)
            res = conn.getresponse()
            text = res.read().decode("utf-8")
            conn.close()
            if res.status == 200:
                return {"status": res.status, "data": json.loads(text)}
            elif res.status == 404:
                return {"status": res.status, "data": None, "error": "Not found"}
            else:
                return {"status": res.status, "data": None, "error": text}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return {"status": -1, "data": None, "error": str(e)}
    return {"status": -1, "data": None, "error": "Max retries exceeded"}


def search_area_codes(area_name: str) -> list:
    """Search for area codes by area name and extract all postcodes."""
    encoded = urllib.parse.quote(area_name)
    result = api_get(f"/v1/area_codes/search?area_name={encoded}")
    
    if result["status"] != 200 or not result["data"]:
        return []
    
    codes = set()
    data = result["data"].get("data", [])
    for group in data:
        if isinstance(group, list):
            for item in group:
                ac_info = item.get("area_code", {})
                ac_list = ac_info.get("area_code_list", [])
                for code in ac_list:
                    codes.add(code)
                # Also add the district
                district = ac_info.get("area_code_district")
                if district:
                    codes.add(district)
    return sorted(codes)


def get_all_uk_districts() -> list:
    """
    Get a comprehensive list of UK postcode DISTRICTS (outward codes).
    These are the first part of UK postcodes (e.g., NW1, SW6, E14).
    Districts have much better API data coverage than full postcodes.
    """
    districts = []
    
    # London districts - most complete data
    london = {
        "E": range(1, 21), "EC": range(1, 5), "N": range(1, 23), "NW": range(1, 12),
        "SE": range(1, 29), "SW": range(1, 21), "W": range(1, 15), "WC": range(1, 3),
    }
    
    # Major cities - good data coverage
    major_cities = {
        "B": range(1, 50),      # Birmingham
        "M": range(1, 35),      # Manchester
        "L": range(1, 35),      # Liverpool
        "LS": range(1, 28),     # Leeds
        "S": range(1, 45),      # Sheffield
        "BS": range(1, 40),     # Bristol
        "NG": range(1, 32),     # Nottingham
        "NE": range(1, 40),     # Newcastle
        "G": range(1, 70),      # Glasgow
        "EH": range(1, 50),     # Edinburgh
        "CF": range(1, 48),     # Cardiff
        "BN": range(1, 42),     # Brighton
        "SO": range(14, 50),    # Southampton
        "PO": range(1, 38),     # Portsmouth
        "LE": range(1, 65),     # Leicester
        "CV": range(1, 47),     # Coventry
        "CB": range(1, 24),     # Cambridge
        "OX": range(1, 44),     # Oxford
        "RG": range(1, 42),     # Reading
        "MK": range(1, 45),     # Milton Keynes
    }
    
    # Other important areas
    other_areas = {
        "GU": range(1, 35),     # Guildford area
        "KT": range(1, 24),     # Kingston area
        "TW": range(1, 20),     # Twickenham area
        "CR": range(0, 9),      # Croydon
        "SM": range(1, 8),      # Sutton
        "HA": range(0, 10),     # Harrow
        "UB": range(1, 11),     # Uxbridge
        "EN": range(1, 12),     # Enfield
        "IG": range(1, 12),     # Ilford
        "RM": range(1, 20),     # Romford
        "DA": range(1, 18),     # Dartford
        "BR": range(1, 9),      # Bromley
        "HP": range(1, 27),     # Hemel Hempstead
        "AL": range(1, 11),     # St Albans
        "WD": range(1, 25),     # Watford
        "LU": range(1, 8),      # Luton
        "SL": range(0, 10),     # Slough
        "TN": range(1, 40),     # Tunbridge Wells
        "ME": range(1, 20),     # Medway
        "CT": range(1, 21),     # Canterbury
        "BH": range(1, 25),     # Bournemouth
        "EX": range(1, 39),     # Exeter
        "PL": range(1, 35),     # Plymouth
        "BA": range(1, 22),     # Bath
        "GL": range(1, 54),     # Gloucester
        "WR": range(1, 15),     # Worcester
        "DY": range(1, 14),     # Dudley
        "WV": range(1, 16),     # Wolverhampton
        "WS": range(1, 15),     # Walsall
        "ST": range(1, 21),     # Stoke-on-Trent
        "DE": range(1, 75),     # Derby
        "NN": range(1, 30),     # Northampton
        "PE": range(1, 37),     # Peterborough
        "IP": range(1, 33),     # Ipswich
        "NR": range(1, 35),     # Norwich
        "HU": range(1, 20),     # Hull
        "DN": range(1, 42),     # Doncaster
        "HD": range(1, 10),     # Huddersfield
        "BD": range(1, 24),     # Bradford
        "HX": range(1, 8),      # Halifax
        "WF": range(1, 17),     # Wakefield
        "YO": range(1, 62),     # York
        "HG": range(1, 6),      # Harrogate
        "DL": range(1, 17),     # Darlington
        "TS": range(1, 29),     # Teesside
        "SR": range(1, 9),      # Sunderland
        "DH": range(1, 10),     # Durham
        "CA": range(1, 28),     # Carlisle
        "LA": range(1, 23),     # Lancaster
        "PR": range(1, 26),     # Preston
        "BB": range(1, 19),     # Blackburn
        "BL": range(1, 10),     # Bolton
        "OL": range(1, 16),     # Oldham
        "SK": range(1, 23),     # Stockport
        "WA": range(1, 16),     # Warrington
        "WN": range(1, 9),      # Wigan
        "CH": range(1, 66),     # Chester
        "CW": range(1, 13),     # Crewe
        "SY": range(1, 25),     # Shrewsbury
        "TF": range(1, 14),     # Telford
        "SA": range(1, 73),     # Swansea
        "NP": range(1, 44),     # Newport
        "LL": range(11, 78),    # Llandudno
        "LD": range(1, 9),      # Llandrindod Wells
        # Scotland
        "AB": range(10, 56),    # Aberdeen
        "DD": range(1, 12),     # Dundee
        "FK": range(1, 21),     # Falkirk
        "KY": range(1, 16),     # Kirkcaldy
        "ML": range(1, 12),     # Motherwell
        "PA": range(1, 78),     # Paisley
        "KA": range(1, 30),     # Kilmarnock
        "DG": range(1, 16),     # Dumfries
        "TD": range(1, 15),     # Galashiels
        "IV": range(1, 63),     # Inverness
        "PH": range(1, 50),     # Perth
        # Northern Ireland
        "BT": range(1, 82),     # Belfast
    }
    
    # Combine all
    for area_dict in [london, major_cities, other_areas]:
        for area, num_range in area_dict.items():
            for num in num_range:
                districts.append(f"{area}{num}")
    
    return districts


# ============ DATA FETCHING FUNCTIONS ============
def fetch_area_code_summary(area_code: str) -> dict:
    """Fetch summary data for an area code."""
    enc = urllib.parse.quote(area_code, safe="")
    return api_get(f"/v1/area_codes/{enc}/summary")


def fetch_crime_summary(area_code: str) -> dict:
    """Fetch crime summary for an area code."""
    enc = urllib.parse.quote(area_code, safe="")
    return api_get(f"/v1/area_codes/{enc}/crime/summary")


def fetch_crime_detail(area_code: str) -> dict:
    """Fetch crime detail for an area code."""
    enc = urllib.parse.quote(area_code, safe="")
    return api_get(f"/v1/area_codes/{enc}/crime/detail")


def fetch_rent_listings(area_code: str) -> dict:
    """Fetch rent listings for an area code."""
    enc = urllib.parse.quote(area_code, safe="")
    return api_get(f"/v1/area_codes/{enc}/rent/listings")


def fetch_sale_listings(area_code: str) -> dict:
    """Fetch sale listings for an area code."""
    enc = urllib.parse.quote(area_code, safe="")
    return api_get(f"/v1/area_codes/{enc}/sale/listings")


def fetch_district_growth(district: str) -> dict:
    """Fetch growth data for a district."""
    enc = urllib.parse.quote(district, safe="")
    return api_get(f"/v1/district/{enc}/growth")


def fetch_district_rent_demand(district: str) -> dict:
    """Fetch rental demand data for a district."""
    enc = urllib.parse.quote(district, safe="")
    return api_get(f"/v1/district/{enc}/rent/demand?additional_data=true")


def fetch_district_sale_demand(district: str) -> dict:
    """Fetch sales demand data for a district."""
    enc = urllib.parse.quote(district, safe="")
    return api_get(f"/v1/district/{enc}/sale/demand?additional_data=true")


def fetch_postcode_data(postcode: str) -> dict:
    """Fetch all postcode-level data (classification, census, amenities, etc.)."""
    enc = urllib.parse.quote(postcode, safe="")
    endpoints = {
        "classification": f"/v1/postcode/{enc}/classification",
        "census": f"/v1/postcode/{enc}/census",
        "amenities": f"/v1/postcode/{enc}/amenities",
        "valuations_current": f"/v1/postcode/{enc}/valuations/current",
        "lha": f"/v1/postcode/{enc}/lha",
        "regeneration": f"/v1/postcode/{enc}/regeneration",
        "energy_performance": f"/v1/postcode/{enc}/energy/performance",
    }
    
    results = {}
    for key, path in endpoints.items():
        results[key] = api_get(path)
        time.sleep(REQUEST_DELAY)
    return results


# ============ DATA FLATTENING FUNCTIONS ============
def flatten_summary(district: str, summary_resp: dict) -> dict:
    """Flatten summary response into a flat dictionary."""
    row = {}
    
    if summary_resp["status"] != 200 or not summary_resp.get("data"):
        return row
    
    data = summary_resp["data"]
    row["area_code_type"] = data.get("area_code_type")
    
    summary_data = data.get("data", [])
    if summary_data and len(summary_data) > 0:
        s = summary_data[0]
        row["total_properties"] = s.get("total_properties")
        row["total_properties_sold_5yrs"] = s.get("total_properties_sold_in_last_5yrs")
        
        # Price ranges
        sold_range = s.get("sold_price_range_in_last_5yrs", [])
        if sold_range and len(sold_range) >= 2:
            row["sold_price_min_5yrs"] = sold_range[0]
            row["sold_price_max_5yrs"] = sold_range[1]
        
        val_range = s.get("current_valuation_range", [])
        if val_range and len(val_range) >= 2:
            row["valuation_min"] = val_range[0]
            row["valuation_max"] = val_range[1]
        
        row["current_rent_listings"] = s.get("current_rent_listings")
        rent_range = s.get("current_rent_listings_pcm_range", [])
        if rent_range and len(rent_range) >= 2:
            row["rent_pcm_min"] = rent_range[0]
            row["rent_pcm_max"] = rent_range[1]
        
        row["current_sale_listings"] = s.get("current_sale_listings")
        sale_range = s.get("current_sale_listings_price_range", [])
        if sale_range and len(sale_range) >= 2:
            row["sale_price_min"] = sale_range[0]
            row["sale_price_max"] = sale_range[1]
    
    return row


def flatten_crime_summary(crime_resp: dict) -> dict:
    """Flatten crime summary into metrics."""
    row = {}
    
    if crime_resp["status"] != 200 or not crime_resp.get("data"):
        return row
    
    data = crime_resp["data"]
    row["crime_total_incidents"] = data.get("total_incidents", 0)
    
    # Count by category
    categories = data.get("category_counts", [])
    for cat in categories:
        cat_name = cat.get("category", "unknown").replace(" ", "_").replace("-", "_").lower()
        row[f"crime_{cat_name}"] = cat.get("count", 0)
    
    return row


def flatten_rent_listings(rent_resp: dict) -> dict:
    """Flatten rent listings into aggregate metrics."""
    row = {}
    
    if rent_resp["status"] != 200 or not rent_resp.get("data"):
        return row
    
    data = rent_resp["data"].get("data", {})
    listings = data.get("rent_listings", [])
    
    if listings:
        row["rent_listing_count"] = len(listings)
        rents = [l.get("rent_pcm", 0) for l in listings if l.get("rent_pcm")]
        if rents:
            row["rent_avg_pcm"] = sum(rents) / len(rents)
            row["rent_median_pcm"] = sorted(rents)[len(rents) // 2]
        
        bedrooms = [l.get("bedrooms", 0) for l in listings if l.get("bedrooms")]
        if bedrooms:
            row["rent_avg_bedrooms"] = sum(bedrooms) / len(bedrooms)
    
    return row


def flatten_sale_listings(sale_resp: dict) -> dict:
    """Flatten sale listings into aggregate metrics."""
    row = {}
    
    if sale_resp["status"] != 200 or not sale_resp.get("data"):
        return row
    
    data = sale_resp["data"].get("data", {})
    listings = data.get("sale_listings", [])
    
    if listings:
        row["sale_listing_count"] = len(listings)
        prices = [l.get("sale_price", 0) for l in listings if l.get("sale_price")]
        if prices:
            row["sale_avg_price"] = sum(prices) / len(prices)
            row["sale_median_price"] = sorted(prices)[len(prices) // 2]
        
        bedrooms = [l.get("bedrooms", 0) for l in listings if l.get("bedrooms")]
        if bedrooms:
            row["sale_avg_bedrooms"] = sum(bedrooms) / len(bedrooms)
    
    return row


def flatten_district_growth(growth_resp: dict) -> tuple[dict, list]:
    """
    Flatten district growth data into:
    - summary stats (dict) for main features
    - time series (list of dicts) for temporal modeling
    """
    row = {}
    time_series = []
    
    if growth_resp["status"] != 200 or not growth_resp.get("data"):
        return row, time_series
    
    data = growth_resp["data"].get("data", {})
    
    # Get yearly growth summary
    yearly = data.get("yearly_data", [])
    if yearly:
        latest = yearly[-1] if yearly else {}
        row["growth_latest_year"] = latest.get("year")
        row["growth_latest_avg_price"] = latest.get("avg_price")
        row["growth_latest_pct_change"] = latest.get("percentage_change")
        row["growth_latest_transactions"] = latest.get("transactions")
        
        # Calculate multi-year trends
        if len(yearly) >= 2:
            first = yearly[0]
            row["growth_5yr_start_price"] = first.get("avg_price")
            if first.get("avg_price") and latest.get("avg_price"):
                row["growth_5yr_total_pct"] = ((latest["avg_price"] - first["avg_price"]) / first["avg_price"]) * 100
        
        # Average yearly change
        pct_changes = [y.get("percentage_change") for y in yearly if y.get("percentage_change") is not None]
        if pct_changes:
            row["growth_avg_yearly_pct"] = sum(pct_changes) / len(pct_changes)
    
    # Get monthly data for time series
    monthly = data.get("monthly_data", [])
    for m in monthly:
        ts_row = {
            "year": m.get("year"),
            "month": m.get("month"),
            "avg_price": m.get("avg_price"),
            "pct_change": m.get("percentage_change"),
            "transactions": m.get("transactions"),
        }
        time_series.append(ts_row)
    
    # Monthly summary stats
    if monthly:
        pct_changes = [m.get("percentage_change", 0) for m in monthly if m.get("percentage_change") is not None]
        if pct_changes:
            row["growth_avg_monthly_pct"] = sum(pct_changes) / len(pct_changes)
            row["growth_monthly_volatility"] = (sum((p - row["growth_avg_monthly_pct"])**2 for p in pct_changes) / len(pct_changes)) ** 0.5
    
    return row, time_series


def flatten_rent_demand(demand_resp: dict) -> dict:
    """Flatten rental demand data."""
    row = {}
    
    if demand_resp["status"] != 200 or not demand_resp.get("data"):
        return row
    
    data = demand_resp["data"].get("data", {})
    demand = data.get("rental_demand", [])
    
    if demand:
        d = demand[0]
        row["rent_demand_total_props"] = d.get("total_properties_for_rent")
        row["rent_demand_mean_pcm"] = d.get("mean_rent_pcm")
        row["rent_demand_median_pcm"] = d.get("median_rent_pcm")
        row["rent_demand_avg_transactions"] = d.get("average_transactions_pcm")
        row["rent_demand_months_inventory"] = d.get("months_of_inventory")
        row["rent_demand_days_on_market"] = d.get("days_on_market")
        row["rent_demand_market_rating"] = d.get("market_rating")
    
    return row


def flatten_sale_demand(demand_resp: dict) -> dict:
    """Flatten sales demand data."""
    row = {}
    
    if demand_resp["status"] != 200 or not demand_resp.get("data"):
        return row
    
    data = demand_resp["data"].get("data", {})
    demand = data.get("sale_demand", [])
    
    if demand:
        d = demand[0]
        row["sale_demand_total_props"] = d.get("total_properties_for_sale")
        row["sale_demand_mean_price"] = d.get("mean_price")
        row["sale_demand_median_price"] = d.get("median_price")
        row["sale_demand_avg_transactions"] = d.get("average_transactions_pcm")
        row["sale_demand_months_inventory"] = d.get("months_of_inventory")
        row["sale_demand_days_on_market"] = d.get("mean_otm_days")
        row["sale_demand_market_rating"] = d.get("market_rating")
    
    return row


# ============ MAIN DATA COLLECTION ============
def fetch_all_data_for_district(district: str) -> tuple[dict, list]:
    """
    Fetch all available data for a single DISTRICT and flatten into one row.
    Returns: (feature_row, growth_time_series)
    
    Note: We fetch at DISTRICT level (e.g., NW1, SW6) not full postcode level,
    because the API has much better data coverage for districts.
    """
    row = {"district": district}
    growth_series = []
    
    # Fetch district summary (using area_codes endpoint with district)
    summary = fetch_area_code_summary(district)
    row.update(flatten_summary(district, summary))
    time.sleep(REQUEST_DELAY)
    
    # Fetch crime summary
    crime = fetch_crime_summary(district)
    row.update(flatten_crime_summary(crime))
    time.sleep(REQUEST_DELAY)
    
    # Fetch rent listings aggregates
    rent = fetch_rent_listings(district)
    row.update(flatten_rent_listings(rent))
    time.sleep(REQUEST_DELAY)
    
    # Fetch sale listings aggregates
    sale = fetch_sale_listings(district)
    row.update(flatten_sale_listings(sale))
    time.sleep(REQUEST_DELAY)
    
    # Fetch district-level growth (TEMPORAL DATA - critical for time-series modeling)
    growth = fetch_district_growth(district)
    growth_features, growth_series = flatten_district_growth(growth)
    row.update(growth_features)
    # Tag time series with district
    for ts in growth_series:
        ts["district"] = district
    time.sleep(REQUEST_DELAY)
    
    # Fetch rental demand metrics
    rent_demand = fetch_district_rent_demand(district)
    row.update(flatten_rent_demand(rent_demand))
    time.sleep(REQUEST_DELAY)
    
    # Fetch sales demand metrics
    sale_demand = fetch_district_sale_demand(district)
    row.update(flatten_sale_demand(sale_demand))
    time.sleep(REQUEST_DELAY)
    
    return row, growth_series


def collect_district_training_data(
    districts: Optional[list] = None,
    limit: Optional[int] = None,
    save_intermediate: bool = True
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Collect training data from the ScanSan API at DISTRICT level.
    
    This produces two datasets:
    1. Cross-sectional features (one row per district) - for spatial modeling
    2. Time-series growth data (multiple rows per district) - for temporal modeling
    
    Args:
        districts: List of districts to fetch (e.g., ['NW1', 'SW1', 'E14'])
        limit: Maximum number of districts to fetch (None for all)
        save_intermediate: Save progress after each batch
    
    Returns:
        Tuple of (features_df, timeseries_df)
    """
    # Use all UK districts if none specified
    if not districts:
        districts = get_all_uk_districts()
    
    if limit:
        districts = districts[:limit]
    
    print(f"\nCollecting data for {len(districts)} districts...")
    
    feature_rows = []
    timeseries_rows = []
    batch_size = 100
    successful = 0
    
    for i, district in enumerate(tqdm(districts, desc="Fetching districts")):
        try:
            row, ts_data = fetch_all_data_for_district(district)
            feature_rows.append(row)
            timeseries_rows.extend(ts_data)
            
            # Count successful fetches (has some data)
            if row.get("total_properties") or row.get("rent_demand_mean_pcm") or row.get("growth_latest_avg_price"):
                successful += 1
            
            # Save intermediate results
            if save_intermediate and (i + 1) % batch_size == 0:
                df_temp = pd.DataFrame(feature_rows)
                df_temp.to_parquet(OUTDIR / "district_training_data_partial.parquet", index=False)
                ts_temp = pd.DataFrame(timeseries_rows)
                if len(ts_temp) > 0:
                    ts_temp.to_parquet(OUTDIR / "district_growth_timeseries_partial.parquet", index=False)
                print(f"\n  Saved intermediate: {len(feature_rows)} districts, {len(timeseries_rows)} time points, {successful} with data")
                
        except Exception as e:
            print(f"\n  Error fetching {district}: {e}")
            feature_rows.append({"district": district, "error": str(e)})
    
    # Create final DataFrames
    df_features = pd.DataFrame(feature_rows)
    df_timeseries = pd.DataFrame(timeseries_rows)
    
    # Clean up data types for features
    numeric_cols = [c for c in df_features.columns if any(x in c for x in 
        ["price", "pcm", "valuation", "properties", "count", "incidents", 
         "bedrooms", "avg", "median", "pct", "inventory", "days", "transactions",
         "volatility", "total", "year", "listings"])]
    
    for col in numeric_cols:
        if col in df_features.columns:
            df_features[col] = pd.to_numeric(df_features[col], errors="coerce")
    
    # Clean up time series types
    if len(df_timeseries) > 0:
        for col in ["year", "month", "avg_price", "pct_change", "transactions"]:
            if col in df_timeseries.columns:
                df_timeseries[col] = pd.to_numeric(df_timeseries[col], errors="coerce")
    
    return df_features, df_timeseries


def save_to_parquet(df: pd.DataFrame, path: Optional[Path] = None, name: str = "features"):
    """Save DataFrame to Parquet file."""
    path = path or PARQUET_PATH
    df.to_parquet(path, index=False, engine="pyarrow")
    print(f"\n✅ Saved {name}: {len(df)} rows to {path}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   File size: {path.stat().st_size / 1024 / 1024:.2f} MB")


def print_data_quality_report(df: pd.DataFrame, name: str = "Dataset"):
    """Print a data quality report."""
    print(f"\n{'='*60}")
    print(f"DATA QUALITY REPORT: {name}")
    print(f"{'='*60}")
    
    print(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Non-null counts
    non_null_pct = (df.notna().sum() / len(df) * 100).sort_values(ascending=False)
    print(f"\nColumn completeness (% non-null):")
    for col, pct in non_null_pct.items():
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {col:40s} {bar} {pct:5.1f}%")
    
    # Rows with meaningful data
    key_cols = ["total_properties", "rent_demand_mean_pcm", "growth_latest_avg_price", 
                "rent_avg_pcm", "sale_avg_price"]
    key_cols = [c for c in key_cols if c in df.columns]
    
    if key_cols:
        rows_with_data = df[key_cols].notna().any(axis=1).sum()
        print(f"\nRows with at least one key metric: {rows_with_data}/{len(df)} ({rows_with_data/len(df)*100:.1f}%)")


# ============ MAIN EXECUTION ============
if __name__ == "__main__":
    print("=" * 60)
    print("ScanSan API District Data Collector for AI Training")
    print("=" * 60)
    print("\nThis collects data at DISTRICT level (e.g., NW1, SW6)")
    print("for better data coverage than full postcodes.")
    print("=" * 60)
    
    # Get all UK districts
    all_districts = get_all_uk_districts()
    print(f"\nTotal UK districts to fetch: {len(all_districts)}")
    
    # Full data collection - all UK districts (~1 hour, ~2000+ districts)
    LIMIT = None  # NO LIMITS - COLLECTING ALL DATA
    
    if LIMIT:
        print(f"Fetching first {LIMIT} districts")
    else:
        print(f"Fetching ALL {len(all_districts)} districts - FULL DATASET MODE 🚀")
    
    # Collect data
    df_features, df_timeseries = collect_district_training_data(
        districts=all_districts,
        limit=LIMIT,
        save_intermediate=True
    )
    
    # Save both datasets
    save_to_parquet(df_features, PARQUET_PATH, "district features")
    if len(df_timeseries) > 0:
        save_to_parquet(df_timeseries, GROWTH_PARQUET_PATH, "growth time series")
    
    # Print quality reports
    print_data_quality_report(df_features, "District Features")
    
    if len(df_timeseries) > 0:
        print(f"\n{'='*60}")
        print("TIME SERIES DATA SUMMARY")
        print(f"{'='*60}")
        print(f"Total time points: {len(df_timeseries)}")
        print(f"Districts with time series: {df_timeseries['district'].nunique()}")
        if "year" in df_timeseries.columns:
            print(f"Year range: {df_timeseries['year'].min():.0f} - {df_timeseries['year'].max():.0f}")
        print(f"\nSample time series data:")
        print(df_timeseries.head(10))
    
    print("\n" + "=" * 60)
    print("SAMPLE FEATURE DATA")
    print("=" * 60)
    
    # Show a sample of rows with good data
    key_cols = ["district", "total_properties", "rent_demand_mean_pcm", 
                "growth_latest_avg_price", "growth_latest_pct_change"]
    key_cols = [c for c in key_cols if c in df_features.columns]
    
    good_rows = df_features[df_features[key_cols[1:]].notna().any(axis=1)]
    print(f"\nDistricts with data: {len(good_rows)}/{len(df_features)}")
    print("\nSample (first 10 with data):")
    print(good_rows[key_cols].head(10).to_string())
    
    print("\n" + "=" * 60)
    print("NEXT STEPS FOR ML TRAINING")
    print("=" * 60)
    print("""
1. SPATIAL FEATURES: Add lat/lon coordinates for each district
   - Use a postcode-to-coordinates lookup
   - Compute neighbor distances and spatial lags

2. TEMPORAL FEATURES: Use the growth time series to create:
   - Lag features (rent_t-1, rent_t-2, etc.)
   - Rolling averages (3mo, 6mo, 12mo)
   - Seasonality indicators (month, quarter)

3. MERGE DATASETS: Join features + time series for panel data

4. TARGET VARIABLE: rent_demand_mean_pcm or rent_avg_pcm
    """)
