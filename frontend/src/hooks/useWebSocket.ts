import { useState, useCallback, useRef, useEffect } from "react";

export interface LessonPlanRequest {
  message: string;
  topic: string;
  number_of_classes: number;
  thread_id?: string; // Optional thread_id for conversation continuity
}

interface UseWebSocketReturn {
  currentMessage: string;
  loading: boolean;
  threadId: string | null;
  sendMessage: (data: LessonPlanRequest) => void;
  clearMessage: () => void;
  resetThread: () => void;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [currentMessage, setCurrentMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const clearMessage = useCallback(() => {
    setCurrentMessage("");
  }, []);

  const resetThread = useCallback(() => {
    setThreadId(null);
    setCurrentMessage("");
  }, []);

  const sendMessage = useCallback(
    (data: LessonPlanRequest) => {
      // Clear previous message and start loading
      setCurrentMessage("");
      setLoading(true);

      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
      }

      // Create new WebSocket connection
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connection established");
        // Include thread_id in the request if available
        const requestData = {
          ...data,
          thread_id: threadId || undefined
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
          // Regular content message
          setCurrentMessage((prev) => prev + message);
          setLoading(false); // Stop loading as soon as first chunk arrives
        }
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed");
        setLoading(false);
        wsRef.current = null;
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setLoading(false);
        wsRef.current = null;
      };
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
    threadId,
    sendMessage,
    clearMessage,
    resetThread
  };
};
