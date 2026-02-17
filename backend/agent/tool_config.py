"""
Shared tool and model configuration for all agent workflows.

Provides consistent tool binding and model configuration across
course_outline, lesson_plan, presentation, and assessment generators.

Tool availability:
- Base tools (always available): MCP tools (Wikipedia; Tavily web search if API key is set)
- Document search: only available when user has uploaded documents

All external tool outputs (MCP tools) are wrapped with sanitization
to defend against indirect prompt injection via adversarial content
in web search results, Wikipedia articles, or uploaded documents.
"""

import logging
from typing import List, Optional

from langchain_core.tools import BaseTool

from .input_sanitizer import sanitize_tool_output
from .model import ModelPurpose, get_model
from .tools import search_uploaded_documents
from services.mcp_client import mcp_manager

logger = logging.getLogger(__name__)


def _wrap_mcp_tool(tool: BaseTool) -> BaseTool:
    """
    Wrap an MCP tool so its output is sanitized before reaching the LLM.

    This defends against indirect prompt injection by marking tool output
    as external reference data and truncating overly long payloads.

    Handles tools with response_format='content_and_artifact' by preserving
    the (content, artifact) tuple structure expected by LangChain.

    Args:
        tool: The original MCP tool.

    Returns:
        A new tool with the same interface but sanitized output.
    """
    is_content_and_artifact = (
        getattr(tool, "response_format", None) == "content_and_artifact"
    )

    if tool.coroutine:
        original_coroutine = tool.coroutine

        async def sanitized_coroutine(*args, **kwargs):
            result = await original_coroutine(*args, **kwargs)
            if is_content_and_artifact and isinstance(result, tuple):
                content, artifact = result
                return sanitize_tool_output(tool.name, str(content)), artifact
            return sanitize_tool_output(tool.name, str(result))

        tool.coroutine = sanitized_coroutine
    else:
        original_func = tool.func

        def sanitized_func(*args, **kwargs):
            result = original_func(*args, **kwargs)
            if is_content_and_artifact and isinstance(result, tuple):
                content, artifact = result
                return sanitize_tool_output(tool.name, str(content)), artifact
            return sanitize_tool_output(tool.name, str(result))

        tool.func = sanitized_func

    return tool


def get_base_tools() -> List[BaseTool]:
    """
    Get base tools that are always available.

    MCP tool outputs are wrapped with sanitization to defend
    against indirect prompt injection from external content.

    Returns:
        List of base tools: MCP tools (Tavily web search, Wikipedia, etc.)
    """
    raw_tools = mcp_manager.get_tools()
    return [_wrap_mcp_tool(tool) for tool in raw_tools]


def get_available_tools(has_documents: bool = False) -> List[BaseTool]:
    """
    Get tools available for agent invocation.

    Args:
        has_documents: Whether the user has uploaded documents.

    Returns:
        List of tools: base tools, optionally with document search.
    """
    tools = get_base_tools()

    if has_documents:
        tools.append(search_uploaded_documents)

    return tools


def get_tools_for_toolnode() -> List[BaseTool]:
    """
    Get all tools for ToolNode registration.

    Includes all possible tools so that ToolNode can handle
    any tool call the model might make.

    Returns:
        List of all available tools (base + document search).
    """
    return get_available_tools(has_documents=True)


def get_model_with_tools(
    has_documents: bool = False,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    purpose: ModelPurpose = "generator",
):
    """
    Get model bound with appropriate tools.

    Args:
        has_documents: Whether to include document search tool.
        api_key: Optional OpenAI API key for per-user model.
        model_name: Optional OpenAI model identifier.
        purpose: Preset purpose for model configuration.

    Returns:
        Model with tools bound.
    """
    tools_to_use = get_available_tools(has_documents)
    return get_model(api_key, model_name=model_name, purpose=purpose).bind_tools(
        tools_to_use
    )
