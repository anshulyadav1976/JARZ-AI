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
import { InvestmentAnalysisView } from "@/components/InvestmentAnalysisView";
import { Tooltip } from "@/components/ui/tooltip-custom";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { BarChart3, Home as HomeIcon, User, TrendingUp, Home as Building, List, Map, Calculator, LineChart, Sparkles, Search } from "lucide-react";

export default function Home() {
  const { state, sendMessage, reset } = useChatStream();
  const { state: propertyState, fetchListings } = usePropertyListings();
  const [activeTab, setActiveTab] = useState("home");
  const [sidebarMode, setSidebarMode] = useState<"valuation" | "properties" | "sustainability" | "investment" | "search">("valuation");
  const [viewMode, setViewMode] = useState<"list" | "map">("list");
  const [comparedAreas, setComparedAreas] = useState<string[]>([]);
  const [savedAreas, setSavedAreas] = useState<string[]>([]);
  const [currentArea, setCurrentArea] = useState<string>("");
  const [autoSwitchEnabled, setAutoSwitchEnabled] = useState(true);

  const handleSendMessage = useCallback((message: string) => {
    sendMessage(message);
    setAutoSwitchEnabled(true); // Re-enable auto-switch when user sends a new message
    
    // Extract area code from message
    const areaCodeMatch = message.match(/\b([A-Z]{1,2}\d{1,2}[A-Z]?)\b/i);
    if (areaCodeMatch) {
      const areaCode = areaCodeMatch[1].toUpperCase();
      setCurrentArea(areaCode);
      
      // If in properties mode, fetch listings
      if (sidebarMode === "properties") {
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
  
  const handleManualSidebarChange = useCallback((mode: typeof sidebarMode) => {
    setSidebarMode(mode);
    setAutoSwitchEnabled(false); // Disable auto-switch when user manually changes tab
  }, []);

  const hasA2UIContent = state.a2uiState.isReady && state.a2uiState.rootId;
  // console.log("[PAGE] hasA2UIContent:", hasA2UIContent, "isReady:", state.a2uiState.isReady, "rootId:", state.a2uiState.rootId);
  
  // Helper function to filter A2UI state by data model path
  const filterA2UIByPath = useCallback((path: string) => {
    // console.log("[filterA2UIByPath] Called with path:", path);
    // console.log("[filterA2UIByPath] Full data model:", state.a2uiState.dataModel);
    if (!state.a2uiState.dataModel) {
      // console.log("[filterA2UIByPath] No data model, returning empty state");
      return state.a2uiState;
    }
    
    const dataModel = state.a2uiState.dataModel as any;
    const pathData = path.split('/').filter(Boolean).reduce(
      (obj, key) => obj?.[key],
      dataModel
    );
    
    // console.log("[filterA2UIByPath] Path data for", path, ":", pathData);
    
    if (!pathData) {
      // console.log("[filterA2UIByPath] No data at path, returning not ready");
      return { ...state.a2uiState, isReady: false };
    }
    
    // Create filtered data model with only this path
    const filteredDataModel: any = {};
    const keys = path.split('/').filter(Boolean);
    let current = filteredDataModel;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = {};
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = pathData;
    
    console.log("[filterA2UIByPath] Returning filtered data model:", filteredDataModel);
    
    return {
      ...state.a2uiState,
      dataModel: filteredDataModel,
    };
  }, [state.a2uiState]);
  
  // Auto-switch to appropriate tab based on tool/content type
  useEffect(() => {
    if (hasA2UIContent && state.a2uiState.dataModel && autoSwitchEnabled) {
      const dataModel = state.a2uiState.dataModel as any;
      
      // console.log("[AUTO-SWITCH] Data model:", dataModel);
      // console.log("[AUTO-SWITCH] Has listings:", !!dataModel.listings);
      // console.log("[AUTO-SWITCH] Has properties:", !!dataModel.listings?.properties);
      // console.log("[AUTO-SWITCH] Has investment:", !!dataModel.investment);
      // console.log("[AUTO-SWITCH] Has prediction:", !!dataModel.prediction);
      // console.log("[AUTO-SWITCH] Has carbon:", !!dataModel.carbon);
      
      // Property listings tool → properties tab
      if (dataModel.listings?.properties) {
        // console.log("[AUTO-SWITCH] Switching to properties tab");
        setSidebarMode("properties");
      }
      // Investment analysis tool → investment tab
      else if (dataModel.investment) {
        // console.log("[AUTO-SWITCH] Switching to investment tab");
        setSidebarMode("investment");
      }
      // Carbon/sustainability tool → sustainability tab
      else if (dataModel.carbon) {
        // console.log("[AUTO-SWITCH] Switching to sustainability tab");
        setSidebarMode("sustainability");
      }
      // Rent forecast or other prediction tools → valuation tab
      else if (dataModel.prediction) {
        // console.log("[AUTO-SWITCH] Switching to valuation tab");
        setSidebarMode("valuation");
      }
      // Default: valuation tab for any other A2UI content
      else {
        // console.log("[AUTO-SWITCH] Defaulting to valuation tab");
        setSidebarMode("valuation");
      }
    }
  }, [hasA2UIContent, autoSwitchEnabled, state.a2uiState.dataModel]);
  
  // Extract investment data for investment analysis view
  const getInvestmentData = () => {
    if (!hasA2UIContent) return null;
    try {
      const dataModel = state.a2uiState.dataModel as any;
      return dataModel?.investment || null;
    } catch {
      return null;
    }
  };

  const investmentData = getInvestmentData();
  
  // Extract prediction data for investment calculator
  const getPredictionData = () => {
    if (!hasA2UIContent) return null;
    try {
      const dataModel = state.a2uiState.dataModel as any;
      const p50 = dataModel?.prediction?.p50 as number;
      const location = dataModel?.location as string;
      if (p50 && location) {
        return { p50, location };
      }
    } catch (e) {
      // Silently fail if data structure is different
    }
    return null;
  };
  
  const predictionData = getPredictionData();

  // Get properties from A2UI data model (sent by agent)
  const getPropertiesFromDataModel = () => {
    try {
      const dataModel = state.a2uiState.dataModel as any;
      const properties = dataModel?.listings?.properties as any[];
      
      if (properties && Array.isArray(properties)) {
        // Properties now have amenities embedded in each property object
        return properties;
      }
    } catch (e) {
      console.error("Error extracting properties from data model:", e);
    }
    return [];
  };

  const propertiesFromAgent = getPropertiesFromDataModel();

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
            <Tooltip content="Valuation & Insights" side="right">
              <Button
                variant={sidebarMode === "valuation" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("valuation")}
                className="w-10 h-10"
              >
                <Sparkles className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Search & Filter" side="right">
              <Button
                variant={sidebarMode === "search" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("search")}
                className="w-10 h-10"
              >
                <Search className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Property Finder" side="right">
              <Button
                variant={sidebarMode === "properties" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("properties")}
                className="w-10 h-10"
              >
                <Building className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Sustainability" side="right">
              <Button
                variant={sidebarMode === "sustainability" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("sustainability")}
                className="w-10 h-10"
              >
                <LineChart className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Investment Analysis" side="right">
              <Button
                variant={sidebarMode === "investment" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("investment")}
                className="w-10 h-10"
              >
                <Calculator className="h-4 w-4" />
              </Button>
            </Tooltip>
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
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-blue-50 via-background to-indigo-50 dark:from-blue-950/20 dark:via-background dark:to-indigo-950/20">
                {hasA2UIContent ? (
                  <>
                    {/* Action Buttons Header */}
                    <InsightsActions 
                      isSaved={currentArea !== "" && savedAreas.includes(currentArea)}
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
                        
                        {/* Main Insights */}
                        <div className="bg-white/50 dark:bg-slate-900/50 rounded-xl p-1 border border-border shadow-lg">
                          <A2UIRenderer state={filterA2UIByPath('prediction')} />
                        </div>
                        
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
                      <div className="w-20 h-20 mx-auto mb-6 bg-muted rounded-full flex items-center justify-center">
                        <BarChart3 className="w-10 h-10 text-foreground" />
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
            
            {/* Property Finder Page */}
            {sidebarMode === "properties" && (
              <div className="h-full flex flex-col bg-muted/30">
                {/* View Toggle */}
                <div className="flex-shrink-0 border-b px-4 py-3 bg-card/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-foreground">Property Finder</h2>
                      <p className="text-xs text-muted-foreground">Find properties with images, links, and reviews</p>
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
                <div className="flex-1 overflow-hidden">
                  {viewMode === "list" ? (
                    <div className="h-full overflow-y-auto p-4">
                      <PropertyListView 
                        properties={propertiesFromAgent.length > 0 ? propertiesFromAgent : propertyState.properties}
                        isLoading={state.isLoading || propertyState.isLoading}
                        error={propertyState.error}
                      />
                    </div>
                  ) : (
                    <PropertyMapView 
                      properties={propertiesFromAgent.length > 0 ? propertiesFromAgent : propertyState.properties}
                    />
                  )}
                </div>
              </div>
            )}
            
            {/* Sustainability Assessment Page */}
            {sidebarMode === "sustainability" && (
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-background via-muted/10 to-muted/20">
                <div className="flex-shrink-0 p-4 border-b bg-card/50">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-muted rounded-lg">
                      <LineChart className="h-5 w-5 text-foreground" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-foreground">Sustainability Assessment</h2>
                      <p className="text-xs text-muted-foreground">Carbon emissions and energy efficiency analysis</p>
                    </div>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  {hasA2UIContent ? (
                    <div className="space-y-6">
                      <div className="bg-white/50 dark:bg-slate-900/50 rounded-xl p-4 border border-border shadow-lg">
                        <A2UIRenderer state={filterA2UIByPath('carbon')} />
                      </div>
                      <InsightsDisclaimer />
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <div className="text-center px-8 py-12 max-w-md">
                        <div className="w-20 h-20 mx-auto mb-6 bg-muted rounded-full flex items-center justify-center">
                          <LineChart className="w-10 h-10 text-foreground" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">Sustainability Assessment</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Ask about a property's carbon footprint, energy efficiency, and environmental impact.
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Try: "What is the carbon footprint of UB10 0GH?"
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
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-muted rounded-lg">
                      <Calculator className="h-5 w-5 text-foreground" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-foreground">Investment Analysis</h2>
                      <p className="text-xs text-muted-foreground">ROI, yields, and cash flow projections</p>
                    </div>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  {investmentData ? (
                    <InvestmentAnalysisView 
                      data={investmentData}
                      location={currentArea || "Unknown"}
                    />
                  ) : hasA2UIContent ? (
                    <div className="space-y-6">
                      <div className="bg-white/50 dark:bg-slate-900/50 rounded-xl p-4 border border-border shadow-lg">
                        <A2UIRenderer state={filterA2UIByPath('investment')} />
                      </div>
                      <InsightsDisclaimer />
                    </div>
                  ) : predictionData ? (
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
                        <div className="w-20 h-20 mx-auto mb-6 bg-muted rounded-full flex items-center justify-center">
                          <Calculator className="w-10 h-10 text-foreground" />
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
