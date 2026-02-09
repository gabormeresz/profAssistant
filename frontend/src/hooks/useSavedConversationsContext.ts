import { useContext } from "react";
import { SavedConversationsContext } from "../contexts/savedConversationsContextDef";

/**
 * Hook to access saved conversations context.
 * Must be used within SavedConversationsProvider.
 */
export function useSavedConversationsContext() {
  const context = useContext(SavedConversationsContext);
  if (context === undefined) {
    throw new Error(
      "useSavedConversationsContext must be used within SavedConversationsProvider"
    );
  }
  return context;
}
