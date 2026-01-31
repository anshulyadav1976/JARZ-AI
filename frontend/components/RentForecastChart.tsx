"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
  Legend,
} from "recharts";
import type { RentForecastChartProps } from "@/lib/types";

export function RentForecastChart({
  historical,
  forecast,
  unit,
}: RentForecastChartProps) {
  // Combine historical and forecast data
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

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
  };

  // Format currency for tooltip
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      const isHistorical = payload.some((p) => p.name === "historical");
      
      return (
        <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">
            {label ? formatDate(label) : ""}
          </p>
          {isHistorical ? (
            <p className="text-sm">
              <span className="text-gray-500">Rent: </span>
              <span className="font-bold text-gray-900 dark:text-white">
                {formatCurrency(payload[0].value)}
              </span>
            </p>
          ) : (
            <>
              {payload.map((p, i) => (
                <p key={i} className="text-sm">
                  <span className="text-gray-500">
                    {p.name === "p50" ? "Expected: " : p.name === "p10" ? "Low: " : "High: "}
                  </span>
                  <span className="font-bold" style={{ color: p.color }}>
                    {formatCurrency(p.value)}
                  </span>
                </p>
              ))}
            </>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2 mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">
          <span className="w-1.5 h-1.5 bg-primary rounded-full"></span>
          Timeline Forecast
        </div>
      </div>
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Historical data and {forecast.length - 1} month forecast with confidence band
      </div>
      
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={combinedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fontSize: 12 }}
              stroke="#9CA3AF"
            />
            <YAxis
              tickFormatter={(value) => `£${value / 1000}k`}
              tick={{ fontSize: 12 }}
              stroke="#9CA3AF"
              domain={["dataMin - 200", "dataMax + 200"]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Historical line */}
            <Line
              type="monotone"
              dataKey="historical"
              stroke="#6B7280"
              strokeWidth={2}
              dot={{ fill: "#6B7280", r: 3 }}
              name="Historical"
              connectNulls={false}
            />
            
            {/* Forecast confidence band (P10 to P90) */}
            <Area
              type="monotone"
              dataKey="p90"
              stroke="transparent"
              fill="url(#colorBand)"
              name="P90 (High)"
            />
            <Area
              type="monotone"
              dataKey="p10"
              stroke="transparent"
              fill="#FFFFFF"
              name="P10 (Low)"
            />
            
            {/* P50 forecast line */}
            <Line
              type="monotone"
              dataKey="p50"
              stroke="#3B82F6"
              strokeWidth={3}
              dot={{ fill: "#3B82F6", r: 4 }}
              name="Forecast (P50)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-4 flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-gray-500"></div>
          <span className="text-gray-600 dark:text-gray-400">Historical</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-blue-500"></div>
          <span className="text-gray-600 dark:text-gray-400">Forecast</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 bg-blue-500/20 rounded"></div>
          <span className="text-gray-600 dark:text-gray-400">Confidence Band</span>
        </div>
      </div>
    </div>
  );
}
