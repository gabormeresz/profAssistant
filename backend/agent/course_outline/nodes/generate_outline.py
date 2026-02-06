"""
Initial outline generation node for the course outline generation workflow.
"""

import logging

from agent.tool_config import get_model_with_tools
from services.api_key_service import require_api_key

from ..state import CourseOutlineState

logger = logging.getLogger(__name__)


async def generate_outline(state: CourseOutlineState) -> dict:
    """
    Generate the initial course outline using the LLM.

    This node invokes the model and allows it to make tool calls
    if it needs additional information. The response is stored in
    agent_response (not messages) to allow for clean JSON formatting later.

    This node is only for initial generation. Refinement is handled
    by a separate refine_outline node.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with the model's response in agent_response.
        If tools are called, also updates messages for tool execution.
    """
    messages = list(state["messages"])

    # Get model with appropriate tools based on whether documents are ingested
    has_documents = state.get("has_ingested_documents", False)
    api_key = await require_api_key(state.get("user_id", ""))
    model_with_tools = get_model_with_tools(has_documents, api_key=api_key)

    response = await model_with_tools.ainvoke(messages)

    # If there are tool calls, we need to add to messages for the ToolNode
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [response], "agent_response": response}

    # Otherwise, just store in agent_response (don't pollute messages with raw response)
    return {"agent_response": response}
