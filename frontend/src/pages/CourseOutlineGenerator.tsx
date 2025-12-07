import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Layout,
  Header,
  CourseOutlineInputSection,
  StructuredCourseOutline,
  LoadingOverlay,
  FollowUpInput,
  UserMessage
} from "../components";
import { useCourseOutlineSSE, useConversationManager } from "../hooks";
import { COURSE_OUTLINE } from "../utils/constants";
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
    files: files?.map((f) => ({ name: f.name }))
  };
}

// ============================================================================
// Component
// ============================================================================

function CourseOutlineGenerator() {
  const { threadId: urlThreadId } = useParams<{ threadId?: string }>();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  // ============================================================================
  // State Management
  // ============================================================================

  // Form state
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState<number>(
    COURSE_OUTLINE.DEFAULT_CLASSES
  );
  const [language, setLanguage] = useState<string>(
    i18n.language === "hu" ? "Hungarian" : "English"
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isEnhancing, setIsEnhancing] = useState(false);

  // SSE streaming hook
  const {
    courseOutline,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread,
    setThreadId
  } = useCourseOutlineSSE();

  // Conversation management hook (handles URL sync, loading, history)
  const {
    hasStarted,
    setHasStarted,
    userMessages,
    setUserMessages,
    resultHistory: outlineHistory,
    setResultHistory: setOutlineHistory
  } = useConversationManager<CourseOutline, SavedCourseOutline>({
    routePath: "/course-outline-generator",
    urlThreadId,
    threadId,
    setThreadId,
    result: courseOutline,
    streamingState,
    isCorrectType: (
      conversation: unknown
    ): conversation is SavedCourseOutline =>
      typeof conversation === "object" &&
      conversation !== null &&
      "topic" in conversation,
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
  // Effects
  // ============================================================================

  // Sync language field with UI language (only before conversation starts)
  useEffect(() => {
    if (!hasStarted) {
      setLanguage(i18n.language === "hu" ? "Hungarian" : "English");
    }
  }, [i18n.language, hasStarted]);

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleInitialSubmit = useCallback(async () => {
    if (!topic.trim()) {
      alert(t("courseOutline.emptyTopic"));
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

    // Clear uploaded files after sending
    setUploadedFiles([]);
  }, [
    topic,
    userComment,
    uploadedFiles,
    numberOfClasses,
    language,
    sendMessage,
    setHasStarted,
    setUserMessages,
    t
  ]);

  const handleFollowUpSubmit = useCallback(
    async (message: string, files: File[]) => {
      if (!message.trim() && files.length === 0) return;

      // Add user message to history
      const userMessage = createUserMessage(message, files);
      setUserMessages((prev) => [...prev, userMessage]);

      // Send to backend (outline will be added via useEffect)
      // On follow-ups, only send message, thread_id, and files
      await sendMessage({
        message,
        thread_id: threadId || undefined,
        files
      });
    },
    [threadId, sendMessage, setUserMessages]
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
    setLanguage(i18n.language === "hu" ? "Hungarian" : "English");
    setUploadedFiles([]);

    // Navigate to base route
    navigate("/course-outline-generator", { replace: true });
  }, [
    resetThread,
    setOutlineHistory,
    setUserMessages,
    setHasStarted,
    navigate,
    i18n.language
  ]);

  // ============================================================================
  // Render
  // ============================================================================

  const isGenerating =
    loading ||
    streamingState === "streaming" ||
    streamingState === "connecting" ||
    isEnhancing;

  const showFollowUpInput =
    hasStarted && (streamingState === "complete" || streamingState === "idle");

  return (
    <Layout
      showSidebar
      onNewConversation={handleNewConversation}
      header={<Header title={t("header.courseOutlineGenerator")} />}
    >
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
          onEnhancerLoadingChange={setIsEnhancing}
          displayFiles={
            hasStarted && userMessages[0]?.files
              ? userMessages[0].files
              : undefined
          }
        />
      </div>

      {/* Display conversation: user messages and course outline responses */}
      <div className="space-y-6">
        {userMessages.map((userMsg, index) => (
          <div key={userMsg.id}>
            {/* User message - skip first message as it's visible in the initial form */}
            {index > 0 && <UserMessage message={userMsg} />}

            {/* Corresponding assistant response (course outline) - either from history or current */}
            {(outlineHistory[index] ||
              (index === userMessages.length - 1 && courseOutline)) && (
              <div className="mt-6">
                <StructuredCourseOutline
                  outline={outlineHistory[index] || courseOutline!}
                  language={language}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Progress indicator */}
      <LoadingOverlay
        message={isEnhancing ? t("overlay.enhancingPrompt") : progressMessage}
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
