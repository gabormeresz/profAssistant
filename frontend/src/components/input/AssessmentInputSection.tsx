import type { Dispatch, SetStateAction } from "react";
import { useTranslation } from "react-i18next";
import FileUpload from "./FileUpload";
import PromptEnhancer from "./PromptEnhancer";
import type {
  QuestionTypeConfig,
  AssessmentPreset
} from "../../types/assessment";

interface AssessmentInputSectionProps {
  courseTitle: string;
  setCourseTitle: Dispatch<SetStateAction<string>>;
  classTitle: string;
  setClassTitle: Dispatch<SetStateAction<string>>;
  keyTopics: string[];
  setKeyTopics: Dispatch<SetStateAction<string[]>>;
  assessmentType: string;
  setAssessmentType: Dispatch<SetStateAction<string>>;
  difficultyLevel: string;
  setDifficultyLevel: Dispatch<SetStateAction<string>>;
  questionTypeConfigs: QuestionTypeConfig[];
  setQuestionTypeConfigs: Dispatch<SetStateAction<QuestionTypeConfig[]>>;
  preset: AssessmentPreset;
  setPreset: Dispatch<SetStateAction<AssessmentPreset>>;
  additionalInstructions: string;
  setAdditionalInstructions: Dispatch<SetStateAction<string>>;
  uploadedFiles: File[];
  setUploadedFiles: Dispatch<SetStateAction<File[]>>;
  language: string;
  setLanguage: Dispatch<SetStateAction<string>>;
  onSubmit: () => void;
  threadId: string | null;
  onEnhancerLoadingChange?: (isLoading: boolean) => void;
  displayFiles?: Array<{ name: string }>;
  isPrefilled?: boolean;
}

export const PRESET_CONFIGS: Record<
  Exclude<AssessmentPreset, "custom">,
  { type: string; difficulty: string; configs: QuestionTypeConfig[] }
> = {
  quick_quiz: {
    type: "quiz",
    difficulty: "mixed",
    configs: [
      { type: "multiple_choice", count: 5, points_each: 2 },
      { type: "true_false", count: 5, points_each: 1 }
    ]
  },
  midterm_exam: {
    type: "exam",
    difficulty: "mixed",
    configs: [
      { type: "multiple_choice", count: 10, points_each: 2 },
      { type: "true_false", count: 5, points_each: 1 },
      { type: "short_answer", count: 5, points_each: 4 },
      { type: "essay", count: 1, points_each: 15 }
    ]
  },
  homework: {
    type: "homework",
    difficulty: "medium",
    configs: [
      { type: "short_answer", count: 5, points_each: 4 },
      { type: "essay", count: 1, points_each: 10 }
    ]
  },
  practice_test: {
    type: "practice",
    difficulty: "easy",
    configs: [
      { type: "multiple_choice", count: 8, points_each: 2 },
      { type: "true_false", count: 4, points_each: 1 },
      { type: "short_answer", count: 3, points_each: 3 }
    ]
  }
};

const QUESTION_TYPES: QuestionTypeConfig["type"][] = [
  "multiple_choice",
  "true_false",
  "short_answer",
  "essay"
];

