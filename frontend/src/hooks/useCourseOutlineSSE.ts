import { useCallback } from "react";
import { API_ENDPOINTS } from "../utils/constants";
import { useSSE } from "./useSSE";
import type {
  CourseOutlineRequest,
  StreamingState,
  CourseOutline
} from "../types";

interface UseCourseOutlineSSEReturn {
  courseOutline: CourseOutline | null;
  progressMessage: string;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendMessage: (data: CourseOutlineRequest) => Promise<CourseOutline | null>;
  resetThread: () => void;
  setThreadId: (id: string | null) => void;
}

/**
 * Course Outline specific SSE hook
 * Wraps the generic useSSE hook with course outline specific logic
 */
export const useCourseOutlineSSE = (): UseCourseOutlineSSEReturn => {
  const {
    data: courseOutline,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendRequest,
    resetThread,
    setThreadId
  } = useSSE<CourseOutline>();

  const sendMessage = useCallback(
    async (data: CourseOutlineRequest): Promise<CourseOutline | null> => {
      // Prepare form data
      const formData = new FormData();
      formData.append("message", data.message);

      // Only append initial request fields if provided
      if (data.topic !== undefined) {
        formData.append("topic", data.topic);
      }
      if (data.number_of_classes !== undefined) {
        formData.append("number_of_classes", data.number_of_classes.toString());
      }
      if (data.language !== undefined) {
        formData.append("language", data.language);
      }

      // Add files if present
      if (data.files && data.files.length > 0) {
        data.files.forEach((file: File) => {
          formData.append("files", file);
        });
      }

      // Send request using generic SSE hook
      return await sendRequest(
        API_ENDPOINTS.COURSE_OUTLINE_GENERATOR,
        formData,
        {
          onComplete: () => {
            // Custom handler for complete event if needed
          }
        }
      );
    },
    [sendRequest]
  );

  return {
    courseOutline,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread,
    setThreadId
  };
};
