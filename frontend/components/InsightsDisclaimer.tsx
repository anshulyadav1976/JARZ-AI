"use client";

import React from "react";
import { AlertCircle, Clock } from "lucide-react";

interface InsightsDisclaimerProps {
  dataDate?: string;
  modelVersion?: string;
}

export function InsightsDisclaimer({ 
  dataDate = "January 2026",
  modelVersion = "v1.0"
}: InsightsDisclaimerProps) {
  return (
    <div className="space-y-3 p-4 bg-muted/30 border-t">
      {/* Data Freshness */}
      <div className="flex items-start gap-2 text-xs text-muted-foreground">
        <Clock className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
        <div>
          <span className="font-medium">Data updated:</span> {dataDate} | <span className="font-medium">Model:</span> {modelVersion}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-2 text-xs text-muted-foreground">
        <AlertCircle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
        <p className="leading-relaxed">
          <span className="font-medium">Disclaimer:</span> These predictions are AI-generated estimates for informational purposes only. 
          Actual rental values may vary. Consult with a qualified real estate professional before making property decisions.
        </p>
      </div>

      {/* Data Source Badge */}
      <div className="flex items-center gap-2 pt-2 border-t border-border/50">
        <span className="text-xs text-muted-foreground">Powered by:</span>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold bg-primary/10 text-primary px-2 py-0.5 rounded">ScanSan API</span>
          <span className="text-xs font-semibold bg-primary/10 text-primary px-2 py-0.5 rounded">OpenRouter AI</span>
        </div>
      </div>
    </div>
  );
}
