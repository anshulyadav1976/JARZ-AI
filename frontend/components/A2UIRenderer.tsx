"use client";

import React from "react";
import type { A2UIComponent, StreamState } from "@/lib/types";
import { resolveBoundValue } from "@/hooks/useAgentStream";
import { SummaryCard } from "./SummaryCard";
import { RentForecastChart } from "./RentForecastChart";
import { NeighbourHeatmapMap } from "./NeighbourHeatmapMap";
import { DriversBar } from "./DriversBar";
import { WhatIfControls } from "./WhatIfControls";
import { CarbonCard } from "./CarbonCard";
import { InvestmentCalculator } from "./InvestmentCalculator";
import { LocationComparisonSummaryCard } from "./LocationComparisonSummaryCard";
import { LocationComparisonRanges } from "./LocationComparisonRanges";
import { LocationComparisonListings } from "./LocationComparisonListings";

interface A2UIRendererProps {
  state: StreamState;
  onWhatIfChange?: (params: {
    horizon?: number;
    kNeighbors?: number;
    compare?: boolean;
  }) => void;
}

// Component registry mapping A2UI component types to React components
const COMPONENT_REGISTRY: Record<
  string,
  React.ComponentType<{ props: Record<string, unknown>; dataModel: Record<string, unknown> }>
> = {
  SummaryCard: SummaryCardWrapper,
  RentForecastChart: RentForecastChartWrapper,
  NeighbourHeatmapMap: NeighbourHeatmapMapWrapper,
  DriversBar: DriversBarWrapper,
  WhatIfControls: WhatIfControlsWrapper,
  CarbonCard: CarbonCardWrapper,
  LocationComparisonSummaryCard: LocationComparisonSummaryCardWrapper,
  LocationComparisonRanges: LocationComparisonRangesWrapper,
  LocationComparisonListings: LocationComparisonListingsWrapper,
};

// Wrapper components to handle A2UI props

function SummaryCardWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const location = resolveBoundValue(props.location as Record<string, unknown>, dataModel) as string;
  const p50 = resolveBoundValue(props.p50 as Record<string, unknown>, dataModel) as number;
  const p10 = resolveBoundValue(props.p10 as Record<string, unknown>, dataModel) as number;
  const p90 = resolveBoundValue(props.p90 as Record<string, unknown>, dataModel) as number;
  const unit = resolveBoundValue(props.unit as Record<string, unknown>, dataModel) as string;
  const horizonMonths = resolveBoundValue(props.horizon_months as Record<string, unknown>, dataModel) as number;
  const takeaway = resolveBoundValue(props.takeaway as Record<string, unknown>, dataModel) as string;

  return (
    <SummaryCard
      location={location || "Unknown"}
      p50={p50 || 0}
      p10={p10 || 0}
      p90={p90 || 0}
      unit={unit || "GBP/month"}
      horizon_months={horizonMonths || 6}
      takeaway={takeaway}
    />
  );
}

function RentForecastChartWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const historicalPath = (props.historicalPath as Record<string, unknown>)?.path as string;
  const forecastPath = (props.forecastPath as Record<string, unknown>)?.path as string;
  const unit = resolveBoundValue(props.unit as Record<string, unknown>, dataModel) as string;

  // Resolve data from model
  const historical = historicalPath
    ? (resolveBoundValue({ path: historicalPath }, dataModel) as Array<Record<string, unknown>>) || []
    : [];
  const forecast = forecastPath
    ? (resolveBoundValue({ path: forecastPath }, dataModel) as Array<Record<string, unknown>>) || []
    : [];

  return (
    <RentForecastChart
      historical={historical.map((h) => ({
        date: h.date as string,
        rent: h.rent as number,
      }))}
      forecast={forecast.map((f) => ({
        date: f.date as string,
        p10: f.p10 as number,
        p50: f.p50 as number,
        p90: f.p90 as number,
      }))}
      unit={unit || "GBP/month"}
    />
  );
}

function NeighbourHeatmapMapWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const centerLat = resolveBoundValue(props.centerLat as Record<string, unknown>, dataModel) as number;
  const centerLon = resolveBoundValue(props.centerLon as Record<string, unknown>, dataModel) as number;
  const selectedAreaCode = resolveBoundValue(props.selectedAreaCode as Record<string, unknown>, dataModel) as string;
  const neighborsPath = (props.neighborsPath as Record<string, unknown>)?.path as string;

  const neighbors = neighborsPath
    ? (resolveBoundValue({ path: neighborsPath }, dataModel) as Array<Record<string, unknown>>) || []
    : [];

  return (
    <NeighbourHeatmapMap
      center={{
        area_code: selectedAreaCode || "",
        area_code_district: "",
        display_name: selectedAreaCode || "",
        lat: centerLat,
        lon: centerLon,
      }}
      neighbors={neighbors.map((n) => ({
        area_code: n.area_code as string,
        display_name: n.display_name as string,
        lat: n.lat as number,
        lon: n.lon as number,
        avg_rent: n.avg_rent as number,
        demand_index: n.demand_index as number,
      }))}
      selectedAreaCode={selectedAreaCode || ""}
    />
  );
}

function DriversBarWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const driversPath = (props.driversPath as Record<string, unknown>)?.path as string;
  const baseValue = resolveBoundValue(props.baseValue as Record<string, unknown>, dataModel) as number;

  const drivers = driversPath
    ? (resolveBoundValue({ path: driversPath }, dataModel) as Array<Record<string, unknown>>) || []
    : [];

  return (
    <DriversBar
      drivers={drivers.map((d) => ({
        name: d.name as string,
        contribution: d.contribution as number,
        direction: d.direction as "positive" | "negative",
      }))}
      base_value={baseValue}
    />
  );
}

function WhatIfControlsWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const currentHorizon = resolveBoundValue(props.currentHorizon as Record<string, unknown>, dataModel) as number;
  const currentKNeighbors = resolveBoundValue(props.currentKNeighbors as Record<string, unknown>, dataModel) as number;

  // For demo, these are static - in real app would connect to state
  return (
    <WhatIfControls
      currentHorizon={currentHorizon || 6}
      currentRadius={5}
      currentKNeighbors={currentKNeighbors || 5}
      onHorizonChange={() => {}}
      onRadiusChange={() => {}}
      onKNeighborsChange={() => {}}
      onCompareToggle={() => {}}
      compareMode={false}
    />
  );
}

function LocationComparisonSummaryCardWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const areasPath = (props.areasPath as Record<string, unknown>)?.path as string;
  const winnersPath = (props.winnersPath as Record<string, unknown>)?.path as string;

  const areas =
    areasPath ? (resolveBoundValue({ path: areasPath }, dataModel) as any[]) || [] : [];
  const winners =
    winnersPath ? (resolveBoundValue({ path: winnersPath }, dataModel) as Record<string, unknown>) || {} : {};

  return (
    <LocationComparisonSummaryCard
      areas={areas as any}
      winners={winners as any}
    />
  );
}

function LocationComparisonRangesWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const areasPath = (props.areasPath as Record<string, unknown>)?.path as string;
  const areas =
    areasPath ? (resolveBoundValue({ path: areasPath }, dataModel) as any[]) || [] : [];

  return <LocationComparisonRanges areas={areas as any} />;
}

function LocationComparisonListingsWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const areasPath = (props.areasPath as Record<string, unknown>)?.path as string;
  const areas =
    areasPath ? (resolveBoundValue({ path: areasPath }, dataModel) as any[]) || [] : [];

  return <LocationComparisonListings areas={areas as any} />;
}

function CarbonCardWrapper({
  props,
  dataModel,
}: {
  props: Record<string, unknown>;
  dataModel: Record<string, unknown>;
}) {
  const location = resolveBoundValue(props.location as Record<string, unknown>, dataModel) as string;
  const currentEmissions = resolveBoundValue(props.currentEmissions as Record<string, unknown>, dataModel) as number;
  const potentialEmissions = resolveBoundValue(props.potentialEmissions as Record<string, unknown>, dataModel) as number;
  const emissionsMetric = resolveBoundValue(props.emissionsMetric as Record<string, unknown>, dataModel) as string;
  const energyRating = resolveBoundValue(props.energyRating as Record<string, unknown>, dataModel) as string;
  const potentialRating = resolveBoundValue(props.potentialRating as Record<string, unknown>, dataModel) as string;
  const propertySize = resolveBoundValue(props.propertySize as Record<string, unknown>, dataModel) as number;
  const propertyType = resolveBoundValue(props.propertyType as Record<string, unknown>, dataModel) as string;
  const currentConsumption = resolveBoundValue(props.currentConsumption as Record<string, unknown>, dataModel) as number;
  const potentialConsumption = resolveBoundValue(props.potentialConsumption as Record<string, unknown>, dataModel) as number;
  const consumptionMetric = resolveBoundValue(props.consumptionMetric as Record<string, unknown>, dataModel) as string;
  const currentEnergyCost = resolveBoundValue(props.currentEnergyCost as Record<string, unknown>, dataModel) as number;
  const potentialEnergyCost = resolveBoundValue(props.potentialEnergyCost as Record<string, unknown>, dataModel) as number;
  const currency = resolveBoundValue(props.currency as Record<string, unknown>, dataModel) as string;
  const environmentalScore = resolveBoundValue(props.environmentalScore as Record<string, unknown>, dataModel) as number;
  const potentialEnvironmentalScore = resolveBoundValue(props.potentialEnvironmentalScore as Record<string, unknown>, dataModel) as number;
  const efficiencyFeatures = resolveBoundValue(props.efficiencyFeatures as Record<string, unknown>, dataModel) as string;
  const embodiedCarbonTotal = resolveBoundValue(props.embodiedCarbonTotal as Record<string, unknown>, dataModel) as number;
  const embodiedCarbonPerM2 = resolveBoundValue(props.embodiedCarbonPerM2 as Record<string, unknown>, dataModel) as number;
  const embodiedCarbonAnnual = resolveBoundValue(props.embodiedCarbonAnnual as Record<string, unknown>, dataModel) as number;
  const embodiedCarbonA1A3 = resolveBoundValue(props.embodiedCarbonA1A3 as Record<string, unknown>, dataModel) as number;
  const embodiedCarbonA4 = resolveBoundValue(props.embodiedCarbonA4 as Record<string, unknown>, dataModel) as number;
  const embodiedCarbonA5 = resolveBoundValue(props.embodiedCarbonA5 as Record<string, unknown>, dataModel) as number;

  return (
    <CarbonCard
      location={location || "Unknown"}
      currentEmissions={currentEmissions || 0}
      potentialEmissions={potentialEmissions || 0}
      emissionsMetric={emissionsMetric || "tonnes CO2/year"}
      energyRating={energyRating || "C"}
      potentialRating={potentialRating || "B"}
      propertySize={propertySize || 0}
      propertyType={propertyType || "flat"}
      currentConsumption={currentConsumption || 0}
      potentialConsumption={potentialConsumption || 0}
      consumptionMetric={consumptionMetric || "kWh/m2"}
      currentEnergyCost={currentEnergyCost || 0}
      potentialEnergyCost={potentialEnergyCost || 0}
      currency={currency || "£"}
      environmentalScore={environmentalScore || 0}
      potentialEnvironmentalScore={potentialEnvironmentalScore || 0}
      efficiencyFeatures={efficiencyFeatures || "Standard efficiency"}
      embodiedCarbonTotal={embodiedCarbonTotal || 0}
      embodiedCarbonPerM2={embodiedCarbonPerM2 || 0}
      embodiedCarbonAnnual={embodiedCarbonAnnual || 0}
      embodiedCarbonA1A3={embodiedCarbonA1A3 || 0}
      embodiedCarbonA4={embodiedCarbonA4 || 0}
      embodiedCarbonA5={embodiedCarbonA5 || 0}
    />
  );
}

