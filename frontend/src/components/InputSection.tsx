import type { StreamingState } from "../hooks/useWebSocket";

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
  threadId
}: InputSectionProps) {
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
        return "Add Comment";
      case "idle":
      default:
        return "Generate Course Outline";
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
