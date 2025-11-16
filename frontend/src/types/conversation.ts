export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  files?: { name: string }[];
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
  user_comment?: string;
  language?: string;
}

export interface SavedLessonPlan extends SavedConversationBase {
  conversation_type: "lesson_plan";
  course_title: string;
  class_number: number;
  class_title: string;
  learning_objectives: string[];
  key_topics: string[];
  activities_projects: string[];
  user_comment?: string;
  language?: string;
}

export type SavedConversation = SavedCourseOutline | SavedLessonPlan;

export interface ConversationListResponse {
  conversations: SavedConversation[];
  total: number;
}

export interface ConversationHistoryResponse {
  thread_id: string;
  messages: {
    role: string;
    content: string;
  }[];
  metadata: SavedConversation;
}
