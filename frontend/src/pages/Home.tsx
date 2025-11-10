import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Layout, LanguageSelector } from "../components";

function Home() {
  const { t } = useTranslation();

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-6">ProfAI</h1>
          <p className="text-lg text-gray-600 mb-8">{t("home.subtitle")}</p>

          <div className="max-w-md mx-auto mb-8">
            <LanguageSelector />
          </div>

          <div className="flex flex-col gap-4 max-w-md mx-auto">
            <Link
              to="/outline-generator"
              className="block px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-md"
            >
              📝 {t("home.courseOutlineGenerator")}
              <span className="block text-sm text-blue-100 mt-1">
                {t("home.courseOutlineGeneratorDescription")}
              </span>
            </Link>

            <div className="border-t border-gray-300 pt-6 mt-2">
              <Link
                to="/lesson-planner"
                className="block px-6 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium shadow-md"
              >
                📚 {t("home.lessonPlanner")}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default Home;
