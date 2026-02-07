"""
Response nodes for the presentation generation workflow.

Contains nodes for generating final structured output.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.model import get_structured_output_model
from agent.base.nodes.helpers import extract_content
from schemas.presentation import Presentation
from services.api_key_service import require_api_key

from ..state import PresentationState

logger = logging.getLogger(__name__)

# System prompt for structured output extraction
EXTRACTION_SYSTEM_PROMPT = """You are a JSON extraction assistant. Your task is to extract presentation information from the provided content and format it as a structured JSON object.

Extract the following fields:
- course_title: String (title of the course)
- lesson_title: String (title of this lesson/class)
- class_number: Integer (the class number)
- slides: List of slide objects, each with:
  - slide_number: Integer (sequential, starting from 1)
  - title: String (slide heading)
  - bullet_points: List of strings (1-6 concise bullet points)
  - speaker_notes: String or null (expanded explanation for the instructor)
  - visual_suggestion: String or null (description of a recommended visual)

Be concise and extract only the essential information. If some information is missing, provide reasonable defaults based on the content."""


async def generate_structured_response(state: PresentationState) -> dict:
    """
    Generate the final structured presentation.

    Uses the agent_response from the conversation to produce
    a properly structured Presentation response. Adds a clean JSON
    message to the checkpoint for frontend compatibility.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with final_response and clean AI message.
    """
    try:
        agent_response = state.get("agent_response")
        if not agent_response:
            logger.error("No agent_response found in state")
            return {"error": "No agent response available for generating output"}

        context_content = extract_content(agent_response)
        logger.info(f"Extracted content length: {len(context_content)} characters")

        if not context_content:
            logger.error("Extracted content is empty")

        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Extract the presentation from the following content:\n\n{context_content}"
            ),
        ]

        logger.info("Invoking structured output model...")

        api_key = await require_api_key(state.get("user_id", ""))
        structured_model = get_structured_output_model(Presentation, api_key=api_key)
        response = await structured_model.ainvoke(messages)

        logger.info(f"Structured output model returned: {type(response)}")

        if not isinstance(response, Presentation):
            logger.error(f"Unexpected response type: {type(response)}")
            return {
                "error": "Failed to generate structured output: unexpected response type"
            }

        clean_json = response.model_dump_json()
        clean_ai_message = AIMessage(content=clean_json)

        logger.info("Successfully generated structured presentation")

        return {"final_response": response, "messages": [clean_ai_message]}

    except Exception as e:
        logger.error(f"Failed to generate structured output: {e}", exc_info=True)
        return {"error": f"Failed to generate structured output: {str(e)}"}
