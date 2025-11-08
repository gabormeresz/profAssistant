import type { LessonPlan } from "../../types";

interface StructuredLessonPlanProps {
  lessonPlan: LessonPlan;
}

export function StructuredLessonPlan({
  lessonPlan
}: StructuredLessonPlanProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      {/* Lesson Header */}
      <div className="mb-8 border-b-2 border-green-500 pb-4">
        <div className="flex items-baseline gap-3 mb-2">
          <span className="text-sm font-semibold text-green-600 bg-green-50 px-3 py-1 rounded">
            Class {lessonPlan.class_number}
          </span>
          <h1 className="text-3xl font-bold text-gray-900">
            {lessonPlan.class_title}
          </h1>
        </div>
      </div>

      {/* Learning Objective */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          Learning Objective
        </h2>
        <p className="text-gray-700 bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
          {lessonPlan.learning_objective}
        </p>
      </div>

      {/* Key Points */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Key Points</h2>
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
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          Lesson Breakdown
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
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Activities</h2>
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
                  Objective:{" "}
                </span>
                <span className="text-gray-700">{activity.objective}</span>
              </div>
              <div>
                <span className="text-sm font-semibold text-gray-600">
                  Instructions:{" "}
                </span>
                <p className="text-gray-700 mt-1">{activity.instructions}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Homework */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Homework</h2>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-gray-700">{lessonPlan.homework}</p>
        </div>
      </div>

      {/* Extra Activities */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          Extra Activities
        </h2>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <p className="text-gray-700">{lessonPlan.extra_activities}</p>
        </div>
      </div>
    </div>
  );
}
