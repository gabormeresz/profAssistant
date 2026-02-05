"""
State definitions for the lesson plan generation workflow.

This module defines TypedDict classes for managing state throughout
the LangGraph workflow, with clear separation of input, processing,
and output schemas.
"""

from typing import TypedDict, List, Dict, Optional, Annotated, Any
from langgraph.graph import MessagesState
from schemas.lesson_plan import LessonPlan
from schemas.evaluation import EvaluationResult
import operator


class LessonPlanInput(TypedDict):
    """
    Input schema for lesson plan generation.

    These are the parameters provided by the user when starting
    or continuing a lesson plan generation conversation.
    """

    course_title: str
    class_number: int
    class_title: str
    learning_objectives: List[str]
    key_topics: List[str]
    activities_projects: List[str]
    message: Optional[str]  # Optional user comment/instruction
    file_contents: Optional[List[Dict[str, str]]]
    language: str
    thread_id: str  # Always provided (generated before graph runs)
    is_first_call: bool  # Flag to distinguish new vs follow-up conversations


class LessonPlanState(MessagesState):
    """
    State for the lesson plan generation workflow.

    Inherits 'messages' from MessagesState for chat history management.
    Adds domain-specific fields for lesson plan generation.
    """

    # Input fields (from user request)
    course_title: str
    class_number: int
    class_title: str
    learning_objectives: List[str]
    key_topics: List[str]
    activities_projects: List[str]
    language: str
    message: Optional[str]  # User message/instruction (for follow-ups)
    file_contents: Optional[List[Dict[str, str]]]

    # Session management
    thread_id: str
    is_first_call: bool
    has_ingested_documents: bool  # Flag to enable/disable document search tool

    # Research results from tools (accumulated within a run)
    research_results: Annotated[List[str], operator.add]

    # Intermediate agent response (not saved to messages directly)
    agent_response: Optional[Any]

    # Evaluation loop state with history tracking
    # Note: evaluation_history is NOT using operator.add because we need to
    # reset it between conversation turns. We manually manage accumulation
    # in the evaluate_lesson_plan node.
    evaluation_count: int  # Counter for evaluation iterations (max 3)
    evaluation_history: List[
        EvaluationResult
    ]  # All evaluations for context (reset per turn)
    current_score: Optional[float]  # Latest score for plateau detection

    # Output fields
    final_response: Optional[LessonPlan]
    error: Optional[str]


class LessonPlanOutput(TypedDict):
    """
    Output schema for lesson plan generation.

    Defines the final structure returned by the workflow.
    Note: final_response is a Dict (not LessonPlan) because LangGraph
    serializes Pydantic models when returning from the graph.
    """

    thread_id: str
    final_response: Optional[Dict[str, Any]]  # Serialized LessonPlan
    error: Optional[str]
