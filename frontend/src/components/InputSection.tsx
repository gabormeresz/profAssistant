interface InputSectionProps {
  input: string;
  setInput: (value: string) => void;
  topic: string;
  setTopic: (value: string) => void;
  numberOfClasses: number;
  setNumberOfClasses: (value: number) => void;
  onSubmit: () => void;
  loading: boolean;
}

export default function InputSection({
  input,
  setInput,
  topic,
  setTopic,
  numberOfClasses,
  setNumberOfClasses,
  onSubmit,
  loading
}: InputSectionProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div className="space-y-4">
        {/* Topic Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Topic / Subject
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="e.g., Mathematics, History, Science..."
          />
        </div>

        {/* Number of Classes Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Classes
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={numberOfClasses}
            onChange={(e) => setNumberOfClasses(parseInt(e.target.value) || 1)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="1"
          />
        </div>

        {/* Message/Prompt Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your prompt
          </label>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors"
            placeholder="Describe what kind of lesson plan or educational content you need..."
          />
        </div>
      </div>

      <div className="flex justify-end mt-4">
        <button
          onClick={onSubmit}
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {loading ? "Processing..." : "Generate Content"}
        </button>
      </div>
    </div>
  );
}
