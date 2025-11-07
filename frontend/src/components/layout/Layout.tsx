import type { ReactNode } from "react";
import { forwardRef } from "react";
import Sidebar, { type SidebarRef } from "./Sidebar";

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
  onNewConversation?: () => void;
}

const Layout = forwardRef<SidebarRef, LayoutProps>(
  ({ children, showSidebar = false, onNewConversation }, ref) => {
    if (showSidebar) {
      return (
        <div className="min-h-screen bg-gray-50 flex">
          <Sidebar ref={ref} onNewConversation={onNewConversation} />
          <main className="flex-1 p-6">
            <div className="max-w-5xl mx-auto">{children}</div>
          </main>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto p-6">{children}</div>
      </div>
    );
  }
);

Layout.displayName = "Layout";

export default Layout;
