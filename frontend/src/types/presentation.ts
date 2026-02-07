/**
 * Presentation types matching the backend Pydantic schema
 */

export interface Slide {
  slide_number: number;
  title: string;
  bullet_points: string[];
  speaker_notes?: string | null;
  visual_suggestion?: string | null;
}

export interface Presentation {
  course_title: string;
  lesson_title: string;
  class_number: number;
  slides: Slide[];
}

export interface PresentationStreamEvent {
  type: "thread_id" | "progress" | "complete" | "error";
  thread_id?: string;
  message?: string;
  data?: Presentation;
}
