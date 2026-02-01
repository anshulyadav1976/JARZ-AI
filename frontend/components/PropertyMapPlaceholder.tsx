"use client";

import React from "react";

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
}

interface PropertyMapPlaceholderProps {
  properties?: Property[];
  center?: [number, number];
}

export function PropertyMapPlaceholder({ properties = [] }: PropertyMapPlaceholderProps) {
  const hashToPos = (id: string) => {
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
    return {
      x: (hash % 1000) / 1000,
      y: ((Math.floor(hash / 1000)) % 1000) / 1000,
    };
  };

  return (
    <div className="relative h-full w-full bg-slate-100 dark:bg-slate-900">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(0,0,0,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,0,0,0.05)_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.06)_1px,transparent_1px)] bg-[length:20px_20px]" />
      <div className="absolute inset-0">
        {properties.map((p) => {
          const { x, y } = hashToPos(p.id);
          return (
            <div
              key={p.id}
              className="absolute w-2 h-2 bg-blue-500 rounded-full shadow"
              style={{ left: `${x * 100}%`, top: `${y * 100}%`, transform: "translate(-50%, -50%)" }}
              title={p.title}
            />
          );
        })}
      </div>
      <div className="absolute bottom-3 left-3 text-xs text-muted-foreground bg-white/80 dark:bg-black/40 px-2 py-1 rounded">
        Map placeholder — set NEXT_PUBLIC_MAPBOX_TOKEN to enable Mapbox
      </div>
    </div>
  );
}
