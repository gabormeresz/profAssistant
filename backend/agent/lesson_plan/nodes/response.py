"""
Response nodes for the lesson plan generation workflow.

Contains nodes for generating final structured output.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.model import get_structured_output_model
from schemas.lesson_plan import LessonPlan
from services.api_key_service import require_api_key

from ..state import LessonPlanState

logger = logging.getLogger(__name__)

# System prompt for structured output extraction
EXTRACTION_SYSTEM_PROMPT = """You are a JSON extraction assistant. Your task is to extract lesson plan information from the provided content and format it as a structured JSON object.

Extract the following fields:
- class_number: Integer (the class/lesson number)
- class_title: String (title of this lesson)
- learning_objective: String (main learning goal)
- key_points: List of strings (2-10 essential concepts)
- lesson_breakdown: List of objects with section_title and description
- activities: List of objects with name, objective, and instructions
- homework: String (homework assignment)
- extra_activities: String (optional enrichment activities)

Be concise and extract only the essential information. If some information is missing, provide reasonable defaults based on the content."""


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
        context_content = _extract_content(agent_response)
        logger.info(f"Extracted content length: {len(context_content)} characters")

        if not context_content:
            logger.error("Extracted content is empty")
            return {"error": "No context available for generating response"}

        # Truncate if content is too long (>30k chars can cause issues)
        if len(context_content) > 30000:
            logger.warning(
                f"Content too long ({len(context_content)} chars), truncating to 30000"
            )
            context_content = context_content[:30000]

        # Build messages with clear extraction instructions
        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Extract the lesson plan from the following content:\n\n{context_content}"
            ),
        ]

        logger.info("Invoking structured output model...")

        # Generate structured output (per-request for user API key)
        api_key = await require_api_key(state.get("user_id", ""))
        structured_model = get_structured_output_model(LessonPlan, api_key=api_key)
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
        logger.error(f"Failed to generate structured output: {e}", exc_info=True)
        return {"error": f"Failed to generate structured output: {str(e)}"}


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
