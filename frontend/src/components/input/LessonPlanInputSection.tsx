import type { Dispatch, SetStateAction } from "react";
import FileUpload from "./FileUpload";
import PromptEnhancer from "./PromptEnhancer";
import { LESSON_PLAN } from "../../utils/constants";

interface LessonPlanInputSectionProps {
  courseTitle: string;
  setCourseTitle: Dispatch<SetStateAction<string>>;
  classNumber: number;
  setClassNumber: Dispatch<SetStateAction<number>>;
  classTitle: string;
  setClassTitle: Dispatch<SetStateAction<string>>;
  learningObjectives: string[];
  setLearningObjectives: Dispatch<SetStateAction<string[]>>;
  keyTopics: string[];
  setKeyTopics: Dispatch<SetStateAction<string[]>>;
  activitiesProjects: string[];
  setActivitiesProjects: Dispatch<SetStateAction<string[]>>;
  userComment: string;
  setUserComment: Dispatch<SetStateAction<string>>;
  uploadedFiles: File[];
  setUploadedFiles: Dispatch<SetStateAction<File[]>>;
  onSubmit: () => void;
  threadId: string | null;
}

export function LessonPlanInputSection({
  courseTitle,
  setCourseTitle,
  classNumber,
  setClassNumber,
  classTitle,
  setClassTitle,
  learningObjectives,
  setLearningObjectives,
  keyTopics,
  setKeyTopics,
  activitiesProjects,
  setActivitiesProjects,
  userComment,
  setUserComment,
  uploadedFiles,
  setUploadedFiles,
  onSubmit,
  threadId
}: LessonPlanInputSectionProps) {
  // Helper functions to manage array fields
  const handleArrayChange = (
    index: number,
    value: string,
    array: string[],
    setter: Dispatch<SetStateAction<string[]>>
  ) => {
    const newArray = [...array];
    newArray[index] = value;
    setter(newArray);
  };

  const addArrayItem = (
    array: string[],
    setter: Dispatch<SetStateAction<string[]>>
  ) => {
    setter([...array, ""]);
  };

  const removeArrayItem = (
    index: number,
    array: string[],
    setter: Dispatch<SetStateAction<string[]>>
  ) => {
    if (array.length > 1) {
      setter(array.filter((_, i) => i !== index));
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Lesson Plan Details
      </h2>

      {/* Course Title */}
      <div className="mb-6">
        <label
          htmlFor="courseTitle"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Course Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="courseTitle"
          value={courseTitle}
          onChange={(e) => setCourseTitle(e.target.value)}
          placeholder="e.g., Introduction to Web Development"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {/* Class Number and Title in a grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <label
            htmlFor="classNumber"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Class # <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="classNumber"
            value={classNumber}
            onChange={(e) => setClassNumber(Number(e.target.value))}
            min={LESSON_PLAN.MIN_CLASS_NUMBER}
            max={LESSON_PLAN.MAX_CLASS_NUMBER}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>

        <div className="md:col-span-3">
          <label
            htmlFor="classTitle"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Class Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="classTitle"
            value={classTitle}
            onChange={(e) => setClassTitle(e.target.value)}
            placeholder="e.g., Introduction to HTML and CSS Basics"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Learning Objectives */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">
            Learning Objectives
          </label>
          {learningObjectives.length < LESSON_PLAN.MAX_OBJECTIVES && (
            <button
              type="button"
              onClick={() =>
                addArrayItem(learningObjectives, setLearningObjectives)
              }
              className="text-sm text-green-600 hover:text-green-700 font-medium"
            >
              + Add Objective
            </button>
          )}
        </div>
        <div className="space-y-2">
          {learningObjectives.map((objective, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={objective}
                onChange={(e) =>
                  handleArrayChange(
                    index,
                    e.target.value,
                    learningObjectives,
                    setLearningObjectives
                  )
                }
                placeholder={`Learning objective ${index + 1}`}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
              {learningObjectives.length > LESSON_PLAN.MIN_OBJECTIVES && (
                <button
                  type="button"
                  onClick={() =>
                    removeArrayItem(
                      index,
                      learningObjectives,
                      setLearningObjectives
                    )
                  }
                  className="px-3 py-2 text-red-600 hover:text-red-700 font-medium"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Key Topics */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">
            Key Topics
          </label>
          {keyTopics.length < LESSON_PLAN.MAX_TOPICS && (
            <button
              type="button"
              onClick={() => addArrayItem(keyTopics, setKeyTopics)}
              className="text-sm text-green-600 hover:text-green-700 font-medium"
            >
              + Add Topic
            </button>
          )}
        </div>
        <div className="space-y-2">
          {keyTopics.map((topic, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={topic}
                onChange={(e) =>
                  handleArrayChange(
                    index,
                    e.target.value,
                    keyTopics,
                    setKeyTopics
                  )
                }
                placeholder={`Key topic ${index + 1}`}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
              {keyTopics.length > LESSON_PLAN.MIN_TOPICS && (
                <button
                  type="button"
                  onClick={() =>
                    removeArrayItem(index, keyTopics, setKeyTopics)
                  }
                  className="px-3 py-2 text-red-600 hover:text-red-700 font-medium"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Activities & Projects */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">
            Activities & Projects
          </label>
          {activitiesProjects.length < LESSON_PLAN.MAX_ACTIVITIES && (
            <button
              type="button"
              onClick={() =>
                addArrayItem(activitiesProjects, setActivitiesProjects)
              }
              className="text-sm text-green-600 hover:text-green-700 font-medium"
            >
              + Add Activity
            </button>
          )}
        </div>
        <div className="space-y-2">
          {activitiesProjects.map((activity, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={activity}
                onChange={(e) =>
                  handleArrayChange(
                    index,
                    e.target.value,
                    activitiesProjects,
                    setActivitiesProjects
                  )
                }
                placeholder={`Activity ${index + 1}`}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
              {activitiesProjects.length > LESSON_PLAN.MIN_ACTIVITIES && (
                <button
                  type="button"
                  onClick={() =>
                    removeArrayItem(
                      index,
                      activitiesProjects,
                      setActivitiesProjects
                    )
                  }
                  className="px-3 py-2 text-red-600 hover:text-red-700 font-medium"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Additional Instructions */}
      <div className="mb-6">
        <label
          htmlFor="userComment"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Additional Instructions (Optional)
        </label>
        <textarea
          id="userComment"
          value={userComment}
          onChange={(e) => setUserComment(e.target.value)}
          placeholder="Any special requirements, teaching methods, or additional context..."
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
        />

        {/* Prompt Enhancer */}
        <PromptEnhancer
          message={userComment}
          contextType="lesson_plan"
          additionalContext={{
            topic: courseTitle,
            class_title: classTitle,
            learning_objectives: learningObjectives.filter((obj) => obj.trim()),
            key_topics: keyTopics.filter((topic) => topic.trim()),
            activities_projects: activitiesProjects.filter((act) => act.trim())
          }}
          onMessageChange={setUserComment}
        />
      </div>

      {/* File Upload */}
      <div className="mb-6">
        <FileUpload files={uploadedFiles} onFilesChange={setUploadedFiles} />
      </div>

      {/* Submit Button */}
      {!threadId && (
        <div className="flex justify-end">
          <button
            onClick={onSubmit}
            className="px-6 py-3 rounded-md font-medium transition-colors bg-green-600 text-white hover:bg-green-700"
          >
            Generate Lesson Plan
          </button>
        </div>
      )}
    </div>
  );
}
