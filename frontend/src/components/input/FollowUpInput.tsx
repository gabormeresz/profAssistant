import { useState } from "react";
import { Send } from "lucide-react";
import FileUpload from "./FileUpload";
import type { StreamingState } from "../../types";

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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="space-y-3">
        {/* Input area */}
        <div className="flex gap-2">
          {/* File upload button (compact) */}
          <FileUpload
            files={uploadedFiles}
            onFilesChange={setUploadedFiles}
            disabled={isDisabled}
            compact
          />

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
