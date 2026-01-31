"use client";

import React from "react";
import { MapPin } from "lucide-react";

export function PropertyMapView() {
  return (
    <div className="h-full flex items-center justify-center bg-muted/20">
      <div className="text-center px-8 py-12 max-w-md">
        <div className="w-20 h-20 mx-auto mb-6 bg-primary/10 rounded-full flex items-center justify-center">
          <MapPin className="w-10 h-10 text-primary" />
        </div>
        <h3 className="text-lg font-semibold mb-2">Map View</h3>
        <p className="text-sm text-muted-foreground">
          Interactive map with property locations will be displayed here. Integration with mapping library coming soon.
        </p>
      </div>
    </div>
  );
}
