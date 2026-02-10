/**
 * Authentication-related types matching the backend schemas.
 */

export interface UserCreate {
  email: string;
  password: string;
}

export interface UserResponse {
  user_id: string;
  email: string;
  role: "admin" | "user";
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

export interface AvailableModel {
  id: string;
  label: string;
  description_key: string;
}

export interface UserSettingsResponse {
  has_api_key: boolean;
  preferred_model: string;
  available_models: AvailableModel[];
  updated_at: string;
}

export interface UserSettingsUpdate {
  openai_api_key?: string | null;
  preferred_model?: string | null;
}
