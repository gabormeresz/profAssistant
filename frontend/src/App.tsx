import { useState } from "react";
import { Layout, Header, InputSection, OutputSection } from "./components";
import { useWebSocket } from "./hooks";

function App() {
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState(1);

  const { currentMessage, threadId, sendMessage, resetThread, streamingState } =
    useWebSocket("ws://localhost:8000/ws");

  const handleSubmit = () => {
    sendMessage({
      message: userComment,
      topic: topic,
      number_of_classes: numberOfClasses
    });
  };

  const handleNewConversation = () => {
    resetThread();
    setUserComment("");
    setTopic("");
    setNumberOfClasses(1);
  };

  return (
    <Layout>
      <Header />

      {/* Show thread status and new conversation button */}
      {threadId && (
        <div className="mb-4 flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-blue-700">
              Active conversation (memory enabled)
            </span>
          </div>
          <button
            onClick={handleNewConversation}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            New Conversation
          </button>
        </div>
      )}

      <InputSection
        userComment={userComment}
        setUserComment={setUserComment}
        topic={topic}
        setTopic={setTopic}
        numberOfClasses={numberOfClasses}
        setNumberOfClasses={setNumberOfClasses}
        onSubmit={handleSubmit}
        streamingState={streamingState}
      />
      <OutputSection
        streamingState={streamingState}
        currentMessage={currentMessage}
      />
    </Layout>
  );
}
export default App;
