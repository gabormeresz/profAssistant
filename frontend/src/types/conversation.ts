export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  files?: { name: string; size: number }[];
  topic?: string;
  numberOfClasses?: number;
}

export interface ConversationHistory {
  messages: ConversationMessage[];
  threadId: string | null;
}
