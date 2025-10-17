import { useState } from "react";
import { Layout, Header, InputSection, OutputSection } from "./components";
import { useWebSocket } from "./hooks";

function App() {
  const [input, setInput] = useState("");
  const { currentMessage, loading, sendMessage } = useWebSocket(
    "ws://localhost:8000/ws"
  );

  const handleSubmit = () => {
    if (input.trim()) {
      sendMessage(input);
    }
  };

  return (
    <Layout>
      <Header />
      <InputSection
        input={input}
        setInput={setInput}
        onSubmit={handleSubmit}
        loading={loading}
      />
      <OutputSection loading={loading} currentMessage={currentMessage} />
    </Layout>
  );
}
export default App;
