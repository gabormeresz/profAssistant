import { useState, useEffect, useRef, useCallback } from "react";
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
import type { SidebarRef } from "../components";
import { useCourseOutlineSSE } from "../hooks";
import { COURSE_OUTLINE, UI_MESSAGES } from "../utils/constants";
import type { CourseOutline, ConversationMessage } from "../types";
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
 * Extracts the user's original comment from a backend-constructed message.
 * Removes auto-generated prefix and file contents sections.
 */
function extractUserComment(content: string): string {
  let cleanedContent = content;

  // Remove auto-generated prefix: "Create a course outline on 'Topic' with N classes.\n"
  const prefixPattern = /^Create a course outline on .+ with \d+ classes\.\n/;
  const match = cleanedContent.match(prefixPattern);
  if (match) {
    cleanedContent = cleanedContent.substring(match[0].length);
  }

  // Remove file contents section if present
  const fileContentsPattern = /\n\nUploaded files:[\s\S]*$/;
  cleanedContent = cleanedContent.replace(fileContentsPattern, "");

  return cleanedContent.trim();
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
  const sidebarRef = useRef<SidebarRef>(null);

  // ============================================================================
  // State Management
  // ============================================================================

  // Form state
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState<number>(
    COURSE_OUTLINE.DEFAULT_CLASSES
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Conversation history
  const [outlineHistory, setOutlineHistory] = useState<CourseOutline[]>([]);
  const [userMessages, setUserMessages] = useState<ConversationMessage[]>([]);
  const [hasStarted, setHasStarted] = useState(false);

  // Refs to prevent duplicate loading and URL update loops
  const loadedThreadIdRef = useRef<string | null>(null);
  const isLoadingFromUrlRef = useRef(false);

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

  // ============================================================================
  // Effects
  // ============================================================================

  // Auto-add completed outlines to history
  useEffect(() => {
    if (!courseOutline || streamingState !== "complete") return;

    setOutlineHistory((prev) => {
      // Prevent duplicates by checking if outline already exists
      const isDuplicate = prev.some(
        (outline) => JSON.stringify(outline) === JSON.stringify(courseOutline)
      );

      if (isDuplicate) {
        // Clear data if it's a duplicate to prevent re-rendering
        clearData();
        return prev;
      }

      return [...prev, courseOutline];
    });

    // Clear data after adding to history (runs after state update)
    const timeoutId = setTimeout(() => clearData(), 100);

    return () => clearTimeout(timeoutId);
  }, [courseOutline, streamingState, clearData]);

  // Update URL when new thread is created
  useEffect(() => {
    const shouldUpdateUrl =
      threadId && !urlThreadId && !isLoadingFromUrlRef.current;

    if (shouldUpdateUrl) {
      navigate(`/outline-generator/${threadId}`, { replace: true });
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
      setOutlineHistory([]);
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
        if ("topic" in conversation) {
          setTopic(conversation.topic);
          setNumberOfClasses(conversation.number_of_classes);
        }
        setHasStarted(true);

        // Parse message history
        const userMsgs: ConversationMessage[] = [];
        const outlines: CourseOutline[] = [];
        let firstUserComment = "";

        history.messages.forEach((msg) => {
          if (msg.role === "user") {
            const cleanedComment = extractUserComment(msg.content);

            // Store first comment for input field
            if (userMsgs.length === 0) {
              firstUserComment = cleanedComment;
            }

            userMsgs.push(createUserMessage(cleanedComment));
          } else if (msg.role === "assistant") {
            try {
              outlines.push(JSON.parse(msg.content));
            } catch (e) {
              console.error("Failed to parse course outline:", e);
            }
          }
        });

        // Update state
        setUserMessages(userMsgs);
        setOutlineHistory(outlines);
        if (firstUserComment) setUserComment(firstUserComment);
      } catch (error) {
        console.error("Failed to load conversation:", error);
        navigate("/outline-generator", { replace: true });
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
      files: uploadedFiles
    });
  }, [topic, userComment, uploadedFiles, numberOfClasses, sendMessage]);

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
        thread_id: threadId || undefined,
        files
      });
    },
    [topic, numberOfClasses, threadId, sendMessage]
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
    setUploadedFiles([]);
    loadedThreadIdRef.current = null;

    // Navigate to base route
    navigate("/outline-generator", { replace: true });
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
