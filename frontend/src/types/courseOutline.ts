/**
 * Course outline types matching the backend Pydantic schema
 */

export interface CourseClass {
  class_number: number;
  class_title: string;
  learning_objectives: string[];
  key_topics: string[];
  activities_projects: string[];
}

export interface CourseOutline {
  course_title: string;
  classes: CourseClass[];
}

export interface StructuredStreamEvent {
  type: "thread_id" | "progress" | "complete" | "error";
  thread_id?: string;
  message?: string;
  data?: CourseOutline;
}
