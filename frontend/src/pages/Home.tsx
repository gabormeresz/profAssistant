import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageSelector } from "../components";
import {
  FileText,
  BookOpen,
  Presentation,
  ClipboardList,
  Users
} from "lucide-react";

function Home() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold">
              Prof<span className="text-blue-600">Assistant</span>
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-40">
              <LanguageSelector variant="header" />
            </div>
            <button className="px-4 py-2 text-gray-700 hover:text-gray-900 whitespace-nowrap h-10 flex items-center justify-center w-28">
              {t("home.login")}
            </button>
            <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap h-10 flex items-center justify-center w-32">
              {t("home.signup")}
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
              {t("home.hero.title")}
            </h2>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              {t("home.hero.subtitle")}
            </p>
            <button className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg">
              {t("home.hero.cta")}
            </button>
          </div>
          <div className="relative">
            <div className="bg-gray-200 rounded-2xl overflow-hidden shadow-xl aspect-[4/3] flex items-center justify-center">
              {/* Placeholder for hero image */}
              <div className="text-center text-gray-400">
                <Users className="w-24 h-24 mx-auto mb-4" strokeWidth={1.5} />
                <p className="text-sm">{t("home.hero.imagePlaceholder")}</p>
              </div>
            </div>
            {/* Decorative elements */}
            <div className="absolute -bottom-4 -right-4 w-32 h-32 opacity-20">
              <svg viewBox="0 0 100 100" className="text-blue-600 fill-current">
                <circle cx="10" cy="10" r="3" />
                <circle cx="30" cy="10" r="3" />
                <circle cx="50" cy="10" r="3" />
                <circle cx="70" cy="10" r="3" />
                <circle cx="90" cy="10" r="3" />
                <circle cx="10" cy="30" r="3" />
                <circle cx="30" cy="30" r="3" />
                <circle cx="50" cy="30" r="3" />
                <circle cx="70" cy="30" r="3" />
                <circle cx="90" cy="30" r="3" />
                <circle cx="10" cy="50" r="3" />
                <circle cx="30" cy="50" r="3" />
                <circle cx="50" cy="50" r="3" />
                <circle cx="70" cy="50" r="3" />
                <circle cx="90" cy="50" r="3" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <Link to="/outline-generator" className="group">
              <div className="bg-gray-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <FileText
                    className="w-6 h-6 text-blue-600 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {t("home.features.courseOutline.title")}
                </h3>
                <p className="text-gray-600 text-sm">
                  {t("home.features.courseOutline.description")}
                </p>
              </div>
            </Link>

            {/* Feature 2 */}
            <Link to="/lesson-planner" className="group">
              <div className="bg-gray-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <BookOpen
                    className="w-6 h-6 text-blue-600 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {t("home.features.lessonPlan.title")}
                </h3>
                <p className="text-gray-600 text-sm">
                  {t("home.features.lessonPlan.description")}
                </p>
              </div>
            </Link>

            {/* Feature 3 - Placeholder */}
            <div className="group cursor-pointer">
              <div className="bg-gray-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <Presentation
                    className="w-6 h-6 text-blue-600 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {t("home.features.presentation.title")}
                </h3>
                <p className="text-gray-600 text-sm">
                  {t("home.features.presentation.description")}
                </p>
              </div>
            </div>

            {/* Feature 4 - Placeholder */}
            <div className="group cursor-pointer">
              <div className="bg-gray-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <ClipboardList
                    className="w-6 h-6 text-blue-600 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {t("home.features.assessment.title")}
                </h3>
                <p className="text-gray-600 text-sm">
                  {t("home.features.assessment.description")}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-2xl font-bold mb-2">
              Prof<span className="text-blue-600">Assistant</span>
            </p>
            <p className="text-gray-600 text-sm">
              © 2025 ProfAssistant. {t("home.footer.rights")}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Home;