// Recursive component renderer
function RenderComponent({
  componentId,
  components,
  dataModel,
}: {
  componentId: string;
  components: Map<string, A2UIComponent>;
  dataModel: Record<string, unknown>;
}) {
  const componentDef = components.get(componentId);
  if (!componentDef) {
    return null;
  }

  const componentData = componentDef.component;
  const componentType = Object.keys(componentData)[0];
  const componentProps = componentData[componentType] as Record<string, unknown>;

  // Handle layout components
  if (componentType === "Column") {
    const children = (componentProps.children as Record<string, unknown>)?.explicitList as string[] || [];
    return (
      <div className="flex flex-col gap-6 w-full">
        {children.map((childId) => (
          <RenderComponent
            key={childId}
            componentId={childId}
            components={components}
            dataModel={dataModel}
          />
        ))}
      </div>
    );
  }

  if (componentType === "Row") {
    const children = (componentProps.children as Record<string, unknown>)?.explicitList as string[] || [];
    return (
      <div className="flex flex-row gap-6 w-full flex-wrap">
        {children.map((childId) => (
          <RenderComponent
            key={childId}
            componentId={childId}
            components={components}
            dataModel={dataModel}
          />
        ))}
      </div>
    );
  }

  if (componentType === "Card") {
    const childId = componentProps.child as string;
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
        <RenderComponent
          componentId={childId}
          components={components}
          dataModel={dataModel}
        />
      </div>
    );
  }

  if (componentType === "Text") {
    const text = resolveBoundValue(componentProps.text as Record<string, unknown>, dataModel) as string;
    const usageHint = componentProps.usageHint as string;
    
    const className = usageHint === "h3" 
      ? "text-xl font-semibold" 
      : usageHint === "h2" 
      ? "text-2xl font-bold"
      : "text-base";
    
    return <span className={className}>{text}</span>;
  }

  // Check custom component registry
  const CustomComponent = COMPONENT_REGISTRY[componentType];
  if (CustomComponent) {
    return <CustomComponent props={componentProps} dataModel={dataModel} />;
  }

  // Unknown component
  console.warn(`Unknown component type: ${componentType}`);
  return (
    <div className="p-4 border border-dashed border-gray-300 rounded">
      <p className="text-sm text-gray-500">Unknown component: {componentType}</p>
    </div>
  );
}

export function A2UIRenderer({ state, onWhatIfChange }: A2UIRendererProps) {
  console.log("[A2UIRenderer] State:", {
    isReady: state.isReady,
    rootId: state.rootId,
    componentsCount: state.components.size,
    dataModelKeys: Object.keys(state.dataModel),
  });
  
  if (!state.isReady || !state.rootId) {
    console.log("[A2UIRenderer] Not ready or no rootId, returning null");
    return null;
  }

  // console.log("[A2UIRenderer] Rendering component:", state.rootId);
  
  return (
    <div className="w-full">
      <RenderComponent
        componentId={state.rootId}
        components={state.components}
        dataModel={state.dataModel}
      />
    </div>
  );
}
