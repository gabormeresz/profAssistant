import { useState } from "react";
import {
  Layout,
  Header,
  InputSection,
  OutputSection,
  ThreadStatus
} from "./components";
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
      <ThreadStatus
        threadId={threadId}
        onNewConversation={handleNewConversation}
      />
      <InputSection
        userComment={userComment}
        setUserComment={setUserComment}
        topic={topic}
        setTopic={setTopic}
        numberOfClasses={numberOfClasses}
        setNumberOfClasses={setNumberOfClasses}
        onSubmit={handleSubmit}
        streamingState={streamingState}
        threadId={threadId}
      />
      <OutputSection
        streamingState={streamingState}
        currentMessage={currentMessage}
      />
    </Layout>
  );
}
export default App;
