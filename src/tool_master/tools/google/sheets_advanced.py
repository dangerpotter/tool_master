"""Advanced operations: groups, slicers, tables, find/replace, copy/paste, metadata."""

import logging
from typing import Optional, List

from tool_master.tools.google._sheets_utils import (
    extract_spreadsheet_id,
    get_sheet_id,
    batch_update,
    parse_a1_range,
    parse_column_range,
    build_grid_range,
    parse_color,
    SHEETS_API_BASE,
    _check_httpx,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Row/Column Groups
# =============================================================================

async def create_row_group(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    start_row: int,
    end_row: int,
) -> dict:
    """Create a collapsible row group.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Sheet name
        start_row: First row (1-indexed)
        end_row: Last row (inclusive)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{
        "addDimensionGroup": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": start_row - 1,
                "endIndex": end_row,
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Created row group {start_row}-{end_row}"}


async def create_column_group(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    start_column: str,
    end_column: str,
) -> dict:
    """Create a collapsible column group.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Sheet name
        start_column: First column (e.g., 'B')
        end_column: Last column (e.g., 'D')

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    start_idx, _ = parse_column_range(start_column)
    _, end_idx = parse_column_range(end_column)

    requests = [{
        "addDimensionGroup": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": start_idx,
                "endIndex": end_idx,
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Created column group {start_column}-{end_column}"}


async def delete_row_group(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    start_row: int,
    end_row: int,
) -> dict:
    """Delete a row group."""
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{
        "deleteDimensionGroup": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": start_row - 1,
                "endIndex": end_row,
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Deleted row group {start_row}-{end_row}"}


async def delete_column_group(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    start_column: str,
    end_column: str,
) -> dict:
    """Delete a column group."""
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    start_idx, _ = parse_column_range(start_column)
    _, end_idx = parse_column_range(end_column)

    requests = [{
        "deleteDimensionGroup": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": start_idx,
                "endIndex": end_idx,
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Deleted column group {start_column}-{end_column}"}


# =============================================================================
# Find/Replace & Copy/Paste
# =============================================================================

async def find_replace(
    access_token: str,
    spreadsheet_id: str,
    find: str,
    replacement: str,
    range_notation: Optional[str] = None,
    match_case: bool = False,
    match_entire_cell: bool = False,
) -> dict:
    """Find and replace text in a spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        find: Text to search for
        replacement: Text to replace with
        range_notation: Limit search to range (optional)
        match_case: Case-sensitive search
        match_entire_cell: Only match entire cell content

    Returns:
        Dict with replacement count, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)

    request = {
        "find": find,
        "replacement": replacement,
        "matchCase": match_case,
        "matchEntireCell": match_entire_cell,
        "allSheets": range_notation is None,
    }

    if range_notation:
        parsed = parse_a1_range(range_notation)
        sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))
        if sheet_id is None:
            return {"error": "Sheet not found"}

        request["range"] = build_grid_range(
            sheet_id,
            parsed.get("start_row"),
            parsed.get("end_row"),
            parsed.get("start_col"),
            parsed.get("end_col"),
        )

    requests = [{"findReplace": request}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    fr_result = result.get("replies", [{}])[0].get("findReplace", {})
    return {
        "success": True,
        "occurrences_changed": fr_result.get("occurrencesChanged", 0),
        "rows_changed": fr_result.get("rowsChanged", 0),
        "sheets_changed": fr_result.get("sheetsChanged", 0),
    }


async def copy_paste(
    access_token: str,
    spreadsheet_id: str,
    source_range: str,
    destination_range: str,
    paste_type: str = "all",
) -> dict:
    """Copy cells from one location to another.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        source_range: Source range in A1 notation
        destination_range: Destination range
        paste_type: all, values, or format

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    src = parse_a1_range(source_range)
    dst = parse_a1_range(destination_range)

    src_sheet_id = await get_sheet_id(access_token, clean_id, src.get("sheet_name"))
    dst_sheet_id = await get_sheet_id(access_token, clean_id, dst.get("sheet_name"))

    if src_sheet_id is None or dst_sheet_id is None:
        return {"error": "Sheet not found"}

    paste_type_map = {
        "all": "PASTE_NORMAL",
        "values": "PASTE_VALUES",
        "format": "PASTE_FORMAT",
    }

    requests = [{
        "copyPaste": {
            "source": build_grid_range(
                src_sheet_id,
                src.get("start_row"),
                src.get("end_row"),
                src.get("start_col"),
                src.get("end_col"),
            ),
            "destination": build_grid_range(
                dst_sheet_id,
                dst.get("start_row"),
                dst.get("end_row"),
                dst.get("start_col"),
                dst.get("end_col"),
            ),
            "pasteType": paste_type_map.get(paste_type, "PASTE_NORMAL"),
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Copied {source_range} to {destination_range}"}


async def cut_paste(
    access_token: str,
    spreadsheet_id: str,
    source_range: str,
    destination: str,
) -> dict:
    """Move cells from one location to another.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        source_range: Source range in A1 notation
        destination: Destination cell (top-left corner)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    src = parse_a1_range(source_range)
    dst = parse_a1_range(destination)

    src_sheet_id = await get_sheet_id(access_token, clean_id, src.get("sheet_name"))
    dst_sheet_id = await get_sheet_id(access_token, clean_id, dst.get("sheet_name"))

    if src_sheet_id is None or dst_sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{
        "cutPaste": {
            "source": build_grid_range(
                src_sheet_id,
                src.get("start_row"),
                src.get("end_row"),
                src.get("start_col"),
                src.get("end_col"),
            ),
            "destination": {
                "sheetId": dst_sheet_id,
                "rowIndex": dst.get("start_row", 0),
                "columnIndex": dst.get("start_col", 0),
            },
            "pasteType": "PASTE_NORMAL",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Moved {source_range} to {destination}"}


# =============================================================================
# Sheet Properties
# =============================================================================

async def hide_sheet(access_token: str, spreadsheet_id: str, sheet_name: str) -> dict:
    """Hide a sheet tab."""
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": f"Sheet '{sheet_name}' not found"}

    requests = [{
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "hidden": True},
            "fields": "hidden",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Hid sheet '{sheet_name}'"}


async def show_sheet(access_token: str, spreadsheet_id: str, sheet_name: str) -> dict:
    """Show a hidden sheet tab."""
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": f"Sheet '{sheet_name}' not found"}

    requests = [{
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "hidden": False},
            "fields": "hidden",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Showed sheet '{sheet_name}'"}


async def set_tab_color(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    color: str,
) -> dict:
    """Set the color of a sheet tab."""
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": f"Sheet '{sheet_name}' not found"}

    requests = [{
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "tabColor": parse_color(color)},
            "fields": "tabColor",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Set tab color for '{sheet_name}'"}


async def add_hyperlink(
    access_token: str,
    spreadsheet_id: str,
    cell: str,
    url: str,
    display_text: Optional[str] = None,
) -> dict:
    """Add a hyperlink to a cell."""
    from urllib.parse import quote

    clean_id = extract_spreadsheet_id(spreadsheet_id)

    # Use HYPERLINK formula
    text = display_text or url
    formula = f'=HYPERLINK("{url}","{text}")'

    parsed = parse_a1_range(cell)
    sheet_name = parsed.get("sheet_name")
    range_notation = f"'{sheet_name}'!{cell}" if sheet_name and "!" not in cell else cell

    from tool_master.tools.google.sheets_core import write_to_sheet
    return await write_to_sheet(access_token, spreadsheet_id, range_notation, [[formula]])


# =============================================================================
# Slicers
# =============================================================================

async def list_slicers(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
) -> dict:
    """List all slicers in a spreadsheet."""
    import httpx
    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{clean_id}?fields=sheets(properties,slicers)"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to get slicers"}

        data = response.json()
        slicers = []

        for sheet in data.get("sheets", []):
            sname = sheet.get("properties", {}).get("title")
            if sheet_name and sname != sheet_name:
                continue

            for slicer in sheet.get("slicers", []):
                spec = slicer.get("spec", {})
                slicers.append({
                    "slicer_id": slicer.get("slicerId"),
                    "title": spec.get("title", "(No title)"),
                    "sheet": sname,
                    "column_index": spec.get("columnIndex"),
                })

        return {"slicers": slicers, "count": len(slicers)}


async def create_slicer(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    data_range: str,
    column_index: int,
    title: Optional[str] = None,
    anchor_row: int = 0,
    anchor_col: int = 0,
) -> dict:
    """Create a slicer widget for filtering."""
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(data_range)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    slicer_spec = {
        "dataRange": build_grid_range(
            sheet_id,
            parsed.get("start_row"),
            parsed.get("end_row"),
            parsed.get("start_col"),
            parsed.get("end_col"),
        ),
        "columnIndex": column_index,
    }
    if title:
        slicer_spec["title"] = title

    requests = [{
        "addSlicer": {
            "slicer": {
                "spec": slicer_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sheet_id,
                            "rowIndex": anchor_row,
                            "columnIndex": anchor_col,
                        }
                    }
                },
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    slicer_id = result.get("replies", [{}])[0].get("addSlicer", {}).get("slicer", {}).get("slicerId")
    return {"success": True, "slicer_id": slicer_id, "message": "Created slicer"}


async def delete_slicer(access_token: str, spreadsheet_id: str, slicer_id: int) -> dict:
    """Delete a slicer."""
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    requests = [{"deleteSlicer": {"slicerId": slicer_id}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Deleted slicer {slicer_id}"}
