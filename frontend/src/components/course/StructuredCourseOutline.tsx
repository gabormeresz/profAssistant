import type { CourseOutline } from "../../types";

interface StructuredCourseOutlineProps {
  outline: CourseOutline;
}

export function StructuredCourseOutline({
  outline
}: StructuredCourseOutlineProps) {
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
              <h2 className="text-2xl font-semibold text-gray-800">
                {courseClass.class_title}
              </h2>
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
