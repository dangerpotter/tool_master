# Tool Master

A master library of reusable LLM tools with pluggable executors for drag-and-drop integration across agent and chatbot projects.

## Features

- **149 Ready-to-Use Tools** - DateTime, Dice, Weather, Wikipedia, Finance, Currency, Dictionary, Translation, Geocoding, URL, Text Analysis, News, File Formats, Google Calendar, Google Sheets
- **Multi-Platform Support** - Works with OpenAI, Anthropic Claude, MCP, and custom platforms
- **MCP Server Integration** - Expose tools as a Model Context Protocol server
- **Pluggable Executors** - Adapters transform tools to any target format
- **Credentials Provider Pattern** - Portable OAuth tools with swappable credential backends
- **Tool Registry** - Discover and query tools by category or tags
- **Type-Safe** - Full Pydantic models with validation

## Installation

```bash
pip install tool-master
```

### Optional Dependencies

```bash
# Finance tools (stock quotes, options, earnings, etc.)
pip install tool-master[finance]

# Weather tools
pip install tool-master[weather]

# Wikipedia tools
pip install tool-master[wikipedia]

# Google tools (Calendar, Sheets)
pip install tool-master[google]

# Currency exchange tools
pip install tool-master[currency]

# Dictionary tools
pip install tool-master[dictionary]

# Translation tools
pip install tool-master[translation]

# Geocoding tools
pip install tool-master[geocoding]

# URL/Web tools
pip install tool-master[url]

# News tools
pip install tool-master[news]

# Text analysis tools (sentiment, language detection)
pip install tool-master[text-analysis]

# File format tools (Excel, CSV, JSON, PDF, PowerPoint, Images)
pip install tool-master[files]

# MCP (Model Context Protocol) support
pip install tool-master[mcp]

# All optional dependencies
pip install tool-master[all]
```

## Environment Setup

