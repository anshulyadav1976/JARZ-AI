"use client";

import { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Property {
  id: string;
  title: string;
  price: number;
  type: "sale" | "rent";
  location: string;
  beds: number;
  baths: number;
  sqft: number;
  url: string;
  imageUrl?: string;
  amenities?: Array<{
    type: string;
    name: string;
    distance: number;
  }>;
}

interface PropertyListingsState {
  properties: any[];
  isLoading: boolean;
  error: string | null;
  areaCode: string | null;
}

interface UsePropertyListingsResult {
  state: PropertyListingsState;
  fetchListings: (areaCode: string, listingType: "rent" | "sale") => Promise<void>;
  fetchListingsBoth: (areaCode: string) => Promise<void>;
}

export function usePropertyListings(): UsePropertyListingsResult {
  const [state, setState] = useState<PropertyListingsState>({
    properties: [],
    isLoading: false,
    error: null,
    areaCode: null,
  });

  const fetchAmenitiesForArea = useCallback(async (areaCode: string): Promise<Array<{ type: string; name: string; distance: number }>> => {
    try {
      const resp = await fetch(`${API_URL}/api/postcode/${encodeURIComponent(areaCode)}/amenities`);
      if (!resp.ok) return [];
      const result = await resp.json();
      const amenities = Array.isArray(result?.amenities) ? result.amenities : [];
      // Normalize to our expected shape and limit
      return amenities
        .filter((a: any) => a && typeof a.type === "string" && a.name)
        .slice(0, 6)
        .map((a: any) => ({
          type: String(a.type),
          name: String(a.name),
          distance: typeof a.distance === "number" ? a.distance : 0,
        }));
    } catch {
      return [];
    }
  }, []);

  const fetchListings = useCallback(async (areaCode: string, listingType: "rent" | "sale" = "sale") => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${API_URL}/api/properties/listings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          area_code: areaCode,
          listing_type: listingType,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success && result.data) {
        const apiData = result.data;
        const dataSection = apiData?.data || {};
        const listingsRaw = (listingType === "sale")
          ? (dataSection?.sale_listings || [])
          : (dataSection?.rent_listings || []);

        const listings = (listingsRaw as any[]).map((item: any, idx: number) => {
          const price = listingType === "rent"
            ? (item?.rent_pcm ?? (item?.rent_pw ? Math.round(item.rent_pw * 52 / 12) : 0))
            : (item?.sale_price ?? 0);
          const size = parseInt(item?.property_size, 10);
          return {
            id: `${item?.street_address || "unknown"}-${idx}`,
            title: item?.street_address || `${item?.area_code_district || areaCode} property`,
            price,
            type: listingType,
            location: item?.area_code_district || areaCode,
            beds: item?.bedrooms ?? 0,
            baths: item?.bathrooms ?? 0,
            livingRooms: item?.living_rooms ?? 1,
            sqft: Number.isFinite(size) ? size : 0,
            url: "",
          };
        });
        // Fetch area amenities and attach (area-wide for now)
        const amenities = await fetchAmenitiesForArea(areaCode);
        const withAmenities = listings.map(p => ({ ...p, amenities }));

        setState({
          properties: withAmenities,
          isLoading: false,
          error: null,
          areaCode: areaCode,
        });
      } else {
        throw new Error("Invalid response format");
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : "Failed to fetch listings",
      }));
    }
  }, []);

  const fetchListingsBoth = useCallback(async (areaCode: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      // Fetch rent
      const rentResp = await fetch(`${API_URL}/api/properties/listings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ area_code: areaCode, listing_type: "rent" }),
      });
      const rentData = rentResp.ok ? await rentResp.json() : null;

      // Fetch sale
      const saleResp = await fetch(`${API_URL}/api/properties/listings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ area_code: areaCode, listing_type: "sale" }),
      });
      const saleData = saleResp.ok ? await saleResp.json() : null;

      const normalize = (result: any, listingType: "rent" | "sale") => {
        if (!result?.success || !result?.data) return [];
        const section = result.data?.data || {};
        const raw = listingType === "sale" ? (section?.sale_listings || []) : (section?.rent_listings || []);
        return (raw as any[]).map((item: any, idx: number) => {
          const price = listingType === "rent" ? (item?.rent_pcm ?? (item?.rent_pw ? Math.round(item.rent_pw * 52 / 12) : 0)) : (item?.sale_price ?? 0);
          const size = parseInt(item?.property_size, 10);
          return {
            id: `${item?.street_address || "unknown"}-${listingType}-${idx}`,
            title: item?.street_address || `${item?.area_code_district || areaCode} property`,
            price,
            type: listingType,
            location: item?.area_code_district || areaCode,
            beds: item?.bedrooms ?? 0,
            baths: item?.bathrooms ?? 0,
            livingRooms: item?.living_rooms ?? 1,
            sqft: Number.isFinite(size) ? size : 0,
            url: "",
          };
        });
      };

      const combined = [
        ...normalize(rentData, "rent"),
        ...normalize(saleData, "sale"),
      ];

      // Fetch area amenities and attach to all listings (area-wide for now)
      const amenities = await fetchAmenitiesForArea(areaCode);
      const withAmenities = combined.map(p => ({ ...p, amenities }));

      setState({
        properties: withAmenities,
        isLoading: false,
        error: null,
        areaCode: areaCode,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : "Failed to fetch listings",
      }));
    }
  }, []);

  return {
    state,
    fetchListings,
    fetchListingsBoth,
  };
}
