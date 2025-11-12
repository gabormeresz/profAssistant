import { useTranslation } from "react-i18next";
import FileUpload from "./FileUpload";
import PromptEnhancer from "./PromptEnhancer";
import { COURSE_OUTLINE } from "../../utils/constants";

interface CourseOutlineInputSectionProps {
  userComment: string;
  setUserComment: (value: string) => void;
  topic: string;
  setTopic: (value: string) => void;
  numberOfClasses: number;
  setNumberOfClasses: (value: number) => void;
  language: string;
  setLanguage: (value: string) => void;
  onSubmit: () => void;
  threadId: string | null;
  uploadedFiles: File[];
  setUploadedFiles: (files: File[]) => void;
  onEnhancerLoadingChange?: (isLoading: boolean) => void;
}

export default function CourseOutlineInputSection({
  userComment,
  setUserComment,
  topic,
  setTopic,
  numberOfClasses,
  setNumberOfClasses,
  language,
  setLanguage,
  onSubmit,
  threadId,
  uploadedFiles,
  setUploadedFiles,
  onEnhancerLoadingChange
}: CourseOutlineInputSectionProps) {
  const { t } = useTranslation();
  const isButtonDisabled =
    !topic.trim() || numberOfClasses < COURSE_OUTLINE.MIN_CLASSES;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div className="space-y-4">
        {/* Topic Field */}
        <div>
          <label
            htmlFor="topic"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("courseOutline.topic")} <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder={t("courseOutline.topicPlaceholder")}
          />
        </div>

        {/* Number of Classes Field */}
        <div>
          <label
            htmlFor="numberOfClasses"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("courseOutline.numberOfClasses")}{" "}
            <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="numberOfClasses"
            min={COURSE_OUTLINE.MIN_CLASSES}
            max={COURSE_OUTLINE.MAX_CLASSES}
            value={numberOfClasses}
            onChange={(e) =>
              setNumberOfClasses(
                parseInt(e.target.value) || COURSE_OUTLINE.DEFAULT_CLASSES
              )
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="1"
          />
        </div>

        {/* Language Selection */}
        <div>
          <label
            htmlFor="language"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("courseOutline.language")}{" "}
            <span className="text-red-500">*</span>
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
          >
            <option value="English">English</option>
            <option value="Hungarian">Hungarian</option>
          </select>
        </div>

        {/* Message/Comment Field */}
        <div>
          <label
            htmlFor="userComment"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {t("courseOutline.userComment")}
          </label>
          <textarea
            id="userComment"
            value={userComment}
            onChange={(e) => setUserComment(e.target.value)}
            className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors"
            placeholder={t("courseOutline.userCommentPlaceholder")}
          />

          {/* Prompt Enhancer */}
          <PromptEnhancer
            message={userComment}
            contextType="course_outline"
            additionalContext={{
              topic: topic,
              num_classes: numberOfClasses
            }}
            language={language}
            onMessageChange={setUserComment}
            onLoadingChange={onEnhancerLoadingChange}
          />
        </div>

        {/* File Upload */}
        <FileUpload files={uploadedFiles} onFilesChange={setUploadedFiles} />
      </div>

      {/* Submit Button */}
      {!threadId && (
        <div className="flex justify-end mt-4">
          <button
            onClick={onSubmit}
            disabled={isButtonDisabled}
            className="px-6 py-3 rounded-lg font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:hover:bg-gray-400"
          >
            {t("courseOutline.generateOutline")}
          </button>
        </div>
      )}
    </div>
  );
}
