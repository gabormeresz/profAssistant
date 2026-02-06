"""
State definitions for the lesson plan generation workflow.

Inherits shared fields from BaseGenerationState and adds only
the lesson-plan-specific fields (course_title, class details, etc.).
"""

from typing import List

from agent.base.state import (
    BaseGenerationInput,
    BaseGenerationState,
    BaseGenerationOutput,
)


class LessonPlanInput(BaseGenerationInput):
    """Input fields specific to lesson plan generation."""

    course_title: str
    class_number: int
    class_title: str
    learning_objectives: List[str]
    key_topics: List[str]
    activities_projects: List[str]


class LessonPlanState(BaseGenerationState):
    """State for lesson plan generation — adds class-specific fields."""

    course_title: str
    class_number: int
    class_title: str
    learning_objectives: List[str]
    key_topics: List[str]
    activities_projects: List[str]


class LessonPlanOutput(BaseGenerationOutput):
    """Output for lesson plan generation (same shape as base)."""

    pass
