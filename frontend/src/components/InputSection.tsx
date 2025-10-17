interface InputSectionProps {
  input: string;
  setInput: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export default function InputSection({
  input,
  setInput,
  onSubmit,
  loading
}: InputSectionProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-3">
        Your prompt
      </label>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors"
        placeholder="Describe what kind of lesson plan or educational content you need..."
      />
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
