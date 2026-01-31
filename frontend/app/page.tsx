"use client";

import React, { useState, useCallback } from "react";
import { useAgentStream } from "@/hooks/useAgentStream";
import { A2UIRenderer } from "@/components/A2UIRenderer";
import type { UserQuery } from "@/lib/types";

export default function Home() {
  const [locationInput, setLocationInput] = useState("");
  const [horizonMonths, setHorizonMonths] = useState(6);
  const [kNeighbors, setKNeighbors] = useState(5);
  const { state, startStream, reset } = useAgentStream();

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!locationInput.trim()) return;

      const query: UserQuery = {
        location_input: locationInput.trim(),
        horizon_months: horizonMonths,
        view_mode: "single",
        k_neighbors: kNeighbors,
        radius_km: 5,
      };

      startStream(query);
    },
    [locationInput, horizonMonths, kNeighbors, startStream]
  );

  const handleReset = useCallback(() => {
    reset();
    setLocationInput("");
  }, [reset]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                JARZ Rental Valuation
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Spatio-Temporal Rental Forecasting
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full">
                Demo Mode
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Search Form */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Location Input */}
              <div className="md:col-span-1">
                <label
                  htmlFor="location"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Location / Postcode
                </label>
                <input
                  type="text"
                  id="location"
                  value={locationInput}
                  onChange={(e) => setLocationInput(e.target.value)}
                  placeholder="e.g., NW1, Camden, E14"
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              {/* Horizon Selection */}
              <div>
                <label
                  htmlFor="horizon"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Forecast Horizon
                </label>
                <select
                  id="horizon"
                  value={horizonMonths}
                  onChange={(e) => setHorizonMonths(Number(e.target.value))}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                >
                  <option value={1}>1 month</option>
                  <option value={3}>3 months</option>
                  <option value={6}>6 months</option>
                  <option value={12}>12 months</option>
                </select>
              </div>

              {/* K Neighbors */}
              <div>
                <label
                  htmlFor="neighbors"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Spatial Neighbors
                </label>
                <select
                  id="neighbors"
                  value={kNeighbors}
                  onChange={(e) => setKNeighbors(Number(e.target.value))}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                >
                  <option value={3}>3 neighbors</option>
                  <option value={5}>5 neighbors</option>
                  <option value={7}>7 neighbors</option>
                  <option value={10}>10 neighbors</option>
                </select>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={state.isLoading || !locationInput.trim()}
                className="flex-1 md:flex-none px-8 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-indigo-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
              >
                {state.isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  "Get Forecast"
                )}
              </button>

              {state.isReady && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-all"
                >
                  Reset
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Error Display */}
        {state.error && (
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-8">
            <div className="flex items-center gap-2">
              <svg
                className="w-5 h-5 text-red-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-red-700 dark:text-red-300 font-medium">
                {state.error}
              </span>
            </div>
          </div>
        )}

        {/* Loading State */}
        {state.isLoading && !state.isReady && (
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-12">
            <div className="flex flex-col items-center justify-center">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-blue-200 dark:border-blue-800 rounded-full"></div>
                <div className="absolute top-0 left-0 w-16 h-16 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
              </div>
              <p className="mt-4 text-gray-600 dark:text-gray-400 font-medium">
                Analyzing rental data...
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Building spatio-temporal features
              </p>
            </div>
          </div>
        )}

        {/* Results - A2UI Rendered */}
        {state.isReady && (
          <div className="space-y-6">
            <A2UIRenderer state={state} />
          </div>
        )}

        {/* Empty State */}
        {!state.isLoading && !state.isReady && !state.error && (
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-12">
            <div className="text-center">
              <div className="w-24 h-24 mx-auto mb-6 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                <svg
                  className="w-12 h-12 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Enter a Location to Get Started
              </h2>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                Enter a UK postcode or area name to receive rental forecasts with
                confidence intervals, spatial context, and key market drivers.
              </p>

              {/* Example locations */}
              <div className="mt-8">
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                  Try these example locations:
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {["NW1", "E14", "SW1", "SE1", "N1"].map((loc) => (
                    <button
                      key={loc}
                      onClick={() => setLocationInput(loc)}
                      className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-all text-sm font-medium"
                    >
                      {loc}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white/50 dark:bg-slate-800/50 border-t border-gray-200 dark:border-gray-700 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              JARZ Rental Valuation - RealTech Hackathon 2026
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>Powered by ScanSan Data</span>
              <span>|</span>
              <span>A2UI Generative Interface</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
