import { createContext } from "react";
import type {
  SavedConversation,
  ConversationType
} from "../types/conversation";

export interface SavedConversationsContextValue {
  conversations: SavedConversation[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  deleteConversation: (threadId: string) => Promise<void>;
  filterByType: (type?: ConversationType) => void;
  currentFilter?: ConversationType;
}

export const SavedConversationsContext = createContext<
  SavedConversationsContextValue | undefined
>(undefined);
