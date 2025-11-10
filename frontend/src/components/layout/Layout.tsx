import type { ReactNode } from "react";
import { forwardRef } from "react";
import Sidebar, { type SidebarRef } from "./Sidebar";
import { ScrollNavigationButtons } from "../ui";

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
  onNewConversation?: () => void;
  header?: ReactNode;
}

const Layout = forwardRef<SidebarRef, LayoutProps>(
  ({ children, showSidebar = false, onNewConversation, header }, ref) => {
    if (showSidebar) {
      return (
        <div className="h-screen bg-gray-50 flex overflow-hidden">
          <Sidebar ref={ref} onNewConversation={onNewConversation} />
          <main className="flex-1 overflow-y-auto relative">
            {header}
            <div className="max-w-5xl mx-auto p-6 pb-24">{children}</div>
            <ScrollNavigationButtons />
          </main>
        </div>
      );
    }

    return (
      <div className="h-screen bg-gray-50 overflow-y-auto">
        {header}
        <div className="max-w-4xl mx-auto p-6">{children}</div>
      </div>
    );
  }
);

Layout.displayName = "Layout";

export default Layout;
