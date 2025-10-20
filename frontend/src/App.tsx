import { useState } from "react";
import {
  Layout,
  Header,
  InputSection,
  OutputSection,
  ThreadStatus
} from "./components";
import { useSSE } from "./hooks";

function App() {
  const [userComment, setUserComment] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const { currentMessage, threadId, sendMessage, resetThread, streamingState } =
    useSSE("http://localhost:8000/stream");

  const handleSubmit = () => {
    sendMessage({
      message: userComment,
      topic: topic,
      number_of_classes: numberOfClasses,
      files: uploadedFiles
    });
  };

  const handleNewConversation = () => {
    resetThread();
    setUserComment("");
    setTopic("");
    setNumberOfClasses(1);
    setUploadedFiles([]);
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
        uploadedFiles={uploadedFiles}
        setUploadedFiles={setUploadedFiles}
      />
      <OutputSection
        streamingState={streamingState}
        currentMessage={currentMessage}
      />
    </Layout>
  );
}
export default App;
