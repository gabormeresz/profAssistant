import { useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Layout,
  Header,
  CourseOutlineInputSection,
  ThreadStatus,
  StructuredCourseOutline,
  ProgressIndicator,
  FollowUpInput,
  UserMessage
} from "../components";
import { useCourseOutlineSSE, useConversationManager } from "../hooks";
import { COURSE_OUTLINE, UI_MESSAGES } from "../utils/constants";
import type { CourseOutline, ConversationMessage } from "../types";
import type { SavedCourseOutline } from "../types/conversation";

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generates a unique ID for messages
 */
function generateMessageId(): string {
  return `user-${crypto.randomUUID()}`;
}

/**
 * Creates a ConversationMessage object from user data
 */
function createUserMessage(
  content: string,
  files?: File[]
): ConversationMessage {
  return {
    id: generateMessageId(),
    role: "user",
    content,
    timestamp: new Date(),
    files: files?.map((f) => ({ name: f.name, size: f.size }))
  };
}

// ============================================================================
// Component
// ============================================================================

function CourseOutlineGenerator() {
  const { threadId: urlThreadId } = useParams<{ threadId?: string }>();
  const navigate = useNavigate();

  // ============================================================================
  // State Management
  // ============================================================================

  // Form state
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState<number>(
    COURSE_OUTLINE.DEFAULT_CLASSES
  );
  const [language, setLanguage] = useState<string>("English");
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // SSE streaming hook
  const {
    courseOutline,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread,
    setThreadId,
    clearData
  } = useCourseOutlineSSE();

  // Conversation management hook (handles URL sync, loading, history)
  const {
    hasStarted,
    setHasStarted,
    userMessages,
    setUserMessages,
    resultHistory: outlineHistory,
    setResultHistory: setOutlineHistory,
    sidebarRef
  } = useConversationManager<CourseOutline, SavedCourseOutline>({
    routePath: "/outline-generator",
    urlThreadId,
    threadId,
    setThreadId,
    result: courseOutline,
    streamingState,
    clearData,
    isCorrectType: (conversation: unknown): conversation is SavedCourseOutline =>
      typeof conversation === "object" && conversation !== null && "topic" in conversation,
    restoreFormState: (conversation: SavedCourseOutline) => {
      setTopic(conversation.topic);
      setNumberOfClasses(conversation.number_of_classes);
      if (conversation.user_comment) {
        setUserComment(conversation.user_comment);
      }
      if (conversation.language) {
        setLanguage(conversation.language);
      }
    },
    parseResult: (content) => JSON.parse(content) as CourseOutline
  });

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleInitialSubmit = useCallback(async () => {
    if (!topic.trim()) {
      alert(UI_MESSAGES.EMPTY_TOPIC);
      return;
    }

    setHasStarted(true);

    // Add user message to history
    const userMessage = createUserMessage(userComment, uploadedFiles);
    setUserMessages((prev) => [...prev, userMessage]);

    // Send to backend (outline will be added via useEffect)
    await sendMessage({
      message: userComment,
      topic,
      number_of_classes: numberOfClasses,
      language,
      files: uploadedFiles
    });
  }, [topic, userComment, uploadedFiles, numberOfClasses, language, sendMessage, setHasStarted, setUserMessages]);

  const handleFollowUpSubmit = useCallback(
    async (message: string, files: File[]) => {
      if (!message.trim() && files.length === 0) return;

      // Add user message to history
      const userMessage = createUserMessage(message, files);
      setUserMessages((prev) => [...prev, userMessage]);

      // Send to backend (outline will be added via useEffect)
      await sendMessage({
        message,
        topic,
        number_of_classes: numberOfClasses,
        language,
        thread_id: threadId || undefined,
        files
      });
    },
    [topic, numberOfClasses, language, threadId, sendMessage, setUserMessages]
  );

  const handleNewConversation = useCallback(() => {
    // Reset all state
    resetThread();
    setOutlineHistory([]);
    setUserMessages([]);
    setHasStarted(false);
    setUserComment("");
    setTopic("");
    setNumberOfClasses(COURSE_OUTLINE.DEFAULT_CLASSES);
    setLanguage("English");
    setUploadedFiles([]);

    // Navigate to base route
    navigate("/outline-generator", { replace: true });
  }, [resetThread, setOutlineHistory, setUserMessages, setHasStarted, navigate]);

  // ============================================================================
  // Render
  // ============================================================================

  const isGenerating =
    loading ||
    streamingState === "streaming" ||
    streamingState === "connecting";

  const showFollowUpInput =
    hasStarted && (streamingState === "complete" || streamingState === "idle");

  return (
    <Layout
      ref={sidebarRef}
      showSidebar
      onNewConversation={handleNewConversation}
    >
      <Header title="Course Outline Generator" />
      <ThreadStatus
        threadId={threadId}
        onNewConversation={handleNewConversation}
      />

      {/* Initial form - grey out after first submission */}
      <div className={hasStarted ? "opacity-50 pointer-events-none" : ""}>
        <CourseOutlineInputSection
          userComment={userComment}
          setUserComment={setUserComment}
          topic={topic}
          setTopic={setTopic}
          numberOfClasses={numberOfClasses}
          setNumberOfClasses={setNumberOfClasses}
          language={language}
          setLanguage={setLanguage}
          onSubmit={handleInitialSubmit}
          threadId={threadId}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
        />
      </div>

      {/* Display conversation: user messages and course outline responses */}
      <div className="space-y-6">
        {userMessages.map((userMsg, index) => (
          <div key={userMsg.id}>
            {/* User message - skip first message as it's visible in the initial form */}
            {index > 0 && <UserMessage message={userMsg} />}

            {/* Corresponding assistant response (course outline) */}
            {outlineHistory[index] && (
              <div className="mt-6">
                <StructuredCourseOutline outline={outlineHistory[index]} />
              </div>
            )}
          </div>
        ))}

        {/* Show current outline being generated (not yet in history) */}
        {courseOutline && (
          <div className="mt-6">
            <StructuredCourseOutline outline={courseOutline} />
          </div>
        )}
      </div>

      {/* Progress indicator */}
      <ProgressIndicator
        message={progressMessage || "Processing..."}
        show={isGenerating}
      />

      {/* Follow-up input */}
      {showFollowUpInput && (
        <FollowUpInput
          onSubmit={handleFollowUpSubmit}
          streamingState={streamingState}
        />
      )}
    </Layout>
  );
}

export default CourseOutlineGenerator;
