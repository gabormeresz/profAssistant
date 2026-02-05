"""
MCP Client manager for integrating MCP tools into the application.

This module provides a singleton manager for connecting to MCP servers
and loading their tools for use in LangGraph workflows.
"""

from typing import Optional, List
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

    async def initialize(self) -> None:
        """
        Initialize MCP client connections.

        Connects to configured MCP servers (e.g., Wikipedia) and loads
        their tools. Safe to call multiple times - will only initialize once.
        """
        if self._initialized:
            return

        if not MCPConfig.WIKIPEDIA_ENABLED:
            print("[MCP] Wikipedia server disabled via configuration")
            self._tools = []
            self._initialized = True
            return

        try:
            # Import here to avoid import errors if package not installed

            self._client = MultiServerMCPClient(
                {  # type: ignore[arg-type]
                    "wikipedia": {
                        "transport": MCPConfig.WIKIPEDIA_TRANSPORT,
                        "url": MCPConfig.WIKIPEDIA_URL,
                    }
                }
            )

            self._tools = await self._client.get_tools()
            self._initialized = True

            tool_names = [t.name for t in self._tools] if self._tools else []
            print(f"[MCP] Initialized successfully with tools: {tool_names}")

        except ImportError as e:
            print(f"[MCP] langchain-mcp-adapters not installed: {e}")
            self._tools = []
            self._initialized = True

        except Exception as e:
            print(f"[MCP] Failed to initialize Wikipedia server: {e}")
            print(
                "[MCP] Continuing without MCP tools - ensure wikipedia-mcp is running:"
            )
            print("[MCP]   uv run wikipedia-mcp --transport sse --port 8765")
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
