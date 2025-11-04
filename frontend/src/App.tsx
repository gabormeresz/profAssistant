import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Home, OutlineGenerator } from "./pages";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/outline-generator" element={<OutlineGenerator />} />
      </Routes>
    </Router>
  );
}

export default App;
