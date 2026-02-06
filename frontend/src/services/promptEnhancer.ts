import { API_ENDPOINTS } from "../utils/constants";
import { getAccessToken, tryRefresh } from "./authService";
import type { EnhancePromptRequest, EnhancePromptResponse } from "../types";

export type { EnhancePromptRequest, EnhancePromptResponse };

/**
 * Call the prompt enhancement API
 */
export async function enhancePrompt(
  data: EnhancePromptRequest
): Promise<EnhancePromptResponse> {
  const formData = new FormData();
  formData.append("message", data.message);
  formData.append("context_type", data.contextType);

  // Add additional context if provided
  if (data.additionalContext) {
    formData.append(
      "additional_context",
      JSON.stringify(data.additionalContext)
    );
  }

  // Add language if provided
  if (data.language) {
    formData.append("language", data.language);
  }

  let token = getAccessToken();
  let response = await fetch(API_ENDPOINTS.ENHANCE_PROMPT, {
    method: "POST",
    body: formData,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  });

  // Retry once with a refreshed token on 401
  if (response.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      token = getAccessToken();
      response = await fetch(API_ENDPOINTS.ENHANCE_PROMPT, {
        method: "POST",
        body: formData,
        headers: token ? { Authorization: `Bearer ${token}` } : undefined
      });
    }
  }

  const result = await response.json();

  if (!response.ok) {
    // FastAPI HTTPException returns { detail: "..." },
    // while explicit JSONResponse errors use { error: "..." }
    const errorMessage =
      result.detail || result.error || "Failed to enhance prompt";
    return {
      error: errorMessage
    };
  }

  return result;
}
