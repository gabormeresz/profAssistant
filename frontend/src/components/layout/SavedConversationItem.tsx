import { useNavigate } from "react-router-dom";
import type { SavedConversation } from "../../types/conversation";

interface SavedConversationItemProps {
  conversation: SavedConversation;
  onDelete?: (threadId: string) => void;
}

export default function SavedConversationItem({
  conversation,
  onDelete
}: SavedConversationItemProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    // Navigate to the appropriate page based on conversation type
    const routes: Record<string, string> = {
      structured_outline: "/structured-outline",
      markdown_outline: "/outline-generator",
      lesson_plan: "/lesson-planner"
    };

    const route = routes[conversation.conversation_type];
    if (route) {
      // Pass the thread_id and conversation data via state
      navigate(route, {
        state: {
          threadId: conversation.thread_id,
          conversation
        }
      });
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent navigation when clicking delete
    if (
      onDelete &&
      confirm("Are you sure you want to delete this conversation?")
    ) {
      onDelete(conversation.thread_id);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getIcon = () => {
    switch (conversation.conversation_type) {
      case "structured_outline":
        return "⚡";
      case "markdown_outline":
        return "📝";
      case "lesson_plan":
        return "📚";
      default:
        return "💬";
    }
  };

  const getSubtitle = () => {
    if (
      conversation.conversation_type === "structured_outline" ||
      conversation.conversation_type === "markdown_outline"
    ) {
      const outline = conversation as Extract<
        SavedConversation,
        { topic: string }
      >;
      return `${outline.number_of_classes} classes`;
    } else if (conversation.conversation_type === "lesson_plan") {
      const lesson = conversation as Extract<
        SavedConversation,
        { subject: string }
      >;
      return lesson.subject;
    }
    return "";
  };

  return (
    <div
      onClick={handleClick}
      className="group relative px-3 py-2 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
    >
      <div className="flex items-start gap-2">
        <span className="text-lg flex-shrink-0 mt-0.5">{getIcon()}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-medium text-gray-900 truncate">
              {conversation.title}
            </h4>
            <button
              onClick={handleDelete}
              className="opacity-0 group-hover:opacity-100 flex-shrink-0 text-gray-400 hover:text-red-600 transition-opacity"
              title="Delete conversation"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-500 truncate">{getSubtitle()}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400">
              {conversation.message_count}{" "}
              {conversation.message_count === 1 ? "message" : "messages"}
            </span>
            <span className="text-xs text-gray-400">•</span>
            <span className="text-xs text-gray-400">
              {formatDate(conversation.updated_at)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
