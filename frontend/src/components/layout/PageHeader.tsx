import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";
import LanguageSelector from "./LanguageSelector";

interface PageHeaderProps {
  actions?: ReactNode;
}

export default function PageHeader({ actions }: PageHeaderProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2">
          <h1 className="text-2xl font-bold dark:text-gray-200">
            Prof
            <span className="text-blue-600 dark:text-blue-400">Assistant</span>
          </h1>
        </Link>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
            aria-label={
              theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
            }
          >
            {theme === "dark" ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </button>
          <LanguageSelector variant="header" />
          {actions}
        </div>
      </div>
    </header>
  );
}
