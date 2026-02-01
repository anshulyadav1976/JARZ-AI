"use client";

import React from "react";
import { MapPin } from "lucide-react";

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
}

function hashToPosition(id: string) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  const left = (h % 90) + 5; // 5% padding
  const top = ((Math.floor(h / 997)) % 90) + 5;
  return { left: `${left}%`, top: `${top}%` };
}

export function PropertyMapView({ properties = [] }: { properties?: Property[] }) {
  const hasProps = properties && properties.length > 0;

  return (
    <div className="h-full flex items-center justify-center bg-muted/20">
      {hasProps ? (
        <div className="relative w-full h-[500px] bg-background border rounded-lg">
          {/* Simple placeholder map grid */}
          <div className="absolute inset-0 opacity-50 grid grid-cols-8 grid-rows-8">
            {Array.from({ length: 64 }).map((_, i) => (
              <div key={i} className="border-[0.5px] border-muted" />
            ))}
          </div>

          {/* Property dots */}
          {properties.map((p) => {
            const pos = hashToPosition(p.id);
            const label = `${p.type === "rent" ? "£" + p.price + "/mo" : "£" + p.price} • ${p.title}`;
            return (
              <div key={p.id} className="absolute" style={{ left: pos.left, top: pos.top }} title={label}>
                <div className="w-3 h-3 rounded-full bg-blue-600 shadow-sm ring-2 ring-blue-300" />
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center px-8 py-12 max-w-md">
          <div className="w-20 h-20 mx-auto mb-6 bg-primary/10 rounded-full flex items-center justify-center">
            <MapPin className="w-10 h-10 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Map View</h3>
          <p className="text-sm text-muted-foreground">
            Type an area code and fetch listings to see blue dots appear here.
          </p>
        </div>
      )}
    </div>
  );
}
