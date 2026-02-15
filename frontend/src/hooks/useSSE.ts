import { useState, useCallback, useRef, useEffect } from "react";
import { logger } from "../utils/logger";
import { authFetch } from "../services/authService";
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
  error: string | null;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendRequest: (
    endpoint: string,
    formData: FormData,
    handlers?: SSEEventHandlers<T>
  ) => Promise<T | null>;
  resetThread: () => void;
  setThreadId: (id: string | null) => void;
  clearError: () => void;
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
 *   await sendRequest(API_ENDPOINTS.COURSE_OUTLINE_GENERATOR, formData);
 * };
 * ```
 */
export const useSSE = <T>(): UseSSEReturn<T> => {
  const [data, setData] = useState<T | null>(null);
  const [progressMessage, setProgressMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [streamingState, setStreamingState] = useState<StreamingState>("idle");
  const [threadId, setThreadId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearData = useCallback(() => {
    setData(null);
    setProgressMessage("");
    setError(null);
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
      setError(null);
      setProgressMessage("overlay.initializing");
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
        // Make SSE request via shared authFetch (handles 401 retry)
        const response = await authFetch(endpoint, {
          method: "POST",
          body: formData,
          signal: abortController.signal
        });

        if (!response.ok) {
          // Try to parse a JSON error body (FastAPI returns {"detail": "..."})
          let errorDetail = `HTTP error! status: ${response.status}`;
          try {
            const body = await response.json();
            if (body.detail) {
              errorDetail = body.detail;
            }
          } catch {
            // Response body wasn't JSON — keep the generic message
          }
          throw new Error(errorDetail);
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
            // Safety net: if the stream ends without a "complete" event, still transition
            setStreamingState((current) =>
              current === "streaming" ? "complete" : current
            );
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
                } else if (currentEvent === "progress") {
                  // Handle both old format (message) and new format (message_key)
                  const messageKey = parsed.message_key || parsed.message;
                  if (messageKey) {
                    // Store the translation key and params for the component to translate
                    const progressData = parsed.params
                      ? JSON.stringify({
                          key: messageKey,
                          params: parsed.params
                        })
                      : messageKey;
                    setProgressMessage(progressData);
                    setLoading(false);
                    handlers?.onProgress?.(progressData);
                  }
                } else if (currentEvent === "complete" && parsed) {
                  const completedData = parsed as T;
                  setData(completedData);
                  setStreamingState("complete");
                  finalData = completedData;
                  setProgressMessage("overlay.complete");
                  handlers?.onComplete?.(completedData);
                } else if (
                  currentEvent === "error" &&
                  (parsed.message_key || parsed.message)
                ) {
                  logger.error(
                    "Stream error:",
                    parsed.message_key || parsed.message
                  );
                  const errorMsg = parsed.message_key || parsed.message;
                  setError(errorMsg);
                  setProgressMessage("");
                  setStreamingState("idle");
                  setLoading(false);
                  handlers?.onError?.(errorMsg);
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
            setError(error.message);
            setProgressMessage("");
            handlers?.onError?.(error.message);
          }
        } else {
          logger.error("Unknown error:", error);
          setError("An unknown error occurred");
          setProgressMessage("");
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
    error,
    loading,
    streamingState,
    threadId,
    sendRequest,
    resetThread,
    setThreadId,
    clearError
  };
};
