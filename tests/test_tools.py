"""Tests for tool functionality."""

import pytest
from tool_master.schemas.tool import Tool, ToolParameter, ToolResult, ParameterType


class TestToolResult:
    def test_ok_result(self):
        result = ToolResult.ok({"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_fail_result(self):
        result = ToolResult.fail("Something went wrong")
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"


class TestTool:
    def test_tool_creation(self):
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(
                    name="input",
                    type=ParameterType.STRING,
                    description="Input string",
                ),
            ],
        )
        assert tool.name == "test_tool"
        assert len(tool.parameters) == 1

    def test_to_json_schema(self):
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(
                    name="required_param",
                    type=ParameterType.STRING,
                    description="A required parameter",
                    required=True,
                ),
                ToolParameter(
                    name="optional_param",
                    type=ParameterType.INTEGER,
                    description="An optional parameter",
                    required=False,
                ),
            ],
        )

        schema = tool.to_json_schema()
        assert schema["type"] == "object"
        assert "required_param" in schema["properties"]
        assert "optional_param" in schema["properties"]
        assert "required_param" in schema["required"]
        assert "optional_param" not in schema["required"]

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        def handler(x: int, y: int) -> int:
            return x + y

        tool = Tool(
            name="add",
            description="Add two numbers",
            parameters=[
                ToolParameter(name="x", type=ParameterType.INTEGER, description="First number"),
                ToolParameter(name="y", type=ParameterType.INTEGER, description="Second number"),
            ],
        ).set_handler(handler)

        result = await tool.execute(x=5, y=3)
        assert result.success is True
        assert result.data == 8

    @pytest.mark.asyncio
    async def test_tool_missing_handler(self):
        tool = Tool(
            name="no_handler",
            description="Tool without handler",
            parameters=[],
        )

        result = await tool.execute()
        assert result.success is False
        assert "No handler" in result.error

    @pytest.mark.asyncio
    async def test_tool_missing_required_param(self):
        def handler(required: str) -> str:
            return required

        tool = Tool(
            name="test",
            description="Test",
            parameters=[
                ToolParameter(
                    name="required",
                    type=ParameterType.STRING,
                    description="Required param",
                    required=True,
                ),
            ],
        ).set_handler(handler)

        result = await tool.execute()
        assert result.success is False
        assert "required" in result.error.lower()
