"""Sheet structure operations: rows, columns, sheet tabs."""

import logging
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from tool_master.tools.google._sheets_utils import (
    SHEETS_API_BASE,
    extract_spreadsheet_id,
    get_sheet_id,
    batch_update,
    parse_column_range,
    parse_row_range,
    _check_httpx,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Sheet Tab Management
# =============================================================================

async def add_sheet(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    rows: int = 1000,
    cols: int = 26,
) -> dict:
    """Add a new sheet tab to the spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Name for the new sheet
        rows: Number of rows (default 1000)
        cols: Number of columns (default 26)

    Returns:
        Dict with new sheet info, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    requests = [{
        "addSheet": {
            "properties": {
                "title": sheet_name,
                "gridProperties": {"rowCount": rows, "columnCount": cols},
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    replies = result.get("replies", [{}])
    props = replies[0].get("addSheet", {}).get("properties", {})

    return {
        "sheet_id": props.get("sheetId"),
        "title": props.get("title"),
        "index": props.get("index"),
        "message": f"Created sheet '{sheet_name}'",
    }


async def delete_sheet(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
) -> dict:
    """Delete a sheet tab from the spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Name of sheet to delete

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": f"Sheet '{sheet_name}' not found"}

    requests = [{"deleteSheet": {"sheetId": sheet_id}}]
    result = await batch_update(access_token, clean_id, requests)

    if "error" in result:
        return result

    return {"success": True, "message": f"Deleted sheet '{sheet_name}'"}


async def rename_sheet(
    access_token: str,
    spreadsheet_id: str,
    old_name: str,
    new_name: str,
) -> dict:
    """Rename a sheet tab.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        old_name: Current sheet name
        new_name: New sheet name

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, old_name)

    if sheet_id is None:
        return {"error": f"Sheet '{old_name}' not found"}

    requests = [{
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "title": new_name},
            "fields": "title",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Renamed '{old_name}' to '{new_name}'"}


# =============================================================================
# Row Operations
# =============================================================================

async def insert_rows(
    access_token: str,
    spreadsheet_id: str,
    start_row: int,
    num_rows: int = 1,
    sheet_name: Optional[str] = None,
) -> dict:
    """Insert empty rows at a position.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        start_row: Row number (1-indexed) where rows will be inserted
        num_rows: Number of rows to insert
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{
        "insertDimension": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": start_row - 1,  # 0-indexed
                "endIndex": start_row - 1 + num_rows,
            },
            "inheritFromBefore": start_row > 1,
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Inserted {num_rows} row(s) at row {start_row}"}


async def delete_rows(
    access_token: str,
    spreadsheet_id: str,
    start_row: int,
    end_row: int,
    sheet_name: Optional[str] = None,
) -> dict:
    """Delete rows from the spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        start_row: First row to delete (1-indexed)
        end_row: Last row to delete (inclusive)
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{
        "deleteDimension": {
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

    count = end_row - start_row + 1
    return {"success": True, "message": f"Deleted {count} row(s)"}


# =============================================================================
# Column Operations
# =============================================================================

async def insert_columns(
    access_token: str,
    spreadsheet_id: str,
    start_column: str,
    num_columns: int = 1,
    sheet_name: Optional[str] = None,
) -> dict:
    """Insert empty columns at a position.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        start_column: Column letter (e.g., 'B') where columns will be inserted
        num_columns: Number of columns to insert
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    start_idx, _ = parse_column_range(start_column)

    requests = [{
        "insertDimension": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": start_idx,
                "endIndex": start_idx + num_columns,
            },
            "inheritFromBefore": start_idx > 0,
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Inserted {num_columns} column(s) at column {start_column}"}


async def delete_columns(
    access_token: str,
    spreadsheet_id: str,
    start_column: str,
    end_column: str,
    sheet_name: Optional[str] = None,
) -> dict:
    """Delete columns from the spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        start_column: First column to delete (e.g., 'B')
        end_column: Last column to delete (e.g., 'D')
        sheet_name: Sheet name (uses first sheet if None)

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
        "deleteDimension": {
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

    return {"success": True, "message": f"Deleted columns {start_column} to {end_column}"}


# =============================================================================
# Freeze & Resize
# =============================================================================

async def freeze_rows(
    access_token: str,
    spreadsheet_id: str,
    num_rows: int,
    sheet_name: Optional[str] = None,
) -> dict:
    """Freeze rows at the top of the sheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        num_rows: Number of rows to freeze (0 to unfreeze)
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": num_rows},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Froze {num_rows} row(s)"}


async def freeze_columns(
    access_token: str,
    spreadsheet_id: str,
    num_columns: int,
    sheet_name: Optional[str] = None,
) -> dict:
    """Freeze columns at the left of the sheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        num_columns: Number of columns to freeze (0 to unfreeze)
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)

    if sheet_id is None:
        return {"error": "Sheet not found"}

    requests = [{
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenColumnCount": num_columns},
            },
            "fields": "gridProperties.frozenColumnCount",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Froze {num_columns} column(s)"}


async def auto_resize_columns(
    access_token: str,
    spreadsheet_id: str,
    start_column: str,
    end_column: str,
    sheet_name: Optional[str] = None,
) -> dict:
    """Auto-resize columns to fit content.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        start_column: First column (e.g., 'A')
        end_column: Last column (e.g., 'D')
        sheet_name: Sheet name (uses first sheet if None)

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
        "autoResizeDimensions": {
            "dimensions": {
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

    return {"success": True, "message": f"Auto-resized columns {start_column} to {end_column}"}


async def sort_range(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    sort_column: int,
    ascending: bool = True,
) -> dict:
    """Sort a range by a column.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to sort (e.g., 'A1:D100')
        sort_column: Column index to sort by (0-based within the range)
        ascending: True for A-Z/0-9, False for Z-A/9-0

    Returns:
        Dict with success status, or error
    """
    from tool_master.tools.google._sheets_utils import parse_a1_range, build_grid_range

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
        "sortRange": {
            "range": grid_range,
            "sortSpecs": [{
                "dimensionIndex": sort_column,
                "sortOrder": "ASCENDING" if ascending else "DESCENDING",
            }],
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Sorted {range_notation}"}
