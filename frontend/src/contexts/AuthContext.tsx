import { useState, useEffect, useCallback, type ReactNode } from "react";
import type { UserResponse, UserSettingsResponse } from "../types/auth";
import {
  fetchCurrentUser,
  fetchUserSettings,
  logoutUser,
  tryRefresh,
  getAccessToken
} from "../services/authService";
import { AuthContext } from "./authContextDef";

export type { AuthContextValue } from "./authContextDef";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [settings, setSettings] = useState<UserSettingsResponse | null>(null);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const u = await fetchCurrentUser();
      setUser(u);
      return u;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  const refreshSettings = useCallback(async () => {
    try {
      const s = await fetchUserSettings();
      setSettings(s);
      return s;
    } catch {
      setSettings(null);
      return null;
    }
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
    setSettings(null);
  }, []);

  // On mount, attempt a silent token refresh via the httpOnly cookie.
  // If the cookie is valid the backend returns a new access token,
  // which we then use to load user + settings.
  //
  // The `cancelled` flag handles React 18 StrictMode, which
  // double-invokes effects in development.  Without it, two
  // concurrent tryRefresh() calls would race and the loser
  // would wipe auth state (token rotation = single-use tokens).
  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      // If we already have an in-memory access token (e.g. after SPA
      // navigation), skip the refresh.
      let hasToken = !!getAccessToken();

      if (!hasToken) {
        // Try to obtain an access token using the httpOnly refresh cookie.
        hasToken = await tryRefresh();
      }

      // If the component was unmounted while we were awaiting (StrictMode),
      // bail out so we don't set state on the stale instance.
      if (cancelled) return;

      if (hasToken) {
        await refreshUser();
        if (cancelled) return;
        await refreshSettings();
      }

      if (cancelled) return;
      setIsLoading(false);
      setIsLoadingSettings(false);
    };
    init();

    return () => {
      cancelled = true;
    };
  }, [refreshUser, refreshSettings]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        refreshUser,
        logout,
        isAuthenticated: user !== null,
        settings,
        isLoadingSettings,
        refreshSettings
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
