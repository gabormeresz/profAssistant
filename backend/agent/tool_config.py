"""
Shared tool and model configuration for all agent workflows.

Provides consistent tool binding and model configuration across
course_outline, lesson_plan, presentation, and assessment generators.

Tool availability:
- Base tools (always available): web_search + MCP tools (Wikipedia, etc.)
- Document search: only available when user has uploaded documents
"""

import logging
from typing import List

from langchain_core.tools import BaseTool

from .model import model
from .tools import web_search, search_uploaded_documents
from services.mcp_client import mcp_manager

logger = logging.getLogger(__name__)


def get_base_tools() -> List[BaseTool]:
    """
    Get base tools that are always available.

    Returns:
        List of base tools: web_search + MCP tools (Wikipedia, etc.)
    """
    return [web_search] + mcp_manager.get_tools()


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


def get_model_with_tools(has_documents: bool = False):
    """
    Get model bound with appropriate tools.

    Args:
        has_documents: Whether to include document search tool.

    Returns:
        Model with tools bound.
    """
    tools_to_use = get_available_tools(has_documents)
    return model.bind_tools(tools_to_use)
