/**
 * API Request/Response Types
 */

export interface CourseOutlineRequest {
  message: string;
  topic?: string; // Required for initial request, omitted on follow-ups
  number_of_classes?: number; // Required for initial request, omitted on follow-ups
  language?: string; // Required for initial request, omitted on follow-ups
  thread_id?: string;
  files?: File[];
}

export interface LessonPlanRequest {
  message: string;
  course_title?: string; // Required for initial request, omitted on follow-ups
  class_number?: number; // Required for initial request, omitted on follow-ups
  class_title?: string; // Required for initial request, omitted on follow-ups
  learning_objectives?: string[]; // Required for initial request, omitted on follow-ups
  key_topics?: string[]; // Required for initial request, omitted on follow-ups
  activities_projects?: string[]; // Required for initial request, omitted on follow-ups
  language?: string; // Required for initial request, omitted on follow-ups
  thread_id?: string;
  files?: File[];
}

export interface EnhancePromptRequest {
  message: string;
  contextType: "course_outline" | "lesson_plan";
  additionalContext?: Record<string, unknown>;
}

export interface EnhancePromptResponse {
  enhanced_prompt?: string;
  error?: string;
}
