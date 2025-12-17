"""Named ranges and protection operations for Google Sheets."""

import logging
from typing import Optional, List

from tool_master.tools.google._sheets_utils import (
    extract_spreadsheet_id,
    get_sheet_id,
    batch_update,
    parse_a1_range,
    build_grid_range,
    SHEETS_API_BASE,
    _check_httpx,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Named Ranges
# =============================================================================

async def create_named_range(
    access_token: str,
    spreadsheet_id: str,
    name: str,
    range_notation: str,
) -> dict:
    """Create a named range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        name: Name for the range (letters, numbers, underscores)
        range_notation: Range in A1 notation

    Returns:
        Dict with named range ID, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "addNamedRange": {
            "namedRange": {
                "name": name,
                "range": grid_range,
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    nr_id = result.get("replies", [{}])[0].get("addNamedRange", {}).get("namedRange", {}).get("namedRangeId")
    return {"success": True, "named_range_id": nr_id, "message": f"Created named range '{name}'"}


async def list_named_ranges(access_token: str, spreadsheet_id: str) -> dict:
    """List all named ranges.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID

    Returns:
        Dict with named ranges list, or error
    """
    import httpx
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{clean_id}?fields=namedRanges"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to get named ranges"}

        data = response.json()
        ranges = []
        for nr in data.get("namedRanges", []):
            ranges.append({
                "named_range_id": nr.get("namedRangeId"),
                "name": nr.get("name"),
                "range": nr.get("range"),
            })

        return {"named_ranges": ranges, "count": len(ranges)}


async def delete_named_range(
    access_token: str,
    spreadsheet_id: str,
    named_range_id: str,
) -> dict:
    """Delete a named range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        named_range_id: Named range ID to delete

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    requests = [{"deleteNamedRange": {"namedRangeId": named_range_id}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": "Deleted named range"}


# =============================================================================
# Protected Ranges
# =============================================================================

async def protect_range(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    description: Optional[str] = None,
    warning_only: bool = False,
) -> dict:
    """Protect a range of cells.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to protect
        description: Description of why it's protected
        warning_only: If True, show warning but allow editing

    Returns:
        Dict with protected range ID, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    protected_range = {"range": grid_range, "warningOnly": warning_only}
    if description:
        protected_range["description"] = description

    requests = [{"addProtectedRange": {"protectedRange": protected_range}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    pr_id = result.get("replies", [{}])[0].get("addProtectedRange", {}).get("protectedRange", {}).get("protectedRangeId")
    return {"success": True, "protected_range_id": pr_id, "message": f"Protected {range_notation}"}


async def list_protected_ranges(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
) -> dict:
    """List all protected ranges.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Filter by sheet (optional)

    Returns:
        Dict with protected ranges list, or error
    """
    import httpx
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{clean_id}?fields=sheets(properties,protectedRanges)"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to get protected ranges"}

        data = response.json()
        protections = []

        for sheet in data.get("sheets", []):
            sname = sheet.get("properties", {}).get("title")
            if sheet_name and sname != sheet_name:
                continue

            for pr in sheet.get("protectedRanges", []):
                protections.append({
                    "protected_range_id": pr.get("protectedRangeId"),
                    "description": pr.get("description", ""),
                    "warning_only": pr.get("warningOnly", False),
                    "sheet": sname,
                    "range": pr.get("range"),
                })

        return {"protected_ranges": protections, "count": len(protections)}


async def update_protected_range(
    access_token: str,
    spreadsheet_id: str,
    protected_range_id: int,
    description: Optional[str] = None,
    warning_only: Optional[bool] = None,
    editors: Optional[List[str]] = None,
) -> dict:
    """Update a protected range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        protected_range_id: ID of protected range to update
        description: New description
        warning_only: Change warning/lock mode
        editors: List of email addresses who can edit

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)

    update = {"protectedRangeId": protected_range_id}
    fields = []

    if description is not None:
        update["description"] = description
        fields.append("description")
    if warning_only is not None:
        update["warningOnly"] = warning_only
        fields.append("warningOnly")
    if editors is not None:
        update["editors"] = {"users": editors}
        fields.append("editors")

    if not fields:
        return {"error": "No updates specified"}

    requests = [{
        "updateProtectedRange": {
            "protectedRange": update,
            "fields": ",".join(fields),
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Updated protected range {protected_range_id}"}


async def delete_protected_range(
    access_token: str,
    spreadsheet_id: str,
    protected_range_id: int,
) -> dict:
    """Remove protection from a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        protected_range_id: ID of protected range to delete

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    requests = [{"deleteProtectedRange": {"protectedRangeId": protected_range_id}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Removed protection from range {protected_range_id}"}


async def protect_sheet(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    description: Optional[str] = None,
    warning_only: bool = False,
    editors: Optional[List[str]] = None,
    unprotected_ranges: Optional[List[str]] = None,
) -> dict:
    """Protect an entire sheet with optional unprotected ranges.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Sheet to protect
        description: Description
        warning_only: If True, show warning but allow editing
        editors: Email addresses who can edit protected areas
        unprotected_ranges: List of A1 ranges that remain editable

    Returns:
        Dict with protected range ID, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": f"Sheet '{sheet_name}' not found"}

    protected_range = {
        "sheetId": sheet_id,
        "warningOnly": warning_only,
    }

    if description:
        protected_range["description"] = description

    if editors:
        protected_range["editors"] = {"users": editors}

    if unprotected_ranges:
        unprotected = []
        for r in unprotected_ranges:
            parsed = parse_a1_range(r)
            unprotected.append(build_grid_range(
                sheet_id,
                parsed.get("start_row"),
                parsed.get("end_row"),
                parsed.get("start_col"),
                parsed.get("end_col"),
            ))
        protected_range["unprotectedRanges"] = unprotected

    requests = [{"addProtectedRange": {"protectedRange": protected_range}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    pr_id = result.get("replies", [{}])[0].get("addProtectedRange", {}).get("protectedRange", {}).get("protectedRangeId")
    return {"success": True, "protected_range_id": pr_id, "message": f"Protected sheet '{sheet_name}'"}
