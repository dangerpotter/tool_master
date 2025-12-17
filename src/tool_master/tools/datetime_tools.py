"""Date and time tools."""

import asyncio
import concurrent.futures
import time
import zoneinfo
from datetime import datetime, timezone
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

# Nominatim API for geocoding (same as geocoding_tools.py)
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
NOMINATIM_HEADERS = {
    "User-Agent": "ToolMaster/1.0 (LLM Tool Library; https://github.com/tool-master)"
}


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


def _is_valid_timezone(tz_name: str) -> bool:
    """Check if a string is a valid IANA timezone name."""
    try:
        zoneinfo.ZoneInfo(tz_name)
        return True
    except (KeyError, zoneinfo.ZoneInfoNotFoundError):
        return False


async def _geocode_location_async(location: str) -> tuple[float, float]:
    """Geocode a location name to lat/lon coordinates."""
    params = {"q": location, "format": "json", "limit": 1}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{NOMINATIM_BASE}/search", params=params, headers=NOMINATIM_HEADERS
        )

        if response.status_code != 200:
            raise ValueError(f"Geocoding API error: {response.text}")

        data = response.json()

        if not data:
            raise ValueError(f"Could not find location: {location}")

        return float(data[0]["lat"]), float(data[0]["lon"])


def _get_timezone_from_coords(lat: float, lon: float) -> str:
    """Get IANA timezone name from coordinates using timezonefinder."""
    try:
        from timezonefinder import TimezoneFinder

        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        if tz_name is None:
            raise ValueError(f"Could not determine timezone for coordinates ({lat}, {lon})")
        return tz_name
    except ImportError:
        raise ImportError(
            "timezonefinder package required for city name lookup. "
            "Install with: pip install tool-master[geocoding]"
        )


async def _resolve_location_to_timezone_async(location: str) -> tuple[str, str]:
    """
    Resolve a location string to an IANA timezone.

    Args:
        location: Either an IANA timezone name or a city/place name

    Returns:
        Tuple of (original_input, timezone_name)
    """
    # First, try to parse as IANA timezone
    if _is_valid_timezone(location):
        return location, location

    # If not a timezone, geocode the location and find its timezone
    lat, lon = await _geocode_location_async(location)
    tz_name = _get_timezone_from_coords(lat, lon)
    return location, tz_name


async def _get_time_difference_async(location1: str, location2: str) -> dict:
    """Get the time difference between two locations or timezones."""
    # Resolve both locations to timezones
    input1, tz_name1 = await _resolve_location_to_timezone_async(location1)
    input2, tz_name2 = await _resolve_location_to_timezone_async(location2)

    # Get current time in both timezones
    tz1 = zoneinfo.ZoneInfo(tz_name1)
    tz2 = zoneinfo.ZoneInfo(tz_name2)

    now_utc = datetime.now(timezone.utc)
    now1 = now_utc.astimezone(tz1)
    now2 = now_utc.astimezone(tz2)

    # Calculate UTC offsets in hours
    offset1_seconds = now1.utcoffset().total_seconds()
    offset2_seconds = now2.utcoffset().total_seconds()

    offset1_hours = offset1_seconds / 3600
    offset2_hours = offset2_seconds / 3600

    # Format offset strings
    def format_offset(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((abs(seconds) % 3600) // 60)
        sign = "+" if hours >= 0 else "-"
        return f"{sign}{abs(hours):02d}:{minutes:02d}"

    offset1_str = format_offset(offset1_seconds)
    offset2_str = format_offset(offset2_seconds)

    # Calculate difference (positive means location2 is ahead)
    diff_hours = offset2_hours - offset1_hours

    # Generate description
    if diff_hours == 0:
        description = f"{input2} and {input1} are in the same timezone"
    elif diff_hours > 0:
        description = f"{input2} is {abs(diff_hours)} hour{'s' if abs(diff_hours) != 1 else ''} ahead of {input1}"
    else:
        description = f"{input2} is {abs(diff_hours)} hour{'s' if abs(diff_hours) != 1 else ''} behind {input1}"

    return {
        "location1": {
            "input": input1,
            "timezone": tz_name1,
            "current_time": now1.isoformat(),
            "utc_offset": offset1_str,
        },
        "location2": {
            "input": input2,
            "timezone": tz_name2,
            "current_time": now2.isoformat(),
            "utc_offset": offset2_str,
        },
        "difference_hours": diff_hours,
        "difference_description": description,
    }


def _get_time_difference_sync(location1: str, location2: str) -> dict:
    """Sync wrapper for get_time_difference."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _get_time_difference_async(location1, location2)
                )
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(
                _get_time_difference_async(location1, location2)
            )
    except RuntimeError:
        return asyncio.run(_get_time_difference_async(location1, location2))


get_time_difference = Tool(
    name="get_time_difference",
    description="Get the time difference between two locations or timezones. Accepts city names (e.g., 'Tokyo', 'New York') or IANA timezone names (e.g., 'America/New_York', 'Asia/Tokyo').",
    parameters=[
        ToolParameter(
            name="location1",
            type=ParameterType.STRING,
            description="First location - can be a city name (e.g., 'Paris', 'Los Angeles') or IANA timezone (e.g., 'Europe/Paris', 'America/Los_Angeles')",
            required=True,
        ),
        ToolParameter(
            name="location2",
            type=ParameterType.STRING,
            description="Second location - can be a city name or IANA timezone",
            required=True,
        ),
    ],
    category="datetime",
    tags=["time", "timezone", "difference", "city", "utility"],
).set_handler(_get_time_difference_sync)
