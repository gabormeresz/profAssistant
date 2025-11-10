import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { useSavedConversations } from "../../hooks";
import SavedConversationItem from "./SavedConversationItem";
import { useImperativeHandle, forwardRef } from "react";
import { useTranslation } from "react-i18next";
import LanguageSelector from "./LanguageSelector";

interface SidebarProps {
  onNewConversation?: () => void;
}

export interface SidebarRef {
  refetchConversations: () => Promise<void>;
}

const Sidebar = forwardRef<SidebarRef, SidebarProps>(
  ({ onNewConversation }, ref) => {
    const location = useLocation();
    const navigate = useNavigate();
    const { threadId: currentThreadId } = useParams<{ threadId?: string }>();
    const { conversations, isLoading, error, deleteConversation, refetch } =
      useSavedConversations();
    const { t } = useTranslation();

    // Expose refetch method to parent components
    useImperativeHandle(ref, () => ({
      refetchConversations: refetch
    }));

    const handleDeleteConversation = async (threadId: string) => {
      // Check if we're deleting the currently active conversation
      const isDeletingActive = threadId === currentThreadId;

      // Delete the conversation
      await deleteConversation(threadId);

      // If we deleted the active conversation, navigate to parent and reset
      if (isDeletingActive) {
        if (onNewConversation) {
          onNewConversation();
        }
        navigate(currentBasePath, { replace: true });
      }
    };

    const navItems = [
      {
        path: "/outline-generator",
        label: t("sidebar.courseOutlineGenerator"),
        icon: "📝"
      },
      {
        path: "/lesson-planner",
        label: t("sidebar.lessonPlanner"),
        icon: "📚"
      }
    ];

    // Extract base path once for reuse
    const currentBasePath = "/" + location.pathname.split("/")[1];

    const handleNavClick = (
      e: React.MouseEvent<HTMLAnchorElement>,
      path: string
    ) => {
      const isOnSamePage = currentBasePath === path;

      if (isOnSamePage) {
        e.preventDefault();
        // If we have a handleNewConversation function, call it
        if (onNewConversation) {
          onNewConversation();
        }
        // Navigate to the base path (without threadId)
        navigate(path, { replace: true });
      }
    };

    return (
      <aside className="w-78 bg-white border-r border-gray-200 sticky top-0 h-screen max-h-screen p-4 flex flex-col">
        <LanguageSelector />

        <nav className="space-y-2">
          {navItems.map((item) => {
            const isActive = currentBasePath === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={(e) => handleNavClick(e, item.path)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700 font-medium"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <hr className="my-6 border-gray-200" />

        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <h3 className="text-sm font-semibold text-gray-700 px-3">
              {t("sidebar.recentConversations")}
            </h3>
            {conversations.length > 0 && (
              <span className="text-xs text-gray-500 px-3">
                {conversations.length}
              </span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 min-h-0">
            {isLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            )}

            {error && (
              <div className="px-3 py-2 text-sm text-red-600 bg-red-50 rounded-lg">
                {error}
              </div>
            )}

            {!isLoading && !error && conversations.length === 0 && (
              <div className="px-3 py-8 text-center">
                <p className="text-sm text-gray-500">
                  {t("sidebar.noConversations")}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {t("sidebar.startNewConversation")}
                </p>
              </div>
            )}

            {!isLoading &&
              !error &&
              conversations.map((conversation) => (
                <SavedConversationItem
                  key={conversation.thread_id}
                  conversation={conversation}
                  onDelete={handleDeleteConversation}
                  isActive={conversation.thread_id === currentThreadId}
                />
              ))}
          </div>
        </div>
      </aside>
    );
  }
);

Sidebar.displayName = "Sidebar";

export default Sidebar;
