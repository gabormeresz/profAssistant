import { useState, useEffect, useCallback, type ReactNode } from "react";
import type { UserResponse } from "../types/auth";
import {
  fetchCurrentUser,
  logoutUser,
  getAccessToken
} from "../services/authService";
import { AuthContext } from "./authContextDef";

export type { AuthContextValue } from "./authContextDef";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const u = await fetchCurrentUser();
      setUser(u);
    } catch {
      setUser(null);
    }
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
  }, []);

  // On mount, check if there's a stored token and load user
  useEffect(() => {
    const init = async () => {
      if (getAccessToken()) {
        await refreshUser();
      }
      setIsLoading(false);
    };
    init();
  }, [refreshUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        refreshUser,
        logout,
        isAuthenticated: user !== null
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
