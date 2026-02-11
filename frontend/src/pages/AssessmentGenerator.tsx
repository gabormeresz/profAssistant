import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Layout,
  Header,
  AssessmentInputSection,
  StructuredAssessment,
  LoadingOverlay,
  FollowUpInput,
  UserMessage,
  ErrorBanner
} from "../components";
import { PRESET_CONFIGS } from "../components/input/AssessmentInputSection";
import { useAssessmentSSE, useConversationManager } from "../hooks";
import type {
  Assessment,
  ConversationMessage,
  QuestionTypeConfig,
  AssessmentPreset
} from "../types";
import type { SavedAssessment } from "../types/conversation";

// ============================================================================
// Helper Functions
// ============================================================================

function generateMessageId(): string {
  return `user-${crypto.randomUUID()}`;
}

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

const DEFAULT_QUESTION_TYPE_CONFIGS: QuestionTypeConfig[] = [
  { type: "multiple_choice", count: 5, points_each: 2 },
  { type: "true_false", count: 5, points_each: 1 }
];

// ============================================================================
// Component
// ============================================================================

function AssessmentGenerator() {
  const { threadId: urlThreadId } = useParams<{ threadId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();

  // ============================================================================
  // State Management
  // ============================================================================

  // Form state
  const [courseTitle, setCourseTitle] = useState("");
  const [classTitle, setClassTitle] = useState("");
  const [keyTopics, setKeyTopics] = useState<string[]>([""]);
  const [assessmentType, setAssessmentType] = useState<string>("quiz");
  const [difficultyLevel, setDifficultyLevel] = useState<string>("mixed");
  const [questionTypeConfigs, setQuestionTypeConfigs] = useState<
    QuestionTypeConfig[]
  >(DEFAULT_QUESTION_TYPE_CONFIGS);
  const [preset, setPreset] = useState<AssessmentPreset>("quick_quiz");
  const [additionalInstructions, setAdditionalInstructions] = useState("");
  const [language, setLanguage] = useState<string>(
    i18n.language === "hu" ? "Hungarian" : "English"
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isPrefilled, setIsPrefilled] = useState(false);

  // SSE streaming hook
  const {
    assessment,
    progressMessage,
    error,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread,
    setThreadId,
    clearError
  } = useAssessmentSSE();

  // Conversation management hook (handles URL sync, loading, history)
  const {
    hasStarted,
    setHasStarted,
    userMessages,
    setUserMessages,
    resultHistory: assessmentHistory,
    setResultHistory: setAssessmentHistory
  } = useConversationManager<Assessment, SavedAssessment>({
    routePath: "/assessment-generator",
    urlThreadId,
    threadId,
    setThreadId,
    result: assessment,
    streamingState,
    isCorrectType: (conversation: unknown): conversation is SavedAssessment =>
      typeof conversation === "object" &&
      conversation !== null &&
      "assessment_type" in conversation &&
      "question_type_configs" in conversation,
    restoreFormState: (conversation: SavedAssessment) => {
      setCourseTitle(conversation.course_title);
      if (conversation.class_title) setClassTitle(conversation.class_title);
      setKeyTopics(
        conversation.key_topics.length > 0 ? conversation.key_topics : [""]
      );
      setAssessmentType(conversation.assessment_type);
      if (conversation.difficulty_level) {
        setDifficultyLevel(conversation.difficulty_level);
      }
      let restoredConfigs: QuestionTypeConfig[] | null = null;
      if (conversation.question_type_configs) {
        try {
          const raw = JSON.parse(conversation.question_type_configs);
          if (Array.isArray(raw) && raw.length > 0) {
            // Normalize: backend stores "question_type", frontend uses "type"
            restoredConfigs = raw.map((c: Record<string, unknown>) => ({
              type: (c.type ||
                c.question_type ||
                "multiple_choice") as QuestionTypeConfig["type"],
              count: (c.count as number) || 1,
              points_each: (c.points_each as number) || 5
            }));
            setQuestionTypeConfigs(restoredConfigs);
          }
        } catch {
          // Keep defaults
        }
      }
      // Infer preset by matching configs against known presets
      const inferredPreset = restoredConfigs
        ? (
            Object.entries(PRESET_CONFIGS) as [
              Exclude<AssessmentPreset, "custom">,
              (typeof PRESET_CONFIGS)[keyof typeof PRESET_CONFIGS]
            ][]
          ).find(
            ([, p]) =>
              p.type === conversation.assessment_type &&
              p.difficulty === (conversation.difficulty_level || "mixed") &&
              JSON.stringify(p.configs) === JSON.stringify(restoredConfigs)
          )
        : undefined;
      setPreset(inferredPreset ? inferredPreset[0] : "custom");
      if (conversation.user_comment) {
        setAdditionalInstructions(conversation.user_comment);
      }
      if (conversation.language) {
        setLanguage(conversation.language);
      }
    },
    parseResult: (content: string) => JSON.parse(content) as Assessment
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

  // Load pre-filled data from navigation state (from course outline or lesson plan)
  useEffect(() => {
    if (location.state) {
      const state = location.state as {
        courseTitle?: string;
        classTitle?: string;
        keyTopics?: string[];
        language?: string;
      };

      if (state.courseTitle) setCourseTitle(state.courseTitle);
      if (state.classTitle) setClassTitle(state.classTitle);
      if (state.keyTopics && state.keyTopics.length > 0) {
        setKeyTopics(state.keyTopics);
        setIsPrefilled(true);
      }
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
      alert(t("assessment.emptyCourseTitle"));
      return;
    }

    const filteredTopics = keyTopics.filter((topic) => topic.trim());
    if (filteredTopics.length === 0) {
      alert(t("assessment.emptyKeyTopics"));
      return;
    }

    setHasStarted(true);

    // Add user message to history
    const userMessage = createUserMessage(
      additionalInstructions,
      uploadedFiles
    );
    setUserMessages((prev) => [...prev, userMessage]);

    // Send to backend
    await sendMessage({
      message: additionalInstructions,
      course_title: courseTitle,
      class_title: classTitle || undefined,
      key_topics: filteredTopics,
      assessment_type: assessmentType,
      difficulty_level: difficultyLevel,
      question_type_configs: JSON.stringify(questionTypeConfigs),
      additional_instructions: additionalInstructions || undefined,
      language,
      files: uploadedFiles
    });

    // Clear uploaded files after sending
    setUploadedFiles([]);
  }, [
    courseTitle,
    classTitle,
    keyTopics,
    assessmentType,
    difficultyLevel,
    questionTypeConfigs,
    additionalInstructions,
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

      // Send to backend - on follow-ups, only send message, thread_id, and files
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
    setAssessmentHistory([]);
    setUserMessages([]);
    setHasStarted(false);
    setCourseTitle("");
    setClassTitle("");
    setKeyTopics([""]);
    setAssessmentType("quiz");
    setDifficultyLevel("mixed");
    setQuestionTypeConfigs(DEFAULT_QUESTION_TYPE_CONFIGS);
    setPreset("quick_quiz");
    setAdditionalInstructions("");
    setLanguage(i18n.language === "hu" ? "Hungarian" : "English");
    setUploadedFiles([]);

    // Navigate to base route
    navigate("/assessment-generator", { replace: true });
  }, [
    resetThread,
    setAssessmentHistory,
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
      header={<Header title={t("header.assessmentGenerator")} />}
    >
      {/* Error banner */}
      <ErrorBanner error={error} onDismiss={clearError} />

      {/* Initial form - grey out after first submission */}
      <div className={hasStarted ? "opacity-50 pointer-events-none" : ""}>
        <AssessmentInputSection
          courseTitle={courseTitle}
          setCourseTitle={setCourseTitle}
          classTitle={classTitle}
          setClassTitle={setClassTitle}
          keyTopics={keyTopics}
          setKeyTopics={setKeyTopics}
          assessmentType={assessmentType}
          setAssessmentType={setAssessmentType}
          difficultyLevel={difficultyLevel}
          setDifficultyLevel={setDifficultyLevel}
          questionTypeConfigs={questionTypeConfigs}
          setQuestionTypeConfigs={setQuestionTypeConfigs}
          preset={preset}
          setPreset={setPreset}
          additionalInstructions={additionalInstructions}
          setAdditionalInstructions={setAdditionalInstructions}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
          language={language}
          setLanguage={setLanguage}
          onSubmit={handleInitialSubmit}
          threadId={threadId}
          onEnhancerLoadingChange={setIsEnhancing}
          isPrefilled={isPrefilled}
          displayFiles={
            hasStarted && userMessages[0]?.files
              ? userMessages[0].files
              : undefined
          }
        />
      </div>

      {/* Display conversation: user messages and assessment responses */}
      <div className="space-y-6">
        {userMessages.map((userMsg, index) => (
          <div key={userMsg.id}>
            {/* User message - skip first message as it's visible in the initial form */}
            {index > 0 && <UserMessage message={userMsg} />}

            {/* Corresponding assistant response (assessment) - either from history or current */}
            {(assessmentHistory[index] ||
              (index === userMessages.length - 1 && assessment)) && (
              <div className="mt-6">
                <StructuredAssessment
                  assessment={assessmentHistory[index] || assessment!}
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

export default AssessmentGenerator;
