/**
 * Centralized Type Exports
 * Import types from here for consistency
 */

// Domain types
// export type { ConversationMessage, ConversationHistory } from "./conversation";
export type { ConversationMessage } from "./conversation";

// API types
export type {
  LessonPlanRequest,
  EnhancePromptRequest,
  EnhancePromptResponse
} from "./api";

// Hook types
export type { StreamingState } from "./hooks";

// Course outline types
export type {
  CourseOutline,
  CourseClass,
  StructuredStreamEvent
} from "./courseOutline";
