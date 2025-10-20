import type { StreamingState } from "../hooks/useSSE";
import { useState } from "react";

interface InputSectionProps {
  userComment: string;
  setUserComment: (value: string) => void;
  topic: string;
  setTopic: (value: string) => void;
  numberOfClasses: number;
  setNumberOfClasses: (value: number) => void;
  onSubmit: () => void;
  streamingState: StreamingState;
  threadId: string | null;
  uploadedFiles: File[];
  setUploadedFiles: (files: File[]) => void;
}

export default function InputSection({
  userComment,
  setUserComment,
  topic,
  setTopic,
  numberOfClasses,
  setNumberOfClasses,
  onSubmit,
  streamingState,
  threadId,
  uploadedFiles,
  setUploadedFiles
}: InputSectionProps) {
  const [uploadError, setUploadError] = useState<string>("");

  // Button should be disabled if we're connecting, streaming, or input is empty
  const isDisabled = streamingState !== "idle" && streamingState !== "complete";

  // Disable topic and numberOfClasses after first submit (when thread exists)
  const isSessionActive = threadId !== null;

  // Dynamic button text based on streaming state
  const getButtonText = () => {
    switch (streamingState) {
      case "connecting":
        return "Connecting...";
      case "streaming":
        return "Generating...";
      case "complete":
        return "Add New Comment";
      case "idle":
      default:
        return "Generate Course Outline";
    }
  };

  // Handle file upload
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const validFiles: File[] = [];
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      "text/plain",
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/markdown"
    ];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      if (file.size > maxSize) {
        setUploadError(`File ${file.name} is too large. Max size is 10MB.`);
        continue;
      }

      if (
        !allowedTypes.includes(file.type) &&
        !file.name.endsWith(".md") &&
        !file.name.endsWith(".txt")
      ) {
        setUploadError(
          `File ${file.name} type not supported. Allowed: PDF, DOCX, TXT, MD`
        );
        continue;
      }

      validFiles.push(file);
    }

    if (validFiles.length > 0) {
      setUploadedFiles([...uploadedFiles, ...validFiles]);
      setUploadError("");
    }
  };

  // Remove file from upload list
  const removeFile = (index: number) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);
  };

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
            min="1"
            max="20"
            value={numberOfClasses}
            onChange={(e) => setNumberOfClasses(parseInt(e.target.value) || 1)}
            disabled={isSessionActive}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            placeholder="1"
          />
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
        </div>

        {/* File Upload Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Reference Materials (Optional)
          </label>
          <div className="flex items-center gap-3">
            <label className="flex-1 cursor-pointer">
              <div className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 transition-colors text-center">
                <svg
                  className="mx-auto h-8 w-8 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                  aria-hidden="true"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <p className="mt-1 text-sm text-gray-500">
                  Click to upload or drag files here
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  PDF, DOCX, TXT, MD (max 10MB each)
                </p>
              </div>
              <input
                type="file"
                multiple
                onChange={handleFileChange}
                className="hidden"
                accept=".txt,.pdf,.docx,.md,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              />
            </label>
          </div>

          {/* Error message */}
          {uploadError && (
            <p className="text-sm text-red-600 mt-2">{uploadError}</p>
          )}

          {/* Uploaded files list */}
          {uploadedFiles.length > 0 && (
            <div className="mt-3 space-y-2">
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <svg
                      className="h-5 w-5 text-gray-400 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <span className="text-sm text-gray-700 truncate">
                      {file.name}
                    </span>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="ml-2 p-1 hover:bg-gray-200 rounded transition-colors flex-shrink-0"
                    type="button"
                  >
                    <svg
                      className="h-4 w-4 text-gray-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end mt-4">
        <button
          onClick={onSubmit}
          disabled={isDisabled}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            streamingState === "complete"
              ? "bg-green-600 text-white hover:bg-green-700"
              : "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          }`}
        >
          {getButtonText()}
        </button>
      </div>
    </div>
  );
}
