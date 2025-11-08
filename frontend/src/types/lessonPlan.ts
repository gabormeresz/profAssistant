/**
 * Lesson plan types matching the backend Pydantic schema
 */

export interface LessonSection {
  section_title: string;
  description: string;
}

export interface ActivityPlan {
  name: string;
  objective: string;
  instructions: string;
}

export interface LessonPlan {
  class_number: number;
  class_title: string;
  learning_objective: string;
  key_points: string[];
  lesson_breakdown: LessonSection[];
  activities: ActivityPlan[];
  homework: string;
  extra_activities: string;
}

export interface LessonPlanStreamEvent {
  type: "thread_id" | "progress" | "complete" | "error";
  thread_id?: string;
  message?: string;
  data?: LessonPlan;
}
