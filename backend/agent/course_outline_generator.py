"""
Course outline generator using LangGraph.

This module re-exports the course outline generator from the course_outline package
for backward compatibility. The implementation has been refactored into a clean
modular structure using LangGraph nodes.

See the course_outline package for the full implementation:
    - course_outline/state.py: State definitions
    - course_outline/prompts.py: System prompts
    - course_outline/nodes.py: Node functions
    - course_outline/graph.py: Graph construction
    - course_outline/generator.py: Main entry point
"""

from .course_outline import (
    run_course_outline_generator,
    CourseOutlineInput,
    CourseOutlineOutput,
    CourseOutlineState,
    build_course_outline_graph,
    get_graph_visualization,
)

__all__ = [
    "run_course_outline_generator",
    "CourseOutlineInput",
    "CourseOutlineOutput",
    "CourseOutlineState",
    "build_course_outline_graph",
    "get_graph_visualization",
]
