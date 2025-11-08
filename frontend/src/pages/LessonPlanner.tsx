import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import {
  Layout,
  Header,
  LessonPlanInputSection,
  ThreadStatus,
  StructuredLessonPlan,
  ProgressIndicator,
  FollowUpInput,
  UserMessage
} from "../components";
import type { SidebarRef } from "../components";
import { useLessonPlanSSE } from "../hooks";
import { LESSON_PLAN, UI_MESSAGES } from "../utils/constants";
import type { LessonPlan, ConversationMessage } from "../types";
import {
  fetchConversation,
  fetchConversationHistory
} from "../services/conversationService";

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
  const sidebarRef = useRef<SidebarRef>(null);

  // ============================================================================
  // State Management
  // ============================================================================

  // Form state
  const [courseTitle, setCourseTitle] = useState("");
  const [classNumber, setClassNumber] = useState<number>(1);
  const [classTitle, setClassTitle] = useState("");
  const [learningObjectives, setLearningObjectives] = useState<string[]>([
    "",
    ""
  ]);
  const [keyTopics, setKeyTopics] = useState<string[]>(["", "", ""]);
  const [activitiesProjects, setActivitiesProjects] = useState<string[]>([""]);
  const [userComment, setUserComment] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Conversation history
  const [lessonHistory, setLessonHistory] = useState<LessonPlan[]>([]);
  const [userMessages, setUserMessages] = useState<ConversationMessage[]>([]);
  const [hasStarted, setHasStarted] = useState(false);

  // Refs to prevent duplicate loading and URL update loops
  const loadedThreadIdRef = useRef<string | null>(null);
  const isLoadingFromUrlRef = useRef(false);

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

  // ============================================================================
  // Effects
  // ============================================================================

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
      };

      if (state.courseTitle) setCourseTitle(state.courseTitle);
      if (state.classNumber) setClassNumber(state.classNumber);
      if (state.classTitle) setClassTitle(state.classTitle);
      if (state.learningObjectives)
        setLearningObjectives(state.learningObjectives);
      if (state.keyTopics) setKeyTopics(state.keyTopics);
      if (state.activitiesProjects)
        setActivitiesProjects(state.activitiesProjects);

      // Clear navigation state after loading
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // Auto-add completed lesson plans to history
  useEffect(() => {
    if (!lessonPlan || streamingState !== "complete") return;

    setLessonHistory((prev) => {
      // Prevent duplicates by checking if lesson plan already exists
      const isDuplicate = prev.some(
        (plan) => JSON.stringify(plan) === JSON.stringify(lessonPlan)
      );

      if (isDuplicate) {
        // Clear data if it's a duplicate to prevent re-rendering
        clearData();
        return prev;
      }

      return [...prev, lessonPlan];
    });

    // Clear data after adding to history (runs after state update)
    const timeoutId = setTimeout(() => clearData(), 100);

    return () => clearTimeout(timeoutId);
  }, [lessonPlan, streamingState, clearData]);

  // Update URL when new thread is created
  useEffect(() => {
    const shouldUpdateUrl =
      threadId && !urlThreadId && !isLoadingFromUrlRef.current;

    if (shouldUpdateUrl) {
      navigate(`/lesson-planner/${threadId}`, { replace: true });
      // Trigger sidebar refetch when a new conversation is created
      sidebarRef.current?.refetchConversations();
    }
  }, [threadId, urlThreadId, navigate]);

  // Load conversation from URL
  useEffect(() => {
    const loadConversation = async () => {
      // Exit early if no thread ID or already loaded
      if (!urlThreadId || loadedThreadIdRef.current === urlThreadId) {
        if (!urlThreadId) loadedThreadIdRef.current = null;
        return;
      }

      // Mark as loaded and prevent URL updates during load
      loadedThreadIdRef.current = urlThreadId;
      isLoadingFromUrlRef.current = true;

      // Clear previous data
      setUserMessages([]);
      setLessonHistory([]);
      setUserComment("");

      try {
        // Fetch metadata and history
        const [conversation, history] = await Promise.all([
          fetchConversation(urlThreadId),
          fetchConversationHistory(urlThreadId)
        ]);

        // Set thread ID for continuation
        setThreadId(urlThreadId);

        // Restore form state
        if ("lesson_title" in conversation) {
          setClassTitle(conversation.lesson_title);
        }
        setHasStarted(true);

        // Parse message history
        const userMsgs: ConversationMessage[] = [];
        const plans: LessonPlan[] = [];

        history.messages.forEach((msg) => {
          if (msg.role === "user") {
            userMsgs.push(createUserMessage(msg.content));
          } else if (msg.role === "assistant") {
            try {
              plans.push(JSON.parse(msg.content));
            } catch (e) {
              console.error("Failed to parse lesson plan:", e);
            }
          }
        });

        // Update state
        setUserMessages(userMsgs);
        setLessonHistory(plans);
      } catch (error) {
        console.error("Failed to load conversation:", error);
        navigate("/lesson-planner", { replace: true });
      } finally {
        // Reset loading flag after render cycle
        setTimeout(() => {
          isLoadingFromUrlRef.current = false;
        }, 0);
      }
    };

    loadConversation();
  }, [urlThreadId, setThreadId, navigate]);

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleInitialSubmit = useCallback(async () => {
    // Validation
    if (!courseTitle.trim()) {
      alert(UI_MESSAGES.EMPTY_COURSE_TITLE);
      return;
    }
    if (!classTitle.trim()) {
      alert(UI_MESSAGES.EMPTY_CLASS_TITLE);
      return;
    }
    if (
      classNumber < LESSON_PLAN.MIN_CLASS_NUMBER ||
      classNumber > LESSON_PLAN.MAX_CLASS_NUMBER
    ) {
      alert(UI_MESSAGES.INVALID_CLASS_NUMBER);
      return;
    }

    // Filter out empty strings from arrays
    const filteredObjectives = learningObjectives.filter((obj) => obj.trim());
    const filteredTopics = keyTopics.filter((topic) => topic.trim());
    const filteredActivities = activitiesProjects.filter((act) => act.trim());

    // Validate array lengths
    if (
      filteredObjectives.length < LESSON_PLAN.MIN_OBJECTIVES ||
      filteredObjectives.length > LESSON_PLAN.MAX_OBJECTIVES
    ) {
      alert(
        `Please provide ${LESSON_PLAN.MIN_OBJECTIVES}-${LESSON_PLAN.MAX_OBJECTIVES} learning objectives`
      );
      return;
    }
    if (
      filteredTopics.length < LESSON_PLAN.MIN_TOPICS ||
      filteredTopics.length > LESSON_PLAN.MAX_TOPICS
    ) {
      alert(
        `Please provide ${LESSON_PLAN.MIN_TOPICS}-${LESSON_PLAN.MAX_TOPICS} key topics`
      );
      return;
    }
    if (
      filteredActivities.length < LESSON_PLAN.MIN_ACTIVITIES ||
      filteredActivities.length > LESSON_PLAN.MAX_ACTIVITIES
    ) {
      alert(
        `Please provide ${LESSON_PLAN.MIN_ACTIVITIES}-${LESSON_PLAN.MAX_ACTIVITIES} activities`
      );
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
    uploadedFiles,
    sendMessage
  ]);

  const handleFollowUpSubmit = useCallback(
    async (message: string, files: File[]) => {
      if (!message.trim() && files.length === 0) return;

      // Filter out empty strings from arrays
      const filteredObjectives = learningObjectives.filter((obj) => obj.trim());
      const filteredTopics = keyTopics.filter((topic) => topic.trim());
      const filteredActivities = activitiesProjects.filter((act) => act.trim());

      // Add user message to history
      const userMessage = createUserMessage(message, files);
      setUserMessages((prev) => [...prev, userMessage]);

      // Send to backend (lesson plan will be added via useEffect)
      await sendMessage({
        message,
        course_title: courseTitle,
        class_number: classNumber,
        class_title: classTitle,
        learning_objectives: filteredObjectives,
        key_topics: filteredTopics,
        activities_projects: filteredActivities,
        thread_id: threadId || undefined,
        files
      });
    },
    [
      courseTitle,
      classNumber,
      classTitle,
      learningObjectives,
      keyTopics,
      activitiesProjects,
      threadId,
      sendMessage
    ]
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
    setLearningObjectives(["", ""]);
    setKeyTopics(["", "", ""]);
    setActivitiesProjects([""]);
    setUserComment("");
    setUploadedFiles([]);
    loadedThreadIdRef.current = null;

    // Navigate to base route
    navigate("/lesson-planner", { replace: true });
  }, [resetThread, navigate]);

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
      <Header title="Lesson Planner" />
      <ThreadStatus
        threadId={threadId}
        onNewConversation={handleNewConversation}
      />

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
          onSubmit={handleInitialSubmit}
          threadId={threadId}
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

export default LessonPlanner;
