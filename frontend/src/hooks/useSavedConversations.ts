import { useState, useEffect, useCallback } from "react";
import type {
  SavedConversation,
  ConversationType
} from "../types/conversation";
import {
  fetchConversations,
  deleteConversation as deleteConversationAPI
} from "../services";
import { logger } from "../utils/logger";

interface UseSavedConversationsReturn {
  conversations: SavedConversation[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  deleteConversation: (threadId: string) => Promise<void>;
  filterByType: (type?: ConversationType) => void;
  currentFilter?: ConversationType;
}

/**
 * Hook to manage saved conversations - fetches on mount and provides utilities
 */
export function useSavedConversations(): UseSavedConversationsReturn {
  const [conversations, setConversations] = useState<SavedConversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentFilter, setCurrentFilter] = useState<
    ConversationType | undefined
  >();

  const fetchData = useCallback(async (filter?: ConversationType) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchConversations({
        conversation_type: filter,
        limit: 100
      });
      setConversations(response.conversations);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load conversations";
      setError(errorMessage);
      logger.error("Error fetching conversations:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch conversations on mount
  useEffect(() => {
    fetchData(currentFilter);
  }, [fetchData, currentFilter]);

  const refetch = useCallback(async () => {
    await fetchData(currentFilter);
  }, [fetchData, currentFilter]);

  const deleteConversation = useCallback(async (threadId: string) => {
    try {
      await deleteConversationAPI(threadId);
      // Remove from local state
      setConversations((prev) => prev.filter((c) => c.thread_id !== threadId));
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to delete conversation";
      setError(errorMessage);
      logger.error("Error deleting conversation:", err);
      throw err;
    }
  }, []);

  const filterByType = useCallback((type?: ConversationType) => {
    setCurrentFilter(type);
  }, []);

  return {
    conversations,
    isLoading,
    error,
    refetch,
    deleteConversation,
    filterByType,
    currentFilter
  };
}
