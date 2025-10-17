interface OutputSectionProps {
  loading: boolean;
  currentMessage: string;
}

export default function OutputSection({
  loading,
  currentMessage
}: OutputSectionProps) {
  if (!loading && !currentMessage) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center mb-4">
        <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
        <span className="text-sm font-medium text-gray-700">AI Response</span>
      </div>

      {loading && !currentMessage && (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span>Generating your content...</span>
        </div>
      )}

      {currentMessage && (
        <div className="prose prose-gray max-w-none">
          <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
            {currentMessage}
          </div>
        </div>
      )}
    </div>
  );
}
