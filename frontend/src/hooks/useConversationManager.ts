import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { logger } from "../utils/logger";
import {
  fetchConversation,
  fetchConversationHistory
} from "../services/conversationService";
import type { ConversationMessage, StreamingState } from "../types";
import { useSavedConversationsContext } from "./useSavedConversationsContext";

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

  // Extract file names from compact tag: [uploaded_files: a.pdf | b.docx]
  const tagPattern = /\[uploaded_files:\s*(.+?)\]/;
  const tagMatch = userContent.match(tagPattern);

  if (tagMatch) {
    userContent = userContent.replace(tagPattern, "").trim();

    const names = tagMatch[1]
      .split("|")
      .map((n) => n.trim())
      .filter(Boolean);
    for (const name of names) {
      files.push({ name });
    }
  }

  // Strip backend-generated follow-up prompt boilerplate so only the
  // user's actual text remains visible in the chat UI.
  if (userContent.startsWith("## Follow-up Request")) {
    userContent = userContent.replace(/^## Follow-up Request\s*/, "");

    // Remove the document upload instruction block
    userContent = userContent.replace(
      /\*\*IMPORTANT: New documents have been uploaded with this request\.\*\*[\s\S]*?incorporate the findings into your response\.\s*/,
      ""
    );

    // Remove the default placeholder when user sent no text (only files)
    userContent = userContent.replace(
      /^Please incorporate the information from the newly uploaded documents into your response\.?\s*$/,
      ""
    );

    userContent = userContent.trim();
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
  const [hasStarted, setHasStarted] = useState(!!urlThreadId);
  const [userMessages, setUserMessages] = useState<ConversationMessage[]>([]);
  const [resultHistory, setResultHistory] = useState<TResult[]>([]);

  // Refs
  const loadedThreadIdRef = useRef<string | null>(null);
  const isLoadingFromUrlRef = useRef(false);
  // Track which result has been processed to prevent duplicate additions
  const lastProcessedResultRef = useRef<string | null>(null);

  // Stabilize callback references using refs so they don't cause
  // the URL-loading effect to re-trigger on every render.
  // (These are typically inline arrow functions from the page component.)
  const isCorrectTypeRef = useRef(isCorrectType);
  isCorrectTypeRef.current = isCorrectType;
  const restoreFormStateRef = useRef(restoreFormState);
  restoreFormStateRef.current = restoreFormState;
  const parseResultRef = useRef(parseResult);
  parseResultRef.current = parseResult;

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

      // CRITICAL: Do NOT attempt to load from API while an SSE stream is
      // active. The URL gets its threadId from the thread_id SSE event
      // (BEFORE the stream completes). If we try to load now, the
      // conversation likely doesn't exist in the DB yet, causing a 404
      // that clears resultHistory and creates an infinite retry loop.
      if (streamingState === "streaming" || streamingState === "connecting") {
        return;
      }

      // Skip loading if this is the thread we just created via SSE
      // (indicated by threadId matching urlThreadId and having a result)
      if (threadId === urlThreadId && result && streamingState === "complete") {
        loadedThreadIdRef.current = urlThreadId;
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
        if (isCorrectTypeRef.current(conversation)) {
          restoreFormStateRef.current(conversation);
        }
        setHasStarted(true);

        // Parse message history
        const userMsgs: ConversationMessage[] = [];
        const results: TResult[] = [];

        // Get uploaded file names from conversation metadata
        const uploadedFileNames = conversation.uploaded_file_names;
        const metadataFiles =
          uploadedFileNames && uploadedFileNames.length > 0
            ? uploadedFileNames.map((name: string) => ({ name }))
            : undefined;

        history.messages.forEach((msg) => {
          if (msg.role === "user") {
            // Parse the message to separate user content from file contents
            const { userContent, files } = parseUserMessage(msg.content);

            // For the first user message, use file names from metadata if available
            const messageFiles =
              userMsgs.length === 0 && metadataFiles
                ? metadataFiles
                : files.length > 0
                  ? files
                  : undefined;

            userMsgs.push({
              id: `user-${crypto.randomUUID()}`,
              role: "user",
              content: userContent,
              timestamp: new Date(),
              files: messageFiles
            });
          } else if (msg.role === "assistant") {
            try {
              results.push(parseResultRef.current(msg.content));
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
        // Only navigate away if we're genuinely trying to load a saved
        // conversation (not one we just created via SSE)
        if (threadId !== urlThreadId) {
          navigate(routePath, { replace: true });
        }
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
    threadId,
    result,
    streamingState,
    setThreadId,
    navigate,
    routePath
    // NOTE: isCorrectType, restoreFormState, parseResult are accessed via
    // refs to avoid re-triggering this effect when their references change
    // (they are inline arrow functions recreated on every render).
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
