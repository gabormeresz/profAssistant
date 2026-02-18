import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { Assessment } from "../../types";
import { useExport } from "../../hooks";
import { assessmentToMarkdown } from "../../utils";

/**
 * Renders a scoring rubric. If the value is a JSON string with
 * "Criteria" / "Points" keys, it shows a nicely formatted list + point
 * scale. Otherwise it falls back to plain text.
 */
function RubricDisplay({ value }: { value: string }) {
  try {
    const parsed = JSON.parse(value);
    if (typeof parsed === "object" && parsed !== null) {
      const criteria: Record<string, string> | undefined =
        parsed.Criteria ?? parsed.criteria;
      const points: Record<string, number> | undefined =
        parsed.Points ?? parsed.points;

      return (
        <div className="mt-1 ml-2 space-y-2 text-sm">
          {criteria && (
            <ul className="space-y-1 list-disc ml-4">
              {Object.entries(criteria).map(([name, desc]) => (
                <li key={name} className="text-gray-700 dark:text-gray-300">
                  <span className="font-medium">{name}:</span> {String(desc)}
                </li>
              ))}
            </ul>
          )}
          {points && (
            <div className="flex flex-wrap gap-2 mt-1">
              {Object.entries(points).map(([level, pts]) => (
                <span
                  key={level}
                  className="inline-flex items-center gap-1 bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 px-2 py-0.5 rounded text-xs font-medium"
                >
                  {level}: {String(pts)}
                </span>
              ))}
            </div>
          )}
          {/* Fallback: if parsed JSON has neither key, render all entries */}
          {!criteria && !points && (
            <ul className="space-y-1 list-disc ml-4">
              {Object.entries(parsed).map(([key, val]) => (
                <li key={key} className="text-gray-700 dark:text-gray-300">
                  <span className="font-medium">{key}:</span>{" "}
                  {typeof val === "object" ? JSON.stringify(val) : String(val)}
                </li>
              ))}
            </ul>
          )}
        </div>
      );
    }
  } catch {
    // Not JSON — fall through to plain text
  }

  return (
    <span className="text-sm text-gray-700 dark:text-gray-300 ml-1">
      {value}
    </span>
  );
}

interface StructuredAssessmentProps {
  assessment: Assessment;
  language?: string;
}

