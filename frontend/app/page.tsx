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
import { InvestmentCalculator } from "@/components/InvestmentCalculator";
import { InvestmentAnalysisView } from "@/components/InvestmentAnalysisView";
import { Tooltip } from "@/components/ui/tooltip-custom";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { BarChart3, Home as HomeIcon, User, UserCircle, MessageSquarePlus, Menu, Sparkles, ArrowLeftRight, Search, Leaf, Calculator, Database, LineChart, List, Map } from "lucide-react";
import { MarketDataPanel } from "@/components/MarketDataPanel";
import {
  getProfile,
  saveProfile,
  PROFILE_ROLE_LABELS,
  INTEREST_OPTIONS,
  type UserProfile,
  type ProfileRole,
  type InterestId,
} from "@/lib/profile";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export default function Home() {
  const [marketTrigger, setMarketTrigger] = useState<{ district?: string | null; postcode?: string | null } | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const { state, sendMessage, reset, loadConversation, applyA2UIMessages } = useChatStream({
    onMarketDataRequest: (data) => {
      setSidebarMode("market");
      setMarketTrigger({ district: data.district ?? null, postcode: data.postcode ?? null });
    },
  });
  const { state: propertyState, fetchListings, fetchListingsBoth } = usePropertyListings();
  const [activeTab, setActiveTab] = useState("home");
  const [sidebarMode, setSidebarMode] = useState<"valuation" | "comparison" | "properties" | "sustainability" | "investment" | "market">("valuation");
  const [viewMode, setViewMode] = useState<"list" | "map">("list");
  const [listingFilterType, setListingFilterType] = useState<"all" | "rent" | "sale">("all");
  const [comparedAreas, setComparedAreas] = useState<string[]>([]);
  const [savedAreas, setSavedAreas] = useState<string[]>([]);
  const [currentArea, setCurrentArea] = useState<string>("");
  const [autoSwitchEnabled, setAutoSwitchEnabled] = useState(true);

  // Profile form state (for Profile tab)
  const [profileName, setProfileName] = useState("");
  const [profileRole, setProfileRole] = useState<ProfileRole | "">("");
  const [profileBio, setProfileBio] = useState("");
  const [profileInterests, setProfileInterests] = useState<string[]>([]);
  const [profilePreferences, setProfilePreferences] = useState("");
  const [profileSaved, setProfileSaved] = useState(false);
  const [chatHistoryOpen, setChatHistoryOpen] = useState(false);

  const handleSendMessage = useCallback((message: string) => {
    sendMessage(message);
    setAutoSwitchEnabled(true); // Re-enable auto-switch when user sends a new message
    
    // Extract area code from message
    const areaCodeMatch = message.match(/\b([A-Z]{1,2}\d{1,2}[A-Z]?)\b/i);
    if (areaCodeMatch) {
      const areaCode = areaCodeMatch[1].toUpperCase();
      setCurrentArea(areaCode);
      // Default to showing all listings on new postcode
      setListingFilterType("all");
      
      // If in properties mode, fetch listings
      if (sidebarMode === "properties") {
        fetchListingsBoth(areaCode);
      }
    }
  }, [sendMessage, sidebarMode, fetchListingsBoth]);

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  const handleNewChat = useCallback(() => {
    reset();
  }, [reset]);

  const handleLoadConversation = useCallback((id: string) => {
    loadConversation(id);
  }, [loadConversation]);

  // Load profile from localStorage when opening Profile tab
  useEffect(() => {
    if (activeTab === "profile") {
      const p = getProfile();
      setProfileName(p?.name ?? "");
      setProfileRole((p?.role as ProfileRole) ?? "");
      setProfileBio(p?.bio ?? "");
      setProfileInterests(p?.interests ?? []);
      setProfilePreferences(p?.preferences ?? "");
      setProfileSaved(false);
    }
  }, [activeTab]);

  const handleProfileSave = useCallback(() => {
    const profile: UserProfile = {
      name: profileName.trim() || null,
      role: profileRole || null,
      bio: profileBio.trim() || null,
      interests: profileInterests.length ? profileInterests : null,
      preferences: profilePreferences.trim() || null,
    };
    saveProfile(profile);
    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 2000);
  }, [profileName, profileRole, profileBio, profileInterests, profilePreferences]);

  const toggleProfileInterest = useCallback((id: InterestId) => {
    setProfileInterests((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }, []);

  // Fetch conversation list (on mount and when current conversation changes so new chats appear)
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/conversations`)
      .then((res) => (res.ok ? res.json() : []))
      .then((list: ConversationSummary[]) => {
        if (!cancelled) setConversations(Array.isArray(list) ? list : []);
      })
      .catch(() => {
        if (!cancelled) setConversations([]);
      });
    return () => {
      cancelled = true;
    };
  }, [state.conversationId]);

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
  
  const handleManualSidebarChange = useCallback((mode: typeof sidebarMode) => {
    setSidebarMode(mode);
    setAutoSwitchEnabled(false); // Disable auto-switch when user manually changes tab
  }, []);

  const handleRunComparison = useCallback(async () => {
    if (comparedAreas.length < 2) return;
    try {
      const res = await fetch(`${API_URL}/api/areas/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ areas: comparedAreas }),
      });
      const data = await res.json();
      if (data?.a2ui_messages) {
        applyA2UIMessages(data.a2ui_messages);
        setSidebarMode("comparison");
      }
    } catch (e) {
      console.error("Comparison request failed", e);
    }
  }, [comparedAreas, applyA2UIMessages]);

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
      
      console.log("[AUTO-SWITCH] Data model:", dataModel);
      console.log("[AUTO-SWITCH] Has listings:", !!dataModel.listings);
      console.log("[AUTO-SWITCH] Has properties:", !!dataModel.listings?.properties);
      console.log("[AUTO-SWITCH] Has investment:", !!dataModel.investment);
      console.log("[AUTO-SWITCH] Has prediction:", !!dataModel.prediction);
      console.log("[AUTO-SWITCH] Has carbon:", !!dataModel.carbon);
      
      // Property listings tool → properties tab
      if (dataModel.listings?.properties) {
        console.log("[AUTO-SWITCH] Switching to properties tab");
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

  // Auto-fetch listings when area or filter changes (no click needed)
  useEffect(() => {
    if (!currentArea) return;
    const h = setTimeout(() => {
      if (listingFilterType === "all") {
        fetchListingsBoth(currentArea);
      } else {
        fetchListings(currentArea, listingFilterType);
      }
    }, 500);
    return () => clearTimeout(h);
  }, [currentArea, listingFilterType, fetchListings, fetchListingsBoth]);

  // Reset filter to "all" when postcode changes to show both initially
  useEffect(() => {
    if (currentArea) {
      setListingFilterType("all");
    }
  }, [currentArea]);

  return (
    <main className="h-screen w-screen flex flex-col bg-gradient-to-br from-background via-background to-muted/20 overflow-hidden">
      <header className="flex-shrink-0 border-b bg-card/80 backdrop-blur-xl supports-[backdrop-filter]:bg-card/60">
        <div className="w-full flex h-16 items-center justify-between px-6 max-w-full">
          <div className="flex items-center gap-3">
            {activeTab === "home" && (
              <Tooltip content={chatHistoryOpen ? "Close chat history" : "Open chat history"} side="right">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setChatHistoryOpen((o) => !o)}
                  className="w-9 h-9 shrink-0"
                  aria-label={chatHistoryOpen ? "Close chat history" : "Open chat history"}
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </Tooltip>
            )}
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
              variant={activeTab === "profile" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("profile")}
              className="gap-2"
            >
              <UserCircle className="h-4 w-4" />
              <span className="hidden sm:inline">Profile</span>
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

      {activeTab === "profile" ? (
        <div className="flex-1 overflow-y-auto p-6 max-w-2xl mx-auto">
          <h2 className="text-xl font-semibold mb-4">Your profile</h2>
          <p className="text-muted-foreground text-sm mb-6">
            This helps RentRadar personalise replies. Your name, role and interests are only used in the chat and are not stored on our servers.
          </p>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-1">Name</label>
              <input
                type="text"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                placeholder="e.g. Alex"
                className="w-full h-9 px-3 rounded-md border bg-background text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">I am a</label>
              <select
                value={profileRole}
                onChange={(e) => setProfileRole(e.target.value as ProfileRole | "")}
                className="w-full h-9 px-3 rounded-md border bg-background text-sm"
                aria-label="Profile role"
              >
                <option value="">— Select —</option>
                {(Object.entries(PROFILE_ROLE_LABELS) as [ProfileRole, string][]).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Short bio (optional)</label>
              <textarea
                value={profileBio}
                onChange={(e) => setProfileBio(e.target.value)}
                placeholder="A sentence about you"
                rows={2}
                className="w-full px-3 py-2 rounded-md border bg-background text-sm resize-none"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Interests (tick what matters to you)</label>
              <div className="flex flex-wrap gap-3">
                {INTEREST_OPTIONS.map(({ id, label }) => (
                  <label key={id} className="flex items-center gap-2 cursor-pointer text-sm">
                    <input
                      type="checkbox"
                      checked={profileInterests.includes(id)}
                      onChange={() => toggleProfileInterest(id)}
                      className="rounded border"
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">What I&apos;m looking for (optional)</label>
              <textarea
                value={profilePreferences}
                onChange={(e) => setProfilePreferences(e.target.value)}
                placeholder="e.g. First buy in London, 2-bed, budget around £400k"
                rows={2}
                className="w-full px-3 py-2 rounded-md border bg-background text-sm resize-none"
              />
            </div>
            <Button onClick={handleProfileSave} className="mt-4">
              {profileSaved ? "Saved" : "Save profile"}
            </Button>
          </div>
        </div>
      ) : (
      <div className="flex-1 flex overflow-hidden w-full min-w-0 min-h-0">
        {/* Chat history sidebar: only when hamburger is toggled */}
        {chatHistoryOpen && (
        <div className="w-52 flex-shrink-0 border-r bg-muted/30 flex flex-col overflow-hidden">
          <div className="p-2 border-b flex-shrink-0">
            <Button
              variant="default"
              size="sm"
              className="w-full gap-2"
              onClick={handleNewChat}
            >
              <MessageSquarePlus className="h-4 w-4" />
              New chat
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto py-2">
            {conversations.length === 0 ? (
              <p className="text-muted-foreground text-xs px-3 py-2">No past chats yet</p>
            ) : (
              <ul className="space-y-0.5 px-2">
                {conversations.map((c) => (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => handleLoadConversation(c.id)}
                      className={`w-full text-left rounded-lg px-3 py-2 text-sm truncate transition-colors ${
                        state.conversationId === c.id
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      }`}
                      title={c.title || "Chat"}
                    >
                      {c.title || "Chat"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        )}

        {/* Icon sidebar - always visible for switching features */}
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
            <Tooltip content="Location Comparison" side="right">
              <Button
                variant={sidebarMode === "comparison" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("comparison")}
                className="w-10 h-10"
              >
                <ArrowLeftRight className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Property Finder" side="right">
              <Button
                variant={sidebarMode === "properties" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("properties")}
                className="w-10 h-10"
              >
                <Search className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Sustainability" side="right">
              <Button
                variant={sidebarMode === "sustainability" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("sustainability")}
                className="w-10 h-10"
              >
                <Leaf className="h-4 w-4" />
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
            <Tooltip content="Market Data" side="right">
              <Button
                variant={sidebarMode === "market" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => handleManualSidebarChange("market")}
                className="w-10 h-10"
              >
                <Database className="h-4 w-4" />
              </Button>
            </Tooltip>
          </div>

        {/* Chat Panel */}
        <div className={`flex-shrink min-w-0 border-r transition-all duration-300 ${hasA2UIContent || sidebarMode !== "valuation" ? "w-full md:w-[45%] lg:w-[38%]" : "w-full"}`}>
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
          <div className={`flex-1 min-w-0 overflow-hidden transition-all duration-300 ${hasA2UIContent || sidebarMode !== "valuation" ? "block" : "hidden md:block"}`}>
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
            
            {/* Search & Filter Page removed */}

            {/* Market Data (Growth, Demand, Valuations, Sale History) */}
            {sidebarMode === "market" && (
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-background via-muted/10 to-muted/20">
                <div className="flex-shrink-0 p-4 border-b bg-card/50">
                  <h2 className="text-lg font-semibold text-foreground">Market Data</h2>
                  <p className="text-xs text-muted-foreground">
                    Growth, rent & sale demand (district), current & historical valuations, sale history + export (postcode).
                  </p>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  <MarketDataPanel
                  defaultDistrict={currentArea}
                  defaultPostcode={currentArea ? `${currentArea} 0BH` : ""}
                  triggerDistrict={marketTrigger?.district}
                  triggerPostcode={marketTrigger?.postcode}
                  onTriggerConsumed={() => setMarketTrigger(null)}
                />
                </div>
              </div>
            )}

            {/* Location Comparison Page */}
            {sidebarMode === "comparison" && (
              <div className="h-full flex flex-col overflow-hidden bg-gradient-to-br from-background via-muted/10 to-muted/20">
                <div className="flex-shrink-0 p-4 border-b bg-card/50">
                  <h2 className="text-lg font-semibold text-foreground">Location Comparison</h2>
                  <p className="text-xs text-muted-foreground">
                    Compare 2–3 areas using ScanSan area summary (ranges + listing counts).
                  </p>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  <ComparisonMode
                    comparedAreas={comparedAreas}
                    onAddArea={handleAddCompareArea}
                    onRemoveArea={handleRemoveCompareArea}
                  />

                  <div className="flex gap-2">
                    <Button
                      onClick={handleRunComparison}
                      disabled={comparedAreas.length < 2}
                      className="gap-2"
                    >
                      Compare now
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => sendMessage(`Compare ${comparedAreas.join(" vs ")}`)}
                      disabled={comparedAreas.length < 2}
                    >
                      Ask agent to compare
                    </Button>
                  </div>

                  <div className="bg-white/60 dark:bg-slate-900/60 rounded-xl p-4 border-2 border-muted shadow">
                    <A2UIRenderer state={filterA2UIByPath("comparison")} />
                  </div>

                  <InsightsDisclaimer />
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
                      <p className="text-xs text-muted-foreground">Type an area code (e.g., NW1) and fetch listings</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Listing type dropdown (also triggers fetch) */}
                      <select
                        value={listingFilterType}
                        onChange={(e) => {
                          const val = e.target.value as "all" | "rent" | "sale";
                          setListingFilterType(val);
                          if (currentArea) {
                            if (val === "all") {
                              fetchListingsBoth(currentArea);
                            } else {
                              fetchListings(currentArea, val);
                            }
                          }
                        }}
                        className="h-7 px-2 text-xs border rounded-md bg-background"
                        aria-label="Listing Type"
                      >
                        <option value="all">All</option>
                        <option value="rent">Rent</option>
                        <option value="sale">Sale</option>
                      </select>
                      {/* View toggle */}
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
                  {/* Area code input (auto-fetch) */}
                  <div className="mt-3 grid grid-cols-1 gap-2">
                    <input
                      className="h-9 px-3 border rounded-md bg-background text-sm"
                      placeholder="Enter area code (e.g., NW1)"
                      value={currentArea}
                      onChange={(e) => setCurrentArea(e.target.value.toUpperCase())}
                    />
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                  {viewMode === "list" ? (
                    <PropertyListView 
                      properties={propertiesFromAgent.length > 0 ? propertiesFromAgent : propertyState.properties}
                      isLoading={state.isLoading || propertyState.isLoading}
                      error={propertyState.error}
                      forcedFilterType={listingFilterType}
                    />
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
      )}

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
