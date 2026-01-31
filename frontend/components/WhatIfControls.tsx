"use client";

import React from "react";
import type { WhatIfControlsProps } from "@/lib/types";

export function WhatIfControls({
  currentHorizon,
  currentRadius,
  currentKNeighbors,
  onHorizonChange,
  onRadiusChange,
  onKNeighborsChange,
  onCompareToggle,
  compareMode,
}: WhatIfControlsProps) {
  const horizonOptions = [1, 3, 6, 12];
  const kNeighborsOptions = [3, 5, 7, 10];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        What-If Analysis
      </h3>

      {/* Horizon Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Forecast Horizon
        </label>
        <div className="flex gap-2">
          {horizonOptions.map((months) => (
            <button
              key={months}
              onClick={() => onHorizonChange(months)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentHorizon === months
                  ? "bg-blue-500 text-white shadow-md"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
              }`}
            >
              {months}m
            </button>
          ))}
        </div>
      </div>

      {/* K Neighbors Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Spatial Neighbors (k)
        </label>
        <div className="flex gap-2">
          {kNeighborsOptions.map((k) => (
            <button
              key={k}
              onClick={() => onKNeighborsChange(k)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentKNeighbors === k
                  ? "bg-blue-500 text-white shadow-md"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
              }`}
            >
              {k}
            </button>
          ))}
        </div>
      </div>

      {/* Radius Slider */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Search Radius: {currentRadius} km
        </label>
        <input
          type="range"
          min="1"
          max="15"
          value={currentRadius}
          onChange={(e) => onRadiusChange(Number(e.target.value))}
          className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
          <span>1 km</span>
          <span>15 km</span>
        </div>
      </div>

      {/* Compare Mode Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Compare Mode
          </span>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Compare two areas side by side
          </p>
        </div>
        <button
          onClick={onCompareToggle}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            compareMode ? "bg-blue-500" : "bg-gray-300 dark:bg-gray-600"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              compareMode ? "translate-x-6" : "translate-x-1"
            }`}
          />
        </button>
      </div>

      {/* Apply Button */}
      <button className="w-full mt-6 px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-medium rounded-lg hover:from-blue-600 hover:to-indigo-600 transition-all shadow-md hover:shadow-lg">
        Apply Changes
      </button>
    </div>
  );
}
