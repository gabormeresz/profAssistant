import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { CourseOutline } from "../../types";
import { useExport } from "../../hooks";
import { courseOutlineToMarkdown } from "../../utils";

interface StructuredCourseOutlineProps {
  outline: CourseOutline;
  language?: string;
}

export function StructuredCourseOutline({
  outline,
  language
}: StructuredCourseOutlineProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { exportToDocx } = useExport();

  const handleExport = async () => {
    const markdown = courseOutlineToMarkdown(outline);
    const filename = `${outline.course_title
      .replace(/\s+/g, "_")
      .toLowerCase()}_outline.docx`;
    await exportToDocx(markdown, { filename });
  };

  const handleCreateLessonPlan = (courseClass: (typeof outline.classes)[0]) => {
    navigate("/lesson-plan-generator", {
      state: {
        courseTitle: outline.course_title,
        classNumber: courseClass.class_number,
        classTitle: courseClass.class_title,
        learningObjectives: courseClass.learning_objectives,
        keyTopics: courseClass.key_topics,
        activitiesProjects: courseClass.activities_projects,
        language: language
      }
    });
  };

  const handleCreateAssessment = () => {
    // Collect all key_topics from every class into a single flat array
    const allTopics = outline.classes.flatMap((c) => c.key_topics);
    navigate("/assessment-generator", {
      state: {
        courseTitle: outline.course_title,
        keyTopics: allTopics,
        language: language
      }
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
      {/* Course Title */}
      <div className="border-b-2 border-blue-500 dark:border-blue-400 pb-3 mb-8">
        <div className="flex items-baseline gap-3">
          <h1 className="text-3xl font-bold text-dark flex-1">
            {outline.course_title}
          </h1>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white text-sm font-medium rounded-md hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors flex items-center gap-2"
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
            onClick={handleCreateAssessment}
            className="px-4 py-2 bg-amber-600 dark:bg-amber-500 text-white text-sm font-medium rounded-md hover:bg-amber-700 dark:hover:bg-amber-400 transition-colors flex items-center gap-2"
            title={t("export.createAssessmentFromCourse")}
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
            {t("export.createAssessmentFromCourse")}
          </button>
        </div>
      </div>

      {/* Classes */}
      <div className="space-y-8">
        {outline.classes.map((courseClass) => (
          <div
            key={courseClass.class_number}
            className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-lg transition-shadow"
          >
            {/* Class Header */}
            <div className="flex items-baseline gap-3 mb-4">
              <span className="text-sm font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/40 px-3 py-1 rounded">
                {t("lessonPlanOutput.classNumber")} {courseClass.class_number}
              </span>
              <h2 className="text-2xl font-semibold text-dark flex-1">
                {courseClass.class_title}
              </h2>
              <button
                onClick={() => handleCreateLessonPlan(courseClass)}
                className="px-4 py-2 bg-green-600 dark:bg-green-500 text-white text-sm font-medium rounded-md hover:bg-green-700 dark:hover:bg-green-400 transition-colors flex items-center gap-2"
                title={t("export.createLessonPlanDraft")}
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
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                {t("export.createLessonPlanDraft")}
              </button>
            </div>

            {/* Learning Objectives */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                {t("courseOutline.learningObjectives")}
              </h3>
              <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                {courseClass.learning_objectives.map((objective, idx) => (
                  <li key={idx} className="ml-2">
                    {objective}
                  </li>
                ))}
              </ul>
            </div>

            {/* Key Topics */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                {t("courseOutline.keyTopics")}
              </h3>
              <div className="flex flex-wrap gap-2">
                {courseClass.key_topics.map((topic, idx) => (
                  <span
                    key={idx}
                    className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full text-sm"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>

            {/* Activities & Projects */}
            <div>
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                {t("courseOutline.activitiesProjects")}
              </h3>
              <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                {courseClass.activities_projects.map((activity, idx) => (
                  <li key={idx} className="ml-2">
                    {activity}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
