import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import { ScrollNavigationButtons } from "../ui";

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
  onNewConversation?: () => void;
  header?: ReactNode;
}

function Layout({
  children,
  showSidebar = false,
  onNewConversation,
  header
}: LayoutProps) {
  if (showSidebar) {
    return (
      <div className="h-screen bg-gray-50 dark:bg-gray-900 flex overflow-hidden">
        <Sidebar onNewConversation={onNewConversation} />
        <main className="flex-1 overflow-y-auto relative bg-surface">
          {header}
          <div className="max-w-5xl mx-auto p-6 pb-24">{children}</div>
          <ScrollNavigationButtons />
        </main>
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-surface-alt">
      {header}
      <div className="max-w-4xl mx-auto p-6">{children}</div>
    </div>
  );
}

Layout.displayName = "Layout";

export default Layout;
