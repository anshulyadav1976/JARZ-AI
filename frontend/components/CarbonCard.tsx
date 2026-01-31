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
  propertySize: number;
  propertyType: string;
  reductionPercent: number;
  recommendations?: Array<{
    recommendation: string;
    potential_reduction: number;
    cost_estimate: string;
  }>;
}

export function CarbonCard({
  location,
  currentEmissions,
  potentialEmissions,
  emissionsMetric,
  energyRating,
  propertySize,
  propertyType,
  reductionPercent,
  recommendations = [],
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
          <span>Embodied Carbon</span>
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

        {/* Current vs Potential Emissions */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Current Emissions</p>
            <p className="text-2xl font-bold text-red-600">
              {currentEmissions.toFixed(1)}
            </p>
            <p className="text-xs text-muted-foreground">{emissionsMetric}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Potential Emissions</p>
            <p className="text-2xl font-bold text-green-600">
              {potentialEmissions.toFixed(1)}
            </p>
            <p className="text-xs text-muted-foreground">{emissionsMetric}</p>
          </div>
        </div>

        {/* Reduction Potential */}
        <div className="bg-green-50 dark:bg-green-950 p-3 rounded-md">
          <p className="text-sm font-medium">
            Potential Reduction: {reductionPercent.toFixed(0)}%
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Save {(currentEmissions - potentialEmissions).toFixed(1)} {emissionsMetric} with improvements
          </p>
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Recommendations</h4>
            <div className="space-y-2">
              {recommendations.map((rec, index) => (
                <div
                  key={index}
                  className="flex items-start justify-between border-l-2 border-green-500 pl-3 py-1"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium">{rec.recommendation}</p>
                    <p className="text-xs text-muted-foreground">
                      Saves ~{rec.potential_reduction.toFixed(1)} tonnes CO₂/year
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                    {rec.cost_estimate}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Environmental Impact */}
        <div className="pt-2 border-t">
          <p className="text-xs text-muted-foreground">
            💡 Embodied carbon represents the total greenhouse gas emissions from construction,
            operation, and maintenance of this property.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
