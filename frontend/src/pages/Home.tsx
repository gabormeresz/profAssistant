import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import { LanguageSelector } from "../components";
import { useTheme } from "../hooks/useTheme";
import {
  FileText,
  BookOpen,
  Presentation,
  ClipboardList,
  User,
  Rocket,
  Sun,
  Moon
} from "lucide-react";

function Home() {
  const { t } = useTranslation();
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold dark:text-gray-200">
              Prof
              <span className="text-blue-600 dark:text-blue-400">
                Assistant
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
              aria-label={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
            >
              {theme === "dark" ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
            <div className="w-40">
              <LanguageSelector variant="header" />
            </div>
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white whitespace-nowrap h-10"
                >
                  <User className="w-4 h-4" />
                  <span className="text-sm font-medium truncate max-w-[140px]">
                    {user?.email}
                  </span>
                </Link>
                <button
                  onClick={async () => {
                    await logout();
                    navigate("/");
                  }}
                  className="px-4 py-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium text-sm whitespace-nowrap h-10 flex items-center justify-center"
                >
                  {t("profile.logout")}
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/auth"
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white whitespace-nowrap h-10 flex items-center justify-center w-32"
                >
                  {t("home.login")}
                </Link>
                <Link
                  to="/auth"
                  className="px-6 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors whitespace-nowrap h-10 flex items-center justify-center w-36"
                >
                  {t("home.signup")}
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-8 sm:px-12 lg:px-20 py-16">
        <div className="grid md:grid-cols-2 gap-24 items-center">
          <div>
            <h2 className="text-5xl font-bold text-gray-900 dark:text-gray-200 mb-6 leading-tight">
              {t("home.hero.title")}
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
              {t("home.hero.subtitle")}
            </p>
            {isAuthenticated ? (
              <Link
                to="/app"
                className="inline-flex items-center gap-2 px-8 py-3 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors font-medium text-lg"
              >
                <Rocket className="w-5 h-5" />
                {t("profile.navigation.openApp")}
              </Link>
            ) : (
              <Link
                to="/auth"
                className="inline-block px-8 py-3 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors font-medium text-lg"
              >
                {t("home.hero.cta")}
              </Link>
            )}
          </div>
          <div className="relative">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-3xl overflow-hidden shadow-xl aspect-[6/5]">
              <img
                src="/professor.png"
                alt="professor using ProfAssistant"
                className="w-full h-full object-cover"
              />
            </div>
            {/* Decorative fingerprint pattern - top left */}
            <div className="absolute -top-12 -left-12 w-32 h-32 opacity-90 pointer-events-none">
              <img
                src="/fingerprint-decor.png"
                alt=""
                className="w-full h-full object-contain"
              />
            </div>
            {/* Decorative dots - bottom right */}
            <div className="absolute -bottom-24 -right-12 w-40 h-40 opacity-90">
              <svg
                viewBox="0 0 140 100"
                className="text-[#22C55D] fill-current"
              >
                {Array.from({ length: 5 }).map((_, j) =>
                  Array.from({ length: 7 }).map((_, i) => (
                    <circle
                      key={`${i}-${j}`}
                      cx={10 + i * 20}
                      cy={10 + j * 19}
                      r="2"
                    />
                  ))
                )}
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white dark:bg-gray-800 py-16">
        <div className="max-w-7xl mx-auto px-8 sm:px-12 lg:px-20">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <Link to="/course-outline-generator" className="group">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <FileText
                    className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2">
                  {t("home.features.courseOutline.title")}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {t("home.features.courseOutline.description")}
                </p>
              </div>
            </Link>

            {/* Feature 2 */}
            <Link to="/lesson-plan-generator" className="group">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <BookOpen
                    className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2">
                  {t("home.features.lessonPlan.title")}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {t("home.features.lessonPlan.description")}
                </p>
              </div>
            </Link>

            {/* Feature 3 - Placeholder */}
            <Link to="/presentation-generator" className="group">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <Presentation
                    className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2">
                  {t("home.features.presentation.title")}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {t("home.features.presentation.description")}
                </p>
              </div>
            </Link>

            {/* Feature 4 - Placeholder */}
            <Link to="/assessment-generator" className="group">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <ClipboardList
                    className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2">
                  {t("home.features.assessment.title")}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {t("home.features.assessment.description")}
                </p>
              </div>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-2xl font-bold mb-2 dark:text-gray-200">
              Prof
              <span className="text-blue-600 dark:text-blue-400">
                Assistant
              </span>
            </p>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              © 2025 ProfAssistant. {t("home.footer.rights")}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Home;
