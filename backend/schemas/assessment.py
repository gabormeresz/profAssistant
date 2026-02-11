"""
Pydantic schemas for assessments / tests.

This module defines the Assessment, AssessmentSection, Question, and
QuestionOption models used to validate and serialize a complete educational
assessment: title, type, sections grouped by question type, and an
embedded answer key with explanations.

The schema includes json_schema_extra example data to aid documentation and
OpenAPI/JSON Schema generation.
"""

from typing import Any, List, Literal, Optional, Union
from collections.abc import Sequence, Mapping
from pydantic import BaseModel, Field, model_validator

# Human-readable labels for question types
QUESTION_TYPE_LABELS = {
    "multiple_choice": "Multiple Choice",
    "true_false": "True/False",
    "short_answer": "Short Answer",
    "essay": "Essay",
}


class QuestionOption(BaseModel):
    """
    Represents a single answer option for a multiple-choice question.
    """

    label: str = Field(..., description="Option label (e.g. A, B, C, D)", max_length=5)
    text: str = Field(..., description="The text of the answer option")
    is_correct: bool = Field(
        ..., description="Whether this option is the correct answer"
    )


class Question(BaseModel):
    """
    Represents a single question in an assessment section.

    Uses optional fields to accommodate different question types:
    - multiple_choice: options + correct_answer (label)
    - true_false: correct_answer (bool as string "true"/"false")
    - short_answer: correct_answer (expected answer text)
    - essay: scoring_rubric + key_points + suggested_word_limit
    """

    question_number: int = Field(
        ..., description="Sequential question number within the section", ge=1
    )
    question_text: str = Field(
        ..., description="The actual question text", min_length=5
    )
    points: int = Field(..., description="Point value for this question", ge=1, le=100)
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ..., description="Difficulty level of the question"
    )

    # Multiple choice specific
    options: Optional[List[QuestionOption]] = Field(
        None,
        description="Answer options for multiple-choice questions (2-6 options)",
    )

    # Correct answer for MC (label), T/F ("true"/"false"), short answer (text)
    correct_answer: Optional[str] = Field(
        None,
        description="The correct answer: option label for MC, 'true'/'false' for T/F, expected text for short answer",
    )

    # Essay specific
    scoring_rubric: Optional[str] = Field(
        None, description="Scoring rubric or criteria for essay evaluation"
    )
    key_points: Optional[List[str]] = Field(
        None,
        description="Expected key points that should appear in the essay answer",
    )
    suggested_word_limit: Optional[int] = Field(
        None, description="Suggested word limit for essay responses", ge=50, le=5000
    )

    # Explanation for the answer key (all types)
    explanation: Optional[str] = Field(
        None,
        description="Explanation of why the correct answer is correct, for the answer key",
    )


class AssessmentSection(BaseModel):
    """
    Represents a section of the assessment containing questions of one type.
    """

    section_number: int = Field(..., description="Sequential section number", ge=1)
    section_title: str = Field(
        ..., description="Title of this section (e.g. 'Part A: Multiple Choice')"
    )
    section_type: Literal["multiple_choice", "true_false", "short_answer", "essay"] = (
        Field(..., description="The type of questions in this section")
    )
    instructions: str = Field(
        ...,
        description="Instructions for students on how to complete this section",
    )
    questions: List[Question] = Field(
        ...,
        description="Questions in this section (1-20)",
        min_length=1,
        max_length=20,
    )

    @model_validator(mode="after")
    def validate_questions_match_section_type(self) -> "AssessmentSection":
        """Validate that questions have the correct fields for the section type."""
        for q in self.questions:
            if self.section_type == "multiple_choice":
                if not q.options or len(q.options) < 2:
                    raise ValueError(
                        f"Question {q.question_number}: multiple choice questions must have at least 2 options"
                    )
                if not q.correct_answer:
                    raise ValueError(
                        f"Question {q.question_number}: multiple choice questions must have a correct_answer (option label)"
                    )
            elif self.section_type == "true_false":
                if q.correct_answer is None or q.correct_answer.lower() not in (
                    "true",
                    "false",
                ):
                    raise ValueError(
                        f"Question {q.question_number}: true/false questions must have correct_answer as 'true' or 'false'"
                    )
            elif self.section_type == "short_answer":
                if not q.correct_answer:
                    raise ValueError(
                        f"Question {q.question_number}: short answer questions must have a correct_answer"
                    )
            elif self.section_type == "essay":
                if not q.scoring_rubric and not q.key_points:
                    raise ValueError(
                        f"Question {q.question_number}: essay questions must have either a scoring_rubric or key_points"
                    )
        return self


