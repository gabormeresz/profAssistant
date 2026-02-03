"""
Course outline generation package.

This package provides a clean LangGraph-based implementation for
generating structured course outlines using LLM agents with tool support.

Public API:
    - run_course_outline_generator: Main async generator for course outline creation
    - CourseOutlineInput: Input schema for the workflow
    - CourseOutlineOutput: Output schema for the workflow
    - CourseOutlineState: Full state schema for the workflow
    - build_course_outline_graph: Function to build the graph for testing/debugging
"""

from .state import CourseOutlineInput, CourseOutlineOutput, CourseOutlineState
from .graph import build_course_outline_graph
from .generator import run_course_outline_generator

__all__ = [
    "run_course_outline_generator",
    "CourseOutlineInput",
    "CourseOutlineOutput",
    "CourseOutlineState",
    "build_course_outline_graph",
]
