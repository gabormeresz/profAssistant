import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { LessonPlan } from "../../types";
import { useExport } from "../../hooks";
import { lessonPlanToMarkdown } from "../../utils";

interface StructuredLessonPlanProps {
  lessonPlan: LessonPlan;
  courseTitle?: string;
  language?: string;
}

export function StructuredLessonPlan({
  lessonPlan,
  courseTitle,
  language
}: StructuredLessonPlanProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { exportToDocx } = useExport();

  const handleExport = async () => {
    const markdown = lessonPlanToMarkdown(lessonPlan);
    const filename = `class_${lessonPlan.class_number}_${lessonPlan.class_title
      .replace(/\s+/g, "_")
      .toLowerCase()}.docx`;
    await exportToDocx(markdown, { filename });
  };

  const handleCreatePresentation = () => {
    navigate("/presentation-generator", {
      state: {
        courseTitle,
        classNumber: lessonPlan.class_number,
        classTitle: lessonPlan.class_title,
        learningObjective: lessonPlan.learning_objective,
        keyPoints: lessonPlan.key_points,
        lessonBreakdown: lessonPlan.lesson_breakdown,
        activities: lessonPlan.activities,
        homework: lessonPlan.homework,
        extraActivities: lessonPlan.extra_activities,
        language
      }
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      {/* Lesson Header */}
      <div className="mb-8 border-b-2 border-green-500 pb-4">
        <div className="flex items-baseline gap-3 mb-2">
          <span className="text-sm font-semibold text-green-600 bg-green-50 px-3 py-1 rounded">
            {t("lessonPlanOutput.classNumber")} {lessonPlan.class_number}
          </span>
          <h1 className="text-3xl font-bold text-dark flex-1">
            {lessonPlan.class_title}
          </h1>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
            title={t("export.exportToDocx")}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {t("export.exportToDocx")}
          </button>
          <button
            onClick={handleCreatePresentation}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors flex items-center gap-2"
            title={t("export.createPresentationDraft")}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            {t("export.createPresentationDraft")}
          </button>
        </div>
      </div>

      {/* Learning Objective */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark mb-3">
          {t("lessonPlanOutput.learningObjective")}
        </h2>
        <p className="text-gray-700 bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
          {lessonPlan.learning_objective}
        </p>
      </div>

      {/* Key Points */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark mb-3">
          {t("lessonPlanOutput.keyPoints")}
        </h2>
        <ul className="space-y-2">
          {lessonPlan.key_points.map((point, idx) => (
            <li
              key={idx}
              className="flex items-start gap-3 text-gray-700 bg-gray-50 p-3 rounded"
            >
              <span className="text-green-600 font-bold mt-0.5">•</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Lesson Breakdown */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark mb-3">
          {t("lessonPlanOutput.lessonBreakdown")}
        </h2>
        <div className="space-y-4">
          {lessonPlan.lesson_breakdown.map((section, idx) => (
            <div
              key={idx}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <h3 className="text-lg font-semibold text-green-600 mb-2">
                {section.section_title}
              </h3>
              <p className="text-gray-700">{section.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Activities */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark mb-3">
          {t("lessonPlanOutput.activities")}
        </h2>
        <div className="space-y-4">
          {lessonPlan.activities.map((activity, idx) => (
            <div
              key={idx}
              className="bg-blue-50 border border-blue-200 rounded-lg p-4"
            >
              <h3 className="text-lg font-semibold text-blue-700 mb-2">
                {activity.name}
              </h3>
              <div className="mb-3">
                <span className="text-sm font-semibold text-gray-600">
                  {t("lessonPlanOutput.objective")}:{" "}
                </span>
                <span className="text-gray-700">{activity.objective}</span>
              </div>
              <div>
                <span className="text-sm font-semibold text-gray-600">
                  {t("lessonPlanOutput.instructions")}:{" "}
                </span>
                <p className="text-gray-700 mt-1">{activity.instructions}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Homework */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark mb-3">
          {t("lessonPlanOutput.homework")}
        </h2>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-gray-700">{lessonPlan.homework}</p>
        </div>
      </div>

      {/* Extra Activities */}
      <div>
        <h2 className="text-xl font-semibold text-dark mb-3">
          {t("lessonPlanOutput.extraActivities")}
        </h2>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <p className="text-gray-700">{lessonPlan.extra_activities}</p>
        </div>
      </div>
    </div>
  );
}
