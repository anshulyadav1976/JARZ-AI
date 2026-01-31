"use client";

import React, { useState, useCallback, useEffect } from "react";
import { useChatStream } from "@/hooks/useChatStream";
import { usePropertyListings } from "@/hooks/usePropertyListings";
import { ChatPanel } from "@/components/ChatPanel";
import { A2UIRenderer } from "@/components/A2UIRenderer";
import { PropertyListView } from "@/components/PropertyListView";
import { PropertyMapView } from "@/components/PropertyMapView";
import { InsightsActions } from "@/components/InsightsActions";
import { InsightsDisclaimer } from "@/components/InsightsDisclaimer";
import { ComparisonMode } from "@/components/ComparisonMode";
import { BudgetFilter } from "@/components/BudgetFilter";
import { InvestmentCalculator } from "@/components/InvestmentCalculator";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { BarChart3, Home as HomeIcon, User, TrendingUp, Home as Building, List, Map, Calculator, LineChart, Sparkles, Search } from "lucide-react";

export default function Home() {
  const { state, sendMessage, reset } = useChatStream();
  const { state: propertyState, fetchListings } = usePropertyListings();
  const [activeTab, setActiveTab] = useState("home");
  const [sidebarMode, setSidebarMode] = useState<"valuation" | "properties" | "market-trends" | "investment" | "search">("valuation");
  const [viewMode, setViewMode] = useState<"list" | "map">("list");
  const [comparedAreas, setComparedAreas] = useState<string[]>([]);
  const [savedAreas, setSavedAreas] = useState<string[]>([]);
  const [currentArea, setCurrentArea] = useState<string>("");

  const handleSendMessage = useCallback((message: string) => {
    sendMessage(message);
    
    // Extract area code from message
    const areaCodeMatch = message.match(/\b([A-Z]{1,2}\d{1,2}[A-Z]?)\b/i);
    if (areaCodeMatch) {
      const areaCode = areaCodeMatch[1].toUpperCase();
      setCurrentArea(areaCode);
      
      // If in buying-selling mode, fetch listings
      if (sidebarMode === "buying-selling") {
        fetchListings(areaCode, "sale");
      }
    }
  }, [sendMessage, sidebarMode, fetchListings]);

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  const handleAddCompareArea = useCallback((areaCode: string) => {
    if (!comparedAreas.includes(areaCode) && comparedAreas.length < 3) {
      setComparedAreas([...comparedAreas, areaCode]);
    }
  }, [comparedAreas]);

  const handleRemoveCompareArea = useCallback((areaCode: string) => {
    setComparedAreas(comparedAreas.filter(a => a !== areaCode));
  }, [comparedAreas]);

  const handleToggleSave = useCallback(() => {
    if (currentArea) {
      if (savedAreas.includes(currentArea)) {
        setSavedAreas(savedAreas.filter(a => a !== currentArea));
      } else {
        setSavedAreas([...savedAreas, currentArea]);
      }
    }
  }, [currentArea, savedAreas]);

  const handleBudgetSearch = useCallback((budget: number, bedrooms?: number) => {
    const bedroomText = bedrooms ? `${bedrooms}-bedroom ` : "";
    sendMessage(`Show me areas where I can rent a ${bedroomText}property for around £${budget} per month`);
  }, [sendMessage]);

  const hasA2UIContent = state.a2uiState.isReady && state.a2uiState.rootId;
  
  // Extract prediction data for investment calculator
  const getPredictionData = () => {
    if (!hasA2UIContent) return null;
    try {
      const p50 = state.a2uiState.dataModel?.prediction?.p50 as number;
      const location = state.a2uiState.dataModel?.location as string;
      if (p50 && location) {
        return { p50, location };
      }
    } catch (e) {
      // Silently fail if data structure is different
    }
    return null;
  };
  
  const predictionData = getPredictionData();

  return (
    <main className="h-screen w-screen flex flex-col bg-gradient-to-br from-background via-background to-muted/20 overflow-hidden">
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

      <div className="flex-1 flex overflow-hidden w-full min-h-0">
        {/* Sidebar - only show after user sends first message */}
        {state.messages.length > 0 && (
          <div className="w-14 flex-shrink-0 border-r bg-card/50 flex flex-col items-center justify-start py-3 gap-1.5">
            <Button
              variant={sidebarMode === "valuation" ? "secondary" : "ghost"}
              size="icon"
              onClick={() => setSidebarMode("valuation")}
              className="w-10 h-10"
              title="Valuation & Insights"
            >
              <Sparkles className="h-4 w-4" />
            </Button>
            <Button
              variant={sidebarMode === "search" ? "secondary" : "ghost"}
              size="icon"
              onClick={() => setSidebarMode("search")}
              className="w-10 h-10"
              title="Search & Filter"
            >
              <Search className="h-4 w-4" />
            </Button>
            <Button
              variant={sidebarMode === "properties" ? "secondary" : "ghost"}
              size="icon"
              onClick={() => setSidebarMode("properties")}
              className="w-10 h-10"
              title="Property Listings"
            >
              <Building className="h-4 w-4" />
            </Button>
            <Button
              variant={sidebarMode === "market-trends" ? "secondary" : "ghost"}
              size="icon"
              onClick={() => setSidebarMode("market-trends")}
              className="w-10 h-10"
              title="Market Trends"
            >
              <LineChart className="h-4 w-4" />
            </Button>
            <Button
              variant={sidebarMode === "investment" ? "secondary" : "ghost"}
              size="icon"
              onClick={() => setSidebarMode("investment")}
              className="w-10 h-10"
              title="Investment Analysis"
            >
              <Calculator className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Chat Panel */}
        <div className={`flex-shrink-0 border-r transition-all duration-300 ${hasA2UIContent || sidebarMode !== "valuation" ? "w-full md:w-[45%] lg:w-[38%]" : "w-full"}`}>
          <ChatPanel
            messages={state.messages}
            onSendMessage={handleSendMessage}
            isLoading={state.isLoading}
            currentTool={state.currentTool}
            streamingContent={state.streamingContent}
          />
        </div>

        {/* Insights/Property Panel */}
        {(
          <div className={`flex-1 overflow-hidden transition-all duration-300 ${hasA2UIContent || sidebarMode !== "valuation" ? "block" : "hidden md:block"}`}>
            {/* Valuation & AI Insights */}
            {sidebarMode === "valuation" && (
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-background via-muted/10 to-muted/20">
                {hasA2UIContent ? (
                  <>
                    {/* Action Buttons Header */}
                    <InsightsActions 
                      isSaved={currentArea && savedAreas.includes(currentArea)}
                      onToggleSave={currentArea ? handleToggleSave : undefined}
                    />
                    
                    {/* Scrollable Content */}
                    <div className="flex-1 overflow-y-auto">
                      <div className="p-6 space-y-6">
                        {/* Comparison Tool */}
                        <ComparisonMode
                          comparedAreas={comparedAreas}
                          onAddArea={handleAddCompareArea}
                          onRemoveArea={handleRemoveCompareArea}
                        />
                        
                        {/* Budget Filter */}
                        <BudgetFilter onSearch={handleBudgetSearch} />
                        
                        {/* Main Insights */}
                        <A2UIRenderer state={state.a2uiState} />
                        
                        {/* Investment Calculator (if we have prediction data) */}
                        {predictionData && (
                          <InvestmentCalculator 
                            predictedRent={predictionData.p50}
                            location={predictionData.location}
                          />
                        )}
                      </div>
                      
                      {/* Disclaimer Footer */}
                      <InsightsDisclaimer />
                    </div>
                  </>
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
            )}
            
            {/* Search & Filter Page */}
            {sidebarMode === "search" && (
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-background via-muted/10 to-muted/20">
                <div className="flex-shrink-0 p-4 border-b bg-card/50">
                  <h2 className="text-lg font-semibold text-foreground">Search & Filter</h2>
                  <p className="text-xs text-muted-foreground">Find properties by budget and criteria</p>
                </div>
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* Budget Filter */}
                  <BudgetFilter onSearch={handleBudgetSearch} />
                  
                  {/* Comparison Tool */}
                  <ComparisonMode
                    comparedAreas={comparedAreas}
                    onAddArea={handleAddCompareArea}
                    onRemoveArea={handleRemoveCompareArea}
                  />
                  
                  <div className="p-6 bg-card border border-border rounded-lg text-center">
                    <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-sm font-semibold mb-2">Quick Search Tips</h3>
                    <ul className="text-xs text-muted-foreground space-y-1 text-left">
                      <li>• Search by postcode (e.g., "NW1", "E14")</li>
                      <li>• Filter by budget and bedrooms</li>
                      <li>• Compare up to 3 areas</li>
                      <li>• Ask "Show me areas under £2000/month"</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
            
            {/* Property Listings Page */}
            {sidebarMode === "properties" && (
              <div className="h-full flex flex-col bg-muted/30">
                {/* View Toggle */}
                <div className="flex-shrink-0 border-b px-4 py-3 bg-card/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-foreground">Property Listings</h2>
                      <p className="text-xs text-muted-foreground">Available properties in your area</p>
                    </div>
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
            
            {/* Market Trends Page */}
            {sidebarMode === "market-trends" && (
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-background via-muted/10 to-muted/20">
                <div className="flex-shrink-0 p-4 border-b bg-card/50">
                  <h2 className="text-lg font-semibold text-foreground">Market Trends</h2>
                  <p className="text-xs text-muted-foreground">Historical data and market analysis</p>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  {hasA2UIContent ? (
                    <div className="space-y-6">
                      <A2UIRenderer state={state.a2uiState} />
                      <InsightsDisclaimer />
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <div className="text-center px-8 py-12 max-w-md">
                        <div className="w-20 h-20 mx-auto mb-6 bg-primary/10 rounded-full flex items-center justify-center">
                          <LineChart className="w-10 h-10 text-primary" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">Market Trends</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Ask about a location to see historical trends, forecast timelines, and market patterns.
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Try: "Show me rental trends for NW1"
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Investment Analysis Page */}
            {sidebarMode === "investment" && (
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-background via-muted/10 to-muted/20">
                <div className="flex-shrink-0 p-4 border-b bg-card/50">
                  <h2 className="text-lg font-semibold text-foreground">Investment Analysis</h2>
                  <p className="text-xs text-muted-foreground">ROI and rental yield calculations</p>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  {predictionData ? (
                    <div className="space-y-6">
                      <InvestmentCalculator 
                        predictedRent={predictionData.p50}
                        location={predictionData.location}
                      />
                      <div className="p-6 bg-card border border-border rounded-lg">
                        <h3 className="text-sm font-semibold mb-3">Investment Tips</h3>
                        <ul className="text-xs text-muted-foreground space-y-2">
                          <li>✓ Aim for 5%+ rental yield in most UK markets</li>
                          <li>✓ Consider capital growth potential alongside yield</li>
                          <li>✓ Factor in 20-30% for costs (maintenance, void periods, fees)</li>
                          <li>✓ Check local demand indicators and transport links</li>
                          <li>✓ Compare against savings account returns (typically 3-5%)</li>
                        </ul>
                      </div>
                      <InsightsDisclaimer />
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <div className="text-center px-8 py-12 max-w-md">
                        <div className="w-20 h-20 mx-auto mb-6 bg-primary/10 rounded-full flex items-center justify-center">
                          <Calculator className="w-10 h-10 text-primary" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">Investment Calculator</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Get a rental valuation first, then calculate your investment returns.
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Try: "What's the expected rent for a 2-bed in E14?"
                        </p>
                      </div>
                    </div>
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
