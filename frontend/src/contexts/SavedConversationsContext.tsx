import { useState, useEffect, useCallback, type ReactNode } from "react";
import type { ConversationType } from "../types/conversation";
import {
  fetchConversations,
  deleteConversation as deleteConversationAPI
} from "../services";
import { useAuth } from "../hooks/useAuth";
import { logger } from "../utils/logger";
import {
  SavedConversationsContext,
  type SavedConversationsContextValue
} from "./savedConversationsContextDef";
import type { SavedConversation } from "../types/conversation";

interface SavedConversationsProviderProps {
  children: ReactNode;
}

/**
 * Global provider for saved conversations.
 * Loads conversations once on mount and caches them across navigation.
 * Provides refetch method to reload when conversations are created, deleted, or continued.
 */
export function SavedConversationsProvider({
  children
}: SavedConversationsProviderProps) {
  const { user, isLoading: isAuthLoading } = useAuth();
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

  // Re-fetch conversations whenever the authenticated user changes
  useEffect(() => {
    if (isAuthLoading) return;
    if (user) {
      fetchData(currentFilter);
    } else {
      // User logged out — clear cached conversations
      setConversations([]);
      setIsLoading(false);
    }
  }, [user, isAuthLoading, fetchData, currentFilter]);

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

  const value: SavedConversationsContextValue = {
    conversations,
    isLoading,
    error,
    refetch,
    deleteConversation,
    filterByType,
    currentFilter
  };

  return (
    <SavedConversationsContext.Provider value={value}>
      {children}
    </SavedConversationsContext.Provider>
  );
}
