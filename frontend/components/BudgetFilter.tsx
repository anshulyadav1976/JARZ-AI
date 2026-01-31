"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, PoundSterling } from "lucide-react";

interface BudgetFilterProps {
  onSearch: (budget: number, bedrooms?: number) => void;
}

export function BudgetFilter({ onSearch }: BudgetFilterProps) {
  const [budget, setBudget] = useState("");
  const [bedrooms, setBedrooms] = useState("");

  const handleSearch = () => {
    const budgetNum = parseFloat(budget);
    const bedroomsNum = bedrooms ? parseInt(bedrooms) : undefined;
    
    if (budgetNum > 0) {
      onSearch(budgetNum, bedroomsNum);
    }
  };

  const quickBudgets = [1000, 1500, 2000, 2500, 3000];

  return (
    <div className="p-4 bg-card border border-border rounded-lg space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Search by Budget</h3>

      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Monthly Budget (£)</label>
          <div className="relative">
            <PoundSterling className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="2000"
              className="h-8 text-sm pl-8"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Bedrooms</label>
          <Input
            type="number"
            value={bedrooms}
            onChange={(e) => setBedrooms(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="2"
            min="1"
            max="5"
            className="h-8 text-sm"
          />
        </div>
      </div>

      {/* Quick budget buttons */}
      <div className="space-y-2">
        <p className="text-xs text-muted-foreground">Quick search:</p>
        <div className="flex flex-wrap gap-1.5">
          {quickBudgets.map((amount) => (
            <Button
              key={amount}
              variant="outline"
              size="sm"
              onClick={() => {
                setBudget(amount.toString());
                onSearch(amount, bedrooms ? parseInt(bedrooms) : undefined);
              }}
              className="h-7 px-2.5 text-xs"
            >
              £{amount}
            </Button>
          ))}
        </div>
      </div>

      <Button
        onClick={handleSearch}
        disabled={!budget || parseFloat(budget) <= 0}
        size="sm"
        className="w-full h-8 gap-1.5"
      >
        <Search className="h-3.5 w-3.5" />
        Find Areas
      </Button>
    </div>
  );
}
