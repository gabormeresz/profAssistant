import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import {
  Home,
  LessonPlanGenerator,
  CourseOutlineGenerator,
  PresentationGenerator,
  AssessmentGenerator
} from "./pages";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/course-outline-generator"
          element={<CourseOutlineGenerator />}
        />
        <Route
          path="/course-outline-generator/:threadId"
          element={<CourseOutlineGenerator />}
        />
        <Route
          path="/lesson-plan-generator"
          element={<LessonPlanGenerator />}
        />
        <Route
          path="/lesson-plan-generator/:threadId"
          element={<LessonPlanGenerator />}
        />
        <Route
          path="/presentation-generator"
          element={<PresentationGenerator />}
        />
        <Route
          path="/presentation-generator/:threadId"
          element={<PresentationGenerator />}
        />
        <Route path="/assessment-generator" element={<AssessmentGenerator />} />
        <Route
          path="/assessment-generator/:threadId"
          element={<AssessmentGenerator />}
        />
      </Routes>
    </Router>
  );
}

export default App;
