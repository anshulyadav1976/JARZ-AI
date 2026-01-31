"use client";

import React from "react";
import type { DriversBarProps, Driver } from "@/lib/types";

export function DriversBar({ drivers, base_value }: DriversBarProps) {
  // Sort by absolute contribution
  const sortedDrivers = [...drivers].sort(
    (a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)
  );

  // Find max contribution for scaling
  const maxContribution = Math.max(
    ...drivers.map((d) => Math.abs(d.contribution)),
    1
  );

  const formatValue = (value: number) => {
    const prefix = value >= 0 ? "+" : "";
    return `${prefix}£${Math.abs(value).toFixed(0)}`;
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg flex-1 min-w-[300px]">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        Prediction Drivers
      </h3>
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Top factors influencing the rent forecast
      </div>

      {/* Base value indicator */}
      {base_value && (
        <div className="mb-4 p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Base Rent
            </span>
            <span className="font-semibold text-gray-900 dark:text-white">
              £{base_value.toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Driver bars */}
      <div className="space-y-3">
        {sortedDrivers.map((driver, i) => {
          const isPositive = driver.direction === "positive";
          const barWidth = (Math.abs(driver.contribution) / maxContribution) * 100;

          return (
            <div key={i} className="relative">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {driver.name}
                </span>
                <span
                  className={`text-sm font-semibold ${
                    isPositive
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {formatValue(isPositive ? driver.contribution : -driver.contribution)}
                </span>
              </div>
              
              {/* Bar container */}
              <div className="relative h-4 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden">
                {/* Center line for reference */}
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-300 dark:bg-gray-600"></div>
                
                {/* Bar */}
                <div
                  className={`absolute top-0 h-full rounded transition-all duration-500 ${
                    isPositive
                      ? "bg-gradient-to-r from-green-400 to-green-500"
                      : "bg-gradient-to-l from-red-400 to-red-500"
                  }`}
                  style={{
                    width: `${barWidth / 2}%`,
                    left: isPositive ? "50%" : `${50 - barWidth / 2}%`,
                  }}
                />
              </div>

              {/* Impact indicator */}
              <div className="flex justify-center mt-1">
                <span className="text-xs text-gray-400">
                  {isPositive ? "↑ Increases rent" : "↓ Decreases rent"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Net Impact
          </span>
          <span className="font-bold text-lg text-gray-900 dark:text-white">
            {formatValue(
              drivers.reduce(
                (sum, d) =>
                  sum + (d.direction === "positive" ? d.contribution : -d.contribution),
                0
              )
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
