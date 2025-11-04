import { useState } from "react";
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

function StructuredOutlineGenerator() {
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

  // Structured SSE hook
  const {
    courseOutline,
    progressMessage,
    loading,
    streamingState,
    threadId,
    sendMessage,
    resetThread
  } = useStructuredSSE();

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
    const result = await sendMessage({
      message: userComment,
      topic,
      number_of_classes: numberOfClasses,
      files: uploadedFiles
    });

    // Store outline in history
    if (result) {
      setOutlineHistory((prev) => [...prev, result]);
    }
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
    const result = await sendMessage({
      message,
      topic,
      number_of_classes: numberOfClasses,
      thread_id: threadId || undefined,
      files
    });

    // Store outline in history
    if (result) {
      setOutlineHistory((prev) => [...prev, result]);
    }
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
  };

  const isGenerating =
    loading ||
    streamingState === "streaming" ||
    streamingState === "connecting";

  return (
    <Layout>
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

        {/* Show current outline being generated */}
        {courseOutline && isGenerating && (
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
