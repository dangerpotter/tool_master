# Tool Master

A master library of reusable LLM tools with pluggable executors for drag-and-drop integration across agent and chatbot projects.

## Project Vision

- **Centralized Tool Library**: Single source of truth for all LLM tools
- **Multi-Ecosystem Support**: Tools work across OpenAI, Anthropic, LangChain, MCP, and custom platforms
- **Executor Abstraction**: Pluggable executors adapt tools to any target system/format
- **Rapid Integration**: Pull tools and match them with the correct executor for any project

## Project Structure

```
Tool_Master/
├── .claude/                     # Claude Code configuration
├── src/tool_master/
│   ├── __init__.py             # Package exports
│   ├── schemas/                # Core data models
│   │   ├── __init__.py
│   │   └── tool.py             # Tool, ToolParameter, ToolResult
│   ├── executors/              # Platform-specific executors
│   │   ├── __init__.py
│   │   ├── base.py             # BaseExecutor ABC
│   │   ├── openai.py           # OpenAI function calling
│   │   ├── anthropic.py        # Anthropic Claude tools
│   │   ├── generic.py          # Platform-agnostic executor
│   │   └── mcp.py              # Model Context Protocol executor
│   ├── mcp_server/             # MCP Server integration
│   │   ├── __init__.py
│   │   └── server.py           # ToolMasterMCPServer class
│   ├── providers/              # Credentials providers for OAuth tools
│   │   ├── __init__.py         # GoogleCredentialsProvider Protocol
│   │   └── google.py           # SimpleGoogleCredentials implementation
│   ├── registry/               # Tool discovery and management
│   │   ├── __init__.py
│   │   └── registry.py         # ToolRegistry, @tool decorator
│   ├── tools/                  # Built-in tool implementations
│   │   ├── __init__.py
│   │   ├── datetime_tools.py   # Date/time tools (5)
│   │   ├── dice_tools.py       # Dice rolling (1)
│   │   ├── weather_tools.py    # Weather API (11)
│   │   ├── wikipedia_tools.py  # Wikipedia (3)
│   │   ├── finance_tools.py    # Stock/finance (11)
│   │   ├── currency_tools.py   # Currency exchange (5)
│   │   ├── dictionary_tools.py # Dictionary/thesaurus (5)
│   │   ├── translation_tools.py # Translation (3)
│   │   ├── geocoding_tools.py  # Geocoding/IP lookup (4)
│   │   ├── url_tools.py        # URL metadata/screenshots (4)
│   │   ├── text_analysis_tools.py # Sentiment/NLP (5)
│   │   ├── news_tools.py       # News API (3)
│   │   ├── file_tools.py       # File formats (18)
│   │   └── google/             # Google API tools (OAuth required)
│   │       ├── __init__.py     # Factory function exports
│   │       ├── calendar_tools.py   # Calendar schemas + factory
│   │       ├── calendar_impl.py    # Calendar API implementation
│   │       ├── sheets_tools.py     # Sheets schemas + factory
│   │       ├── _sheets_utils.py    # Shared sheets utilities
│   │       ├── sheets_core.py      # Core CRUD operations
│   │       ├── sheets_structure.py # Rows, columns, tabs
│   │       ├── sheets_formatting.py # Text, colors, borders
│   │       ├── sheets_charts.py    # Charts, pivot tables
│   │       ├── sheets_filters.py   # Filters, validation
│   │       ├── sheets_protection.py # Named/protected ranges
│   │       └── sheets_advanced.py  # Groups, slicers, copy/paste
│   └── utils/                  # Utilities
│       ├── __init__.py
│       └── introspection.py    # Function-to-tool conversion
├── tests/                      # Test suite
├── examples/                   # Usage examples
└── pyproject.toml              # Package configuration
```

## Key Concepts

### Tools
Self-contained units of functionality defined with:
- **Schema**: name, description, parameters (with types, descriptions, required flags)
- **Handler**: The actual implementation function
- **Metadata**: category, tags, version

```python
from tool_master import Tool, ToolParameter
from tool_master.schemas.tool import ParameterType

my_tool = Tool(
    name="my_tool",
    description="Does something useful",
    parameters=[
        ToolParameter(
            name="input",
            type=ParameterType.STRING,
            description="The input to process",
            required=True,
        ),
    ],
    category="utility",
    tags=["example"],
).set_handler(my_handler_function)
```

