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
  conversationId: string | null;
}

export interface MarketDataRequestPayload {
  district?: string | null;
  postcode?: string | null;
}

interface UseChatStreamOptions {
  onMarketDataRequest?: (data: MarketDataRequestPayload) => void;
}

interface UseChatStreamResult {
  state: ChatStreamState;
  sendMessage: (message: string) => void;
  reset: () => void;
  loadConversation: (conversationId: string) => Promise<void>;
  applyA2UIMessages: (messages: A2UIMessage[]) => void;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/** Apply a single A2UI message to a state snapshot (pure). Used to replay saved UI when loading a conversation. */
function applyOneA2UIMessage(
  components: Map<string, import("@/lib/types").A2UIComponent>,
  dataModel: Record<string, unknown>,
  rootId: string | null,
  isReady: boolean,
  message: A2UIMessage
): { components: Map<string, import("@/lib/types").A2UIComponent>; dataModel: Record<string, unknown>; rootId: string | null; isReady: boolean } {
  const newComponents = new Map(components);
  let newDataModel = { ...dataModel };
  let newRootId = rootId;
  let newIsReady = isReady;

  if ("surfaceUpdate" in message) {
    for (const comp of message.surfaceUpdate.components) {
      newComponents.set(comp.id, comp);
    }
  }
  if ("dataModelUpdate" in message) {
    const update = message.dataModelUpdate;
    newDataModel = { ...dataModel };
    if (update.path) {
      const pathParts = update.path.split("/").filter(Boolean);
      let current: Record<string, unknown> = newDataModel;
      for (let i = 0; i < pathParts.length - 1; i++) {
        if (!current[pathParts[i]]) current[pathParts[i]] = {};
        current = current[pathParts[i]] as Record<string, unknown>;
      }
      const lastKey = pathParts[pathParts.length - 1];
      if (!current[lastKey]) current[lastKey] = {};
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
  }
  if ("beginRendering" in message) {
    newRootId = message.beginRendering.root;
    newIsReady = true;
  }
  return { components: newComponents, dataModel: newDataModel, rootId: newRootId, isReady: newIsReady };
}

export function useChatStream(options?: UseChatStreamOptions): UseChatStreamResult {
  const onMarketDataRequestRef = useRef(options?.onMarketDataRequest);
  onMarketDataRequestRef.current = options?.onMarketDataRequest;

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
    conversationId: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const historyRef = useRef<ChatHistory[]>([]);
  const conversationIdRef = useRef<string | null>(null);

  conversationIdRef.current = state.conversationId;

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    historyRef.current = [];
    conversationIdRef.current = null;
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
      conversationId: null,
    });
  }, []);

  const processA2UIMessage = useCallback((message: A2UIMessage) => {
    console.log("[processA2UIMessage] Processing message:", message);
    setState((prev) => {
      const newA2UIState = { ...prev.a2uiState };

      if ("surfaceUpdate" in message) {
        console.log("[processA2UIMessage] Surface update with", message.surfaceUpdate.components.length, "components");
        const newComponents = new Map(prev.a2uiState.components);
        for (const comp of message.surfaceUpdate.components) {
          newComponents.set(comp.id, comp);
        }
        newA2UIState.components = newComponents;
      }

      if ("dataModelUpdate" in message) {
        console.log("[processA2UIMessage] Data model update at path:", message.dataModelUpdate.path);
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
        console.log("[processA2UIMessage] Updated data model:", newA2UIState.dataModel);
      }

      if ("beginRendering" in message) {
        console.log("[processA2UIMessage] Begin rendering root:", message.beginRendering.root);
        newA2UIState.rootId = message.beginRendering.root;
        newA2UIState.isReady = true;
      }

      return {
        ...prev,
        a2uiState: newA2UIState,
      };
    });
  }, []);

  const loadConversation = useCallback(
    async (conversationId: string) => {
      try {
        const res = await fetch(`${API_URL}/api/conversations/${conversationId}`);
        if (!res.ok) throw new Error("Failed to load conversation");
        const conv = await res.json();
        const msgs = (conv.messages || []) as Array<{
          id: string;
          role: string;
          content: string;
          a2ui_snapshot?: A2UIMessage[];
          created_at?: string;
        }>;
        const messageList: Message[] = msgs
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => ({
            id: m.id || generateId(),
            role: m.role as "user" | "assistant" | "system",
            content: m.content || "",
            timestamp: m.created_at ? new Date(m.created_at) : undefined,
          }));
        historyRef.current = msgs.map((m) => ({
          role: m.role,
          content: m.content,
        }));
        // Apply A2UI from all assistant messages in order; compute final UI state in one go so it restores reliably
        const a2uiToApply: A2UIMessage[] = [];
        for (const m of msgs) {
          if (m.role === "assistant" && m.a2ui_snapshot?.length) {
            a2uiToApply.push(...m.a2ui_snapshot);
          }
        }
        let a2uiState: StreamState = state.a2uiState;
        if (a2uiToApply.length) {
          let components = new Map<string, import("@/lib/types").A2UIComponent>();
          let dataModel: Record<string, unknown> = {};
          let rootId: string | null = null;
          let isReady = false;
          for (const msg of a2uiToApply) {
            const next = applyOneA2UIMessage(components, dataModel, rootId, isReady, msg);
            components = next.components;
            dataModel = next.dataModel;
            rootId = next.rootId;
            isReady = next.isReady;
          }
          a2uiState = {
            components,
            dataModel,
            rootId,
            isReady,
            isLoading: false,
            error: null,
          };
        } else {
          a2uiState = {
            ...state.a2uiState,
            dataModel: {},
            rootId: null,
            isReady: false,
          };
        }
        setState((prev) => ({
          ...prev,
          messages: messageList,
          conversationId,
          error: null,
          streamingContent: "",
          currentTool: null,
          a2uiState,
        }));
      } catch (e) {
        console.error("Load conversation error:", e);
        setState((prev) => ({ ...prev, error: (e as Error).message }));
      }
    },
    []
  );

  const applyA2UIMessages = useCallback(
    (messages: A2UIMessage[]) => {
      for (const msg of messages) {
        processA2UIMessage(msg);
      }
    },
    [processA2UIMessage]
  );

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

      const conversationIdToSend = conversationIdRef.current ?? undefined;
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
          conversation_id: conversationIdToSend,
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
          // IMPORTANT: keep currentEvent across chunks; event/data lines can arrive in different reads
          let currentEvent = "";

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
            for (const line of lines) {
              // Normalize CRLF and blank separators
              const normalized = line.trimEnd();
              if (normalized.trim() === "") {
                // Blank line indicates end of one SSE event block
                currentEvent = "";
                continue;
              }

              // Comment/keepalive line (e.g. ": ping - ...")
              if (normalized.startsWith(":")) {
                continue;
              }

              if (normalized.startsWith("event: ")) {
                currentEvent = normalized.slice(7).trim();
                continue;
              }

              if (normalized.startsWith("data: ")) {
                const jsonStr = normalized.slice(6).trim();
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
                    console.log("[A2UI] Received message:", data);
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
                    // Complete; backend may send conversation_id for persistence
                    const cid = data.conversation_id ?? null;
                    setState((prev) => ({
                      ...prev,
                      isLoading: false,
                      currentTool: null,
                      ...(cid != null ? { conversationId: cid } : {}),
                    }));
                  } else if (currentEvent === "market_data_request") {
                    // Agent requested Market Data tab + load for district/postcode
                    const payload: MarketDataRequestPayload = {
                      district: data.district ?? undefined,
                      postcode: data.postcode ?? undefined,
                    };
                    onMarketDataRequestRef.current?.(payload);
                  } else if (currentEvent === "status") {
                    // Status update - can add visual feedback here if needed
                    console.log("Agent status:", data);
                  }
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
    loadConversation,
    applyA2UIMessages,
  };
}
