import type { StreamingState } from "../hooks/useWebSocket";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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

  // Determine indicator color and label based on state
  const getIndicatorStyle = () => {
    switch (streamingState) {
      case "connecting":
        return {
          color: "bg-yellow-500",
          label: "Connecting to AI...",
          animate: "animate-pulse"
        };
      case "streaming":
        return {
          color: "bg-green-500",
          label: "Streaming Response",
          animate: "animate-pulse"
        };
      case "complete":
        return {
          color: "bg-blue-500",
          label: "Complete",
          animate: ""
        };
      default:
        return {
          color: "bg-gray-500",
          label: "AI Response",
          animate: ""
        };
    }
  };

  const indicator = getIndicatorStyle();

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center mb-4">
        <div
          className={`w-2 h-2 ${indicator.color} rounded-full mr-3 ${indicator.animate}`}
        ></div>
        <span className="text-sm font-medium text-gray-700">
          {indicator.label}
        </span>
      </div>

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
