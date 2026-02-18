import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Layout,
  Header,
  PresentationInputSection,
  StructuredPresentation,
  LoadingOverlay,
  FollowUpInput,
  UserMessage,
  ErrorBanner,
  ForkButton
} from "../components";
import { usePresentationSSE, useConversationManager } from "../hooks";
import { PRESENTATION } from "../utils/constants";
import type { Presentation, ConversationMessage } from "../types";
import type { SavedPresentation } from "../types/conversation";
import type { LessonSection, ActivityPlan } from "../types";

// ============================================================================
// Helper: serialize structured lesson plan data into readable text
// ============================================================================

function formatLessonBreakdown(sections: LessonSection[]): string {
  return sections.map((s) => `${s.section_title}: ${s.description}`).join("\n");
}

function formatActivities(activities: ActivityPlan[]): string {
  return activities
    .map(
      (a) =>
        `${a.name}\n  Objective: ${a.objective}\n  Instructions: ${a.instructions}`
    )
    .join("\n\n");
}

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

function PresentationGenerator() {
  const { threadId: urlThreadId } = useParams<{ threadId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();

  // ============================================================================
  // State Management
  // ============================================================================

  // Form state
  const [courseTitle, setCourseTitle] = useState("");
  const [classNumber, setClassNumber] = useState<number | null>(null);
  const [classTitle, setClassTitle] = useState("");
  const [learningObjective, setLearningObjective] = useState("");
  const [keyPoints, setKeyPoints] = useState<string[]>([""]);
  const [lessonBreakdown, setLessonBreakdown] = useState("");
  const [activities, setActivities] = useState("");
  const [homework, setHomework] = useState("");
  const [extraActivities, setExtraActivities] = useState("");
  const [userComment, setUserComment] = useState("");
  const [language, setLanguage] = useState<string>(
    i18n.language === "hu" ? "Hungarian" : "English"
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isEnhancing, setIsEnhancing] = useState(false);

  // SSE streaming hook
  const {
    presentation,
    progressMessage,
    error,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread,
    setThreadId,
    clearError
  } = usePresentationSSE();

  // Conversation management hook (handles URL sync, loading, history)
  const {
    hasStarted,
    setHasStarted,
    userMessages,
    setUserMessages,
    resultHistory: presentationHistory,
    setResultHistory: setPresentationHistory
  } = useConversationManager<Presentation, SavedPresentation>({
    routePath: "/presentation-generator",
    urlThreadId,
    threadId,
    setThreadId,
    result: presentation,
    streamingState,
    isCorrectType: (conversation: unknown): conversation is SavedPresentation =>
      typeof conversation === "object" &&
      conversation !== null &&
      "conversation_type" in conversation &&
      (conversation as SavedPresentation).conversation_type === "presentation",
    restoreFormState: (conversation: SavedPresentation) => {
      setCourseTitle(conversation.course_title);
      setClassNumber(conversation.class_number ?? null);
      setClassTitle(conversation.class_title);
      if (conversation.learning_objective) {
        setLearningObjective(conversation.learning_objective);
      }
      if (conversation.key_points?.length) {
        setKeyPoints(conversation.key_points);
      }
      if (conversation.lesson_breakdown) {
        setLessonBreakdown(conversation.lesson_breakdown);
      }
      if (conversation.activities) {
        setActivities(conversation.activities);
      }
      if (conversation.homework) {
        setHomework(conversation.homework);
      }
      if (conversation.extra_activities) {
        setExtraActivities(conversation.extra_activities);
      }
      if (conversation.user_comment) {
        setUserComment(conversation.user_comment);
      }
      if (conversation.language) {
        setLanguage(conversation.language);
      }
    },
    parseResult: (content: string) => JSON.parse(content) as Presentation
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

  // Load pre-filled data from navigation state (from lesson plan)
  useEffect(() => {
    if (location.state) {
      const state = location.state as {
        courseTitle?: string;
        classNumber?: number;
        classTitle?: string;
        learningObjective?: string;
        keyPoints?: string[];
        lessonBreakdown?: LessonSection[];
        activities?: ActivityPlan[];
        homework?: string;
        extraActivities?: string;
        language?: string;
      };

      if (state.courseTitle) setCourseTitle(state.courseTitle);
      if (state.classNumber !== undefined)
        setClassNumber(state.classNumber ?? null);
      if (state.classTitle) setClassTitle(state.classTitle);
      if (state.learningObjective)
        setLearningObjective(state.learningObjective);
      if (state.keyPoints?.length) setKeyPoints(state.keyPoints);
      if (state.lessonBreakdown?.length)
        setLessonBreakdown(formatLessonBreakdown(state.lessonBreakdown));
      if (state.activities?.length)
        setActivities(formatActivities(state.activities));
      if (state.homework) setHomework(state.homework);
      if (state.extraActivities) setExtraActivities(state.extraActivities);
      if (state.language) setLanguage(state.language);

      // Clear navigation state after loading
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleInitialSubmit = useCallback(async () => {
    // Validation
    if (!courseTitle.trim()) {
      alert(t("presentation.emptyCourseTitle"));
      return;
    }
    if (!classTitle.trim()) {
      alert(t("presentation.emptyClassTitle"));
      return;
    }
    if (
      classNumber !== null &&
      (classNumber < PRESENTATION.MIN_CLASS_NUMBER ||
        classNumber > PRESENTATION.MAX_CLASS_NUMBER)
    ) {
      alert(t("presentation.invalidClassNumber"));
      return;
    }

    // Filter out empty key points
    const filteredKeyPoints = keyPoints.filter((kp) => kp.trim());

    if (filteredKeyPoints.length > PRESENTATION.MAX_KEY_POINTS) {
      alert(
        t("presentation.maxKeyPoints", { max: PRESENTATION.MAX_KEY_POINTS })
      );
      return;
    }

    setHasStarted(true);

    // Add user message to history
    const userMessage = createUserMessage(userComment, uploadedFiles);
    setUserMessages((prev) => [...prev, userMessage]);

    // Send to backend
    await sendMessage({
      message: userComment,
      course_title: courseTitle,
      class_number: classNumber ?? undefined,
      class_title: classTitle,
      learning_objective: learningObjective,
      key_points: filteredKeyPoints,
      lesson_breakdown: lessonBreakdown,
      activities,
      homework,
      extra_activities: extraActivities,
      language,
      files: uploadedFiles
    });

    // Clear uploaded files after sending
    setUploadedFiles([]);
  }, [
    courseTitle,
    classNumber,
    classTitle,
    learningObjective,
    keyPoints,
    lessonBreakdown,
    activities,
    homework,
    extraActivities,
    userComment,
    language,
    uploadedFiles,
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
    setPresentationHistory([]);
    setUserMessages([]);
    setHasStarted(false);
    setCourseTitle("");
    setClassNumber(null);
    setClassTitle("");
    setLearningObjective("");
    setKeyPoints([""]);
    setLessonBreakdown("");
    setActivities("");
    setHomework("");
    setExtraActivities("");
    setUserComment("");
    setLanguage(i18n.language === "hu" ? "Hungarian" : "English");
    setUploadedFiles([]);

    // Navigate to base route
    navigate("/presentation-generator", { replace: true });
  }, [
    resetThread,
    setPresentationHistory,
    setUserMessages,
    setHasStarted,
    navigate,
    i18n.language
  ]);

  const handleFork = useCallback(() => {
    // Save current form values before resetting
    const saved = {
      courseTitle,
      classNumber,
      classTitle,
      learningObjective,
      keyPoints: [...keyPoints],
      lessonBreakdown,
      activities,
      homework,
      extraActivities,
      userComment,
      language
    };

    // Reset conversation state
    resetThread();
    setPresentationHistory([]);
    setUserMessages([]);
    setHasStarted(false);
    setUploadedFiles([]);

    // Navigate to base route
    navigate("/presentation-generator", { replace: true });

    // Re-apply saved form values
    setCourseTitle(saved.courseTitle);
    setClassNumber(saved.classNumber);
    setClassTitle(saved.classTitle);
    setLearningObjective(saved.learningObjective);
    setKeyPoints(saved.keyPoints);
    setLessonBreakdown(saved.lessonBreakdown);
    setActivities(saved.activities);
    setHomework(saved.homework);
    setExtraActivities(saved.extraActivities);
    setUserComment(saved.userComment);
    setLanguage(saved.language);
  }, [
    courseTitle,
    classNumber,
    classTitle,
    learningObjective,
    keyPoints,
    lessonBreakdown,
    activities,
    homework,
    extraActivities,
    userComment,
    language,
    resetThread,
    setPresentationHistory,
    setUserMessages,
    setHasStarted,
    navigate
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
      header={<Header title={t("header.presentationGenerator")} />}
    >
      {/* Error banner */}
      <ErrorBanner error={error} onDismiss={clearError} />

      {/* Initial form - grey out after first submission */}
      <div className={hasStarted ? "opacity-50 pointer-events-none" : ""}>
        <PresentationInputSection
          courseTitle={courseTitle}
          setCourseTitle={setCourseTitle}
          classNumber={classNumber}
          setClassNumber={setClassNumber}
          classTitle={classTitle}
          setClassTitle={setClassTitle}
          learningObjective={learningObjective}
          setLearningObjective={setLearningObjective}
          keyPoints={keyPoints}
          setKeyPoints={setKeyPoints}
          lessonBreakdown={lessonBreakdown}
          setLessonBreakdown={setLessonBreakdown}
          activities={activities}
          setActivities={setActivities}
          homework={homework}
          setHomework={setHomework}
          extraActivities={extraActivities}
          setExtraActivities={setExtraActivities}
          userComment={userComment}
          setUserComment={setUserComment}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
          language={language}
          setLanguage={setLanguage}
          onSubmit={handleInitialSubmit}
          threadId={threadId}
          onEnhancerLoadingChange={setIsEnhancing}
          displayFiles={
            hasStarted && userMessages[0]?.files
              ? userMessages[0].files
              : undefined
          }
        />
      </div>
      {hasStarted && <ForkButton onClick={handleFork} />}

      {/* Display conversation: user messages and presentation responses */}
      <div className="space-y-6">
        {userMessages.map((userMsg, index) => (
          <div key={userMsg.id}>
            {/* User message - skip first message as it's visible in the initial form */}
            {index > 0 && <UserMessage message={userMsg} />}

            {/* Corresponding assistant response (presentation) - either from history or current */}
            {(presentationHistory[index] ||
              (index === userMessages.length - 1 && presentation)) && (
              <div className="mt-6">
                <StructuredPresentation
                  presentation={presentationHistory[index] || presentation!}
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

export default PresentationGenerator;
