import { useState } from "react";
import { Send, X, Upload, File as FileIcon } from "lucide-react";
import { useTranslation } from "react-i18next";
import { formatFileSize } from "../../utils";
import type { StreamingState } from "../../types";

interface FollowUpInputProps {
  onSubmit: (message: string, files: File[]) => void;
  streamingState: StreamingState;
}

export default function FollowUpInput({
  onSubmit,
  streamingState
}: FollowUpInputProps) {
  const { t } = useTranslation();
  const [message, setMessage] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

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

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="space-y-3">
        {/* Uploaded files list - only shown when files exist */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            {uploadedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FileIcon className="h-4 w-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                  <span className="text-sm text-gray-700 dark:text-gray-300 truncate">
                    {file.name}
                  </span>
                  <span className="text-xs text-gray-500 flex-shrink-0">
                    ({formatFileSize(file.size)})
                  </span>
                </div>
                <button
                  onClick={() => {
                    const newFiles = uploadedFiles.filter(
                      (_, i) => i !== index
                    );
                    setUploadedFiles(newFiles);
                  }}
                  className="ml-2 p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors flex-shrink-0"
                  type="button"
                  disabled={isDisabled}
                >
                  <X className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input area */}
        <div className="flex gap-2">
          {/* File upload button */}
          <label className="cursor-pointer flex-shrink-0">
            <div className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <Upload className="h-5 w-5 text-gray-500 dark:text-gray-400" />
            </div>
            <input
              type="file"
              multiple
              onChange={(e) => {
                const fileList = e.target.files;
                if (fileList) {
                  const newFiles = Array.from(fileList);
                  setUploadedFiles([...uploadedFiles, ...newFiles]);
                }
                e.target.value = "";
              }}
              className="hidden"
              disabled={isDisabled}
            />
          </label>

          {/* Message textarea */}
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            placeholder={t("followUp.placeholder")}
            rows={2}
          />

          {/* Send button */}
          <button
            onClick={handleSubmit}
            disabled={
              isDisabled || (!message.trim() && uploadedFiles.length === 0)
            }
            className="flex-shrink-0 px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-400 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="h-5 w-5" />
            <span className="hidden sm:inline">{t("followUp.send")}</span>
          </button>
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400">
          {t("followUp.sendHint")}
        </p>
      </div>
    </div>
  );
}