export function StructuredAssessment({
  assessment
}: StructuredAssessmentProps) {
  const { t } = useTranslation();
  const { exportToDocx } = useExport();
  const [showAnswerKey, setShowAnswerKey] = useState(false);

  const handleExport = async () => {
    const markdown = assessmentToMarkdown(assessment, false);
    const filename = `assessment_${assessment.assessment_title
      .replace(/\s+/g, "_")
      .toLowerCase()
      .slice(0, 60)}.docx`;
    await exportToDocx(markdown, { filename });
  };

  const handleExportWithAnswers = async () => {
    const markdown = assessmentToMarkdown(assessment, true);
    const filename = `assessment_answer_key_${assessment.assessment_title
      .replace(/\s+/g, "_")
      .toLowerCase()
      .slice(0, 60)}.docx`;
    await exportToDocx(markdown, { filename });
  };

  const difficultyColor = (diff: string) => {
    switch (diff) {
      case "easy":
        return "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400";
      case "medium":
        return "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400";
      case "hard":
        return "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400";
      default:
        return "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300";
    }
  };

  const sectionTypeColor = (type: string) => {
    switch (type) {
      case "multiple_choice":
        return "border-blue-500 dark:border-blue-400";
      case "true_false":
        return "border-purple-500 dark:border-purple-400";
      case "short_answer":
        return "border-green-500 dark:border-green-400";
      case "essay":
        return "border-orange-500 dark:border-orange-400";
      default:
        return "border-gray-500 dark:border-gray-400";
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
      {/* Assessment Header */}
      <div className="mb-8 border-b-2 border-indigo-500 dark:border-indigo-400 pb-4">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/40 px-3 py-1 rounded">
                {t(`assessment.types.${assessment.assessment_type}`)}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {assessment.total_points} {t("assessmentOutput.points")}{" "}
                &middot; {assessment.estimated_duration_minutes}{" "}
                {t("assessmentOutput.minutes")}
              </span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {assessment.assessment_title}
            </h1>
            {assessment.class_title && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {assessment.course_title} &mdash; {assessment.class_title}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2 flex-shrink-0">
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white text-sm font-medium rounded-md hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors flex items-center gap-2"
              title={t("export.exportToDocx")}
            >
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
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              {t("export.exportToDocx")}
            </button>
            <button
              onClick={handleExportWithAnswers}
              className="px-4 py-2 bg-green-600 dark:bg-green-500 text-white text-sm font-medium rounded-md hover:bg-green-700 dark:hover:bg-green-400 transition-colors flex items-center gap-2"
              title={t("assessmentOutput.exportWithAnswers")}
            >
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
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {t("assessmentOutput.exportWithAnswers")}
            </button>
          </div>
        </div>
      </div>

      {/* General Instructions */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
          {t("assessmentOutput.generalInstructions")}
        </h2>
        <p className="text-gray-700 dark:text-gray-300 bg-indigo-50 dark:bg-indigo-950 p-4 rounded-lg border-l-4 border-indigo-500 dark:border-indigo-400">
          {assessment.general_instructions}
        </p>
      </div>

      {/* Answer Key Toggle */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={() => setShowAnswerKey(!showAnswerKey)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
            showAnswerKey
              ? "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-700"
              : "bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600"
          }`}
        >
          {showAnswerKey
            ? t("assessmentOutput.hideAnswerKey")
            : t("assessmentOutput.showAnswerKey")}
        </button>
      </div>

      {/* Sections */}
      <div className="space-y-8">
        {assessment.sections.map((section) => (
          <div
            key={section.section_number}
            className={`border-l-4 ${sectionTypeColor(section.section_type)} pl-4`}
          >
            <div className="flex items-center gap-3 mb-3">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {section.section_title}
              </h2>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {section.questions.length}{" "}
                {section.questions.length === 1
                  ? t("assessmentOutput.question")
                  : t("assessmentOutput.questions")}
              </span>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 italic">
              {section.instructions}
            </p>

            <div className="space-y-4">
              {section.questions.map((question) => (
                <div
                  key={question.question_number}
                  className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4"
                >
                  {/* Question header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {question.question_number}.{" "}
                      </span>
                      <span className="text-gray-800 dark:text-gray-200">
                        {question.question_text}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${difficultyColor(
                          question.difficulty
                        )}`}
                      >
                        {t(`assessment.difficulty.${question.difficulty}`)}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                        {question.points} {t("assessmentOutput.pts")}
                      </span>
                    </div>
                  </div>

                  {/* Multiple choice options */}
                  {question.options && (
                    <div className="mt-3 space-y-1 ml-4">
                      {question.options.map((option) => (
                        <div
                          key={option.label}
                          className={`flex items-center gap-2 py-1 px-2 rounded ${
                            showAnswerKey && option.is_correct
                              ? "bg-green-100 dark:bg-green-900/40"
                              : ""
                          }`}
                        >
                          <span className="font-medium text-gray-600 dark:text-gray-400 w-6">
                            {option.label})
                          </span>
                          <span className="text-gray-700 dark:text-gray-300">
                            {option.text}
                          </span>
                          {showAnswerKey && option.is_correct && (
                            <span className="text-green-600 dark:text-green-400 text-sm ml-1">
                              ✓
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Essay specific: word limit */}
                  {section.section_type === "essay" &&
                    question.suggested_word_limit && (
                      <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 italic ml-4">
                        {t("assessmentOutput.suggestedWordLimit")}:{" "}
                        {question.suggested_word_limit}{" "}
                        {t("assessmentOutput.words")}
                      </p>
                    )}

                  {/* Answer Key section (toggled) */}
                  {showAnswerKey && (
                    <div className="mt-3 ml-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded p-3">
                      {/* Correct Answer (non-essay) */}
                      {question.correct_answer && (
                        <div className="mb-1">
                          <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
                            {t("assessmentOutput.correctAnswer")}:{" "}
                          </span>
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {section.section_type === "true_false"
                              ? question.correct_answer === "true"
                                ? t("assessmentOutput.true")
                                : t("assessmentOutput.false")
                              : question.correct_answer}
                          </span>
                        </div>
                      )}

                      {/* Explanation */}
                      {question.explanation && (
                        <div className="mb-1">
                          <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
                            {t("assessmentOutput.explanation")}:{" "}
                          </span>
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {question.explanation}
                          </span>
                        </div>
                      )}

                      {/* Scoring Rubric (essay) */}
                      {question.scoring_rubric && (
                        <div className="mb-2">
                          <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
                            {t("assessmentOutput.scoringRubric")}:
                          </span>
                          <RubricDisplay value={question.scoring_rubric} />
                        </div>
                      )}

                      {/* Key Points (essay) */}
                      {question.key_points &&
                        question.key_points.length > 0 && (
                          <div>
                            <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
                              {t("assessmentOutput.keyPoints")}:{" "}
                            </span>
                            <ul className="mt-1 space-y-1 ml-4">
                              {question.key_points.map((point, idx) => (
                                <li
                                  key={idx}
                                  className="text-sm text-gray-700 dark:text-gray-300 list-disc"
                                >
                                  {point}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Grading Notes */}
      {assessment.grading_notes && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
            {t("assessmentOutput.gradingNotes")}
          </h2>
          <div className="bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <p className="text-gray-700 dark:text-gray-300">
              {assessment.grading_notes}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
