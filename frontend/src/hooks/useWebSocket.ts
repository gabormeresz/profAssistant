import { useState, useCallback, useRef, useEffect } from "react";

export interface LessonPlanRequest {
  message: string;
  topic: string;
  number_of_classes: number;
}

interface UseWebSocketReturn {
  currentMessage: string;
  loading: boolean;
  sendMessage: (data: LessonPlanRequest) => void;
  clearMessage: () => void;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [currentMessage, setCurrentMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const clearMessage = useCallback(() => {
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
        // Send structured JSON data
        ws.send(JSON.stringify(data));
      };

      ws.onmessage = (event) => {
        setCurrentMessage((prev) => prev + event.data);
        setLoading(false); // Stop loading as soon as first chunk arrives
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
    [url]
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
    sendMessage,
    clearMessage
  };
};
