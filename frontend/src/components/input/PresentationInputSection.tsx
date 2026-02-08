import type { Dispatch, SetStateAction } from "react";
import { useTranslation } from "react-i18next";
import FileUpload from "./FileUpload";
import PromptEnhancer from "./PromptEnhancer";
import { PRESENTATION } from "../../utils/constants";

interface PresentationInputSectionProps {
  courseTitle: string;
  setCourseTitle: Dispatch<SetStateAction<string>>;
  classNumber: number;
  setClassNumber: Dispatch<SetStateAction<number>>;
  classTitle: string;
  setClassTitle: Dispatch<SetStateAction<string>>;
  learningObjective: string;
  setLearningObjective: Dispatch<SetStateAction<string>>;
  keyPoints: string[];
  setKeyPoints: Dispatch<SetStateAction<string[]>>;
  lessonBreakdown: string;
  setLessonBreakdown: Dispatch<SetStateAction<string>>;
  activities: string;
  setActivities: Dispatch<SetStateAction<string>>;
  homework: string;
  setHomework: Dispatch<SetStateAction<string>>;
  extraActivities: string;
  setExtraActivities: Dispatch<SetStateAction<string>>;
  userComment: string;
  setUserComment: Dispatch<SetStateAction<string>>;
  uploadedFiles: File[];
  setUploadedFiles: Dispatch<SetStateAction<File[]>>;
  language: string;
  setLanguage: Dispatch<SetStateAction<string>>;
  onSubmit: () => void;
  threadId: string | null;
  onEnhancerLoadingChange?: (isLoading: boolean) => void;
  displayFiles?: Array<{ name: string }>;
}

