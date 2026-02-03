"""
State definitions for the course outline generation workflow.

This module defines TypedDict classes for managing state throughout
the LangGraph workflow, with clear separation of input, processing,
and output schemas.
"""

from typing import TypedDict, List, Dict, Optional, Annotated, Any
from langgraph.graph import MessagesState
from schemas.course_outline import CourseOutline
from schemas.evaluation import EvaluationResult
import operator


class CourseOutlineInput(TypedDict):
    """
    Input schema for course outline generation.

    These are the parameters provided by the user when starting
    or continuing a course outline generation conversation.
    """

    topic: str
    number_of_classes: int
    message: Optional[str]  # Optional user comment/instruction
    file_contents: Optional[List[Dict[str, str]]]
    language: str
    thread_id: str  # Always provided (generated before graph runs)
    is_first_call: bool  # Flag to distinguish new vs follow-up conversations


class CourseOutlineState(MessagesState):
    """
    State for the course outline generation workflow.

    Inherits 'messages' from MessagesState for chat history management.
    Adds domain-specific fields for course outline generation.
    """

    # Input fields (from user request)
    topic: str
    number_of_classes: int
    language: str
    message: Optional[str]  # User message/instruction (for follow-ups)
    file_contents: Optional[List[Dict[str, str]]]

    # Session management
    thread_id: str
    is_first_call: bool

    # Research results from tools (accumulated within a run)
    research_results: Annotated[List[str], operator.add]

    # Intermediate agent response (not saved to messages directly)
    agent_response: Optional[Any]

    # Evaluation loop state with history tracking
    # Note: evaluation_history is NOT using operator.add because we need to
    # reset it between conversation turns. We manually manage accumulation
    # in the evaluate_outline node.
    evaluation_count: int  # Counter for evaluation iterations (max 3)
    evaluation_history: List[
        EvaluationResult
    ]  # All evaluations for context (reset per turn)
    current_score: Optional[float]  # Latest score for plateau detection

    # Output fields
    final_response: Optional[CourseOutline]
    error: Optional[str]


class CourseOutlineOutput(TypedDict):
    """
    Output schema for course outline generation.

    Defines the final structure returned by the workflow.
    Note: final_response is a Dict (not CourseOutline) because LangGraph
    serializes Pydantic models when returning from the graph.
    """

    thread_id: str
    final_response: Optional[Dict[str, Any]]  # Serialized CourseOutline
    error: Optional[str]
