"use client";

import React, { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ExternalLink, MapPin, Bed, Bath, Square, Loader2, School, Hospital, Train, ShoppingCart, Search, SlidersHorizontal, Sofa } from "lucide-react";
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
}

export function PropertyListView({ properties = [], isLoading = false, error = null }: PropertyListViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "rent" | "sale">("all");
  const [minBeds, setMinBeds] = useState<number>(0);
  const [maxPrice, setMaxPrice] = useState<number>(0);

  const formatPrice = (price: number, type: "sale" | "rent") => {
    if (type === "sale") {
      return `£${(price / 1000).toFixed(0)}k`;
    }
    return `£${price.toLocaleString('en-GB')}/mo`;
  };

  // Normalize text for robust matching (case-insensitive, ignore spaces)
  const normalizeText = (text: string) => text.toLowerCase().replace(/\s+/g, "");

  // Build a safe listing URL. If a property provides a full URL use it,
  // otherwise fall back to a Google search for the property title + location.
  const getListingUrl = (p: PropertyFinderProperty) => {
    if (p.url && /^https?:\/\//i.test(p.url)) return p.url;
    if (p.url && p.url.startsWith("//")) return `https:${p.url}`;
    const q = encodeURIComponent(`${p.title} ${p.location}`);
    return `https://www.google.com/search?q=${q}`;
  };

  // Filter and search properties
  const filteredProperties = useMemo(() => {
    // When searching, show all matching cards regardless of other filters
    if (searchQuery) {
      const q = normalizeText(searchQuery);
      return properties.filter(property => {
        const fields = [property.title, property.location, property.type, property.id];
        const matchesSearch = fields.some(f => normalizeText(String(f || "")).includes(q));
        return matchesSearch;
      });
    }

    // Otherwise, apply the explicit filters
    return properties.filter(property => {
      if (filterType !== "all" && property.type !== filterType) {
        return false;
      }
      if (minBeds > 0 && property.beds < minBeds) {
        return false;
      }
      if (maxPrice > 0 && property.price > maxPrice) {
        return false;
      }
      return true;
    });
  }, [properties, searchQuery, filterType, minBeds, maxPrice]);

  const getAmenityIcon = (type: string) => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes("school") || lowerType.includes("education")) {
      return <School className="h-2.5 w-2.5" />;
    }
    if (lowerType.includes("hospital") || lowerType.includes("health") || lowerType.includes("medical")) {
      return <Hospital className="h-2.5 w-2.5" />;
    }
    if (lowerType.includes("transport") || lowerType.includes("station") || lowerType.includes("train") || lowerType.includes("tube")) {
      return <Train className="h-2.5 w-2.5" />;
    }
    if (lowerType.includes("shop") || lowerType.includes("supermarket") || lowerType.includes("retail")) {
      return <ShoppingCart className="h-2.5 w-2.5" />;
    }
    return <MapPin className="h-2.5 w-2.5" />;
  };

  const FloorPlan: React.FC<{ beds: number; baths: number; livingRooms?: number }> = ({ beds, baths, livingRooms = 1 }) => {
    const rooms: Array<{ type: "bed" | "bath" | "living"; count: number; color: string }> = [
      { type: "bed", count: Math.max(0, beds), color: "bg-blue-600" },
      { type: "bath", count: Math.max(0, baths), color: "bg-cyan-600" },
      { type: "living", count: Math.max(0, livingRooms), color: "bg-violet-600" },
    ];
    const total = rooms.reduce((sum, r) => sum + r.count, 0) || 1;
    const gridCols = Math.max(2, Math.ceil(Math.sqrt(total)));
    const totalSlots = gridCols * gridCols;

    const renderIcon = (type: "bed" | "bath" | "living") => {
      const common = "w-1/3 h-1/3 text-white";
      if (type === "bed") return <Bed className={common} />;
      if (type === "bath") return <Bath className={common} />;
      return <Sofa className={common} />;
    };

    const icons = rooms.flatMap((r, idx) => (
      Array.from({ length: r.count }).map((_, i) => (
        <div key={`${r.type}-${idx}-${i}`} className={`${r.color} flex items-center justify-center overflow-hidden`} style={{ aspectRatio: "1 / 1" }}>
          <div className="flex items-center justify-center w-full h-full">
            {renderIcon(r.type)}
          </div>
        </div>
      ))
    ));

    return (
      <div className="mt-2 p-0 border rounded-lg bg-muted/20">
        <div className="relative w-full" style={{ aspectRatio: "1 / 1" }}>
          <div className="absolute inset-0 grid gap-0" style={{ gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))`, gridTemplateRows: `repeat(${gridCols}, minmax(0, 1fr))` }}>
            {icons}
            {Array.from({ length: Math.max(0, totalSlots - total) }).map((_, i) => (
              <div key={`empty-${i}`} style={{ aspectRatio: "1 / 1" }} />
            ))}
          </div>
        </div>
        <div className="mt-1.5 flex gap-2 text-[9px] text-muted-foreground px-2 pb-1.5">
          <span>Beds: {beds}</span>
          <span>Baths: {baths}</span>
          <span>Living: {Math.max(0, livingRooms)}</span>
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
    <div className="h-full flex flex-col pl-3 sm:pl-4">
      {/* Search and Filter Bar */}
      <div className="space-y-2 pb-2 border-b mb-4 flex-shrink-0">
        {/* Using the main search bar; local search removed */}

        {/* Filter Options (always shown) */}
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

      {/* Property Cards Gallery */}
      <div className="overflow-y-auto flex-1 pr-2">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-4">
        {filteredProperties.map((property) => (
          <a key={property.id} href={getListingUrl(property)} target="_blank" rel="noopener noreferrer" className="block">
            <Card className="p-4 hover:shadow-lg transition-all flex flex-col h-full">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1 mb-1">
                    <h3 className="font-medium text-xs truncate leading-tight">{property.title}</h3>
                    {property.location && (
                      <p className="text-[10px] text-primary mt-1 truncate">
                        {property.location}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1 ml-2 flex-shrink-0">
                  <div className="font-bold text-sm whitespace-nowrap">{formatPrice(property.price, property.type)}</div>
                  <Badge variant={property.type === "sale" ? "default" : "secondary"} className="text-[10px] px-1.5 py-0">
                    {property.type === "sale" ? "For Sale" : "To Rent"}
                  </Badge>
                </div>
              </div>

              <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-2 flex-wrap">
                {property.sqft > 0 && (
                  <div className="flex items-center gap-0.5">
                    <Square className="h-2.5 w-2.5" />
                    <span>{property.sqft} sqft</span>
                  </div>
                )}
              </div>

              <FloorPlan beds={property.beds} baths={property.baths} livingRooms={property.livingRooms ?? 1} />

              {property.amenities && property.amenities.length > 0 && (
                <div className="mb-2 pb-2 border-t pt-2 flex-grow">
                  <p className="text-[10px] font-medium text-muted-foreground mb-1.5">Nearby</p>
                  <div className="grid grid-cols-1 gap-1.5">
                  {property.amenities.slice(0, 3).map((amenity, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[10px]">
                      {getAmenityIcon(amenity.type)}
                      <span className="flex-1 truncate">{amenity.name}</span>
                      <span className="text-muted-foreground whitespace-nowrap">
                        {amenity.distance < 1 
                          ? `${(amenity.distance * 1000).toFixed(0)}m` 
                          : `${amenity.distance.toFixed(1)}mi`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            </Card>
          </a>
        ))}
        </div>
      </div>
    </div>
  );
}