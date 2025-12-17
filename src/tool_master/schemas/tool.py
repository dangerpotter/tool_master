"""Core tool schema definitions."""

from enum import Enum
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field


class ParameterType(str, Enum):
    """Supported parameter types for tool inputs."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolParameter(BaseModel):
    """Definition of a single tool parameter."""

    name: str = Field(..., description="Parameter name")
    type: ParameterType = Field(..., description="Parameter type")
    description: str = Field(..., description="Description of the parameter")
    required: bool = Field(default=True, description="Whether the parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if not required")
    enum: Optional[list[Any]] = Field(default=None, description="Allowed values (for enums)")
    items_type: Optional[ParameterType] = Field(default=None, description="Type of array items (if type is array)")

    model_config = {"extra": "allow"}


class ToolResult(BaseModel):
    """Result returned from tool execution."""

    success: bool = Field(..., description="Whether the tool executed successfully")
    data: Optional[Any] = Field(default=None, description="Result data on success")
    error: Optional[str] = Field(default=None, description="Error message on failure")

    @classmethod
    def ok(cls, data: Any) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error=error)


class Tool(BaseModel):
    """
    Core tool definition.

    This is the canonical format for all tools in the Tool Master library.
    Tools can be converted to various LLM-specific formats via executors.
    """

    name: str = Field(..., description="Unique tool name (snake_case)")
    description: str = Field(..., description="Clear description of what the tool does")
    parameters: list[ToolParameter] = Field(default_factory=list, description="Tool parameters")

    # Metadata
    category: Optional[str] = Field(default=None, description="Tool category (e.g., 'productivity', 'data')")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    version: str = Field(default="1.0.0", description="Tool version")

    # The actual implementation function (not serialized)
    _handler: Optional[Callable[..., Any]] = None

    model_config = {"extra": "allow"}

    def set_handler(self, handler: Callable[..., Any]) -> "Tool":
        """Set the handler function for this tool."""
        self._handler = handler
        return self

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given parameters."""
        if self._handler is None:
            return ToolResult.fail(f"No handler set for tool '{self.name}'")

        try:
            # Validate required parameters
            for param in self.parameters:
                if param.required and param.name not in kwargs:
                    if param.default is None:
                        return ToolResult.fail(f"Missing required parameter: {param.name}")
                    kwargs[param.name] = param.default

            # Execute handler
            result = self._handler(**kwargs)

            # Handle async handlers
            if hasattr(result, "__await__"):
                result = await result

            return ToolResult.ok(result)

        except Exception as e:
            return ToolResult.fail(str(e))

    def to_json_schema(self) -> dict[str, Any]:
        """Convert tool parameters to JSON Schema format."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type.value,
                "description": param.description,
            }

            if param.enum:
                prop["enum"] = param.enum

            if param.type == ParameterType.ARRAY and param.items_type:
                prop["items"] = {"type": param.items_type.value}

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
