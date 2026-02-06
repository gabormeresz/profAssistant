import type {
  ConversationListResponse,
  ConversationType,
  SavedConversation,
  ConversationHistoryResponse
} from "../types/conversation";
import { getAccessToken, tryRefresh } from "./authService";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Build Authorization header if a token is available.
 */
function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Authenticated fetch with automatic token refresh on 401.
 */
async function authFetch(url: string, init?: RequestInit): Promise<Response> {
  let res = await fetch(url, {
    ...init,
    headers: { ...authHeaders(), ...(init?.headers || {}) }
  });

  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetch(url, {
        ...init,
        headers: { ...authHeaders(), ...(init?.headers || {}) }
      });
    }
  }

  return res;
}

export interface FetchConversationsParams {
  conversation_type?: ConversationType;
  limit?: number;
  offset?: number;
}

/**
 * Fetch all saved conversations with optional filtering
 */
export async function fetchConversations(
  params?: FetchConversationsParams
): Promise<ConversationListResponse> {
  const queryParams = new URLSearchParams();

  if (params?.conversation_type) {
    queryParams.append("conversation_type", params.conversation_type);
  }
  if (params?.limit) {
    queryParams.append("limit", params.limit.toString());
  }
  if (params?.offset) {
    queryParams.append("offset", params.offset.toString());
  }

  const url = `${API_BASE_URL}/conversations${
    queryParams.toString() ? `?${queryParams}` : ""
  }`;

  const response = await authFetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a specific conversation by thread_id
 */
export async function fetchConversation(
  threadId: string
): Promise<SavedConversation> {
  const response = await authFetch(`${API_BASE_URL}/conversations/${threadId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch conversation: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete a conversation by thread_id
 */
export async function deleteConversation(threadId: string): Promise<void> {
  const response = await authFetch(
    `${API_BASE_URL}/conversations/${threadId}`,
    {
      method: "DELETE"
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.statusText}`);
  }
}

/**
 * Fetch conversation history (messages) for a specific thread_id
 */
export async function fetchConversationHistory(
  threadId: string
): Promise<ConversationHistoryResponse> {
  const response = await authFetch(
    `${API_BASE_URL}/conversations/${threadId}/history`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch conversation history: ${response.statusText}`
    );
  }

  return response.json();
}
