import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import Indicator from "./Indicator";
import { Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ConversationMessage } from "../types/conversation";
import type { StreamingState } from "../hooks/useSSE";

interface ConversationViewProps {
  messages: ConversationMessage[];
  streamingState: StreamingState;
  currentStreamingContent: string;
}

export default function ConversationView({
  messages,
  streamingState,
  currentStreamingContent
}: ConversationViewProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentStreamingContent]);

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
      {/* Header */}
      {messages.length > 0 && (
        <div className="mb-6 pb-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Conversation History
          </h2>
        </div>
      )}

      {/* Messages */}
      <div className="space-y-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {/* Currently streaming message */}
        {streamingState !== "idle" && currentStreamingContent && (
          <div className="flex gap-4 flex-row">
            <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gray-700">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="inline-block max-w-[85%] rounded-lg p-4 bg-white border border-gray-200">
                <Indicator streamingState={streamingState} />
                {currentStreamingContent && (
                  <div className="markdown-content mt-3">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {currentStreamingContent}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
