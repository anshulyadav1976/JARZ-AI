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

  const spreadPct = ((p90 - p10) / p50) * 100;
  const confidenceLevel =
    spreadPct < 20 ? "High" : spreadPct < 35 ? "Moderate" : "Low";
  const confidenceColor =
    spreadPct < 20
      ? "text-green-600 dark:text-green-400"
      : spreadPct < 35
      ? "text-yellow-600 dark:text-yellow-400"
      : "text-red-600 dark:text-red-400";

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium mb-3">
            <span className="w-1.5 h-1.5 bg-primary rounded-full"></span>
            Rental Forecast
          </div>
          <h3 className="text-2xl font-bold text-foreground mb-1">
            {location}
          </h3>
          <p className="text-sm text-muted-foreground">
            {horizon_months} month forecast horizon
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-6">
        {/* P10 - Lower bound */}
        <div className="text-center p-4 bg-muted/50 rounded-lg border border-border hover:border-muted-foreground/20 transition-colors">
          <div className="text-xs font-medium text-muted-foreground mb-2">
            Low (P10)
          </div>
          <div className="text-lg font-bold text-foreground">
            {formatCurrency(p10)}
          </div>
        </div>

        {/* P50 - Median */}
        <div className="text-center p-4 bg-primary/10 rounded-lg border-2 border-primary/30 shadow-sm">
          <div className="text-xs font-semibold text-primary mb-2">
            Expected (P50)
          </div>
          <div className="text-2xl font-bold text-primary">
            {formatCurrency(p50)}
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            {unit}
          </div>
        </div>

        {/* P90 - Upper bound */}
        <div className="text-center p-4 bg-muted/50 rounded-lg border border-border hover:border-muted-foreground/20 transition-colors">
          <div className="text-xs font-medium text-muted-foreground mb-2">
            High (P90)
          </div>
          <div className="text-lg font-bold text-foreground">
            {formatCurrency(p90)}
          </div>
        </div>
      </div>

      {/* Confidence indicator */}
      <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg mb-4">
        <span className="text-sm font-medium text-muted-foreground">
          Confidence Level
        </span>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${confidenceColor.includes('green') ? 'bg-green-500' : confidenceColor.includes('yellow') ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
          <span className={`text-sm font-semibold ${confidenceColor}`}>
            {confidenceLevel}
          </span>
        </div>
      </div>

      {/* Visual range bar */}
      <div className="relative h-4 bg-muted rounded-full overflow-hidden mb-6">
        <div
          className="absolute h-full bg-gradient-to-r from-primary/30 via-primary/60 to-primary/30 rounded-full"
          style={{
            left: `${((p10 - p10) / (p90 - p10)) * 100}%`,
            right: `${100 - ((p90 - p10) / (p90 - p10)) * 100}%`,
          }}
        />
        <div
          className="absolute h-full w-1 bg-primary shadow-md"
          style={{
            left: `${((p50 - p10) / (p90 - p10)) * 100}%`,
          }}
        />
      </div>

      {/* Takeaway */}
      {takeaway && (
        <div className="p-4 bg-muted/50 rounded-lg border-l-4 border-primary">
          <p className="text-sm text-foreground leading-relaxed">{takeaway}</p>
        </div>
      )}
    </div>
  );
}
