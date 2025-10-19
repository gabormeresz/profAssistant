import { useState, useCallback, useRef, useEffect } from "react";

export interface LessonPlanRequest {
  message: string;
  topic: string;
  number_of_classes: number;
  thread_id?: string; // Optional thread_id for conversation continuity
  files?: File[]; // Optional files to upload
}

export type StreamingState = "idle" | "connecting" | "streaming" | "complete";

interface UseWebSocketReturn {
  currentMessage: string;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendMessage: (data: LessonPlanRequest) => void;
  clearMessage: () => void;
  resetThread: () => void;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [currentMessage, setCurrentMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingState, setStreamingState] = useState<StreamingState>("idle");
  const [threadId, setThreadId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

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
    async (data: LessonPlanRequest) => {
      // Clear previous message and start loading
      setCurrentMessage("");
      setLoading(true);
      setStreamingState("connecting"); // Stage 1: Waiting for connection and model to start

      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
      }

      try {
        // If files are present, upload them first
        let fileContents: Array<{ filename: string; content: string }> = [];
        if (data.files && data.files.length > 0) {
          const formData = new FormData();
          data.files.forEach((file) => {
            formData.append("files", file);
          });

          // Upload files to backend
          const uploadResponse = await fetch("http://localhost:8000/upload", {
            method: "POST",
            body: formData
          });

          if (!uploadResponse.ok) {
            throw new Error("File upload failed");
          }

          const uploadResult = await uploadResponse.json();
          fileContents = uploadResult.files || [];
        }

        // Create new WebSocket connection
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("WebSocket connection established");
          // Include thread_id and file contents in the request
          const requestData = {
            message: data.message,
            topic: data.topic,
            number_of_classes: data.number_of_classes,
            thread_id: threadId || undefined,
            file_contents: fileContents.length > 0 ? fileContents : undefined
          };
          ws.send(JSON.stringify(requestData));
        };

        ws.onmessage = (event) => {
          const message = event.data;

          // Check if this is a thread_id message
          if (message.startsWith("__THREAD_ID__:")) {
            const extractedThreadId = message
              .replace("__THREAD_ID__:", "")
              .trim();
            setThreadId(extractedThreadId);
            console.log("Thread ID set:", extractedThreadId);
          } else {
            // Regular content message - Stage 2: Streaming
            setStreamingState("streaming");
            setCurrentMessage((prev) => prev + message);
            setLoading(false); // Stop loading as soon as first chunk arrives
          }
        };

        ws.onclose = () => {
          console.log("WebSocket connection closed");
          setLoading(false);
          setStreamingState("complete"); // Stage 3: Streaming complete
          wsRef.current = null;
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          setLoading(false);
          setStreamingState("idle");
          wsRef.current = null;
        };
      } catch (error) {
        console.error("Error processing request:", error);
        setLoading(false);
        setStreamingState("idle");
        setCurrentMessage("Error: Failed to process files");
      }
    },
    [url, threadId]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
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
