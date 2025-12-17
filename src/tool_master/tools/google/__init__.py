"""Google API tools (Calendar, Sheets, etc.).

These tools require OAuth credentials. Use the factory functions
to create tools wired to your credentials provider.

Usage:
    from tool_master.providers import SimpleGoogleCredentials
    from tool_master.tools.google import create_calendar_tools, create_sheets_tools

    # Configure credentials (env vars or direct)
    creds = SimpleGoogleCredentials(
        client_id="...",
        client_secret="...",
        refresh_token="...",
    )

    # Create tools
    calendar_tools = create_calendar_tools(creds)
    sheets_tools = create_sheets_tools(creds)

You can also import just the schemas for custom implementations:
    from tool_master.tools.google.calendar_tools import CALENDAR_SCHEMAS
"""

from tool_master.tools.google.calendar_tools import (
    create_calendar_tools,
    CALENDAR_SCHEMAS,
)
from tool_master.tools.google.sheets_tools import (
    create_sheets_tools,
    SHEETS_SCHEMAS,
)

__all__ = [
    # Calendar
    "create_calendar_tools",
    "CALENDAR_SCHEMAS",
    # Sheets
    "create_sheets_tools",
    "SHEETS_SCHEMAS",
]
