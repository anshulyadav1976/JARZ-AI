"use client";

import React, { useState, useEffect } from "react";
import type { DriversBarProps, Driver } from "@/lib/types";

export function DriversBar({ drivers, base_value }: DriversBarProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [animatedValues, setAnimatedValues] = useState<Record<number, number>>({});

  useEffect(() => {
    setIsVisible(true);
  }, []);

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

  // Animate numbers counting up
  useEffect(() => {
    if (!isVisible) return;

    sortedDrivers.forEach((driver, index) => {
      const targetValue = Math.abs(driver.contribution);
      const duration = 1000;
      const startTime = Date.now() + (index * 100); // Stagger each driver
      
      const animate = () => {
        const now = Date.now();
        const elapsed = now - startTime;
        
        if (elapsed < 0) {
          requestAnimationFrame(animate);
          return;
        }
        
        const progress = Math.min(elapsed / duration, 1);
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = targetValue * easeOutQuart;
        
        setAnimatedValues(prev => ({ ...prev, [index]: currentValue }));
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      
      requestAnimationFrame(animate);
    });
  }, [isVisible, sortedDrivers]);

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 flex-1 min-w-[300px] group">
      <div className="flex items-center gap-2 mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium animate-in fade-in slide-in-from-top-2 duration-500">
          <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></span>
          Key Drivers
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Top factors influencing the rent forecast
      </p>

      {/* Base value indicator */}
      {base_value && (
        <div className="mb-6 p-4 bg-gradient-to-br from-muted/50 to-muted/30 rounded-lg border border-border animate-in fade-in slide-in-from-left-3 duration-700 hover:scale-[1.02] transition-transform">
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
          const animatedValue = animatedValues[i] || 0;
          const animatedBarWidth = (animatedValue / maxContribution) * 100;

          return (
            <div 
              key={i} 
              className="relative p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-all duration-300 hover:scale-[1.02] hover:shadow-md animate-in fade-in slide-in-from-left-4"
              style={{ 
                animationDelay: `${i * 100}ms`,
                animationFillMode: 'backwards'
              }}
            >
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-foreground">
                  {driver.name}
                </span>
                <span
                  className={`text-sm font-bold px-2 py-1 rounded transition-all duration-300 ${
                    isPositive
                      ? "text-green-600 dark:text-green-400 bg-green-500/10 hover:bg-green-500/20"
                      : "text-red-600 dark:text-red-400 bg-red-500/10 hover:bg-red-500/20"
                  }`}
                >
                  {formatValue(isPositive ? animatedValue : -animatedValue)}
                </span>
              </div>
              
              {/* Bar container */}
              <div className="relative h-3 bg-muted rounded-full overflow-hidden">
                {/* Center line for reference */}
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border"></div>
                
                {/* Bar with shimmer effect */}
                <div
                  className={`absolute top-0 h-full rounded-full transition-all duration-1000 ease-out ${
                    isPositive
                      ? "bg-gradient-to-r from-green-500 via-green-600 to-green-500 animate-shimmer"
                      : "bg-gradient-to-l from-red-500 via-red-600 to-red-500 animate-shimmer"
                  }`}
                  style={{
                    width: `${animatedBarWidth / 2}%`,
                    left: isPositive ? "50%" : `${50 - animatedBarWidth / 2}%`,
                    backgroundSize: '200% 100%',
                  }}
                />
              </div>

              {/* Impact indicator with icon animation */}
              <div className="flex justify-center mt-1.5">
                <span className={`text-xs text-muted-foreground flex items-center gap-1 ${isVisible ? 'animate-bounce-subtle' : ''}`}>
                  {isPositive ? "↑ Increases rent" : "↓ Decreases rent"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 animate-in fade-in slide-in-from-bottom-3 duration-1000">
        <div className="flex justify-between items-center p-3 rounded-lg bg-gradient-to-r from-primary/5 to-primary/10 hover:from-primary/10 hover:to-primary/15 transition-all duration-300">
          <span className="text-sm font-medium text-muted-foreground">
            Net Impact
          </span>
          <span className="font-bold text-lg text-foreground animate-pulse-slow">
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
