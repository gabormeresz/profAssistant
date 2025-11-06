import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Layout,
  Header,
  InputSection,
  ThreadStatus,
  StructuredCourseOutline,
  ProgressIndicator,
  FollowUpInput,
  UserMessage
} from "../components";
import { useStructuredSSE } from "../hooks";
import { COURSE_OUTLINE, UI_MESSAGES } from "../utils/constants";
import type { CourseOutline, ConversationMessage } from "../types";
import {
  fetchConversation,
  fetchConversationHistory
} from "../services/conversationService";

function StructuredOutlineGenerator() {
  const { threadId: urlThreadId } = useParams<{ threadId?: string }>();
  const navigate = useNavigate();

  // Form state
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState<number>(
    COURSE_OUTLINE.DEFAULT_CLASSES
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Store all course outlines from conversation
  const [outlineHistory, setOutlineHistory] = useState<CourseOutline[]>([]);
  const [userMessages, setUserMessages] = useState<ConversationMessage[]>([]);
  const [hasStarted, setHasStarted] = useState(false);

  // Track which conversation was last loaded to prevent stale data
  const loadedThreadIdRef = useRef<string | null>(null);
  // Track if we're loading from URL to prevent URL update loops
  const isLoadingFromUrlRef = useRef(false);

  // Structured SSE hook
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
  } = useStructuredSSE();

  // When a new outline is generated and streaming is complete, add it to history and clear
  useEffect(() => {
    if (courseOutline && streamingState === "complete") {
      setOutlineHistory((prev) => {
        // Check if this outline is already in the history to avoid duplicates
        const isAlreadyInHistory = prev.some(
          (outline) => JSON.stringify(outline) === JSON.stringify(courseOutline)
        );

        if (isAlreadyInHistory) {
          return prev;
        }

        // Add the new outline and clear the SSE state
        setTimeout(() => clearData(), 100);
        return [...prev, courseOutline];
      });
    }
  }, [courseOutline, streamingState, clearData]);

  // Update URL when thread_id changes from SSE (only for NEW conversations)
  useEffect(() => {
    // Only update URL if:
    // 1. We have a threadId from SSE
    // 2. There's NO threadId in the URL yet (new conversation)
    // 3. We're not currently loading from URL
    if (threadId && !urlThreadId && !isLoadingFromUrlRef.current) {
      // Update URL without causing a navigation/reload
      navigate(`/structured-outline/${threadId}`, { replace: true });
    }
  }, [threadId, urlThreadId, navigate]);

  // Load conversation from URL parameter
  useEffect(() => {
    const loadFromUrl = async () => {
      if (!urlThreadId) {
        // No thread ID in URL, this is a new conversation
        loadedThreadIdRef.current = null;
        return;
      }

      // Skip if we already loaded this conversation
      if (loadedThreadIdRef.current === urlThreadId) {
        return;
      }

      // Mark this conversation as being loaded FIRST
      // This prevents the check above from running the load twice
      loadedThreadIdRef.current = urlThreadId;

      // Mark that we're loading from URL to prevent URL update loop
      isLoadingFromUrlRef.current = true;

      // Clear previous conversation data first
      setUserMessages([]);
      setOutlineHistory([]);
      setUserComment("");

      try {
        // Fetch conversation metadata
        const conversation = await fetchConversation(urlThreadId);

        // Set the thread ID to continue the conversation
        setThreadId(urlThreadId);

        // Reset flag after React finishes the render cycle
        // This ensures the URL update effect sees the flag as true
        setTimeout(() => {
          isLoadingFromUrlRef.current = false;
        }, 0);

        // Populate form with saved data
        if ("topic" in conversation) {
          setTopic(conversation.topic);
          setNumberOfClasses(conversation.number_of_classes);
        }
        setHasStarted(true);

        // Load conversation history (messages and outlines)
        const history = await fetchConversationHistory(urlThreadId);

        // Parse messages to separate user messages and assistant outlines
        const userMsgs: ConversationMessage[] = [];
        const outlines: CourseOutline[] = [];
        let firstUserComment = "";

        history.messages.forEach((msg, index) => {
          if (msg.role === "user") {
            // User message - need to parse out the user's original comment
            // Backend constructs messages as: "Create a course outline on '{topic}' with {number_of_classes} classes.\n{user_comment}\n\n"
            let userComment = msg.content;

            // Try to extract just the user comment by removing the generated prefix
            const prefixPattern =
              /^Create a course outline on .+ with \d+ classes\.\n/;
            const match = userComment.match(prefixPattern);
            if (match) {
              // Remove the prefix to get just the user's comment
              userComment = userComment.substring(match[0].length).trim();
            }

            // Remove file contents section if present
            const fileContentsPattern = /\n\nUploaded files:[\s\S]*$/;
            userComment = userComment.replace(fileContentsPattern, "").trim();

            // Save the first user comment to populate the input field
            if (index === 0 || userMsgs.length === 0) {
              firstUserComment = userComment;
            }

            userMsgs.push({
              id: `user-${index}`,
              role: "user",
              content: userComment,
              timestamp: new Date(), // We don't have the original timestamp
              topic: "topic" in conversation ? conversation.topic : "",
              numberOfClasses:
                "number_of_classes" in conversation
                  ? conversation.number_of_classes
                  : 0
            });
          } else if (msg.role === "assistant") {
            // Assistant message - parse as CourseOutline
            try {
              const outline = JSON.parse(msg.content);
              outlines.push(outline);
            } catch (e) {
              console.error(
                "Failed to parse assistant message as course outline:",
                e
              );
            }
          }
        });

        setUserMessages(userMsgs);
        setOutlineHistory(outlines);

        // Set the initial user comment in the input field
        if (firstUserComment) {
          setUserComment(firstUserComment);
        }
      } catch (error) {
        console.error("Failed to load conversation from URL:", error);
        // If conversation not found, redirect to new conversation
        navigate("/structured-outline", { replace: true });
        // Reset flag on error as well
        setTimeout(() => {
          isLoadingFromUrlRef.current = false;
        }, 0);
      }
    };

    loadFromUrl();
  }, [urlThreadId, setThreadId, navigate]);

  // Handle initial form submission
  const handleInitialSubmit = async () => {
    if (!topic.trim()) {
      alert(UI_MESSAGES.EMPTY_TOPIC);
      return;
    }

    setHasStarted(true);

    // Add user message
    const userMessage: ConversationMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userComment,
      timestamp: new Date(),
      files: uploadedFiles?.map((f) => ({ name: f.name, size: f.size })),
      topic,
      numberOfClasses
    };
    setUserMessages((prev) => [...prev, userMessage]);

    // Send to backend
    await sendMessage({
      message: userComment,
      topic,
      number_of_classes: numberOfClasses,
      files: uploadedFiles
    });

    // Note: The outline will be automatically added to outlineHistory via useEffect
  };

  // Handle follow-up messages
  const handleFollowUpSubmit = async (message: string, files: File[]) => {
    if (!message.trim() && files.length === 0) return;

    // Add user message
    const userMessage: ConversationMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
      timestamp: new Date(),
      files: files?.map((f) => ({ name: f.name, size: f.size }))
    };
    setUserMessages((prev) => [...prev, userMessage]);

    // Send to backend with the same thread
    await sendMessage({
      message,
      topic,
      number_of_classes: numberOfClasses,
      thread_id: threadId || undefined,
      files
    });

    // Note: The outline will be automatically added to outlineHistory via useEffect
  };

  // Handle new conversation
  const handleNewConversation = () => {
    resetThread();
    setOutlineHistory([]);
    setUserMessages([]);
    setHasStarted(false);
    setUserComment("");
    setTopic("");
    setNumberOfClasses(COURSE_OUTLINE.DEFAULT_CLASSES);
    setUploadedFiles([]);
    loadedThreadIdRef.current = null; // Reset loaded thread tracking

    // Navigate to base URL for new conversation
    navigate("/structured-outline", { replace: true });
  };

  const isGenerating =
    loading ||
    streamingState === "streaming" ||
    streamingState === "connecting";

  return (
    <Layout showSidebar>
      <Header title="Course Outline Generator (Structured Output)" />
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

      {/* Display conversation: user messages and course outline responses */}
      <div className="space-y-6">
        {userMessages.map((userMsg, index) => (
          <div key={userMsg.id}>
            {/* User message */}
            <UserMessage message={userMsg} />

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

export default StructuredOutlineGenerator;
