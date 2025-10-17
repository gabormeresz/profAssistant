import { useState } from "react";
import { Layout, Header, InputSection, OutputSection } from "./components";
import { useWebSocket } from "./hooks";

function App() {
  const [input, setInput] = useState("");
  const [topic, setTopic] = useState("");
  const [numberOfClasses, setNumberOfClasses] = useState(1);

  const { currentMessage, loading, sendMessage } = useWebSocket(
    "ws://localhost:8000/ws"
  );

  const handleSubmit = () => {
    if (input.trim()) {
      sendMessage({
        message: input,
        topic: topic,
        number_of_classes: numberOfClasses
      });
    }
  };

  return (
    <Layout>
      <Header />
      <InputSection
        input={input}
        setInput={setInput}
        topic={topic}
        setTopic={setTopic}
        numberOfClasses={numberOfClasses}
        setNumberOfClasses={setNumberOfClasses}
        onSubmit={handleSubmit}
        loading={loading}
      />
      <OutputSection loading={loading} currentMessage={currentMessage} />
    </Layout>
  );
}
export default App;
