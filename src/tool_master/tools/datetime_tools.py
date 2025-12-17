"""Date and time tools."""

import time
from datetime import datetime, timezone
from typing import Optional

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter


def _get_unix_timestamp() -> dict:
    """Get the current Unix timestamp."""
    ts = time.time()
    return {
        "unix_timestamp": ts,
        "unix_timestamp_int": int(ts),
        "iso": datetime.now(timezone.utc).isoformat(),
    }


def _get_current_time(timezone_name: Optional[str] = None) -> dict:
    """Get the current date and time."""
    if timezone_name:
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(timezone_name)
        except Exception:
            tz = timezone.utc
    else:
        tz = timezone.utc

    now = datetime.now(tz)
    return {
        "iso": now.isoformat(),
        "unix": int(now.timestamp()),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "timezone": str(tz),
        "weekday": now.strftime("%A"),
    }


def _format_date(
    date_string: str,
    input_format: str = "%Y-%m-%d",
    output_format: str = "%B %d, %Y",
) -> str:
    """Format a date string from one format to another."""
    dt = datetime.strptime(date_string, input_format)
    return dt.strftime(output_format)


def _parse_date(date_string: str, format: Optional[str] = None) -> dict:
    """Parse a date string and return its components."""
    if format:
        dt = datetime.strptime(date_string, format)
    else:
        # Try common formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
        ]
        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            raise ValueError(f"Could not parse date: {date_string}")

    return {
        "iso": dt.isoformat(),
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "weekday": dt.strftime("%A"),
        "week_number": dt.isocalendar()[1],
    }


# Tool definitions
get_current_time = Tool(
    name="get_current_time",
    description="Get the current date and time, optionally in a specific timezone",
    parameters=[
        ToolParameter(
            name="timezone_name",
            type=ParameterType.STRING,
            description="IANA timezone name (e.g., 'America/New_York', 'Europe/London'). Defaults to UTC.",
            required=False,
        ),
    ],
    category="datetime",
    tags=["time", "date", "utility"],
).set_handler(_get_current_time)


format_date = Tool(
    name="format_date",
    description="Convert a date string from one format to another",
    parameters=[
        ToolParameter(
            name="date_string",
            type=ParameterType.STRING,
            description="The date string to format",
            required=True,
        ),
        ToolParameter(
            name="input_format",
            type=ParameterType.STRING,
            description="The input date format (Python strftime format). Default: %Y-%m-%d",
            required=False,
            default="%Y-%m-%d",
        ),
        ToolParameter(
            name="output_format",
            type=ParameterType.STRING,
            description="The output date format (Python strftime format). Default: %B %d, %Y",
            required=False,
            default="%B %d, %Y",
        ),
    ],
    category="datetime",
    tags=["time", "date", "format", "utility"],
).set_handler(_format_date)


parse_date = Tool(
    name="parse_date",
    description="Parse a date string and return its components (year, month, day, etc.)",
    parameters=[
        ToolParameter(
            name="date_string",
            type=ParameterType.STRING,
            description="The date string to parse",
            required=True,
        ),
        ToolParameter(
            name="format",
            type=ParameterType.STRING,
            description="Optional format string. If not provided, common formats will be tried.",
            required=False,
        ),
    ],
    category="datetime",
    tags=["time", "date", "parse", "utility"],
).set_handler(_parse_date)


get_unix_timestamp = Tool(
    name="get_unix_timestamp",
    description="Get the current Unix timestamp (seconds since January 1, 1970 UTC). Useful for precise time calculations.",
    parameters=[],
    category="datetime",
    tags=["time", "timestamp", "unix", "utility"],
).set_handler(_get_unix_timestamp)
