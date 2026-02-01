"use client";

import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { Card } from "./ui/card";
import { X, ExternalLink, Bed, Bath, Maximize } from "lucide-react";

// Set your Mapbox access token
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw';

interface Property {
  id: string;
  title: string;
  price: number;
  type: "sale" | "rent";
  location: string;
  beds: number;
  baths: number;
  sqft: number;
  url: string;
  imageUrl?: string;
  lat?: number;
  lng?: number;
  amenities?: Array<{
    type: string;
    name: string;
    distance: number;
  }>;
}

interface PropertyMapViewClientProps {
  properties?: Property[];
  center?: [number, number];
}

export function PropertyMapViewClient({ properties = [], center }: PropertyMapViewClientProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  console.log('[PropertyMapViewClient] Render - properties count:', properties.length);
  console.log('[PropertyMapViewClient] Mapbox token:', mapboxgl.accessToken);
  console.log('[PropertyMapViewClient] Token valid:', !!mapboxgl.accessToken && mapboxgl.accessToken.startsWith('pk.'));
  console.log('[PropertyMapViewClient] Center:', center);

  // Initialize map
  useEffect(() => {
    console.log('[PropertyMapViewClient] Init effect - mapContainer:', !!mapContainer.current, 'map exists:', !!map.current);
    
    if (!mapContainer.current || map.current) {
      console.log('[PropertyMapViewClient] Skipping init - container or map already exists');
      return;
    }

    if (!mapboxgl.accessToken || !mapboxgl.accessToken.startsWith('pk.')) {
      console.error('[PropertyMapViewClient] Invalid or missing Mapbox token!');
      console.error('[PropertyMapViewClient] Token value:', mapboxgl.accessToken);
      console.error('[PropertyMapViewClient] NEXT_PUBLIC_MAPBOX_TOKEN:', process.env.NEXT_PUBLIC_MAPBOX_TOKEN);
      return;
    }

    try {
      // Default to London if no center provided
      const defaultCenter: [number, number] = center || [-0.1276, 51.5074];
      console.log('[PropertyMapViewClient] Creating map with center:', defaultCenter);

      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: defaultCenter,
        zoom: 12,
        pitch: 45,
        bearing: 0,
        attributionControl: true
      });

      console.log('[PropertyMapViewClient] Map instance created');

      // Add navigation controls
      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

      // Add fullscreen control
      map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

      // Add scale control
      map.current.addControl(new mapboxgl.ScaleControl(), 'bottom-left');

      console.log('[PropertyMapViewClient] Controls added');

      map.current.on('load', () => {
        console.log('[PropertyMapViewClient] Map loaded successfully!');
        setMapLoaded(true);
      });

      map.current.on('error', (e) => {
        console.error('[PropertyMapViewClient] Map error:', e);
        console.error('[PropertyMapViewClient] Error details:', e.error);
      });

      map.current.on('style.load', () => {
        console.log('[PropertyMapViewClient] Map style loaded');
      });

      map.current.on('render', () => {
        console.log('[PropertyMapViewClient] Map rendering...');
      });
    } catch (error) {
      console.error('[PropertyMapViewClient] Error initializing map:', error);
      console.error('[PropertyMapViewClient] Error stack:', error instanceof Error ? error.stack : 'No stack trace');
    }

    return () => {
      console.log('[PropertyMapViewClient] Cleanup - removing map');
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [center]);

  // Update markers when properties change
  useEffect(() => {
    console.log('[PropertyMapViewClient] Markers effect - map:', !!map.current, 'mapLoaded:', mapLoaded, 'properties:', properties.length);
    console.log('[PropertyMapViewClient] Properties array:', properties);
    console.log('[PropertyMapViewClient] First property:', properties[0]);
    
    if (!map.current || !mapLoaded) {
      console.log('[PropertyMapViewClient] Skipping markers - map not ready');
      return;
    }

    // Clear existing markers
    console.log('[PropertyMapViewClient] Clearing', markers.current.length, 'existing markers');
    markers.current.forEach(marker => marker.remove());
    markers.current = [];

    if (properties.length === 0) {
      console.log('[PropertyMapViewClient] No properties to display');
      return;
    }

    console.log('[PropertyMapViewClient] Adding markers for', properties.length, 'properties');

    // Create GeoJSON for clustering
    const geojsonData: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: properties.map((property, index) => {
        const lat = property.lat ?? (51.5074 + (Math.random() - 0.5) * 0.1);
        const lng = property.lng ?? (-0.1276 + (Math.random() - 0.5) * 0.1);
        
        return {
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [lng, lat]
          },
          properties: {
            id: property.id,
            title: property.title,
            price: property.price,
            type: property.type,
            beds: property.beds,
            baths: property.baths,
            sqft: property.sqft,
            location: property.location,
            url: property.url,
            imageUrl: property.imageUrl,
            index: index
          }
        };
      })
    };

    // Remove existing sources and layers
    if (map.current.getSource('properties')) {
      if (map.current.getLayer('clusters')) map.current.removeLayer('clusters');
      if (map.current.getLayer('cluster-count')) map.current.removeLayer('cluster-count');
      if (map.current.getLayer('unclustered-point')) map.current.removeLayer('unclustered-point');
      map.current.removeSource('properties');
    }

    // Add source with clustering
    map.current.addSource('properties', {
      type: 'geojson',
      data: geojsonData,
      cluster: true,
      clusterMaxZoom: 16,
      clusterRadius: 50
    });

    // Add cluster circles
    map.current.addLayer({
      id: 'clusters',
      type: 'circle',
      source: 'properties',
      filter: ['has', 'point_count'],
      paint: {
        'circle-color': [
          'step',
          ['get', 'point_count'],
          '#10b981', 20,
          '#3b82f6', 50,
          '#8b5cf6'
        ],
        'circle-radius': [
          'step',
          ['get', 'point_count'],
          20, 20,
          30, 50,
          40
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff'
      }
    });

    // Add cluster count labels
    map.current.addLayer({
      id: 'cluster-count',
      type: 'symbol',
      source: 'properties',
      filter: ['has', 'point_count'],
      layout: {
        'text-field': '{point_count_abbreviated}',
        'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
        'text-size': 12
      },
      paint: {
        'text-color': '#ffffff'
      }
    });

    // Add individual property markers
    map.current.addLayer({
      id: 'unclustered-point',
      type: 'circle',
      source: 'properties',
      filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-color': '#10b981',
        'circle-radius': 8,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff'
      }
    });

    // Add click handlers for clusters
    map.current.on('click', 'clusters', (e) => {
      const features = map.current!.queryRenderedFeatures(e.point, {
        layers: ['clusters']
      });
      const clusterId = features[0].properties.cluster_id;
      (map.current!.getSource('properties') as mapboxgl.GeoJSONSource).getClusterExpansionZoom(
        clusterId,
        (err, zoom) => {
          if (err) return;
          
          map.current!.easeTo({
            center: (features[0].geometry as any).coordinates,
            zoom: zoom
          });
        }
      );
    });

    // Add click handler for individual points
    map.current.on('click', 'unclustered-point', (e) => {
      if (!e.features || !e.features[0]) return;
      
      const props = e.features[0].properties;
      const property = properties[props.index];
      
      if (property) {
        setSelectedProperty(property);
        map.current!.flyTo({
          center: (e.features[0].geometry as any).coordinates,
          zoom: 15,
          essential: true
        });
      }
    });

    // Change cursor on hover
    map.current.on('mouseenter', 'clusters', () => {
      map.current!.getCanvas().style.cursor = 'pointer';
    });
    map.current.on('mouseleave', 'clusters', () => {
      map.current!.getCanvas().style.cursor = '';
    });
    map.current.on('mouseenter', 'unclustered-point', () => {
      map.current!.getCanvas().style.cursor = 'pointer';
    });
    map.current.on('mouseleave', 'unclustered-point', () => {
      map.current!.getCanvas().style.cursor = '';
    });

    console.log('[PropertyMapViewClient] Created clustered markers');

    // Fit map to show all markers
    if (geojsonData.features.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      geojsonData.features.forEach(feature => {
        bounds.extend(feature.geometry.coordinates as [number, number]);
      });
      
      map.current.fitBounds(bounds, {
        padding: { top: 100, bottom: 100, left: 100, right: 400 },
        maxZoom: 13
      });
    }
  }, [properties, mapLoaded]);

  console.log('[PropertyMapViewClient] Rendering - mapLoaded:', mapLoaded, 'selectedProperty:', !!selectedProperty);

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `£${price.toLocaleString()}`;
    }
    return `£${price.toLocaleString()}`;
  };

  return (
    <div className="relative h-full w-full bg-slate-900">
      <div ref={mapContainer} className="absolute inset-0 w-full h-full" style={{ minHeight: '400px' }} />
      
      {/* Debug overlay */}
      <div className="absolute top-2 left-2 bg-black/80 text-white text-xs p-2 rounded z-50 pointer-events-none">
        <div>Map Loaded: {mapLoaded ? '✓' : '✗'}</div>
        <div>Properties: {properties.length}</div>
        <div>Clustered: ✓</div>
        <div>Token: {mapboxgl.accessToken ? '✓' : '✗'}</div>
      </div>
      
      {/* Property Detail Card */}
      {selectedProperty && (
        <Card className="absolute top-4 right-4 w-96 max-h-[calc(100vh-8rem)] overflow-auto shadow-xl z-10">
          <div className="relative">
            {/* Close button */}
            <button
              onClick={() => setSelectedProperty(null)}
              className="absolute top-2 right-2 z-10 p-1.5 bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Property Image */}
            {selectedProperty.imageUrl && (
              <img
                src={selectedProperty.imageUrl}
                alt={selectedProperty.title}
                className="w-full h-48 object-cover rounded-t-lg"
              />
            )}

            {/* Property Details */}
            <div className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-lg line-clamp-2">
                    {selectedProperty.title}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {selectedProperty.location}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 mb-3 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Bed className="w-4 h-4" />
                  <span>{selectedProperty.beds} beds</span>
                </div>
                <div className="flex items-center gap-1">
                  <Bath className="w-4 h-4" />
                  <span>{selectedProperty.baths} baths</span>
                </div>
                <div className="flex items-center gap-1">
                  <Maximize className="w-4 h-4" />
                  <span>{selectedProperty.sqft.toLocaleString()} sqft</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-primary">
                    {formatPrice(selectedProperty.price)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {selectedProperty.type === 'rent' ? 'per month' : 'purchase price'}
                  </div>
                </div>
                
                <a
                  href={selectedProperty.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors text-sm font-medium"
                >
                  View Details
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>

              {/* Amenities */}
              {selectedProperty.amenities && selectedProperty.amenities.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <h4 className="text-sm font-semibold mb-2">Nearby Amenities</h4>
                  <div className="space-y-1">
                    {selectedProperty.amenities.slice(0, 5).map((amenity, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">{amenity.name}</span>
                        <span className="font-medium">{amenity.distance}m</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Instructions overlay when no properties */}
      {properties.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <Card className="p-6 text-center max-w-sm pointer-events-auto">
            <h3 className="text-lg font-semibold mb-2">No Properties to Display</h3>
            <p className="text-sm text-muted-foreground">
              Enter a postcode and search for properties to see them on the map
            </p>
          </Card>
        </div>
      )}
    </div>
  );
}
