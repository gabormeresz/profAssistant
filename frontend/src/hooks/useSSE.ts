import { useState, useCallback, useRef, useEffect } from "react";
import { logger } from "../utils/logger";
import type { StreamingState } from "../types";

/**
 * Generic SSE event handler
 */
export interface SSEEventHandlers<T> {
  onThreadId?: (threadId: string) => void;
  onProgress?: (message: string) => void;
  onComplete?: (data: T) => void;
  onError?: (message: string) => void;
}

/**
 * Generic SSE hook return type
 */
export interface UseSSEReturn<T> {
  data: T | null;
  progressMessage: string;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendRequest: (
    endpoint: string,
    formData: FormData,
    handlers?: SSEEventHandlers<T>
  ) => Promise<T | null>;
  clearData: () => void;
  resetThread: () => void;
  setThreadId: (id: string | null) => void;
}

/**
 * Generic SSE hook for handling Server-Sent Events
 *
 * This hook provides a reusable implementation for SSE connections with:
 * - Automatic connection management
 * - Progress tracking
 * - Thread ID management
 * - Graceful error handling
 * - Request cancellation
 *
 * @template T - The type of data expected from the complete event
 *
 * @example
 * ```typescript
 * const { data, progressMessage, loading, sendRequest } = useSSE<CourseOutline>();
 *
 * const handleSubmit = async () => {
 *   const formData = new FormData();
 *   formData.append("message", message);
 *
 *   await sendRequest(API_ENDPOINTS.OUTLINE_GENERATOR, formData);
 * };
 * ```
 */
export const useSSE = <T>(): UseSSEReturn<T> => {
  const [data, setData] = useState<T | null>(null);
  const [progressMessage, setProgressMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingState, setStreamingState] = useState<StreamingState>("idle");
  const [threadId, setThreadId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const clearData = useCallback(() => {
    setData(null);
    setProgressMessage("");
    setStreamingState("idle");
  }, []);

  const resetThread = useCallback(() => {
    setThreadId(null);
    clearData();
  }, [clearData]);

  const sendRequest = useCallback(
    async (
      endpoint: string,
      formData: FormData,
      handlers?: SSEEventHandlers<T>
    ): Promise<T | null> => {
      // Clear previous data and start loading
      setData(null);
      setProgressMessage("Initializing...");
      setLoading(true);
      setStreamingState("connecting");

      // Cancel previous request if any
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Add thread_id to formData if it exists
      if (threadId && !formData.has("thread_id")) {
        formData.append("thread_id", threadId);
      }

      let finalData: T | null = null;

      try {
        // Make SSE request
        const response = await fetch(endpoint, {
          method: "POST",
          body: formData,
          signal: abortController.signal
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
          throw new Error("Response body is null");
        }

        // Read the stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = "";
        let currentEvent = "";

        setStreamingState("streaming");

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            setStreamingState("complete");
            setLoading(false);
            return finalData;
          }

          // Decode the chunk
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            // Check for SSE event type
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const jsonData = line.slice(6);

              try {
                const parsed = JSON.parse(jsonData);

                // Handle different event types
                if (currentEvent === "thread_id" && parsed.thread_id) {
                  setThreadId(parsed.thread_id);
                  logger.debug("Thread ID set:", parsed.thread_id);
                  handlers?.onThreadId?.(parsed.thread_id);
                } else if (currentEvent === "progress" && parsed.message) {
                  setProgressMessage(parsed.message);
                  setLoading(false); // Not loading, but actively processing
                  handlers?.onProgress?.(parsed.message);
                } else if (currentEvent === "complete" && parsed) {
                  // Structured data received
                  const completedData = parsed as T;
                  setData(completedData);
                  finalData = completedData;
                  setProgressMessage("Complete!");
                  handlers?.onComplete?.(completedData);
                } else if (currentEvent === "error" && parsed.message) {
                  logger.error("Stream error:", parsed.message);
                  setProgressMessage(`Error: ${parsed.message}`);
                  setStreamingState("idle");
                  setLoading(false);
                  handlers?.onError?.(parsed.message);
                }
              } catch (e) {
                logger.error("Failed to parse SSE data:", e);
              }

              currentEvent = ""; // Reset after processing
            } else if (line === "") {
              currentEvent = "";
            }
          }
        }
      } catch (error) {
        if (error instanceof Error) {
          if (error.name === "AbortError") {
            logger.debug("Request aborted");
            // Don't set error state for aborted requests
            return null;
          } else {
            logger.error("Error processing request:", error);
            setProgressMessage(`Error: ${error.message}`);
            handlers?.onError?.(error.message);
          }
        } else {
          logger.error("Unknown error:", error);
          setProgressMessage("Error: An unknown error occurred");
          handlers?.onError?.("An unknown error occurred");
        }
        setLoading(false);
        setStreamingState("idle");
        return null;
      } finally {
        if (abortControllerRef.current) {
          abortControllerRef.current = null;
        }
      }
    },
    [threadId]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    data,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendRequest,
    clearData,
    resetThread,
    setThreadId
  };
};
