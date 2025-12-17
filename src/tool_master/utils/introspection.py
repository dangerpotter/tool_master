"""Introspection utilities for creating tools from functions."""

import inspect
from typing import Any, Callable, Optional, get_type_hints

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter


def python_type_to_param_type(python_type: Any) -> ParameterType:
    """Convert a Python type annotation to ParameterType."""
    # Handle Optional types
    origin = getattr(python_type, "__origin__", None)
    if origin is type(None):
        return ParameterType.STRING

    # Handle Union types (including Optional)
    if origin is type(None) or str(origin) == "typing.Union":
        args = getattr(python_type, "__args__", ())
        # Get the non-None type from Optional
        for arg in args:
            if arg is not type(None):
                return python_type_to_param_type(arg)
        return ParameterType.STRING

    # Handle list/List types
    if origin is list or str(origin) == "typing.List":
        return ParameterType.ARRAY

    # Handle dict/Dict types
    if origin is dict or str(origin) == "typing.Dict":
        return ParameterType.OBJECT

    # Direct type mappings
    type_map = {
        str: ParameterType.STRING,
        int: ParameterType.INTEGER,
        float: ParameterType.NUMBER,
        bool: ParameterType.BOOLEAN,
        list: ParameterType.ARRAY,
        dict: ParameterType.OBJECT,
    }

    return type_map.get(python_type, ParameterType.STRING)


def tool_from_function(
    func: Callable,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Tool:
    """
    Create a Tool from a Python function using introspection.

    Args:
        func: The function to convert
        name: Override the tool name (defaults to function name)
        description: Override description (defaults to docstring)
        category: Tool category
        tags: Tool tags

    Returns:
        A Tool with the function as its handler
    """
    # Get function signature
    sig = inspect.signature(func)

    # Try to get type hints
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    # Build parameters from signature
    parameters: list[ToolParameter] = []

    for param_name, param in sig.parameters.items():
        # Skip *args and **kwargs
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        # Determine type
        param_type = hints.get(param_name, str)
        tool_param_type = python_type_to_param_type(param_type)

        # Check if required (has no default)
        has_default = param.default is not inspect.Parameter.empty
        default_value = param.default if has_default else None

        # Get description from docstring if available
        param_description = f"Parameter: {param_name}"
        if func.__doc__:
            # Try to extract parameter description from docstring
            doc_lines = func.__doc__.split("\n")
            for i, line in enumerate(doc_lines):
                if f":param {param_name}:" in line or f"{param_name}:" in line:
                    # Extract the description part
                    parts = line.split(":", 2)
                    if len(parts) >= 2:
                        param_description = parts[-1].strip()
                    break

        parameters.append(
            ToolParameter(
                name=param_name,
                type=tool_param_type,
                description=param_description,
                required=not has_default,
                default=default_value if has_default else None,
            )
        )

    # Create the tool
    tool = Tool(
        name=name or func.__name__,
        description=description or func.__doc__ or f"Function: {func.__name__}",
        parameters=parameters,
        category=category,
        tags=tags or [],
    )

    # Set the handler
    tool.set_handler(func)

    return tool
