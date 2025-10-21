import { useState } from "react";
import { Upload, File, X, Sparkles } from "lucide-react";

interface InputSectionProps {
  userComment: string;
  setUserComment: (value: string) => void;
  topic: string;
  setTopic: (value: string) => void;
  numberOfClasses: number;
  setNumberOfClasses: (value: number) => void;
  onSubmit: () => void;
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
  threadId,
  uploadedFiles,
  setUploadedFiles
}: InputSectionProps) {
  const [uploadError, setUploadError] = useState<string>("");
  const [isEnhancing, setIsEnhancing] = useState<boolean>(false);
  const [enhanceError, setEnhanceError] = useState<string>("");

  // Disable topic and numberOfClasses after first submit (when thread exists)
  const isSessionActive = threadId !== null;

  // Disable button if required fields are empty
  const isButtonDisabled = !topic.trim() || numberOfClasses < 1;

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

  // Handle prompt enhancement
  const handleEnhancePrompt = async () => {
    setIsEnhancing(true);
    setEnhanceError("");

    try {
      const formData = new FormData();
      formData.append("message", userComment);
      formData.append("topic", topic);
      formData.append("num_classes", numberOfClasses.toString());

      const response = await fetch("http://localhost:8000/enhance-prompt", {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        setEnhanceError(data.error || "Failed to enhance prompt");
        return;
      }

      if (data.enhanced_prompt) {
        setUserComment(data.enhanced_prompt);
      }
    } catch (error) {
      setEnhanceError(
        error instanceof Error ? error.message : "Failed to enhance prompt"
      );
    } finally {
      setIsEnhancing(false);
    }
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

          {/* Enhance Prompt Button */}
          <div className="mt-2 flex items-start gap-2">
            <button
              type="button"
              onClick={handleEnhancePrompt}
              disabled={
                isEnhancing || userComment.trim().length < 5 || !topic.trim()
              }
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="h-4 w-4" />
              {isEnhancing ? "Enhancing..." : "Enhance Prompt"}
            </button>
            {enhanceError && (
              <p className="text-sm text-red-600 mt-1">{enhanceError}</p>
            )}
          </div>
        </div>

        {/* File Upload Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Reference Materials (Optional)
          </label>
          <div className="flex items-center gap-3">
            <label className="flex-1 cursor-pointer">
              <div className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 transition-colors text-center">
                <Upload className="mx-auto h-8 w-8 text-gray-400" />
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
                    <File className="h-5 w-5 text-gray-400 flex-shrink-0" />
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
                    <X className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Hide button after first submission */}
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
