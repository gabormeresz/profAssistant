"""
Lesson plan refinement node for the lesson plan generation workflow.
"""

import logging

from langchain_core.messages import HumanMessage

from agent.tool_config import get_model_with_tools
from services.api_key_service import require_api_key

from ..state import LessonPlanState
from ..prompts import get_refinement_prompt

logger = logging.getLogger(__name__)


async def refine_lesson_plan(state: LessonPlanState) -> dict:
    """
    Refine the lesson plan based on evaluation feedback.

    This node takes the evaluation history and uses it to generate
    an improved version of the lesson plan, focusing on the
    lowest-scoring dimensions.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with the refined response in agent_response.
    """
    messages = list(state["messages"])

    # Get the previous response content for context
    agent_response = state.get("agent_response")
    original_content = ""
    if agent_response and hasattr(agent_response, "content"):
        original_content = str(agent_response.content)

    # Get evaluation history for context
    evaluation_history = state.get("evaluation_history", [])
    language = state.get("language", "English")

    refinement_prompt = get_refinement_prompt(
        original_content, evaluation_history, language
    )
    refinement_message = HumanMessage(content=refinement_prompt)
    messages.append(refinement_message)

    # Get model with appropriate tools based on whether documents are ingested
    has_documents = state.get("has_ingested_documents", False)
    api_key = await require_api_key(state.get("user_id", ""))
    model_with_tools = get_model_with_tools(has_documents, api_key=api_key)

    response = await model_with_tools.ainvoke(messages)

    # If there are tool calls, we need to add both the refinement prompt and response to messages
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [refinement_message, response], "agent_response": response}

    # Otherwise, just store in agent_response (don't pollute messages with prompts)
    return {"agent_response": response}
