"use client";

import React, { useMemo } from "react";
import type { AreaSummaryComparisonRow, LocationComparisonRangesProps } from "@/lib/types";

const RANGE_COLORS = {
  rent: "hsl(var(--chart-1))",
  sale: "hsl(var(--chart-2))",
  sold: "hsl(var(--chart-3))",
};

function formatCurrency(value?: number | null, compact = false) {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
    notation: compact ? "compact" : "standard",
  }).format(value);
}

function getRange(row: AreaSummaryComparisonRow, kind: "rent" | "sale" | "sold") {
  if (kind === "rent") return [row.rent_pcm_min, row.rent_pcm_max] as const;
  if (kind === "sale") return [row.sale_price_min, row.sale_price_max] as const;
  return [row.sold_price_min, row.sold_price_max] as const;
}

export function LocationComparisonRanges({ areas }: LocationComparisonRangesProps) {
  const scales = useMemo(() => {
    const all = {
      rent: [] as number[],
      sale: [] as number[],
      sold: [] as number[],
    };
    for (const a of areas) {
      for (const [k, vals] of [
        ["rent", getRange(a, "rent")],
        ["sale", getRange(a, "sale")],
        ["sold", getRange(a, "sold")],
      ] as const) {
        const [lo, hi] = vals;
        if (typeof lo === "number") all[k].push(lo);
        if (typeof hi === "number") all[k].push(hi);
      }
    }
    const mk = (arr: number[]) => {
      const min = arr.length ? Math.min(...arr) : 0;
      const max = arr.length ? Math.max(...arr) : 1;
      return { min, max: Math.max(max, min + 1) };
    };
    return {
      rent: mk(all.rent),
      sale: mk(all.sale),
      sold: mk(all.sold),
    };
  }, [areas]);

  const RangeRow = ({
    label,
    kind,
    compact,
    color,
  }: {
    label: string;
    kind: "rent" | "sale" | "sold";
    compact?: boolean;
    color: string;
  }) => {
    const { min, max } = scales[kind];
    const hasScale = max > min;
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            {label}
          </span>
          {hasScale && (
            <span className="text-[10px] text-muted-foreground/80 tabular-nums">
              Scale: {formatCurrency(min, compact)} – {formatCurrency(max, compact)}
            </span>
          )}
        </div>
        <div className="space-y-3">
          {areas.map((a) => {
            const [lo, hi] = getRange(a, kind);
            const has = typeof lo === "number" && typeof hi === "number";
            const left = has && hasScale ? ((lo! - min) / (max - min)) * 100 : 0;
            const width = has && hasScale ? (Math.max(lo!, hi!) - Math.min(lo!, hi!)) / (max - min) * 100 : 0;
            const barLeft = has && hasScale ? ((Math.min(lo!, hi!) - min) / (max - min)) * 100 : 0;
            return (
              <div key={`${kind}-${a.area_code}`} className="flex items-center gap-3">
                <div className="w-14 text-xs font-semibold text-foreground tabular-nums shrink-0">
                  {a.area_code}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="h-4 bg-muted/60 rounded-lg overflow-hidden border border-border/50 relative">
                    {has ? (
                      <div
                        className="absolute top-0 bottom-0 rounded-md transition-all"
                        style={{
                          left: `${barLeft}%`,
                          width: `${Math.max(4, width)}%`,
                          backgroundColor: color,
                          opacity: 0.85,
                        }}
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center text-[10px] text-muted-foreground">
                        No data
                      </div>
                    )}
                  </div>
                </div>
                <div className="w-36 text-right text-xs text-muted-foreground tabular-nums shrink-0">
                  {formatCurrency(lo, compact)} – {formatCurrency(hi, compact)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
        <span className="w-2 h-2 bg-primary rounded-full" />
        Price Ranges
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Ranges scaled across selected areas. Bars show relative position and width.
      </p>

      <div className="space-y-8">
        <RangeRow label="Rent (pcm range)" kind="rent" color={RANGE_COLORS.rent} />
        <RangeRow label="Sale listings (price range)" kind="sale" compact color={RANGE_COLORS.sale} />
        <RangeRow label="Sold (last 5 years)" kind="sold" compact color={RANGE_COLORS.sold} />
      </div>

      <p className="mt-4 text-[10px] text-muted-foreground/80">
        Data: ScanSan area summary API
      </p>
    </div>
  );
}

