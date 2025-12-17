"""Base executor interface."""

from abc import ABC, abstractmethod
from typing import Any

from tool_master.schemas.tool import Tool, ToolResult


class BaseExecutor(ABC):
    """
    Abstract base class for tool executors.

    Executors are responsible for:
    1. Converting Tool definitions to platform-specific formats
    2. Executing tools and returning results
    3. Handling platform-specific error formats
    """

    @abstractmethod
    def format_tool(self, tool: Tool) -> dict[str, Any]:
        """
        Convert a Tool to the platform-specific schema format.

        Args:
            tool: The Tool to convert

        Returns:
            Platform-specific tool definition (e.g., OpenAI function schema)
        """
        pass

    @abstractmethod
    def format_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """
        Convert multiple Tools to platform-specific format.

        Args:
            tools: List of Tools to convert

        Returns:
            List of platform-specific tool definitions
        """
        pass

    @abstractmethod
    async def execute(self, tool: Tool, arguments: dict[str, Any]) -> ToolResult:
        """
        Execute a tool with the given arguments.

        Args:
            tool: The Tool to execute
            arguments: The arguments to pass to the tool

        Returns:
            ToolResult with success/failure and data/error
        """
        pass

    @abstractmethod
    def format_result(self, result: ToolResult) -> Any:
        """
        Format a ToolResult for the platform.

        Args:
            result: The ToolResult to format

        Returns:
            Platform-specific result format
        """
        pass

    def validate_arguments(self, tool: Tool, arguments: dict[str, Any]) -> list[str]:
        """
        Validate arguments against tool schema.

        Args:
            tool: The Tool definition
            arguments: The arguments to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        for param in tool.parameters:
            if param.required and param.name not in arguments:
                errors.append(f"Missing required parameter: {param.name}")

        # Check for unknown parameters
        known_params = {p.name for p in tool.parameters}
        for arg_name in arguments:
            if arg_name not in known_params:
                errors.append(f"Unknown parameter: {arg_name}")

        return errors
