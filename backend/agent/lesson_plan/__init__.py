"""
Lesson plan generation package.

This package provides a clean LangGraph-based implementation for
generating structured lesson plans using LLM agents with tool support.

Public API:
    - run_lesson_plan_generator: Main async generator for lesson plan creation
    - LessonPlanInput: Input schema for the workflow
    - LessonPlanOutput: Output schema for the workflow
    - LessonPlanState: Full state schema for the workflow
    - build_lesson_plan_graph: Function to build the graph for testing/debugging
"""

from .state import LessonPlanInput, LessonPlanOutput, LessonPlanState
from .graph import build_lesson_plan_graph
from .generator import run_lesson_plan_generator

__all__ = [
    "run_lesson_plan_generator",
    "LessonPlanInput",
    "LessonPlanOutput",
    "LessonPlanState",
    "build_lesson_plan_graph",
]
