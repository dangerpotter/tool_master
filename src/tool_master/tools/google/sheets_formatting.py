"""Sheet formatting operations: text, colors, borders, alignment, merging."""

import logging
from typing import Optional

from tool_master.tools.google._sheets_utils import (
    extract_spreadsheet_id,
    get_sheet_id,
    batch_update,
    parse_a1_range,
    parse_color,
    build_grid_range,
)

logger = logging.getLogger(__name__)


async def format_columns(
    access_token: str,
    spreadsheet_id: str,
    columns: str,
    format_type: str,
    pattern: Optional[str] = None,
    sheet_name: Optional[str] = None,
) -> dict:
    """Apply number/date formatting to columns.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        columns: Column range (e.g., 'B' or 'B:D')
        format_type: One of: number, currency, percent, date, datetime, text
        pattern: Custom format pattern (optional)
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Dict with success status, or error
    """
    from tool_master.tools.google._sheets_utils import parse_column_range

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    sheet_id = await get_sheet_id(access_token, clean_id, sheet_name)
    if sheet_id is None:
        return {"error": "Sheet not found"}

    start_col, end_col = parse_column_range(columns)

    # Determine format pattern
    FORMAT_PATTERNS = {
        "number": "#,##0.00",
        "currency": "$#,##0.00",
        "percent": "0.00%",
        "date": "yyyy-mm-dd",
        "datetime": "yyyy-mm-dd hh:mm:ss",
        "text": "@",
    }
    actual_pattern = pattern or FORMAT_PATTERNS.get(format_type, "@")

    requests = [{
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col,
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {"type": "NUMBER", "pattern": actual_pattern}
                }
            },
            "fields": "userEnteredFormat.numberFormat",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Applied {format_type} format to columns {columns}"}


