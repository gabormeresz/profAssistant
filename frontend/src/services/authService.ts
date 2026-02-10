/**
 * Authentication API service.
 * Handles login, registration, token refresh, logout, and user settings.
 *
 * Security model:
 *   - Access token: short-lived JWT, held **in memory only** (never persisted).
 *   - Refresh token: long-lived opaque UUID, stored as an httpOnly cookie by
 *     the backend. The frontend never sees or handles the refresh token value.
 */

import type {
  UserCreate,
  UserResponse,
  AccessTokenResponse,
  UserSettingsResponse,
  UserSettingsUpdate
} from "../types/auth";
import { API_BASE_URL } from "../utils/constants";

// ---------------------------------------------------------------------------
//  In-memory token storage (never persisted to localStorage)
// ---------------------------------------------------------------------------

let _accessToken: string | null = null;

export function getAccessToken(): string | null {
  return _accessToken;
}

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

/**
 * Clear in-memory token and any legacy localStorage entries.
 */
export function clearTokens(): void {
  _accessToken = null;
  // Clean up legacy localStorage entries from before the migration
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// ---------------------------------------------------------------------------
//  Helpers
// ---------------------------------------------------------------------------

/**
 * Build headers with Bearer token for authenticated requests.
 * Does NOT set Content-Type — callers sending JSON should add it explicitly
 * so that FormData requests can let the browser set the boundary automatically.
 */
function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Try to refresh the access token using the httpOnly refresh-token cookie.
 * Returns true on success (new access token stored in memory), false otherwise.
 */
export async function tryRefresh(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include" // send httpOnly cookie
    });
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const data: AccessTokenResponse = await res.json();
    setAccessToken(data.access_token);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

/**
 * Authenticated fetch wrapper with automatic token refresh on 401.
 *
 * Exported so that other service modules can reuse it instead of
 * duplicating the 401-retry logic.
 */
export async function authFetch(
  url: string,
  init?: RequestInit
): Promise<Response> {
  let res = await fetch(url, {
    ...init,
    credentials: "include",
    headers: { ...authHeaders(), ...(init?.headers || {}) }
  });

  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetch(url, {
        ...init,
        credentials: "include",
        headers: { ...authHeaders(), ...(init?.headers || {}) }
      });
    }
  }

  return res;
}

// ---------------------------------------------------------------------------
//  Public API functions
// ---------------------------------------------------------------------------

/**
 * Register a new user account.
 */
export async function registerUser(data: UserCreate): Promise<UserResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

/**
 * Log in with email + password.
 * The backend sets the refresh token as an httpOnly cookie.
 * We only store the short-lived access token in memory.
 */
export async function loginUser(
  data: UserCreate
): Promise<AccessTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    credentials: "include", // receive the httpOnly cookie
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login failed");
  }

  const tokens: AccessTokenResponse = await res.json();
  setAccessToken(tokens.access_token);
  return tokens;
}

/**
 * Log out: invalidate refresh token server-side (cookie is cleared by
 * the backend) and clear the in-memory access token.
 */
export async function logoutUser(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include" // send the httpOnly cookie so the backend can invalidate it
  }).catch(() => {});
  clearTokens();
}

/**
 * Get the current authenticated user's profile.
 */
export async function fetchCurrentUser(): Promise<UserResponse> {
  const res = await authFetch(`${API_BASE_URL}/auth/me`, {
    headers: { "Content-Type": "application/json" }
  });
  if (!res.ok) {
    throw new Error("Not authenticated");
  }
  return res.json();
}

/**
 * Get the current user's settings.
 */
export async function fetchUserSettings(): Promise<UserSettingsResponse> {
  const res = await authFetch(`${API_BASE_URL}/auth/settings`, {
    headers: { "Content-Type": "application/json" }
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch settings");
  }
  return res.json();
}

/**
 * Update user settings (API key and/or preferred model).
 */
export async function updateUserSettings(
  data: UserSettingsUpdate
): Promise<UserSettingsResponse> {
  const res = await authFetch(`${API_BASE_URL}/auth/settings`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update settings");
  }
  return res.json();
}