### Executors
Adapters that transform tools into platform-specific formats:
- **OpenAIExecutor**: OpenAI function calling format
- **AnthropicExecutor**: Anthropic Claude tools format
- **GenericExecutor**: Platform-agnostic format
- **MCPExecutor**: Model Context Protocol format

```python
from tool_master.executors import OpenAIExecutor

executor = OpenAIExecutor()
openai_tools = executor.format_tools([my_tool])
result = await executor.execute(my_tool, {"input": "test"})
```

### MCP Integration

Tool Master provides two ways to use tools with the Model Context Protocol:

**1. MCPExecutor** - Format tools for MCP without running a server:

```python
from tool_master.executors import MCPExecutor

executor = MCPExecutor()
mcp_tools = executor.format_tools([my_tool])  # MCP tool schema format
result = await executor.execute(my_tool, {"input": "test"})
formatted = executor.format_result(result)  # MCP CallToolResult format
```

**2. ToolMasterMCPServer** - Run tools as a full MCP server:

```python
from tool_master.mcp_server import ToolMasterMCPServer
from tool_master.tools.datetime_tools import get_current_time, format_date

# Create server and register tools
server = ToolMasterMCPServer("my-tools")
server.register_tools([get_current_time, format_date])

# Or register from a registry
server.register_from_registry(my_registry)

# Run with stdio transport (for MCP clients like Claude Desktop)
import asyncio
asyncio.run(server.run_stdio())
```

Install MCP support: `pip install tool-master[mcp]`

### Tool Registry
Central registry for discovering and loading tools:
- Register tools by name
- Query by category or tags
- Search across name/description

```python
from tool_master import ToolRegistry

registry = ToolRegistry()
registry.register(my_tool)

# Find tools
math_tools = registry.get_by_category("math")
utility_tools = registry.get_by_tag("utility")
```

### @tool Decorator
Create tools directly from functions:

```python
from tool_master.registry.registry import tool

@tool("greet", "Generate a greeting", category="utility")
def greet(name: str, formal: bool = False) -> str:
    return f"Hello, {name}!" if not formal else f"Good day, {name}."
```

### Credentials Providers (OAuth Tools)

OAuth-dependent tools (like Google Calendar/Sheets) use the Credentials Provider pattern for portability.

**Tool Categories:**

| Category | Examples | Handler | Credentials |
|----------|----------|---------|-------------|
| **Standalone** | dice, datetime | Included | None |
| **No Auth APIs** | currency, dictionary, translation, geocoding, url | Included | None |
| **Local Libraries** | text_analysis, file_tools | Included | pip install |
| **API Key** | weather, wikipedia, news | Included | Env var |
| **External API** | finance | Included | yfinance |
| **OAuth** | Calendar, Sheets | Factory-created | Credentials Provider |

**Using Google OAuth Tools:**

```python
from tool_master.providers import SimpleGoogleCredentials
from tool_master.tools.google import create_calendar_tools, create_sheets_tools

# Option 1: Use environment variables
# Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
creds = SimpleGoogleCredentials()

# Option 2: Direct configuration
creds = SimpleGoogleCredentials(
    client_id="your-client-id",
    client_secret="your-client-secret",
    refresh_token="your-refresh-token",
)

# Create tools - they're wired to handle token refresh automatically
calendar_tools = create_calendar_tools(creds)  # 9 tools
sheets_tools = create_sheets_tools(creds)       # 62 tools
```

**Schema-only access (for custom implementations):**

```python
from tool_master.tools.google.calendar_tools import CALENDAR_SCHEMAS
from tool_master.tools.google.sheets_tools import SHEETS_SCHEMAS

# Get just the schemas, implement your own handlers
for schema in SHEETS_SCHEMAS:
    my_tool = schema.model_copy()
    my_tool.set_handler(my_custom_handler)
```

**Available Google Calendar Tools (9):**
- create_calendar, list_calendars, list_events, get_event
- create_event, update_event, delete_event, quick_add_event, share_calendar

