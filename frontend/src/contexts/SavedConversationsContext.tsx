import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode
} from "react";
import type {
  SavedConversation,
  ConversationType
} from "../types/conversation";
import {
  fetchConversations,
  deleteConversation as deleteConversationAPI
} from "../services";
import { useAuth } from "../hooks/useAuth";
import { logger } from "../utils/logger";

interface SavedConversationsContextValue {
  conversations: SavedConversation[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  deleteConversation: (threadId: string) => Promise<void>;
  filterByType: (type?: ConversationType) => void;
  currentFilter?: ConversationType;
}

const SavedConversationsContext = createContext<
  SavedConversationsContextValue | undefined
>(undefined);

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
  }, [user?.user_id, isAuthLoading, fetchData, currentFilter]);

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

/**
 * Hook to access saved conversations context.
 * Must be used within SavedConversationsProvider.
 */
export function useSavedConversationsContext(): SavedConversationsContextValue {
  const context = useContext(SavedConversationsContext);
  if (context === undefined) {
    throw new Error(
      "useSavedConversationsContext must be used within SavedConversationsProvider"
    );
  }
  return context;
}
