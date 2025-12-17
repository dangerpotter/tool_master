"""OpenAI function calling executor."""

from typing import Any

from tool_master.executors.base import BaseExecutor
from tool_master.schemas.tool import Tool, ToolResult


class OpenAIExecutor(BaseExecutor):
    """
    Executor for OpenAI function calling format.

    Converts tools to OpenAI's function calling schema and handles
    execution in the OpenAI-expected format.
    """

    def format_tool(self, tool: Tool) -> dict[str, Any]:
        """Convert a Tool to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.to_json_schema(),
            },
        }

    def format_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert multiple Tools to OpenAI format."""
        return [self.format_tool(tool) for tool in tools]

    async def execute(self, tool: Tool, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool and return the result."""
        errors = self.validate_arguments(tool, arguments)
        if errors:
            return ToolResult.fail("; ".join(errors))

        return await tool.execute(**arguments)

    def format_result(self, result: ToolResult) -> str:
        """Format result as string for OpenAI tool response."""
        if result.success:
            if isinstance(result.data, str):
                return result.data
            import json
            return json.dumps(result.data)
        return f"Error: {result.error}"

    def format_tool_response(self, tool_call_id: str, result: ToolResult) -> dict[str, Any]:
        """
        Format a complete tool response message for OpenAI.

        Args:
            tool_call_id: The ID from the original tool call
            result: The ToolResult from execution

        Returns:
            OpenAI tool response message
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": self.format_result(result),
        }