export function PresentationInputSection({
  courseTitle,
  setCourseTitle,
  classNumber,
  setClassNumber,
  classTitle,
  setClassTitle,
  learningObjective,
  setLearningObjective,
  keyPoints,
  setKeyPoints,
  lessonBreakdown,
  setLessonBreakdown,
  activities,
  setActivities,
  homework,
  setHomework,
  extraActivities,
  setExtraActivities,
  userComment,
  setUserComment,
  uploadedFiles,
  setUploadedFiles,
  language,
  setLanguage,
  onSubmit,
  threadId,
  onEnhancerLoadingChange,
  displayFiles
}: PresentationInputSectionProps) {
  const { t } = useTranslation();

  const isButtonDisabled =
    !courseTitle.trim() ||
    !classTitle.trim() ||
    classNumber < PRESENTATION.MIN_CLASS_NUMBER;

  // Helper functions for key points array
  const handleKeyPointChange = (index: number, value: string) => {
    const newKeyPoints = [...keyPoints];
    newKeyPoints[index] = value;
    setKeyPoints(newKeyPoints);
  };

  const addKeyPoint = () => {
    setKeyPoints([...keyPoints, ""]);
  };

  const removeKeyPoint = (index: number) => {
    if (keyPoints.length > 1) {
      setKeyPoints(keyPoints.filter((_, i) => i !== index));
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div className="space-y-4">
        {/* Course Title */}
        <div className="mb-6">
          <label
            htmlFor="courseTitle"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.courseTitle")}{" "}
            <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="courseTitle"
            value={courseTitle}
            onChange={(e) => setCourseTitle(e.target.value)}
            placeholder={t("presentation.courseTitlePlaceholder")}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Class Number and Title */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label
              htmlFor="classNumber"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              {t("presentation.classNumber")}{" "}
              <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              id="classNumber"
              value={classNumber}
              onChange={(e) => setClassNumber(Number(e.target.value))}
              min={PRESENTATION.MIN_CLASS_NUMBER}
              max={PRESENTATION.MAX_CLASS_NUMBER}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="md:col-span-3">
            <label
              htmlFor="classTitle"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              {t("presentation.classTitle")}{" "}
              <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="classTitle"
              value={classTitle}
              onChange={(e) => setClassTitle(e.target.value)}
              placeholder={t("presentation.classTitlePlaceholder")}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Language Selection */}
        <div className="mb-6">
          <label
            htmlFor="language"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.language")} <span className="text-red-500">*</span>
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="English">English</option>
            <option value="Hungarian">Hungarian</option>
          </select>
        </div>

        {/* Learning Objective */}
        <div className="mb-6">
          <label
            htmlFor="learningObjective"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.learningObjective")}
          </label>
          <textarea
            id="learningObjective"
            value={learningObjective}
            onChange={(e) => setLearningObjective(e.target.value)}
            placeholder={t("presentation.learningObjectivePlaceholder")}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>

        {/* Key Points */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700">
              {t("presentation.keyPoints")}
            </label>
            {keyPoints.length < PRESENTATION.MAX_KEY_POINTS && (
              <button
                type="button"
                onClick={addKeyPoint}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                {t("presentation.addKeyPoint")}
              </button>
            )}
          </div>
          <div className="space-y-2">
            {keyPoints.map((point, index) => (
              <div key={index} className="flex gap-2">
                <textarea
                  value={point}
                  onChange={(e) => handleKeyPointChange(index, e.target.value)}
                  placeholder={t("presentation.keyPointsPlaceholder")}
                  rows={2}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
                {keyPoints.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeKeyPoint(index)}
                    className="px-3 py-2 text-red-600 hover:text-red-700 font-medium"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Lesson Breakdown */}
        <div className="mb-6">
          <label
            htmlFor="lessonBreakdown"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.lessonBreakdown")}
          </label>
          <textarea
            id="lessonBreakdown"
            value={lessonBreakdown}
            onChange={(e) => setLessonBreakdown(e.target.value)}
            placeholder={t("presentation.lessonBreakdownPlaceholder")}
            rows={6}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>

        {/* Activities */}
        <div className="mb-6">
          <label
            htmlFor="activities"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.activities")}
          </label>
          <textarea
            id="activities"
            value={activities}
            onChange={(e) => setActivities(e.target.value)}
            placeholder={t("presentation.activitiesPlaceholder")}
            rows={6}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>

        {/* Homework */}
        <div className="mb-6">
          <label
            htmlFor="homework"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.homework")}
          </label>
          <textarea
            id="homework"
            value={homework}
            onChange={(e) => setHomework(e.target.value)}
            placeholder={t("presentation.homeworkPlaceholder")}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>

        {/* Extra Activities */}
        <div className="mb-6">
          <label
            htmlFor="extraActivities"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.extraActivities")}
          </label>
          <textarea
            id="extraActivities"
            value={extraActivities}
            onChange={(e) => setExtraActivities(e.target.value)}
            placeholder={t("presentation.extraActivitiesPlaceholder")}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>

        {/* Additional Instructions */}
        <div className="mb-6">
          <label
            htmlFor="userComment"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("presentation.userComment")}
          </label>
          <textarea
            id="userComment"
            value={userComment}
            onChange={(e) => setUserComment(e.target.value)}
            placeholder={t("presentation.userCommentPlaceholder")}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />

          {/* Prompt Enhancer */}
          <PromptEnhancer
            message={userComment}
            contextType="presentation"
            additionalContext={{
              topic: courseTitle,
              class_title: classTitle,
              learning_objective: learningObjective,
              key_points: keyPoints.filter((kp) => kp.trim()),
              lesson_breakdown: lessonBreakdown,
              activities,
              homework,
              extra_activities: extraActivities
            }}
            language={language}
            onMessageChange={setUserComment}
            onLoadingChange={onEnhancerLoadingChange}
          />
        </div>

        {/* File Upload */}
        <div className="mb-6">
          <FileUpload
            files={uploadedFiles}
            onFilesChange={setUploadedFiles}
            displayOnly={threadId !== null}
            displayFiles={displayFiles}
          />
        </div>
      </div>

      {/* Submit Button */}
      {!threadId && (
        <div className="flex justify-end">
          <button
            onClick={onSubmit}
            disabled={isButtonDisabled}
            className="px-6 py-3 rounded-lg font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:hover:bg-gray-400"
          >
            {t("presentation.generatePresentation")}
          </button>
        </div>
      )}
    </div>
  );
}
