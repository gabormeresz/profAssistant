/**
 * Export API service.
 * Calls backend endpoints that generate downloadable files (e.g. PPTX).
 */

import type { Presentation } from "../types";
import { API_ENDPOINTS } from "../utils/constants";
import { getAccessToken, tryRefresh } from "./authService";

/**
 * Send presentation data to the backend and receive a .pptx blob.
 */
export async function exportPresentationToPptx(
  presentation: Presentation
): Promise<Blob> {
  let token = getAccessToken();

  let response = await fetch(API_ENDPOINTS.EXPORT_PRESENTATION_PPTX, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(presentation)
  });

  if (response.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      token = getAccessToken();
      response = await fetch(API_ENDPOINTS.EXPORT_PRESENTATION_PPTX, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify(presentation)
      });
    }
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(
      err.detail || err.error || "Failed to generate PowerPoint file"
    );
  }

  return response.blob();
}
