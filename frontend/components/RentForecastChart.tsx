"use client";

import React from "react";
import {
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
  Legend,
  ReferenceLine,
} from "recharts";
import type { RentForecastChartProps } from "@/lib/types";

const CHART_COLORS = {
  historical: "hsl(var(--muted-foreground))",
  forecast: "hsl(var(--chart-1))",
  band: "hsl(var(--chart-1) / 0.25)",
};

export function RentForecastChart({
  historical,
  forecast,
  unit,
}: RentForecastChartProps) {
  const combinedData = [
    ...historical.map((h) => ({
      date: h.date,
      historical: h.rent,
      isHistorical: true,
    })),
    ...forecast.map((f) => ({
      date: f.date,
      p10: f.p10,
      p50: f.p50,
      p90: f.p90,
      isForecast: true,
    })),
  ];

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatAxis = (value: number) =>
    value >= 1000 ? `£${(value / 1000).toFixed(1)}k` : `£${value}`;

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string }>;
    label?: string;
  }) => {
    if (!active || !payload?.length) return null;
    const isHistorical = payload.some((p) => p.name === "historical");
    return (
      <div className="bg-card border border-border rounded-xl p-3 shadow-lg">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          {label ? formatDate(label) : ""}
        </p>
        {isHistorical ? (
          <p className="text-sm">
            <span className="text-muted-foreground">Rent </span>
            <span className="font-bold text-foreground tabular-nums">
              {formatCurrency(payload[0].value)}
            </span>
          </p>
        ) : (
          <div className="space-y-1">
            {payload
              .filter((p) => p.value != null && !Number.isNaN(p.value))
              .map((p, i) => (
                <p key={i} className="text-sm flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    {p.name === "p50"
                      ? "Expected"
                      : p.name === "p10"
                      ? "Low (P10)"
                      : "High (P90)"}
                  </span>
                  <span className="font-semibold tabular-nums" style={{ color: p.color }}>
                    {formatCurrency(p.value)}
                  </span>
                </p>
              ))}
          </div>
        )}
      </div>
    );
  };

  const lastHistorical = historical.length ? historical[historical.length - 1]?.date : null;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="flex items-center gap-2 mb-2">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide">
          <span className="w-2 h-2 bg-primary rounded-full" />
          Timeline Forecast
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Historical rent and {forecast.length}‑month forecast with P10–P90 band
      </p>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={combinedData}
            margin={{ top: 10, right: 16, left: 8, bottom: 0 }}
          >
            <defs>
              <linearGradient id="forecastBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={CHART_COLORS.forecast} stopOpacity={0.35} />
                <stop offset="100%" stopColor={CHART_COLORS.forecast} stopOpacity={0.06} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={formatAxis}
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              domain={["dataMin - 100", "dataMax + 100"]}
              label={{
                value: "Rent (£)",
                angle: -90,
                position: "insideLeft",
                style: { fontSize: 11, fill: "hsl(var(--muted-foreground))" },
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            {lastHistorical && (
              <ReferenceLine
                x={lastHistorical}
                stroke="hsl(var(--border))"
                strokeDasharray="4 4"
              />
            )}
            <Legend
              wrapperStyle={{ paddingTop: 8 }}
              formatter={(value) => (
                <span className="text-xs text-muted-foreground">{value}</span>
              )}
            />

            <Line
              type="monotone"
              dataKey="historical"
              stroke={CHART_COLORS.historical}
              strokeWidth={2}
              dot={{ fill: CHART_COLORS.historical, r: 3 }}
              name="Historical"
              connectNulls={false}
            />
            <Area
              type="monotone"
              dataKey="p90"
              stroke="transparent"
              fill="url(#forecastBand)"
              name="P10–P90 band"
            />
            <Area
              type="monotone"
              dataKey="p10"
              stroke="transparent"
              fill="var(--background)"
              name=""
            />
            <Line
              type="monotone"
              dataKey="p50"
              stroke={CHART_COLORS.forecast}
              strokeWidth={3}
              dot={{ fill: CHART_COLORS.forecast, r: 4 }}
              name="Forecast (P50)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground">
        <span className="flex items-center gap-2">
          <span className="w-6 h-0.5 rounded bg-muted-foreground/80" /> Historical
        </span>
        <span className="flex items-center gap-2">
          <span className="w-6 h-0.5 rounded" style={{ backgroundColor: CHART_COLORS.forecast }} /> Forecast
        </span>
        <span className="flex items-center gap-2">
          <span className="w-4 h-2.5 rounded opacity-60" style={{ backgroundColor: CHART_COLORS.band }} /> Confidence band
        </span>
      </div>
    </div>
  );
}
