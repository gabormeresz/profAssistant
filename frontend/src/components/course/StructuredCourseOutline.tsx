import { useNavigate } from "react-router-dom";
import type { CourseOutline } from "../../types";

interface StructuredCourseOutlineProps {
  outline: CourseOutline;
}

export function StructuredCourseOutline({
  outline
}: StructuredCourseOutlineProps) {
  const navigate = useNavigate();

  const handleCreateLessonPlan = (courseClass: typeof outline.classes[0]) => {
    navigate("/lesson-planner", {
      state: {
        courseTitle: outline.course_title,
        classNumber: courseClass.class_number,
        classTitle: courseClass.class_title,
        learningObjectives: courseClass.learning_objectives,
        keyTopics: courseClass.key_topics,
        activitiesProjects: courseClass.activities_projects
      }
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      {/* Course Title */}
      <h1 className="text-3xl font-bold text-gray-900 mb-8 border-b-2 border-blue-500 pb-3">
        {outline.course_title}
      </h1>

      {/* Classes */}
      <div className="space-y-8">
        {outline.classes.map((courseClass) => (
          <div
            key={courseClass.class_number}
            className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
          >
            {/* Class Header */}
            <div className="flex items-baseline gap-3 mb-4">
              <span className="text-sm font-semibold text-blue-600 bg-blue-50 px-3 py-1 rounded">
                Class {courseClass.class_number}
              </span>
              <h2 className="text-2xl font-semibold text-gray-800 flex-1">
                {courseClass.class_title}
              </h2>
              <button
                onClick={() => handleCreateLessonPlan(courseClass)}
                className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors flex items-center gap-2"
                title="Create a detailed lesson plan for this class"
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
                Create Lesson Plan
              </button>
            </div>

            {/* Learning Objectives */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                Learning Objectives
              </h3>
              <ul className="list-disc list-inside space-y-1 text-gray-600">
                {courseClass.learning_objectives.map((objective, idx) => (
                  <li key={idx} className="ml-2">
                    {objective}
                  </li>
                ))}
              </ul>
            </div>

            {/* Key Topics */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                Key Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                {courseClass.key_topics.map((topic, idx) => (
                  <span
                    key={idx}
                    className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>

            {/* Activities & Projects */}
            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                Activities & Projects
              </h3>
              <ul className="list-disc list-inside space-y-1 text-gray-600">
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
