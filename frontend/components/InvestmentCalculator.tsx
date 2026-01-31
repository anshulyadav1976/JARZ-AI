"use client";

import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { TrendingUp, Calculator } from "lucide-react";

interface InvestmentCalculatorProps {
  predictedRent: number;
  location: string;
}

export function InvestmentCalculator({ predictedRent, location }: InvestmentCalculatorProps) {
  const [propertyValue, setPropertyValue] = useState("");
  const [rentalYield, setRentalYield] = useState<number | null>(null);
  const [monthlyProfit, setMonthlyProfit] = useState<number | null>(null);

  useEffect(() => {
    if (propertyValue && parseFloat(propertyValue) > 0 && predictedRent > 0) {
      const value = parseFloat(propertyValue);
      const annualRent = predictedRent * 12;
      const yield_ = (annualRent / value) * 100;
      setRentalYield(yield_);

      // Estimate monthly costs (mortgage ~3.5% interest + 20% for maintenance, insurance, etc)
      const monthlyMortgage = (value * 0.035) / 12;
      const monthlyCosts = monthlyMortgage * 1.2;
      const profit = predictedRent - monthlyCosts;
      setMonthlyProfit(profit);
    } else {
      setRentalYield(null);
      setMonthlyProfit(null);
    }
  }, [propertyValue, predictedRent]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2 mb-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">
          <span className="w-1.5 h-1.5 bg-primary rounded-full"></span>
          Investment Calculator
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-4">
        Calculate potential returns for {location}
      </p>

      <div className="space-y-4">
        {/* Property Value Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Property Value (£)
          </label>
          <Input
            type="number"
            value={propertyValue}
            onChange={(e) => setPropertyValue(e.target.value)}
            placeholder="500000"
            className="h-10"
          />
        </div>

        {/* Expected Monthly Rent */}
        <div className="p-3 bg-muted/50 rounded-lg">
          <div className="text-xs text-muted-foreground mb-1">Expected Monthly Rent</div>
          <div className="text-lg font-bold text-foreground">{formatCurrency(predictedRent)}</div>
        </div>

        {/* Results */}
        {rentalYield !== null && (
          <div className="space-y-3 pt-3 border-t border-border">
            {/* Rental Yield */}
            <div className="flex items-center justify-between p-3 bg-primary/5 rounded-lg border border-primary/20">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium text-foreground">Rental Yield</span>
              </div>
              <span className={`text-lg font-bold ${rentalYield >= 5 ? 'text-green-600 dark:text-green-400' : rentalYield >= 3 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}`}>
                {rentalYield.toFixed(2)}%
              </span>
            </div>

            {/* Monthly Cash Flow */}
            {monthlyProfit !== null && (
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Calculator className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-foreground">Est. Monthly Cash Flow</span>
                </div>
                <span className={`text-lg font-bold ${monthlyProfit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {monthlyProfit >= 0 ? '+' : ''}{formatCurrency(monthlyProfit)}
                </span>
              </div>
            )}

            {/* Annual Return */}
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <span className="text-sm font-medium text-foreground">Annual Rental Income</span>
              <span className="text-lg font-bold text-foreground">
                {formatCurrency(predictedRent * 12)}
              </span>
            </div>

            {/* Yield Guidance */}
            <div className="text-xs text-muted-foreground p-3 bg-muted/30 rounded-lg">
              <p className="leading-relaxed">
                {rentalYield >= 5 && "🟢 Strong yield - above market average"}
                {rentalYield >= 3 && rentalYield < 5 && "🟡 Moderate yield - typical for UK market"}
                {rentalYield < 3 && "🔴 Low yield - consider growth potential"}
              </p>
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-muted-foreground mt-4 pt-4 border-t border-border">
        Estimates based on 3.5% mortgage rate and 20% operational costs. Actual returns may vary.
      </p>
    </div>
  );
}
