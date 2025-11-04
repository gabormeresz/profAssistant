import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import {
  Home,
  LessonPlanner,
  OutlineGenerator,
  StructuredOutlineGenerator
} from "./pages";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/outline-generator" element={<OutlineGenerator />} />
        <Route
          path="/structured-outline"
          element={<StructuredOutlineGenerator />}
        />

        <Route path="/lesson-planner" element={<LessonPlanner />} />
      </Routes>
    </Router>
  );
}

export default App;
