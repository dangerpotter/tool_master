"""Google Calendar API implementation.

Pure API functions that accept an access_token. No database or Flask dependencies.
These are used internally by the calendar tools factory.
"""

import logging
from datetime import datetime
from typing import Optional, List
from urllib.parse import urlencode, quote

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


def _format_event(event: dict) -> dict:
    """Format a Google Calendar event for display."""
    start = event.get("start", {})
    end = event.get("end", {})

    return {
        "event_id": event.get("id"),
        "title": event.get("summary", "(No title)"),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "timezone": start.get("timeZone", ""),
        "all_day": "date" in start and "dateTime" not in start,
        "status": event.get("status"),
        "html_link": event.get("htmlLink"),
        "created": event.get("created"),
        "updated": event.get("updated"),
        "attendees": [
            {"email": a.get("email"), "status": a.get("responseStatus")}
            for a in event.get("attendees", [])
        ],
    }


async def create_calendar(
    access_token: str,
    title: str,
    description: str = "",
    timezone: str = "UTC",
    make_public: bool = True
) -> dict:
    """Create a new secondary calendar.

    Args:
        access_token: Valid Google OAuth access token
        title: Calendar title/summary
        description: Optional description
        timezone: IANA timezone (e.g., "America/New_York")
        make_public: If True, automatically make calendar publicly viewable

    Returns:
        Dict with calendar_id, url, is_public, share_link, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body = {
        "summary": title,
        "description": description,
        "timeZone": timezone,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{CALENDAR_API_BASE}/calendars",
            headers=headers,
            json=body
        )

        if response.status_code not in (200, 201):
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        data = response.json()
        calendar_id = data.get("id")

        result = {
            "calendar_id": calendar_id,
            "title": data.get("summary"),
            "description": data.get("description", ""),
            "timezone": data.get("timeZone"),
            "url": f"https://calendar.google.com/calendar/embed?src={quote(calendar_id)}",
            "is_public": False,
        }

        if make_public:
            share_result = await share_calendar(access_token, calendar_id, make_public=True)
            if "error" not in share_result:
                result["is_public"] = True
                result["share_link"] = share_result.get("share_link")
            else:
                result["share_warning"] = f"Calendar created but not made public: {share_result.get('error')}"

        return result


async def list_calendars(access_token: str) -> dict:
    """List all calendars accessible by the authenticated user.

    Args:
        access_token: Valid Google OAuth access token

    Returns:
        Dict with calendars list, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{CALENDAR_API_BASE}/users/me/calendarList"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        data = response.json()
        items = data.get("items", [])

        calendars = []
        for item in items:
            calendars.append({
                "calendar_id": item.get("id"),
                "title": item.get("summary"),
                "description": item.get("description", ""),
                "timezone": item.get("timeZone"),
                "access_role": item.get("accessRole"),
                "primary": item.get("primary", False),
            })

        return {"calendars": calendars, "count": len(calendars)}


