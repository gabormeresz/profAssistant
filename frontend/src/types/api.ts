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

export interface PresentationRequest {
  message: string;
  course_title?: string;
  class_number?: number;
  class_title?: string;
  learning_objective?: string;
  key_points?: string[];
  lesson_breakdown?: string;
  activities?: string;
  homework?: string;
  extra_activities?: string;
  language?: string;
  thread_id?: string;
  files?: File[];
}

export interface AssessmentRequest {
  message: string;
  course_title?: string;
  class_title?: string;
  key_topics?: string[];
  assessment_type?: string;
  difficulty_level?: string;
  question_type_configs?: string; // JSON-serialized QuestionTypeConfig[]
  additional_instructions?: string;
  language?: string;
  thread_id?: string;
  files?: File[];
}

export interface EnhancePromptRequest {
  message: string;
  contextType: "course_outline" | "lesson_plan" | "presentation" | "assessment";
  additionalContext?: Record<string, unknown>;
  language?: string;
}

export interface EnhancePromptResponse {
  enhanced_prompt?: string;
  error?: string;
}
