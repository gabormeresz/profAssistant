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
  SavedPresentation,
  SavedAssessment,
  ConversationType,
  ConversationListResponse
} from "./conversation";

// API types
export type {
  CourseOutlineRequest,
  LessonPlanRequest,
  PresentationRequest,
  AssessmentRequest,
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

// Presentation types
export type {
  Presentation,
  Slide,
  PresentationStreamEvent
} from "./presentation";

// Assessment types
export type {
  Assessment,
  AssessmentSection,
  Question,
  QuestionOption,
  QuestionTypeConfig,
  AssessmentPreset,
  AssessmentStreamEvent
} from "./assessment";

// Auth types
export type {
  UserCreate,
  UserResponse,
  TokenPair,
  TokenRefreshRequest,
  UserSettingsResponse,
  UserSettingsUpdate,
  AvailableModel
} from "./auth";
