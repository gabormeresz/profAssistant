"""
Evaluation nodes for the lesson plan generation workflow.

Contains nodes for quality evaluation of generated content.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent.model import get_structured_output_model
from agent.base.nodes.helpers import extract_content
from config import EvaluationConfig
from schemas.evaluation import EvaluationResult
from services.api_key_service import require_api_key

from ..state import LessonPlanState
from ..prompts import get_evaluator_system_prompt

logger = logging.getLogger(__name__)


async def evaluate_lesson_plan(state: LessonPlanState) -> dict:
    """
    Evaluate the generated lesson plan for quality using scoring.

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
    content_to_evaluate = extract_content(agent_response)

    # Build evaluation messages with clear context
    language = state.get("language", "English")
    class_title = state.get("class_title", "Unknown")
    class_number = state.get("class_number", 0)
    learning_objectives = state.get("learning_objectives", [])

    objectives_str = "\n".join(f"  - {obj}" for obj in learning_objectives)

    evaluation_request = f"""## Lesson Plan Evaluation Request

**Class Number:** {class_number}
**Class Title:** {class_title}
**Learning Objectives:**
{objectives_str}

Please evaluate the following lesson plan against the rubric.
Score each dimension independently, then provide the overall weighted score.

---

## Lesson Plan to Evaluate

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
        # Call the evaluator model with structured output (per-request for user API key)
        api_key = await require_api_key(state.get("user_id", ""))
        evaluation_model = get_structured_output_model(
            EvaluationResult, api_key=api_key
        )
        evaluation_result = await evaluation_model.ainvoke(evaluation_messages)

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
