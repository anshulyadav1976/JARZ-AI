"use client";

import React, { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ExternalLink, MapPin, Bed, Bath, Square, Loader2, School, Hospital, Train, ShoppingCart, Search, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PropertyFinderProperty {
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

interface PropertyFinderViewProps {
  properties?: PropertyFinderProperty[];
  isLoading?: boolean;
  error?: string | null;
}

export function PropertyListView({ properties = [], isLoading = false, error = null }: PropertyListViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "rent" | "sale">("all");
  const [minBeds, setMinBeds] = useState<number>(0);
  const [maxPrice, setMaxPrice] = useState<number>(0);
  const [showFilters, setShowFilters] = useState(false);

  const formatPrice = (price: number, type: "sale" | "rent") => {
    if (type === "sale") {
      return `£${(price / 1000).toFixed(0)}k`;
    }
    return `£${price.toLocaleString()}/mo`;
  };

  // Filter and search properties
  const filteredProperties = useMemo(() => {
    return properties.filter(property => {
      // Search filter
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase();
        const matchesSearch = 
          property.title.toLowerCase().includes(searchLower) ||
          property.location.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }
      
      // Type filter
      if (filterType !== "all" && property.type !== filterType) {
        return false;
      }
      
      // Beds filter
      if (minBeds > 0 && property.beds < minBeds) {
        return false;
      }
      
      // Price filter
      if (maxPrice > 0 && property.price > maxPrice) {
        return false;
      }
      
      return true;
    });
  }, [properties, searchQuery, filterType, minBeds, maxPrice]);

  const getAmenityIcon = (type: string) => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes("school") || lowerType.includes("education")) {
      return <School className="h-3 w-3" />;
    }
    if (lowerType.includes("hospital") || lowerType.includes("health") || lowerType.includes("medical")) {
      return <Hospital className="h-3 w-3" />;
    }
    if (lowerType.includes("transport") || lowerType.includes("station") || lowerType.includes("train") || lowerType.includes("tube")) {
      return <Train className="h-3 w-3" />;
    }
    if (lowerType.includes("shop") || lowerType.includes("supermarket") || lowerType.includes("retail")) {
      return <ShoppingCart className="h-3 w-3" />;
    }
    return <MapPin className="h-3 w-3" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-sm text-muted-foreground">Loading properties...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center px-8 py-12 max-w-md">
          <div className="w-20 h-20 mx-auto mb-6 bg-destructive/10 rounded-full flex items-center justify-center">
            <MapPin className="w-10 h-10 text-destructive" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Error Loading Properties</h3>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  if (properties.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center px-8 py-12 max-w-md">
          <div className="w-20 h-20 mx-auto mb-6 bg-primary/10 rounded-full flex items-center justify-center">
            <MapPin className="w-10 h-10 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No Properties Found</h3>
          <p className="text-sm text-muted-foreground">
            Ask about a location (e.g., "Show me properties in NW1") to see available listings.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Search and Filter Bar */}
      <div className="space-y-2 pb-2 border-b">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by address or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
          <Button
            variant={showFilters ? "secondary" : "outline"}
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="h-9 px-3"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Filter Options */}
        {showFilters && (
          <div className="grid grid-cols-3 gap-2 pt-2">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Type</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as any)}
                className="w-full h-8 px-2 text-xs border rounded-md bg-background"
              >
                <option value="all">All</option>
                <option value="rent">Rent</option>
                <option value="sale">Sale</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Min Beds</label>
              <Input
                type="number"
                min="0"
                value={minBeds || ""}
                onChange={(e) => setMinBeds(parseInt(e.target.value) || 0)}
                placeholder="Any"
                className="h-8 text-xs"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Max Price</label>
              <Input
                type="number"
                min="0"
                value={maxPrice || ""}
                onChange={(e) => setMaxPrice(parseInt(e.target.value) || 0)}
                placeholder="Any"
                className="h-8 text-xs"
              />
            </div>
          </div>
        )}
        
        {/* Results Count */}
        <div className="text-xs text-muted-foreground">
          Showing {filteredProperties.length} of {properties.length} {properties.length === 1 ? 'property' : 'properties'}
        </div>
      </div>

      {/* Empty State for Filtered Results */}
      {filteredProperties.length === 0 && properties.length > 0 && (
        <div className="text-center py-8">
          <p className="text-sm text-muted-foreground">No properties match your filters</p>
          <Button
            variant="link"
            size="sm"
            onClick={() => {
              setSearchQuery("");
              setFilterType("all");
              setMinBeds(0);
              setMaxPrice(0);
            }}
            className="mt-2"
          >
            Clear filters
          </Button>
        </div>
      )}

      {/* Property Cards */}
      {filteredProperties.map((property) => (
        <Card key={property.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold text-sm">{property.title}</h3>
                <Badge variant={property.type === "sale" ? "default" : "secondary"} className="text-xs">
                  {property.type === "sale" ? "For Sale" : "To Rent"}
                </Badge>
              </div>
            </div>
            <div className="flex items-center justify-between mt-2">
              <div className="font-bold text-lg">{formatPrice(property.price, property.type)}</div>
              <a
                href={property.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
              >
                View Listing
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            {/* Placeholder for reviews */}
            <div className="mt-2 text-xs text-muted-foreground">
              <span>Reviews: </span>
              <span className="italic">(No reviews yet)</span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
            <div className="flex items-center gap-1">
              <Bed className="h-3 w-3" />
              <span>{property.beds} beds</span>
            </div>
            <div className="flex items-center gap-1">
              <Bath className="h-3 w-3" />
              <span>{property.baths} baths</span>
            </div>
            {property.sqft > 0 && (
              <div className="flex items-center gap-1">
                <Square className="h-3 w-3" />
                <span>{property.sqft} sqft</span>
              </div>
            )}
          </div>

          {property.amenities && property.amenities.length > 0 && (
            <div className="mb-3 pb-3 border-t pt-3">
              <p className="text-xs font-medium text-muted-foreground mb-2">Nearby Amenities</p>
              <div className="grid grid-cols-1 gap-2">
                {property.amenities.slice(0, 3).map((amenity, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs">
                    {getAmenityIcon(amenity.type)}
                    <span className="flex-1 truncate">{amenity.name}</span>
                    <span className="text-muted-foreground">
                      {amenity.distance < 1 
                        ? `${(amenity.distance * 1000).toFixed(0)}m` 
                        : `${amenity.distance.toFixed(1)}mi`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <a
            href={property.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            View Listing
            <ExternalLink className="h-3 w-3" />
          </a>
        </Card>
      ))}
    </div>
  );
}
