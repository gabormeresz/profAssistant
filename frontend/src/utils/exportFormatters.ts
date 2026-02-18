import type {
  LessonPlan,
  CourseOutline,
  Presentation,
  Assessment
} from "../types";
import i18n from "../i18n/config";

/**
 * Convert a lesson plan to markdown format
 */
export function lessonPlanToMarkdown(lessonPlan: LessonPlan): string {
  const t = i18n.t.bind(i18n);
  const sections: string[] = [];

  // Title
  sections.push(
    `# ${t('lessonPlanOutput.classNumber')} ${lessonPlan.class_number}: ${lessonPlan.class_title}\n`
  );

  // Learning Objective
  sections.push(`## ${t('lessonPlanOutput.learningObjective')}\n`);
  sections.push(`${lessonPlan.learning_objective}\n`);

  // Key Points
  sections.push(`## ${t('lessonPlanOutput.keyPoints')}\n`);
  lessonPlan.key_points.forEach((point) => {
    sections.push(`- ${point}`);
  });
  sections.push("");

  // Lesson Breakdown
  sections.push(`## ${t('lessonPlanOutput.lessonBreakdown')}\n`);
  lessonPlan.lesson_breakdown.forEach((section) => {
    sections.push(`### ${section.section_title}\n`);
    sections.push(`${section.description}\n`);
  });

  // Activities
  sections.push(`## ${t('lessonPlanOutput.activities')}\n`);
  lessonPlan.activities.forEach((activity, idx) => {
    sections.push(`### ${t('lessonPlanOutput.activity')} ${idx + 1}: ${activity.name}\n`);
    sections.push(`**${t('lessonPlanOutput.objective')}:** ${activity.objective}\n`);
    sections.push(
      `**${t('lessonPlanOutput.instructions')}:** ${activity.instructions.replace(/\n/g, " ")}\n`
    );
  });

  // Homework
  sections.push(`## ${t('lessonPlanOutput.homework')}\n`);
  sections.push(`${lessonPlan.homework}\n`);

  // Extra Activities
  sections.push(`## ${t('lessonPlanOutput.extraActivities')}\n`);
  sections.push(`${lessonPlan.extra_activities}`);

  return sections.join("\n");
}

/**
 * Convert a course outline to markdown format
 */
export function courseOutlineToMarkdown(outline: CourseOutline): string {
  const t = i18n.t.bind(i18n);
  const sections: string[] = [];

  // Course Title
  sections.push(`# ${outline.course_title}\n`);

  // Classes
  outline.classes.forEach((courseClass) => {
    sections.push(
      `## ${t('lessonPlanOutput.classNumber')} ${courseClass.class_number}: ${courseClass.class_title}\n`
    );

    // Learning Objectives
    sections.push(`### ${t('courseOutline.learningObjectives')}\n`);
    courseClass.learning_objectives.forEach((objective) => {
      sections.push(`- ${objective}`);
    });
    sections.push("");

    // Key Topics
    sections.push(`### ${t('courseOutline.keyTopics')}\n`);
    courseClass.key_topics.forEach((topic) => {
      sections.push(`- ${topic}`);
    });
    sections.push("");

    // Activities & Projects
    sections.push(`### ${t('courseOutline.activitiesProjects')}\n`);
    courseClass.activities_projects.forEach((activity) => {
      sections.push(`- ${activity}`);
    });
    sections.push("");
  });

  return sections.join("\n");
}

/**
 * Convert a presentation to markdown format
 */
export function presentationToMarkdown(presentation: Presentation): string {
  const t = i18n.t.bind(i18n);
  const sections: string[] = [];

  // Title
  sections.push(`# ${presentation.course_title}\n`);
  if (presentation.class_number != null) {
    sections.push(
      `## ${t('presentationOutput.classNumber')} ${presentation.class_number}: ${presentation.lesson_title}\n`
    );
  } else {
    sections.push(
      `## ${presentation.lesson_title}\n`
    );
  }

  // Slides
  presentation.slides.forEach((slide) => {
    sections.push(`### ${t('presentationOutput.slide')} ${slide.slide_number}: ${slide.title}\n`);

    // Bullet points
    slide.bullet_points.forEach((point) => {
      sections.push(`- ${point}`);
    });
    sections.push("");

    // Speaker notes
    if (slide.speaker_notes) {
      sections.push(`**${t('presentationOutput.speakerNotes')}:** ${slide.speaker_notes}\n`);
    }

    // Visual suggestion
    if (slide.visual_suggestion) {
      sections.push(`**${t('presentationOutput.visualSuggestion')}:** ${slide.visual_suggestion}\n`);
    }
  });

  return sections.join("\n");
}