export function AssessmentInputSection({
  courseTitle,
  setCourseTitle,
  classTitle,
  setClassTitle,
  keyTopics,
  setKeyTopics,
  assessmentType,
  setAssessmentType,
  difficultyLevel,
  setDifficultyLevel,
  questionTypeConfigs,
  setQuestionTypeConfigs,
  preset,
  setPreset,
  additionalInstructions,
  setAdditionalInstructions,
  uploadedFiles,
  setUploadedFiles,
  language,
  setLanguage,
  onSubmit,
  threadId,
  onEnhancerLoadingChange,
  displayFiles,
  isPrefilled
}: AssessmentInputSectionProps) {
  const { t } = useTranslation();

  const isButtonDisabled =
    !courseTitle.trim() || keyTopics.filter((t) => t.trim()).length === 0;

  // Helper functions for array fields
  const handleArrayChange = (
    index: number,
    value: string,
    array: string[],
    setter: Dispatch<SetStateAction<string[]>>
  ) => {
    const newArray = [...array];
    newArray[index] = value;
    setter(newArray);
  };

  const addArrayItem = (
    array: string[],
    setter: Dispatch<SetStateAction<string[]>>
  ) => {
    setter([...array, ""]);
  };

  const removeArrayItem = (
    index: number,
    array: string[],
    setter: Dispatch<SetStateAction<string[]>>
  ) => {
    if (array.length > 1) {
      setter(array.filter((_, i) => i !== index));
    }
  };

  // Preset handling
  const handlePresetChange = (newPreset: AssessmentPreset) => {
    setPreset(newPreset);
    if (newPreset !== "custom") {
      const config = PRESET_CONFIGS[newPreset];
      setAssessmentType(config.type);
      setDifficultyLevel(config.difficulty);
      setQuestionTypeConfigs(config.configs);
    }
  };

  // Question type config management
  const handleConfigChange = (
    index: number,
    field: keyof QuestionTypeConfig,
    value: string | number
  ) => {
    const newConfigs = [...questionTypeConfigs];
    newConfigs[index] = { ...newConfigs[index], [field]: value };
    setQuestionTypeConfigs(newConfigs);
    setPreset("custom");
  };

  const addQuestionType = () => {
    // Find a type not yet in configs
    const usedTypes = questionTypeConfigs.map((c) => c.type);
    const available = QUESTION_TYPES.find((t) => !usedTypes.includes(t));
    if (available) {
      setQuestionTypeConfigs([
        ...questionTypeConfigs,
        { type: available, count: 3, points_each: 2 }
      ]);
      setPreset("custom");
    }
  };

  const removeQuestionType = (index: number) => {
    if (questionTypeConfigs.length > 1) {
      setQuestionTypeConfigs(questionTypeConfigs.filter((_, i) => i !== index));
      setPreset("custom");
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <div className="space-y-4">
        {/* Course Title */}
        <div className="mb-6">
          <label
            htmlFor="courseTitle"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {t("assessment.courseTitle")}{" "}
            <span className="text-red-500 dark:text-red-400">*</span>
          </label>
          <input
            type="text"
            id="courseTitle"
            value={courseTitle}
            onChange={(e) => setCourseTitle(e.target.value)}
            placeholder={t("assessment.courseTitlePlaceholder")}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>

        {/* Class / Lesson Title */}
        <div className="mb-6">
          <label
            htmlFor="classTitle"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {t("assessment.classTitle")}
          </label>
          <input
            type="text"
            id="classTitle"
            value={classTitle}
            onChange={(e) => setClassTitle(e.target.value)}
            placeholder={t("assessment.classTitlePlaceholder")}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>

        {/* Language Selection */}
        <div className="mb-6">
          <label
            htmlFor="language"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {t("assessment.language")}{" "}
            <span className="text-red-500 dark:text-red-400">*</span>
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="English">English</option>
            <option value="Hungarian">Hungarian</option>
          </select>
        </div>

        {/* Key Topics (merged with former learning objectives) */}
        <div className="mb-6">
          {isPrefilled && (
            <div className="mb-2 flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {t("assessment.prefilledHint")}
            </div>
          )}
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              {t("assessment.keyTopics")}{" "}
              <span className="text-red-500 dark:text-red-400">*</span>
            </label>
            {keyTopics.length < 10 && (
              <button
                type="button"
                onClick={() => addArrayItem(keyTopics, setKeyTopics)}
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
              >
                {t("assessment.addTopic")}
              </button>
            )}
          </div>
          <div className="space-y-2">
            {keyTopics.map((topic, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={topic}
                  onChange={(e) =>
                    handleArrayChange(
                      index,
                      e.target.value,
                      keyTopics,
                      setKeyTopics
                    )
                  }
                  placeholder={t("assessment.keyTopicsPlaceholder")}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                {keyTopics.length > 1 && (
                  <button
                    type="button"
                    onClick={() =>
                      removeArrayItem(index, keyTopics, setKeyTopics)
                    }
                    className="px-3 py-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Assessment Preset Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t("assessment.preset")}
          </label>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {(
              [
                "quick_quiz",
                "midterm_exam",
                "homework",
                "practice_test",
                "custom"
              ] as AssessmentPreset[]
            ).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => handlePresetChange(p)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors border ${
                  preset === p
                    ? "bg-blue-600 dark:bg-blue-500 text-white border-blue-600 dark:border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600"
                }`}
              >
                {t(`assessment.presets.${p}`)}
              </button>
            ))}
          </div>
        </div>

        {/* Assessment Type & Difficulty */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label
              htmlFor="assessmentType"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              {t("assessment.assessmentType")}{" "}
              <span className="text-red-500 dark:text-red-400">*</span>
            </label>
            <select
              id="assessmentType"
              value={assessmentType}
              onChange={(e) => {
                setAssessmentType(e.target.value);
                setPreset("custom");
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="quiz">{t("assessment.types.quiz")}</option>
              <option value="exam">{t("assessment.types.exam")}</option>
              <option value="homework">{t("assessment.types.homework")}</option>
              <option value="practice">{t("assessment.types.practice")}</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="difficultyLevel"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              {t("assessment.difficultyLevel")}
            </label>
            <select
              id="difficultyLevel"
              value={difficultyLevel}
              onChange={(e) => {
                setDifficultyLevel(e.target.value);
                setPreset("custom");
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="easy">{t("assessment.difficulty.easy")}</option>
              <option value="medium">
                {t("assessment.difficulty.medium")}
              </option>
              <option value="hard">{t("assessment.difficulty.hard")}</option>
              <option value="mixed">{t("assessment.difficulty.mixed")}</option>
            </select>
          </div>
        </div>

        {/* Question Type Configurations */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              {t("assessment.questionTypes")}
            </label>
            {questionTypeConfigs.length < 4 && (
              <button
                type="button"
                onClick={addQuestionType}
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
              >
                {t("assessment.addQuestionType")}
              </button>
            )}
          </div>
          <div className="space-y-3">
            {questionTypeConfigs.map((config, index) => (
              <div
                key={index}
                className="flex items-center gap-3 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg"
              >
                <select
                  value={config.type}
                  onChange={(e) =>
                    handleConfigChange(index, "type", e.target.value)
                  }
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-600 text-gray-900 dark:text-white"
                >
                  {QUESTION_TYPES.map((qt) => (
                    <option key={qt} value={qt}>
                      {t(`assessment.questionTypeLabels.${qt}`)}
                    </option>
                  ))}
                </select>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-500 dark:text-gray-400">
                    {t("assessment.count")}
                  </label>
                  <input
                    type="number"
                    value={config.count}
                    onChange={(e) =>
                      handleConfigChange(index, "count", Number(e.target.value))
                    }
                    min={1}
                    max={20}
                    className="w-16 px-2 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-center bg-white dark:bg-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-500 dark:text-gray-400">
                    {t("assessment.pointsEach")}
                  </label>
                  <input
                    type="number"
                    value={config.points_each}
                    onChange={(e) =>
                      handleConfigChange(
                        index,
                        "points_each",
                        Number(e.target.value)
                      )
                    }
                    min={1}
                    max={100}
                    className="w-16 px-2 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-center bg-white dark:bg-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
                {questionTypeConfigs.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeQuestionType(index)}
                    className="px-2 py-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          {/* Calculated total */}
          <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            {t("assessment.totalQuestions")}:{" "}
            {questionTypeConfigs.reduce((sum, c) => sum + c.count, 0)} |{" "}
            {t("assessment.totalPoints")}:{" "}
            {questionTypeConfigs.reduce(
              (sum, c) => sum + c.count * c.points_each,
              0
            )}
          </div>
        </div>

        {/* Additional Instructions */}
        <div className="mb-6">
          <label
            htmlFor="additionalInstructions"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {t("assessment.additionalInstructions")}
          </label>
          <textarea
            id="additionalInstructions"
            value={additionalInstructions}
            onChange={(e) => setAdditionalInstructions(e.target.value)}
            placeholder={t("assessment.additionalInstructionsPlaceholder")}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />

          {/* Prompt Enhancer */}
          <PromptEnhancer
            message={additionalInstructions}
            contextType="assessment"
            additionalContext={{
              topic: courseTitle,
              class_title: classTitle,
              key_topics: keyTopics.filter((topic) => topic.trim()),
              assessment_type: assessmentType,
              difficulty_level: difficultyLevel
            }}
            language={language}
            onMessageChange={setAdditionalInstructions}
            onLoadingChange={onEnhancerLoadingChange}
          />
        </div>

        {/* File Upload */}
        <div className="mb-6">
          <FileUpload
            files={uploadedFiles}
            onFilesChange={setUploadedFiles}
            displayOnly={threadId !== null}
            displayFiles={displayFiles}
          />
        </div>
      </div>

      {/* Submit Button */}
      {!threadId && (
        <div className="flex justify-end">
          <button
            onClick={onSubmit}
            disabled={isButtonDisabled}
            className="px-6 py-3 rounded-lg font-medium transition-colors bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 dark:hover:bg-blue-400 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:hover:bg-gray-400"
          >
            {t("assessment.generateAssessment")}
          </button>
        </div>
      )}
    </div>
  );
}
