import UserMessage from "./UserMessage";
import AssistantMessage from "./AssistantMessage";
import type { ConversationMessage } from "../types/conversation";

interface ChatMessageProps {
  message: ConversationMessage;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  if (message.role === "user") {
    return <UserMessage message={message} />;
  }

  return <AssistantMessage message={message} />;
}
