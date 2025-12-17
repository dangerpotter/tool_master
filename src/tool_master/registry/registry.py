"""Central tool registry for managing tools."""

from typing import Callable, Optional

from tool_master.schemas.tool import Tool


class ToolRegistry:
    """
    Central registry for discovering and managing tools.

    The registry provides:
    - Tool registration and storage
    - Lookup by name, category, or tags
    - Bulk operations for loading tools into executors
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._categories: dict[str, set[str]] = {}
        self._tags: dict[str, set[str]] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: The Tool to register

        Raises:
            ValueError: If a tool with the same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

        # Index by category
        if tool.category:
            if tool.category not in self._categories:
                self._categories[tool.category] = set()
            self._categories[tool.category].add(tool.name)

        # Index by tags
        for tag in tool.tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(tool.name)

    def unregister(self, name: str) -> Optional[Tool]:
        """
        Remove a tool from the registry.

        Args:
            name: Name of the tool to remove

        Returns:
            The removed Tool, or None if not found
        """
        tool = self._tools.pop(name, None)
        if tool:
            # Remove from category index
            if tool.category and tool.category in self._categories:
                self._categories[tool.category].discard(name)

            # Remove from tag index
            for tag in tool.tags:
                if tag in self._tags:
                    self._tags[tag].discard(name)

        return tool

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: The tool name

        Returns:
            The Tool if found, None otherwise
        """
        return self._tools.get(name)

    def get_by_category(self, category: str) -> list[Tool]:
        """
        Get all tools in a category.

        Args:
            category: The category name

        Returns:
            List of Tools in the category
        """
        names = self._categories.get(category, set())
        return [self._tools[name] for name in names if name in self._tools]

    def get_by_tag(self, tag: str) -> list[Tool]:
        """
        Get all tools with a specific tag.

        Args:
            tag: The tag to search for

        Returns:
            List of Tools with the tag
        """
        names = self._tags.get(tag, set())
        return [self._tools[name] for name in names if name in self._tools]

    def get_by_tags(self, tags: list[str], match_all: bool = False) -> list[Tool]:
        """
        Get tools matching multiple tags.

        Args:
            tags: List of tags to match
            match_all: If True, tools must have ALL tags; if False, ANY tag

        Returns:
            List of matching Tools
        """
        if not tags:
            return []

        tag_sets = [self._tags.get(tag, set()) for tag in tags]

        if match_all:
            # Intersection - tools must have all tags
            matching_names = set.intersection(*tag_sets) if tag_sets else set()
        else:
            # Union - tools can have any tag
            matching_names = set.union(*tag_sets) if tag_sets else set()

        return [self._tools[name] for name in matching_names if name in self._tools]

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[Tool]:
        """
        Search for tools with multiple criteria.

        Args:
            query: Text to search in name/description
            category: Category filter
            tags: Tags filter (matches any)

        Returns:
            List of matching Tools
        """
        results = list(self._tools.values())

        if category:
            results = [t for t in results if t.category == category]

        if tags:
            tag_names = set()
            for tag in tags:
                tag_names.update(self._tags.get(tag, set()))
            results = [t for t in results if t.name in tag_names]

        if query:
            query_lower = query.lower()
            results = [
                t for t in results
                if query_lower in t.name.lower() or query_lower in t.description.lower()
            ]

        return results

    def all(self) -> list[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def categories(self) -> list[str]:
        """Get all categories with at least one tool."""
        return [cat for cat, tools in self._categories.items() if tools]

    def tags_list(self) -> list[str]:
        """Get all tags with at least one tool."""
        return [tag for tag, tools in self._tags.items() if tools]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Global default registry
_default_registry: Optional[ToolRegistry] = None


def get_default_registry() -> ToolRegistry:
    """Get or create the default global registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def register_tool(tool: Tool) -> Tool:
    """Register a tool in the default registry."""
    get_default_registry().register(tool)
    return tool


def tool(
    name: str,
    description: str,
    category: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Callable[[Callable], Tool]:
    """
    Decorator to create and register a tool from a function.

    Usage:
        @tool("my_tool", "Does something useful", category="utilities")
        def my_tool(param1: str, param2: int = 10):
            return f"Result: {param1}, {param2}"
    """
    def decorator(func: Callable) -> Tool:
        from tool_master.utils.introspection import tool_from_function

        t = tool_from_function(
            func,
            name=name,
            description=description,
            category=category,
            tags=tags or [],
        )
        register_tool(t)
        return t

    return decorator
