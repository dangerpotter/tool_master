"""Basic usage example for Tool Master."""

import asyncio
from tool_master import Tool, ToolParameter, ToolRegistry
from tool_master.schemas.tool import ParameterType
from tool_master.executors import OpenAIExecutor, AnthropicExecutor, GenericExecutor
from tool_master.tools import get_current_time, format_date
from tool_master.registry.registry import tool


# Example 1: Using built-in tools
async def example_builtin_tools():
    """Demonstrate using built-in tools."""
    print("=== Built-in Tools ===\n")

    # Execute the get_current_time tool
    result = await get_current_time.execute(timezone_name="America/New_York")
    print(f"Current time result: {result}\n")

    # Execute the format_date tool
    result = await format_date.execute(
        date_string="2024-03-15",
        output_format="%A, %B %d, %Y"
    )
    print(f"Formatted date: {result}\n")


# Example 2: Creating a custom tool
async def example_custom_tool():
    """Demonstrate creating custom tools."""
    print("=== Custom Tool ===\n")

    # Define a custom tool
    def calculate_area(length: float, width: float) -> float:
        """Calculate the area of a rectangle."""
        return length * width

    area_tool = Tool(
        name="calculate_area",
        description="Calculate the area of a rectangle given length and width",
        parameters=[
            ToolParameter(
                name="length",
                type=ParameterType.NUMBER,
                description="The length of the rectangle",
                required=True,
            ),
            ToolParameter(
                name="width",
                type=ParameterType.NUMBER,
                description="The width of the rectangle",
                required=True,
            ),
        ],
        category="math",
        tags=["geometry", "calculation"],
    ).set_handler(calculate_area)

    # Execute the tool
    result = await area_tool.execute(length=10.5, width=5.0)
    print(f"Area calculation: {result}\n")


# Example 3: Using the @tool decorator
async def example_decorator():
    """Demonstrate using the @tool decorator."""
    print("=== Tool Decorator ===\n")

    @tool("greet_user", "Generate a greeting message", category="utility")
    def greet_user(name: str, formal: bool = False) -> str:
        """Generate a greeting for the user."""
        if formal:
            return f"Good day, {name}. How may I assist you?"
        return f"Hey {name}! How's it going?"

    # The decorator returns a Tool, so we can execute it
    result = await greet_user.execute(name="Alice", formal=True)
    print(f"Formal greeting: {result}\n")

    result = await greet_user.execute(name="Bob")
    print(f"Casual greeting: {result}\n")


# Example 4: Using executors for different platforms
async def example_executors():
    """Demonstrate using executors for different LLM platforms."""
    print("=== Executors ===\n")

    # Create executors
    openai_executor = OpenAIExecutor()
    anthropic_executor = AnthropicExecutor()
    generic_executor = GenericExecutor()

    # Format the same tool for different platforms
    tools = [get_current_time, format_date]

    print("OpenAI format:")
    openai_tools = openai_executor.format_tools(tools)
    for t in openai_tools:
        print(f"  - {t['function']['name']}: {t['type']}")

    print("\nAnthropic format:")
    anthropic_tools = anthropic_executor.format_tools(tools)
    for t in anthropic_tools:
        print(f"  - {t['name']}")

    print("\nGeneric format:")
    generic_tools = generic_executor.format_tools(tools)
    for t in generic_tools:
        print(f"  - {t['name']} (v{t['metadata']['version']})")

    # Execute via executor
    print("\nExecuting via OpenAI executor:")
    result = await openai_executor.execute(
        get_current_time,
        {"timezone_name": "UTC"}
    )
    print(f"  Result: {openai_executor.format_result(result)[:50]}...")


# Example 5: Using the registry
async def example_registry():
    """Demonstrate using the tool registry."""
    print("\n=== Tool Registry ===\n")

    # Create a registry
    registry = ToolRegistry()

    # Register tools
    registry.register(get_current_time)
    registry.register(format_date)

    # Create and register a custom tool
    def reverse_string(text: str) -> str:
        return text[::-1]

    string_tool = Tool(
        name="reverse_string",
        description="Reverse a string",
        parameters=[
            ToolParameter(
                name="text",
                type=ParameterType.STRING,
                description="Text to reverse",
                required=True,
            ),
        ],
        category="text",
        tags=["string", "utility"],
    ).set_handler(reverse_string)

    registry.register(string_tool)

    # Query the registry
    print(f"Total tools: {len(registry)}")
    print(f"Categories: {registry.categories()}")
    print(f"All tags: {registry.tags_list()}")

    # Get tools by category
    datetime_tools = registry.get_by_category("datetime")
    print(f"\nDatetime tools: {[t.name for t in datetime_tools]}")

    # Search tools
    utility_tools = registry.get_by_tag("utility")
    print(f"Utility tools: {[t.name for t in utility_tools]}")


async def main():
    """Run all examples."""
    await example_builtin_tools()
    await example_custom_tool()
    await example_decorator()
    await example_executors()
    await example_registry()


if __name__ == "__main__":
    asyncio.run(main())
