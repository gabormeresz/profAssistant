import { useState } from "react";
import { Upload, File, X, Send } from "lucide-react";
import type { StreamingState } from "../hooks/useSSE";

interface FollowUpInputProps {
  onSubmit: (message: string, files: File[]) => void;
  streamingState: StreamingState;
}

export default function FollowUpInput({
  onSubmit,
  streamingState
}: FollowUpInputProps) {
  const [message, setMessage] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploadError, setUploadError] = useState<string>("");

  const isDisabled = streamingState !== "idle" && streamingState !== "complete";

  const handleSubmit = () => {
    if (message.trim() || uploadedFiles.length > 0) {
      onSubmit(message, uploadedFiles);
      setMessage("");
      setUploadedFiles([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="space-y-3">
        {/* Uploaded files list (show above input) */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            {uploadedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <File className="h-4 w-4 text-gray-400 flex-shrink-0" />
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

        {/* Error message */}
        {uploadError && <p className="text-sm text-red-600">{uploadError}</p>}

        {/* Input area */}
        <div className="flex gap-2">
          {/* File upload button */}
          <label className="cursor-pointer flex-shrink-0">
            <div className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Upload className="h-5 w-5 text-gray-500" />
            </div>
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              className="hidden"
              accept=".txt,.pdf,.docx,.md,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              disabled={isDisabled}
            />
          </label>

          {/* Message textarea */}
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Type your follow-up message... (Shift+Enter for new line)"
            rows={2}
          />

          {/* Send button */}
          <button
            onClick={handleSubmit}
            disabled={
              isDisabled || (!message.trim() && uploadedFiles.length === 0)
            }
            className="flex-shrink-0 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="h-5 w-5" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>

        <p className="text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
