// API Configuration — single source of truth for the backend URL.
// In Docker/production, set VITE_API_URL at build time (or leave empty to
// use the nginx reverse-proxy on the same origin).
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";
export const API_ENDPOINTS = {
  COURSE_OUTLINE_GENERATOR: `${API_BASE_URL}/course-outline-generator`,
  LESSON_PLAN_GENERATOR: `${API_BASE_URL}/lesson-plan-generator`,
  PRESENTATION_GENERATOR: `${API_BASE_URL}/presentation-generator`,
  ASSESSMENT_GENERATOR: `${API_BASE_URL}/assessment-generator`,
  ENHANCE_PROMPT: `${API_BASE_URL}/enhance-prompt`,
  EXPORT_PRESENTATION_PPTX: `${API_BASE_URL}/export-presentation-pptx`
} as const;

// File Upload Configuration
export const FILE_UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB in bytes
  MAX_SIZE_MB: 10,
  ALLOWED_TYPES: [
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown"
  ] as const,
  ALLOWED_EXTENSIONS: [".txt", ".pdf", ".docx", ".md"] as const,
  ERROR_MESSAGES: {
    TOO_LARGE: (filename: string, maxSize: number) =>
      `File ${filename} is too large. Max size is ${maxSize}MB.`,
    UNSUPPORTED_TYPE: (filename: string) =>
      `File ${filename} type not supported. Allowed: PDF, DOCX, TXT, MD`
  }
} as const;

// Prompt Enhancement
export const PROMPT_ENHANCEMENT = {
  MIN_LENGTH: 5,
  ERROR_MESSAGES: {
    EMPTY_FIELDS: "Please enter both a topic and a comment to enhance.",
    GENERIC_ERROR: "Failed to enhance prompt"
  }
} as const;

// Course Outline Configuration
export const COURSE_OUTLINE = {
  MIN_CLASSES: 1,
  MAX_CLASSES: 20,
  DEFAULT_CLASSES: 1
} as const;

// Lesson Plan Configuration
export const LESSON_PLAN = {
  MIN_CLASS_NUMBER: 1,
  MAX_CLASS_NUMBER: 100,
  MIN_OBJECTIVES: 0, // Optional - can be empty
  MAX_OBJECTIVES: 5,
  MIN_TOPICS: 0, // Optional - can be empty
  MAX_TOPICS: 7,
  MIN_ACTIVITIES: 0, // Optional - can be empty
  MAX_ACTIVITIES: 5
} as const;

// Presentation Configuration
export const PRESENTATION = {
  MIN_CLASS_NUMBER: 1,
  MAX_CLASS_NUMBER: 100,
  MAX_KEY_POINTS: 10
} as const;

// Assessment Configuration
export const ASSESSMENT = {
  MAX_OBJECTIVES: 5,
  MAX_TOPICS: 7,
  MAX_QUESTION_TYPES: 4,
  MAX_QUESTIONS_PER_TYPE: 20,
  MAX_POINTS_PER_QUESTION: 100
} as const;

// UI Messages
export const UI_MESSAGES = {
  EMPTY_TOPIC: "Please enter a topic",
  EMPTY_COURSE_TITLE: "Please enter a course title",
  EMPTY_CLASS_TITLE: "Please enter a class title",
  INVALID_CLASS_NUMBER: "Please enter a valid class number"
} as const;
