import { API_ENDPOINTS } from "../utils/constants";
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
  formData.append("topic", data.topic);
  formData.append("num_classes", data.numberOfClasses.toString());

  const response = await fetch(API_ENDPOINTS.ENHANCE_PROMPT, {
    method: "POST",
    body: formData
  });

  const result = await response.json();

  if (!response.ok) {
    return {
      error: result.error || "Failed to enhance prompt"
    };
  }

  return result;
}
