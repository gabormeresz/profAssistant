import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Home, LessonPlanner, OutlineGenerator } from "./pages";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/outline-generator" element={<OutlineGenerator />} />
        <Route path="/lesson-planner" element={<LessonPlanner />} />
      </Routes>
    </Router>
  );
}

export default App;
