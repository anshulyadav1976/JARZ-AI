"use client";

import React, { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GrowthChart } from "./GrowthChart";
import { RentDemandCard } from "./RentDemandCard";
import { SaleDemandCard } from "./SaleDemandCard";
import { ValuationsCard } from "./ValuationsCard";
import { SaleHistoryTable } from "./SaleHistoryTable";
import type { GrowthData, RentDemandItem, SaleDemandItem, ValuationRecord, HistoricalValuationRecord, SaleHistoryRecord } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MarketDataPanelProps {
  defaultDistrict?: string;
  defaultPostcode?: string;
  /** When set (e.g. by agent), panel will switch to these values and trigger load, then call this. */
  triggerDistrict?: string | null;
  triggerPostcode?: string | null;
  onTriggerConsumed?: () => void;
}

export function MarketDataPanel({
  defaultDistrict = "",
  defaultPostcode = "",
  triggerDistrict,
  triggerPostcode,
  onTriggerConsumed,
}: MarketDataPanelProps) {
  const [district, setDistrict] = useState(defaultDistrict);
  const [postcode, setPostcode] = useState(defaultPostcode);
  const [loadingDistrict, setLoadingDistrict] = useState(false);
  const [loadingPostcode, setLoadingPostcode] = useState(false);
  const triggerConsumedRef = React.useRef(false);
  const [growthData, setGrowthData] = useState<GrowthData | null>(null);
  const [rentDemand, setRentDemand] = useState<RentDemandItem[] | null>(null);
  const [saleDemand, setSaleDemand] = useState<SaleDemandItem[] | null>(null);
  const [rentMeta, setRentMeta] = useState<{ target_month?: string; target_year?: number }>({});
  const [saleMeta, setSaleMeta] = useState<{ target_month?: string; target_year?: number }>({});
  const [currentValuations, setCurrentValuations] = useState<ValuationRecord[] | null>(null);
  const [historicalValuations, setHistoricalValuations] = useState<HistoricalValuationRecord[] | null>(null);
  const [saleHistory, setSaleHistory] = useState<SaleHistoryRecord[] | null>(null);

  const loadDistrict = useCallback(async (override?: string | null) => {
    const d = (override ?? district).trim().toUpperCase().split(/\s+/)[0];
    if (!d) return;
    if (override != null) setDistrict(override.trim());
    setLoadingDistrict(true);
    try {
      const [growthRes, rentRes, saleRes] = await Promise.all([
        fetch(`${API_URL}/api/district/${encodeURIComponent(d)}/growth`),
        fetch(`${API_URL}/api/district/${encodeURIComponent(d)}/rent/demand?additional_data=false`),
        fetch(`${API_URL}/api/district/${encodeURIComponent(d)}/sale/demand?additional_data=false`),
      ]);
      const growthJson = await growthRes.json();
      const rentJson = await rentRes.json();
      const saleJson = await saleRes.json();
      setGrowthData(growthJson.data || null);
      setRentDemand(rentJson.data?.rental_demand ?? null);
      setSaleDemand(saleJson.data?.sale_demand ?? null);
      setRentMeta({ target_month: rentJson.target_month, target_year: rentJson.target_year });
      setSaleMeta({ target_month: saleJson.target_month, target_year: saleJson.target_year });
    } catch (e) {
      console.error("District data fetch failed", e);
      setGrowthData(null);
      setRentDemand(null);
      setSaleDemand(null);
    } finally {
      setLoadingDistrict(false);
    }
  }, [district]);

  const loadPostcode = useCallback(async (override?: string | null) => {
    const raw = (override ?? postcode).trim().replace(/\s/g, "").toUpperCase();
    if (!raw) return;
    if (override != null) setPostcode(raw);
    setLoadingPostcode(true);
    try {
      const [currentRes, historicalRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/api/postcode/${encodeURIComponent(raw)}/valuations/current`),
        fetch(`${API_URL}/api/postcode/${encodeURIComponent(raw)}/valuations/historical`),
        fetch(`${API_URL}/api/postcode/${encodeURIComponent(raw)}/sale/history`),
      ]);
      const currentJson = await currentRes.json();
      const historicalJson = await historicalRes.json();
      const historyJson = await historyRes.json();
      setCurrentValuations(currentJson.data || null);
      setHistoricalValuations(historicalJson.data || null);
      setSaleHistory(historyJson.data || null);
    } catch (e) {
      console.error("Postcode data fetch failed", e);
      setCurrentValuations(null);
      setHistoricalValuations(null);
      setSaleHistory(null);
    } finally {
      setLoadingPostcode(false);
    }
  }, [postcode]);

  // When agent triggers market data load, set inputs and run load
  React.useEffect(() => {
    const hasTrigger = (triggerDistrict != null && triggerDistrict !== "") || (triggerPostcode != null && triggerPostcode !== "");
    if (!hasTrigger) {
      triggerConsumedRef.current = false;
      return;
    }
    if (triggerConsumedRef.current) return;
    triggerConsumedRef.current = true;
    if (triggerDistrict != null && triggerDistrict !== "") {
      setDistrict(triggerDistrict);
      loadDistrict(triggerDistrict);
    }
    if (triggerPostcode != null && triggerPostcode !== "") {
      const p = triggerPostcode.replace(/\s/g, "").toUpperCase();
      setPostcode(p);
      loadPostcode(p);
    }
    onTriggerConsumed?.();
  }, [triggerDistrict, triggerPostcode, onTriggerConsumed, loadDistrict, loadPostcode]);

  const displayDistrict = district.trim().toUpperCase().split(/\s+/)[0] || district;
  const displayPostcode = postcode.trim().replace(/\s/g, "").toUpperCase() || postcode;

  return (
    <div className="space-y-8">
      <div className="grid gap-6 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="market-district">District (e.g. NW1)</Label>
          <div className="flex gap-2">
            <Input
              id="market-district"
              placeholder="NW1"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadDistrict()}
            />
            <Button onClick={loadDistrict} disabled={loadingDistrict}>
              {loadingDistrict ? "Loading…" : "Load"}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">Growth, rent demand, sale demand</p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="market-postcode">Postcode (e.g. NW1 0BH)</Label>
          <div className="flex gap-2">
            <Input
              id="market-postcode"
              placeholder="NW1 0BH"
              value={postcode}
              onChange={(e) => setPostcode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadPostcode()}
            />
            <Button onClick={loadPostcode} disabled={loadingPostcode}>
              {loadingPostcode ? "Loading…" : "Load"}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">Valuations, sale history + export</p>
        </div>
      </div>

      {(growthData || rentDemand || saleDemand) && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-foreground">District: {displayDistrict}</h3>
          {growthData && (
            <GrowthChart
              district={displayDistrict}
              monthlyData={growthData.monthly_data}
              yearlyData={growthData.yearly_data}
            />
          )}
          {rentDemand != null && (
            <RentDemandCard
              district={displayDistrict}
              demand={rentDemand}
              targetMonth={rentMeta.target_month}
              targetYear={rentMeta.target_year}
            />
          )}
          {saleDemand != null && (
            <SaleDemandCard
              district={displayDistrict}
              demand={saleDemand}
              targetMonth={saleMeta.target_month}
              targetYear={saleMeta.target_year}
            />
          )}
        </div>
      )}

      {(currentValuations != null || historicalValuations != null || saleHistory != null) && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-foreground">Postcode: {displayPostcode}</h3>
          {(currentValuations != null || historicalValuations != null) && (
            <ValuationsCard
              postcode={displayPostcode}
              current={currentValuations ?? undefined}
              historical={historicalValuations ?? undefined}
            />
          )}
          {saleHistory != null && (
            <SaleHistoryTable
              postcode={displayPostcode}
              data={saleHistory}
              exportUrl={API_URL}
            />
          )}
        </div>
      )}

      {!growthData && !rentDemand && !saleDemand && !currentValuations && !historicalValuations && !saleHistory && (
        <p className="text-muted-foreground text-sm">Enter a district and/or postcode and click Load to fetch market data.</p>
      )}
    </div>
  );
}
