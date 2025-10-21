import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, FileDown } from "lucide-react";
import { useExport } from "../../hooks";
import type { ConversationMessage } from "../../types";

interface AssistantMessageProps {
  message: ConversationMessage;
}

export default function AssistantMessage({ message }: AssistantMessageProps) {
  const { exportToDocx } = useExport();

  const handleExport = async () => {
    try {
      const timestamp = new Date().toISOString().slice(0, 10);
      const messageTime = message.timestamp
        .toISOString()
        .slice(11, 19)
        .replace(/:/g, "-");
      await exportToDocx(message.content, {
        filename: `ai-response-${timestamp}-${messageTime}.docx`
      });
    } catch (error) {
      console.error("Failed to export DOCX:", error);
      alert("Failed to export document. Please try again.");
    }
  };

  return (
    <div className="flex gap-4 flex-row">
      {/* Avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gray-700">
        <Bot className="h-5 w-5 text-white" />
      </div>

      {/* Message Content */}
      <div className="flex-1 text-left">
        <div className="inline-block max-w-[85%] rounded-lg p-4 bg-white border border-gray-200">
          {/* Message content */}
          {message.content && (
            <div className="text-gray-900 markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Timestamp and Export Button */}
          <div className="flex items-center justify-between mt-2">
            <div className="text-xs text-gray-500">
              {message.timestamp.toLocaleTimeString()}
            </div>

            {/* Export button */}
            {message.content && (
              <button
                onClick={handleExport}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                title="Export this message to DOCX"
              >
                <FileDown className="h-3 w-3" />
                Export
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