**Available Google Sheets Tools (62):**
- **Core**: create_spreadsheet, list_spreadsheets, read_sheet, write_to_sheet, add_row_to_sheet, search_sheets, clear_range
- **Structure**: add_sheet, delete_sheet, rename_sheet, insert_rows, delete_rows, insert_columns, delete_columns, freeze_rows, freeze_columns, auto_resize_columns, sort_range
- **Formatting**: format_columns, set_text_format, set_text_color, set_background_color, set_alignment, set_borders, merge_cells, unmerge_cells, alternating_colors, add_note
- **Charts**: create_chart, list_charts, delete_chart, create_pivot_table, list_pivot_tables, delete_pivot_table
- **Filters**: set_basic_filter, clear_basic_filter, create_filter_view, delete_filter_view, list_filter_views, conditional_format, data_validation
- **Protection**: create_named_range, list_named_ranges, delete_named_range, protect_range, list_protected_ranges, delete_protected_range, protect_sheet
- **Advanced**: find_replace, copy_paste, cut_paste, hide_sheet, show_sheet, set_tab_color, add_hyperlink, create_row_group, create_column_group, delete_row_group, delete_column_group, list_slicers, create_slicer, delete_slicer

## Development

### Setup
```bash
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest
```

### Type Checking
```bash
mypy src/tool_master
```

## Adding New Tools

1. Create a new file in `src/tool_master/tools/` (e.g., `my_tools.py`)
2. Define handler functions
3. Create Tool objects with parameters and metadata
4. Export from `tools/__init__.py`

## Adding New Executors

1. Create a new file in `src/tool_master/executors/`
2. Inherit from `BaseExecutor`
3. Implement `format_tool`, `format_tools`, `execute`, `format_result`
4. Export from `executors/__init__.py`

## Existing Tools (149 Total)

**Standalone Tools:**
- [x] DateTime tools (5 tools) - datetime_tools.py
  - get_current_time, get_unix_timestamp, format_date, parse_date, get_time_difference
- [x] Dice tools (1 tool) - dice_tools.py

**API Key Tools:**
- [x] Weather tools (11 tools) - weather_tools.py (WEATHER_API_KEY)
  - get_weather, get_hourly_weather, search_weather_locations, get_weather_alerts
  - get_air_quality, get_timezone, get_astronomy
  - get_historical_weather, get_future_weather, get_marine_weather, get_sports_events
- [x] Wikipedia tools (3 tools) - wikipedia_tools.py
- [x] News tools (3 tools) - news_tools.py (NEWS_API_KEY)

**No-Auth API Tools:**
- [x] Currency tools (5 tools) - currency_tools.py
- [x] Dictionary tools (5 tools) - dictionary_tools.py
- [x] Translation tools (3 tools) - translation_tools.py
- [x] Geocoding tools (4 tools) - geocoding_tools.py
- [x] URL tools (4 tools) - url_tools.py
  - take_screenshot supports 20+ device presets for responsive design testing

**Local Library Tools:**
- [x] Text Analysis tools (5 tools) - text_analysis_tools.py
- [x] File Format tools (18 tools) - file_tools.py
  - **Excel**: read_excel, write_excel, list_excel_sheets, read_excel_sheet_info
  - **CSV**: read_csv, write_csv, csv_to_excel
  - **JSON**: read_json, write_json, validate_json
  - **PDF**: read_pdf_text, read_pdf_metadata, count_pdf_pages
  - **PowerPoint**: read_pptx_text, read_pptx_structure
  - **Image**: read_image_metadata, resize_image, convert_image_format

**External API Tools:**
- [x] Finance tools (11 tools) - finance_tools.py (yfinance)

**OAuth Tools:**
- [x] Google Calendar tools (9 tools) - google/calendar_tools.py
- [x] Google Sheets tools (62 tools) - google/sheets_tools.py

## Planned Executors

- [x] OpenAI function calling
- [x] Anthropic Claude tools
- [x] Generic/platform-agnostic
- [x] Model Context Protocol (MCP)
- [ ] LangChain tools
- [ ] Custom formats as needed

## README Updates
Always update @README.md at the end of every plan. If you don't believe the update requires an edit to the README, inform the user.