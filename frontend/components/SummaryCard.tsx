"use client";

import React from "react";
import type { SummaryCardProps } from "@/lib/types";

export function SummaryCard({
  location,
  p50,
  p10,
  p90,
  unit,
  horizon_months,
  takeaway,
}: SummaryCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const range = Math.max(p90 - p10, 1);
  const spreadPct = (range / p50) * 100;
  const confidenceLevel =
    spreadPct < 20 ? "High" : spreadPct < 35 ? "Moderate" : "Low";
  const confidenceColor =
    spreadPct < 20
      ? "text-emerald-600 dark:text-emerald-400"
      : spreadPct < 35
      ? "text-amber-600 dark:text-amber-400"
      : "text-rose-600 dark:text-rose-400";

  const confidenceBarColor =
    spreadPct < 20
      ? "bg-emerald-500/80"
      : spreadPct < 35
      ? "bg-amber-400/80"
      : "bg-rose-400/80";

  const medianPosition = ((p50 - p10) / range) * 100;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
            <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
            Rental Forecast
          </div>
          <h3 className="text-2xl font-bold text-foreground tracking-tight mb-1">
            {location}
          </h3>
          <p className="text-sm text-muted-foreground">
            {horizon_months}-month horizon · {unit}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-4 bg-muted/40 rounded-xl border border-border/80">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Low (P10)
          </div>
          <div className="text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(p10)}
          </div>
        </div>

        <div className="text-center p-4 rounded-xl border-2 border-primary/40 bg-primary/5 shadow-sm ring-1 ring-primary/10">
          <div className="text-[11px] font-semibold text-primary uppercase tracking-wider mb-2">
            Expected (P50)
          </div>
          <div className="text-2xl font-bold text-primary tabular-nums">
            {formatCurrency(p50)}
          </div>
          <div className="text-xs text-muted-foreground mt-1.5">{unit}</div>
        </div>

        <div className="text-center p-4 bg-muted/40 rounded-xl border border-border/80">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            High (P90)
          </div>
          <div className="text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(p90)}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between px-4 py-2.5 bg-muted/20 rounded-xl mb-4">
        <span className="text-sm font-medium text-muted-foreground">
          Forecast confidence
        </span>
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${confidenceBarColor} ring-2 ring-background`} />
          <span className={`text-sm font-semibold ${confidenceColor}`}>
            {confidenceLevel}
          </span>
        </div>
      </div>

      <div className="relative h-7 bg-muted/60 rounded-full overflow-hidden mb-2 border border-border/50">
        <div
          className={`absolute inset-y-0 ${confidenceBarColor} rounded-full transition-all`}
          style={{ left: "0%", width: "100%", opacity: 0.9 }}
        />
        <div
          className="absolute top-0 bottom-0 w-1 bg-primary rounded-full shadow-md ring-2 ring-background"
          style={{ left: `clamp(2%, ${medianPosition}%, 98%)` }}
          title={`Median: ${formatCurrency(p50)}`}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground mb-6 px-0.5">
        <span>{formatCurrency(p10)}</span>
        <span>{formatCurrency(p90)}</span>
      </div>

      {takeaway && (
        <div className="p-4 bg-muted/30 rounded-xl border-l-4 border-primary">
          <p className="text-sm text-foreground leading-relaxed">{takeaway}</p>
        </div>
      )}

      <p className="mt-4 text-[10px] text-muted-foreground/80">
        Data may include model estimates. Verify with local sources.
      </p>
    </div>
  );
}
