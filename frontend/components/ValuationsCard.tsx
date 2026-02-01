"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { ValuationRecord, HistoricalValuationRecord } from "@/lib/types";

function formatCurrency(value?: number | null) {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(value);
}

export interface ValuationsCardProps {
  postcode: string;
  current?: ValuationRecord[];
  historical?: HistoricalValuationRecord[];
}

export function ValuationsCard({ postcode, current = [], historical = [] }: ValuationsCardProps) {
  // Flatten historical for chart: one series per property (first 5) or aggregate
  const historicalSeries = historical.slice(0, 5).flatMap((rec, i) =>
    (rec.valuations || []).map((v) => ({
      date: v.date?.slice(0, 10) ?? v.date,
      [rec.property_address?.slice(0, 20) ?? `Property ${i + 1}`]: v.valuation,
    }))
  );
  // Merge by date for display (simplified: show first property's history if only one)
  const chartData =
    historical.length === 1 && historical[0].valuations?.length
      ? historical[0].valuations.map((v) => ({
          date: v.date?.slice(0, 10) ?? v.date,
          valuation: v.valuation,
        }))
      : historical.length > 1
      ? (() => {
          const byDate: Record<string, { date: string; [key: string]: unknown }> = {};
          historical.forEach((rec, i) => {
            (rec.valuations || []).forEach((v) => {
              const d = v.date?.slice(0, 10) ?? v.date;
              if (!byDate[d]) byDate[d] = { date: d };
              (byDate[d] as Record<string, number>)[`P${i + 1}`] = v.valuation;
            });
          });
          return Object.values(byDate).sort((a, b) => (a.date < b.date ? -1 : 1));
        })()
      : [];

  const hasCurrent = current && current.length > 0;
  const hasHistorical = chartData.length > 0;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
        <span className="w-2 h-2 bg-primary rounded-full" />
        Valuations — {postcode}
      </div>

      {hasCurrent && (
        <>
          <p className="text-sm text-muted-foreground mb-4">Current valuations by address</p>
          <div className="overflow-x-auto max-h-48 overflow-y-auto rounded-xl border border-border mb-4">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 sticky top-0">
                <tr>
                  <th className="text-left p-2 font-semibold text-muted-foreground">Address</th>
                  <th className="text-right p-2 font-semibold text-muted-foreground">Range (min – max)</th>
                  <th className="text-right p-2 font-semibold text-muted-foreground">Last sold</th>
                </tr>
              </thead>
              <tbody>
                {current.slice(0, 15).map((rec, i) => (
                  <tr key={i} className="border-t border-border/50">
                    <td className="p-2 text-foreground truncate max-w-[200px]" title={rec.property_address}>
                      {rec.property_address}
                    </td>
                    <td className="p-2 text-right tabular-nums">
                      {rec.bounded_valuation?.length === 2
                        ? `${formatCurrency(rec.bounded_valuation[0])} – ${formatCurrency(rec.bounded_valuation[1])}`
                        : "—"}
                    </td>
                    <td className="p-2 text-right tabular-nums">
                      {rec.last_sold_price != null ? formatCurrency(rec.last_sold_price) : "—"}
                      {rec.last_sold_date ? ` (${rec.last_sold_date})` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {current.length > 15 && (
            <p className="text-xs text-muted-foreground mb-4">Showing first 15 of {current.length} addresses.</p>
          )}
        </>
      )}

      {hasHistorical && (
        <>
          <p className="text-sm text-muted-foreground mb-4">Historical valuation trend</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 16, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={(v) => (v >= 1000 ? `£${(v / 1000).toFixed(0)}k` : `£${v}`)}
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), "Valuation"]}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend />
                {"valuation" in (chartData[0] || {}) && (
                  <Line
                    type="monotone"
                    dataKey="valuation"
                    name="Valuation"
                    stroke="hsl(var(--chart-1))"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                )}
                {!("valuation" in (chartData[0] || {})) &&
                  Object.keys(chartData[0] || {}).filter((k) => k !== "date").map((key, i) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      name={key}
                      stroke={`hsl(var(--chart-${(i % 5) + 1}))`}
                      strokeWidth={2}
                      dot={{ r: 2 }}
                    />
                  ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {!hasCurrent && !hasHistorical && (
        <p className="text-muted-foreground">No valuation data for this postcode.</p>
      )}

      <p className="mt-4 text-[10px] text-muted-foreground/80">Data: ScanSan valuations API</p>
    </div>
  );
}
