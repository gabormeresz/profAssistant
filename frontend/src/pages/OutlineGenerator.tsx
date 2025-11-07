import { useState } from "react";
import {
  Layout,
  Header,
  InputSection,
  ThreadStatus,
  ConversationView,
  FollowUpInput
} from "../components";
import { useSSE, useConversation } from "../hooks";
import { UI_MESSAGES, COURSE_OUTLINE } from "../utils/constants";

function OutlineGenerator() {
  // Form state
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState<number>(
    COURSE_OUTLINE.DEFAULT_CLASSES
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Conversation management
  const {
    messages,
    hasStarted,
    addUserMessage,
    addAssistantMessage,
    reset: resetConversation
  } = useConversation();

  // SSE streaming
  const {
    currentMessage,
    threadId,
    sendMessage,
    resetThread,
    streamingState,
    clearMessage
  } = useSSE();

  // Handle initial form submission
  const handleInitialSubmit = async () => {
    if (!topic.trim()) {
      alert(UI_MESSAGES.EMPTY_TOPIC);
      return;
    }

    // Add user message to conversation
    addUserMessage(userComment, uploadedFiles, { topic, numberOfClasses });

    // Send to backend
    const response = await sendMessage({
      message: userComment,
      topic,
      number_of_classes: numberOfClasses,
      files: uploadedFiles
    });

    // Add assistant response
    if (response) {
      addAssistantMessage(response);
      clearMessage();
    }
  };

  // Handle follow-up messages
  const handleFollowUpSubmit = async (message: string, files: File[]) => {
    if (!message.trim() && files.length === 0) return;

    // Add user message
    addUserMessage(message, files);

    // Send to backend
    const response = await sendMessage({
      message,
      topic,
      number_of_classes: numberOfClasses,
      thread_id: threadId || undefined,
      files
    });

    // Add assistant response
    if (response) {
      addAssistantMessage(response);
      clearMessage();
    }
  };

  // Handle new conversation
  const handleNewConversation = () => {
    resetThread();
    resetConversation();
    setUserComment("");
    setTopic("");
    setNumberOfClasses(COURSE_OUTLINE.DEFAULT_CLASSES);
    setUploadedFiles([]);
  };

  return (
    <Layout showSidebar onNewConversation={handleNewConversation}>
      <Header title="Course Outline Generator (Markdown Streaming)" />
      <ThreadStatus
        threadId={threadId}
        onNewConversation={handleNewConversation}
      />

      {/* Initial form - grey out after first submission */}
      <div className={hasStarted ? "opacity-50 pointer-events-none" : ""}>
        <InputSection
          userComment={userComment}
          setUserComment={setUserComment}
          topic={topic}
          setTopic={setTopic}
          numberOfClasses={numberOfClasses}
          setNumberOfClasses={setNumberOfClasses}
          onSubmit={handleInitialSubmit}
          threadId={threadId}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
        />
      </div>

      {/* Conversation history */}
      {messages.length > 0 && (
        <div className="mb-6">
          <ConversationView
            messages={messages}
            streamingState={streamingState}
            currentStreamingContent={
              streamingState === "complete" ? "" : currentMessage
            }
          />
        </div>
      )}

      {/* Follow-up input */}
      {hasStarted &&
        (streamingState === "complete" || streamingState === "idle") && (
          <FollowUpInput
            onSubmit={handleFollowUpSubmit}
            streamingState={streamingState}
          />
        )}
    </Layout>
  );
}

export default OutlineGenerator;
