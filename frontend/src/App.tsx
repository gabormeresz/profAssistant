import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Home, LessonPlanner, CourseOutlineGenerator } from "./pages";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/outline-generator" element={<CourseOutlineGenerator />} />
        <Route
          path="/outline-generator/:threadId"
          element={<CourseOutlineGenerator />}
        />
        <Route path="/lesson-planner" element={<LessonPlanner />} />
        <Route
          path="/lesson-planner/:threadId"
          element={<LessonPlanner />}
        />
      </Routes>
    </Router>
  );
}

export default App;
