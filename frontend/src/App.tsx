import { useState } from "react";
import {
  Layout,
  Header,
  InputSection,
  ThreadStatus,
  ConversationView,
  FollowUpInput
} from "./components";
import { useSSE } from "./hooks";
import type { ConversationMessage } from "./types/conversation";

function App() {
  // Initial form state
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Conversation history
  const [conversationHistory, setConversationHistory] = useState<
    ConversationMessage[]
  >([]);
  const [hasStartedConversation, setHasStartedConversation] = useState(false);

  const {
    currentMessage,
    threadId,
    sendMessage,
    resetThread,
    streamingState,
    clearMessage
  } = useSSE("http://localhost:8000/stream");

  // Handle initial form submission
  const handleInitialSubmit = async () => {
    if (!topic.trim()) {
      alert("Please enter a topic");
      return;
    }

    // Add user message to history
    const userMessage: ConversationMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userComment,
      timestamp: new Date(),
      files: uploadedFiles.map((f) => ({ name: f.name, size: f.size })),
      topic: topic,
      numberOfClasses: numberOfClasses
    };

    setConversationHistory([userMessage]);
    setHasStartedConversation(true);

    // Send to backend
    const response = await sendMessage({
      message: userComment,
      topic: topic,
      number_of_classes: numberOfClasses,
      files: uploadedFiles
    });

    // Add assistant response to history and clear streaming message
    if (response) {
      const assistantMessage: ConversationMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response,
        timestamp: new Date()
      };
      setConversationHistory((prev) => [...prev, assistantMessage]);
      clearMessage(); // Clear the streaming message to avoid duplication
    }
  };

  // Handle follow-up messages
  const handleFollowUpSubmit = async (message: string, files: File[]) => {
    if (!message.trim() && files.length === 0) {
      return;
    }

    // Add user message to history
    const userMessage: ConversationMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
      timestamp: new Date(),
      files: files.map((f) => ({ name: f.name, size: f.size }))
    };

    setConversationHistory((prev) => [...prev, userMessage]);

    // Send to backend (keep topic and numberOfClasses from initial submission)
    const response = await sendMessage({
      message: message,
      topic: topic,
      number_of_classes: numberOfClasses,
      thread_id: threadId || undefined,
      files: files
    });

    // Add assistant response to history and clear streaming message
    if (response) {
      const assistantMessage: ConversationMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response,
        timestamp: new Date()
      };
      setConversationHistory((prev) => [...prev, assistantMessage]);
      clearMessage(); // Clear the streaming message to avoid duplication
    }
  };

  // Handle new conversation
  const handleNewConversation = () => {
    resetThread();
    setUserComment("");
    setTopic("");
    setNumberOfClasses(1);
    setUploadedFiles([]);
    setConversationHistory([]);
    setHasStartedConversation(false);
  };

  return (
    <Layout>
      <Header />
      <ThreadStatus
        threadId={threadId}
        onNewConversation={handleNewConversation}
      />

      {/* Initial form - grey out after first submission */}
      <div
        className={
          hasStartedConversation ? "opacity-50 pointer-events-none" : ""
        }
      >
        <InputSection
          userComment={userComment}
          setUserComment={setUserComment}
          topic={topic}
          setTopic={setTopic}
          numberOfClasses={numberOfClasses}
          setNumberOfClasses={setNumberOfClasses}
          onSubmit={handleInitialSubmit}
          streamingState={hasStartedConversation ? "complete" : streamingState}
          threadId={threadId}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
        />
      </div>

      {/* Conversation history */}
      {conversationHistory.length > 0 && (
        <div className="mb-6">
          <ConversationView
            messages={conversationHistory}
            streamingState={streamingState}
            currentStreamingContent={
              streamingState === "complete" ? "" : currentMessage
            }
          />
        </div>
      )}

      {/* Follow-up input - show after conversation has started and not currently streaming */}
      {hasStartedConversation &&
        (streamingState === "complete" || streamingState === "idle") && (
          <FollowUpInput
            onSubmit={handleFollowUpSubmit}
            streamingState={streamingState}
          />
        )}
    </Layout>
  );
}
export default App;
