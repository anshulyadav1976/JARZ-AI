"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle2, Info, Calculator, PiggyBank, Calendar } from "lucide-react";

interface InvestmentData {
  property_value?: number;
  predicted_rent?: number;
  gross_yield?: number;
  net_yield?: number;
  monthly_cash_flow?: number;
  annual_roi?: number;
  break_even_years?: number;
  monthly_mortgage?: number;
  monthly_costs?: number;
  deposit_amount?: number;
  ml_roi_1yr?: number;
  ml_roi_3yr?: number;
  ml_roi_5yr?: number;
  ml_available?: boolean;
  mortgage_rate?: number;
  rate_source?: string;
  operating_costs_total?: number;
  operating_costs_percentage?: number;
  operating_costs_energy?: number;
  operating_costs_insurance?: number;
  operating_costs_management?: number;
  operating_costs_maintenance?: number;
  operating_costs_void?: number;
  energy_cost_source?: string;
}

interface InvestmentAnalysisViewProps {
  data: InvestmentData;
  location: string;
}

export function InvestmentAnalysisView({ data, location }: InvestmentAnalysisViewProps) {
  const {
    property_value = 0,
    predicted_rent = 0,
    gross_yield = 0,
    net_yield = 0,
    monthly_cash_flow = 0,
    annual_roi = 0,
    break_even_years = 0,
    monthly_mortgage = 0,
    monthly_costs = 0,
    deposit_amount = 0,
    ml_roi_1yr = 0,
    ml_roi_3yr = 0,
    ml_roi_5yr = 0,
    ml_available = false,
    mortgage_rate = 0,
    rate_source = "",
    operating_costs_total = 0,
    operating_costs_percentage = 0,
    operating_costs_energy = 0,
    operating_costs_insurance = 0,
    operating_costs_management = 0,
    operating_costs_maintenance = 0,
    operating_costs_void = 0,
    energy_cost_source = "",
  } = data;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getYieldQuality = (yield_: number) => {
    if (yield_ >= 5) return { label: "Excellent", color: "text-green-600 dark:text-green-400", bg: "bg-green-50 dark:bg-green-950" };
    if (yield_ >= 3) return { label: "Good", color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-50 dark:bg-blue-950" };
    return { label: "Below Average", color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-950" };
  };

  const yieldQuality = getYieldQuality(gross_yield);

  return (
    <div className="space-y-6">
      {/* Header Summary */}
      <Card className="p-6 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-foreground mb-1">{location}</h3>
            <p className="text-sm text-muted-foreground">Investment Analysis</p>
          </div>
          <Badge className={`${yieldQuality.bg} ${yieldQuality.color} border-0`}>
            {yieldQuality.label}
          </Badge>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Property Value</p>
            <p className="text-2xl font-bold text-foreground">{formatCurrency(property_value)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Monthly Rent</p>
            <p className="text-2xl font-bold text-foreground">{formatCurrency(predicted_rent)}</p>
          </div>
        </div>
      </Card>

      {/* Total Return Analysis - HOW YOU ACTUALLY MAKE MONEY - MOVED TO TOP */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h4 className="font-semibold text-foreground">Total Return Analysis</h4>
        </div>
        
        <div className="mb-4 p-3 bg-muted rounded-lg">
          <p className="text-sm text-muted-foreground">
            <strong>Note:</strong> In this area, investment returns come from property price growth and rental income combined. 
            Property values typically appreciate 5-7% annually.
          </p>
        </div>

        <div className="space-y-4">
          {/* Current Annual Rental Cash Flow */}
          <div className="p-3 bg-muted rounded-lg border border-border">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-muted-foreground">Annual Rental Cash Flow (Rent - Costs - Mortgage)</span>
              <span className={`text-lg font-bold ${monthly_cash_flow * 12 >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {monthly_cash_flow * 12 >= 0 ? '+' : ''}{formatCurrency(monthly_cash_flow * 12)}/year
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              This is your rental profit/loss before property appreciation
            </p>
          </div>

          {/* 5% Growth Scenario */}
          <div className="p-4 bg-muted rounded-lg border border-border">
            <p className="text-xs font-semibold text-foreground mb-3">With 5% Annual Property Growth (Conservative)</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Property Value Gain</span>
                <span className="text-base font-semibold text-green-600 dark:text-green-400">+{formatCurrency(property_value * 0.05)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Annual Rental Cash Flow</span>
                <span className={`text-base font-semibold ${monthly_cash_flow * 12 >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {monthly_cash_flow * 12 >= 0 ? '+' : ''}{formatCurrency(monthly_cash_flow * 12)}
                </span>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-border">
                <span className="font-bold text-foreground">Total Annual Profit</span>
                <span className={`text-lg font-bold ${(property_value * 0.05 + monthly_cash_flow * 12) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {(property_value * 0.05 + monthly_cash_flow * 12) >= 0 ? '+' : ''}{formatCurrency(property_value * 0.05 + monthly_cash_flow * 12)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">ROI on {formatCurrency(deposit_amount)} deposit</span>
                <span className={`text-base font-semibold ${((property_value * 0.05 + monthly_cash_flow * 12) / deposit_amount * 100) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {((property_value * 0.05 + monthly_cash_flow * 12) / deposit_amount * 100) >= 0 ? '+' : ''}{((property_value * 0.05 + monthly_cash_flow * 12) / deposit_amount * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* 7% Growth Scenario */}
          <div className="p-4 bg-muted rounded-lg">
            <p className="text-xs font-semibold text-foreground mb-3">With 7% Annual Property Growth (Historical Average)</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground">Total Annual Profit</span>
                <span className={`text-lg font-bold ${(property_value * 0.07 + monthly_cash_flow * 12) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {(property_value * 0.07 + monthly_cash_flow * 12) >= 0 ? '+' : ''}{formatCurrency(property_value * 0.07 + monthly_cash_flow * 12)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">ROI on deposit</span>
                <span className={`text-base font-semibold ${((property_value * 0.07 + monthly_cash_flow * 12) / deposit_amount * 100) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {((property_value * 0.07 + monthly_cash_flow * 12) / deposit_amount * 100) >= 0 ? '+' : ''}{((property_value * 0.07 + monthly_cash_flow * 12) / deposit_amount * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Yield Metrics */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h4 className="font-semibold text-foreground">Rental Yield</h4>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">Gross Yield</p>
            <p className="text-2xl font-bold text-foreground mb-1">{gross_yield.toFixed(2)}%</p>
            <p className="text-xs text-muted-foreground">Before costs</p>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">Net Yield</p>
            <p className="text-2xl font-bold text-foreground mb-1">{net_yield.toFixed(2)}%</p>
            <p className="text-xs text-muted-foreground">After all costs</p>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-2">
            <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-blue-900 dark:text-blue-100">
              UK average gross yield: 4-5%. Yields above 5% are considered excellent, 3-5% good, below 3% may indicate capital growth focus.
            </p>
          </div>
        </div>
      </Card>

      {/* Cash Flow */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calculator className="h-5 w-5 text-primary" />
          <h4 className="font-semibold text-foreground">Monthly Cash Flow</h4>
          {rate_source && (
            <Badge variant="outline" className="text-xs">{rate_source}</Badge>
          )}
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-muted-foreground">Rental Income</span>
            <span className="text-base font-semibold text-green-600 dark:text-green-400">+{formatCurrency(predicted_rent)}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-border">
            <span className="text-sm text-muted-foreground">
              Mortgage Payment {mortgage_rate > 0 && `(${mortgage_rate.toFixed(1)}%)`}
            </span>
            <span className="text-base font-semibold text-red-600 dark:text-red-400">-{formatCurrency(monthly_mortgage)}</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-muted-foreground">
              Operating Costs ({operating_costs_percentage > 0 ? operating_costs_percentage.toFixed(0) : '25'}%)
            </span>
            <span className="text-base font-semibold text-red-600 dark:text-red-400">-{formatCurrency(operating_costs_total || (monthly_costs - monthly_mortgage))}</span>
          </div>
          <div className="flex items-center justify-between py-3 border-t-2 border-border bg-muted/30 -mx-6 px-6">
            <span className="font-semibold text-foreground">Net Monthly Cash Flow</span>
            <div className="flex items-center gap-2">
              {monthly_cash_flow >= 0 ? (
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
              )}
              <span className={`text-lg font-bold ${monthly_cash_flow >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {monthly_cash_flow >= 0 ? '+' : ''}{formatCurrency(monthly_cash_flow)}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Operating Costs Breakdown */}
      {operating_costs_total > 0 && (
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Info className="h-5 w-5 text-primary" />
            <h4 className="font-semibold text-foreground">Operating Costs Breakdown</h4>
            {energy_cost_source && (
              <Badge variant="outline" className="text-xs">{energy_cost_source}</Badge>
            )}
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between py-1.5">
              <span className="text-xs text-muted-foreground">Energy Bills</span>
              <span className="text-sm font-medium text-foreground">{formatCurrency(operating_costs_energy)}/mo</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-xs text-muted-foreground">Landlord Insurance</span>
              <span className="text-sm font-medium text-foreground">{formatCurrency(operating_costs_insurance)}/mo</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-xs text-muted-foreground">Management Fees (12%)</span>
              <span className="text-sm font-medium text-foreground">{formatCurrency(operating_costs_management)}/mo</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-xs text-muted-foreground">Maintenance</span>
              <span className="text-sm font-medium text-foreground">{formatCurrency(operating_costs_maintenance)}/mo</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-xs text-muted-foreground">Void Allowance (8.3%)</span>
              <span className="text-sm font-medium text-foreground">{formatCurrency(operating_costs_void)}/mo</span>
            </div>
            <div className="flex items-center justify-between py-2 border-t border-border mt-2 pt-3">
              <span className="text-sm font-semibold text-foreground">Total Operating Costs</span>
              <span className="text-base font-bold text-foreground">{formatCurrency(operating_costs_total)}/mo</span>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-muted rounded-lg">
            <p className="text-xs text-muted-foreground">
              <strong>Note:</strong> Operating costs include energy (from {energy_cost_source || 'estimates'}), 
              insurance, property management, maintenance reserve, and void periods (average 1 month/year).
            </p>
          </div>
        </Card>
      )}

      {/* ROI & Break-even */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <PiggyBank className="h-5 w-5 text-primary" />
          <h4 className="font-semibold text-foreground">Return on Investment</h4>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">Initial Investment</p>
            <p className="text-lg font-bold text-foreground">{formatCurrency(deposit_amount)}</p>
            <p className="text-xs text-muted-foreground mt-1">25% deposit</p>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">Rental Cash Flow ROI</p>
            <p className={`text-lg font-bold ${annual_roi >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {annual_roi >= 0 ? '+' : ''}{annual_roi.toFixed(1)}%
            </p>
            <p className="text-xs text-muted-foreground mt-1">Excludes capital appreciation</p>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-muted rounded-lg">
          <p className="text-xs text-muted-foreground">
            <strong>Note:</strong> The rental cash flow ROI shows rental income only. See Total Return Analysis above for complete returns including property value growth.
          </p>
        </div>
        
        {break_even_years > 0 && break_even_years < 50 && (
          <div className="mt-4 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <p className="text-xs text-muted-foreground">Break-even Period</p>
            </div>
            <p className="text-xl font-bold text-foreground">{break_even_years.toFixed(1)} years</p>
            <p className="text-xs text-muted-foreground mt-1">Time to recover initial investment from cash flow</p>
          </div>
        )}
      </Card>

      {/* ML Predictions */}
      {ml_available && (ml_roi_1yr > 0 || ml_roi_3yr > 0 || ml_roi_5yr > 0) && (
        <Card className="p-6 border-2 border-purple-200 dark:border-purple-800 bg-gradient-to-br from-purple-50 to-white dark:from-purple-950/20 dark:to-background">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
              <TrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h4 className="font-semibold text-foreground">🤖 AI Investment Forecast</h4>
              <p className="text-xs text-muted-foreground">Machine learning-powered predictions</p>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-purple-200 dark:border-purple-800">
              <p className="text-xs text-muted-foreground mb-1">1-Year ROI</p>
              <p className="text-lg font-bold text-purple-600 dark:text-purple-400">{ml_roi_1yr.toFixed(1)}%</p>
            </div>
            <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-purple-200 dark:border-purple-800">
              <p className="text-xs text-muted-foreground mb-1">3-Year ROI</p>
              <p className="text-lg font-bold text-purple-600 dark:text-purple-400">{ml_roi_3yr.toFixed(1)}%</p>
            </div>
            <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border-2 border-purple-300 dark:border-purple-700">
              <p className="text-xs text-muted-foreground mb-1">5-Year ROI</p>
              <p className="text-xl font-bold text-purple-600 dark:text-purple-400">{ml_roi_5yr.toFixed(1)}%</p>
            </div>
          </div>
          
          {/* Model Confidence & Transparency */}
          <div className="space-y-3">
            <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-amber-900 dark:text-amber-100 mb-1">Model Confidence & Limitations</p>
                  <ul className="text-xs text-amber-900 dark:text-amber-100 space-y-1">
                    <li>• <strong>Ranking Accuracy: 99.85%</strong> - Excellent at comparing areas</li>
                    <li>• <strong>R² Score: 0.14</strong> - Low precision for exact ROI values</li>
                    <li>• <strong>Spearman Correlation: 0.9985</strong> - Near-perfect ranking order</li>
                  </ul>
                </div>
              </div>
            </div>
            
            <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-start gap-2">
                <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">How to Use These Predictions</p>
                  <ul className="text-xs text-blue-900 dark:text-blue-100 space-y-1">
                    <li>✓ Use for <strong>shortlisting</strong> high-potential areas</li>
                    <li>✓ Compare <strong>relative performance</strong> between locations</li>
                    <li>✓ Identify <strong>top quartile</strong> investment opportunities (98% accuracy)</li>
                    <li>✗ Don't rely on exact percentage values</li>
                    <li>✗ Always conduct thorough due diligence on specific properties</li>
                  </ul>
                </div>
              </div>
            </div>
            
            <div className="p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-green-900 dark:text-green-100 mb-1">Model Strengths</p>
                  <ul className="text-xs text-green-900 dark:text-green-100 space-y-1">
                    <li>• Trained on 1,776 UK districts with real historical data</li>
                    <li>• Top 10% areas average 161% ROI vs 16% for bottom 10%</li>
                    <li>• Long-short strategy achieves 89% spread over 5 years</li>
                    <li>• Excellent for portfolio construction and risk management</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Disclaimer */}
      <Card className="p-4 bg-muted/30">
        <p className="text-xs text-muted-foreground">
          <strong>Disclaimer:</strong> This analysis is for informational purposes only and should not be considered financial advice. 
          Property investment involves risk. Past performance does not guarantee future results. Always consult with a qualified 
          financial advisor and conduct thorough due diligence before making investment decisions.
        </p>
      </Card>
    </div>
  );
}
