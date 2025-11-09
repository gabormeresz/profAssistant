import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { logger } from "../utils/logger";
import {
  fetchConversation,
  fetchConversationHistory
} from "../services/conversationService";
import type { ConversationMessage, StreamingState } from "../types";
import type { SidebarRef } from "../components";

export interface UseConversationManagerConfig<TResult, TConversation> {
  /**
   * The route path for this generator (e.g., "/outline-generator")
   */
  routePath: string;

  /**
   * The thread ID from URL params
   */
  urlThreadId: string | undefined;

  /**
   * Current thread ID from SSE hook
   */
  threadId: string | null;

  /**
   * Set thread ID function from SSE hook
   */
  setThreadId: (id: string | null) => void;

  /**
   * The completed result from SSE hook
   */
  result: TResult | null;

  /**
   * Streaming state from SSE hook
   */
  streamingState: StreamingState;

  /**
   * Clear data function from SSE hook
   */
  clearData: () => void;

  /**
   * Type guard to check if conversation metadata matches expected type
   */
  isCorrectType: (conversation: unknown) => conversation is TConversation;

  /**
   * Restore form state from loaded conversation
   */
  restoreFormState: (conversation: TConversation) => void;

  /**
   * Parse assistant message content to result object
   */
  parseResult: (content: string) => TResult;
}

export interface UseConversationManagerReturn<TResult> {
  /**
   * Whether the conversation has started
   */
  hasStarted: boolean;

  /**
   * Set whether the conversation has started
   */
  setHasStarted: (value: boolean) => void;

  /**
   * List of user messages in the conversation
   */
  userMessages: ConversationMessage[];

  /**
   * Set user messages
   */
  setUserMessages: React.Dispatch<React.SetStateAction<ConversationMessage[]>>;

  /**
   * History of generated results
   */
  resultHistory: TResult[];

  /**
   * Set result history
   */
  setResultHistory: React.Dispatch<React.SetStateAction<TResult[]>>;

  /**
   * Reference to sidebar for refetching
   */
  sidebarRef: React.MutableRefObject<SidebarRef | null>;
}

/**
 * Generic hook for managing conversation state and URL synchronization.
 *
 * This hook handles common patterns across generator pages:
 * - URL synchronization with thread ID
 * - Loading conversations from URL
 * - Parsing message history
 * - Auto-adding completed results to history
 * - Form state restoration
 *
 * @template TResult - The type of generated result (CourseOutline, LessonPlan, etc.)
 * @template TConversation - The type of conversation metadata
 */
export function useConversationManager<TResult, TConversation>(
  config: UseConversationManagerConfig<TResult, TConversation>
): UseConversationManagerReturn<TResult> {
  const {
    routePath,
    urlThreadId,
    threadId,
    setThreadId,
    result,
    streamingState,
    clearData,
    isCorrectType,
    restoreFormState,
    parseResult
  } = config;

  const navigate = useNavigate();

  // State
  const [hasStarted, setHasStarted] = useState(false);
  const [userMessages, setUserMessages] = useState<ConversationMessage[]>([]);
  const [resultHistory, setResultHistory] = useState<TResult[]>([]);

  // Refs
  const sidebarRef = useRef<SidebarRef | null>(null);
  const loadedThreadIdRef = useRef<string | null>(null);
  const isLoadingFromUrlRef = useRef(false);

  // Update URL when thread ID changes (from SSE)
  useEffect(() => {
    const shouldUpdateUrl =
      threadId && !urlThreadId && !isLoadingFromUrlRef.current;

    if (shouldUpdateUrl) {
      navigate(`${routePath}/${threadId}`, { replace: true });
      // Trigger sidebar refetch when a new conversation is created
      sidebarRef.current?.refetchConversations();
    }
  }, [threadId, urlThreadId, navigate, routePath]);

  // Load conversation from URL
  useEffect(() => {
    const loadConversation = async () => {
      // Exit early if no thread ID or already loaded
      if (!urlThreadId || loadedThreadIdRef.current === urlThreadId) {
        if (!urlThreadId) loadedThreadIdRef.current = null;
        return;
      }

      // Mark as loaded and prevent URL updates during load
      loadedThreadIdRef.current = urlThreadId;
      isLoadingFromUrlRef.current = true;

      // Clear previous data
      setUserMessages([]);
      setResultHistory([]);

      try {
        // Fetch metadata and history
        const [conversation, history] = await Promise.all([
          fetchConversation(urlThreadId),
          fetchConversationHistory(urlThreadId)
        ]);

        // Set thread ID for continuation
        setThreadId(urlThreadId);

        // Restore form state if correct type
        if (isCorrectType(conversation)) {
          restoreFormState(conversation);
        }
        setHasStarted(true);

        // Parse message history
        const userMsgs: ConversationMessage[] = [];
        const results: TResult[] = [];

        history.messages.forEach((msg) => {
          if (msg.role === "user") {
            userMsgs.push({
              id: `user-${crypto.randomUUID()}`,
              role: "user",
              content: msg.content,
              timestamp: new Date()
            });
          } else if (msg.role === "assistant") {
            try {
              results.push(parseResult(msg.content));
            } catch (e) {
              logger.error("Failed to parse result:", e);
            }
          }
        });

        // Update state
        setUserMessages(userMsgs);
        setResultHistory(results);
      } catch (error) {
        logger.error("Failed to load conversation:", error);
        navigate(routePath, { replace: true });
      } finally {
        // Reset loading flag after render cycle
        setTimeout(() => {
          isLoadingFromUrlRef.current = false;
        }, 0);
      }
    };

    loadConversation();
  }, [
    urlThreadId,
    setThreadId,
    navigate,
    routePath,
    isCorrectType,
    restoreFormState,
    parseResult
  ]);

  // Auto-add completed results to history
  useEffect(() => {
    if (!result || streamingState !== "complete") return;

    setResultHistory((prev) => {
      const isDuplicate = prev.some(
        (item) => JSON.stringify(item) === JSON.stringify(result)
      );
      if (isDuplicate) return prev;
      return [...prev, result];
    });

    const timeoutId = setTimeout(() => clearData(), 100);
    return () => clearTimeout(timeoutId);
  }, [result, streamingState, clearData]);

  return {
    hasStarted,
    setHasStarted,
    userMessages,
    setUserMessages,
    resultHistory,
    setResultHistory,
    sidebarRef
  };
}
