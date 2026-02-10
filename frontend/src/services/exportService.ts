/**
 * Export API service.
 * Calls backend endpoints that generate downloadable files (e.g. PPTX).
 */

import type { Presentation } from "../types";
import { API_ENDPOINTS } from "../utils/constants";
import { authFetch } from "./authService";

/**
 * Send presentation data to the backend and receive a .pptx blob.
 */
export async function exportPresentationToPptx(
  presentation: Presentation
): Promise<Blob> {
  const response = await authFetch(API_ENDPOINTS.EXPORT_PRESENTATION_PPTX, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(presentation)
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(
      err.detail || err.error || "Failed to generate PowerPoint file"
    );
  }

  return response.blob();
}
