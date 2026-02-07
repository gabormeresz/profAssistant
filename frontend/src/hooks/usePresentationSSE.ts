import { useCallback } from "react";
import { API_ENDPOINTS } from "../utils/constants";
import { useSSE } from "./useSSE";
import type {
  PresentationRequest,
  StreamingState,
  Presentation
} from "../types";

interface UsePresentationSSEReturn {
  presentation: Presentation | null;
  progressMessage: string;
  error: string | null;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendMessage: (data: PresentationRequest) => Promise<Presentation | null>;
  resetThread: () => void;
  setThreadId: (id: string | null) => void;
  clearError: () => void;
}

/**
 * Presentation specific SSE hook
 * Wraps the generic useSSE hook with presentation specific logic
 */
export const usePresentationSSE = (): UsePresentationSSEReturn => {
  const {
    data: presentation,
    progressMessage,
    error,
    loading,
    streamingState,
    threadId,
    sendRequest,
    resetThread,
    setThreadId,
    clearError
  } = useSSE<Presentation>();

  const sendMessage = useCallback(
    async (data: PresentationRequest): Promise<Presentation | null> => {
      const formData = new FormData();
      formData.append("message", data.message);

      if (data.course_title !== undefined) {
        formData.append("course_title", data.course_title);
      }
      if (data.class_number !== undefined) {
        formData.append("class_number", data.class_number.toString());
      }
      if (data.class_title !== undefined) {
        formData.append("class_title", data.class_title);
      }
      if (data.learning_objective !== undefined) {
        formData.append("learning_objective", data.learning_objective);
      }
      if (data.key_points !== undefined) {
        formData.append("key_points", JSON.stringify(data.key_points));
      }
      if (data.lesson_breakdown !== undefined) {
        formData.append("lesson_breakdown", data.lesson_breakdown);
      }
      if (data.activities !== undefined) {
        formData.append("activities", data.activities);
      }
      if (data.homework !== undefined) {
        formData.append("homework", data.homework);
      }
      if (data.extra_activities !== undefined) {
        formData.append("extra_activities", data.extra_activities);
      }
      if (data.language !== undefined) {
        formData.append("language", data.language);
      }

      // Add files if present
      if (data.files && data.files.length > 0) {
        data.files.forEach((file) => {
          formData.append("files", file);
        });
      }

      return await sendRequest(API_ENDPOINTS.PRESENTATION_GENERATOR, formData);
    },
    [sendRequest]
  );

  return {
    presentation,
    progressMessage,
    error,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread,
    setThreadId,
    clearError
  };
};
