"use client";

import React, { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { MapPin, Bed, Bath, Square, Loader2, School, Hospital, Train, ShoppingCart, Sofa } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PropertyFinderProperty {
  id: string;
  title: string;
  price: number;
  type: "sale" | "rent";
  location: string;
  beds: number;
  baths: number;
  livingRooms?: number;
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
  forcedFilterType?: "all" | "rent" | "sale";
}

export function PropertyListView({ properties = [], isLoading = false, error = null, forcedFilterType }: PropertyFinderViewProps) {
  // Use parent-controlled type filter only
  const filterType = forcedFilterType ?? "all";
  const [minBeds, setMinBeds] = useState<number>(0);
  const [maxPrice, setMaxPrice] = useState<number>(0);
  // No internal toggle or search bar; filters are always visible

  const formatPrice = (price: number, type: "sale" | "rent") => {
    if (type === "sale") {
      return `£${(price / 1000).toFixed(0)}k`;
    }
    return `£${price.toLocaleString()}/mo`;
  };

  // Filter properties
  const filteredProperties = useMemo(() => {
    return properties.filter((property: PropertyFinderProperty) => {
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
  }, [properties, filterType, minBeds, maxPrice]);

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

  const FloorPlan: React.FC<{ beds: number; baths: number; livingRooms?: number }> = ({ beds, baths, livingRooms = 1 }) => {
    const rooms: Array<{ type: "bed" | "bath" | "living"; count: number; color: string }> = [
      { type: "bed", count: Math.max(0, beds), color: "bg-blue-600" },
      { type: "bath", count: Math.max(0, baths), color: "bg-cyan-600" },
      { type: "living", count: Math.max(0, livingRooms), color: "bg-violet-600" },
    ];
    const total = rooms.reduce((sum, r) => sum + r.count, 0) || 1;
    // Adaptive square grid with no upper cap to avoid overlap
    const gridCols = Math.max(2, Math.ceil(Math.sqrt(total)));
    const totalSlots = gridCols * gridCols;

    const renderIcon = (type: "bed" | "bath" | "living") => {
      // Smaller icon footprint; do not alter box sizing
      const common = "w-1/2 h-1/2 text-white";
      if (type === "bed") return <Bed className={common} />;
      if (type === "bath") return <Bath className={common} />;
      return <Sofa className={common} />;
    };

    const icons = rooms.flatMap((r, idx) => (
      Array.from({ length: r.count }).map((_, i) => (
        <div
          key={`${r.type}-${idx}-${i}`}
          className={`${r.color} flex items-center justify-center overflow-hidden`}
          style={{ aspectRatio: "1 / 1" }}
        >
          <div className="flex items-center justify-center w-full h-full">
            {renderIcon(r.type)}
          </div>
        </div>
      ))
    ));

    return (
      <div className="mt-3 p-0 border rounded-lg bg-muted/20">
        <div className="relative w-full" style={{ aspectRatio: "1 / 1" }}>
          <div
            className="absolute inset-0 grid gap-0"
            style={{ gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))`, gridTemplateRows: `repeat(${gridCols}, minmax(0, 1fr))` }}
          >
            {icons}
            {Array.from({ length: Math.max(0, totalSlots - total) }).map((_, i) => (
              <div key={`empty-${i}`} style={{ aspectRatio: "1 / 1" }} />
            ))}
          </div>
        </div>
        <div className="mt-2 flex gap-3 text-[10px] text-muted-foreground px-2 pb-2">
          <span>Bedrooms: {beds}</span>
          <span>Bathrooms: {baths}</span>
          <span>Living rooms: {Math.max(0, livingRooms)}</span>
        </div>
      </div>
    );
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
      {/* Filters (always visible, no extra click) */}
      <div className="space-y-2 pb-2 border-b">
        <div className="grid grid-cols-2 gap-2 pt-2">
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
              setMinBeds(0);
              setMaxPrice(0);
            }}
            className="mt-2"
          >
            Clear filters
          </Button>
        </div>
      )}

      {/* Property Cards Gallery */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
      {filteredProperties.map((property: PropertyFinderProperty) => (
        <Card key={property.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <h3 className="font-semibold text-sm mb-1">{property.title}</h3>
            </div>
            <div className="flex flex-col items-end mt-1">
              <div className="font-bold text-lg">{formatPrice(property.price, property.type)}</div>
              <Badge variant={property.type === "sale" ? "default" : "secondary"} className="text-[10px] mt-1">
                {property.type === "sale" ? "For Sale" : "To Rent"}
              </Badge>
            </div>
          </div>

          {/* Removed duplicate bed/bath counters; keep sqft only if available */}
          {property.sqft > 0 && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
              <Square className="h-3 w-3" />
              <span>{property.sqft} sqft</span>
            </div>
          )}

          {/* Floorplan visualization */}
          <FloorPlan beds={property.beds} baths={property.baths} livingRooms={property.livingRooms ?? 1} />

          {/* Nearby amenities section (always present) */}
          <div className="mt-3 pt-3 border-t">
            <p className="text-xs font-medium text-muted-foreground mb-2">Nearby Amenities</p>
            {property.amenities && property.amenities.length > 0 ? (
              <div className="grid grid-cols-1 gap-2">
                {property.amenities.map((amenity: { type: string; name: string; distance: number }, idx: number) => (
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
            ) : (
              <p className="text-[11px] text-muted-foreground">Amenities data not available for this listing.</p>
            )}
          </div>
        </Card>
      ))}
      </div>
    </div>
  );
}
