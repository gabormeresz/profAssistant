"""
Response nodes for the course outline generation workflow.

Contains nodes for generating final structured output.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage

from agent.model import get_structured_output_model
from agent.base.nodes.helpers import extract_content
from schemas.course_outline import CourseOutline
from services.api_key_service import resolve_user_llm_config

from ..state import CourseOutlineState

logger = logging.getLogger(__name__)


async def generate_structured_response(state: CourseOutlineState) -> dict:
    """
    Generate the final structured course outline.

    Uses the agent_response from the conversation to produce
    a properly structured CourseOutline response. Adds a clean JSON
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
            return {"error": "No agent response available for generating output"}

        # Extract content from the agent response
        context_content = extract_content(agent_response)

        if not context_content:
            return {"error": "No context available for generating response"}

        # Generate structured output - the schema enforces the structure,
        # so we just need to pass the content for parsing
        api_key, model_name = await resolve_user_llm_config(state.get("user_id", ""))
        structured_model = get_structured_output_model(
            CourseOutline,
            api_key=api_key,
            model_name=model_name,
            purpose="generator",
        )
        response = await structured_model.ainvoke(
            [HumanMessage(content=context_content)]
        )

        # Ensure we have a CourseOutline object
        if not isinstance(response, CourseOutline):
            return {
                "error": "Failed to generate structured output: unexpected response type"
            }

        # Convert the structured response to clean JSON for checkpoint storage
        # This ensures the frontend can parse it without markdown code fences
        clean_json = response.model_dump_json()
        clean_ai_message = AIMessage(content=clean_json)

        # Add the clean JSON as the AI message to the checkpoint
        return {"final_response": response, "messages": [clean_ai_message]}

    except Exception as e:
        logger.error(f"Failed to generate structured output: {e}")
        return {"error": f"Failed to generate structured output: {str(e)}"}
