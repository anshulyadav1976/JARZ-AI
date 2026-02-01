"use client";

import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';

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
  lat?: number;
  lng?: number;
  amenities?: Array<{
    type: string;
    name: string;
    distance: number;
  }>;
}

interface PropertyMapViewProps {
  properties?: Property[];
  center?: [number, number];
}

// Choose between Mapbox client or placeholder at build time based on token presence
const MAPBOX_ENABLED = !!process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

const PropertyMapComponent = dynamic(
  () => MAPBOX_ENABLED
    ? import('./PropertyMapViewClient').then(mod => ({ default: mod.PropertyMapViewClient }))
    : import('./PropertyMapPlaceholder').then(mod => ({ default: mod.PropertyMapPlaceholder })),
  {
    ssr: false,
    loading: () => (
      <div className="h-full w-full flex items-center justify-center bg-muted/20">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading map...</p>
        </div>
      </div>
    ),
  }
);

export function PropertyMapView({ properties = [], center }: PropertyMapViewProps) {
  return <PropertyMapComponent properties={properties} center={center} />;
}