async def set_text_format(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    underline: Optional[bool] = None,
    strikethrough: Optional[bool] = None,
    font_family: Optional[str] = None,
    font_size: Optional[int] = None,
) -> dict:
    """Apply text formatting to a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range in A1 notation
        bold, italic, underline, strikethrough: Boolean formatting options
        font_family: Font name (e.g., 'Arial')
        font_size: Font size in points

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    text_format = {}
    fields = []

    if bold is not None:
        text_format["bold"] = bold
        fields.append("userEnteredFormat.textFormat.bold")
    if italic is not None:
        text_format["italic"] = italic
        fields.append("userEnteredFormat.textFormat.italic")
    if underline is not None:
        text_format["underline"] = underline
        fields.append("userEnteredFormat.textFormat.underline")
    if strikethrough is not None:
        text_format["strikethrough"] = strikethrough
        fields.append("userEnteredFormat.textFormat.strikethrough")
    if font_family:
        text_format["fontFamily"] = font_family
        fields.append("userEnteredFormat.textFormat.fontFamily")
    if font_size:
        text_format["fontSize"] = font_size
        fields.append("userEnteredFormat.textFormat.fontSize")

    if not fields:
        return {"error": "No formatting options specified"}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "repeatCell": {
            "range": grid_range,
            "cell": {"userEnteredFormat": {"textFormat": text_format}},
            "fields": ",".join(fields),
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Applied text formatting to {range_notation}"}


async def set_text_color(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    color: str,
) -> dict:
    """Set text (foreground) color for a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range in A1 notation
        color: Color as hex (#FF0000) or name (red)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    rgb = parse_color(color)
    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "repeatCell": {
            "range": grid_range,
            "cell": {"userEnteredFormat": {"textFormat": {"foregroundColor": rgb}}},
            "fields": "userEnteredFormat.textFormat.foregroundColor",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Set text color to {color} on {range_notation}"}


async def set_background_color(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    color: str,
) -> dict:
    """Set background (fill) color for a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range in A1 notation
        color: Color as hex (#FFFF00) or name (yellow)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    rgb = parse_color(color)
    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "repeatCell": {
            "range": grid_range,
            "cell": {"userEnteredFormat": {"backgroundColor": rgb}},
            "fields": "userEnteredFormat.backgroundColor",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Set background color to {color} on {range_notation}"}


async def set_alignment(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    horizontal: Optional[str] = None,
    vertical: Optional[str] = None,
    wrap: Optional[str] = None,
) -> dict:
    """Set text alignment and wrapping for a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range in A1 notation
        horizontal: left, center, or right
        vertical: top, middle, or bottom
        wrap: overflow, clip, or wrap

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    format_obj = {}
    fields = []

    if horizontal:
        format_obj["horizontalAlignment"] = horizontal.upper()
        fields.append("userEnteredFormat.horizontalAlignment")
    if vertical:
        format_obj["verticalAlignment"] = vertical.upper()
        fields.append("userEnteredFormat.verticalAlignment")
    if wrap:
        wrap_map = {"overflow": "OVERFLOW_CELL", "clip": "CLIP", "wrap": "WRAP"}
        format_obj["wrapStrategy"] = wrap_map.get(wrap.lower(), "OVERFLOW_CELL")
        fields.append("userEnteredFormat.wrapStrategy")

    if not fields:
        return {"error": "No alignment options specified"}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "repeatCell": {
            "range": grid_range,
            "cell": {"userEnteredFormat": format_obj},
            "fields": ",".join(fields),
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Set alignment on {range_notation}"}


async def set_borders(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    border_style: str = "solid",
    color: str = "black",
    sides: str = "all",
) -> dict:
    """Add borders to cells.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range in A1 notation
        border_style: solid, dashed, dotted, double, thick, medium, none
        color: Border color
        sides: all, outer, inner, top, bottom, left, right

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    style_map = {
        "solid": "SOLID",
        "dashed": "DASHED",
        "dotted": "DOTTED",
        "double": "DOUBLE",
        "thick": "SOLID_THICK",
        "medium": "SOLID_MEDIUM",
        "none": "NONE",
    }
    api_style = style_map.get(border_style.lower(), "SOLID")
    rgb = parse_color(color)

    border_spec = {"style": api_style, "color": rgb} if api_style != "NONE" else {"style": "NONE"}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    update_borders = {"range": grid_range}

    if sides == "all":
        update_borders.update({
            "top": border_spec, "bottom": border_spec,
            "left": border_spec, "right": border_spec,
            "innerHorizontal": border_spec, "innerVertical": border_spec,
        })
    elif sides == "outer":
        update_borders.update({
            "top": border_spec, "bottom": border_spec,
            "left": border_spec, "right": border_spec,
        })
    elif sides == "inner":
        update_borders.update({
            "innerHorizontal": border_spec, "innerVertical": border_spec,
        })
    else:
        update_borders[sides] = border_spec

    requests = [{"updateBorders": update_borders}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Set {sides} borders on {range_notation}"}


async def merge_cells(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    merge_type: str = "all",
) -> dict:
    """Merge cells in a range.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to merge
        merge_type: all, horizontal (merge rows), or vertical (merge columns)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(range_notation)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    type_map = {
        "all": "MERGE_ALL",
        "horizontal": "MERGE_ROWS",
        "vertical": "MERGE_COLUMNS",
    }

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    requests = [{
        "mergeCells": {
            "range": grid_range,
            "mergeType": type_map.get(merge_type.lower(), "MERGE_ALL"),
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Merged cells in {range_notation}"}


async def unmerge_cells(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
) -> dict:
    """Unmerge previously merged cells.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to unmerge

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

    requests = [{"unmergeCells": {"range": grid_range}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Unmerged cells in {range_notation}"}


async def alternating_colors(
    access_token: str,
    spreadsheet_id: str,
    range_notation: str,
    header_color: str = "blue",
    first_band_color: str = "white",
    second_band_color: str = "lightgray",
) -> dict:
    """Apply alternating row colors (zebra stripes).

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        range_notation: Range to apply banding
        header_color: Color for header row
        first_band_color: Color for odd data rows
        second_band_color: Color for even data rows

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

    requests = [{
        "addBanding": {
            "bandedRange": {
                "range": grid_range,
                "rowProperties": {
                    "headerColor": parse_color(header_color),
                    "firstBandColor": parse_color(first_band_color),
                    "secondBandColor": parse_color(second_band_color),
                },
            }
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Applied alternating colors to {range_notation}"}


async def add_note(
    access_token: str,
    spreadsheet_id: str,
    cell: str,
    note: str,
) -> dict:
    """Add a note (comment) to a cell.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        cell: Cell in A1 notation (e.g., 'B2')
        note: Note text (empty string to clear)

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(cell)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("start_row") + 1 if parsed.get("start_row") is not None else None,
        parsed.get("start_col"),
        parsed.get("start_col") + 1 if parsed.get("start_col") is not None else None,
    )

    requests = [{
        "repeatCell": {
            "range": grid_range,
            "cell": {"note": note},
            "fields": "note",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    action = "Added note to" if note else "Cleared note from"
    return {"success": True, "message": f"{action} {cell}"}
