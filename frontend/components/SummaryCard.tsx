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
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-700 rounded-xl p-6 shadow-lg">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-600 dark:text-gray-300">
            Rental Forecast
          </h2>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
            {location}
          </h3>
        </div>
        <div className="text-right">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {horizon_months} month horizon
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* P10 - Lower bound */}
        <div className="text-center p-4 bg-white/50 dark:bg-slate-600/50 rounded-lg">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
            Low (P10)
          </div>
          <div className="text-xl font-bold text-gray-700 dark:text-gray-200">
            {formatCurrency(p10)}
          </div>
        </div>

        {/* P50 - Median */}
        <div className="text-center p-4 bg-blue-100 dark:bg-blue-900/50 rounded-lg border-2 border-blue-300 dark:border-blue-700">
          <div className="text-sm text-blue-600 dark:text-blue-300 mb-1 font-medium">
            Expected (P50)
          </div>
          <div className="text-2xl font-bold text-blue-700 dark:text-blue-200">
            {formatCurrency(p50)}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {unit}
          </div>
        </div>

        {/* P90 - Upper bound */}
        <div className="text-center p-4 bg-white/50 dark:bg-slate-600/50 rounded-lg">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
            High (P90)
          </div>
          <div className="text-xl font-bold text-gray-700 dark:text-gray-200">
            {formatCurrency(p90)}
          </div>
        </div>
      </div>

      {/* Confidence indicator */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Confidence Level
        </span>
        <span className={`font-semibold ${confidenceColor}`}>
          {confidenceLevel}
        </span>
      </div>

      {/* Visual range bar */}
      <div className="relative h-3 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden mb-4">
        <div
          className="absolute h-full bg-gradient-to-r from-blue-300 via-blue-500 to-blue-300 rounded-full"
          style={{
            left: `${((p10 - p10) / (p90 - p10)) * 100}%`,
            right: `${100 - ((p90 - p10) / (p90 - p10)) * 100}%`,
          }}
        />
        <div
          className="absolute h-full w-1 bg-blue-700 dark:bg-blue-300"
          style={{
            left: `${((p50 - p10) / (p90 - p10)) * 100}%`,
          }}
        />
      </div>

      {/* Takeaway */}
      {takeaway && (
        <div className="mt-4 p-3 bg-white/70 dark:bg-slate-600/70 rounded-lg">
          <p className="text-sm text-gray-700 dark:text-gray-300">{takeaway}</p>
        </div>
      )}
    </div>
  );
}
