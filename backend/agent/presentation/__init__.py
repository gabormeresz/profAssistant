"""
Presentation generation package.

This package provides a clean LangGraph-based implementation for
generating structured educational presentations using LLM agents
with tool support.

Public API:
    - run_presentation_generator: Main async generator for presentation creation
    - PresentationInput: Input schema for the workflow
    - PresentationOutput: Output schema for the workflow
    - PresentationState: Full state schema for the workflow
    - build_presentation_graph: Function to build the graph for testing/debugging
"""

from .state import PresentationInput, PresentationOutput, PresentationState
from .graph import build_presentation_graph
from .generator import run_presentation_generator

__all__ = [
    "run_presentation_generator",
    "PresentationInput",
    "PresentationOutput",
    "PresentationState",
    "build_presentation_graph",
]
