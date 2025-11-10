import { useCallback } from "react";
import { API_ENDPOINTS } from "../utils/constants";
import { useSSE } from "./useSSE";
import type { LessonPlanRequest, StreamingState, LessonPlan } from "../types";

interface UseLessonPlanSSEReturn {
  lessonPlan: LessonPlan | null;
  progressMessage: string;
  loading: boolean;
  streamingState: StreamingState;
  threadId: string | null;
  sendMessage: (data: LessonPlanRequest) => Promise<LessonPlan | null>;
  clearData: () => void;
  resetThread: () => void;
  setThreadId: (id: string | null) => void;
}

/**
 * Lesson Plan specific SSE hook
 * Wraps the generic useSSE hook with lesson plan specific logic
 */
export const useLessonPlanSSE = (): UseLessonPlanSSEReturn => {
  const {
    data: lessonPlan,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendRequest,
    clearData,
    resetThread,
    setThreadId
  } = useSSE<LessonPlan>();

  const sendMessage = useCallback(
    async (data: LessonPlanRequest): Promise<LessonPlan | null> => {
      // Prepare form data
      const formData = new FormData();
      formData.append("message", data.message);
      formData.append("course_title", data.course_title);
      formData.append("class_number", data.class_number.toString());
      formData.append("class_title", data.class_title);
      formData.append(
        "learning_objectives",
        JSON.stringify(data.learning_objectives)
      );
      formData.append("key_topics", JSON.stringify(data.key_topics));
      formData.append(
        "activities_projects",
        JSON.stringify(data.activities_projects)
      );

      // Add language if provided
      if (data.language) {
        formData.append("language", data.language);
      }

      // Add files if present
      if (data.files && data.files.length > 0) {
        data.files.forEach((file) => {
          formData.append("files", file);
        });
      }

      // Send request using generic SSE hook
      return await sendRequest(API_ENDPOINTS.LESSON_PLANNER, formData, {
        onComplete: () => {
          // Custom handler for complete event if needed
        }
      });
    },
    [sendRequest]
  );

  return {
    lessonPlan,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    clearData,
    resetThread,
    setThreadId
  };
};
