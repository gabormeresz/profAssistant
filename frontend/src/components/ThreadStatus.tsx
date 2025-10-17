interface ThreadStatusProps {
  threadId: string | null;
  onNewConversation: () => void;
}

export default function ThreadStatus({
  threadId,
  onNewConversation
}: ThreadStatusProps) {
  if (!threadId) {
    return null;
  }

  return (
    <div className="mb-4 flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
        <span className="text-sm text-blue-700">
          Active conversation (memory enabled)
        </span>
      </div>
      <button
        onClick={onNewConversation}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        New Conversation
      </button>
    </div>
  );
}