/**
 * Convert an assessment to markdown format
 * @param assessment - The assessment data
 * @param includeAnswerKey - Whether to include answer key information
 */
export function assessmentToMarkdown(
  assessment: Assessment,
  includeAnswerKey: boolean = false
): string {
  const t = i18n.t.bind(i18n);
  const sections: string[] = [];

  // Title
  sections.push(`# ${assessment.assessment_title}\n`);
  sections.push(
    `**${t('assessmentOutput.course')}:** ${assessment.course_title}${
      assessment.class_title ? ` — ${assessment.class_title}` : ""
    }`
  );
  sections.push(
    `**${t('assessmentOutput.type')}:** ${assessment.assessment_type} | **${t('assessmentOutput.totalPoints')}:** ${assessment.total_points} | **${t('assessmentOutput.duration')}:** ${assessment.estimated_duration_minutes} ${t('assessmentOutput.minutes')}\n`
  );

  // General instructions
  sections.push(`## ${t('assessmentOutput.generalInstructions')}\n`);
  sections.push(`${assessment.general_instructions}\n`);

  // Sections
  assessment.sections.forEach((section) => {
    sections.push(`## ${section.section_title}\n`);
    sections.push(`*${section.instructions}*\n`);

    section.questions.forEach((question) => {
      sections.push(
        `**${question.question_number}.** ${question.question_text} *(${question.points} ${t('assessmentOutput.pts')})*\n`
      );

      // Multiple choice options
      if (question.options) {
        question.options.forEach((option) => {
          const marker = includeAnswerKey && option.is_correct ? "**✓**" : "";
          sections.push(`   ${option.label}) ${option.text} ${marker}`);
        });
        sections.push("");
      }

      // Essay word limit
      if (section.section_type === "essay" && question.suggested_word_limit) {
        sections.push(
          `   *${t('assessmentOutput.suggestedWordLimit')}: ${question.suggested_word_limit} ${t('assessmentOutput.words')}*\n`
        );
      }

      // Answer key
      if (includeAnswerKey) {
        if (question.correct_answer) {
          const answer =
            section.section_type === "true_false"
              ? question.correct_answer === "true"
                ? t('assessmentOutput.true')
                : t('assessmentOutput.false')
              : question.correct_answer;
          sections.push(`   > **${t('assessmentOutput.correctAnswer')}:** ${answer}`);
        }
        if (question.explanation) {
          sections.push(`   > **${t('assessmentOutput.explanation')}:** ${question.explanation}`);
        }
        if (question.scoring_rubric) {
          const rubricText = question.scoring_rubric;
          try {
            const parsed = JSON.parse(rubricText);
            if (typeof parsed === "object" && parsed !== null) {
              const criteria = parsed.Criteria ?? parsed.criteria;
              const points = parsed.Points ?? parsed.points;
              const parts: string[] = [];
              if (criteria) {
                Object.entries(criteria).forEach(([name, desc]) => {
                  parts.push(`   >   - **${name}:** ${String(desc)}`);
                });
              }
              if (points) {
                const scale = Object.entries(points)
                  .map(([level, pts]) => `${level}: ${String(pts)}`)
                  .join(" | ");
                parts.push(`   >   - *${scale}*`);
              }
              if (parts.length > 0) {
                sections.push(`   > **${t('assessmentOutput.scoringRubric')}:**`);
                parts.forEach((p) => sections.push(p));
              } else {
                sections.push(`   > **${t('assessmentOutput.scoringRubric')}:** ${rubricText}`);
              }
            } else {
              sections.push(`   > **${t('assessmentOutput.scoringRubric')}:** ${rubricText}`);
            }
          } catch {
            sections.push(`   > **${t('assessmentOutput.scoringRubric')}:** ${rubricText}`);
          }
        }
        if (question.key_points && question.key_points.length > 0) {
          sections.push(`   > **${t('assessmentOutput.keyPoints')}:**`);
          question.key_points.forEach((point) => {
            sections.push(`   > - ${point}`);
          });
        }
        sections.push("");
      }
    });
  });

  // Grading notes
  if (assessment.grading_notes) {
    sections.push(`## ${t('assessmentOutput.gradingNotes')}\n`);
    sections.push(`${assessment.grading_notes}\n`);
  }

  return sections.join("\n");
}
