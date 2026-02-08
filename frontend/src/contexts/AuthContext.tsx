import { useState, useEffect, useCallback, type ReactNode } from "react";
import type { UserResponse, UserSettingsResponse } from "../types/auth";
import {
  fetchCurrentUser,
  fetchUserSettings,
  logoutUser,
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
    } catch {
      setUser(null);
    }
  }, []);

  const refreshSettings = useCallback(async () => {
    try {
      const s = await fetchUserSettings();
      setSettings(s);
    } catch {
      setSettings(null);
    }
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
    setSettings(null);
  }, []);

  // On mount, check if there's a stored token and load user + settings
  useEffect(() => {
    const init = async () => {
      if (getAccessToken()) {
        await refreshUser();
        await refreshSettings();
      }
      setIsLoading(false);
      setIsLoadingSettings(false);
    };
    init();
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
