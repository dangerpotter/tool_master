"""Anthropic Claude tools executor."""

from typing import Any

from tool_master.executors.base import BaseExecutor
from tool_master.schemas.tool import Tool, ToolResult


class AnthropicExecutor(BaseExecutor):
    """
    Executor for Anthropic Claude tools format.

    Converts tools to Anthropic's tool use schema and handles
    execution in the Claude-expected format.
    """

    def format_tool(self, tool: Tool) -> dict[str, Any]:
        """Convert a Tool to Anthropic tools format."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.to_json_schema(),
        }

    def format_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert multiple Tools to Anthropic format."""
        return [self.format_tool(tool) for tool in tools]

    async def execute(self, tool: Tool, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool and return the result."""
        errors = self.validate_arguments(tool, arguments)
        if errors:
            return ToolResult.fail("; ".join(errors))

        return await tool.execute(**arguments)

    def format_result(self, result: ToolResult) -> Any:
        """Format result for Anthropic tool response."""
        if result.success:
            return result.data
        return {"error": result.error}

    def format_tool_response(self, tool_use_id: str, result: ToolResult) -> dict[str, Any]:
        """
        Format a complete tool result message for Anthropic.

        Args:
            tool_use_id: The ID from the original tool_use block
            result: The ToolResult from execution

        Returns:
            Anthropic tool_result content block
        """
        content: dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
        }

        if result.success:
            # Anthropic expects content as string or list of content blocks
            if isinstance(result.data, str):
                content["content"] = result.data
            else:
                import json
                content["content"] = json.dumps(result.data)
        else:
            content["is_error"] = True
            content["content"] = result.error or "Unknown error"

        return content
