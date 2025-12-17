"""Core Google Sheets operations: create, read, write, search, list."""

import logging
from typing import Optional, List
from urllib.parse import quote, urlencode

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from tool_master.tools.google._sheets_utils import (
    SHEETS_API_BASE,
    DRIVE_API_BASE,
    extract_spreadsheet_id,
    _check_httpx,
)

logger = logging.getLogger(__name__)


async def create_spreadsheet(
    access_token: str,
    title: str,
    sheet_names: Optional[List[str]] = None,
) -> dict:
    """Create a new Google Sheets spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        title: Title for the new spreadsheet
        sheet_names: Optional list of sheet names (default: ["Sheet1"])

    Returns:
        Dict with spreadsheet_id, url, sheets, or error
    """
    _check_httpx()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    sheets = []
    if sheet_names:
        for name in sheet_names:
            sheets.append({"properties": {"title": name}})
    else:
        sheets.append({"properties": {"title": "Sheet1"}})

    body = {"properties": {"title": title}, "sheets": sheets}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(SHEETS_API_BASE, headers=headers, json=body)

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"error": error_msg}

            data = response.json()
            spreadsheet_id = data.get("spreadsheetId")

            # Make publicly accessible with link
            try:
                await client.post(
                    f"https://www.googleapis.com/drive/v3/files/{spreadsheet_id}/permissions",
                    headers=headers,
                    json={"role": "writer", "type": "anyone"},
                )
            except Exception as e:
                logger.warning(f"Failed to share spreadsheet: {e}")

            return {
                "spreadsheet_id": spreadsheet_id,
                "title": title,
                "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
                "sheets": [s["properties"]["title"] for s in data.get("sheets", [])],
            }

        except Exception as e:
            logger.error(f"Error creating spreadsheet: {e}")
            return {"error": str(e)}


async def list_spreadsheets(
    access_token: str,
    query: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """List spreadsheets from Google Drive.

    Args:
        access_token: Valid Google OAuth access token
        query: Optional search query for file names
        limit: Maximum number of results

    Returns:
        Dict with spreadsheets list, or error
    """
    _check_httpx()

    headers = {"Authorization": f"Bearer {access_token}"}

    q_parts = ["mimeType='application/vnd.google-apps.spreadsheet'"]
    if query:
        q_parts.append(f"name contains '{query}'")

    params = {
        "q": " and ".join(q_parts),
        "fields": "files(id,name,createdTime,modifiedTime,webViewLink)",
        "pageSize": min(limit, 100),
        "orderBy": "modifiedTime desc",
    }

    url = f"{DRIVE_API_BASE}/files?{urlencode(params)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"error": error_msg}

            data = response.json()
            files = data.get("files", [])

            return {
                "spreadsheets": [
                    {
                        "spreadsheet_id": f["id"],
                        "title": f["name"],
                        "created_at": f.get("createdTime"),
                        "modified_at": f.get("modifiedTime"),
                        "url": f.get("webViewLink", f"https://docs.google.com/spreadsheets/d/{f['id']}"),
                    }
                    for f in files
                ],
                "count": len(files),
            }

        except Exception as e:
            logger.error(f"Error listing spreadsheets: {e}")
            return {"error": str(e)}


async def read_sheet(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
) -> dict:
    """Read values from a spreadsheet range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID (or URL)
        range_notation: A1 notation (e.g., "Sheet1!A1:D10")

    Returns:
        Dict with values (2D array), or error
    """
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    encoded_range = quote(range_notation, safe='')
    url = f"{SHEETS_API_BASE}/{clean_id}/values/{encoded_range}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)

            if response.status_code == 404:
                return {"error": "Spreadsheet or range not found"}

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"error": error_msg}

            data = response.json()
            values = data.get("values", [])

            return {
                "range": data.get("range"),
                "values": values,
                "row_count": len(values),
                "col_count": max(len(row) for row in values) if values else 0,
            }

        except Exception as e:
            logger.error(f"Error reading range: {e}")
            return {"error": str(e)}