Some tools require API keys or OAuth credentials. Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Required For | How to Obtain |
|----------|--------------|---------------|
| `WEATHER_API_KEY` | Weather tools | [weatherapi.com](https://www.weatherapi.com/) (free tier) |
| `NEWS_API_KEY` | News tools | [newsapi.org](https://newsapi.org/register) (free tier) |
| `GOOGLE_CLIENT_ID` | Calendar & Sheets | [Google Cloud Console](https://console.cloud.google.com/) |
| `GOOGLE_CLIENT_SECRET` | Calendar & Sheets | [Google Cloud Console](https://console.cloud.google.com/) |
| `GOOGLE_REFRESH_TOKEN` | Calendar & Sheets | OAuth flow (see [OAuth Setup](#oauth-setup)) |

Most tools work without any credentials (Currency, Dictionary, Translation, Geocoding, URL, Wikipedia, Finance, DateTime, Dice, Text Analysis).

## Quick Start

```python
from tool_master import Tool, ToolRegistry
from tool_master.executors import OpenAIExecutor

# Import built-in tools
from tool_master.tools import get_current_time, roll_dice, get_weather

# Create a registry and register tools
registry = ToolRegistry()
registry.register(get_current_time)
registry.register(roll_dice)
registry.register(get_weather)

# Format for OpenAI
executor = OpenAIExecutor()
openai_tools = executor.format_tools(registry.list_all())

# Execute a tool
result = await executor.execute(get_current_time, {"timezone": "America/New_York"})
```

## Available Tools (149 Total)

### DateTime Tools (5)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_current_time` | Get current date/time for a timezone | `timezone` (optional) |
| `get_unix_timestamp` | Get current Unix timestamp | None |
| `format_date` | Format a date string | `date`, `format` |
| `parse_date` | Parse a date string | `date_string`, `format` |
| `get_time_difference` | Get time difference between locations/timezones | `location1`, `location2` |

Supports both city names (e.g., "Tokyo", "New York") and IANA timezones (e.g., "Asia/Tokyo", "America/New_York").

```python
from tool_master.tools import get_current_time, get_unix_timestamp, format_date, parse_date, get_time_difference
```

### Dice Tools (1)

| Tool | Description | Parameters |
|------|-------------|------------|
| `roll_dice` | Roll dice with D&D notation | `notation`, `reason` (optional) |

Supports: `d20`, `2d6+3`, `4d6 drop lowest`, `1d20 advantage`, `1d%` (percentile)

```python
from tool_master.tools import roll_dice
```

### Weather Tools (11)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_weather` | Get weather conditions and daily forecast | `location`, `days` (optional, 1-7) |
| `get_hourly_weather` | Get hour-by-hour forecast | `location`, `days` (optional, 1-3) |
| `search_weather_locations` | Search/autocomplete locations | `query` |
| `get_weather_alerts` | Get severe weather alerts/warnings | `location` |
| `get_air_quality` | Get air quality index and pollutants | `location` |
| `get_timezone` | Get timezone info for a location | `location` |
| `get_astronomy` | Get sunrise, sunset, moon phases | `location`, `date` (optional) |
| `get_historical_weather` | Get past weather (from 2010) | `location`, `date` |
| `get_future_weather` | Get long-range forecast (14-300 days) | `location`, `date` |
| `get_marine_weather` | Get marine/sailing forecast with tides | `location`, `days` (optional, 1-7) |
| `get_sports_events` | Get sports events (football, cricket, golf) | `query` |

Requires: `WEATHER_API_KEY` environment variable (WeatherAPI.com)

```python
from tool_master.tools import (
    get_weather, get_hourly_weather, search_weather_locations,
    get_weather_alerts, get_air_quality, get_timezone, get_astronomy,
    get_historical_weather, get_future_weather, get_marine_weather,
    get_sports_events,
)
```

### Wikipedia Tools (3)

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_wikipedia` | Search for articles | `query`, `limit` (optional) |
| `get_wikipedia_article` | Get article summary | `title` |
| `get_random_wikipedia_article` | Get random article | None |

```python
from tool_master.tools import search_wikipedia, get_wikipedia_article, get_random_wikipedia_article
```

### Finance Tools (11)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_stock_quote` | Current price and key metrics | `symbol` |
| `search_stocks` | Search by name or symbol | `query`, `count` (optional) |
| `get_top_stocks` | Top performers by sector | `entity_type`, `sector`, `count` |
| `get_price_history` | Historical OHLCV data | `symbol`, `period`, `interval` |
| `get_earnings` | Earnings and EPS data | `symbol`, `period` |
| `get_analyst_ratings` | Buy/hold/sell recommendations | `symbol` |
| `get_dividends` | Dividend info and history | `symbol`, `include_history` |
| `get_stock_news` | Recent news articles | `symbol`, `count` |
| `get_options` | Options chain data | `symbol`, `option_type`, `date` |
| `get_financials` | Revenue, margins, cash flow | `symbol`, `period` |
| `get_holders` | Institutional ownership | `symbol` |

Supports stocks (AAPL), ETFs (SPY), and crypto (BTC-USD).

```python
from tool_master.tools import (
    get_stock_quote, search_stocks, get_top_stocks, get_price_history,
    get_earnings, get_analyst_ratings, get_dividends,
    get_stock_news, get_options, get_financials, get_holders,
)
```

### Currency Tools (5)

| Tool | Description | Parameters |
|------|-------------|------------|
| `convert_currency` | Convert between currencies | `amount`, `from_currency`, `to_currency` |
| `get_exchange_rates` | Get current exchange rates | `base_currency`, `symbols` (optional) |
| `get_historical_rates` | Get rates for a specific date | `date`, `base_currency`, `symbols` |
| `get_rate_history` | Get rate changes over date range | `from_currency`, `to_currency`, `start_date`, `end_date` |
| `list_currencies` | List all supported currencies | None |

No API key required - uses Frankfurter API (European Central Bank data).

```python
from tool_master.tools import (
    convert_currency, get_exchange_rates, get_historical_rates,
    get_rate_history, list_currencies,
)
```

### Dictionary Tools (5)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_definition` | Get word definition and phonetics | `word`, `language` (optional) |
| `get_synonyms` | Get synonyms for a word | `word`, `max_results` (optional) |
| `get_antonyms` | Get antonyms for a word | `word`, `max_results` (optional) |
| `find_rhymes` | Find rhyming words | `word`, `max_results` (optional) |
| `find_similar_words` | Find by meaning, sound, or spelling | `word`, `match_type`, `max_results` |

No API key required - uses Free Dictionary API and Datamuse API.

```python
from tool_master.tools import (
    get_definition, get_synonyms, get_antonyms,
    find_rhymes, find_similar_words,
)
```

### Translation Tools (3)

| Tool | Description | Parameters |
|------|-------------|------------|
| `translate_text` | Translate text between languages | `text`, `source_language`, `target_language` |
| `detect_language` | Detect the language of text | `text` |
| `list_supported_languages` | List all supported language codes | None |

No API key required - uses MyMemory API (50+ languages supported).

```python
from tool_master.tools import translate_text, detect_language, list_supported_languages
```

### Geocoding Tools (4)

| Tool | Description | Parameters |
|------|-------------|------------|
| `geolocate_ip` | Get location from IP address | `ip_address` (optional) |
| `geocode_address` | Convert address to coordinates | `address`, `limit` (optional) |
| `reverse_geocode` | Convert coordinates to address | `latitude`, `longitude` |
| `lookup_zipcode` | Get location from postal code | `postal_code`, `country_code` (optional) |

No API key required - uses IP-API, Nominatim (OpenStreetMap), and Zippopotam.

```python
from tool_master.tools import geolocate_ip, geocode_address, reverse_geocode, lookup_zipcode
```

### URL Tools (4)

| Tool | Description | Parameters |
|------|-------------|------------|
| `extract_url_metadata` | Get title, description, images from URL | `url` |
| `take_screenshot` | Capture screenshot of webpage | `url`, `width`, `height`, `full_page`, `device`, `color_scheme` |
| `generate_pdf` | Generate PDF from webpage | `url` |
| `expand_url` | Expand shortened URLs | `url` |

No API key required - uses Microlink API.

**Screenshot Device Presets:** The `take_screenshot` tool supports 20+ device presets for responsive design testing:
- **Mobile (Apple):** iPhone 15 Pro Max, iPhone 15 Pro, iPhone 15, iPhone 14, iPhone SE
- **Mobile (Android):** Samsung Galaxy S23 Ultra, Samsung Galaxy S23, Pixel 8 Pro, Pixel 8
- **Tablets:** iPad Pro 12.9, iPad Pro 11, iPad Air, iPad Mini, Samsung Galaxy Tab S9
- **Desktop:** MacBook Pro 16, MacBook Pro 14, MacBook Air, iMac 24, Desktop 1920x1080, Desktop 1440x900

Also supports `color_scheme` parameter ("light" or "dark") to force a specific appearance.

```python
from tool_master.tools import extract_url_metadata, take_screenshot, generate_pdf, expand_url
```

### Text Analysis Tools (5)

| Tool | Description | Parameters |
|------|-------------|------------|
| `detect_text_language` | Detect language of text | `text` |
| `analyze_sentiment` | Get sentiment polarity and subjectivity | `text` |
| `extract_noun_phrases` | Extract key topics/entities | `text` |
| `get_word_frequency` | Count word frequencies | `text`, `top_n`, `exclude_stopwords` |
| `correct_spelling` | Suggest spelling corrections | `text` |

No API required - uses local Python libraries (langdetect, textblob).

```python
from tool_master.tools import (
    detect_text_language, analyze_sentiment, extract_noun_phrases,
    get_word_frequency, correct_spelling,
)
```

### News Tools (3)

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_news` | Search for news articles | `query`, `language`, `sort_by`, `from_date`, `to_date` |
| `get_top_headlines` | Get top headlines by country/category | `country`, `category`, `query`, `page_size` |
| `get_news_sources` | List available news sources | `category`, `language`, `country` |

Requires: `NEWS_API_KEY` environment variable (NewsAPI.org)

```python
from tool_master.tools import search_news, get_top_headlines, get_news_sources
```

### File Format Tools (18)

**Excel Tools (4)**

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_excel` | Read .xlsx file contents | `file_path`, `sheet_name`, `max_rows` |
| `write_excel` | Write data to .xlsx file | `file_path`, `data`, `sheet_name`, `headers` |
| `list_excel_sheets` | List all sheets in workbook | `file_path` |
| `read_excel_sheet_info` | Get sheet dimensions and headers | `file_path`, `sheet_name` |

**CSV Tools (3)**

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_csv` | Read .csv file (auto-detect delimiter) | `file_path`, `max_rows`, `delimiter` |
| `write_csv` | Write data to .csv file | `file_path`, `data`, `headers`, `delimiter` |
| `csv_to_excel` | Convert CSV to Excel format | `csv_path`, `excel_path`, `sheet_name` |

**JSON Tools (3)**

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_json` | Read and parse .json file | `file_path` |
| `write_json` | Write data to .json file | `file_path`, `data`, `indent` |
| `validate_json` | Validate JSON and get structure summary | `file_path` |

**PDF Tools (3)**

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_pdf_text` | Extract text from PDF pages | `file_path`, `start_page`, `end_page` |
| `read_pdf_metadata` | Get title, author, creation date | `file_path` |
| `count_pdf_pages` | Quick page count | `file_path` |

**PowerPoint Tools (2)**

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_pptx_text` | Extract text from all slides | `file_path` |
| `read_pptx_structure` | Get slide count, titles, notes | `file_path` |

**Image Tools (3)**

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_image_metadata` | Get dimensions, format, EXIF data | `file_path` |
| `resize_image` | Resize image to dimensions | `file_path`, `output_path`, `width`, `height` |
| `convert_image_format` | Convert between formats | `file_path`, `output_path`, `format` |

No API key required - uses local libraries (openpyxl, pypdf, python-pptx, pillow).

```python
from tool_master.tools import (
    # Excel
    read_excel, write_excel, list_excel_sheets, read_excel_sheet_info,
    # CSV
    read_csv, write_csv, csv_to_excel,
    # JSON
    read_json, write_json, validate_json,
    # PDF
    read_pdf_text, read_pdf_metadata, count_pdf_pages,
    # PowerPoint
    read_pptx_text, read_pptx_structure,
    # Image
    read_image_metadata, resize_image, convert_image_format,
)
```

### Google Calendar Tools (9)

| Tool | Description |
|------|-------------|
| `create_calendar` | Create a new calendar |
| `list_calendars` | List all calendars |
| `list_events` | List events with filters |
| `get_event` | Get event details |
| `create_event` | Create an event |
| `update_event` | Update an event |
| `delete_event` | Delete an event |
| `quick_add_event` | Create event from text |
| `share_calendar` | Share calendar with others |

Requires OAuth credentials (see [OAuth Setup](#oauth-setup)).

```python
from tool_master.providers import SimpleGoogleCredentials
from tool_master.tools.google import create_calendar_tools

creds = SimpleGoogleCredentials()  # Uses env vars
calendar_tools = create_calendar_tools(creds)  # Returns list of 9 Tool objects
```

### Google Sheets Tools (62)

**Core Operations (7)**
- `create_spreadsheet`, `list_spreadsheets`, `read_sheet`, `write_to_sheet`, `add_row_to_sheet`, `search_sheets`, `clear_range`

**Structure (11)**
- `add_sheet`, `delete_sheet`, `rename_sheet`, `insert_rows`, `delete_rows`, `insert_columns`, `delete_columns`, `freeze_rows`, `freeze_columns`, `auto_resize_columns`, `sort_range`

**Formatting (10)**
- `format_columns`, `set_text_format`, `set_text_color`, `set_background_color`, `set_alignment`, `set_borders`, `merge_cells`, `unmerge_cells`, `alternating_colors`, `add_note`

**Charts & Pivots (6)**
- `create_chart`, `list_charts`, `delete_chart`, `create_pivot_table`, `list_pivot_tables`, `delete_pivot_table`

**Filters & Validation (7)**
- `set_basic_filter`, `clear_basic_filter`, `create_filter_view`, `delete_filter_view`, `list_filter_views`, `conditional_format`, `data_validation`

**Protection (7)**
- `create_named_range`, `list_named_ranges`, `delete_named_range`, `protect_range`, `list_protected_ranges`, `delete_protected_range`, `protect_sheet`

**Advanced (14)**
- `find_replace`, `copy_paste`, `cut_paste`, `hide_sheet`, `show_sheet`, `set_tab_color`, `add_hyperlink`, `create_row_group`, `create_column_group`, `delete_row_group`, `delete_column_group`, `list_slicers`, `create_slicer`, `delete_slicer`

```python
from tool_master.providers import SimpleGoogleCredentials
from tool_master.tools.google import create_sheets_tools

creds = SimpleGoogleCredentials()  # Uses env vars
sheets_tools = create_sheets_tools(creds)  # Returns list of 62 Tool objects
```

## Executors

Executors adapt tools to different LLM platforms.

### OpenAI Executor

```python
from tool_master.executors import OpenAIExecutor

executor = OpenAIExecutor()

# Format tools for OpenAI API
openai_format = executor.format_tools([get_weather, roll_dice])

# Execute and get result
result = await executor.execute(get_weather, {"location": "New York"})
```

### Anthropic Executor

```python
from tool_master.executors import AnthropicExecutor

executor = AnthropicExecutor()

# Format tools for Claude API
claude_format = executor.format_tools([get_weather, roll_dice])

# Execute and get result
result = await executor.execute(get_weather, {"location": "London"})
```

### Generic Executor

```python
from tool_master.executors import GenericExecutor

executor = GenericExecutor()

# Platform-agnostic format
generic_format = executor.format_tools([get_weather])
```

### MCP Executor

```python
from tool_master.executors import MCPExecutor

executor = MCPExecutor()

# Format tools for MCP
mcp_format = executor.format_tools([get_weather, roll_dice])

# Execute and get MCP-formatted result
result = await executor.execute(get_weather, {"location": "Tokyo"})
formatted = executor.format_result(result)  # {content: [...], isError: false}
```

### MCP Server

Run Tool Master tools as a full MCP server for use with MCP-compatible clients like Claude Desktop.

```python
from tool_master.mcp_server import ToolMasterMCPServer
from tool_master.tools import get_current_time, roll_dice, get_weather

# Create server and register tools
server = ToolMasterMCPServer("my-tools")
server.register_tools([get_current_time, roll_dice, get_weather])

# Or register from a registry
server.register_from_registry(my_registry)

# Run with stdio transport
import asyncio
asyncio.run(server.run_stdio())
```

## Tool Registry

Organize and discover tools by category or tags.

```python
from tool_master import ToolRegistry
from tool_master.tools import get_weather, roll_dice, get_stock_quote

registry = ToolRegistry()

# Register tools
registry.register(get_weather)
registry.register(roll_dice)
registry.register(get_stock_quote)

# Query tools
finance_tools = registry.get_by_category("finance")
utility_tools = registry.get_by_tag("utility")
all_tools = registry.list_all()

# Search by name/description
results = registry.search("weather")
```

## Creating Custom Tools

### Using Tool Class

```python
from tool_master import Tool, ToolParameter
from tool_master.schemas.tool import ParameterType

def my_handler(text: str, uppercase: bool = False) -> str:
    return text.upper() if uppercase else text

my_tool = Tool(
    name="transform_text",
    description="Transform text with various options",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to transform",
            required=True,
        ),
        ToolParameter(
            name="uppercase",
            type=ParameterType.BOOLEAN,
            description="Convert to uppercase",
            required=False,
            default=False,
        ),
    ],
    category="text",
    tags=["utility", "transform"],
).set_handler(my_handler)
```

### Using @tool Decorator

```python
from tool_master.registry.registry import tool

@tool("greet", "Generate a greeting message", category="utility")
def greet(name: str, formal: bool = False) -> str:
    """
    Args:
        name: The name to greet
        formal: Use formal greeting style
    """
    return f"Good day, {name}." if formal else f"Hello, {name}!"
```

## OAuth Setup

Google Calendar and Sheets tools require OAuth credentials.

### Environment Variables

```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REFRESH_TOKEN="your-refresh-token"
```

### Direct Configuration

```python
from tool_master.providers import SimpleGoogleCredentials

creds = SimpleGoogleCredentials(
    client_id="your-client-id",
    client_secret="your-client-secret",
    refresh_token="your-refresh-token",
)
```

### Custom Credentials Provider

Implement the `GoogleCredentialsProvider` protocol for custom credential backends:

```python
from tool_master.providers import GoogleCredentialsProvider

class MyCredentialsProvider:
    def get_access_token(self) -> str:
        # Fetch from your credential store
        return fetch_token_from_vault()

    def refresh_token(self) -> str:
        # Handle token refresh
        return refresh_and_return_token()

# Use with Google tools
creds = MyCredentialsProvider()
calendar_tools = create_calendar_tools(creds)
```

## Schema-Only Access

Get tool schemas without handlers for custom implementations:

```python
from tool_master.tools.google.calendar_tools import CALENDAR_SCHEMAS
from tool_master.tools.google.sheets_tools import SHEETS_SCHEMAS

# Iterate schemas and add custom handlers
for schema in CALENDAR_SCHEMAS:
    my_tool = schema.model_copy()
    my_tool.set_handler(my_custom_implementation)
```

## Tool Categories

| Category | Credentials | Examples |
|----------|-------------|----------|
| **Standalone** | None | DateTime, Dice |
| **No Auth APIs** | None | Currency, Dictionary, Translation, Geocoding, URL |
| **Local Libraries** | None (pip install) | Text Analysis, File Formats |
| **API Key** | Environment variable | Weather, Wikipedia, News |
| **OAuth** | Credentials Provider | Google Calendar, Sheets |
| **External API** | None (yfinance) | Finance tools |

## Project Structure

```
Tool_Master/
├── src/tool_master/
│   ├── schemas/           # Tool, ToolParameter, ToolResult models
│   ├── executors/         # OpenAI, Anthropic, MCP, Generic adapters
│   ├── mcp_server/        # MCP Server integration
│   ├── providers/         # Credentials provider interfaces
│   ├── registry/          # ToolRegistry and @tool decorator
│   ├── tools/             # Built-in tool implementations
│   │   ├── datetime_tools.py
│   │   ├── dice_tools.py
│   │   ├── weather_tools.py
│   │   ├── wikipedia_tools.py
│   │   ├── finance_tools.py
│   │   ├── currency_tools.py
│   │   ├── dictionary_tools.py
│   │   ├── translation_tools.py
│   │   ├── geocoding_tools.py
│   │   ├── url_tools.py
│   │   ├── text_analysis_tools.py
│   │   ├── news_tools.py
│   │   ├── file_tools.py
│   │   └── google/        # OAuth tools (Calendar, Sheets)
│   └── utils/             # Introspection utilities
├── tests/
├── examples/
└── docs/
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/tool_master
```

## License

MIT License
