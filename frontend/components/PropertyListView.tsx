"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, MapPin, Bed, Bath, Square, Loader2 } from "lucide-react";

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
}

interface PropertyListViewProps {
  properties?: Property[];
  isLoading?: boolean;
  error?: string | null;
}

export function PropertyListView({ properties = [], isLoading = false, error = null }: PropertyListViewProps) {
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
        <Card key={property.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
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
            </div>
            <div className="text-right">
              <div className="font-bold text-lg">{formatPrice(property.price, property.type)}</div>
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
            <div className="flex items-center gap-1">
              <Square className="h-3 w-3" />
              <span>{property.sqft} sqft</span>
            </div>
          </div>

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
