"""
MCP Client manager for integrating MCP tools into the application.

This module provides a singleton manager for connecting to MCP servers
and loading their tools for use in LangGraph workflows.

Configured servers:
- Wikipedia (local SSE server for encyclopedic knowledge)
- Tavily (remote hosted server for web search and content extraction)
"""

from typing import Optional, List, Dict, Any
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import MCPConfig


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

        if MCPConfig.TAVILY_ENABLED:
            if not MCPConfig.TAVILY_API_KEY:
                print("[MCP] Tavily enabled but TAVILY_API_KEY is not set — skipping")
            else:
                servers["tavily"] = {
                    "transport": MCPConfig.TAVILY_TRANSPORT,
                    "url": MCPConfig.TAVILY_URL,
                    "headers": {
                        "Authorization": f"Bearer {MCPConfig.TAVILY_API_KEY}",
                    },
                }

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
            print("[MCP] No MCP servers enabled")
            self._tools = []
            self._initialized = True
            return

        try:
            self._client = MultiServerMCPClient(servers)  # type: ignore[arg-type]

            all_tools = await self._client.get_tools()
            self._tools = self._filter_tools(all_tools)
            self._initialized = True

            tool_names = [t.name for t in self._tools]
            print(f"[MCP] Initialized successfully with tools: {tool_names}")

            # Log any filtered-out tools for transparency
            filtered_out = [t.name for t in all_tools if t not in self._tools]
            if filtered_out:
                print(f"[MCP] Filtered out tools: {filtered_out}")

        except ImportError as e:
            print(f"[MCP] langchain-mcp-adapters not installed: {e}")
            self._tools = []
            self._initialized = True

        except Exception as e:
            print(f"[MCP] Failed to initialize MCP servers: {e}")
            print("[MCP] Continuing without MCP tools")
            if MCPConfig.WIKIPEDIA_ENABLED:
                print(
                    "[MCP]   Ensure wikipedia-mcp is running: "
                    "uv run wikipedia-mcp --transport sse --port 8765"
                )
            if MCPConfig.TAVILY_ENABLED:
                print("[MCP]   Ensure TAVILY_API_KEY is valid")
            self._tools = []
            self._initialized = True

    def get_tools(self) -> List[BaseTool]:
        """
        Get loaded MCP tools.

        Returns:
            List of LangChain tools loaded from MCP servers.
            Empty list if not initialized or initialization failed.
        """
        return self._tools or []

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
                    print(f"[MCP] Error during cleanup: {e}")

        self._client = None
        self._tools = None
        self._initialized = False
        print("[MCP] Cleanup complete")


# Singleton instance for use throughout the application
mcp_manager = MCPClientManager()
