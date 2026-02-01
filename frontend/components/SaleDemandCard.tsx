"use client";

import React from "react";
import type { SaleDemandItem } from "@/lib/types";

function formatCurrency(value?: number | null) {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
    notation: "compact",
  }).format(value);
}

export interface SaleDemandCardProps {
  district: string;
  demand?: SaleDemandItem[];
  targetMonth?: string;
  targetYear?: number;
}

export function SaleDemandCard({
  district,
  demand = [],
  targetMonth,
  targetYear,
}: SaleDemandCardProps) {
  const primary = demand[0];

  if (!primary) {
    return (
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
          <span className="w-2 h-2 bg-primary rounded-full" />
          Sales Demand — {district}
        </div>
        <p className="text-muted-foreground">No sales demand data for this district.</p>
      </div>
    );
  }

  const period = [targetMonth, targetYear].filter(Boolean).join(" ") || "Latest";

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
        <span className="w-2 h-2 bg-primary rounded-full" />
        Sales Demand — {district}
      </div>
      <p className="text-sm text-muted-foreground mb-4">Period: {period}</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="p-3 rounded-xl bg-muted/40 border border-border/80">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Properties for sale</div>
          <div className="text-lg font-bold text-foreground tabular-nums">
            {primary.total_properties_for_sale ?? "—"}
          </div>
        </div>
        <div className="p-3 rounded-xl bg-muted/40 border border-border/80">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Mean price</div>
          <div className="text-lg font-bold text-foreground tabular-nums">
            {formatCurrency(primary.mean_price)}
          </div>
        </div>
        <div className="p-3 rounded-xl bg-muted/40 border border-border/80">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Median price</div>
          <div className="text-lg font-bold text-foreground tabular-nums">
            {formatCurrency(primary.median_price)}
          </div>
        </div>
        <div className="p-3 rounded-xl bg-muted/40 border border-border/80">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Days on market</div>
          <div className="text-lg font-bold text-foreground tabular-nums">
            {primary.days_on_market ?? "—"}
          </div>
        </div>
        <div className="p-3 rounded-xl bg-muted/40 border border-border/80">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Months of inventory</div>
          <div className="text-lg font-bold text-foreground tabular-nums">
            {primary.months_of_inventory != null ? primary.months_of_inventory.toFixed(1) : "—"}
          </div>
        </div>
        <div className="p-3 rounded-xl border-2 border-primary/30 bg-primary/5">
          <div className="text-[11px] font-semibold text-primary uppercase tracking-wider">Market rating</div>
          <div className="text-lg font-bold text-primary tabular-nums">
            {primary.market_rating ?? "—"}
          </div>
        </div>
      </div>
      <p className="mt-4 text-[10px] text-muted-foreground/80">Data: ScanSan sale demand API</p>
    </div>
  );
}
