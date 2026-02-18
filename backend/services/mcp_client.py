"""
MCP Client manager for integrating MCP tools into the application.

This module provides a singleton manager for connecting to MCP servers
and loading their tools for use in LangGraph workflows.

Configured servers:
- Wikipedia (local SSE server for encyclopedic knowledge)
- Tavily (remote hosted server for web search and content extraction)
"""

import logging
from typing import Optional, List, Dict, Any
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import MCPConfig

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Singleton manager for MCP client connections.

    Handles initialization and cleanup of MCP server connections,
    and provides access to loaded tools for use in LangGraph nodes.
    """

    _instance: Optional["MCPClientManager"] = None
    _client = None
    _tools: Optional[List[BaseTool]] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _build_server_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Build the server configuration dict for MultiServerMCPClient.

        Includes only enabled servers. Tavily uses an Authorization header
        to keep the API key out of URLs and logs.
        """
        servers: Dict[str, Dict[str, Any]] = {}

        if MCPConfig.WIKIPEDIA_ENABLED:
            servers["wikipedia"] = {
                "transport": MCPConfig.WIKIPEDIA_TRANSPORT,
                "url": MCPConfig.WIKIPEDIA_URL,
            }

        if MCPConfig.TAVILY_API_KEY:
            servers["tavily"] = {
                "transport": MCPConfig.TAVILY_TRANSPORT,
                "url": MCPConfig.TAVILY_URL,
                "headers": {
                    "Authorization": f"Bearer {MCPConfig.TAVILY_API_KEY}",
                },
            }
        else:
            logger.info("TAVILY_API_KEY is not set — Tavily web search disabled")

        return servers

    def _filter_tools(self, tools: List[BaseTool]) -> List[BaseTool]:
        """
        Filter loaded tools to only expose allowed ones.

        Tools from each server are filtered to their respective
        allowed-tool lists in MCPConfig.
        """
        allowed = set(MCPConfig.WIKIPEDIA_ALLOWED_TOOLS) | set(
            MCPConfig.TAVILY_ALLOWED_TOOLS
        )
        filtered = [t for t in tools if t.name in allowed]
        return filtered

    def _validate_tool_schemas(self, tools: List[BaseTool]) -> List[BaseTool]:
        """
        Validate that MCP tool schemas match expected constraints.

        Defends against a compromised MCP server injecting prompt payloads
        via altered tool descriptions or adding unexpected parameters.
        Tools that fail validation are logged and excluded.
        """
        expected_schemas = MCPConfig.EXPECTED_TOOL_SCHEMAS
        validated: List[BaseTool] = []

        for tool in tools:
            schema = expected_schemas.get(tool.name)
            if schema is None:
                # No schema expectation defined — accept with a warning
                logger.warning(
                    "MCP tool '%s' has no expected schema defined — accepting as-is",
                    tool.name,
                )
                validated.append(tool)
                continue

            # Check description length
            max_desc_len = schema.get("max_description_length", 500)
            if tool.description and len(tool.description) > max_desc_len:
                logger.warning(
                    "MCP tool '%s' description length (%d) exceeds expected max (%d) "
                    "— possible prompt injection in schema. Tool rejected.",
                    tool.name,
                    len(tool.description),
                    max_desc_len,
                )
                continue

            # Check required parameters are present
            required_params = schema.get("required_params", set())
            if required_params:
                tool_params = set()
                if hasattr(tool, "args_schema") and tool.args_schema:
                    args_schema = tool.args_schema
                    if hasattr(args_schema, "model_fields"):
                        # Pydantic v2 model class
                        tool_params = set(args_schema.model_fields.keys())  # type: ignore[union-attr]
                    elif isinstance(args_schema, dict):
                        # MCP-adapted tools may expose schema as a plain dict
                        props = args_schema.get("properties", args_schema)
                        tool_params = set(props.keys())
                if (
                    not tool_params
                    and hasattr(tool, "args")
                    and isinstance(tool.args, dict)
                ):
                    tool_params = set(tool.args.keys())

                missing = required_params - tool_params
                if missing:
                    logger.warning(
                        "MCP tool '%s' is missing expected params %s "
                        "— schema may have been altered. Tool rejected.",
                        tool.name,
                        missing,
                    )
                    continue

            validated.append(tool)

        return validated

    async def initialize(self) -> None:
        """
        Initialize MCP client connections.

        Connects to configured MCP servers (Wikipedia, Tavily, etc.) and
        loads their tools. Safe to call multiple times — only initializes once.
        """
        if self._initialized:
            return

        servers = self._build_server_config()

        if not servers:
            logger.warning("No MCP servers enabled")
            self._tools = []
            self._initialized = True
            return

        try:
            self._client = MultiServerMCPClient(servers)  # type: ignore[arg-type]

            all_tools = await self._client.get_tools()
            filtered = self._filter_tools(all_tools)
            self._tools = self._validate_tool_schemas(filtered)
            self._initialized = True

            tool_names = [t.name for t in self._tools]
            logger.info("MCP initialized successfully with tools: %s", tool_names)

            # Log any filtered-out tools for transparency
            filtered_out = [t.name for t in all_tools if t not in self._tools]
            if filtered_out:
                logger.info("MCP filtered out tools: %s", filtered_out)

        except ImportError as e:
            logger.error("langchain-mcp-adapters not installed: %s", e)
            self._tools = []
            self._initialized = True

        except Exception as e:
            logger.error("Failed to initialize MCP servers: %s", e)
            logger.info("Continuing without MCP tools")
            if MCPConfig.WIKIPEDIA_ENABLED:
                logger.info(
                    "Ensure wikipedia-mcp is running: "
                    "uv run wikipedia-mcp --transport sse --port 8765"
                )
            if MCPConfig.TAVILY_API_KEY:
                logger.info("Ensure TAVILY_API_KEY is valid")
            self._tools = []
            self._initialized = True

    def get_tools(self) -> List[BaseTool]:
        """
        Get loaded MCP tools.

        Returns a shallow copy so callers cannot mutate the internal list.

        Returns:
            List of LangChain tools loaded from MCP servers.
            Empty list if not initialized or initialization failed.
        """
        return list(self._tools) if self._tools else []

    def is_initialized(self) -> bool:
        """Check if the client manager has been initialized."""
        return self._initialized

    async def cleanup(self) -> None:
        """
        Cleanup MCP client resources.

        Resets the manager state. Called during application shutdown.
        """
        if self._client is not None:
            # Close client if it has a close method
            if hasattr(self._client, "close"):
                try:
                    await self._client.close()  # type: ignore[attr-defined]
                except Exception as e:
                    logger.error("Error during MCP cleanup: %s", e)

        self._client = None
        self._tools = None
        self._initialized = False
        logger.info("MCP cleanup complete")


# Singleton instance for use throughout the application
mcp_manager = MCPClientManager()
