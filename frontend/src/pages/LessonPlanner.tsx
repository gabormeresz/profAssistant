import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Layout,
  Header,
  LessonPlanInputSection,
  StructuredLessonPlan,
  LoadingOverlay,
  FollowUpInput,
  UserMessage
} from "../components";
import { useLessonPlanSSE, useConversationManager } from "../hooks";
import { LESSON_PLAN } from "../utils/constants";
import type { LessonPlan, ConversationMessage } from "../types";
import type { SavedLessonPlan } from "../types/conversation";

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

function LessonPlanner() {
  const { threadId: urlThreadId } = useParams<{ threadId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();

  // ============================================================================
  // State Management
  // ============================================================================

  // Form state
  const [courseTitle, setCourseTitle] = useState("");
  const [classNumber, setClassNumber] = useState<number>(1);
  const [classTitle, setClassTitle] = useState("");
  const [learningObjectives, setLearningObjectives] = useState<string[]>([""]);
  const [keyTopics, setKeyTopics] = useState<string[]>([""]);
  const [activitiesProjects, setActivitiesProjects] = useState<string[]>([""]);
  const [userComment, setUserComment] = useState("");
  const [language, setLanguage] = useState<string>(
    i18n.language === "hu" ? "Hungarian" : "English"
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isEnhancing, setIsEnhancing] = useState(false);

  // SSE streaming hook
  const {
    lessonPlan,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread,
    setThreadId,
    clearData
  } = useLessonPlanSSE();

  // Conversation management hook (handles URL sync, loading, history)
  const {
    hasStarted,
    setHasStarted,
    userMessages,
    setUserMessages,
    resultHistory: lessonHistory,
    setResultHistory: setLessonHistory,
    sidebarRef
  } = useConversationManager<LessonPlan, SavedLessonPlan>({
    routePath: "/lesson-planner",
    urlThreadId,
    threadId,
    setThreadId,
    result: lessonPlan,
    streamingState,
    clearData,
    isCorrectType: (conversation: unknown): conversation is SavedLessonPlan =>
      typeof conversation === "object" &&
      conversation !== null &&
      "class_title" in conversation,
    restoreFormState: (conversation: SavedLessonPlan) => {
      setClassTitle(conversation.class_title);
      setCourseTitle(conversation.course_title);
      setClassNumber(conversation.class_number);
      setLearningObjectives(conversation.learning_objectives);
      setKeyTopics(conversation.key_topics);
      setActivitiesProjects(conversation.activities_projects);
      if (conversation.user_comment) {
        setUserComment(conversation.user_comment);
      }
      if (conversation.language) {
        setLanguage(conversation.language);
      }
    },
    parseResult: (content: string) => JSON.parse(content) as LessonPlan
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

  // Load pre-filled data from navigation state (from course outline)
  useEffect(() => {
    if (location.state) {
      const state = location.state as {
        courseTitle?: string;
        classNumber?: number;
        classTitle?: string;
        learningObjectives?: string[];
        keyTopics?: string[];
        activitiesProjects?: string[];
        language?: string;
      };

      if (state.courseTitle) setCourseTitle(state.courseTitle);
      if (state.classNumber) setClassNumber(state.classNumber);
      if (state.classTitle) setClassTitle(state.classTitle);
      if (state.learningObjectives)
        setLearningObjectives(state.learningObjectives);
      if (state.keyTopics) setKeyTopics(state.keyTopics);
      if (state.activitiesProjects)
        setActivitiesProjects(state.activitiesProjects);
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
      alert(t("lessonPlan.emptyCourseTitle"));
      return;
    }
    if (!classTitle.trim()) {
      alert(t("lessonPlan.emptyClassTitle"));
      return;
    }
    if (
      classNumber < LESSON_PLAN.MIN_CLASS_NUMBER ||
      classNumber > LESSON_PLAN.MAX_CLASS_NUMBER
    ) {
      alert(t("lessonPlan.invalidClassNumber"));
      return;
    }

    // Filter out empty strings from arrays
    const filteredObjectives = learningObjectives.filter((obj) => obj.trim());
    const filteredTopics = keyTopics.filter((topic) => topic.trim());
    const filteredActivities = activitiesProjects.filter((act) => act.trim());

    // Validate maximum array lengths (minimum is 0, so optional)
    if (filteredObjectives.length > LESSON_PLAN.MAX_OBJECTIVES) {
      alert(
        `Please provide at most ${LESSON_PLAN.MAX_OBJECTIVES} learning objectives`
      );
      return;
    }
    if (filteredTopics.length > LESSON_PLAN.MAX_TOPICS) {
      alert(`Please provide at most ${LESSON_PLAN.MAX_TOPICS} key topics`);
      return;
    }
    if (filteredActivities.length > LESSON_PLAN.MAX_ACTIVITIES) {
      alert(`Please provide at most ${LESSON_PLAN.MAX_ACTIVITIES} activities`);
      return;
    }

    setHasStarted(true);

    // Add user message to history
    const userMessage = createUserMessage(userComment, uploadedFiles);
    setUserMessages((prev) => [...prev, userMessage]);

    // Send to backend (lesson plan will be added via useEffect)
    await sendMessage({
      message: userComment,
      course_title: courseTitle,
      class_number: classNumber,
      class_title: classTitle,
      learning_objectives: filteredObjectives,
      key_topics: filteredTopics,
      activities_projects: filteredActivities,
      language,
      files: uploadedFiles
    });
  }, [
    courseTitle,
    classNumber,
    classTitle,
    learningObjectives,
    keyTopics,
    activitiesProjects,
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

      // Send to backend (lesson plan will be added via useEffect)
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
    setLessonHistory([]);
    setUserMessages([]);
    setHasStarted(false);
    setCourseTitle("");
    setClassNumber(1);
    setClassTitle("");
    setLearningObjectives([""]);
    setKeyTopics([""]);
    setActivitiesProjects([""]);
    setUserComment("");
    setLanguage(i18n.language === "hu" ? "Hungarian" : "English");
    setUploadedFiles([]);

    // Navigate to base route
    navigate("/lesson-planner", { replace: true });
  }, [
    resetThread,
    setLessonHistory,
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
      ref={sidebarRef}
      showSidebar
      onNewConversation={handleNewConversation}
      header={<Header title={t("header.lessonPlanner")} />}
    >
      {/* Initial form - grey out after first submission */}
      <div className={hasStarted ? "opacity-50 pointer-events-none" : ""}>
        <LessonPlanInputSection
          courseTitle={courseTitle}
          setCourseTitle={setCourseTitle}
          classNumber={classNumber}
          setClassNumber={setClassNumber}
          classTitle={classTitle}
          setClassTitle={setClassTitle}
          learningObjectives={learningObjectives}
          setLearningObjectives={setLearningObjectives}
          keyTopics={keyTopics}
          setKeyTopics={setKeyTopics}
          activitiesProjects={activitiesProjects}
          setActivitiesProjects={setActivitiesProjects}
          userComment={userComment}
          setUserComment={setUserComment}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
          language={language}
          setLanguage={setLanguage}
          onSubmit={handleInitialSubmit}
          threadId={threadId}
          onEnhancerLoadingChange={setIsEnhancing}
        />
      </div>

      {/* Display conversation: user messages and lesson plan responses */}
      <div className="space-y-6">
        {userMessages.map((userMsg, index) => (
          <div key={userMsg.id}>
            {/* User message - skip first message as it's visible in the initial form */}
            {index > 0 && <UserMessage message={userMsg} />}

            {/* Corresponding assistant response (lesson plan) */}
            {lessonHistory[index] && (
              <div className="mt-6">
                <StructuredLessonPlan lessonPlan={lessonHistory[index]} />
              </div>
            )}
          </div>
        ))}

        {/* Show current lesson plan being generated (not yet in history) */}
        {lessonPlan && (
          <div className="mt-6">
            <StructuredLessonPlan lessonPlan={lessonPlan} />
          </div>
        )}
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

export default LessonPlanner;
