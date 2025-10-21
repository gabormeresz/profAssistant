/**
 * API Request/Response Types
 */

export interface LessonPlanRequest {
  message: string;
  topic: string;
  number_of_classes: number;
  thread_id?: string;
  files?: File[];
}

export interface EnhancePromptRequest {
  message: string;
  topic: string;
  numberOfClasses: number;
}

export interface EnhancePromptResponse {
  enhanced_prompt?: string;
  error?: string;
}
