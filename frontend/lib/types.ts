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

// Stream state
export interface StreamState {
  components: Map<string, A2UIComponent>;
  dataModel: Record<string, unknown>;
  rootId: string | null;
  isReady: boolean;
  isLoading: boolean;
  error: string | null;
}
