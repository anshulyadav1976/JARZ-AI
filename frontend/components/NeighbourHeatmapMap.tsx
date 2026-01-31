"use client";

import React from "react";
import type { NeighbourHeatmapMapProps, Neighbor } from "@/lib/types";

// Simple SVG-based map visualization
// In production, you'd use a proper map library like Mapbox or Leaflet

export function NeighbourHeatmapMap({
  center,
  neighbors,
  selectedAreaCode,
}: NeighbourHeatmapMapProps) {
  // Calculate bounds for positioning
  const allPoints = [
    { lat: center.lat || 51.5, lon: center.lon || -0.1 },
    ...neighbors.map((n) => ({ lat: n.lat, lon: n.lon })),
  ];

  const minLat = Math.min(...allPoints.map((p) => p.lat));
  const maxLat = Math.max(...allPoints.map((p) => p.lat));
  const minLon = Math.min(...allPoints.map((p) => p.lon));
  const maxLon = Math.max(...allPoints.map((p) => p.lon));

  const padding = 0.02;
  const latRange = maxLat - minLat + padding * 2;
  const lonRange = maxLon - minLon + padding * 2;

  // Convert lat/lon to SVG coordinates
  const toSVG = (lat: number, lon: number) => {
    const x = ((lon - minLon + padding) / lonRange) * 100;
    const y = 100 - ((lat - minLat + padding) / latRange) * 100;
    return { x, y };
  };

  // Get color based on rent/demand
  const getColor = (neighbor: Neighbor) => {
    const demand = neighbor.demand_index || 75;
    if (demand >= 80) return "#EF4444"; // Red - high demand
    if (demand >= 70) return "#F97316"; // Orange
    if (demand >= 60) return "#EAB308"; // Yellow
    return "#22C55E"; // Green - lower demand
  };

  const centerPos = toSVG(center.lat || 51.5, center.lon || -0.1);

  const formatCurrency = (value?: number) => {
    if (!value) return "N/A";
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow flex-1 min-w-[300px] flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">
          <span className="w-1.5 h-1.5 bg-primary rounded-full"></span>
          Neighboring Areas
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Spatial context with {neighbors.length} nearby areas
      </p>

      {/* SVG Map */}
      <div className="relative aspect-square bg-muted/50 rounded-lg overflow-hidden border border-border flex-shrink-0">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
              <path
                d="M 10 0 L 0 0 0 10"
                fill="none"
                stroke="#CBD5E1"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#grid)" />

          {/* Connection lines from center to neighbors */}
          {neighbors.map((neighbor, i) => {
            const pos = toSVG(neighbor.lat, neighbor.lon);
            return (
              <line
                key={`line-${i}`}
                x1={centerPos.x}
                y1={centerPos.y}
                x2={pos.x}
                y2={pos.y}
                stroke="#94A3B8"
                strokeWidth="0.5"
                strokeDasharray="2,2"
              />
            );
          })}

          {/* Neighbor circles */}
          {neighbors.map((neighbor, i) => {
            const pos = toSVG(neighbor.lat, neighbor.lon);
            return (
              <g key={`neighbor-${i}`}>
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="4"
                  fill={getColor(neighbor)}
                  stroke="#FFFFFF"
                  strokeWidth="1"
                  className="transition-all hover:r-6 cursor-pointer"
                />
                <title>
                  {neighbor.display_name}
                  {"\n"}Avg Rent: {formatCurrency(neighbor.avg_rent)}
                  {"\n"}Demand: {neighbor.demand_index?.toFixed(1)}
                </title>
              </g>
            );
          })}

          {/* Center point (selected area) */}
          <circle
            cx={centerPos.x}
            cy={centerPos.y}
            r="6"
            fill="#3B82F6"
            stroke="#FFFFFF"
            strokeWidth="2"
          />
          <circle
            cx={centerPos.x}
            cy={centerPos.y}
            r="10"
            fill="none"
            stroke="#3B82F6"
            strokeWidth="1"
            strokeDasharray="3,3"
          >
            <animate
              attributeName="r"
              values="8;12;8"
              dur="2s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values="1;0.3;1"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-4 p-3 bg-muted/30 rounded-lg flex-shrink-0">
        <div className="flex items-center justify-around text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-primary shadow-sm"></div>
            <span className="text-muted-foreground font-medium">Selected</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500 shadow-sm"></div>
            <span className="text-muted-foreground font-medium">High Demand</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500 shadow-sm"></div>
            <span className="text-muted-foreground font-medium">Lower Demand</span>
          </div>
        </div>
      </div>

      {/* Neighbor list - takes remaining height */}
      <div className="mt-4 space-y-2 flex-1 overflow-y-auto min-h-0">
        {neighbors.map((neighbor, i) => (
          <div
            key={i}
            className="flex items-center justify-between p-3 bg-muted/50 hover:bg-muted/70 rounded-lg border border-border transition-colors"
          >
            <div className="flex items-center gap-3">
              <div
                className="w-2.5 h-2.5 rounded-full shadow-sm"
                style={{ backgroundColor: getColor(neighbor) }}
              ></div>
              <span className="font-medium text-foreground text-sm">
                {neighbor.area_code}
              </span>
            </div>
            <span className="text-muted-foreground font-semibold text-sm">
              {formatCurrency(neighbor.avg_rent)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
