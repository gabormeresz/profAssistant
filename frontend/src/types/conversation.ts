export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  files?: { name: string }[];
}

// Saved conversation types matching backend schema
export type ConversationType =
  | "course_outline"
  | "lesson_plan"
  | "presentation"
  | "assessment";

export interface SavedConversationBase {
  thread_id: string;
  conversation_type: ConversationType;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  uploaded_file_names?: string[];
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

export interface SavedPresentation extends SavedConversationBase {
  conversation_type: "presentation";
  course_title: string;
  class_number?: number | null;
  class_title: string;
  learning_objective?: string;
  key_points: string[];
  lesson_breakdown?: string;
  activities?: string;
  homework?: string;
  extra_activities?: string;
  user_comment?: string;
  language?: string;
}

export interface SavedAssessment extends SavedConversationBase {
  conversation_type: "assessment";
  course_title: string;
  class_title?: string;
  key_topics: string[];
  assessment_type: string;
  difficulty_level?: string;
  question_type_configs: string; // JSON string
  user_comment?: string;
  language?: string;
}

export type SavedConversation =
  | SavedCourseOutline
  | SavedLessonPlan
  | SavedPresentation
  | SavedAssessment;

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
