"""
Shared helper functions used by generation workflow nodes.
"""

from langchain_core.messages import AIMessage


def extract_content(response) -> str:
    """
    Extract string content from an agent response.

    Args:
        response: The agent response object (typically an AIMessage).

    Returns:
        String content from the response.
    """
    if hasattr(response, "content") and response.content:
        return str(response.content)
    return str(response)


def has_tool_calls(response) -> bool:
    """
    Check if an agent response has pending tool calls.

    Args:
        response: The agent response to check.

    Returns:
        True if the response has tool calls, False otherwise.
    """
    return isinstance(response, AIMessage) and bool(response.tool_calls)
