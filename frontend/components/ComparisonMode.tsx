"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, X } from "lucide-react";

interface ComparisonModeProps {
  onAddArea: (areaCode: string) => void;
  onRemoveArea: (areaCode: string) => void;
  comparedAreas: string[];
  maxAreas?: number;
}

export function ComparisonMode({
  onAddArea,
  onRemoveArea,
  comparedAreas,
  maxAreas = 3,
}: ComparisonModeProps) {
  const [newArea, setNewArea] = useState("");

  const handleAdd = () => {
    if (newArea.trim() && comparedAreas.length < maxAreas) {
      onAddArea(newArea.toUpperCase().trim());
      setNewArea("");
    }
  };

  const canAddMore = comparedAreas.length < maxAreas;

  return (
    <div className="p-4 bg-card border border-border rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Compare Areas</h3>
        <span className="text-xs text-muted-foreground">
          {comparedAreas.length}/{maxAreas} areas
        </span>
      </div>

      {/* Current areas being compared */}
      {comparedAreas.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {comparedAreas.map((area) => (
            <div
              key={area}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-medium"
            >
              <span>{area}</span>
              <button
                onClick={() => onRemoveArea(area)}
                className="hover:bg-primary/20 rounded-full p-0.5 transition-colors"
                title="Remove"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add new area */}
      {canAddMore && (
        <div className="flex gap-2">
          <Input
            value={newArea}
            onChange={(e) => setNewArea(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="Enter postcode (e.g., E14)"
            className="h-8 text-sm"
          />
          <Button
            onClick={handleAdd}
            size="sm"
            disabled={!newArea.trim()}
            className="h-8 px-3 gap-1"
          >
            <Plus className="h-3.5 w-3.5" />
            Add
          </Button>
        </div>
      )}

      {comparedAreas.length >= 2 && (
        <p className="text-xs text-muted-foreground">
          Chat with: "Compare {comparedAreas.join(" vs ")}"
        </p>
      )}
    </div>
  );
}
