"use client";

import React from "react";
import { Trophy, Home, TrendingDown, List } from "lucide-react";
import type { LocationComparisonSummaryCardProps } from "@/lib/types";

function formatCurrency(value?: number | null, compact = false) {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
    notation: compact ? "compact" : "standard",
  }).format(value);
}

export function LocationComparisonSummaryCard({ areas, winners }: LocationComparisonSummaryCardProps) {
  const byCode = new Map(areas.map((a) => [a.area_code, a]));

  const cheapestRentArea = winners.cheapest_rent_mid ? byCode.get(winners.cheapest_rent_mid) : undefined;
  const mostRentListingsArea = winners.most_rent_listings ? byCode.get(winners.most_rent_listings) : undefined;
  const cheapestSaleArea = winners.cheapest_sale_mid ? byCode.get(winners.cheapest_sale_mid) : undefined;

  const MetricCard = ({
    label,
    icon: Icon,
    areaCode,
    subtext,
    isWinner,
  }: {
    label: string;
    icon: React.ElementType;
    areaCode: string;
    subtext: string;
    isWinner: boolean;
  }) => (
    <div
      className={`p-4 rounded-xl border transition-all ${
        isWinner
          ? "border-primary/40 bg-primary/5 ring-1 ring-primary/10"
          : "border-border bg-muted/30"
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5" />
          {label}
        </span>
        {isWinner && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 text-amber-700 dark:text-amber-400 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide">
            <Trophy className="w-3 h-3" />
            Best
          </span>
        )}
      </div>
      <div className="text-lg font-bold text-foreground tabular-nums tracking-tight">
        {areaCode}
      </div>
      <div className="text-xs text-muted-foreground mt-1">{subtext}</div>
    </div>
  );

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-4">
        <span className="w-2 h-2 bg-primary rounded-full" />
        Location Comparison
      </div>

      <h3 className="text-xl font-bold text-foreground tracking-tight mb-1">
        {areas.map((a) => a.area_code).join(" vs ")}
      </h3>
      <p className="text-sm text-muted-foreground mb-6">
        Area summary: listings and price ranges
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Cheapest rent (midpoint)"
          icon={TrendingDown}
          areaCode={cheapestRentArea?.area_code ?? "—"}
          subtext={`${formatCurrency(cheapestRentArea?.rent_pcm_min)} – ${formatCurrency(cheapestRentArea?.rent_pcm_max)} pcm`}
          isWinner={!!winners.cheapest_rent_mid}
        />
        <MetricCard
          label="Most rent listings"
          icon={List}
          areaCode={mostRentListingsArea?.area_code ?? "—"}
          subtext={`${mostRentListingsArea?.rent_listings ?? "—"} listings`}
          isWinner={!!winners.most_rent_listings}
        />
        <MetricCard
          label="Cheapest sale (midpoint)"
          icon={Home}
          areaCode={cheapestSaleArea?.area_code ?? "—"}
          subtext={`${formatCurrency(cheapestSaleArea?.sale_price_min, true)} – ${formatCurrency(cheapestSaleArea?.sale_price_max, true)}`}
          isWinner={!!winners.cheapest_sale_mid}
        />
      </div>

      <p className="mt-4 text-[10px] text-muted-foreground/80">
        Data: ScanSan area summary API
      </p>
    </div>
  );
}

