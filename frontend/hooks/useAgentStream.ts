"use client";

import { useState, useCallback, useRef } from "react";
import type {
  UserQuery,
  A2UIMessage,
  A2UIComponent,
  StreamState,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UseAgentStreamResult {
  state: StreamState;
  startStream: (query: UserQuery) => void;
  reset: () => void;
}

export function useAgentStream(): UseAgentStreamResult {
  const [state, setState] = useState<StreamState>({
    components: new Map(),
    dataModel: {},
    rootId: null,
    isReady: false,
    isLoading: false,
    error: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setState({
      components: new Map(),
      dataModel: {},
      rootId: null,
      isReady: false,
      isLoading: false,
      error: null,
    });
  }, []);

  const processMessage = useCallback((message: A2UIMessage) => {
    setState((prev) => {
      const newState = { ...prev };

      if ("surfaceUpdate" in message) {
        // Add/update components
        const newComponents = new Map(prev.components);
        for (const comp of message.surfaceUpdate.components) {
          newComponents.set(comp.id, comp);
        }
        newState.components = newComponents;
      }

      if ("dataModelUpdate" in message) {
        // Update data model
        const update = message.dataModelUpdate;
        const newDataModel = { ...prev.dataModel };

        // Handle path-based updates
        if (update.path) {
          const pathParts = update.path.split("/").filter(Boolean);
          let current: Record<string, unknown> = newDataModel;

          // Navigate to parent
          for (let i = 0; i < pathParts.length - 1; i++) {
            if (!current[pathParts[i]]) {
              current[pathParts[i]] = {};
            }
            current = current[pathParts[i]] as Record<string, unknown>;
          }

          // Set the value at the final path
          const lastKey = pathParts[pathParts.length - 1];
          if (!current[lastKey]) {
            current[lastKey] = {};
          }

          // Process contents
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
          // Root-level update
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

        newState.dataModel = newDataModel;
      }

      if ("beginRendering" in message) {
        newState.rootId = message.beginRendering.root;
        newState.isReady = true;
      }

      return newState;
    });
  }, []);

  const startStream = useCallback(
    (query: UserQuery) => {
      // Reset state
      reset();

      setState((prev) => ({ ...prev, isLoading: true }));

      // Create POST request for SSE
      // Note: EventSource doesn't support POST, so we use fetch with ReadableStream
      const controller = new AbortController();

      fetch(`${API_URL}/api/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ query }),
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

          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              setState((prev) => ({ ...prev, isLoading: false }));
              break;
            }

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE events
            const lines = buffer.split("\n");
            buffer = lines.pop() || ""; // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const jsonStr = line.slice(6);
                try {
                  const data = JSON.parse(jsonStr);
                  processMessage(data);
                } catch (e) {
                  console.error("Failed to parse SSE data:", e);
                }
              } else if (line.startsWith("event: error")) {
                // Next line will be the error data
              } else if (line.startsWith("event: complete")) {
                setState((prev) => ({ ...prev, isLoading: false }));
              }
            }
          }
        })
        .catch((error) => {
          if (error.name !== "AbortError") {
            console.error("Stream error:", error);
            setState((prev) => ({
              ...prev,
              isLoading: false,
              error: error.message,
            }));
          }
        });

      // Store controller for cleanup
      eventSourceRef.current = {
        close: () => controller.abort(),
      } as EventSource;
    },
    [reset, processMessage]
  );

  return {
    state,
    startStream,
    reset,
  };
}

// Helper to resolve data bindings
export function resolveBoundValue(
  boundValue: Record<string, unknown>,
  dataModel: Record<string, unknown>
): unknown {
  if (boundValue.literalString !== undefined) return boundValue.literalString;
  if (boundValue.literalNumber !== undefined) return boundValue.literalNumber;
  if (boundValue.literalBoolean !== undefined) return boundValue.literalBoolean;

  if (boundValue.path && typeof boundValue.path === "string") {
    const pathParts = boundValue.path.split("/").filter(Boolean);
    let current: unknown = dataModel;

    for (const part of pathParts) {
      if (current && typeof current === "object" && part in current) {
        current = (current as Record<string, unknown>)[part];
      } else {
        return undefined;
      }
    }

    return current;
  }

  return undefined;
}
