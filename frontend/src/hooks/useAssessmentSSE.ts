import { useCallback } from "react";
import { API_ENDPOINTS } from "../utils/constants";
import { useSSE } from "./useSSE";
import type { AssessmentRequest, StreamingState, Assessment } from "../types";

interface UseAssessmentSSEReturn {
  assessment: Assessment | null;
  progressMessage: string;
  error: string | null;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendMessage: (data: AssessmentRequest) => Promise<Assessment | null>;
  resetThread: () => void;
  setThreadId: (id: string | null) => void;
  clearError: () => void;
}

/**
 * Assessment specific SSE hook
 * Wraps the generic useSSE hook with assessment specific logic
 */
export const useAssessmentSSE = (): UseAssessmentSSEReturn => {
  const {
    data: assessment,
    progressMessage,
    error,
    loading,
    streamingState,
    threadId,
    sendRequest,
    resetThread,
    setThreadId,
    clearError
  } = useSSE<Assessment>();

  const sendMessage = useCallback(
    async (data: AssessmentRequest): Promise<Assessment | null> => {
      // Prepare form data
      const formData = new FormData();
      formData.append("message", data.message);

      // Only append initial request fields if provided
      if (data.course_title !== undefined) {
        formData.append("course_title", data.course_title);
      }
      if (data.class_title !== undefined) {
        formData.append("class_title", data.class_title);
      }
      if (data.key_topics !== undefined) {
        formData.append("key_topics", JSON.stringify(data.key_topics));
      }
      if (data.assessment_type !== undefined) {
        formData.append("assessment_type", data.assessment_type);
      }
      if (data.difficulty_level !== undefined) {
        formData.append("difficulty_level", data.difficulty_level);
      }
      if (data.question_type_configs !== undefined) {
        formData.append("question_type_configs", data.question_type_configs);
      }
      if (data.additional_instructions !== undefined) {
        formData.append(
          "additional_instructions",
          data.additional_instructions
        );
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

      // Send request using generic SSE hook
      return await sendRequest(API_ENDPOINTS.ASSESSMENT_GENERATOR, formData);
    },
    [sendRequest]
  );

  return {
    assessment,
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
