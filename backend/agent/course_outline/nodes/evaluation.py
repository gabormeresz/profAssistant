"""
Evaluation nodes for the course outline generation workflow.

Contains nodes for quality evaluation of generated content.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent.model import get_structured_output_model
from config import EvaluationConfig
from schemas.evaluation import EvaluationResult

from ..state import CourseOutlineState
from ..prompts import get_evaluator_system_prompt

logger = logging.getLogger(__name__)

# Pre-configured model for evaluation structured output
_evaluation_model = get_structured_output_model(EvaluationResult)


def evaluate_outline(state: CourseOutlineState) -> dict:
    """
    Evaluate the generated course outline for quality using scoring.

    This node acts as an evaluator agent that assesses the quality of
    the generated content across multiple dimensions and provides
    a numeric score. Uses structured output for reliable parsing.

    Note: Since evaluation_history doesn't use operator.add, we manually
    accumulate by getting existing history and appending to it.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with evaluation_count, evaluation_history, and current_score.
    """
    # Get current evaluation count (default to 0 if not set)
    current_count = state.get("evaluation_count", 0)
    # Get existing evaluation history (already reset by initialize_conversation for follow-ups)
    existing_history = state.get("evaluation_history", []) or []

    # If we've already done max retries, skip evaluation
    if current_count >= EvaluationConfig.MAX_RETRIES:
        return {
            "evaluation_count": current_count,
        }

    # Get the agent's response to evaluate
    agent_response = state.get("agent_response")
    if not agent_response:
        return {
            "evaluation_count": current_count + 1,
            "current_score": 0.0,
            "evaluation_history": existing_history,
        }

    # Extract content from the agent response
    content_to_evaluate = _extract_content(agent_response)

    # Build evaluation messages with clear context
    language = state.get("language", "English")
    topic = state.get("topic", "Unknown")
    num_classes = state.get("number_of_classes", 0)

    evaluation_request = f"""## Course Outline Evaluation Request

**Expected Topic:** {topic}
**Expected Number of Classes:** {num_classes}

Please evaluate the following course outline against the rubric.
Score each dimension independently, then provide the overall weighted score.

---

## Course Outline to Evaluate

{content_to_evaluate}

---

Provide your evaluation with:
1. Score for each dimension (0.0-1.0)
2. Overall weighted score
3. Verdict (APPROVED if ≥ 0.8, NEEDS_REFINEMENT otherwise)
4. Brief reasoning
5. 1-3 specific, actionable suggestions if NEEDS_REFINEMENT"""

    evaluation_messages = [
        SystemMessage(content=get_evaluator_system_prompt(language)),
        HumanMessage(content=evaluation_request),
    ]

    try:
        # Call the evaluator model with structured output
        evaluation_result = _evaluation_model.invoke(evaluation_messages)

        # Ensure we have an EvaluationResult object
        if not isinstance(evaluation_result, EvaluationResult):
            return {
                "evaluation_count": current_count + 1,
                "current_score": 0.0,
                "evaluation_history": existing_history,
            }

        # Add to evaluation history (manually accumulate) and update current score
        updated_history = existing_history + [evaluation_result]
        return {
            "evaluation_count": current_count + 1,
            "evaluation_history": updated_history,
            "current_score": evaluation_result.score,
        }

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        # If evaluation fails, return low score but still increment count
        # Don't add to history since we don't have a valid evaluation
        return {
            "evaluation_count": current_count + 1,
            "current_score": 0.0,
            "evaluation_history": existing_history,
        }


def _extract_content(response) -> str:
    """
    Extract string content from an agent response.

    Args:
        response: The agent response object.

    Returns:
        String content from the response.
    """
    if hasattr(response, "content") and response.content:
        return str(response.content)
    return str(response)
