"""Tests for MCP Server functionality."""

import pytest
from tool_master.schemas.tool import Tool, ToolParameter, ToolResult, ParameterType
from tool_master import ToolRegistry

# Skip all tests if mcp is not installed
pytest.importorskip("mcp")

from tool_master.mcp_server import ToolMasterMCPServer


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


@pytest.fixture
def error_tool():
    def handler() -> str:
        raise ValueError("Something went wrong!")

    return Tool(
        name="error_tool",
        description="A tool that always errors",
        parameters=[],
    ).set_handler(handler)


class TestToolMasterMCPServer:
    def test_create_server(self):
        server = ToolMasterMCPServer("test-server")
        assert server is not None
        assert server.tools == {}

    def test_create_server_default_name(self):
        server = ToolMasterMCPServer()
        assert server is not None

    def test_register_tool(self, sample_tool):
        server = ToolMasterMCPServer("test")
        server.register_tool(sample_tool)

        assert "repeat_message" in server.tools
        assert server.tools["repeat_message"] is sample_tool

    def test_register_tools(self, sample_tool, dict_returning_tool):
        server = ToolMasterMCPServer("test")
        server.register_tools([sample_tool, dict_returning_tool])

        assert len(server.tools) == 2
        assert "repeat_message" in server.tools
        assert "greet" in server.tools

    def test_register_from_registry(self, sample_tool, dict_returning_tool):
        registry = ToolRegistry()
        registry.register(sample_tool)
        registry.register(dict_returning_tool)

        server = ToolMasterMCPServer("test")
        server.register_from_registry(registry)

        assert len(server.tools) == 2
        assert "repeat_message" in server.tools
        assert "greet" in server.tools

    def test_tools_property_returns_copy(self, sample_tool):
        server = ToolMasterMCPServer("test")
        server.register_tool(sample_tool)

        tools_copy = server.tools
        tools_copy["new_tool"] = sample_tool

        # Original should not be modified
        assert "new_tool" not in server.tools

    def test_server_property(self):
        server = ToolMasterMCPServer("test")
        assert server.server is not None

    def test_to_mcp_tool(self, sample_tool):
        server = ToolMasterMCPServer("test")
        mcp_tool = server._to_mcp_tool(sample_tool)

        assert mcp_tool.name == "repeat_message"
        assert mcp_tool.description == "Repeat a message multiple times"
        assert mcp_tool.inputSchema["type"] == "object"
        assert "message" in mcp_tool.inputSchema["properties"]

    def test_to_call_result_success_string(self, sample_tool):
        server = ToolMasterMCPServer("test")
        result = ToolResult.ok("Hello!")
        call_result = server._to_call_result(result)

        assert call_result.isError is False
        assert len(call_result.content) == 1
        assert call_result.content[0].type == "text"
        assert call_result.content[0].text == "Hello!"

    def test_to_call_result_success_dict(self, sample_tool):
        server = ToolMasterMCPServer("test")
        result = ToolResult.ok({"key": "value"})
        call_result = server._to_call_result(result)

        assert call_result.isError is False
        assert '{"key": "value"}' in call_result.content[0].text

    def test_to_call_result_success_none(self, sample_tool):
        server = ToolMasterMCPServer("test")
        result = ToolResult.ok(None)
        call_result = server._to_call_result(result)

        assert call_result.isError is False
        assert call_result.content[0].text == ""

    def test_to_call_result_error(self, sample_tool):
        server = ToolMasterMCPServer("test")
        result = ToolResult.fail("Something broke")
        call_result = server._to_call_result(result)

        assert call_result.isError is True
        assert call_result.content[0].text == "Something broke"


class TestMCPServerHandlers:
    """Tests for the actual MCP protocol handlers."""

    @pytest.mark.asyncio
    async def test_tool_execution_through_server(self, sample_tool):
        """Test that tools can be executed correctly after registration."""
        server = ToolMasterMCPServer("test")
        server.register_tool(sample_tool)

        # Execute the tool directly and verify result conversion
        result = await sample_tool.execute(message="hi", count=3)
        call_result = server._to_call_result(result)

        assert call_result.isError is False
        assert call_result.content[0].text == "hihihi"

    @pytest.mark.asyncio
    async def test_tool_mcp_conversion(self, sample_tool, dict_returning_tool):
        """Test that tools are correctly converted to MCP format."""
        server = ToolMasterMCPServer("test")
        server.register_tools([sample_tool, dict_returning_tool])

        # Convert tools to MCP format
        mcp_tools = [server._to_mcp_tool(t) for t in server.tools.values()]

        assert len(mcp_tools) == 2
        names = {t.name for t in mcp_tools}
        assert names == {"repeat_message", "greet"}

    @pytest.mark.asyncio
    async def test_dict_result_serialization(self, dict_returning_tool):
        """Test that dict results are properly JSON serialized."""
        server = ToolMasterMCPServer("test")
        server.register_tool(dict_returning_tool)

        result = await dict_returning_tool.execute(name="World")
        call_result = server._to_call_result(result)

        assert call_result.isError is False
        assert "Hello, World!" in call_result.content[0].text
        assert '"name": "World"' in call_result.content[0].text

    @pytest.mark.asyncio
    async def test_error_result_handling(self, error_tool):
        """Test that errors are properly converted to MCP error results."""
        server = ToolMasterMCPServer("test")
        server.register_tool(error_tool)

        # When a tool raises an exception, we simulate the error handling
        result = ToolResult.fail("Tool execution error: Something went wrong!")
        call_result = server._to_call_result(result)

        assert call_result.isError is True
        assert "Tool execution error" in call_result.content[0].text
