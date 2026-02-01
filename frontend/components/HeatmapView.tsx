"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MapPin, Loader2, Home } from "lucide-react";

// Mapbox GL types
declare global {
  interface Window {
    mapboxgl: any;
  }
}

interface HeatmapDataPoint {
  area_code: string;
  lat: number;
  lng: number;
  price?: number;
  min_price?: number;
  max_price?: number;
  median_price?: number;
  listing_count?: number;
  crime_count?: number;
  crime_rate?: number;
}

interface HeatmapViewProps {
  listingType?: "rent" | "sale";
}

export function HeatmapView({ listingType = "rent" }: HeatmapViewProps) {
  const [data, setData] = useState<HeatmapDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"rent" | "sale" | "crime">(listingType);
  const [selectedArea, setSelectedArea] = useState<HeatmapDataPoint | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

  console.log("[HeatmapView] Component mounted, viewMode:", viewMode);
  console.log("[HeatmapView] Mapbox token present:", MAPBOX_TOKEN ? "Yes" : "No");

  // Fetch heatmap data
  const fetchHeatmapData = useCallback(async () => {
    setLoading(true);
    console.log("[HeatmapView] Fetching heatmap data, viewMode:", viewMode);
    console.log("[HeatmapView] API URL:", API_URL);
    try {
      const url = viewMode === "crime" 
        ? `${API_URL}/api/heatmap/crime`
        : `${API_URL}/api/heatmap/areas?listing_type=${viewMode}`;
      
      const response = await fetch(url);
      console.log("[HeatmapView] Response status:", response.status);
      const result = await response.json();
      console.log("[HeatmapView] Result:", result);
      
      if (result.success && result.data) {
        console.log("[HeatmapView] Loaded data points:", result.data.length);
        setData(result.data);
      } else {
        console.error("[HeatmapView] No data in response");
      }
    } catch (error) {
      console.error("[HeatmapView] Error fetching heatmap data:", error);
    } finally {
      setLoading(false);
    }
  }, [API_URL, viewMode]);

  useEffect(() => {
    fetchHeatmapData();
  }, [fetchHeatmapData]);

  // Initialize Mapbox
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Check if mapbox is already loaded
    if (window.mapboxgl) {
      initializeMap();
      return;
    }

    // Load Mapbox GL CSS
    const link = document.createElement("link");
    link.href = "https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css";
    link.rel = "stylesheet";
    document.head.appendChild(link);

    // Load Mapbox GL JS
    const script = document.createElement("script");
    script.src = "https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js";
    script.async = true;
    script.onload = initializeMap;
    script.onerror = () => {
      console.error("[HeatmapView] Failed to load Mapbox GL JS");
      setLoading(false);
    };
    document.head.appendChild(script);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  const initializeMap = () => {
    if (!window.mapboxgl || !mapContainerRef.current || mapRef.current) return;

    try {
      window.mapboxgl.accessToken = MAPBOX_TOKEN;
      
      const map = new window.mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/streets-v12",
        center: [-0.1278, 51.5074], // London center
        zoom: 10,
      });

      map.addControl(new window.mapboxgl.NavigationControl(), "top-right");
      
      map.on('load', () => {
        console.log("[HeatmapView] Map loaded successfully");
      });

      mapRef.current = map;
      console.log("[HeatmapView] Mapbox initialized");
    } catch (error) {
      console.error("[HeatmapView] Error initializing map:", error);
      setLoading(false);
    }
  };

  // Add heatmap layer when data changes
  useEffect(() => {
    if (!mapRef.current || data.length === 0) return;

    const map = mapRef.current;

    // Wait for map to be loaded
    if (!map.isStyleLoaded()) {
      map.on('load', () => addHeatmapLayer());
      return;
    }

    addHeatmapLayer();

    function addHeatmapLayer() {
      // Remove existing layers and sources
      if (map.getLayer('heatmap-layer')) {
        map.removeLayer('heatmap-layer');
      }
      if (map.getLayer('heatmap-points')) {
        map.removeLayer('heatmap-points');
      }
      if (map.getSource('heatmap-data')) {
        map.removeSource('heatmap-data');
      }

      // Convert data to GeoJSON
      const geojsonData = {
        type: 'FeatureCollection',
        features: data.map((point) => ({
          type: 'Feature',
          properties: {
            value: viewMode === "crime" ? point.crime_count : point.price,
            price: point.price,
            area_code: point.area_code,
            median_price: point.median_price,
            min_price: point.min_price,
            max_price: point.max_price,
            listing_count: point.listing_count,
            crime_count: point.crime_count,
            crime_rate: point.crime_rate,
          },
          geometry: {
            type: 'Point',
            coordinates: [point.lng, point.lat],
          },
        })),
      };

      // Add source
      map.addSource('heatmap-data', {
        type: 'geojson',
        data: geojsonData,
      });

      // Calculate min/max for weight
      const values = viewMode === "crime" 
        ? data.map(d => d.crime_count || 0)
        : data.map(d => d.price || 0);
      const minValue = Math.min(...values);
      const maxValue = Math.max(...values);

      // Add heatmap layer
      map.addLayer({
        id: 'heatmap-layer',
        type: 'heatmap',
        source: 'heatmap-data',
        maxzoom: 15,
        paint: {
          // Increase weight based on value
          'heatmap-weight': [
            'interpolate',
            ['linear'],
            ['get', 'value'],
            minValue,
            0.5,
            maxValue,
            1.5,
          ],
          // Intensity - keep it lower for smoother gradients
          'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 0.8, 9, 1.5],
          // Color ramp matching the original blue→cyan→yellow→orange→red
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0,
            'rgba(0, 0, 255, 0)',
            0.1,
            'rgba(0, 100, 255, 0.7)',
            0.3,
            'rgba(0, 200, 200, 0.75)',
            0.5,
            'rgba(255, 230, 0, 0.8)',
            0.7,
            'rgba(255, 120, 0, 0.85)',
            0.9,
            'rgba(255, 50, 0, 0.9)',
          ],
          // Larger radius for smoother blob-like appearance
          'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 25, 9, 50, 15, 70],
          // Keep heatmap visible, don't transition to circles
          'heatmap-opacity': 0.85,
        },
      });

      // Add invisible click targets for interactivity
      map.addLayer({
        id: 'heatmap-points',
        type: 'circle',
        source: 'heatmap-data',
        paint: {
          'circle-radius': 15,
          'circle-color': '#000000',
          'circle-opacity': 0,
          'circle-stroke-width': 0,
        },
      });

      // Add click handler for points
      map.on('click', 'heatmap-points', (e: any) => {
        if (e.features && e.features[0]) {
          const props = e.features[0].properties;
          setSelectedArea({
            area_code: props.area_code,
            lat: e.lngLat.lat,
            lng: e.lngLat.lng,
            price: props.price,
            median_price: props.median_price,
            min_price: props.min_price,
            max_price: props.max_price,
            listing_count: props.listing_count,
            crime_count: props.crime_count,
            crime_rate: props.crime_rate,
          });

          // Show popup with mode-specific content
          const popupContent = viewMode === "crime" 
            ? `
              <div style="padding: 12px; min-width: 200px;">
                <h3 style="margin: 0 0 12px 0; font-weight: bold; font-size: 16px; color: #1a1a1a;">${props.area_code}</h3>
                <div style="border-top: 2px solid #e0e0e0; padding-top: 8px;">
                  ${props.crime_count ? `<p style="margin: 6px 0; font-size: 14px;"><strong>Total Incidents:</strong> <span style="color: #dc2626;">${props.crime_count.toLocaleString()}</span></p>` : ""}
                </div>
              </div>
            `
            : `
              <div style="padding: 12px; min-width: 200px;">
                <h3 style="margin: 0 0 12px 0; font-weight: bold; font-size: 16px; color: #1a1a1a;">${props.area_code}</h3>
                <div style="border-top: 2px solid #e0e0e0; padding-top: 8px;">
                  ${props.median_price ? `<p style="margin: 6px 0; font-size: 14px;"><strong>Median:</strong> <span style="color: #2563eb;">£${Math.round(props.median_price).toLocaleString()}</span>${viewMode === "rent" ? "/month" : ""}</p>` : ""}
                  ${props.min_price ? `<p style="margin: 6px 0; font-size: 13px; color: #666;"><strong>Min:</strong> £${Math.round(props.min_price).toLocaleString()}${viewMode === "rent" ? "/mo" : ""}</p>` : ""}
                  ${props.max_price ? `<p style="margin: 6px 0; font-size: 13px; color: #666;"><strong>Max:</strong> £${Math.round(props.max_price).toLocaleString()}${viewMode === "rent" ? "/mo" : ""}</p>` : ""}
                  ${props.listing_count ? `<p style="margin: 6px 0; font-size: 13px; color: #666;"><strong>Listings:</strong> ${props.listing_count}</p>` : ""}
                </div>
              </div>
            `;

          // Show popup
          new window.mapboxgl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(popupContent)
            .addTo(map);
        }
      });

      // Change cursor on hover
      map.on('mouseenter', 'heatmap-points', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'heatmap-points', () => {
        map.getCanvas().style.cursor = '';
      });

      console.log("[HeatmapView] Added heatmap layer with", data.length, "points");
    }
  }, [data, viewMode]);

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-background via-muted/10 to-muted/20">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b bg-card/50 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              London {viewMode === "crime" ? "Crime" : "Price"} Heatmap
            </h2>
            <p className="text-xs text-muted-foreground">
              {viewMode === "crime" ? "Crime incidents across London" : "Property prices across London"}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (mapRef.current) {
                mapRef.current.flyTo({ center: [-0.1278, 51.5074], zoom: 10 });
              }
            }}
          >
            <Home className="h-4 w-4 mr-2" />
            Reset View
          </Button>
        </div>

        {/* View Mode Tabs */}
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as "rent" | "sale" | "crime")}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="rent">Rent</TabsTrigger>
            <TabsTrigger value="sale">Sale</TabsTrigger>
            <TabsTrigger value="crime">Crime</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Map Container */}
      <div className="flex-1 relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Loading heatmap data...</p>
            </div>
          </div>
        )}
        
        <div 
          ref={mapContainerRef} 
          className="absolute inset-0"
          style={{ minHeight: '400px' }}
        />

        {/* Selected Area Info */}
        {selectedArea && (
          <Card className="absolute bottom-4 left-4 right-4 p-4 bg-card/95 backdrop-blur z-10">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-lg">{selectedArea.area_code}</h3>
                <div className="mt-3 space-y-2 text-sm">
                  {viewMode === "crime" ? (
                    <>
                      {selectedArea.crime_count && (
                        <div className="pb-2 border-b">
                          <p className="text-xs text-muted-foreground">Total Incidents</p>
                          <p className="text-xl font-bold text-destructive">
                            {selectedArea.crime_count.toLocaleString()}
                          </p>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {selectedArea.median_price && (
                        <div className="pb-2 border-b">
                          <p className="text-xs text-muted-foreground">Median Price</p>
                          <p className="text-xl font-bold text-primary">
                            £{Math.round(selectedArea.median_price).toLocaleString()}
                            {viewMode === "rent" && <span className="text-sm font-normal">/month</span>}
                          </p>
                        </div>
                      )}
                      <div className="grid grid-cols-2 gap-2">
                        {selectedArea.min_price && (
                          <div>
                            <p className="text-xs text-muted-foreground">Min</p>
                            <p className="font-semibold">£{Math.round(selectedArea.min_price).toLocaleString()}</p>
                          </div>
                        )}
                        {selectedArea.max_price && (
                          <div>
                            <p className="text-xs text-muted-foreground">Max</p>
                            <p className="font-semibold">£{Math.round(selectedArea.max_price).toLocaleString()}</p>
                          </div>
                        )}
                      </div>
                      {selectedArea.listing_count && (
                        <p className="text-xs text-muted-foreground pt-1">
                          {selectedArea.listing_count} active listings
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedArea(null)}
              >
                ✕
              </Button>
            </div>
          </Card>
        )}

        {/* Legend */}
        {data.length > 0 && !loading && (() => {
          if (viewMode === "crime") {
            const crimes = data.map((d) => d.crime_count || 0);
            const minCrime = Math.min(...crimes);
            const maxCrime = Math.max(...crimes);
            
            return (
              <div className="absolute top-4 right-4 bg-card/95 backdrop-blur p-3 rounded-lg border text-xs z-10 shadow-lg">
                <p className="font-semibold mb-2">Crime Count</p>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(0, 100, 255)" }}></div>
                    <span>{Math.round(minCrime).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(0, 220, 150)" }}></div>
                    <span>Lower</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(255, 230, 0)" }}></div>
                    <span>Medium</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(255, 120, 0)" }}></div>
                    <span>Higher</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(255, 50, 0)" }}></div>
                    <span>{Math.round(maxCrime).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            );
          } else {
            const prices = data.map((d) => d.price || 0);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            
            return (
              <div className="absolute top-4 right-4 bg-card/95 backdrop-blur p-3 rounded-lg border text-xs z-10 shadow-lg">
                <p className="font-semibold mb-2">Price Range ({viewMode === "rent" ? "/month" : ""})</p>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(0, 100, 255)" }}></div>
                    <span>£{Math.round(minPrice).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(0, 220, 150)" }}></div>
                    <span>Lower</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(255, 230, 0)" }}></div>
                    <span>Medium</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(255, 120, 0)" }}></div>
                    <span>Higher</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: "rgb(255, 50, 0)" }}></div>
                    <span>£{Math.round(maxPrice).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            );
          }
        })()}
      </div>
    </div>
  );
}