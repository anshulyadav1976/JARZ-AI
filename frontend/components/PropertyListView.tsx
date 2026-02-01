"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, MapPin, Bed, Bath, Square, Loader2 } from "lucide-react";

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
}

interface PropertyFinderViewProps {
  properties?: PropertyFinderProperty[];
  isLoading?: boolean;
  error?: string | null;
}

export function PropertyFinderView({ properties = [], isLoading = false, error = null }: PropertyFinderViewProps) {
  const formatPrice = (price: number, type: "sale" | "rent") => {
    if (type === "sale") {
      return `£${(price / 1000).toFixed(0)}k`;
    }
    return `£${price.toLocaleString()}/mo`;
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
      {properties.map((property) => (
        <Card key={property.id} className="p-4 hover:shadow-md transition-shadow flex gap-4">
          {/* Property Image */}
          {property.imageUrl && (
            <img
              src={property.imageUrl}
              alt={property.title}
              className="w-32 h-24 object-cover rounded-md flex-shrink-0 border"
              loading="lazy"
            />
          )}
          <div className="flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold text-sm">{property.title}</h3>
                <Badge variant={property.type === "sale" ? "default" : "secondary"} className="text-xs">
                  {property.type === "sale" ? "For Sale" : "To Rent"}
                </Badge>
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
                <MapPin className="h-3 w-3" />
                <span>{property.location}</span>
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
                <div className="flex items-center gap-1">
                  <Square className="h-3 w-3" />
                  <span>{property.sqft} sqft</span>
                </div>
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
        </Card>
      ))}
    </div>
  );
}
