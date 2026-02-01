"use client";

import { useState, useCallback, useRef } from "react";
import type { Message } from "@/components/ChatMessage";
import type { A2UIMessage, A2UIComponent, StreamState } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChatHistory {
  role: string;
  content: string | null;
  tool_calls?: unknown[];
  tool_call_id?: string;
  name?: string;
}

interface CurrentTool {
  name: string;
  isRunning: boolean;
}

interface ChatStreamState {
  messages: Message[];
  a2uiState: StreamState;
  isLoading: boolean;
  error: string | null;
  currentTool: CurrentTool | null;
  streamingContent: string;
}

interface UseChatStreamResult {
  state: ChatStreamState;
  sendMessage: (message: string) => void;
  reset: () => void;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function useChatStream(): UseChatStreamResult {
  const [state, setState] = useState<ChatStreamState>({
    messages: [],
    a2uiState: {
      components: new Map(),
      dataModel: {},
      rootId: null,
      isReady: false,
      isLoading: false,
      error: null,
    },
    isLoading: false,
    error: null,
    currentTool: null,
    streamingContent: "",
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const historyRef = useRef<ChatHistory[]>([]);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    historyRef.current = [];
    setState({
      messages: [],
      a2uiState: {
        components: new Map(),
        dataModel: {},
        rootId: null,
        isReady: false,
        isLoading: false,
        error: null,
      },
      isLoading: false,
      error: null,
      currentTool: null,
      streamingContent: "",
    });
  }, []);

  const processA2UIMessage = useCallback((message: A2UIMessage) => {
    setState((prev) => {
      const newA2UIState = { ...prev.a2uiState };

      if ("surfaceUpdate" in message) {
        const newComponents = new Map(prev.a2uiState.components);
        for (const comp of message.surfaceUpdate.components) {
          newComponents.set(comp.id, comp);
        }
        newA2UIState.components = newComponents;
      }

      if ("dataModelUpdate" in message) {
        const update = message.dataModelUpdate;
        const newDataModel = { ...prev.a2uiState.dataModel };

        if (update.path) {
          const pathParts = update.path.split("/").filter(Boolean);
          let current: Record<string, unknown> = newDataModel;

          for (let i = 0; i < pathParts.length - 1; i++) {
            if (!current[pathParts[i]]) {
              current[pathParts[i]] = {};
            }
            current = current[pathParts[i]] as Record<string, unknown>;
          }

          const lastKey = pathParts[pathParts.length - 1];
          if (!current[lastKey]) {
            current[lastKey] = {};
          }

          for (const entry of update.contents) {
            const value =
              entry.valueString ??
              entry.valueNumber ??
              entry.valueBoolean ??
              entry.valueArray ??
              entry.valueMap;
            (current[lastKey] as Record<string, unknown>)[entry.key] = value;
          }
        } else {
          for (const entry of update.contents) {
            const value =
              entry.valueString ??
              entry.valueNumber ??
              entry.valueBoolean ??
              entry.valueArray ??
              entry.valueMap;
            newDataModel[entry.key] = value;
          }
        }

        newA2UIState.dataModel = newDataModel;
      }

      if ("beginRendering" in message) {
        newA2UIState.rootId = message.beginRendering.root;
        newA2UIState.isReady = true;
      }

      return {
        ...prev,
        a2uiState: newA2UIState,
      };
    });
  }, []);

  const sendMessage = useCallback(
    (messageContent: string) => {
      // Add user message
      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content: messageContent,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
        error: null,
        streamingContent: "",
        currentTool: null,
        // Clear A2UI data model for new query (but keep UI showing until new results come in)
        a2uiState: {
          ...prev.a2uiState,
          dataModel: {}, // Clear previous tool data
        },
      }));

      // Add to history
      historyRef.current.push({
        role: "user",
        content: messageContent,
      });

      // Abort any existing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      // Make streaming request
      fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          message: messageContent,
          history: historyRef.current.slice(0, -1), // Exclude current message
        }),
        signal: controller.signal,
      })
        .then(async (response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          if (!reader) {
            throw new Error("No response body");
          }

          const decoder = new TextDecoder();
          let buffer = "";
          let accumulatedContent = "";
          let hasReceivedA2UI = false;

          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              // Finalize the message
              if (accumulatedContent) {
                const assistantMessage: Message = {
                  id: generateId(),
                  role: "assistant",
                  content: accumulatedContent,
                  timestamp: new Date(),
                };

                // Add to history
                historyRef.current.push({
                  role: "assistant",
                  content: accumulatedContent,
                });

                setState((prev) => ({
                  ...prev,
                  messages: [...prev.messages, assistantMessage],
                  isLoading: false,
                  streamingContent: "",
                  currentTool: null,
                }));
              } else {
                setState((prev) => ({
                  ...prev,
                  isLoading: false,
                  streamingContent: "",
                  currentTool: null,
                }));
              }
              break;
            }

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE events
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            let currentEvent = "";
            for (const line of lines) {
              if (line.startsWith("event: ")) {
                currentEvent = line.slice(7).trim();
                continue;
              }

              if (line.startsWith("data: ")) {
                const jsonStr = line.slice(6).trim();
                try {
                  const data = JSON.parse(jsonStr);

                  // Handle different event types based on event name
                  if (currentEvent === "text" && data.content !== undefined) {
                    // Text content
                    accumulatedContent += data.content;
                    setState((prev) => ({
                      ...prev,
                      streamingContent: accumulatedContent,
                    }));
                  } else if (currentEvent === "tool_start" && data.tool !== undefined) {
                    // Tool start
                    setState((prev) => ({
                      ...prev,
                      currentTool: { name: data.tool, isRunning: true },
                    }));
                  } else if (currentEvent === "tool_end" && data.tool !== undefined) {
                    // Tool end
                    setState((prev) => ({
                      ...prev,
                      currentTool: { name: data.tool, isRunning: false },
                    }));
                  } else if (currentEvent === "a2ui") {
                    // A2UI message
                    hasReceivedA2UI = true;
                    processA2UIMessage(data);
                  } else if (currentEvent === "error" && data.error) {
                    // Error
                    setState((prev) => ({
                      ...prev,
                      error: data.error,
                      isLoading: false,
                    }));
                  } else if (currentEvent === "complete") {
                    // Complete
                    setState((prev) => ({
                      ...prev,
                      isLoading: false,
                      currentTool: null,
                    }));
                  } else if (currentEvent === "status") {
                    // Status update - can add visual feedback here if needed
                    console.log("Agent status:", data);
                  }

                  currentEvent = "";
                } catch (e) {
                  console.error("Failed to parse SSE data:", e, "Line:", jsonStr);
                }
              }
            }
          }
        })
        .catch((error) => {
          if (error.name !== "AbortError") {
            console.error("Chat stream error:", error);
            setState((prev) => ({
              ...prev,
              isLoading: false,
              error: error.message,
              currentTool: null,
            }));
          }
        });
    },
    [processA2UIMessage]
  );

  return {
    state,
    sendMessage,
    reset,
  };
}
