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
  setUploadedFiles
}: CourseOutlineInputSectionProps) {
  const isSessionActive = threadId !== null;
  const isButtonDisabled =
    !topic.trim() || numberOfClasses < COURSE_OUTLINE.MIN_CLASSES;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div className="space-y-4">
        {/* Topic Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Topic / Subject
            {isSessionActive && (
              <span className="ml-2 text-xs text-gray-500">
                (locked for this conversation)
              </span>
            )}
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={isSessionActive}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            placeholder="e.g., Mathematics, History, Science..."
          />
        </div>

        {/* Number of Classes Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Classes
            {isSessionActive && (
              <span className="ml-2 text-xs text-gray-500">
                (locked for this conversation, ask in comment to add or remove
                classes)
              </span>
            )}
          </label>
          <input
            type="number"
            min={COURSE_OUTLINE.MIN_CLASSES}
            max={COURSE_OUTLINE.MAX_CLASSES}
            value={numberOfClasses}
            onChange={(e) =>
              setNumberOfClasses(
                parseInt(e.target.value) || COURSE_OUTLINE.DEFAULT_CLASSES
              )
            }
            disabled={isSessionActive}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            placeholder="1"
          />
        </div>

        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Language
            {isSessionActive && (
              <span className="ml-2 text-xs text-gray-500">
                (locked for this conversation)
              </span>
            )}
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isSessionActive}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
          >
            <option value="English">English</option>
            <option value="Hungarian">Hungarian</option>
          </select>
        </div>

        {/* Message/Comment Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your comment
          </label>
          <textarea
            value={userComment}
            onChange={(e) => setUserComment(e.target.value)}
            className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors"
            placeholder="Add any additional context or requirements..."
          />

          {/* Prompt Enhancer */}
          <PromptEnhancer
            message={userComment}
            contextType="course_outline"
            additionalContext={{
              topic: topic,
              num_classes: numberOfClasses
            }}
            onMessageChange={setUserComment}
          />
        </div>

        {/* File Upload */}
        <FileUpload
          files={uploadedFiles}
          onFilesChange={setUploadedFiles}
          disabled={isSessionActive}
        />
      </div>

      {/* Submit Button */}
      {!isSessionActive && (
        <div className="flex justify-end mt-4">
          <button
            onClick={onSubmit}
            disabled={isButtonDisabled}
            className="px-6 py-3 rounded-lg font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:hover:bg-gray-400"
          >
            Generate Course Outline
          </button>
        </div>
      )}
    </div>
  );
}
