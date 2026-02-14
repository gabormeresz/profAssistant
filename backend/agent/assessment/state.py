"""
State definitions for the assessment generation workflow.

Inherits shared fields from BaseGenerationState and adds only
the assessment-specific fields (course context, question type configs, etc.).
"""

from typing import List, Literal, Optional, TypedDict

from agent.base.state import (
    BaseGenerationInput,
    BaseGenerationState,
    BaseGenerationOutput,
)


QuestionType = Literal["multiple_choice", "true_false", "short_answer", "essay"]


class QuestionTypeConfig(TypedDict):
    """Configuration for a single question type in an assessment."""

    question_type: QuestionType
    count: int
    points_each: int


AssessmentType = Literal["quiz", "exam", "homework", "practice"]
DifficultyLevel = Literal["easy", "medium", "hard", "mixed"]


class AssessmentInput(BaseGenerationInput):
    """Input fields specific to assessment generation."""

    course_title: str
    class_title: Optional[str]
    key_topics: List[str]
    assessment_type: AssessmentType
    difficulty_level: DifficultyLevel
    question_type_configs: List[QuestionTypeConfig]
    additional_instructions: Optional[str]


class AssessmentState(BaseGenerationState):
    """State for assessment generation — adds assessment-specific fields."""

    course_title: str
    class_title: Optional[str]
    key_topics: List[str]
    assessment_type: AssessmentType
    difficulty_level: DifficultyLevel
    question_type_configs: List[QuestionTypeConfig]
    additional_instructions: Optional[str]


class AssessmentOutput(BaseGenerationOutput):
    """Output for assessment generation (same shape as base)."""

    pass
