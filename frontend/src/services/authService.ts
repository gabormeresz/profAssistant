/**
 * Authentication API service.
 * Handles login, registration, token refresh, logout, and user settings.
 */

import type {
  UserCreate,
  UserResponse,
  TokenPair,
  UserSettingsResponse,
  UserSettingsUpdate
} from "../types/auth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
//  Token storage helpers
// ---------------------------------------------------------------------------

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function storeTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// ---------------------------------------------------------------------------
//  Helpers
// ---------------------------------------------------------------------------

/**
 * Build headers with Bearer token for authenticated requests.
 */
function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
}

/**
 * Try to refresh the access token using the stored refresh token.
 * Returns true on success (new tokens stored), false otherwise.
 */
export async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const tokens: TokenPair = await res.json();
    storeTokens(tokens);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

/**
 * Authenticated fetch wrapper with automatic token refresh on 401.
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
 * Log in with email + password. Stores tokens on success.
 */
export async function loginUser(data: UserCreate): Promise<TokenPair> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login failed");
  }

  const tokens: TokenPair = await res.json();
  storeTokens(tokens);
  return tokens;
}

/**
 * Log out: invalidate refresh token server-side and clear local storage.
 */
export async function logoutUser(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (refreshToken) {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken })
    }).catch(() => {});
  }
  clearTokens();
}

/**
 * Get the current authenticated user's profile.
 */
export async function fetchCurrentUser(): Promise<UserResponse> {
  const res = await authFetch(`${API_BASE_URL}/auth/me`);
  if (!res.ok) {
    throw new Error("Not authenticated");
  }
  return res.json();
}

/**
 * Get the current user's settings.
 */
export async function fetchUserSettings(): Promise<UserSettingsResponse> {
  const res = await authFetch(`${API_BASE_URL}/auth/settings`);
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
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update settings");
  }
  return res.json();
}
