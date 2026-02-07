"""
Evaluation nodes for the presentation generation workflow.

Contains nodes for quality evaluation of generated presentation content.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent.model import get_structured_output_model
from agent.base.nodes.helpers import extract_content
from config import EvaluationConfig
from schemas.evaluation import EvaluationResult
from services.api_key_service import require_api_key

from ..state import PresentationState
from ..prompts import get_evaluator_system_prompt

logger = logging.getLogger(__name__)


async def evaluate_presentation(state: PresentationState) -> dict:
    """
    Evaluate the generated presentation for quality using scoring.

    This node acts as an evaluator agent that assesses the quality of
    the generated slides across multiple dimensions and provides
    a numeric score. Uses structured output for reliable parsing.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with evaluation_count, evaluation_history, and current_score.
    """
    current_count = state.get("evaluation_count", 0)
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
    content_to_evaluate = extract_content(agent_response)

    # Build evaluation messages with clear context
    language = state.get("language", "English")
    class_title = state.get("class_title", "Unknown")
    class_number = state.get("class_number", 0)
    learning_objective = state.get("learning_objective") or "Not specified"
    key_points = state.get("key_points", [])

    key_points_str = (
        "\n".join(f"  - {kp}" for kp in key_points) if key_points else "  (none)"
    )

    evaluation_request = f"""## Presentation Evaluation Request

**Class Number:** {class_number}
**Class Title:** {class_title}
**Learning Objective:** {learning_objective}
**Key Points:**
{key_points_str}

Please evaluate the following presentation against the rubric.
Score each dimension independently, then provide the overall weighted score.

---

## Presentation to Evaluate

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
        api_key = await require_api_key(state.get("user_id", ""))
        evaluation_model = get_structured_output_model(
            EvaluationResult, api_key=api_key
        )
        evaluation_result = await evaluation_model.ainvoke(evaluation_messages)

        if not isinstance(evaluation_result, EvaluationResult):
            return {
                "evaluation_count": current_count + 1,
                "current_score": 0.0,
                "evaluation_history": existing_history,
            }

        updated_history = existing_history + [evaluation_result]
        return {
            "evaluation_count": current_count + 1,
            "evaluation_history": updated_history,
            "current_score": evaluation_result.score,
        }

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return {
            "evaluation_count": current_count + 1,
            "current_score": 0.0,
            "evaluation_history": existing_history,
        }
