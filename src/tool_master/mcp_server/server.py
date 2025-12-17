"""MCP Server that exposes Tool Master tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tool_master.schemas.tool import Tool
    from tool_master.registry.registry import ToolRegistry


class ToolMasterMCPServer:
    """
    MCP Server that exposes Tool Master tools via the Model Context Protocol.

    This server wraps Tool Master tools and exposes them as MCP tools,
    allowing any MCP-compatible client to discover and call them.

    Example usage:
        ```python
        from tool_master.mcp_server import ToolMasterMCPServer
        from tool_master.tools import datetime_tools

        server = ToolMasterMCPServer("my-tools")
        server.register_tools(datetime_tools.TOOLS)

        # Run with stdio transport
        import asyncio
        asyncio.run(server.run_stdio())
        ```

    Example with registry:
        ```python
        from tool_master import ToolRegistry
        from tool_master.mcp_server import ToolMasterMCPServer

        registry = ToolRegistry()
        # ... register tools ...

        server = ToolMasterMCPServer("my-tools")
        server.register_from_registry(registry)
        ```
    """

    def __init__(self, name: str = "tool-master") -> None:
        """
        Initialize the MCP server.

        Args:
            name: The server name to advertise to clients
        """
        # Import here to make mcp optional
        from mcp.server import Server

        self._server = Server(name)
        self._tools: dict[str, Tool] = {}
        self._setup_handlers()

    def register_tool(self, tool: Tool) -> None:
        """
        Register a Tool Master tool with the server.

        Args:
            tool: The Tool to register
        """
        self._tools[tool.name] = tool

    def register_tools(self, tools: list[Tool]) -> None:
        """
        Register multiple tools with the server.

        Args:
            tools: List of Tools to register
        """
        for tool in tools:
            self.register_tool(tool)

    def register_from_registry(self, registry: ToolRegistry) -> None:
        """
        Register all tools from a ToolRegistry.

        Args:
            registry: The ToolRegistry to pull tools from
        """
        for tool in registry.all():
            self.register_tool(tool)

    def _setup_handlers(self) -> None:
        """Set up MCP protocol handlers for list_tools and call_tool."""
        from mcp.types import CallToolResult, TextContent, Tool as MCPTool

        @self._server.list_tools()
        async def handle_list_tools() -> list[MCPTool]:
            """Return all registered tools in MCP format."""
            return [self._to_mcp_tool(tool) for tool in self._tools.values()]

        @self._server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None = None
        ) -> CallToolResult:
            """Execute a tool by name with given arguments."""
            tool = self._tools.get(name)
            if not tool:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True,
                )

            try:
                result = await tool.execute(**(arguments or {}))
                return self._to_call_result(result)
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Tool execution error: {e}")],
                    isError=True,
                )

    def _to_mcp_tool(self, tool: Tool) -> Any:
        """
        Convert a Tool Master tool to an MCP Tool.

        Args:
            tool: The Tool to convert

        Returns:
            MCP Tool object
        """
        from mcp.types import Tool as MCPTool

        return MCPTool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.to_json_schema(),
        )

    def _to_call_result(self, result: Any) -> Any:
        """
        Convert a ToolResult to an MCP CallToolResult.

        Args:
            result: The ToolResult from tool execution

        Returns:
            MCP CallToolResult object
        """
        from mcp.types import CallToolResult, TextContent

        if result.success:
            if isinstance(result.data, str):
                text = result.data
            elif result.data is None:
                text = ""
            else:
                text = json.dumps(result.data)

            return CallToolResult(
                content=[TextContent(type="text", text=text)],
                isError=False,
            )

        return CallToolResult(
            content=[TextContent(type="text", text=result.error or "Unknown error")],
            isError=True,
        )

    async def run_stdio(self) -> None:
        """
        Run the server with stdio transport.

        This is the most common way to run an MCP server, where it
        communicates via stdin/stdout with the client.
        """
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                self._server.create_initialization_options(),
            )

    @property
    def server(self) -> Any:
        """Access the underlying MCP Server instance for advanced use cases."""
        return self._server

    @property
    def tools(self) -> dict[str, Tool]:
        """Get a copy of registered tools."""
        return dict(self._tools)
