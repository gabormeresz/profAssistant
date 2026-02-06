/**
 * Centralized Type Exports
 * Import types from here for consistency
 */

// Domain types
export type {
  ConversationMessage,
  SavedConversation,
  SavedCourseOutline,
  SavedLessonPlan,
  ConversationType,
  ConversationListResponse
} from "./conversation";

// API types
export type {
  CourseOutlineRequest,
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

// Lesson plan types
export type {
  LessonPlan,
  LessonSection,
  ActivityPlan,
  LessonPlanStreamEvent
} from "./lessonPlan";

// Auth types
export type {
  UserCreate,
  UserResponse,
  TokenPair,
  TokenRefreshRequest,
  UserSettingsResponse,
  UserSettingsUpdate
} from "./auth";
