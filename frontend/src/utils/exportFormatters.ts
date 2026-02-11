import type {
  LessonPlan,
  CourseOutline,
  Presentation,
  Assessment
} from "../types";

/**
 * Convert a lesson plan to markdown format
 */
export function lessonPlanToMarkdown(lessonPlan: LessonPlan): string {
  const sections: string[] = [];

  // Title
  sections.push(
    `# Class ${lessonPlan.class_number}: ${lessonPlan.class_title}\n`
  );

  // Learning Objective
  sections.push(`## Learning Objective\n`);
  sections.push(`${lessonPlan.learning_objective}\n`);

  // Key Points
  sections.push(`## Key Points\n`);
  lessonPlan.key_points.forEach((point) => {
    sections.push(`- ${point}`);
  });
  sections.push("");

  // Lesson Breakdown
  sections.push(`## Lesson Breakdown\n`);
  lessonPlan.lesson_breakdown.forEach((section) => {
    sections.push(`### ${section.section_title}\n`);
    sections.push(`${section.description}\n`);
  });

  // Activities
  sections.push(`## Activities\n`);
  lessonPlan.activities.forEach((activity, idx) => {
    sections.push(`### Activity ${idx + 1}: ${activity.name}\n`);
    sections.push(`**Objective:** ${activity.objective}\n`);
    sections.push(
      `**Instructions:** ${activity.instructions.replace(/\n/g, " ")}\n`
    );
  });

  // Homework
  sections.push(`## Homework\n`);
  sections.push(`${lessonPlan.homework}\n`);

  // Extra Activities
  sections.push(`## Extra Activities\n`);
  sections.push(`${lessonPlan.extra_activities}`);

  return sections.join("\n");
}

/**
 * Convert a course outline to markdown format
 */
export function courseOutlineToMarkdown(outline: CourseOutline): string {
  const sections: string[] = [];

  // Course Title
  sections.push(`# ${outline.course_title}\n`);

  // Classes
  outline.classes.forEach((courseClass) => {
    sections.push(
      `## Class ${courseClass.class_number}: ${courseClass.class_title}\n`
    );

    // Learning Objectives
    sections.push(`### Learning Objectives\n`);
    courseClass.learning_objectives.forEach((objective) => {
      sections.push(`- ${objective}`);
    });
    sections.push("");

    // Key Topics
    sections.push(`### Key Topics\n`);
    courseClass.key_topics.forEach((topic) => {
      sections.push(`- ${topic}`);
    });
    sections.push("");

    // Activities & Projects
    sections.push(`### Activities & Projects\n`);
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
  const sections: string[] = [];

  // Title
  sections.push(`# ${presentation.course_title}\n`);
  sections.push(
    `## Class ${presentation.class_number}: ${presentation.lesson_title}\n`
  );

  // Slides
  presentation.slides.forEach((slide) => {
    sections.push(`### Slide ${slide.slide_number}: ${slide.title}\n`);

    // Bullet points
    slide.bullet_points.forEach((point) => {
      sections.push(`- ${point}`);
    });
    sections.push("");

    // Speaker notes
    if (slide.speaker_notes) {
      sections.push(`**Speaker Notes:** ${slide.speaker_notes}\n`);
    }

    // Visual suggestion
    if (slide.visual_suggestion) {
      sections.push(`**Visual Suggestion:** ${slide.visual_suggestion}\n`);
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
  const sections: string[] = [];

  // Title
  sections.push(`# ${assessment.assessment_title}\n`);
  sections.push(
    `**Course:** ${assessment.course_title}${
      assessment.class_title ? ` — ${assessment.class_title}` : ""
    }`
  );
  sections.push(
    `**Type:** ${assessment.assessment_type} | **Total Points:** ${assessment.total_points} | **Duration:** ${assessment.estimated_duration_minutes} minutes\n`
  );

  // General instructions
  sections.push(`## General Instructions\n`);
  sections.push(`${assessment.general_instructions}\n`);

  // Sections
  assessment.sections.forEach((section) => {
    sections.push(`## ${section.section_title}\n`);
    sections.push(`*${section.instructions}*\n`);

    section.questions.forEach((question) => {
      sections.push(
        `**${question.question_number}.** ${question.question_text} *(${question.points} pts)*\n`
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
          `   *Suggested word limit: ${question.suggested_word_limit} words*\n`
        );
      }

      // Answer key
      if (includeAnswerKey) {
        if (question.correct_answer) {
          const answer =
            section.section_type === "true_false"
              ? question.correct_answer === "true"
                ? "True"
                : "False"
              : question.correct_answer;
          sections.push(`   > **Answer:** ${answer}`);
        }
        if (question.explanation) {
          sections.push(`   > **Explanation:** ${question.explanation}`);
        }
        if (question.scoring_rubric) {
          let rubricText = question.scoring_rubric;
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
                sections.push(`   > **Scoring Rubric:**`);
                parts.forEach((p) => sections.push(p));
              } else {
                sections.push(`   > **Scoring Rubric:** ${rubricText}`);
              }
            } else {
              sections.push(`   > **Scoring Rubric:** ${rubricText}`);
            }
          } catch {
            sections.push(`   > **Scoring Rubric:** ${rubricText}`);
          }
        }
        if (question.key_points && question.key_points.length > 0) {
          sections.push(`   > **Key Points:**`);
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
    sections.push(`## Grading Notes\n`);
    sections.push(`${assessment.grading_notes}\n`);
  }

  return sections.join("\n");
}
