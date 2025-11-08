import type { LessonPlan, CourseOutline } from "../types";

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
