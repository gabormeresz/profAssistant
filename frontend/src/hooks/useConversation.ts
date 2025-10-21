import { useState, useCallback } from "react";
import type { ConversationMessage } from "../types";

interface UseConversationReturn {
  messages: ConversationMessage[];
  hasStarted: boolean;
  addUserMessage: (
    content: string,
    files?: File[],
    metadata?: { topic?: string; numberOfClasses?: number }
  ) => void;
  addAssistantMessage: (content: string) => void;
  reset: () => void;
}

export function useConversation(): UseConversationReturn {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [hasStarted, setHasStarted] = useState(false);

  const addUserMessage = useCallback(
    (
      content: string,
      files?: File[],
      metadata?: { topic?: string; numberOfClasses?: number }
    ) => {
      const message: ConversationMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
        timestamp: new Date(),
        files: files?.map((f) => ({ name: f.name, size: f.size })),
        topic: metadata?.topic,
        numberOfClasses: metadata?.numberOfClasses
      };

      setMessages((prev) => [...prev, message]);
      setHasStarted(true);
    },
    []
  );

  const addAssistantMessage = useCallback((content: string) => {
    const message: ConversationMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, message]);
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setHasStarted(false);
  }, []);

  return {
    messages,
    hasStarted,
    addUserMessage,
    addAssistantMessage,
    reset
  };
}
