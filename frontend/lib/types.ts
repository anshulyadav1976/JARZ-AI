/**
 * Shared TypeScript types for the frontend
 */

// User query sent to backend
export interface UserQuery {
  location_input: string;
  area_code?: string;
  horizon_months: number;
  view_mode: "single" | "compare";
  radius_km?: number;
  k_neighbors?: number;
}

// Prediction result from model
export interface PredictionResult {
  p10: number;
  p50: number;
  p90: number;
  unit: string;
  horizon_months: number;
  metadata?: Record<string, unknown>;
}

// Single driver in explanation
export interface Driver {
  name: string;
  contribution: number;
  direction: "positive" | "negative";
}

// Explanation result from SHAP/heuristic
export interface ExplanationResult {
  drivers: Driver[];
  base_value?: number;
}

// Location data
export interface ResolvedLocation {
  area_code: string;
  area_code_district: string;
  display_name: string;
  lat?: number;
  lon?: number;
}

// Neighbor data for map
export interface Neighbor {
  area_code: string;
  display_name: string;
  lat: number;
  lon: number;
  avg_rent?: number;
  demand_index?: number;
}

// Historical data point for charts
export interface HistoricalDataPoint {
  date: string;
  rent: number;
  p10?: number;
  p90?: number;
}

// Forecast data point
export interface ForecastDataPoint {
  date: string;
  p10: number;
  p50: number;
  p90: number;
}

// A2UI Message types
export interface A2UIComponent {
  id: string;
  component: Record<string, unknown>;
}

export interface SurfaceUpdate {
  surfaceId?: string;
  components: A2UIComponent[];
}

export interface DataModelUpdate {
  surfaceId?: string;
  path?: string;
  contents: Array<{
    key: string;
    valueString?: string;
    valueNumber?: number;
    valueBoolean?: boolean;
    valueMap?: unknown[];
    valueArray?: unknown[];
  }>;
}

export interface BeginRendering {
  surfaceId?: string;
  root: string;
  catalogId?: string;
}

export type A2UIMessage =
  | { surfaceUpdate: SurfaceUpdate }
  | { dataModelUpdate: DataModelUpdate }
  | { beginRendering: BeginRendering };

// Component props types for A2UI rendering
export interface SummaryCardProps {
  location: string;
  p50: number;
  p10: number;
  p90: number;
  unit: string;
  horizon_months: number;
  takeaway?: string;
}

export interface RentForecastChartProps {
  historical: HistoricalDataPoint[];
  forecast: ForecastDataPoint[];
  unit: string;
}

export interface NeighbourHeatmapMapProps {
  center: ResolvedLocation;
  neighbors: Neighbor[];
  selectedAreaCode: string;
}

export interface DriversBarProps {
  drivers: Driver[];
  base_value?: number;
}

export interface WhatIfControlsProps {
  currentHorizon: number;
  currentRadius: number;
  currentKNeighbors: number;
  onHorizonChange: (value: number) => void;
  onRadiusChange: (value: number) => void;
  onKNeighborsChange: (value: number) => void;
  onCompareToggle: () => void;
  compareMode: boolean;
}

// ============================================================================
// Location Comparison (Area Summary)
// ============================================================================

export interface AreaSummaryComparisonRow {
  area_code: string;
  display_name: string;
  total_properties?: number | null;
  total_properties_sold_in_last_5yrs?: number | null;
  sold_price_min?: number | null;
  sold_price_max?: number | null;
  valuation_min?: number | null;
  valuation_max?: number | null;
  rent_listings?: number | null;
  rent_pcm_min?: number | null;
  rent_pcm_max?: number | null;
  sale_listings?: number | null;
  sale_price_min?: number | null;
  sale_price_max?: number | null;
  rent_pcm_mid?: number | null;
  sale_price_mid?: number | null;
  sold_price_mid?: number | null;
  valuation_mid?: number | null;
}

export interface LocationComparisonWinners {
  cheapest_rent_mid?: string | null;
  most_rent_listings?: string | null;
  cheapest_sale_mid?: string | null;
  most_sale_listings?: string | null;
  most_total_properties?: string | null;
}

export interface LocationComparisonSummaryCardProps {
  areas: AreaSummaryComparisonRow[];
  winners: LocationComparisonWinners;
}

export interface LocationComparisonRangesProps {
  areas: AreaSummaryComparisonRow[];
}

export interface LocationComparisonListingsProps {
  areas: AreaSummaryComparisonRow[];
}

// Stream state
export interface StreamState {
  components: Map<string, A2UIComponent>;
  dataModel: Record<string, unknown>;
  rootId: string | null;
  isReady: boolean;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Market Data (Growth, Demand, Valuations, Sale History)
// ============================================================================

export interface GrowthDataPoint {
  area_code_district?: string;
  year_month: string;
  avg_price: number;
  percentage_change: number;
}

export interface GrowthData {
  monthly_data?: GrowthDataPoint[];
  yearly_data?: GrowthDataPoint[];
}

export interface RentDemandItem {
  total_properties_for_rent?: number;
  mean_rent_pcm?: number;
  median_rent_pcm?: number;
  currency?: string;
  average_transactions_pcm?: number;
  months_of_inventory?: number;
  turnover_percentage_pcm?: number;
  days_on_market?: number;
  market_rating?: string;
}

export interface SaleDemandItem {
  total_properties_for_sale?: number;
  mean_price?: number;
  median_price?: number;
  currency?: string;
  average_transactions_pcm?: number;
  months_of_inventory?: number;
  days_on_market?: number;
  market_rating?: string;
}

export interface ValuationRecord {
  property_address: string;
  last_sold_price?: number | null;
  last_sold_date?: string | null;
  bounded_valuation?: [number, number];
  lower_outlier?: boolean;
  upper_outlier?: boolean;
}

export interface HistoricalValuationPoint {
  date: string;
  valuation: number;
}

export interface HistoricalValuationRecord {
  property_address: string;
  valuations: HistoricalValuationPoint[];
}

export interface SaleHistoryTransaction {
  sold_date?: string;
  sold_price?: number;
  property_tenure?: string;
  price_diff_amount?: number | null;
  price_diff_percentage?: number | null;
}

export interface SaleHistoryRecord {
  property_address: string;
  uprn?: number | null;
  property_type?: string;
  transactions: SaleHistoryTransaction[];
}
