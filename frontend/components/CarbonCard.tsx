"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface CarbonCardProps {
  location: string;
  currentEmissions: number;
  potentialEmissions: number;
  emissionsMetric: string;
  energyRating: string;
  potentialRating: string;
  propertySize: number;
  propertyType: string;
  currentConsumption: number;
  potentialConsumption: number;
  consumptionMetric: string;
  currentEnergyCost: number;
  potentialEnergyCost: number;
  currency: string;
  environmentalScore: number;
  potentialEnvironmentalScore: number;
  efficiencyFeatures: string;
  embodiedCarbonTotal: number;
  embodiedCarbonPerM2: number;
  embodiedCarbonAnnual: number;
  embodiedCarbonA1A3: number;
  embodiedCarbonA4: number;
  embodiedCarbonA5: number;
}

export function CarbonCard({
  location,
  currentEmissions,
  potentialEmissions,
  emissionsMetric,
  energyRating,
  potentialRating,
  propertySize,
  propertyType,
  currentConsumption,
  potentialConsumption,
  consumptionMetric,
  currentEnergyCost,
  potentialEnergyCost,
  currency,
  environmentalScore,
  potentialEnvironmentalScore,
  efficiencyFeatures,
  embodiedCarbonTotal,
  embodiedCarbonPerM2,
  embodiedCarbonAnnual,
  embodiedCarbonA1A3,
  embodiedCarbonA4,
  embodiedCarbonA5,
}: CarbonCardProps) {
  // Determine badge color based on EPC rating
  const getRatingColor = (rating: string) => {
    const ratingMap: Record<string, string> = {
      A: "bg-green-600",
      B: "bg-green-500",
      C: "bg-yellow-500",
      D: "bg-orange-400",
      E: "bg-orange-500",
      F: "bg-red-500",
      G: "bg-red-600",
    };
    return ratingMap[rating] || "bg-gray-500";
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>🌱 Sustainability Assessment</span>
          <Badge className={getRatingColor(energyRating)}>
            EPC: {energyRating}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Location and Property Info */}
        <div>
          <p className="text-sm text-muted-foreground">
            {location} • {propertyType} • {propertySize} m²
          </p>
        </div>

        {/* EPC Rating Progress */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-950 dark:to-blue-950 p-4 rounded-md">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-xs text-muted-foreground">Current Rating</p>
              <Badge className={getRatingColor(energyRating)} variant="default">
                {energyRating}
              </Badge>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">→</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Potential</p>
              <Badge className={getRatingColor(potentialRating)} variant="outline">
                {potentialRating}
              </Badge>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Environmental Score: {environmentalScore}/100 → {potentialEnvironmentalScore}/100
          </p>
        </div>

        {/* Energy Consumption */}
        <div className="bg-amber-50 dark:bg-amber-950 p-3 rounded-md">
          <h4 className="text-sm font-semibold mb-2">⚡ Energy Consumption</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Current</p>
              <p className="text-2xl font-bold text-orange-600">
                {currentConsumption.toFixed(0)}
              </p>
              <p className="text-xs text-muted-foreground">{consumptionMetric}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Potential</p>
              <p className="text-2xl font-bold text-green-600">
                {potentialConsumption.toFixed(0)}
              </p>
              <p className="text-xs text-muted-foreground">{consumptionMetric}</p>
            </div>
          </div>
        </div>

        {/* Energy Costs */}
        <div className="bg-emerald-50 dark:bg-emerald-950 p-3 rounded-md">
          <h4 className="text-sm font-semibold mb-2">💰 Annual Energy Costs</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Current</p>
              <p className="text-2xl font-bold text-red-600">
                {currency}{currentEnergyCost.toFixed(0)}
              </p>
              <p className="text-xs text-muted-foreground">per year</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Potential</p>
              <p className="text-2xl font-bold text-green-600">
                {currency}{potentialEnergyCost.toFixed(0)}
              </p>
              <p className="text-xs text-muted-foreground">per year</p>
            </div>
          </div>
          <div className="mt-2 pt-2 border-t border-emerald-200 dark:border-emerald-800">
            <p className="text-sm font-medium text-green-700 dark:text-green-400">
              💵 Save {currency}{(currentEnergyCost - potentialEnergyCost).toFixed(0)}/year
              ({(((currentEnergyCost - potentialEnergyCost) / currentEnergyCost) * 100).toFixed(0)}% reduction)
            </p>
          </div>
        </div>

        {/* CO2 Emissions */}
        <div>
          <h4 className="text-sm font-semibold mb-2">🏭 Operational CO2</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Current</p>
              <p className="text-2xl font-bold text-red-600">
                {currentEmissions.toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">{emissionsMetric}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Potential</p>
              <p className="text-2xl font-bold text-green-600">
                {potentialEmissions.toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">{emissionsMetric}</p>
            </div>
          </div>
        </div>

        {/* Embodied Carbon - EN 15978 */}
        <div className="bg-purple-50 dark:bg-purple-950 p-4 rounded-md">
          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
            🏗️ Embodied Carbon (EN 15978)
            <span className="text-xs font-normal text-muted-foreground">A1-A5</span>
          </h4>
          
          <div className="space-y-3">
            {/* Total & Intensity */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Total (A1-A5)</p>
                <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">
                  {embodiedCarbonTotal.toFixed(1)}
                </p>
                <p className="text-xs text-muted-foreground">tonnes CO₂e</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Intensity</p>
                <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">
                  {embodiedCarbonPerM2.toFixed(0)}
                </p>
                <p className="text-xs text-muted-foreground">kg CO₂e/m²</p>
              </div>
            </div>

            {/* Stage breakdown */}
            <div className="pt-2 border-t border-purple-200 dark:border-purple-800">
              <p className="text-xs font-medium mb-2">Stage Breakdown:</p>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">A1-A3 (Materials + Manufacturing)</span>
                  <span className="font-medium">{embodiedCarbonA1A3.toFixed(1)} t CO₂e</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">A4 (Transportation)</span>
                  <span className="font-medium">{embodiedCarbonA4.toFixed(1)} t CO₂e</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">A5 (Construction)</span>
                  <span className="font-medium">{embodiedCarbonA5.toFixed(1)} t CO₂e</span>
                </div>
              </div>
            </div>

            {/* Annualized */}
            <div className="pt-2 border-t border-purple-200 dark:border-purple-800">
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">Annualized (60-year lifespan)</span>
                <span className="text-sm font-bold text-purple-700 dark:text-purple-400">
                  {embodiedCarbonAnnual.toFixed(2)} t/year
                </span>
              </div>
            </div>

            {/* Total annual footprint */}
            <div className="pt-2 border-t-2 border-purple-300 dark:border-purple-700 bg-purple-100 dark:bg-purple-900 -mx-4 -mb-4 px-4 py-3 rounded-b-md">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold">Total Annual Carbon Footprint</span>
                <span className="text-xl font-bold text-purple-800 dark:text-purple-300">
                  {(currentEmissions + embodiedCarbonAnnual).toFixed(2)} t/year
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Operational ({currentEmissions.toFixed(1)}t) + Embodied ({embodiedCarbonAnnual.toFixed(2)}t)
              </p>
            </div>
          </div>
        </div>

        {/* Efficiency Features */}
        <div className="bg-blue-50 dark:bg-blue-950 p-3 rounded-md">
          <h4 className="text-sm font-semibold mb-1">✨ Key Features</h4>
          <p className="text-sm text-muted-foreground">
            {efficiencyFeatures}
          </p>
        </div>

        {/* Environmental Impact */}
        <div className="pt-2 border-t">
          <p className="text-xs text-muted-foreground">
            📊 This comprehensive sustainability assessment analyzes energy performance, costs, and environmental impact to support informed property investment decisions.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
