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
  properties: PropertyFinderProperty[];
  isLoading: boolean;
  error: string | null;
  areaCode: string | null;
}

interface UsePropertyListingsResult {
  state: PropertyListingsState;
  fetchListings: (areaCode: string, listingType: "rent" | "sale") => Promise<void>;
}

export function usePropertyListings(): UsePropertyListingsResult {
  const [state, setState] = useState<PropertyListingsState>({
    properties: [],
    isLoading: false,
    error: null,
    areaCode: null,
  });

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
        const listings = result.data.listings || [];
        setState({
          properties: listings,
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

  return {
    state,
    fetchListings,
  };
}
