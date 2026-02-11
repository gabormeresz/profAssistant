"""
Evaluation nodes for the assessment generation workflow.

Contains nodes for quality evaluation of generated assessment content.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent.model import get_structured_output_model
from agent.base.nodes.helpers import extract_content
from config import EvaluationConfig
from schemas.evaluation import EvaluationResult
from services.api_key_service import resolve_user_llm_config

from ..state import AssessmentState
from ..prompts import get_evaluator_system_prompt

logger = logging.getLogger(__name__)


async def evaluate_assessment(state: AssessmentState) -> dict:
    """
    Evaluate the generated assessment for quality using scoring.

    This node acts as an evaluator agent that assesses the quality of
    the generated assessment across multiple dimensions and provides
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
    course_title = state.get("course_title", "Unknown")
    assessment_type = state.get("assessment_type", "quiz")
    key_topics = state.get("key_topics", [])

    topics_str = "\n".join(f"  - {t}" for t in key_topics)

    evaluation_request = f"""## Assessment Evaluation Request

**Course Title:** {course_title}
**Assessment Type:** {assessment_type}
**Key Topics:**
{topics_str}

Please evaluate the following assessment against the rubric.
Score each dimension independently, then provide the overall weighted score.

---

## Assessment to Evaluate

{content_to_evaluate}

---

Provide your evaluation with:
1. Score for each dimension (0.0-1.0)
2. Overall weighted score
3. Verdict (APPROVED if ≥ 0.8, NEEDS_REFINEMENT otherwise)
4. Brief reasoning
5. 1-3 specific, actionable suggestions if NEEDS_REFINEMENT"""

    evaluation_messages = [
        SystemMessage(
            content=get_evaluator_system_prompt(
                language,
                question_type_configs=state.get("question_type_configs", []),
            )
        ),
        HumanMessage(content=evaluation_request),
    ]

    try:
        # Call the evaluator model with structured output
        api_key, model_name = await resolve_user_llm_config(state.get("user_id", ""))
        evaluation_model = get_structured_output_model(
            EvaluationResult,
            api_key=api_key,
            model_name=model_name,
            purpose="evaluator",
        )
        evaluation_result = await evaluation_model.ainvoke(evaluation_messages)

        # Ensure we have an EvaluationResult object
        if not isinstance(evaluation_result, EvaluationResult):
            return {
                "evaluation_count": current_count + 1,
                "current_score": 0.0,
                "evaluation_history": existing_history,
            }

        # Add to evaluation history and update current score
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
