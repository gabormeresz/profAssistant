"""
State definitions for the presentation generation workflow.

Inherits shared fields from BaseGenerationState and adds only
the presentation-specific fields (course_title, class details,
lesson context, etc.).
"""

from typing import List, Optional  # noqa: F401

from agent.base.state import (
    BaseGenerationInput,
    BaseGenerationState,
    BaseGenerationOutput,
)


class PresentationInput(BaseGenerationInput):
    """Input fields specific to presentation generation."""

    course_title: str
    class_number: Optional[int]
    class_title: str
    learning_objective: Optional[str]
    key_points: List[str]
    lesson_breakdown: Optional[str]
    activities: Optional[str]
    homework: Optional[str]
    extra_activities: Optional[str]


class PresentationState(BaseGenerationState):
    """State for presentation generation — adds lesson-context fields."""

    course_title: str
    class_number: Optional[int]
    class_title: str
    learning_objective: Optional[str]
    key_points: List[str]
    lesson_breakdown: Optional[str]
    activities: Optional[str]
    homework: Optional[str]
    extra_activities: Optional[str]


class PresentationOutput(BaseGenerationOutput):
    """Output for presentation generation (same shape as base)."""

    pass
