"""
Base state definitions shared across all generation workflows.

Each generation module (course_outline, lesson_plan, etc.) inherits
from these base types and adds only its domain-specific fields.
"""

from typing import TypedDict, List, Dict, Optional, Annotated, Any

from langgraph.graph import MessagesState
from schemas.evaluation import EvaluationResult

import operator


class BaseGenerationInput(TypedDict):
    """Common input fields for all generation workflows."""

    message: Optional[str]
    file_contents: Optional[List[Dict[str, str]]]
    language: str
    thread_id: str
    is_first_call: bool
    user_id: str


class BaseGenerationState(MessagesState):
    """
    Common state fields for all generation workflows.

    Extends MessagesState (which provides the `messages` field with
    automatic accumulation). Each generation module inherits from this
    and adds its domain-specific fields (e.g. topic, class_title).
    """

    language: str
    message: Optional[str]
    file_contents: Optional[List[Dict[str, str]]]
    thread_id: str
    is_first_call: bool
    user_id: str

    # Document ingestion
    has_ingested_documents: bool
    research_results: Annotated[List[str], operator.add]

    # Generation
    agent_response: Optional[Any]

    # Evaluation loop
    evaluation_count: int
    evaluation_history: List[EvaluationResult]
    current_score: Optional[float]

    # Output
    final_response: Optional[Any]
    error: Optional[str]


class BaseGenerationOutput(TypedDict):
    """Common output fields for all generation workflows."""

    thread_id: str
    final_response: Optional[Dict[str, Any]]
    error: Optional[str]
