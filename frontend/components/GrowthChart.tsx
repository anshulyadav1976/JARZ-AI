"use client";

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import type { GrowthDataPoint } from "@/lib/types";

const CHART_COLOR = "hsl(var(--chart-1))";
const FORECAST_COLOR = "hsl(var(--chart-2))";

/** Simple linear regression: y = mx + c, returns [m, c]. */
function linearRegression(x: number[], y: number[]): [number, number] {
  const n = x.length;
  if (n < 2) return [0, y[0] ?? 0];
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  for (let i = 0; i < n; i++) {
    sumX += x[i];
    sumY += y[i];
    sumXY += x[i] * y[i];
    sumX2 += x[i] * x[i];
  }
  const denom = n * sumX2 - sumX * sumX;
  const m = denom !== 0 ? (n * sumXY - sumX * sumY) / denom : 0;
  const c = (sumY - m * sumX) / n;
  return [m, c];
}

/** Get last calendar year from year_month (e.g. "2024-06" -> 2024). */
function lastYearFromPeriod(period: string): number {
  const y = parseInt(period.slice(0, 4), 10);
  return Number.isNaN(y) ? new Date().getFullYear() : y;
}

function formatDate(ym: string) {
  if (!ym) return "";
  const [y, m] = ym.split("-");
  const months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(" ");
  return `${months[parseInt(m || "1", 10) - 1]} ${y?.slice(2) ?? y}`;
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
    notation: "compact",
  }).format(value);
}

export interface GrowthChartProps {
  district: string;
  monthlyData?: GrowthDataPoint[];
  yearlyData?: GrowthDataPoint[];
}

export function GrowthChart({ district, monthlyData = [], yearlyData = [] }: GrowthChartProps) {
  const monthly = (monthlyData || []).map((d) => ({
    period: d.year_month,
    label: formatDate(d.year_month),
    avg_price: d.avg_price,
    change: d.percentage_change,
  }));
  const yearly = (yearlyData || []).map((d) => ({
    period: d.year_month,
    label: formatDate(d.year_month),
    avg_price: d.avg_price,
    change: d.percentage_change,
  }));
  const historical = monthly.length >= yearly.length ? monthly : yearly;
  const isMonthly = monthly.length >= yearly.length;

  // 5-year forecast via linear regression on avg_price vs index
  const { chartData, forecastPoints, lastHistoricalPeriod } = useMemo(() => {
    if (historical.length < 2) {
      return { chartData: historical, forecastPoints: [] as Array<{ period: string; label: string; forecast: number }>, lastHistoricalPeriod: null as string | null };
    }
    const x = historical.map((_, i) => i);
    const y = historical.map((d) => d.avg_price);
    const [m, c] = linearRegression(x, y);
    const n = historical.length;
    const lastPeriod = historical[n - 1].period;
    const lastYear = lastYearFromPeriod(lastPeriod);
    // Bridge point: regression value at last index so forecast line meets trend at end of history
    const forecastPoints: Array<{ period: string; label: string; forecast: number }> = [
      { period: lastPeriod, label: formatDate(lastPeriod), forecast: Math.round(m * (n - 1) + c) },
    ];
    for (let i = 1; i <= 5; i++) {
      const year = lastYear + i;
      const period = `${year}-01`;
      const forecast = Math.round(m * (n + i - 1) + c);
      forecastPoints.push({
        period,
        label: formatDate(period),
        forecast: Math.max(0, forecast),
      });
    }
    const chartData = [
      ...historical.map((d) => ({ ...d, forecast: null as number | null })),
      ...forecastPoints.map((fp) => ({
        period: fp.period,
        label: fp.label,
        avg_price: null as number | null,
        change: null as number | null,
        forecast: fp.forecast,
      })),
    ];
    return {
      chartData,
      forecastPoints,
      lastHistoricalPeriod: historical[n - 1].period,
    };
  }, [historical]);

  const data = chartData;

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; dataKey: string }>;
    label?: string;
  }) => {
    if (!active || !payload?.length) return null;
    const row = data.find((d) => d.period === label);
    const isForecast = row && "forecast" in row && (row as { forecast?: number }).forecast != null;
    const value = (row as { avg_price?: number; forecast?: number })?.avg_price ?? (row as { forecast?: number })?.forecast ?? payload[0]?.value;
    return (
      <div className="bg-card border border-border rounded-xl p-3 shadow-lg">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          {row?.label ?? label}
          {isForecast && <span className="ml-1 text-[10px] text-muted-foreground">(forecast)</span>}
        </p>
        <p className="text-sm font-semibold text-foreground tabular-nums">
          Avg price: {formatCurrency(value ?? 0)}
        </p>
        {row && "change" in row && (row as { change?: number }).change != null && (
          <p className={`text-xs tabular-nums ${(row as { change: number }).change >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
            {(row as { change: number }).change >= 0 ? "+" : ""}{(row as { change: number }).change.toFixed(2)}% change
          </p>
        )}
      </div>
    );
  };

  if (historical.length === 0) {
    return (
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
          <span className="w-2 h-2 bg-primary rounded-full" />
          Price Growth
        </div>
        <p className="text-muted-foreground">No growth data for district {district}.</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
        <span className="w-2 h-2 bg-primary rounded-full" />
        Price Growth — {district}
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        {isMonthly ? "Month-on-month" : "Year-on-year"} average price and % change. 5-year trend forecast (simple linear regression).
      </p>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 16, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis
              dataKey="period"
              tickFormatter={(v) => formatDate(v)}
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
              tickLine={false}
            />
            <YAxis
              yAxisId="price"
              tickFormatter={(v) => formatCurrency(v)}
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis yAxisId="change" orientation="right" hide />
            <Tooltip content={<CustomTooltip />} />
            <Legend formatter={(v) => <span className="text-xs text-muted-foreground">{v}</span>} />
            {lastHistoricalPeriod && (
              <ReferenceLine
                yAxisId="price"
                x={lastHistoricalPeriod}
                stroke="hsl(var(--border))"
                strokeDasharray="4 4"
              />
            )}
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="avg_price"
              name="Avg price"
              stroke={CHART_COLOR}
              strokeWidth={2}
              dot={{ fill: CHART_COLOR, r: 3 }}
              connectNulls={false}
            />
            {forecastPoints.length > 0 && (
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="forecast"
                name="5-year forecast"
                stroke={FORECAST_COLOR}
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={{ fill: FORECAST_COLOR, r: 3 }}
                connectNulls={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-[10px] text-muted-foreground/80">Data: ScanSan district growth API. Forecast: simple linear regression, not a guarantee.</p>
    </div>
  );
}
