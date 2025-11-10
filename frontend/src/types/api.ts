/**
 * API Request/Response Types
 */

export interface CourseOutlineRequest {
  message: string;
  topic: string;
  number_of_classes: number;
  language?: string;
  thread_id?: string;
  files?: File[];
}

export interface LessonPlanRequest {
  message: string;
  course_title: string;
  class_number: number;
  class_title: string;
  learning_objectives: string[];
  key_topics: string[];
  activities_projects: string[];
  language?: string;
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
