"""Tests for MCP executor functionality."""

import pytest
from tool_master.schemas.tool import Tool, ToolParameter, ToolResult, ParameterType
from tool_master.executors import MCPExecutor


@pytest.fixture
def sample_tool():
    def handler(message: str, count: int = 1) -> str:
        return message * count

    return Tool(
        name="repeat_message",
        description="Repeat a message multiple times",
        parameters=[
            ToolParameter(
                name="message",
                type=ParameterType.STRING,
                description="The message to repeat",
                required=True,
            ),
            ToolParameter(
                name="count",
                type=ParameterType.INTEGER,
                description="Number of times to repeat",
                required=False,
                default=1,
            ),
        ],
        category="text",
        tags=["string", "utility"],
    ).set_handler(handler)


@pytest.fixture
def dict_returning_tool():
    def handler(name: str) -> dict:
        return {"greeting": f"Hello, {name}!", "name": name}

    return Tool(
        name="greet",
        description="Generate a greeting",
        parameters=[
            ToolParameter(
                name="name",
                type=ParameterType.STRING,
                description="Name to greet",
                required=True,
            ),
        ],
    ).set_handler(handler)


class TestMCPExecutor:
    def test_format_tool(self, sample_tool):
        executor = MCPExecutor()
        formatted = executor.format_tool(sample_tool)

        assert formatted["name"] == "repeat_message"
        assert formatted["description"] == "Repeat a message multiple times"
        assert "inputSchema" in formatted
        assert formatted["inputSchema"]["type"] == "object"
        assert "message" in formatted["inputSchema"]["properties"]
        assert "count" in formatted["inputSchema"]["properties"]
        assert "message" in formatted["inputSchema"]["required"]

    def test_format_tool_uses_input_schema_not_parameters(self, sample_tool):
        """MCP uses 'inputSchema' not 'parameters' or 'input_schema'."""
        executor = MCPExecutor()
        formatted = executor.format_tool(sample_tool)

        assert "inputSchema" in formatted
        assert "parameters" not in formatted
        assert "input_schema" not in formatted

    def test_format_tools(self, sample_tool, dict_returning_tool):
        executor = MCPExecutor()
        formatted = executor.format_tools([sample_tool, dict_returning_tool])

        assert len(formatted) == 2
        assert formatted[0]["name"] == "repeat_message"
        assert formatted[1]["name"] == "greet"

    @pytest.mark.asyncio
    async def test_execute_success(self, sample_tool):
        executor = MCPExecutor()
        result = await executor.execute(sample_tool, {"message": "hi", "count": 3})

        assert result.success is True
        assert result.data == "hihihi"

    @pytest.mark.asyncio
    async def test_execute_with_default(self, sample_tool):
        executor = MCPExecutor()
        result = await executor.execute(sample_tool, {"message": "test"})

        assert result.success is True
        assert result.data == "test"

    @pytest.mark.asyncio
    async def test_execute_missing_required(self, sample_tool):
        executor = MCPExecutor()
        result = await executor.execute(sample_tool, {"count": 5})

        assert result.success is False
        assert "Missing required parameter" in result.error

    @pytest.mark.asyncio
    async def test_execute_unknown_parameter(self, sample_tool):
        executor = MCPExecutor()
        result = await executor.execute(
            sample_tool, {"message": "hi", "unknown": "value"}
        )

        assert result.success is False
        assert "Unknown parameter" in result.error

    def test_format_result_success_string(self):
        executor = MCPExecutor()
        result = ToolResult.ok("Hello, world!")
        formatted = executor.format_result(result)

        assert formatted["isError"] is False
        assert len(formatted["content"]) == 1
        assert formatted["content"][0]["type"] == "text"
        assert formatted["content"][0]["text"] == "Hello, world!"

    def test_format_result_success_dict(self):
        executor = MCPExecutor()
        result = ToolResult.ok({"key": "value", "count": 42})
        formatted = executor.format_result(result)

        assert formatted["isError"] is False
        assert len(formatted["content"]) == 1
        assert formatted["content"][0]["type"] == "text"
        assert '{"key": "value", "count": 42}' in formatted["content"][0]["text"]

    def test_format_result_success_none(self):
        executor = MCPExecutor()
        result = ToolResult.ok(None)
        formatted = executor.format_result(result)

        assert formatted["isError"] is False
        assert formatted["content"][0]["text"] == ""

    def test_format_result_error(self):
        executor = MCPExecutor()
        result = ToolResult.fail("Something went wrong")
        formatted = executor.format_result(result)

        assert formatted["isError"] is True
        assert len(formatted["content"]) == 1
        assert formatted["content"][0]["type"] == "text"
        assert formatted["content"][0]["text"] == "Something went wrong"

    def test_format_result_error_none(self):
        executor = MCPExecutor()
        result = ToolResult(success=False, error=None)
        formatted = executor.format_result(result)

        assert formatted["isError"] is True
        assert formatted["content"][0]["text"] == "Unknown error"

    def test_format_call_tool_result_basic(self):
        executor = MCPExecutor()
        result = ToolResult.ok("test data")
        formatted = executor.format_call_tool_result(result)

        assert formatted["isError"] is False
        assert formatted["content"][0]["text"] == "test data"

    def test_format_call_tool_result_structured(self):
        executor = MCPExecutor()
        data = {"temperature": 72, "unit": "fahrenheit"}
        result = ToolResult.ok(data)
        formatted = executor.format_call_tool_result(result, structured=True)

        assert formatted["isError"] is False
        assert formatted["structuredContent"] == data

    def test_format_call_tool_result_structured_string_no_structured_content(self):
        """String results should not have structuredContent even with structured=True."""
        executor = MCPExecutor()
        result = ToolResult.ok("plain string")
        formatted = executor.format_call_tool_result(result, structured=True)

        assert formatted["isError"] is False
        assert "structuredContent" not in formatted