class Assessment(BaseModel):
    """
    Complete assessment structure for an educational course.
    """

    assessment_title: str = Field(
        ...,
        description="Title of the assessment",
        min_length=3,
        max_length=300,
    )
    assessment_type: Literal["quiz", "exam", "homework", "practice"] = Field(
        ..., description="Type of assessment"
    )
    course_title: str = Field(
        ..., description="Title of the course this assessment is for"
    )
    class_title: Optional[str] = Field(
        None, description="Title of the specific class/lesson (if applicable)"
    )
    total_points: int = Field(
        ..., description="Total points available in the assessment", ge=1
    )
    estimated_duration_minutes: int = Field(
        ..., description="Estimated time to complete in minutes", ge=5, le=300
    )
    general_instructions: str = Field(
        ..., description="General instructions for students taking the assessment"
    )
    sections: List[AssessmentSection] = Field(
        ...,
        description="Ordered sections of the assessment (1-6 sections)",
        min_length=1,
        max_length=6,
    )
    grading_notes: Optional[str] = Field(
        None,
        description="Additional grading notes or guidelines for the instructor",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "assessment_title": "Midterm Exam: Introduction to Python Programming",
                "assessment_type": "exam",
                "course_title": "Introduction to Python Programming",
                "class_title": "Variables and Data Types",
                "total_points": 50,
                "estimated_duration_minutes": 60,
                "general_instructions": "Answer all questions. Multiple choice questions have exactly one correct answer. Show your work for short answer questions.",
                "sections": [
                    {
                        "section_number": 1,
                        "section_title": "Part A: Multiple Choice",
                        "section_type": "multiple_choice",
                        "instructions": "Select the best answer for each question.",
                        "questions": [
                            {
                                "question_number": 1,
                                "question_text": "Which of the following is the correct way to declare a variable in Python?",
                                "points": 5,
                                "difficulty": "easy",
                                "options": [
                                    {
                                        "label": "A",
                                        "text": "int x = 5",
                                        "is_correct": False,
                                    },
                                    {"label": "B", "text": "x = 5", "is_correct": True},
                                    {
                                        "label": "C",
                                        "text": "var x = 5",
                                        "is_correct": False,
                                    },
                                    {
                                        "label": "D",
                                        "text": "let x = 5",
                                        "is_correct": False,
                                    },
                                ],
                                "correct_answer": "B",
                                "explanation": "Python uses dynamic typing and does not require type declarations. Variables are created by simple assignment.",
                            }
                        ],
                    },
                    {
                        "section_number": 2,
                        "section_title": "Part B: True/False",
                        "section_type": "true_false",
                        "instructions": "Indicate whether each statement is true or false.",
                        "questions": [
                            {
                                "question_number": 1,
                                "question_text": "In Python, strings are immutable.",
                                "points": 3,
                                "difficulty": "medium",
                                "correct_answer": "true",
                                "explanation": "Python strings cannot be modified after creation. Any operation that appears to modify a string creates a new string object.",
                            }
                        ],
                    },
                    {
                        "section_number": 3,
                        "section_title": "Part C: Short Answer",
                        "section_type": "short_answer",
                        "instructions": "Provide a brief answer to each question.",
                        "questions": [
                            {
                                "question_number": 1,
                                "question_text": "What is the output of print(type(3.14))?",
                                "points": 5,
                                "difficulty": "easy",
                                "correct_answer": "<class 'float'>",
                                "explanation": "The type() function returns the data type of the argument. 3.14 is a floating-point number.",
                            }
                        ],
                    },
                    {
                        "section_number": 4,
                        "section_title": "Part D: Essay",
                        "section_type": "essay",
                        "instructions": "Write a well-structured response to the following question.",
                        "questions": [
                            {
                                "question_number": 1,
                                "question_text": "Compare and contrast lists and tuples in Python. When would you use each?",
                                "points": 15,
                                "difficulty": "hard",
                                "scoring_rubric": "Full marks: covers mutability, performance, use cases with examples. Partial: covers at least 2 of 3 aspects.",
                                "key_points": [
                                    "Lists are mutable, tuples are immutable",
                                    "Tuples are slightly faster and use less memory",
                                    "Use tuples for fixed data, lists for dynamic collections",
                                    "Tuples can be dictionary keys, lists cannot",
                                ],
                                "suggested_word_limit": 300,
                                "explanation": "A strong answer should cover mutability differences, performance implications, and practical use cases with code examples.",
                            }
                        ],
                    },
                ],
                "grading_notes": "Award partial credit for short answer questions that demonstrate understanding even if the exact syntax is incorrect.",
            }
        }
    }