async def list_events(
    access_token: str,
    calendar_id: str,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    single_events: bool = True
) -> dict:
    """List events from a calendar.

    Args:
        access_token: Valid Google OAuth access token
        calendar_id: Google Calendar ID
        time_min: Lower bound (RFC3339 timestamp)
        time_max: Upper bound (RFC3339 timestamp)
        max_results: Maximum number of events
        single_events: Expand recurring events

    Returns:
        Dict with events list, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {"Authorization": f"Bearer {access_token}"}

    params = {
        "maxResults": min(max_results, 100),
        "singleEvents": str(single_events).lower(),
        "orderBy": "startTime" if single_events else "updated",
    }

    if time_min:
        params["timeMin"] = time_min
    else:
        params["timeMin"] = datetime.utcnow().isoformat() + "Z"

    if time_max:
        params["timeMax"] = time_max

    url = f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events?{urlencode(params)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 404:
            return {"error": "Calendar not found"}

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        data = response.json()
        events = data.get("items", [])

        return {
            "events": [_format_event(e) for e in events],
            "count": len(events),
            "calendar_id": calendar_id,
        }


async def get_event(
    access_token: str,
    calendar_id: str,
    event_id: str
) -> dict:
    """Get a single event by ID.

    Args:
        access_token: Valid Google OAuth access token
        calendar_id: Google Calendar ID
        event_id: Event ID

    Returns:
        Dict with event details, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events/{event_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 404:
            return {"error": "Event not found"}

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        return {"event": _format_event(response.json())}


async def create_event(
    access_token: str,
    calendar_id: str,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: Optional[List[str]] = None,
    all_day: bool = False,
    timezone: str = "UTC",
    reminders: Optional[List[dict]] = None,
    send_notifications: bool = True
) -> dict:
    """Create a new calendar event.

    Args:
        access_token: Valid Google OAuth access token
        calendar_id: Google Calendar ID
        title: Event title/summary
        start_time: Start time (ISO 8601 format or date for all-day)
        end_time: End time (ISO 8601 format or date for all-day)
        description: Optional event description
        location: Optional location string
        attendees: Optional list of email addresses to invite
        all_day: If True, use date-only format for all-day events
        timezone: IANA timezone for the event
        reminders: Optional list of reminders
        send_notifications: If True, send email invitations to attendees

    Returns:
        Dict with event details, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body = {
        "summary": title,
        "description": description,
        "location": location,
    }

    if all_day:
        body["start"] = {"date": start_time}
        body["end"] = {"date": end_time}
    else:
        body["start"] = {"dateTime": start_time, "timeZone": timezone}
        body["end"] = {"dateTime": end_time, "timeZone": timezone}

    if attendees:
        body["attendees"] = [{"email": email} for email in attendees]

    if reminders:
        body["reminders"] = {"useDefault": False, "overrides": reminders}

    url = f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events"
    if attendees and send_notifications:
        url += "?sendUpdates=all"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=body)

        if response.status_code not in (200, 201):
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        result = {"event": _format_event(response.json())}
        if attendees:
            result["invitations_sent"] = send_notifications
            result["attendees"] = attendees
        return result


async def update_event(
    access_token: str,
    calendar_id: str,
    event_id: str,
    updates: dict
) -> dict:
    """Update an existing event.

    Args:
        access_token: Valid Google OAuth access token
        calendar_id: Google Calendar ID
        event_id: Event ID to update
        updates: Dict of fields to update

    Returns:
        Dict with updated event, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events/{event_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get existing event
        get_response = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        if get_response.status_code != 200:
            if get_response.status_code == 404:
                return {"error": "Event not found"}
            error_data = get_response.json() if get_response.text else {}
            return {"error": error_data.get("error", {}).get("message", "Failed to get event")}

        event = get_response.json()

        # Apply updates
        if "title" in updates:
            event["summary"] = updates["title"]
        if "description" in updates:
            event["description"] = updates["description"]
        if "location" in updates:
            event["location"] = updates["location"]
        if "start_time" in updates:
            timezone = updates.get("timezone", "UTC")
            if updates.get("all_day"):
                event["start"] = {"date": updates["start_time"]}
            else:
                event["start"] = {"dateTime": updates["start_time"], "timeZone": timezone}
        if "end_time" in updates:
            timezone = updates.get("timezone", "UTC")
            if updates.get("all_day"):
                event["end"] = {"date": updates["end_time"]}
            else:
                event["end"] = {"dateTime": updates["end_time"], "timeZone": timezone}

        response = await client.put(url, headers=headers, json=event)

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        return {"event": _format_event(response.json())}


async def delete_event(
    access_token: str,
    calendar_id: str,
    event_id: str
) -> dict:
    """Delete an event from a calendar.

    Args:
        access_token: Valid Google OAuth access token
        calendar_id: Google Calendar ID
        event_id: Event ID to delete

    Returns:
        Dict with success status, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events/{event_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.delete(url, headers=headers)

        if response.status_code == 404:
            return {"error": "Event not found"}

        if response.status_code not in (200, 204):
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        return {"success": True, "message": "Event deleted"}


async def quick_add_event(
    access_token: str,
    calendar_id: str,
    text: str
) -> dict:
    """Create an event using natural language.

    Args:
        access_token: Valid Google OAuth access token
        calendar_id: Google Calendar ID
        text: Natural language description

    Returns:
        Dict with created event, or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events/quickAdd?text={quote(text)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers)

        if response.status_code not in (200, 201):
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        return {"event": _format_event(response.json())}


async def share_calendar(
    access_token: str,
    calendar_id: str,
    email: Optional[str] = None,
    role: str = "reader",
    make_public: bool = False
) -> dict:
    """Share a calendar with a user or make it public.

    Args:
        access_token: Valid Google OAuth access token
        calendar_id: Google Calendar ID
        email: Email address to share with
        role: Access role - "reader", "writer"
        make_public: If True, make calendar publicly readable

    Returns:
        Dict with share info or error
    """
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    if make_public:
        body = {"role": "reader", "scope": {"type": "default"}}
    elif email:
        body = {"role": role, "scope": {"type": "user", "value": email}}
    else:
        return {"error": "Must provide email or set make_public=True"}

    url = f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/acl"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=body)

        if response.status_code not in (200, 201):
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"error": error_msg}

        data = response.json()

        share_link = None
        if make_public:
            share_link = f"https://calendar.google.com/calendar/embed?src={quote(calendar_id)}"

        return {
            "success": True,
            "role": data.get("role"),
            "scope": data.get("scope"),
            "share_link": share_link,
        }
