"""
State definitions for the course outline generation workflow.

Inherits shared fields from BaseGenerationState and adds only
the course-outline-specific fields (topic, number_of_classes).
"""

from agent.base.state import (
    BaseGenerationInput,
    BaseGenerationState,
    BaseGenerationOutput,
)


class CourseOutlineInput(BaseGenerationInput):
    """Input fields specific to course outline generation."""

    topic: str
    number_of_classes: int


class CourseOutlineState(BaseGenerationState):
    """State for course outline generation — adds topic and class count."""

    topic: str
    number_of_classes: int


class CourseOutlineOutput(BaseGenerationOutput):
    """Output for course outline generation (same shape as base)."""

    pass
