"""Model Context Protocol (MCP) executor."""

import json
from typing import Any

from tool_master.executors.base import BaseExecutor
from tool_master.schemas.tool import Tool, ToolResult


class MCPExecutor(BaseExecutor):
    """
    Executor for Model Context Protocol (MCP) format.

    Converts tools to MCP's tool schema and handles execution
    in the MCP-expected format with content blocks.

    MCP tool schema format:
        {
            "name": "tool_name",
            "description": "What the tool does",
            "inputSchema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }

    MCP result format:
        {
            "content": [{"type": "text", "text": "..."}],
            "isError": false
        }
    """

    def format_tool(self, tool: Tool) -> dict[str, Any]:
        """
        Convert a Tool to MCP tools format.

        Args:
            tool: The Tool to convert

        Returns:
            MCP tool definition with name, description, and inputSchema
        """
        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.to_json_schema(),
        }

    def format_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert multiple Tools to MCP format."""
        return [self.format_tool(tool) for tool in tools]

    async def execute(self, tool: Tool, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool and return the result."""
        errors = self.validate_arguments(tool, arguments)
        if errors:
            return ToolResult.fail("; ".join(errors))

        return await tool.execute(**arguments)

    def format_result(self, result: ToolResult) -> dict[str, Any]:
        """
        Format result for MCP CallToolResult format.

        MCP expects results as:
            {
                "content": [{"type": "text", "text": "..."}],
                "isError": false
            }

        Args:
            result: The ToolResult to format

        Returns:
            MCP-formatted result with content blocks and isError flag
        """
        if result.success:
            content = self._serialize_content(result.data)
            return {"content": content, "isError": False}

        return {
            "content": [{"type": "text", "text": result.error or "Unknown error"}],
            "isError": True,
        }

    def _serialize_content(self, data: Any) -> list[dict[str, Any]]:
        """
        Convert data to MCP content blocks.

        Args:
            data: The data to serialize

        Returns:
            List of MCP content blocks (currently only text type)
        """
        if data is None:
            return [{"type": "text", "text": ""}]

        if isinstance(data, str):
            return [{"type": "text", "text": data}]

        # JSON serialize other types
        return [{"type": "text", "text": json.dumps(data)}]

    def format_call_tool_result(
        self, result: ToolResult, structured: bool = False
    ) -> dict[str, Any]:
        """
        Format a complete MCP CallToolResult.

        This is the full response format for tools/call responses.

        Args:
            result: The ToolResult from execution
            structured: Whether to include structuredContent field

        Returns:
            Complete MCP CallToolResult
        """
        response = self.format_result(result)

        if structured and result.success and result.data is not None:
            # Add structuredContent for typed responses
            if not isinstance(result.data, str):
                response["structuredContent"] = result.data

        return response
