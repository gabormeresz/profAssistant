import { File, User } from "lucide-react";
import type { ConversationMessage } from "../../types";

interface UserMessageProps {
  message: ConversationMessage;
}

export default function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex gap-4 flex-row-reverse">
      {/* Avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-blue-600">
        <User className="h-5 w-5 text-white" />
      </div>

      {/* Message Content */}
      <div className="flex-1 text-right text-m">
        <div className="inline-block max-w-[85%] rounded-lg p-4 bg-blue-600 text-white">
          {/* Message content */}
          {message.content && (
            <div>
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
          )}

          {/* Uploaded files */}
          {message.files && message.files.length > 0 && (
            <div className="mt-3 pt-3 border-t border-blue-400">
              <div className="mb-2 font-bold">Attached files:</div>
              <div className="space-y-1">
                {message.files.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs">
                    <File className="h-4 w-4" />
                    <span>{file.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className="flex items-center justify-end mt-2">
            <div className="text-xs text-blue-200">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
