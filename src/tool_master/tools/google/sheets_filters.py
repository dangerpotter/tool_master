"""Filter and validation operations for Google Sheets."""

import logging
from typing import Optional, List

from tool_master.tools.google._sheets_utils import (
    extract_spreadsheet_id,
    get_sheet_id,
    batch_update,
    parse_a1_range,
    build_grid_range,
    parse_color,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Basic Filters
# =============================================================================

async def set_basic_filter(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
) -> dict:
    """Enable auto-filter dropdowns on a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to filter (include header row)

    Returns:
        Dict with success status, or error
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

    requests = [{"setBasicFilter": {"filter": {"range": grid_range}}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Enabled filter on {range_notation}"}


async def clear_basic_filter(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
) -> dict:
    """Remove basic filter from a sheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{"clearBasicFilter": {"sheetId": sheet_id}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": "Cleared filter"}


# =============================================================================
# Filter Views
# =============================================================================

async def create_filter_view(
    access_token: str,
    spreadsheet_id: str,
    title: str,
    range_notation: str,
) -> dict:
    """Create a named filter view.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        title: Name for the filter view
        range_notation: Range for the filter view

    Returns:
        Dict with filter view ID, or error
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
        "addFilterView": {
            "filter": {
                "title": title,
                "range": grid_range,
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    fv_id = result.get("replies", [{}])[0].get("addFilterView", {}).get("filter", {}).get("filterViewId")
    return {"success": True, "filter_view_id": fv_id, "message": f"Created filter view '{title}'"}


async def delete_filter_view(
    access_token: str,
    spreadsheet_id: str,
    filter_view_id: int,
) -> dict:
    """Delete a filter view.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        filter_view_id: Filter view ID to delete

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    requests = [{"deleteFilterView": {"filterId": filter_view_id}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Deleted filter view {filter_view_id}"}


async def list_filter_views(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
) -> dict:
    """List all filter views.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Filter by sheet (optional)

    Returns:
        Dict with filter views list, or error
    """
    from tool_master.tools.google._sheets_utils import SHEETS_API_BASE, _check_httpx
    import httpx

    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{clean_id}?fields=sheets(properties,filterViews)"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to get filter views"}

        data = response.json()
        views = []

        for sheet in data.get("sheets", []):
            sname = sheet.get("properties", {}).get("title")
            if sheet_name and sname != sheet_name:
                continue

            for fv in sheet.get("filterViews", []):
                views.append({
                    "filter_view_id": fv.get("filterViewId"),
                    "title": fv.get("title"),
                    "sheet": sname,
                })

        return {"filter_views": views, "count": len(views)}


# =============================================================================
# Conditional Formatting
# =============================================================================

async def conditional_format(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    rule_type: str,
    condition_value: Optional[str] = None,
    format_type: str = "background",
    color: str = "red",
) -> dict:
    """Add conditional formatting to a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to format
        rule_type: greater_than, less_than, equals, contains, not_empty, is_empty
        condition_value: Value to compare against
        format_type: background or text
        color: Color to apply

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    # Build condition
    condition_type_map = {
        "greater_than": "NUMBER_GREATER",
        "less_than": "NUMBER_LESS",
        "equals": "NUMBER_EQ",
        "contains": "TEXT_CONTAINS",
        "not_empty": "NOT_BLANK",
        "is_empty": "BLANK",
    }

    bool_condition = {"type": condition_type_map.get(rule_type, "NUMBER_GREATER")}
    if condition_value and rule_type not in ("not_empty", "is_empty"):
        bool_condition["values"] = [{"userEnteredValue": condition_value}]

    # Build format
    rgb = parse_color(color)
    cell_format = {}
    if format_type == "background":
        cell_format["backgroundColor"] = rgb
    else:
        cell_format["textFormat"] = {"foregroundColor": rgb}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [grid_range],
                "booleanRule": {
                    "condition": bool_condition,
                    "format": cell_format,
                },
            },
            "index": 0,
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Added conditional formatting to {range_notation}"}


# =============================================================================
# Data Validation
# =============================================================================

async def data_validation(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    validation_type: str,
    values: Optional[List[str]] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    strict: bool = True,
) -> dict:
    """Add data validation to a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to validate
        validation_type: dropdown, number_range, date, checkbox
        values: List of allowed values (for dropdown)
        min_value, max_value: Range bounds (for number_range)
        strict: If True, reject invalid input

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    # Build validation rule
    if validation_type == "dropdown":
        if not values:
            return {"error": "values required for dropdown validation"}
        condition = {
            "type": "ONE_OF_LIST",
            "values": [{"userEnteredValue": v} for v in values],
        }
    elif validation_type == "number_range":
        if min_value is not None and max_value is not None:
            condition = {
                "type": "NUMBER_BETWEEN",
                "values": [
                    {"userEnteredValue": str(min_value)},
                    {"userEnteredValue": str(max_value)},
                ],
            }
        elif min_value is not None:
            condition = {
                "type": "NUMBER_GREATER_THAN_EQ",
                "values": [{"userEnteredValue": str(min_value)}],
            }
        elif max_value is not None:
            condition = {
                "type": "NUMBER_LESS_THAN_EQ",
                "values": [{"userEnteredValue": str(max_value)}],
            }
        else:
            return {"error": "min_value and/or max_value required for number_range"}
    elif validation_type == "date":
        condition = {"type": "DATE_IS_VALID"}
    elif validation_type == "checkbox":
        condition = {"type": "BOOLEAN"}
    else:
        return {"error": f"Unknown validation_type: {validation_type}"}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "setDataValidation": {
            "range": grid_range,
            "rule": {
                "condition": condition,
                "strict": strict,
                "showCustomUi": validation_type == "dropdown",
            },
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Added {validation_type} validation to {range_notation}"}