async def write_to_sheet(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    values: List[List],
) -> dict:
    """Write values to a spreadsheet range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID (or URL)
        range_notation: A1 notation (e.g., "Sheet1!A1")
        values: 2D array of values to write

    Returns:
        Dict with updated range info, or error
    """
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    encoded_range = quote(range_notation, safe='')
    url = f"{SHEETS_API_BASE}/{clean_id}/values/{encoded_range}?valueInputOption=USER_ENTERED"
    body = {"values": values}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.put(url, headers=headers, json=body)

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"error": error_msg}

            data = response.json()
            return {
                "updated_range": data.get("updatedRange"),
                "updated_rows": data.get("updatedRows"),
                "updated_columns": data.get("updatedColumns"),
                "updated_cells": data.get("updatedCells"),
            }

        except Exception as e:
            logger.error(f"Error writing range: {e}")
            return {"error": str(e)}


async def add_row_to_sheet(
    access_token: str,
    spreadsheet_id: str,
    values: List,
    sheet_name: Optional[str] = None,
) -> dict:
    """Append a single row to a spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID (or URL)
        values: List of values for the row
        sheet_name: Sheet name (defaults to first sheet)

    Returns:
        Dict with appended range info, or error
    """
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    range_notation = f"'{sheet_name}'!A:Z" if sheet_name else "A:Z"
    encoded_range = quote(range_notation, safe='')
    url = f"{SHEETS_API_BASE}/{clean_id}/values/{encoded_range}:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
    body = {"values": [values]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"error": error_msg}

            data = response.json()
            updates = data.get("updates", {})
            return {
                "updated_range": updates.get("updatedRange"),
                "updated_rows": updates.get("updatedRows"),
                "updated_cells": updates.get("updatedCells"),
            }

        except Exception as e:
            logger.error(f"Error appending row: {e}")
            return {"error": str(e)}


async def search_sheets(
    access_token: str,
    spreadsheet_id: str,
    search_text: str,
    sheet_name: Optional[str] = None,
) -> dict:
    """Search for text in a spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID (or URL)
        search_text: Text to search for
        sheet_name: Limit search to specific sheet

    Returns:
        Dict with matching cells, or error
    """
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get all sheets or specific sheet
    if sheet_name:
        range_notation = f"'{sheet_name}'"
    else:
        # First get sheet names
        meta_url = f"{SHEETS_API_BASE}/{clean_id}?fields=sheets.properties.title"
        async with httpx.AsyncClient(timeout=30.0) as client:
            meta_response = await client.get(meta_url, headers=headers)
            if meta_response.status_code != 200:
                return {"error": "Could not get spreadsheet metadata"}
            meta = meta_response.json()
            sheets = [s["properties"]["title"] for s in meta.get("sheets", [])]
            if not sheets:
                return {"matches": [], "count": 0}

    matches = []
    search_lower = search_text.lower()

    async with httpx.AsyncClient(timeout=30.0) as client:
        sheets_to_search = [sheet_name] if sheet_name else sheets

        for sname in sheets_to_search:
            encoded_range = quote(f"'{sname}'", safe='')
            url = f"{SHEETS_API_BASE}/{clean_id}/values/{encoded_range}"

            try:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    continue

                data = response.json()
                values = data.get("values", [])

                for row_idx, row in enumerate(values):
                    for col_idx, cell in enumerate(row):
                        if search_lower in str(cell).lower():
                            matches.append({
                                "sheet": sname,
                                "row": row_idx + 1,
                                "column": col_idx + 1,
                                "cell": f"{chr(65 + col_idx)}{row_idx + 1}" if col_idx < 26 else f"Col{col_idx + 1}",
                                "value": str(cell),
                            })

            except Exception as e:
                logger.warning(f"Error searching sheet {sname}: {e}")

    return {"matches": matches, "count": len(matches), "search_text": search_text}


async def clear_range(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
) -> dict:
    """Clear values from a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID (or URL)
        range_notation: A1 notation range to clear

    Returns:
        Dict with cleared range info, or error
    """
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    encoded_range = quote(range_notation, safe='')
    url = f"{SHEETS_API_BASE}/{clean_id}/values/{encoded_range}:clear"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json={})

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"error": error_msg}

            data = response.json()
            return {
                "cleared_range": data.get("clearedRange"),
                "spreadsheet_id": data.get("spreadsheetId"),
            }

        except Exception as e:
            logger.error(f"Error clearing range: {e}")
            return {"error": str(e)}
