/**
 * Assessment types matching the backend Pydantic schema
 */

export interface QuestionOption {
  label: string;
  text: string;
  is_correct: boolean;
}

export interface Question {
  question_number: number;
  question_text: string;
  points: number;
  difficulty: "easy" | "medium" | "hard";
  options?: QuestionOption[];
  correct_answer?: string;
  scoring_rubric?: string;
  key_points?: string[];
  suggested_word_limit?: number;
  explanation?: string;
}

export interface AssessmentSection {
  section_number: number;
  section_title: string;
  section_type: "multiple_choice" | "true_false" | "short_answer" | "essay";
  instructions: string;
  questions: Question[];
}

export interface Assessment {
  assessment_title: string;
  assessment_type: "quiz" | "exam" | "homework" | "practice";
  course_title: string;
  class_title?: string;
  total_points: number;
  estimated_duration_minutes: number;
  general_instructions: string;
  sections: AssessmentSection[];
  grading_notes?: string;
}

export interface AssessmentStreamEvent {
  type: "thread_id" | "progress" | "complete" | "error";
  thread_id?: string;
  message?: string;
  data?: Assessment;
}

/**
 * Question type configuration used in the input form
 */
export interface QuestionTypeConfig {
  type: "multiple_choice" | "true_false" | "short_answer" | "essay";
  count: number;
  points_each: number;
}

/**
 * Assessment type presets
 */
export type AssessmentPreset =
  | "quick_quiz"
  | "midterm_exam"
  | "homework"
  | "practice_test"
  | "custom";
