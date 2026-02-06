import { createContext } from "react";

export interface AuthContextValue {
  /** The currently logged-in user, or null if not authenticated. */
  user: import("../types/auth").UserResponse | null;
  /** True while we are checking the stored token on first load. */
  isLoading: boolean;
  /** Re-fetch the current user (e.g. after login). */
  refreshUser: () => Promise<void>;
  /** Log out and clear state. */
  logout: () => Promise<void>;
  /** Whether the user is authenticated. */
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined
);
