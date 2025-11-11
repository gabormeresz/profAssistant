import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { useSavedConversations } from "../../hooks";
import SavedConversationItem from "./SavedConversationItem";
import { useImperativeHandle, forwardRef } from "react";
import { useTranslation } from "react-i18next";
import LanguageSelector from "./LanguageSelector";
import { FileText, BookOpen } from "lucide-react";

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
        icon: FileText
      },
      {
        path: "/lesson-planner",
        label: t("sidebar.lessonPlanner"),
        icon: BookOpen
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
      <aside className="w-78 bg-[#2a3342] border-r border-[#1f2937] sticky top-0 h-screen max-h-screen p-4 flex flex-col">
        <div className="mb-6 text-center">
          <Link to="/" className="text-2xl font-bold transition-colors">
            <span className="text-white">Prof</span>
            <span className="text-[#5f7aff]">Assistant</span>
          </Link>
        </div>

        <LanguageSelector />

        <nav className="space-y-2">
          {navItems.map((item) => {
            const isActive = currentBasePath === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={(e) => handleNavClick(e, item.path)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-[#333f51] text-white font-medium"
                    : "text-[#cddaef] hover:text-white hover:bg-[#333f51]"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "" : "opacity-70"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <hr className="my-6 border-[#3d4a5c]" />

        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <h3 className="text-sm font-semibold text-[#cddaef] px-3">
              {t("sidebar.recentConversations")}
            </h3>
            {conversations.length > 0 && (
              <span className="text-xs text-[#cddaef] px-3">
                {conversations.length}
              </span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 min-h-0 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-[#1f2937] [&::-webkit-scrollbar-thumb]:bg-[#3d4a5c] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-[#4a5568]">
            {isLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#80acff]"></div>
              </div>
            )}

            {error && (
              <div className="px-3 py-2 text-sm text-red-400 bg-red-900/20 rounded-lg">
                {error}
              </div>
            )}

            {!isLoading && !error && conversations.length === 0 && (
              <div className="px-3 py-8 text-center">
                <p className="text-sm text-[#cddaef]">
                  {t("sidebar.noConversations")}
                </p>
                <p className="text-xs text-[#6b7890] mt-1">
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
