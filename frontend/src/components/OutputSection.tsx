import type { StreamingState } from "../hooks/useWebSocket";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Indicator from "./Indicator";

interface OutputSectionProps {
  streamingState: StreamingState;
  currentMessage: string;
}

export default function OutputSection({
  streamingState,
  currentMessage
}: OutputSectionProps) {
  if (
    streamingState === "idle" ||
    (streamingState === "complete" && !currentMessage)
  ) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <Indicator streamingState={streamingState} />

      {streamingState === "connecting" && (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full"></div>
          <span>Waiting for model to start...</span>
        </div>
      )}

      {currentMessage && (
        <div className="markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {currentMessage}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}
