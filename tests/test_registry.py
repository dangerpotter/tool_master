"""Tests for registry functionality."""

import pytest
from tool_master.schemas.tool import Tool, ToolParameter, ParameterType
from tool_master.registry import ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


@pytest.fixture
def sample_tools():
    tool1 = Tool(
        name="tool_one",
        description="First tool",
        parameters=[],
        category="category_a",
        tags=["tag1", "tag2"],
    )
    tool2 = Tool(
        name="tool_two",
        description="Second tool",
        parameters=[],
        category="category_a",
        tags=["tag2", "tag3"],
    )
    tool3 = Tool(
        name="tool_three",
        description="Third tool",
        parameters=[],
        category="category_b",
        tags=["tag1"],
    )
    return [tool1, tool2, tool3]


class TestToolRegistry:
    def test_register_tool(self, registry, sample_tools):
        registry.register(sample_tools[0])
        assert "tool_one" in registry
        assert len(registry) == 1

    def test_register_duplicate_raises(self, registry, sample_tools):
        registry.register(sample_tools[0])
        with pytest.raises(ValueError, match="already registered"):
            registry.register(sample_tools[0])

    def test_get_tool(self, registry, sample_tools):
        registry.register(sample_tools[0])
        tool = registry.get("tool_one")
        assert tool is not None
        assert tool.name == "tool_one"

    def test_get_nonexistent_returns_none(self, registry):
        assert registry.get("nonexistent") is None

    def test_unregister_tool(self, registry, sample_tools):
        registry.register(sample_tools[0])
        removed = registry.unregister("tool_one")
        assert removed is not None
        assert removed.name == "tool_one"
        assert "tool_one" not in registry

    def test_get_by_category(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        category_a_tools = registry.get_by_category("category_a")
        assert len(category_a_tools) == 2
        names = [t.name for t in category_a_tools]
        assert "tool_one" in names
        assert "tool_two" in names

    def test_get_by_tag(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        tag1_tools = registry.get_by_tag("tag1")
        assert len(tag1_tools) == 2
        names = [t.name for t in tag1_tools]
        assert "tool_one" in names
        assert "tool_three" in names

    def test_get_by_tags_any(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        tools = registry.get_by_tags(["tag1", "tag3"], match_all=False)
        assert len(tools) == 3  # All tools have at least one of these tags

    def test_get_by_tags_all(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        tools = registry.get_by_tags(["tag1", "tag2"], match_all=True)
        assert len(tools) == 1
        assert tools[0].name == "tool_one"

    def test_search_by_query(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        results = registry.search(query="first")
        assert len(results) == 1
        assert results[0].name == "tool_one"

    def test_search_by_category_and_tag(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        results = registry.search(category="category_a", tags=["tag2"])
        assert len(results) == 2

    def test_all_tools(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        all_tools = registry.all()
        assert len(all_tools) == 3

    def test_categories_list(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        categories = registry.categories()
        assert "category_a" in categories
        assert "category_b" in categories

    def test_tags_list(self, registry, sample_tools):
        for tool in sample_tools:
            registry.register(tool)

        tags = registry.tags_list()
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags
