import type { StreamingState } from "../hooks/useSSE";

interface IndicatorProps {
  streamingState: StreamingState;
}

export default function Indicator({ streamingState }: IndicatorProps) {
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
    <div className="flex items-center mb-4">
      <div
        className={`w-2 h-2 ${indicator.color} rounded-full mr-3 ${indicator.animate}`}
      ></div>
      <span className="text-sm font-medium text-gray-700">
        {indicator.label}
      </span>
    </div>
  );
}
