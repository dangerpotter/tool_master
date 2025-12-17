"""Google Calendar tools with schema definitions and factory function.

Usage:
    from tool_master.providers import SimpleGoogleCredentials
    from tool_master.tools.google import create_calendar_tools

    creds = SimpleGoogleCredentials()
    calendar_tools = create_calendar_tools(creds)

For schema-only access (custom implementations):
    from tool_master.tools.google.calendar_tools import CALENDAR_SCHEMAS
"""

from typing import TYPE_CHECKING, List, Optional
import re

from tool_master.schemas.tool import Tool, ToolParameter, ParameterType

if TYPE_CHECKING:
    from tool_master.providers import GoogleCredentialsProvider


# =============================================================================
# Schema Definitions (no handlers)
# =============================================================================

_create_calendar_schema = Tool(
    name="create_calendar",
    description="Create a new Google Calendar. By default, calendars are PUBLIC so everyone can view them via the share link.",
    parameters=[
        ToolParameter(
            name="title",
            type=ParameterType.STRING,
            description="Title for the calendar (e.g., 'Group Events 2025', 'Book Club Meetings')",
            required=True,
        ),
        ToolParameter(
            name="description",
            type=ParameterType.STRING,
            description="Brief description of what this calendar is for",
            required=False,
        ),
        ToolParameter(
            name="timezone",
            type=ParameterType.STRING,
            description="IANA timezone (e.g., 'America/New_York', 'Europe/London', 'UTC'). Default: UTC",
            required=False,
        ),
        ToolParameter(
            name="make_public",
            type=ParameterType.BOOLEAN,
            description="If true (default), calendar is publicly viewable via the share link",
            required=False,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "create"],
)

_list_calendars_schema = Tool(
    name="list_calendars",
    description="List all calendars accessible by the authenticated user.",
    parameters=[],
    category="calendar",
    tags=["google", "calendar", "list"],
)

_list_events_schema = Tool(
    name="list_events",
    description="List upcoming events from a calendar. Use when someone asks what's coming up or wants to see the calendar.",
    parameters=[
        ToolParameter(
            name="calendar_id",
            type=ParameterType.STRING,
            description="The Google Calendar ID",
            required=True,
        ),
        ToolParameter(
            name="time_min",
            type=ParameterType.STRING,
            description="Start of time range in ISO 8601 format (e.g., '2025-01-01T00:00:00Z'). Defaults to now.",
            required=False,
        ),
        ToolParameter(
            name="time_max",
            type=ParameterType.STRING,
            description="End of time range in ISO 8601 format. Defaults to unlimited.",
            required=False,
        ),
        ToolParameter(
            name="max_results",
            type=ParameterType.INTEGER,
            description="Maximum number of events to return (1-100). Default: 10",
            required=False,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "events", "list"],
)

_get_event_schema = Tool(
    name="get_event",
    description="Get details of a specific event by its ID.",
    parameters=[
        ToolParameter(
            name="calendar_id",
            type=ParameterType.STRING,
            description="The Google Calendar ID",
            required=True,
        ),
        ToolParameter(
            name="event_id",
            type=ParameterType.STRING,
            description="The event ID to retrieve",
            required=True,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "events", "get"],
)

_create_event_schema = Tool(
    name="create_event",
    description="Create a new event on a calendar. Can invite attendees via email. Returns the event link.",
    parameters=[
        ToolParameter(
            name="calendar_id",
            type=ParameterType.STRING,
            description="The Google Calendar ID",
            required=True,
        ),
        ToolParameter(
            name="title",
            type=ParameterType.STRING,
            description="Event title/name",
            required=True,
        ),
        ToolParameter(
            name="start_time",
            type=ParameterType.STRING,
            description="Start time in ISO 8601 format (e.g., '2025-01-15T14:00:00') or date for all-day events ('2025-01-15')",
            required=True,
        ),
        ToolParameter(
            name="end_time",
            type=ParameterType.STRING,
            description="End time in ISO 8601 format or date for all-day events",
            required=True,
        ),
        ToolParameter(
            name="description",
            type=ParameterType.STRING,
            description="Optional event description/notes",
            required=False,
        ),
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="Optional location (address or place name)",
            required=False,
        ),
        ToolParameter(
            name="all_day",
            type=ParameterType.BOOLEAN,
            description="If true, creates an all-day event (use date format for start/end)",
            required=False,
        ),
        ToolParameter(
            name="timezone",
            type=ParameterType.STRING,
            description="IANA timezone for the event times (e.g., 'America/New_York'). Default: UTC",
            required=False,
        ),
        ToolParameter(
            name="attendees",
            type=ParameterType.ARRAY,
            description="List of email addresses to invite. They will receive calendar invitations.",
            required=False,
        ),
        ToolParameter(
            name="send_notifications",
            type=ParameterType.BOOLEAN,
            description="If true (default), send email invitations to attendees",
            required=False,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "events", "create"],
)

_update_event_schema = Tool(
    name="update_event",
    description="Update an existing event. Use when someone wants to change event details or reschedule.",
    parameters=[
        ToolParameter(
            name="calendar_id",
            type=ParameterType.STRING,
            description="The Google Calendar ID",
            required=True,
        ),
        ToolParameter(
            name="event_id",
            type=ParameterType.STRING,
            description="The event ID to update",
            required=True,
        ),
        ToolParameter(
            name="title",
            type=ParameterType.STRING,
            description="New title (optional)",
            required=False,
        ),
        ToolParameter(
            name="start_time",
            type=ParameterType.STRING,
            description="New start time in ISO 8601 format (optional)",
            required=False,
        ),
        ToolParameter(
            name="end_time",
            type=ParameterType.STRING,
            description="New end time in ISO 8601 format (optional)",
            required=False,
        ),
        ToolParameter(
            name="description",
            type=ParameterType.STRING,
            description="New description (optional)",
            required=False,
        ),
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="New location (optional)",
            required=False,
        ),
        ToolParameter(
            name="timezone",
            type=ParameterType.STRING,
            description="Timezone for new times. Default: UTC",
            required=False,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "events", "update"],
)

_delete_event_schema = Tool(
    name="delete_event",
    description="Delete an event from a calendar. Use when someone wants to cancel or remove an event.",
    parameters=[
        ToolParameter(
            name="calendar_id",
            type=ParameterType.STRING,
            description="The Google Calendar ID",
            required=True,
        ),
        ToolParameter(
            name="event_id",
            type=ParameterType.STRING,
            description="The event ID to delete",
            required=True,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "events", "delete"],
)

_quick_add_event_schema = Tool(
    name="quick_add_event",
    description="Create an event using natural language. Google parses the text to extract date, time, and details. Use for quick, informal event creation like 'Dinner tomorrow at 7pm at Mario's'.",
    parameters=[
        ToolParameter(
            name="calendar_id",
            type=ParameterType.STRING,
            description="The Google Calendar ID",
            required=True,
        ),
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="Natural language event description (e.g., 'Dinner with John at 7pm tomorrow at Olive Garden')",
            required=True,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "events", "quick-add"],
)

_share_calendar_schema = Tool(
    name="share_calendar",
    description="Share a calendar with someone via email or make it publicly viewable.",
    parameters=[
        ToolParameter(
            name="calendar_id",
            type=ParameterType.STRING,
            description="The Google Calendar ID",
            required=True,
        ),
        ToolParameter(
            name="email",
            type=ParameterType.STRING,
            description="Email address to share with (omit if making public)",
            required=False,
        ),
        ToolParameter(
            name="role",
            type=ParameterType.STRING,
            description="Access level: 'reader' (view only) or 'writer' (can edit). Default: reader",
            required=False,
            enum=["reader", "writer"],
        ),
        ToolParameter(
            name="make_public",
            type=ParameterType.BOOLEAN,
            description="If true, makes the calendar publicly viewable and returns a share link",
            required=False,
        ),
    ],
    category="calendar",
    tags=["google", "calendar", "share"],
)


# All calendar schemas for export
CALENDAR_SCHEMAS: List[Tool] = [
    _create_calendar_schema,
    _list_calendars_schema,
    _list_events_schema,
    _get_event_schema,
    _create_event_schema,
    _update_event_schema,
    _delete_event_schema,
    _quick_add_event_schema,
    _share_calendar_schema,
]


# =============================================================================
# Factory Function
# =============================================================================

def create_calendar_tools(credentials: "GoogleCredentialsProvider") -> List[Tool]:
    """Create calendar tools wired to the given credentials provider.

    Args:
        credentials: A GoogleCredentialsProvider instance that handles OAuth tokens

    Returns:
        List of Tool objects with handlers ready to use

    Example:
        from tool_master.providers import SimpleGoogleCredentials
        from tool_master.tools.google import create_calendar_tools

        creds = SimpleGoogleCredentials()
        tools = create_calendar_tools(creds)
    """
    from tool_master.tools.google import calendar_impl as impl

    # Handler implementations
    async def _create_calendar(
        title: str,
        description: str = "",
        timezone: str = "UTC",
        make_public: bool = True,
    ) -> dict:
        token = await credentials.get_access_token()
        return await impl.create_calendar(token, title, description, timezone, make_public)

    async def _list_calendars() -> dict:
        token = await credentials.get_access_token()
        return await impl.list_calendars(token)

    async def _list_events(
        calendar_id: str,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
    ) -> dict:
        token = await credentials.get_access_token()
        return await impl.list_events(token, calendar_id, time_min, time_max, max_results)

    async def _get_event(calendar_id: str, event_id: str) -> dict:
        token = await credentials.get_access_token()
        return await impl.get_event(token, calendar_id, event_id)

    async def _create_event(
        calendar_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        all_day: bool = False,
        timezone: str = "UTC",
        attendees: Optional[List[str]] = None,
        send_notifications: bool = True,
    ) -> dict:
        # Validate attendee emails if provided
        if attendees:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid = [e for e in attendees if not re.match(email_pattern, e)]
            if invalid:
                return {"error": f"Invalid email addresses: {', '.join(invalid)}"}

        token = await credentials.get_access_token()
        return await impl.create_event(
            token, calendar_id, title, start_time, end_time,
            description, location, attendees, all_day, timezone,
            send_notifications=send_notifications
        )

    async def _update_event(
        calendar_id: str,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = "UTC",
    ) -> dict:
        updates = {}
        if title is not None:
            updates["title"] = title
        if start_time is not None:
            updates["start_time"] = start_time
        if end_time is not None:
            updates["end_time"] = end_time
        if description is not None:
            updates["description"] = description
        if location is not None:
            updates["location"] = location
        updates["timezone"] = timezone

        if not any(k != "timezone" for k in updates):
            return {"error": "No updates provided"}

        token = await credentials.get_access_token()
        return await impl.update_event(token, calendar_id, event_id, updates)

    async def _delete_event(calendar_id: str, event_id: str) -> dict:
        token = await credentials.get_access_token()
        return await impl.delete_event(token, calendar_id, event_id)

    async def _quick_add_event(calendar_id: str, text: str) -> dict:
        token = await credentials.get_access_token()
        return await impl.quick_add_event(token, calendar_id, text)

    async def _share_calendar(
        calendar_id: str,
        email: Optional[str] = None,
        role: str = "reader",
        make_public: bool = False,
    ) -> dict:
        if not email and not make_public:
            return {"error": "Provide email to share with, or set make_public=True"}

        token = await credentials.get_access_token()
        return await impl.share_calendar(token, calendar_id, email, role, make_public)

    # Map schema names to handlers
    handlers = {
        "create_calendar": _create_calendar,
        "list_calendars": _list_calendars,
        "list_events": _list_events,
        "get_event": _get_event,
        "create_event": _create_event,
        "update_event": _update_event,
        "delete_event": _delete_event,
        "quick_add_event": _quick_add_event,
        "share_calendar": _share_calendar,
    }

    # Create tools with handlers
    tools = []
    for schema in CALENDAR_SCHEMAS:
        tool = schema.model_copy(deep=True)
        handler = handlers.get(tool.name)
        if handler:
            tool.set_handler(handler)
        tools.append(tool)

    return tools
