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
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow flex-1 min-w-[300px]">
      <div className="flex items-center gap-2 mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">
          <span className="w-1.5 h-1.5 bg-primary rounded-full"></span>
          Key Drivers
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Top factors influencing the rent forecast
      </p>

      {/* Base value indicator */}
      {base_value && (
        <div className="mb-6 p-4 bg-muted/50 rounded-lg border border-border">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-muted-foreground">
              Base Rent
            </span>
            <span className="text-lg font-bold text-foreground">
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
            <div key={i} className="relative p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-foreground">
                  {driver.name}
                </span>
                <span
                  className={`text-sm font-bold px-2 py-1 rounded ${
                    isPositive
                      ? "text-green-600 dark:text-green-400 bg-green-500/10"
                      : "text-red-600 dark:text-red-400 bg-red-500/10"
                  }`}
                >
                  {formatValue(isPositive ? driver.contribution : -driver.contribution)}
                </span>
              </div>
              
              {/* Bar container */}
              <div className="relative h-3 bg-muted rounded-full overflow-hidden">
                {/* Center line for reference */}
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border"></div>
                
                {/* Bar */}
                <div
                  className={`absolute top-0 h-full rounded-full transition-all duration-500 ${
                    isPositive
                      ? "bg-gradient-to-r from-green-500 to-green-600"
                      : "bg-gradient-to-l from-red-500 to-red-600"
                  }`}
                  style={{
                    width: `${barWidth / 2}%`,
                    left: isPositive ? "50%" : `${50 - barWidth / 2}%`,
                  }}
                />
              </div>

              {/* Impact indicator */}
              <div className="flex justify-center mt-1.5">
                <span className="text-xs text-muted-foreground">
                  {isPositive ? "↑ Increases rent" : "↓ Decreases rent"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-border">
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">
            Net Impact
          </span>
          <span className="font-bold text-lg text-foreground tabular-nums">
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
