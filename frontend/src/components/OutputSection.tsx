import type { StreamingState } from "../hooks/useSSE";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Indicator from "./Indicator";
import { useExport } from "../hooks";

interface OutputSectionProps {
  streamingState: StreamingState;
  currentMessage: string;
}

export default function OutputSection({
  streamingState,
  currentMessage
}: OutputSectionProps) {
  const { exportToDocx } = useExport();

  if (
    streamingState === "idle" ||
    (streamingState === "complete" && !currentMessage)
  ) {
    return null;
  }

  const handleExportDocx = async () => {
    try {
      const timestamp = new Date().toISOString().slice(0, 10);
      await exportToDocx(currentMessage, {
        filename: `ai-response-${timestamp}.docx`
      });
    } catch (error) {
      console.error("Failed to export DOCX:", error);
      alert("Failed to export document. Please try again.");
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <Indicator streamingState={streamingState} />

        {streamingState === "complete" && currentMessage && (
          <button
            onClick={handleExportDocx}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Export DOCX
          </button>
        )}
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
