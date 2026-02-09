import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Layout } from "../components";
import { FileText, BookOpen, Presentation, ClipboardList } from "lucide-react";

const features = [
  {
    to: "/course-outline-generator",
    icon: FileText,
    titleKey: "home.features.courseOutline.title",
    descKey: "home.features.courseOutline.description"
  },
  {
    to: "/lesson-plan-generator",
    icon: BookOpen,
    titleKey: "home.features.lessonPlan.title",
    descKey: "home.features.lessonPlan.description"
  },
  {
    to: "/presentation-generator",
    icon: Presentation,
    titleKey: "home.features.presentation.title",
    descKey: "home.features.presentation.description"
  },
  {
    to: "/assessment-generator",
    icon: ClipboardList,
    titleKey: "home.features.assessment.title",
    descKey: "home.features.assessment.description"
  }
];

function AppPage() {
  const { t } = useTranslation();

  return (
    <Layout showSidebar>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-200 mb-3">
            {t("app.welcome")}
          </h2>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            {t("app.welcomeSubtitle")}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-6">
          {features.map(({ to, icon: Icon, titleKey, descKey }) => (
            <Link key={to} to={to} className="group">
              <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 hover:shadow-lg transition-shadow h-full">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <Icon
                    className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white"
                    strokeWidth={2}
                  />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2">
                  {t(titleKey)}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {t(descKey)}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  );
}

export default AppPage;
