"""Tests for executor functionality."""

import pytest
from tool_master.schemas.tool import Tool, ToolParameter, ToolResult, ParameterType
from tool_master.executors import OpenAIExecutor, AnthropicExecutor, GenericExecutor


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


class TestOpenAIExecutor:
    def test_format_tool(self, sample_tool):
        executor = OpenAIExecutor()
        formatted = executor.format_tool(sample_tool)

        assert formatted["type"] == "function"
        assert formatted["function"]["name"] == "repeat_message"
        assert "parameters" in formatted["function"]

    def test_format_tools(self, sample_tool):
        executor = OpenAIExecutor()
        formatted = executor.format_tools([sample_tool])

        assert len(formatted) == 1
        assert formatted[0]["function"]["name"] == "repeat_message"

    @pytest.mark.asyncio
    async def test_execute(self, sample_tool):
        executor = OpenAIExecutor()
        result = await executor.execute(sample_tool, {"message": "hi", "count": 3})

        assert result.success is True
        assert result.data == "hihihi"

    def test_format_result_success(self):
        executor = OpenAIExecutor()
        result = ToolResult.ok({"data": "test"})
        formatted = executor.format_result(result)

        assert '{"data": "test"}' in formatted

    def test_format_result_error(self):
        executor = OpenAIExecutor()
        result = ToolResult.fail("Something broke")
        formatted = executor.format_result(result)

        assert "Error: Something broke" == formatted


class TestAnthropicExecutor:
    def test_format_tool(self, sample_tool):
        executor = AnthropicExecutor()
        formatted = executor.format_tool(sample_tool)

        assert formatted["name"] == "repeat_message"
        assert "input_schema" in formatted
        assert formatted["input_schema"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_execute(self, sample_tool):
        executor = AnthropicExecutor()
        result = await executor.execute(sample_tool, {"message": "test"})

        assert result.success is True
        assert result.data == "test"

    def test_format_tool_response(self):
        executor = AnthropicExecutor()
        result = ToolResult.ok("success data")
        response = executor.format_tool_response("tool_123", result)

        assert response["type"] == "tool_result"
        assert response["tool_use_id"] == "tool_123"
        assert response["content"] == "success data"


class TestGenericExecutor:
    def test_format_tool_includes_metadata(self, sample_tool):
        executor = GenericExecutor()
        formatted = executor.format_tool(sample_tool)

        assert formatted["name"] == "repeat_message"
        assert "metadata" in formatted
        assert formatted["metadata"]["category"] == "text"
        assert "utility" in formatted["metadata"]["tags"]

    def test_format_result_as_dict(self):
        executor = GenericExecutor()
        result = ToolResult.ok({"key": "value"})
        formatted = executor.format_result(result)

        assert formatted["success"] is True
        assert formatted["data"] == {"key": "value"}
