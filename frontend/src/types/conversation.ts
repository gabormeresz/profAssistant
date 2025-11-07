export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  files?: { name: string; size: number }[];
  topic?: string;
  numberOfClasses?: number;
}

// Saved conversation types matching backend schema
export type ConversationType = "course_outline" | "lesson_plan";

export interface SavedConversationBase {
  thread_id: string;
  conversation_type: ConversationType;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SavedCourseOutline extends SavedConversationBase {
  conversation_type: "course_outline";
  topic: string;
  number_of_classes: number;
  difficulty_level?: string;
  target_audience?: string;
}

export interface SavedLessonPlan extends SavedConversationBase {
  conversation_type: "lesson_plan";
  lesson_title: string;
  subject: string;
  grade_level?: string;
  duration_minutes?: number;
  learning_objectives?: string;
}

export type SavedConversation = SavedCourseOutline | SavedLessonPlan;

export interface ConversationListResponse {
  conversations: SavedConversation[];
  total: number;
}

export interface ConversationHistoryMessage {
  role: string;
  content: string;
}

export interface ConversationHistoryResponse {
  thread_id: string;
  messages: ConversationHistoryMessage[];
  metadata: SavedConversation;
}
