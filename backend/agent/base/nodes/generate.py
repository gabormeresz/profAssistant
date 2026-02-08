"""
Content generation node shared across all generation workflows.

Invokes the LLM with tool access for initial content generation.
The logic is identical for all content types — domain-specific
behavior comes from the system prompt set up in build_messages.
"""

import logging

from agent.tool_config import get_model_with_tools
from services.api_key_service import resolve_user_llm_config

from ..state import BaseGenerationState

logger = logging.getLogger(__name__)


async def generate_content(state: BaseGenerationState) -> dict:
    """
    Generate content using the LLM with tool access.

    Invokes the model and allows it to make tool calls if it needs
    additional information. The response is stored in agent_response
    (not messages) to allow for clean JSON formatting later.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with the model's response in agent_response.
        If tools are called, also updates messages for tool execution.
    """
    messages = list(state["messages"])

    # Get model with appropriate tools based on whether documents are ingested
    has_documents = state.get("has_ingested_documents", False)
    api_key, model_name = await resolve_user_llm_config(state.get("user_id", ""))
    model_with_tools = get_model_with_tools(
        has_documents, api_key=api_key, model_name=model_name, purpose="generator"
    )

    response = await model_with_tools.ainvoke(messages)

    # If there are tool calls, we need to add to messages for the ToolNode
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [response], "agent_response": response}

    # Otherwise, just store in agent_response (don't pollute messages with raw response)
    return {"agent_response": response}
