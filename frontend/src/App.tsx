import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import {
  Home,
  LessonPlanGenerator,
  CourseOutlineGenerator,
  PresentationGenerator,
  AssessmentGenerator,
  AuthPage,
  ProfilePage
} from "./pages";
import { SavedConversationsProvider } from "./contexts/SavedConversationsContext";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components";

function App() {
  return (
    <Router>
      <AuthProvider>
        <SavedConversationsProvider>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/course-outline-generator"
              element={
                <ProtectedRoute>
                  <CourseOutlineGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/course-outline-generator/:threadId"
              element={
                <ProtectedRoute>
                  <CourseOutlineGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lesson-plan-generator"
              element={
                <ProtectedRoute>
                  <LessonPlanGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lesson-plan-generator/:threadId"
              element={
                <ProtectedRoute>
                  <LessonPlanGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/presentation-generator"
              element={
                <ProtectedRoute>
                  <PresentationGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/presentation-generator/:threadId"
              element={
                <ProtectedRoute>
                  <PresentationGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assessment-generator"
              element={
                <ProtectedRoute>
                  <AssessmentGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assessment-generator/:threadId"
              element={
                <ProtectedRoute>
                  <AssessmentGenerator />
                </ProtectedRoute>
              }
            />
          </Routes>
        </SavedConversationsProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
