"""
Response nodes for the assessment generation workflow.

Contains nodes for generating final structured output.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.input_sanitizer import EXTRACTION_SYSTEM_PROMPT
from agent.model import get_structured_output_model
from agent.base.nodes.helpers import extract_content
from schemas.assessment import (
    Assessment,
    build_dynamic_assessment_model,
)
from services.api_key_service import resolve_user_llm_config

from ..state import AssessmentState

logger = logging.getLogger(__name__)

# Assessment-specific extraction rules appended to the shared prompt
_ASSESSMENT_EXTRACTION_RULES = """\nAdditional rules for assessment extraction:
- Extract ONLY the sections and questions that appear in the content.
- Do NOT invent, add, or remove sections or questions.
- For true/false: correct_answer must be exactly "true" or "false" (lowercase).
- For multiple choice: correct_answer must match an option label (e.g. "B").
- Ensure total_points equals the sum of all individual question points.
"""

_ASSESSMENT_EXTRACTION_SYSTEM_PROMPT = (
    EXTRACTION_SYSTEM_PROMPT + _ASSESSMENT_EXTRACTION_RULES
)


async def generate_structured_response(state: AssessmentState) -> dict:
    """
    Generate the final structured assessment.

    Uses the agent_response from the conversation to produce
    a properly structured Assessment response. Adds a clean JSON
    message to the checkpoint for frontend compatibility.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with final_response and clean AI message.
    """
    try:
        # Get the agent's response content
        agent_response = state.get("agent_response")
        if not agent_response:
            logger.error("No agent_response found in state")
            return {"error": "No agent response available for generating output"}

        # Extract content from the agent response
        context_content = extract_content(agent_response)
        logger.info(f"Extracted content length: {len(context_content)} characters")

        if not context_content:
            logger.error("Extracted content is empty")

        # ── Dynamic schema: lock section types & count to match request ──
        question_type_configs = state.get("question_type_configs", [])
        DynamicAssessment = build_dynamic_assessment_model(question_type_configs)
        logger.info(
            f"Using {'dynamic' if DynamicAssessment is not Assessment else 'static'} "
            f"assessment schema ({len(question_type_configs)} type config(s))"
        )

        # Build messages for extraction
        messages = [
            SystemMessage(content=_ASSESSMENT_EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Extract the assessment from the content "
                    "inside <generated_content> tags below.\n\n"
                    f"<generated_content>\n{context_content}\n</generated_content>"
                )
            ),
        ]

        logger.info("Invoking structured output model...")

        # Generate structured output
        api_key, model_name = await resolve_user_llm_config(state.get("user_id", ""))
        structured_model = get_structured_output_model(
            DynamicAssessment,
            api_key=api_key,
            model_name=model_name,
            purpose="generator",
        )
        response = await structured_model.ainvoke(messages)

        logger.info(f"Structured output model returned: {type(response)}")

        # Ensure we have an Assessment object
        if not isinstance(response, Assessment):
            logger.error(f"Unexpected response type: {type(response)}")
            return {
                "error": "Failed to generate structured output: unexpected response type"
            }

        # Convert the structured response to clean JSON for checkpoint storage
        clean_json = response.model_dump_json()
        clean_ai_message = AIMessage(content=clean_json)

        logger.info("Successfully generated structured assessment")

        # Add the clean JSON as the AI message to the checkpoint
        return {
            "final_response": response,
            "messages": [clean_ai_message],
        }

    except Exception as e:
        logger.error("Failed to generate structured assessment: %s", e, exc_info=True)
        return {"error": "Failed to generate structured assessment"}
