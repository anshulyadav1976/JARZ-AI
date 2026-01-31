"use client";

import React, { useState, useCallback } from "react";
import { useChatStream } from "@/hooks/useChatStream";
import { ChatPanel } from "@/components/ChatPanel";
import { A2UIRenderer } from "@/components/A2UIRenderer";

export default function Home() {
  const { state, sendMessage, reset } = useChatStream();
  const [showA2UIPanel, setShowA2UIPanel] = useState(true);

  const handleSendMessage = useCallback(
    (message: string) => {
      sendMessage(message);
    },
    [sendMessage]
  );

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  // Check if we have any A2UI content to show
  const hasA2UIContent = state.a2uiState.isReady && state.a2uiState.rootId;

  return (
    <main className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="flex-shrink-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-screen-2xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  JARZ Rental Valuation
                </h1>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Spatio-Temporal Rental Forecasting
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Toggle A2UI Panel button */}
              <button
                onClick={() => setShowA2UIPanel(!showA2UIPanel)}
                className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  showA2UIPanel
                    ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                }`}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <span className="hidden sm:inline">
                  {showA2UIPanel ? "Hide" : "Show"} Insights
                </span>
              </button>

              {/* Reset button */}
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span className="hidden sm:inline">New Chat</span>
              </button>

              {/* Demo mode badge */}
              <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full">
                Demo Mode
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content - split view */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel - Left Side */}
        <div
          className={`flex-shrink-0 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ${
            showA2UIPanel && hasA2UIContent
              ? "w-full md:w-1/2 lg:w-2/5"
              : "w-full"
          }`}
        >
          <ChatPanel
            messages={state.messages}
            onSendMessage={handleSendMessage}
            isLoading={state.isLoading}
            currentTool={state.currentTool}
            streamingContent={state.streamingContent}
          />
        </div>

        {/* A2UI Panel - Right Side */}
        {showA2UIPanel && (
          <div
            className={`flex-1 overflow-hidden transition-all duration-300 ${
              hasA2UIContent ? "block" : "hidden md:block"
            }`}
          >
            <div className="h-full overflow-y-auto bg-gray-50 dark:bg-slate-800/50">
              {hasA2UIContent ? (
                <div className="p-4 space-y-4">
                  <A2UIRenderer state={state.a2uiState} />
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center px-8 py-12">
                    <div className="w-20 h-20 mx-auto mb-6 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                      <svg
                        className="w-10 h-10 text-blue-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Insights Panel
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs mx-auto">
                      Ask about a location to see rental forecasts, market
                      analysis, and visualizations appear here.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="flex-shrink-0 bg-white/50 dark:bg-slate-800/50 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-screen-2xl mx-auto px-4 py-2">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span>JARZ Rental Valuation - RealTech Hackathon 2026</span>
            <div className="flex items-center gap-3">
              <span>Powered by OpenRouter LLM</span>
              <span className="hidden sm:inline">|</span>
              <span className="hidden sm:inline">A2UI Generative Interface</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
