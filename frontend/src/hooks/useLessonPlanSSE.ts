import { useState, useCallback, useRef, useEffect } from "react";
import { API_ENDPOINTS } from "../utils/constants";
import type { LessonPlanRequest, StreamingState, LessonPlan } from "../types";

interface UseLessonPlanSSEReturn {
  lessonPlan: LessonPlan | null;
  progressMessage: string;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendMessage: (data: LessonPlanRequest) => Promise<LessonPlan | null>;
  clearData: () => void;
  resetThread: () => void;
  setThreadId: (id: string | null) => void;
}

export const useLessonPlanSSE = (): UseLessonPlanSSEReturn => {
  const [lessonPlan, setLessonPlan] = useState<LessonPlan | null>(null);
  const [progressMessage, setProgressMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingState, setStreamingState] = useState<StreamingState>("idle");
  const [threadId, setThreadId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const clearData = useCallback(() => {
    setLessonPlan(null);
    setProgressMessage("");
    setStreamingState("idle");
  }, []);

  const resetThread = useCallback(() => {
    setThreadId(null);
    clearData();
  }, [clearData]);

  const sendMessage = useCallback(
    async (data: LessonPlanRequest): Promise<LessonPlan | null> => {
      // Clear previous data and start loading
      setLessonPlan(null);
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

      let finalPlan: LessonPlan | null = null;

      try {
        // Prepare form data
        const formData = new FormData();
        formData.append("message", data.message);
        formData.append("course_title", data.course_title);
        formData.append("class_number", data.class_number.toString());
        formData.append("class_title", data.class_title);
        formData.append(
          "learning_objectives",
          JSON.stringify(data.learning_objectives)
        );
        formData.append("key_topics", JSON.stringify(data.key_topics));
        formData.append(
          "activities_projects",
          JSON.stringify(data.activities_projects)
        );

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
        const response = await fetch(API_ENDPOINTS.LESSON_PLANNER, {
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
            return finalPlan;
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
                  console.log("Thread ID set:", parsed.thread_id);
                } else if (currentEvent === "progress" && parsed.message) {
                  setProgressMessage(parsed.message);
                  setLoading(false); // Not loading, but actively processing
                } else if (currentEvent === "complete" && parsed) {
                  // Structured data received
                  const plan = parsed as LessonPlan;
                  setLessonPlan(plan);
                  finalPlan = plan;
                  setProgressMessage("Lesson plan complete!");
                } else if (currentEvent === "error" && parsed.message) {
                  console.error("Stream error:", parsed.message);
                  setProgressMessage(`Error: ${parsed.message}`);
                  setStreamingState("idle");
                  setLoading(false);
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", e);
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
            console.log("Request aborted");
            // Don't set error state for aborted requests
            return null;
          } else {
            console.error("Error processing request:", error);
            setProgressMessage(`Error: ${error.message}`);
          }
        } else {
          console.error("Unknown error:", error);
          setProgressMessage("Error: An unknown error occurred");
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
    lessonPlan,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    clearData,
    resetThread,
    setThreadId
  };
};
