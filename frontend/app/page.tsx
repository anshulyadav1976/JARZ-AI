"use client";

import React, { useState, useCallback, useEffect } from "react";
import { useChatStream } from "@/hooks/useChatStream";
import { usePropertyListings } from "@/hooks/usePropertyListings";
import { ChatPanel } from "@/components/ChatPanel";
import { A2UIRenderer } from "@/components/A2UIRenderer";
import { PropertyListView } from "@/components/PropertyListView";
import { PropertyMapView } from "@/components/PropertyMapView";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { BarChart3, Home as HomeIcon, User, TrendingUp, Home as Building, List, Map } from "lucide-react";

export default function Home() {
  const { state, sendMessage, reset } = useChatStream();
  const { state: propertyState, fetchListings } = usePropertyListings();
  const [showA2UIPanel, setShowA2UIPanel] = useState(true);
  const [activeTab, setActiveTab] = useState("home");
  const [sidebarMode, setSidebarMode] = useState<"rent-analysis" | "buying-selling">("rent-analysis");
  const [viewMode, setViewMode] = useState<"list" | "map">("list");

  const handleSendMessage = useCallback((message: string) => {
    sendMessage(message);
    
    // If in buying-selling mode, try to extract area code and fetch listings
    if (sidebarMode === "buying-selling") {
      const areaCodeMatch = message.match(/\b([A-Z]{1,2}\d{1,2}[A-Z]?)\b/i);
      if (areaCodeMatch) {
        const areaCode = areaCodeMatch[1].toUpperCase();
        fetchListings(areaCode, "sale");
      }
    }
  }, [sendMessage, sidebarMode, fetchListings]);

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  const hasA2UIContent = state.a2uiState.isReady && state.a2uiState.rootId;

  return (
    <main className="h-screen w-screen flex flex-col bg-gradient-to-br from-background via-background to-muted/20">
      <header className="flex-shrink-0 border-b bg-card/80 backdrop-blur-xl supports-[backdrop-filter]:bg-card/60">
        <div className="w-full flex h-16 items-center justify-between px-6 max-w-full">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-7 h-7">
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 24L14 4L24 24H4Z" fill="currentColor" className="text-foreground"/>
                <path d="M9 24L14 14L19 24H9Z" fill="currentColor" className="text-background"/>
              </svg>
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-foreground">RentRadar</h1>
          </div>

          <nav className="flex items-center gap-2">
            <Button
              variant={activeTab === "home" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("home")}
              className="gap-2"
            >
              <HomeIcon className="h-4 w-4" />
              <span className="hidden sm:inline">Home</span>
            </Button>
            <Button
              variant={activeTab === "about" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("about")}
              className="gap-2"
            >
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">About</span>
            </Button>
          </nav>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden w-full">
        {/* Sidebar */}
        <div className="w-20 flex-shrink-0 border-r bg-card/50 flex flex-col items-center py-4 gap-3">
          <Button
            variant={sidebarMode === "rent-analysis" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setSidebarMode("rent-analysis")}
            className="w-12 h-12"
            title="Rent Analysis"
          >
            <TrendingUp className="h-5 w-5" />
          </Button>
          <Button
            variant={sidebarMode === "buying-selling" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setSidebarMode("buying-selling")}
            className="w-12 h-12"
            title="Buying & Selling"
          >
            <Building className="h-5 w-5" />
          </Button>
        </div>

        {/* Chat Panel */}
        <div className={`flex-shrink-0 border-r transition-all duration-300 ${showA2UIPanel && (hasA2UIContent || sidebarMode === "buying-selling") ? "w-full md:w-1/2 lg:w-2/5" : "w-full"}`}>
          <ChatPanel
            messages={state.messages}
            onSendMessage={handleSendMessage}
            isLoading={state.isLoading}
            currentTool={state.currentTool}
            streamingContent={state.streamingContent}
            onTogglePanel={() => setShowA2UIPanel(!showA2UIPanel)}
            showPanel={showA2UIPanel}
          />
        </div>

        {/* Insights/Property Panel */}
        {showA2UIPanel && (
          <div className={`flex-1 overflow-hidden transition-all duration-300 ${hasA2UIContent || sidebarMode === "buying-selling" ? "block" : "hidden md:block"}`}>
            {sidebarMode === "rent-analysis" ? (
              <div className="h-full overflow-y-auto bg-muted/30">
                {hasA2UIContent ? (
                  <div className="p-6 space-y-4">
                    <A2UIRenderer state={state.a2uiState} />
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center px-8 py-12 max-w-md">
                      <div className="w-20 h-20 mx-auto mb-6 bg-primary/10 rounded-full flex items-center justify-center">
                        <BarChart3 className="w-10 h-10 text-primary" />
                      </div>
                      <h3 className="text-lg font-semibold mb-2">Insights Panel</h3>
                      <p className="text-sm text-muted-foreground">
                        Ask about a location to see rental forecasts, market analysis, and visualizations appear here.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col bg-muted/30">
                {/* View Toggle */}
                <div className="flex-shrink-0 border-b px-4 py-3 bg-card/50">
                  <div className="flex items-center justify-between">
                    <h2 className="font-semibold text-sm">Property Listings</h2>
                    <div className="flex items-center gap-1 bg-muted rounded-md p-1">
                      <Button
                        variant={viewMode === "list" ? "secondary" : "ghost"}
                        size="sm"
                        onClick={() => setViewMode("list")}
                        className="h-7 px-3"
                      >
                        <List className="h-4 w-4 mr-1" />
                        <span className="text-xs">List</span>
                      </Button>
                      <Button
                        variant={viewMode === "map" ? "secondary" : "ghost"}
                        size="sm"
                        onClick={() => setViewMode("map")}
                        className="h-7 px-3"
                      >
                        <Map className="h-4 w-4 mr-1" />
                        <span className="text-xs">Map</span>
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4">
                  {viewMode === "list" ? (
                    <PropertyListView 
                      properties={propertyState.properties}
                      isLoading={propertyState.isLoading}
                      error={propertyState.error}
                    />
                  ) : (
                    <PropertyMapView />
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <footer className="flex-shrink-0 border-t bg-card/80 backdrop-blur">
        <div className="w-full px-6 py-3 max-w-full">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
            <span>RentRadar - AI Rental Valuation © 2026</span>
            <div className="flex items-center gap-3">
              <span>Powered by AI</span>
              <Separator orientation="vertical" className="h-4 hidden sm:block" />
              <span className="hidden sm:inline">RealTech</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
