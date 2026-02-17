"""
Response nodes for the lesson plan generation workflow.

Contains nodes for generating final structured output.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.input_sanitizer import EXTRACTION_SYSTEM_PROMPT
from agent.model import get_structured_output_model
from agent.base.nodes.helpers import extract_content
from schemas.lesson_plan import LessonPlan
from services.api_key_service import resolve_user_llm_config

from ..state import LessonPlanState

logger = logging.getLogger(__name__)


async def generate_structured_response(state: LessonPlanState) -> dict:
    """
    Generate the final structured lesson plan.

    Uses the agent_response from the conversation to produce
    a properly structured LessonPlan response. Adds a clean JSON
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

        # Build messages with clear extraction instructions
        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Extract the lesson plan from the content "
                    "inside <generated_content> tags below.\n\n"
                    f"<generated_content>\n{context_content}\n</generated_content>"
                )
            ),
        ]

        logger.info("Invoking structured output model...")

        # Generate structured output (per-request for user API key)
        api_key, model_name = await resolve_user_llm_config(state.get("user_id", ""))
        structured_model = get_structured_output_model(
            LessonPlan,
            api_key=api_key,
            model_name=model_name,
            purpose="generator",
        )
        response = await structured_model.ainvoke(messages)

        logger.info(f"Structured output model returned: {type(response)}")

        # Ensure we have a LessonPlan object
        if not isinstance(response, LessonPlan):
            logger.error(f"Unexpected response type: {type(response)}")
            return {
                "error": "Failed to generate structured output: unexpected response type"
            }

        # Convert the structured response to clean JSON for checkpoint storage
        # This ensures the frontend can parse it without markdown code fences
        clean_json = response.model_dump_json()
        clean_ai_message = AIMessage(content=clean_json)

        logger.info("Successfully generated structured lesson plan")

        # Add the clean JSON as the AI message to the checkpoint
        return {"final_response": response, "messages": [clean_ai_message]}

    except Exception as e:
        logger.error("Failed to generate structured output: %s", e, exc_info=True)
        return {"error": "Failed to generate structured output"}
