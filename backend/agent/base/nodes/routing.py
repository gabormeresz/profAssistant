"""
Routing functions shared across all generation workflows.

Contains conditional edge functions for graph navigation.
These are identical for all content types since they only
inspect shared state fields (agent_response, evaluation_count, etc.).
"""

import logging
from typing import Literal

from config import EvaluationConfig

from .helpers import has_tool_calls
from ..state import BaseGenerationState

logger = logging.getLogger(__name__)


def route_after_generate(state: BaseGenerationState) -> Literal["tools", "evaluate"]:
    """
    Route the workflow after generation.

    Checks if the generator wants to use tools or if it's ready to be evaluated.

    Args:
        state: The current workflow state.

    Returns:
        "tools" if tools should be called, "evaluate" otherwise.
    """
    agent_response = state.get("agent_response")

    if not agent_response:
        return "evaluate"

    if has_tool_calls(agent_response):
        return "tools"

    return "evaluate"


def route_after_refine(
    state: BaseGenerationState,
) -> Literal["tools_refine", "evaluate"]:
    """
    Route the workflow after refinement.

    Checks if the refiner wants to use tools or if it's ready to be evaluated.

    Args:
        state: The current workflow state.

    Returns:
        "tools_refine" if tools should be called, "evaluate" otherwise.
    """
    agent_response = state.get("agent_response")

    if not agent_response:
        return "evaluate"

    if has_tool_calls(agent_response):
        return "tools_refine"

    return "evaluate"


def route_after_evaluate(state: BaseGenerationState) -> Literal["refine", "respond"]:
    """
    Route the workflow after evaluation with plateau detection.

    Decides whether to refine based on:
    1. Score threshold (>= 0.8 means approved)
    2. Max retries reached
    3. Score plateau (not improving significantly)
    4. Empty evaluation history (evaluation failed)

    Args:
        state: The current workflow state.

    Returns:
        "refine" if more refinement needed, "respond" otherwise.
    """
    evaluation_count = state.get("evaluation_count", 0)
    current_score = state.get("current_score") or 0.0
    evaluation_history = state.get("evaluation_history", [])

    # If evaluation history is empty (evaluation failed), go to respond
    # We can't refine without evaluation feedback
    if not evaluation_history:
        logger.info("No evaluation history, going to respond")
        return "respond"

    # Check if score meets approval threshold
    if current_score >= EvaluationConfig.APPROVAL_THRESHOLD:
        logger.info(
            f"Score {current_score:.2f} >= {EvaluationConfig.APPROVAL_THRESHOLD}, APPROVED"
        )
        return "respond"

    # Check if we've exceeded max retries
    if evaluation_count >= EvaluationConfig.MAX_RETRIES:
        logger.info(
            f"Max retries ({EvaluationConfig.MAX_RETRIES}) reached, going to respond"
        )
        return "respond"

    # Check for plateau - if we have at least 2 evaluations, compare scores
    if len(evaluation_history) >= 2:
        previous_score = evaluation_history[-2].score
        improvement = current_score - previous_score

        if improvement < EvaluationConfig.MIN_IMPROVEMENT_THRESHOLD:
            logger.info(
                f"Plateau detected: improvement {improvement:.3f} < "
                f"{EvaluationConfig.MIN_IMPROVEMENT_THRESHOLD}"
            )
            return "respond"

        logger.info(f"Score improved by {improvement:.3f}, continuing refinement")

    logger.info(
        f"Score {current_score:.2f} < {EvaluationConfig.APPROVAL_THRESHOLD}, "
        "going to refine"
    )
    return "refine"
