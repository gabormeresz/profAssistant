"""
Initial lesson plan generation node for the lesson plan generation workflow.
"""

import logging

from agent.tool_config import get_model_with_tools

from ..state import LessonPlanState

logger = logging.getLogger(__name__)


def generate_lesson_plan(state: LessonPlanState) -> dict:
    """
    Generate the initial lesson plan using the LLM.

    This node invokes the model and allows it to make tool calls
    if it needs additional information. The response is stored in
    agent_response (not messages) to allow for clean JSON formatting later.

    This node is only for initial generation. Refinement is handled
    by a separate refine_lesson_plan node.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with the model's response in agent_response.
        If tools are called, also updates messages for tool execution.
    """
    messages = list(state["messages"])

    # Get model with appropriate tools based on whether documents are ingested
    has_documents = state.get("has_ingested_documents", False)
    model_with_tools = get_model_with_tools(has_documents)

    response = model_with_tools.invoke(messages)

    # If there are tool calls, we need to add to messages for the ToolNode
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [response], "agent_response": response}

    # Otherwise, just store in agent_response (don't pollute messages with raw response)
    return {"agent_response": response}