# ---------------------------------------------------------------------------
# Dynamic schema factory
# ---------------------------------------------------------------------------


def _make_constrained_section(qt: str, count: int, pts_each: int, label: str) -> type:
    """
    Create an ``AssessmentSection`` subclass whose JSON schema locks
    ``section_type`` to a single value and ``questions`` to exactly
    *count* items (``minItems`` / ``maxItems`` in JSON schema).

    A helper function is used (instead of a loop body) so that each
    invocation gets its own closure over *qt*, *count*, etc.
    """
    SectionTypeLiteral = Literal.__getitem__(qt)  # type: ignore[attr-defined]

    class _Section(AssessmentSection):
        section_type: SectionTypeLiteral = Field(  # type: ignore[valid-type]
            ..., description=f"Must be '{qt}'"
        )
        questions: List[Question] = Field(
            ...,
            description=(
                f"Exactly {count} {label} question(s), "
                f"each worth {pts_each} point(s)"
            ),
            min_length=count,
            max_length=count,
        )

    _Section.__name__ = f"AssessmentSection_{qt}"
    _Section.__qualname__ = f"AssessmentSection_{qt}"
    return _Section


def build_dynamic_assessment_model(
    question_type_configs: Sequence[Mapping[str, Any]],
) -> type:
    """
    Build a dynamically constrained Assessment model that only allows
    the requested question types, section count, **and** per-section
    question count.

    For every distinct question type a dedicated ``AssessmentSection``
    subclass is created whose ``questions`` field has
    ``min_length == max_length == count``.  This translates to
    ``minItems`` / ``maxItems`` in the JSON schema, which OpenAI
    structured-output honours as a hard constraint.

    When multiple question types are requested the ``sections`` field
    becomes ``List[Union[SectionA, SectionB, …]]`` (discriminated by
    ``section_type``).

    Args:
        question_type_configs: List of dicts with at least
            ``question_type`` (str), ``count`` (int), and optionally
            ``points_each`` (int) keys.

    Returns:
        A Pydantic model class (subclass of Assessment).
        Falls back to the static ``Assessment`` if configs are empty.
    """
    if not question_type_configs:
        return Assessment

    # Deduplicate while preserving order
    seen: set[str] = set()
    ordered_configs: list[dict[str, Any]] = []
    for cfg in question_type_configs:
        qt = cfg.get("question_type", "")
        if qt and qt not in seen:
            seen.add(qt)
            ordered_configs.append(dict(cfg))

    if not ordered_configs:
        return Assessment

    n_sections = len(ordered_configs)

    # --- Build per-type section classes & description ---
    section_classes: list[type] = []
    section_desc_parts: list[str] = []
    for i, cfg in enumerate(ordered_configs, 1):
        qt = cfg["question_type"]
        count = cfg.get("count", 1)
        pts_each = cfg.get("points_each", 5)
        label: str = QUESTION_TYPE_LABELS.get(qt) or qt
        section_pts = count * pts_each

        section_cls = _make_constrained_section(qt, count, pts_each, label)
        section_classes.append(section_cls)
        section_desc_parts.append(
            f"Section {i}: {label} ({qt}) — {count} question(s), "
            f"{pts_each} pts each = {section_pts} pts"
        )

    sections_description = f"Exactly {n_sections} section(s): " + "; ".join(
        section_desc_parts
    )

    # --- Union of section types (or single type) ---
    if n_sections == 1:
        SectionType = section_classes[0]
    else:
        SectionType = Union.__getitem__(tuple(section_classes))  # type: ignore[attr-defined]

    # --- Constrained Assessment subclass ---
    class ConstrainedAssessment(Assessment):
        """Assessment with dynamically locked section types, counts, and per-section question count."""

        sections: List[SectionType] = Field(  # type: ignore[valid-type]
            ...,
            description=sections_description,
            min_length=n_sections,
            max_length=n_sections,
        )

    ConstrainedAssessment.__name__ = "Assessment"
    ConstrainedAssessment.__qualname__ = "Assessment"

    return ConstrainedAssessment
