import { useState } from "react";
import { useTranslation } from "react-i18next";
import { saveAs } from "file-saver";
import type { Presentation } from "../../types";
import { useExport } from "../../hooks";
import { presentationToMarkdown } from "../../utils";
import { exportPresentationToPptx } from "../../services";
import { LoadingOverlay } from "../ui";

interface StructuredPresentationProps {
  presentation: Presentation;
}

export function StructuredPresentation({
  presentation
}: StructuredPresentationProps) {
  const { t } = useTranslation();
  const { exportToDocx } = useExport();
  const [pptxLoading, setPptxLoading] = useState(false);
  const [pptxError, setPptxError] = useState<string | null>(null);

  const handleExportDocx = async () => {
    const markdown = presentationToMarkdown(presentation);
    const classNumPart =
      presentation.class_number != null
        ? `_class_${presentation.class_number}`
        : "";
    const filename = `presentation${classNumPart}_${presentation.lesson_title
      .replace(/\s+/g, "_")
      .toLowerCase()}.docx`;
    await exportToDocx(markdown, { filename });
  };

  const handleExportPptx = async () => {
    setPptxLoading(true);
    setPptxError(null);
    try {
      const blob = await exportPresentationToPptx(presentation);
      const safeTitle = presentation.lesson_title
        .replace(/\s+/g, "_")
        .toLowerCase();
      const classNumPart =
        presentation.class_number != null
          ? `_class_${presentation.class_number}`
          : "";
      const filename = `presentation${classNumPart}_${safeTitle}.pptx`;
      saveAs(blob, filename);
    } catch (err) {
      setPptxError(
        err instanceof Error ? err.message : "Failed to generate PPTX"
      );
    } finally {
      setPptxLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
      {/* PPTX Loading Overlay (reuses the same modal as generation) */}
      <LoadingOverlay message={t("export.generatingPptx")} show={pptxLoading} />

      {/* Presentation Header */}
      <div className="mb-8 border-b-2 border-purple-500 dark:border-purple-400 pb-4">
        <div className="flex items-baseline gap-3 mb-2">
          {presentation.class_number != null && (
            <span className="text-sm font-semibold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/40 px-3 py-1 rounded">
              {t("presentationOutput.classNumber")} {presentation.class_number}
            </span>
          )}
          <h1 className="text-3xl font-bold text-dark flex-1">
            {presentation.lesson_title}
          </h1>
          <div className="flex flex-col gap-2">
            {/* Export to PPTX */}
            <button
              onClick={handleExportPptx}
              disabled={pptxLoading}
              className="px-4 py-2 bg-purple-600 dark:bg-purple-500 text-white text-sm font-medium rounded-md hover:bg-purple-700 dark:hover:bg-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              title={t("export.exportToPptx")}
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
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              {t("export.exportToPptx")}
            </button>
            {/* Export to DOCX */}
            <button
              onClick={handleExportDocx}
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
          </div>
        </div>
        {/* PPTX error banner */}
        {pptxError && (
          <div className="mt-2 p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg flex items-center justify-between">
            <span className="text-red-700 dark:text-red-300 text-sm">
              {pptxError}
            </span>
            <button
              onClick={() => setPptxError(null)}
              className="text-red-400 hover:text-red-600 dark:hover:text-red-300 text-sm ml-4"
            >
              ✕
            </button>
          </div>
        )}
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          {presentation.course_title} &mdash; {presentation.slides.length}{" "}
          {t("presentationOutput.slides")}
        </p>
      </div>

      {/* Slides */}
      <div className="space-y-6">
        {presentation.slides.map((slide) => (
          <div
            key={slide.slide_number}
            className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
          >
            {/* Slide header */}
            <div className="bg-purple-50 dark:bg-purple-950 px-5 py-3 flex items-center gap-3 border-b border-purple-200 dark:border-purple-800">
              <span className="text-xs font-bold text-purple-700 dark:text-purple-300 bg-purple-200 dark:bg-purple-800 px-2 py-0.5 rounded">
                {slide.slide_number}
              </span>
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                {slide.title}
              </h2>
            </div>

            <div className="p-5 space-y-4">
              {/* Bullet points */}
              <ul className="space-y-2">
                {slide.bullet_points.map((point, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-3 text-gray-700 dark:text-gray-300"
                  >
                    <span className="text-purple-500 dark:text-purple-400 font-bold mt-0.5">
                      •
                    </span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>

              {/* Speaker notes */}
              {slide.speaker_notes && (
                <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-amber-700 dark:text-amber-300 mb-1">
                    {t("presentationOutput.speakerNotes")}
                  </h3>
                  <p className="text-gray-700 dark:text-gray-300 text-sm whitespace-pre-line">
                    {slide.speaker_notes}
                  </p>
                </div>
              )}

              {/* Visual suggestion */}
              {slide.visual_suggestion && (
                <div className="bg-sky-50 dark:bg-sky-950 border border-sky-200 dark:border-sky-800 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-sky-700 dark:text-sky-300 mb-1 flex items-center gap-1">
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
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    {t("presentationOutput.visualSuggestion")}
                  </h3>
                  <p className="text-gray-700 dark:text-gray-300 text-sm">
                    {slide.visual_suggestion}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
