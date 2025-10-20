import { useState, useCallback, useRef, useEffect } from "react";

export interface LessonPlanRequest {
  message: string;
  topic: string;
  number_of_classes: number;
  thread_id?: string;
  files?: File[];
}

export type StreamingState = "idle" | "connecting" | "streaming" | "complete";

interface UseSSEReturn {
  currentMessage: string;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendMessage: (data: LessonPlanRequest) => Promise<string>; // Returns the complete message
  clearMessage: () => void;
  resetThread: () => void;
}

export const useSSE = (url: string): UseSSEReturn => {
  const [currentMessage, setCurrentMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingState, setStreamingState] = useState<StreamingState>("idle");
  const [threadId, setThreadId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const clearMessage = useCallback(() => {
    setCurrentMessage("");
    setStreamingState("idle");
  }, []);

  const resetThread = useCallback(() => {
    setThreadId(null);
    setCurrentMessage("");
    setStreamingState("idle");
  }, []);

  const sendMessage = useCallback(
    async (data: LessonPlanRequest): Promise<string> => {
      // Clear previous message and start loading
      setCurrentMessage("");
      setLoading(true);
      setStreamingState("connecting");

      // Cancel previous request if any
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      let completeMessage = "";

      try {
        // Prepare form data
        const formData = new FormData();
        formData.append("message", data.message);
        formData.append("topic", data.topic);
        formData.append("number_of_classes", data.number_of_classes.toString());

        if (threadId) {
          formData.append("thread_id", threadId);
        }

        // Add files if present
        if (data.files && data.files.length > 0) {
          data.files.forEach((file) => {
            formData.append("files", file);
          });
        }

        // Make SSE request
        const response = await fetch(url, {
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
        let currentEvent = ""; // Track current SSE event type

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            setStreamingState("complete");
            setLoading(false);
            return completeMessage;
          }

          // Decode the chunk
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            // Check for SSE event type
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim(); // Extract event type
            } else if (line.startsWith("data: ")) {
              const jsonData = line.slice(6); // Remove "data: " prefix

              try {
                const parsed = JSON.parse(jsonData);

                // Handle thread_id event separately
                if (currentEvent === "thread_id" && parsed.thread_id) {
                  setThreadId(parsed.thread_id);
                  console.log("Thread ID set:", parsed.thread_id);
                  currentEvent = ""; // Reset event type
                } else if (parsed.content) {
                  // Regular content message - start streaming
                  if (streamingState !== "streaming") {
                    setStreamingState("streaming");
                  }
                  completeMessage += parsed.content;
                  setCurrentMessage((prev) => prev + parsed.content);
                  setLoading(false);
                  currentEvent = ""; // Reset event type
                } else if (parsed.error) {
                  console.error("Stream error:", parsed.error);
                  setCurrentMessage(`Error: ${parsed.error}`);
                  setStreamingState("idle");
                  setLoading(false);
                  currentEvent = ""; // Reset event type
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", e);
              }
            } else if (line === "") {
              // Empty line resets the event type (SSE specification)
              currentEvent = "";
            }
          }
        }
      } catch (error) {
        if (error instanceof Error) {
          if (error.name === "AbortError") {
            console.log("Request aborted");
          } else {
            console.error("Error processing request:", error);
            setCurrentMessage(`Error: ${error.message}`);
          }
        } else {
          console.error("Unknown error:", error);
          setCurrentMessage("Error: An unknown error occurred");
        }
        setLoading(false);
        setStreamingState("idle");
        return ""; // Return empty string on error
      } finally {
        abortControllerRef.current = null;
      }
    },
    [url, threadId, streamingState]
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
    currentMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    clearMessage,
    resetThread
  };
};
