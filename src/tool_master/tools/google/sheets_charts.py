"""Chart and pivot table operations for Google Sheets."""

import logging
from typing import Optional, List

from tool_master.tools.google._sheets_utils import (
    extract_spreadsheet_id,
    get_sheet_id,
    get_spreadsheet_metadata,
    batch_update,
    parse_a1_range,
    build_grid_range,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Charts
# =============================================================================

async def create_chart(
    access_token: str,
    spreadsheet_id: str,
    data_range: str,
    chart_type: str = "column",
    title: Optional[str] = None,
    anchor_cell: str = "F1",
    legend_position: str = "bottom",
) -> dict:
    """Create an embedded chart.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        data_range: Data range in A1 notation
        chart_type: bar, line, column, pie, area, scatter
        title: Chart title
        anchor_cell: Cell where chart is placed
        legend_position: bottom, top, left, right, none

    Returns:
        Dict with chart info, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(data_range)
    anchor_parsed = parse_a1_range(anchor_cell)
    sheet_id = await get_sheet_id(access_token, clean_id, parsed.get("sheet_name"))

    if sheet_id is None:
        return {"error": "Sheet not found"}

    type_map = {
        "bar": "BAR",
        "line": "LINE",
        "column": "COLUMN",
        "pie": "PIE",
        "area": "AREA",
        "scatter": "SCATTER",
    }
    api_type = type_map.get(chart_type.lower(), "COLUMN")

    legend_map = {
        "bottom": "BOTTOM_LEGEND",
        "top": "TOP_LEGEND",
        "left": "LEFT_LEGEND",
        "right": "RIGHT_LEGEND",
        "none": "NO_LEGEND",
    }

    grid_range = build_grid_range(
        sheet_id,
        parsed.get("start_row"),
        parsed.get("end_row"),
        parsed.get("start_col"),
        parsed.get("end_col"),
    )

    chart_spec = {
        "basicChart": {
            "chartType": api_type,
            "legendPosition": legend_map.get(legend_position, "BOTTOM_LEGEND"),
            "domains": [{"domain": {"sourceRange": {"sources": [grid_range]}}}],
            "series": [{"series": {"sourceRange": {"sources": [grid_range]}}}],
        }
    }

    if title:
        chart_spec["title"] = title

    anchor_row = anchor_parsed.get("start_row", 0)
    anchor_col = anchor_parsed.get("start_col", 5)

    requests = [{
        "addChart": {
            "chart": {
                "spec": chart_spec,
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

    chart_id = result.get("replies", [{}])[0].get("addChart", {}).get("chart", {}).get("chartId")
    return {"success": True, "chart_id": chart_id, "message": f"Created {chart_type} chart"}


async def list_charts(access_token: str, spreadsheet_id: str) -> dict:
    """List all charts in a spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID

    Returns:
        Dict with charts list, or error
    """
    meta = await get_spreadsheet_metadata(access_token, spreadsheet_id)
    if "error" in meta:
        return meta

    # Need to get full chart info
    from tool_master.tools.google._sheets_utils import SHEETS_API_BASE, _check_httpx
    import httpx

    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{clean_id}?fields=sheets.charts"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to get charts"}

        data = response.json()
        charts = []
        for sheet in data.get("sheets", []):
            for chart in sheet.get("charts", []):
                charts.append({
                    "chart_id": chart.get("chartId"),
                    "title": chart.get("spec", {}).get("title", "(No title)"),
                    "type": chart.get("spec", {}).get("basicChart", {}).get("chartType", "Unknown"),
                })

        return {"charts": charts, "count": len(charts)}


async def delete_chart(access_token: str, spreadsheet_id: str, chart_id: int) -> dict:
    """Delete a chart.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        chart_id: Chart ID to delete

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    requests = [{"deleteEmbeddedObject": {"objectId": chart_id}}]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Deleted chart {chart_id}"}


# =============================================================================
# Pivot Tables
# =============================================================================

async def create_pivot_table(
    access_token: str,
    spreadsheet_id: str,
    source_range: str,
    row_groups: List[dict],
    values: List[dict],
    anchor_cell: str = "F1",
    column_groups: Optional[List[dict]] = None,
    show_totals: bool = True,
) -> dict:
    """Create a pivot table.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        source_range: Source data range
        row_groups: Row groupings [{"column": 0}, ...]
        values: Value aggregations [{"column": 2, "function": "SUM"}, ...]
        anchor_cell: Where to place the pivot table
        column_groups: Optional column groupings
        show_totals: Show row/column totals

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(source_range)
    anchor_parsed = parse_a1_range(anchor_cell)
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

    # Build row groups
    pivot_rows = []
    for rg in row_groups:
        group = {"sourceColumnOffset": rg["column"], "showTotals": show_totals}
        if "sort_order" in rg:
            group["sortOrder"] = rg["sort_order"]
        pivot_rows.append(group)

    # Build values
    pivot_values = []
    for v in values:
        val = {
            "sourceColumnOffset": v["column"],
            "summarizeFunction": v.get("function", "SUM"),
        }
        if "name" in v:
            val["name"] = v["name"]
        pivot_values.append(val)

    # Build column groups
    pivot_cols = []
    if column_groups:
        for cg in column_groups:
            pivot_cols.append({
                "sourceColumnOffset": cg["column"],
                "showTotals": show_totals,
            })

    anchor_row = anchor_parsed.get("start_row", 0)
    anchor_col = anchor_parsed.get("start_col", 5)

    requests = [{
        "updateCells": {
            "rows": [{
                "values": [{
                    "pivotTable": {
                        "source": grid_range,
                        "rows": pivot_rows,
                        "columns": pivot_cols,
                        "values": pivot_values,
                    }
                }]
            }],
            "start": {
                "sheetId": sheet_id,
                "rowIndex": anchor_row,
                "columnIndex": anchor_col,
            },
            "fields": "pivotTable",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Created pivot table at {anchor_cell}"}


async def list_pivot_tables(access_token: str, spreadsheet_id: str) -> dict:
    """List all pivot tables in a spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID

    Returns:
        Dict with pivot tables list, or error
    """
    from tool_master.tools.google._sheets_utils import SHEETS_API_BASE, _check_httpx
    import httpx

    _check_httpx()

    clean_id = extract_spreadsheet_id(spreadsheet_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{clean_id}?fields=sheets(properties,data.rowData.values.pivotTable)"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to get pivot tables"}

        data = response.json()
        pivots = []

        for sheet in data.get("sheets", []):
            sheet_name = sheet.get("properties", {}).get("title")
            for grid_data in sheet.get("data", []):
                for row_idx, row in enumerate(grid_data.get("rowData", [])):
                    for col_idx, cell in enumerate(row.get("values", [])):
                        if "pivotTable" in cell:
                            pt = cell["pivotTable"]
                            pivots.append({
                                "sheet": sheet_name,
                                "anchor_cell": f"{chr(65 + col_idx)}{row_idx + 1}",
                                "row_groups": len(pt.get("rows", [])),
                                "column_groups": len(pt.get("columns", [])),
                                "values": len(pt.get("values", [])),
                            })

        return {"pivot_tables": pivots, "count": len(pivots)}


async def delete_pivot_table(
    access_token: str,
    spreadsheet_id: str,
    anchor_cell: str,
) -> dict:
    """Delete a pivot table by clearing its anchor cell.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        anchor_cell: Cell where pivot table starts

    Returns:
        Dict with success status, or error
    """
    clean_id = extract_spreadsheet_id(spreadsheet_id)
    parsed = parse_a1_range(anchor_cell)
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
        "updateCells": {
            "range": grid_range,
            "fields": "pivotTable",
        }
    }]

    result = await batch_update(access_token, clean_id, requests)
    if "error" in result:
        return result

    return {"success": True, "message": f"Deleted pivot table at {anchor_cell}"}
