import type { StreamingState } from "../hooks/useSSE";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Indicator from "./Indicator";
import { useExport } from "../hooks";
import { FileDown } from "lucide-react";

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
            <FileDown className="h-4 w-4" />
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
