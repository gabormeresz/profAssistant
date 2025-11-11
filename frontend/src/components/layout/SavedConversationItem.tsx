import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { SavedConversation } from "../../types/conversation";
import { FileText, BookOpen, MessageCircle } from "lucide-react";

interface SavedConversationItemProps {
  conversation: SavedConversation;
  onDelete?: (threadId: string) => void;
  isActive?: boolean;
}

export default function SavedConversationItem({
  conversation,
  onDelete,
  isActive = false
}: SavedConversationItemProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleClick = () => {
    // Navigate to the appropriate page based on conversation type using URL params
    const routes: Record<string, string> = {
      course_outline: `/outline-generator/${conversation.thread_id}`,
      lesson_plan: `/lesson-planner/${conversation.thread_id}`
    };

    const route = routes[conversation.conversation_type];
    if (route) {
      navigate(route);
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

  // const formatDate = (dateString: string) => {
  //   const date = new Date(dateString);
  //   const now = new Date();
  //   const diffMs = now.getTime() - date.getTime();
  //   const diffMins = Math.floor(diffMs / 60000);
  //   const diffHours = Math.floor(diffMs / 3600000);
  //   const diffDays = Math.floor(diffMs / 86400000);

  //   if (diffMins < 60) return `${diffMins}m ago`;
  //   if (diffHours < 24) return `${diffHours}h ago`;
  //   if (diffDays < 7) return `${diffDays}d ago`;
  //   return date.toLocaleDateString();
  // };

  const getIcon = () => {
    switch (conversation.conversation_type) {
      case "course_outline":
        return FileText;
      case "lesson_plan":
        return BookOpen;
      default:
        return MessageCircle;
    }
  };

  const getLanguageFlag = () => {
    const language = conversation.language || "English";
    return language === "English" ? "EN" : "HU";
  };

  const getSubtitle = () => {
    if (conversation.conversation_type === "course_outline") {
      const outline = conversation as Extract<
        SavedConversation,
        { topic: string }
      >;
      return `${outline.number_of_classes} ${t("sidebar.classes")}`;
    } else if (conversation.conversation_type === "lesson_plan") {
      const lesson = conversation as Extract<
        SavedConversation,
        { course_title: string }
      >;
      return lesson.course_title;
    }
    return "";
  };

  return (
    <div
      onClick={handleClick}
      className={`group relative px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isActive
          ? "bg-[#333f51] border-l-2 border-[#80acff] pl-2.5"
          : "hover:bg-[#333f51]"
      }`}
    >
      <div className="flex items-center gap-2">
        {(() => {
          const Icon = getIcon();
          return (
            <Icon
              className={`w-4.5 h-4.5 flex-shrink-0 ${
                isActive
                  ? "text-[#80acff]"
                  : "text-[#cddaef] opacity-70 group-hover:text-white"
              }`}
            />
          );
        })()}
        <span
          className={`text-sm flex-shrink-0 ${
            isActive ? "text-white" : "text-[#cddaef]"
          }`}
          title={conversation.language || "Hungarian"}
        >
          {getLanguageFlag()}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4
              className={`text-sm font-medium truncate ${
                isActive ? "text-white" : "text-[#cddaef]"
              }`}
            >
              {conversation.title}
            </h4>
            <button
              onClick={handleDelete}
              className="opacity-0 group-hover:opacity-100 flex-shrink-0 text-[#cddaef] hover:text-red-400 transition-opacity"
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
          <p
            className={`text-xs truncate mt-1 ${
              isActive ? "text-white" : "text-[#cddaef]"
            }`}
          >
            {getSubtitle()}
          </p>
          {/* <div className="flex items-center gap-2 mt-1">
            <span
              className={`text-xs ${
                isActive ? "text-white" : "text-[#cddaef]"
              }`}
            >
              {formatDate(conversation.updated_at)}
            </span>
          </div> */}
        </div>
      </div>
    </div>
  );
}
