"""
Assessment generation package.

This package provides a clean LangGraph-based implementation for
generating structured educational assessments using LLM agents with tool support.

Public API:
    - run_assessment_generator: Main async generator for assessment creation
    - AssessmentInput: Input schema for the workflow
    - AssessmentOutput: Output schema for the workflow
    - AssessmentState: Full state schema for the workflow
    - build_assessment_graph: Function to build the graph for testing/debugging
"""

from .state import AssessmentInput, AssessmentOutput, AssessmentState
from .graph import build_assessment_graph
from .generator import run_assessment_generator

__all__ = [
    "run_assessment_generator",
    "AssessmentInput",
    "AssessmentOutput",
    "AssessmentState",
    "build_assessment_graph",
]
