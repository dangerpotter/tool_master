"""Generic executor for simple use cases."""

from typing import Any

from tool_master.executors.base import BaseExecutor
from tool_master.schemas.tool import Tool, ToolResult


class GenericExecutor(BaseExecutor):
    """
    Generic executor for platform-agnostic tool execution.

    Useful for testing, local development, or custom integrations
    that don't need platform-specific formatting.
    """

    def format_tool(self, tool: Tool) -> dict[str, Any]:
        """Convert a Tool to generic JSON format."""
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.to_json_schema(),
            "metadata": {
                "category": tool.category,
                "tags": tool.tags,
                "version": tool.version,
            },
        }

    def format_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert multiple Tools to generic format."""
        return [self.format_tool(tool) for tool in tools]

    async def execute(self, tool: Tool, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool and return the result."""
        errors = self.validate_arguments(tool, arguments)
        if errors:
            return ToolResult.fail("; ".join(errors))

        return await tool.execute(**arguments)

    def format_result(self, result: ToolResult) -> dict[str, Any]:
        """Format result as standard dictionary."""
        return result.model_dump()
