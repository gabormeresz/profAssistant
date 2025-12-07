import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { logger } from "../utils/logger";
import {
  fetchConversation,
  fetchConversationHistory
} from "../services/conversationService";
import type { ConversationMessage, StreamingState } from "../types";
import { useSavedConversationsContext } from "../contexts/SavedConversationsContext";

/**
 * Parse a user message to extract file contents section
 * Returns the user's actual message and any attached file information
 */
function parseUserMessage(content: string): {
  userContent: string;
  files: { name: string }[];
} {
  const files: { name: string }[] = [];
  let userContent = content;

  // Check if message contains file contents section
  const fileMarkerStart = "<<<REFERENCE_MATERIALS_BEGIN>>>";
  const fileMarkerEnd = "<<<REFERENCE_MATERIALS_END>>>";

  const startIdx = content.indexOf(fileMarkerStart);
  const endIdx = content.indexOf(fileMarkerEnd);

  if (startIdx !== -1 && endIdx !== -1) {
    // Extract the file contents section
    const fileSection = content.substring(
      startIdx + fileMarkerStart.length,
      endIdx
    );

    // Remove file section from user content
    userContent = content.substring(0, startIdx).trim();

    // Parse individual files from the section
    // Format: <<<FILE_BEGIN:filename>>>\ncontent\n<<<FILE_END>>>
    const filePattern = /<<<FILE_BEGIN:(.+?)>>>/g;
    let match;

    while ((match = filePattern.exec(fileSection)) !== null) {
      const filename = match[1].trim();

      files.push({ name: filename });
    }
  }

  return { userContent, files };
}

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
    isCorrectType,
    restoreFormState,
    parseResult
  } = config;

  const navigate = useNavigate();
  const { refetch: refetchConversations } = useSavedConversationsContext();

  // State
  const [hasStarted, setHasStarted] = useState(false);
  const [userMessages, setUserMessages] = useState<ConversationMessage[]>([]);
  const [resultHistory, setResultHistory] = useState<TResult[]>([]);

  // Refs
  const loadedThreadIdRef = useRef<string | null>(null);
  const isLoadingFromUrlRef = useRef(false);
  // Track which result has been processed to prevent duplicate additions
  const lastProcessedResultRef = useRef<string | null>(null);

  // Update URL when thread ID changes (from SSE)
  useEffect(() => {
    const shouldUpdateUrl =
      threadId && !urlThreadId && !isLoadingFromUrlRef.current;

    if (shouldUpdateUrl) {
      navigate(`${routePath}/${threadId}`, { replace: true });
      // Trigger refetch when a new conversation is created
      refetchConversations();
    }
  }, [threadId, urlThreadId, navigate, routePath, refetchConversations]);

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

      // Clear previous data and reset tracking
      setUserMessages([]);
      setResultHistory([]);
      lastProcessedResultRef.current = null;

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
            // Parse the message to separate user content from file contents
            const { userContent, files } = parseUserMessage(msg.content);

            userMsgs.push({
              id: `user-${crypto.randomUUID()}`,
              role: "user",
              content: userContent,
              timestamp: new Date(),
              files: files.length > 0 ? files : undefined
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

        // Mark the last result as processed to prevent re-adding if SSE fires
        if (results.length > 0) {
          lastProcessedResultRef.current = JSON.stringify(
            results[results.length - 1]
          );
        }
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

    // Create a unique key for this result based on its content
    const resultKey = JSON.stringify(result);

    // Skip if this is the same result we already processed
    if (lastProcessedResultRef.current === resultKey) {
      return;
    }

    // Mark this result as processed
    lastProcessedResultRef.current = resultKey;

    // Add to history
    setResultHistory((prev) => [...prev, result]);

    // Trigger refetch when a conversation is continued (new result added)
    refetchConversations();
  }, [result, streamingState, refetchConversations]);

  return {
    hasStarted,
    setHasStarted,
    userMessages,
    setUserMessages,
    resultHistory,
    setResultHistory
  };
}
