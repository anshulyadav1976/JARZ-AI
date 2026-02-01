"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { LocationComparisonListingsProps } from "@/lib/types";

const RENT_COLOR = "hsl(var(--chart-1))";
const SALE_COLOR = "hsl(var(--chart-2))";

export function LocationComparisonListings({ areas }: LocationComparisonListingsProps) {
  const data = areas.map((a) => ({
    area: a.area_code,
    "Rent listings": a.rent_listings ?? 0,
    "Sale listings": a.sale_listings ?? 0,
    total_properties: a.total_properties ?? 0,
  }));

  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string }>;
    label?: string;
  }) => {
    if (!active || !payload?.length) return null;
    const row = data.find((d) => d.area === label);
    return (
      <div className="bg-card border border-border rounded-xl p-3 shadow-lg">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          {label}
        </p>
        <div className="space-y-1 text-sm">
          <p className="flex justify-between gap-4 tabular-nums">
            <span className="text-muted-foreground">Rent listings</span>
            <span className="font-semibold text-foreground">{payload.find((p) => p.name === "Rent listings")?.value ?? 0}</span>
          </p>
          <p className="flex justify-between gap-4 tabular-nums">
            <span className="text-muted-foreground">Sale listings</span>
            <span className="font-semibold text-foreground">{payload.find((p) => p.name === "Sale listings")?.value ?? 0}</span>
          </p>
          {row && row.total_properties > 0 && (
            <p className="flex justify-between gap-4 tabular-nums text-muted-foreground text-xs pt-1 border-t border-border">
              <span>Total properties (area)</span>
              <span>{row.total_properties.toLocaleString()}</span>
            </p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
        <span className="w-2 h-2 bg-primary rounded-full" />
        Listings by area
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Current rent and sale listing counts from area summary.
      </p>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 16, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis
              dataKey="area"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted) / 0.5)" }} />
            <Legend
              formatter={(value) => (
                <span className="text-xs text-muted-foreground">{value}</span>
              )}
            />
            <Bar dataKey="Rent listings" fill={RENT_COLOR} radius={[6, 6, 0, 0]} maxBarSize={48} />
            <Bar dataKey="Sale listings" fill={SALE_COLOR} radius={[6, 6, 0, 0]} maxBarSize={48} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-muted-foreground">
        <span className="flex items-center gap-2">
          <span className="w-4 h-3 rounded" style={{ backgroundColor: RENT_COLOR }} /> Rent
        </span>
        <span className="flex items-center gap-2">
          <span className="w-4 h-3 rounded" style={{ backgroundColor: SALE_COLOR }} /> Sale
        </span>
      </div>

      <p className="mt-4 text-[10px] text-muted-foreground/80">
        Data: ScanSan area summary API
      </p>
    </div>
  );
}

