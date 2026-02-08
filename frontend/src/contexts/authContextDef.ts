import { createContext } from "react";

export interface AuthContextValue {
  /** The currently logged-in user, or null if not authenticated. */
  user: import("../types/auth").UserResponse | null;
  /** True while we are checking the stored token on first load. */
  isLoading: boolean;
  /** Re-fetch the current user (e.g. after login). */
  refreshUser: () => Promise<import("../types/auth").UserResponse | null>;
  /** Log out and clear state. */
  logout: () => Promise<void>;
  /** Whether the user is authenticated. */
  isAuthenticated: boolean;
  /** The user's settings (API key status, preferred model, etc.). */
  settings: import("../types/auth").UserSettingsResponse | null;
  /** True while settings are being loaded for the first time. */
  isLoadingSettings: boolean;
  /** Re-fetch settings (e.g. after saving on the profile page). */
  refreshSettings: () => Promise<
    import("../types/auth").UserSettingsResponse | null
  >;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined
);
