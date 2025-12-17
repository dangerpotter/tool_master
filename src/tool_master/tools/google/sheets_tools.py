"""Google Sheets tool schemas and factory function.

Contains all 80+ sheets tool schemas organized by category, plus the factory
function to create tools wired to a credentials provider.

Usage:
    from tool_master.providers import SimpleGoogleCredentials
    from tool_master.tools.google import create_sheets_tools

    creds = SimpleGoogleCredentials()
    sheets_tools = create_sheets_tools(creds)

For schema-only access:
    from tool_master.tools.google.sheets_tools import SHEETS_SCHEMAS
"""

from typing import TYPE_CHECKING, List, Optional

from tool_master.schemas.tool import Tool, ToolParameter, ParameterType

if TYPE_CHECKING:
    from tool_master.providers import GoogleCredentialsProvider


# =============================================================================
# CORE SCHEMAS: Create, Read, Write, Search, List
# =============================================================================

_create_spreadsheet = Tool(
    name="create_spreadsheet",
    description="Create a new Google Sheets spreadsheet. Returns URL and ID.",
    parameters=[
        ToolParameter(name="title", type=ParameterType.STRING, description="Spreadsheet title", required=True),
        ToolParameter(name="sheet_names", type=ParameterType.ARRAY, description="List of sheet names (default: ['Sheet1'])", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "create"],
)

_list_spreadsheets = Tool(
    name="list_spreadsheets",
    description="List spreadsheets from Google Drive.",
    parameters=[
        ToolParameter(name="query", type=ParameterType.STRING, description="Search query for file names", required=False),
        ToolParameter(name="limit", type=ParameterType.INTEGER, description="Max results (default: 20)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "list"],
)

_read_sheet = Tool(
    name="read_sheet",
    description="Read values from a spreadsheet range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID or URL", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation (e.g., 'Sheet1!A1:D10')", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "read"],
)

_write_to_sheet = Tool(
    name="write_to_sheet",
    description="Write values to a spreadsheet range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID or URL", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation", required=True),
        ToolParameter(name="values", type=ParameterType.ARRAY, description="2D array of values to write", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "write"],
)

_add_row_to_sheet = Tool(
    name="add_row_to_sheet",
    description="Append a single row to a spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID or URL", required=True),
        ToolParameter(name="values", type=ParameterType.ARRAY, description="List of values for the row", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name (default: first sheet)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "append"],
)

_search_sheets = Tool(
    name="search_sheets",
    description="Search for text in a spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID or URL", required=True),
        ToolParameter(name="search_text", type=ParameterType.STRING, description="Text to search for", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Limit to specific sheet", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "search"],
)

_clear_range = Tool(
    name="clear_range",
    description="Clear values from a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to clear in A1 notation", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "clear"],
)

# =============================================================================
# STRUCTURE SCHEMAS: Rows, Columns, Sheets
# =============================================================================

_add_sheet = Tool(
    name="add_sheet",
    description="Add a new sheet tab to the spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Name for the new sheet", required=True),
        ToolParameter(name="rows", type=ParameterType.INTEGER, description="Number of rows (default: 1000)", required=False),
        ToolParameter(name="cols", type=ParameterType.INTEGER, description="Number of columns (default: 26)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

_delete_sheet = Tool(
    name="delete_sheet",
    description="Delete a sheet tab.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet to delete", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

_rename_sheet = Tool(
    name="rename_sheet",
    description="Rename a sheet tab.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="old_name", type=ParameterType.STRING, description="Current sheet name", required=True),
        ToolParameter(name="new_name", type=ParameterType.STRING, description="New sheet name", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

_insert_rows = Tool(
    name="insert_rows",
    description="Insert empty rows at a position.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="start_row", type=ParameterType.INTEGER, description="Row number (1-indexed) to insert at", required=True),
        ToolParameter(name="num_rows", type=ParameterType.INTEGER, description="Number of rows to insert (default: 1)", required=False),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

_delete_rows = Tool(
    name="delete_rows",
    description="Delete rows from the spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="start_row", type=ParameterType.INTEGER, description="First row to delete (1-indexed)", required=True),
        ToolParameter(name="end_row", type=ParameterType.INTEGER, description="Last row to delete (inclusive)", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

_insert_columns = Tool(
    name="insert_columns",
    description="Insert empty columns at a position.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="start_column", type=ParameterType.STRING, description="Column letter to insert at (e.g., 'B')", required=True),
        ToolParameter(name="num_columns", type=ParameterType.INTEGER, description="Number of columns to insert (default: 1)", required=False),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

_delete_columns = Tool(
    name="delete_columns",
    description="Delete columns from the spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="start_column", type=ParameterType.STRING, description="First column to delete (e.g., 'B')", required=True),
        ToolParameter(name="end_column", type=ParameterType.STRING, description="Last column to delete (e.g., 'D')", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

_freeze_rows = Tool(
    name="freeze_rows",
    description="Freeze rows at the top of the sheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="num_rows", type=ParameterType.INTEGER, description="Number of rows to freeze (0 to unfreeze)", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "layout"],
)

_freeze_columns = Tool(
    name="freeze_columns",
    description="Freeze columns at the left of the sheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="num_columns", type=ParameterType.INTEGER, description="Number of columns to freeze (0 to unfreeze)", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "layout"],
)

_auto_resize_columns = Tool(
    name="auto_resize_columns",
    description="Auto-resize columns to fit content.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="start_column", type=ParameterType.STRING, description="First column (e.g., 'A')", required=True),
        ToolParameter(name="end_column", type=ParameterType.STRING, description="Last column (e.g., 'D')", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "layout"],
)

_sort_range = Tool(
    name="sort_range",
    description="Sort a range by a column.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to sort (e.g., 'A1:D100')", required=True),
        ToolParameter(name="sort_column", type=ParameterType.INTEGER, description="Column index to sort by (0-based within range)", required=True),
        ToolParameter(name="ascending", type=ParameterType.BOOLEAN, description="True for A-Z, False for Z-A (default: True)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "structure"],
)

# =============================================================================
# FORMATTING SCHEMAS
# =============================================================================

_format_columns = Tool(
    name="format_columns",
    description="Apply number/date formatting to columns.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="columns", type=ParameterType.STRING, description="Column range (e.g., 'B' or 'B:D')", required=True),
        ToolParameter(name="format_type", type=ParameterType.STRING, description="number, currency, percent, date, datetime, text", required=True, enum=["number", "currency", "percent", "date", "datetime", "text"]),
        ToolParameter(name="pattern", type=ParameterType.STRING, description="Custom format pattern", required=False),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_set_text_format = Tool(
    name="set_text_format",
    description="Apply text formatting (bold, italic, font, etc.) to a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation", required=True),
        ToolParameter(name="bold", type=ParameterType.BOOLEAN, description="Make text bold", required=False),
        ToolParameter(name="italic", type=ParameterType.BOOLEAN, description="Make text italic", required=False),
        ToolParameter(name="underline", type=ParameterType.BOOLEAN, description="Underline text", required=False),
        ToolParameter(name="strikethrough", type=ParameterType.BOOLEAN, description="Strikethrough text", required=False),
        ToolParameter(name="font_family", type=ParameterType.STRING, description="Font name (e.g., 'Arial')", required=False),
        ToolParameter(name="font_size", type=ParameterType.INTEGER, description="Font size in points", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_set_text_color = Tool(
    name="set_text_color",
    description="Set text (foreground) color for a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation", required=True),
        ToolParameter(name="color", type=ParameterType.STRING, description="Color as hex (#FF0000) or name (red)", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_set_background_color = Tool(
    name="set_background_color",
    description="Set background (fill) color for a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation", required=True),
        ToolParameter(name="color", type=ParameterType.STRING, description="Color as hex (#FFFF00) or name (yellow)", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_set_alignment = Tool(
    name="set_alignment",
    description="Set text alignment and wrapping for a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation", required=True),
        ToolParameter(name="horizontal", type=ParameterType.STRING, description="left, center, or right", required=False, enum=["left", "center", "right"]),
        ToolParameter(name="vertical", type=ParameterType.STRING, description="top, middle, or bottom", required=False, enum=["top", "middle", "bottom"]),
        ToolParameter(name="wrap", type=ParameterType.STRING, description="overflow, clip, or wrap", required=False, enum=["overflow", "clip", "wrap"]),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_set_borders = Tool(
    name="set_borders",
    description="Add borders to cells.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation", required=True),
        ToolParameter(name="border_style", type=ParameterType.STRING, description="solid, dashed, dotted, double, thick, medium, none", required=False, enum=["solid", "dashed", "dotted", "double", "thick", "medium", "none"]),
        ToolParameter(name="color", type=ParameterType.STRING, description="Border color", required=False),
        ToolParameter(name="sides", type=ParameterType.STRING, description="all, outer, inner, top, bottom, left, right", required=False, enum=["all", "outer", "inner", "top", "bottom", "left", "right"]),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_merge_cells = Tool(
    name="merge_cells",
    description="Merge cells in a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to merge", required=True),
        ToolParameter(name="merge_type", type=ParameterType.STRING, description="all, horizontal, or vertical", required=False, enum=["all", "horizontal", "vertical"]),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_unmerge_cells = Tool(
    name="unmerge_cells",
    description="Unmerge previously merged cells.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to unmerge", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_alternating_colors = Tool(
    name="alternating_colors",
    description="Apply alternating row colors (zebra stripes).",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to apply banding", required=True),
        ToolParameter(name="header_color", type=ParameterType.STRING, description="Header row color (default: blue)", required=False),
        ToolParameter(name="first_band_color", type=ParameterType.STRING, description="Odd rows color (default: white)", required=False),
        ToolParameter(name="second_band_color", type=ParameterType.STRING, description="Even rows color (default: lightgray)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_add_note = Tool(
    name="add_note",
    description="Add a note (comment) to a cell.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="cell", type=ParameterType.STRING, description="Cell in A1 notation (e.g., 'B2')", required=True),
        ToolParameter(name="note", type=ParameterType.STRING, description="Note text (empty to clear)", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

# =============================================================================
# CHART & PIVOT SCHEMAS
# =============================================================================

_create_chart = Tool(
    name="create_chart",
    description="Create an embedded chart from data.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="data_range", type=ParameterType.STRING, description="Data range in A1 notation", required=True),
        ToolParameter(name="chart_type", type=ParameterType.STRING, description="bar, line, column, pie, area, scatter", required=False, enum=["bar", "line", "column", "pie", "area", "scatter"]),
        ToolParameter(name="title", type=ParameterType.STRING, description="Chart title", required=False),
        ToolParameter(name="anchor_cell", type=ParameterType.STRING, description="Where to place chart (default: F1)", required=False),
        ToolParameter(name="legend_position", type=ParameterType.STRING, description="bottom, top, left, right, none", required=False, enum=["bottom", "top", "left", "right", "none"]),
    ],
    category="sheets",
    tags=["google", "sheets", "charts"],
)

_list_charts = Tool(
    name="list_charts",
    description="List all charts in a spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "charts"],
)

_delete_chart = Tool(
    name="delete_chart",
    description="Delete a chart.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="chart_id", type=ParameterType.INTEGER, description="Chart ID (from list_charts)", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "charts"],
)

_create_pivot_table = Tool(
    name="create_pivot_table",
    description="Create a pivot table for data analysis.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="source_range", type=ParameterType.STRING, description="Source data range", required=True),
        ToolParameter(name="row_groups", type=ParameterType.ARRAY, description="Row groupings [{column: 0}, ...]", required=True),
        ToolParameter(name="values", type=ParameterType.ARRAY, description="Values [{column: 2, function: 'SUM'}, ...]", required=True),
        ToolParameter(name="anchor_cell", type=ParameterType.STRING, description="Where to place pivot (default: F1)", required=False),
        ToolParameter(name="column_groups", type=ParameterType.ARRAY, description="Column groupings", required=False),
        ToolParameter(name="show_totals", type=ParameterType.BOOLEAN, description="Show totals (default: True)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "pivot"],
)

_list_pivot_tables = Tool(
    name="list_pivot_tables",
    description="List all pivot tables in a spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "pivot"],
)

_delete_pivot_table = Tool(
    name="delete_pivot_table",
    description="Delete a pivot table.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="anchor_cell", type=ParameterType.STRING, description="Cell where pivot table starts", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "pivot"],
)

# =============================================================================
# FILTER & VALIDATION SCHEMAS
# =============================================================================

_set_basic_filter = Tool(
    name="set_basic_filter",
    description="Enable auto-filter dropdowns on a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to filter (include header)", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "filters"],
)

_clear_basic_filter = Tool(
    name="clear_basic_filter",
    description="Remove basic filter from a sheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "filters"],
)

_create_filter_view = Tool(
    name="create_filter_view",
    description="Create a named filter view.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="title", type=ParameterType.STRING, description="Filter view name", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range for the filter", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "filters"],
)

_delete_filter_view = Tool(
    name="delete_filter_view",
    description="Delete a filter view.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="filter_view_id", type=ParameterType.INTEGER, description="Filter view ID", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "filters"],
)

_list_filter_views = Tool(
    name="list_filter_views",
    description="List all filter views.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Filter by sheet", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "filters"],
)

_conditional_format = Tool(
    name="conditional_format",
    description="Add conditional formatting to highlight cells based on values.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to format", required=True),
        ToolParameter(name="rule_type", type=ParameterType.STRING, description="greater_than, less_than, equals, contains, not_empty, is_empty", required=True, enum=["greater_than", "less_than", "equals", "contains", "not_empty", "is_empty"]),
        ToolParameter(name="condition_value", type=ParameterType.STRING, description="Value to compare (not needed for empty checks)", required=False),
        ToolParameter(name="format_type", type=ParameterType.STRING, description="background or text", required=False, enum=["background", "text"]),
        ToolParameter(name="color", type=ParameterType.STRING, description="Color to apply (default: red)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_data_validation = Tool(
    name="data_validation",
    description="Add data validation rules (dropdowns, number ranges, checkboxes).",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to validate", required=True),
        ToolParameter(name="validation_type", type=ParameterType.STRING, description="dropdown, number_range, date, checkbox", required=True, enum=["dropdown", "number_range", "date", "checkbox"]),
        ToolParameter(name="values", type=ParameterType.ARRAY, description="Dropdown values list", required=False),
        ToolParameter(name="min_value", type=ParameterType.NUMBER, description="Min for number_range", required=False),
        ToolParameter(name="max_value", type=ParameterType.NUMBER, description="Max for number_range", required=False),
        ToolParameter(name="strict", type=ParameterType.BOOLEAN, description="Reject invalid input (default: True)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "validation"],
)

# =============================================================================
# PROTECTION SCHEMAS
# =============================================================================

_create_named_range = Tool(
    name="create_named_range",
    description="Create a named range for use in formulas.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="name", type=ParameterType.STRING, description="Name for the range", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range in A1 notation", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "ranges"],
)

_list_named_ranges = Tool(
    name="list_named_ranges",
    description="List all named ranges.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "ranges"],
)

_delete_named_range = Tool(
    name="delete_named_range",
    description="Delete a named range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="named_range_id", type=ParameterType.STRING, description="Named range ID", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "ranges"],
)

_protect_range = Tool(
    name="protect_range",
    description="Protect a range of cells from editing.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Range to protect", required=True),
        ToolParameter(name="description", type=ParameterType.STRING, description="Why it's protected", required=False),
        ToolParameter(name="warning_only", type=ParameterType.BOOLEAN, description="Show warning but allow editing (default: False)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "protection"],
)

_list_protected_ranges = Tool(
    name="list_protected_ranges",
    description="List all protected ranges.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Filter by sheet", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "protection"],
)

_delete_protected_range = Tool(
    name="delete_protected_range",
    description="Remove protection from a range.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="protected_range_id", type=ParameterType.INTEGER, description="Protected range ID", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "protection"],
)

_protect_sheet = Tool(
    name="protect_sheet",
    description="Protect an entire sheet with optional unprotected ranges.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet to protect", required=True),
        ToolParameter(name="description", type=ParameterType.STRING, description="Description", required=False),
        ToolParameter(name="warning_only", type=ParameterType.BOOLEAN, description="Show warning only (default: False)", required=False),
        ToolParameter(name="editors", type=ParameterType.ARRAY, description="Email addresses who can edit", required=False),
        ToolParameter(name="unprotected_ranges", type=ParameterType.ARRAY, description="Ranges that remain editable", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "protection"],
)

# =============================================================================
# ADVANCED SCHEMAS
# =============================================================================

_find_replace = Tool(
    name="find_replace",
    description="Find and replace text in a spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="find", type=ParameterType.STRING, description="Text to search for", required=True),
        ToolParameter(name="replacement", type=ParameterType.STRING, description="Text to replace with", required=True),
        ToolParameter(name="range", type=ParameterType.STRING, description="Limit to range", required=False),
        ToolParameter(name="match_case", type=ParameterType.BOOLEAN, description="Case-sensitive (default: False)", required=False),
        ToolParameter(name="match_entire_cell", type=ParameterType.BOOLEAN, description="Match entire cell (default: False)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "edit"],
)

_copy_paste = Tool(
    name="copy_paste",
    description="Copy cells from one location to another.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="source_range", type=ParameterType.STRING, description="Source range", required=True),
        ToolParameter(name="destination_range", type=ParameterType.STRING, description="Destination range", required=True),
        ToolParameter(name="paste_type", type=ParameterType.STRING, description="all, values, or format", required=False, enum=["all", "values", "format"]),
    ],
    category="sheets",
    tags=["google", "sheets", "edit"],
)

_cut_paste = Tool(
    name="cut_paste",
    description="Move cells from one location to another.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="source_range", type=ParameterType.STRING, description="Source range", required=True),
        ToolParameter(name="destination", type=ParameterType.STRING, description="Destination cell", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "edit"],
)

_hide_sheet = Tool(
    name="hide_sheet",
    description="Hide a sheet tab from view.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet to hide", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "tabs"],
)

_show_sheet = Tool(
    name="show_sheet",
    description="Show a hidden sheet tab.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet to show", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "tabs"],
)

_set_tab_color = Tool(
    name="set_tab_color",
    description="Set the color of a sheet tab.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=True),
        ToolParameter(name="color", type=ParameterType.STRING, description="Tab color", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "tabs"],
)

_add_hyperlink = Tool(
    name="add_hyperlink",
    description="Add a clickable hyperlink to a cell.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="cell", type=ParameterType.STRING, description="Cell in A1 notation", required=True),
        ToolParameter(name="url", type=ParameterType.STRING, description="URL to link to", required=True),
        ToolParameter(name="display_text", type=ParameterType.STRING, description="Text to display", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "formatting"],
)

_create_row_group = Tool(
    name="create_row_group",
    description="Create a collapsible row group.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=True),
        ToolParameter(name="start_row", type=ParameterType.INTEGER, description="First row (1-indexed)", required=True),
        ToolParameter(name="end_row", type=ParameterType.INTEGER, description="Last row (inclusive)", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "groups"],
)

_create_column_group = Tool(
    name="create_column_group",
    description="Create a collapsible column group.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=True),
        ToolParameter(name="start_column", type=ParameterType.STRING, description="First column (e.g., 'B')", required=True),
        ToolParameter(name="end_column", type=ParameterType.STRING, description="Last column (e.g., 'D')", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "groups"],
)

_delete_row_group = Tool(
    name="delete_row_group",
    description="Delete a row group.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=True),
        ToolParameter(name="start_row", type=ParameterType.INTEGER, description="First row", required=True),
        ToolParameter(name="end_row", type=ParameterType.INTEGER, description="Last row", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "groups"],
)

_delete_column_group = Tool(
    name="delete_column_group",
    description="Delete a column group.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=True),
        ToolParameter(name="start_column", type=ParameterType.STRING, description="First column", required=True),
        ToolParameter(name="end_column", type=ParameterType.STRING, description="Last column", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "groups"],
)

_list_slicers = Tool(
    name="list_slicers",
    description="List all slicers in a spreadsheet.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Filter by sheet", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "slicers"],
)

_create_slicer = Tool(
    name="create_slicer",
    description="Create a slicer widget for filtering.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="sheet_name", type=ParameterType.STRING, description="Sheet name", required=True),
        ToolParameter(name="data_range", type=ParameterType.STRING, description="Data range to filter", required=True),
        ToolParameter(name="column_index", type=ParameterType.INTEGER, description="Column to filter by (0-based)", required=True),
        ToolParameter(name="title", type=ParameterType.STRING, description="Slicer title", required=False),
        ToolParameter(name="anchor_row", type=ParameterType.INTEGER, description="Position row (0-indexed)", required=False),
        ToolParameter(name="anchor_col", type=ParameterType.INTEGER, description="Position column (0-indexed)", required=False),
    ],
    category="sheets",
    tags=["google", "sheets", "slicers"],
)

_delete_slicer = Tool(
    name="delete_slicer",
    description="Delete a slicer.",
    parameters=[
        ToolParameter(name="spreadsheet_id", type=ParameterType.STRING, description="Google Sheets ID", required=True),
        ToolParameter(name="slicer_id", type=ParameterType.INTEGER, description="Slicer ID", required=True),
    ],
    category="sheets",
    tags=["google", "sheets", "slicers"],
)


# =============================================================================
# ALL SCHEMAS LIST
# =============================================================================

SHEETS_SCHEMAS: List[Tool] = [
    # Core
    _create_spreadsheet, _list_spreadsheets, _read_sheet, _write_to_sheet,
    _add_row_to_sheet, _search_sheets, _clear_range,
    # Structure
    _add_sheet, _delete_sheet, _rename_sheet, _insert_rows, _delete_rows,
    _insert_columns, _delete_columns, _freeze_rows, _freeze_columns,
    _auto_resize_columns, _sort_range,
    # Formatting
    _format_columns, _set_text_format, _set_text_color, _set_background_color,
    _set_alignment, _set_borders, _merge_cells, _unmerge_cells, _alternating_colors,
    _add_note,
    # Charts & Pivots
    _create_chart, _list_charts, _delete_chart, _create_pivot_table,
    _list_pivot_tables, _delete_pivot_table,
    # Filters & Validation
    _set_basic_filter, _clear_basic_filter, _create_filter_view, _delete_filter_view,
    _list_filter_views, _conditional_format, _data_validation,
    # Protection
    _create_named_range, _list_named_ranges, _delete_named_range, _protect_range,
    _list_protected_ranges, _delete_protected_range, _protect_sheet,
    # Advanced
    _find_replace, _copy_paste, _cut_paste, _hide_sheet, _show_sheet, _set_tab_color,
    _add_hyperlink, _create_row_group, _create_column_group, _delete_row_group,
    _delete_column_group, _list_slicers, _create_slicer, _delete_slicer,
]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_sheets_tools(credentials: "GoogleCredentialsProvider") -> List[Tool]:
    """Create sheets tools wired to the given credentials provider.

    Args:
        credentials: A GoogleCredentialsProvider instance

    Returns:
        List of Tool objects with handlers ready to use
    """
    from tool_master.tools.google import sheets_core, sheets_structure
    from tool_master.tools.google import sheets_formatting, sheets_charts
    from tool_master.tools.google import sheets_filters, sheets_protection
    from tool_master.tools.google import sheets_advanced

    # Map tool names to their implementation functions
    # Each handler wraps the impl function with credentials
    async def make_handler(impl_func, **param_map):
        async def handler(**kwargs):
            token = await credentials.get_access_token()
            # Remap parameter names if needed
            for old_name, new_name in param_map.items():
                if old_name in kwargs:
                    kwargs[new_name] = kwargs.pop(old_name)
            return await impl_func(token, **kwargs)
        return handler

    # Build handlers map
    handlers = {}

    # Core handlers
    async def h_create_spreadsheet(title, sheet_names=None):
        token = await credentials.get_access_token()
        return await sheets_core.create_spreadsheet(token, title, sheet_names)
    handlers["create_spreadsheet"] = h_create_spreadsheet

    async def h_list_spreadsheets(query=None, limit=20):
        token = await credentials.get_access_token()
        return await sheets_core.list_spreadsheets(token, query, limit)
    handlers["list_spreadsheets"] = h_list_spreadsheets

    async def h_read_sheet(spreadsheet_id, range):
        token = await credentials.get_access_token()
        return await sheets_core.read_sheet(token, spreadsheet_id, range)
    handlers["read_sheet"] = h_read_sheet

    async def h_write_to_sheet(spreadsheet_id, range, values):
        token = await credentials.get_access_token()
        return await sheets_core.write_to_sheet(token, spreadsheet_id, range, values)
    handlers["write_to_sheet"] = h_write_to_sheet

    async def h_add_row_to_sheet(spreadsheet_id, values, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_core.add_row_to_sheet(token, spreadsheet_id, values, sheet_name)
    handlers["add_row_to_sheet"] = h_add_row_to_sheet

    async def h_search_sheets(spreadsheet_id, search_text, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_core.search_sheets(token, spreadsheet_id, search_text, sheet_name)
    handlers["search_sheets"] = h_search_sheets

    async def h_clear_range(spreadsheet_id, range):
        token = await credentials.get_access_token()
        return await sheets_core.clear_range(token, spreadsheet_id, range)
    handlers["clear_range"] = h_clear_range

    # Structure handlers
    async def h_add_sheet(spreadsheet_id, sheet_name, rows=1000, cols=26):
        token = await credentials.get_access_token()
        return await sheets_structure.add_sheet(token, spreadsheet_id, sheet_name, rows, cols)
    handlers["add_sheet"] = h_add_sheet

    async def h_delete_sheet(spreadsheet_id, sheet_name):
        token = await credentials.get_access_token()
        return await sheets_structure.delete_sheet(token, spreadsheet_id, sheet_name)
    handlers["delete_sheet"] = h_delete_sheet

    async def h_rename_sheet(spreadsheet_id, old_name, new_name):
        token = await credentials.get_access_token()
        return await sheets_structure.rename_sheet(token, spreadsheet_id, old_name, new_name)
    handlers["rename_sheet"] = h_rename_sheet

    async def h_insert_rows(spreadsheet_id, start_row, num_rows=1, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_structure.insert_rows(token, spreadsheet_id, start_row, num_rows, sheet_name)
    handlers["insert_rows"] = h_insert_rows

    async def h_delete_rows(spreadsheet_id, start_row, end_row, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_structure.delete_rows(token, spreadsheet_id, start_row, end_row, sheet_name)
    handlers["delete_rows"] = h_delete_rows

    async def h_insert_columns(spreadsheet_id, start_column, num_columns=1, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_structure.insert_columns(token, spreadsheet_id, start_column, num_columns, sheet_name)
    handlers["insert_columns"] = h_insert_columns

    async def h_delete_columns(spreadsheet_id, start_column, end_column, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_structure.delete_columns(token, spreadsheet_id, start_column, end_column, sheet_name)
    handlers["delete_columns"] = h_delete_columns

    async def h_freeze_rows(spreadsheet_id, num_rows, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_structure.freeze_rows(token, spreadsheet_id, num_rows, sheet_name)
    handlers["freeze_rows"] = h_freeze_rows

    async def h_freeze_columns(spreadsheet_id, num_columns, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_structure.freeze_columns(token, spreadsheet_id, num_columns, sheet_name)
    handlers["freeze_columns"] = h_freeze_columns

    async def h_auto_resize_columns(spreadsheet_id, start_column, end_column, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_structure.auto_resize_columns(token, spreadsheet_id, start_column, end_column, sheet_name)
    handlers["auto_resize_columns"] = h_auto_resize_columns

    async def h_sort_range(spreadsheet_id, range, sort_column, ascending=True):
        token = await credentials.get_access_token()
        return await sheets_structure.sort_range(token, spreadsheet_id, range, sort_column, ascending)
    handlers["sort_range"] = h_sort_range

    # Formatting handlers
    async def h_format_columns(spreadsheet_id, columns, format_type, pattern=None, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_formatting.format_columns(token, spreadsheet_id, columns, format_type, pattern, sheet_name)
    handlers["format_columns"] = h_format_columns

    async def h_set_text_format(spreadsheet_id, range, bold=None, italic=None, underline=None, strikethrough=None, font_family=None, font_size=None):
        token = await credentials.get_access_token()
        return await sheets_formatting.set_text_format(token, spreadsheet_id, range, bold, italic, underline, strikethrough, font_family, font_size)
    handlers["set_text_format"] = h_set_text_format

    async def h_set_text_color(spreadsheet_id, range, color):
        token = await credentials.get_access_token()
        return await sheets_formatting.set_text_color(token, spreadsheet_id, range, color)
    handlers["set_text_color"] = h_set_text_color

    async def h_set_background_color(spreadsheet_id, range, color):
        token = await credentials.get_access_token()
        return await sheets_formatting.set_background_color(token, spreadsheet_id, range, color)
    handlers["set_background_color"] = h_set_background_color

    async def h_set_alignment(spreadsheet_id, range, horizontal=None, vertical=None, wrap=None):
        token = await credentials.get_access_token()
        return await sheets_formatting.set_alignment(token, spreadsheet_id, range, horizontal, vertical, wrap)
    handlers["set_alignment"] = h_set_alignment

    async def h_set_borders(spreadsheet_id, range, border_style="solid", color="black", sides="all"):
        token = await credentials.get_access_token()
        return await sheets_formatting.set_borders(token, spreadsheet_id, range, border_style, color, sides)
    handlers["set_borders"] = h_set_borders

    async def h_merge_cells(spreadsheet_id, range, merge_type="all"):
        token = await credentials.get_access_token()
        return await sheets_formatting.merge_cells(token, spreadsheet_id, range, merge_type)
    handlers["merge_cells"] = h_merge_cells

    async def h_unmerge_cells(spreadsheet_id, range):
        token = await credentials.get_access_token()
        return await sheets_formatting.unmerge_cells(token, spreadsheet_id, range)
    handlers["unmerge_cells"] = h_unmerge_cells

    async def h_alternating_colors(spreadsheet_id, range, header_color="blue", first_band_color="white", second_band_color="lightgray"):
        token = await credentials.get_access_token()
        return await sheets_formatting.alternating_colors(token, spreadsheet_id, range, header_color, first_band_color, second_band_color)
    handlers["alternating_colors"] = h_alternating_colors

    async def h_add_note(spreadsheet_id, cell, note):
        token = await credentials.get_access_token()
        return await sheets_formatting.add_note(token, spreadsheet_id, cell, note)
    handlers["add_note"] = h_add_note

    # Chart handlers
    async def h_create_chart(spreadsheet_id, data_range, chart_type="column", title=None, anchor_cell="F1", legend_position="bottom"):
        token = await credentials.get_access_token()
        return await sheets_charts.create_chart(token, spreadsheet_id, data_range, chart_type, title, anchor_cell, legend_position)
    handlers["create_chart"] = h_create_chart

    async def h_list_charts(spreadsheet_id):
        token = await credentials.get_access_token()
        return await sheets_charts.list_charts(token, spreadsheet_id)
    handlers["list_charts"] = h_list_charts

    async def h_delete_chart(spreadsheet_id, chart_id):
        token = await credentials.get_access_token()
        return await sheets_charts.delete_chart(token, spreadsheet_id, chart_id)
    handlers["delete_chart"] = h_delete_chart

    async def h_create_pivot_table(spreadsheet_id, source_range, row_groups, values, anchor_cell="F1", column_groups=None, show_totals=True):
        token = await credentials.get_access_token()
        return await sheets_charts.create_pivot_table(token, spreadsheet_id, source_range, row_groups, values, anchor_cell, column_groups, show_totals)
    handlers["create_pivot_table"] = h_create_pivot_table

    async def h_list_pivot_tables(spreadsheet_id):
        token = await credentials.get_access_token()
        return await sheets_charts.list_pivot_tables(token, spreadsheet_id)
    handlers["list_pivot_tables"] = h_list_pivot_tables

    async def h_delete_pivot_table(spreadsheet_id, anchor_cell):
        token = await credentials.get_access_token()
        return await sheets_charts.delete_pivot_table(token, spreadsheet_id, anchor_cell)
    handlers["delete_pivot_table"] = h_delete_pivot_table

    # Filter handlers
    async def h_set_basic_filter(spreadsheet_id, range):
        token = await credentials.get_access_token()
        return await sheets_filters.set_basic_filter(token, spreadsheet_id, range)
    handlers["set_basic_filter"] = h_set_basic_filter

    async def h_clear_basic_filter(spreadsheet_id, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_filters.clear_basic_filter(token, spreadsheet_id, sheet_name)
    handlers["clear_basic_filter"] = h_clear_basic_filter

    async def h_create_filter_view(spreadsheet_id, title, range):
        token = await credentials.get_access_token()
        return await sheets_filters.create_filter_view(token, spreadsheet_id, title, range)
    handlers["create_filter_view"] = h_create_filter_view

    async def h_delete_filter_view(spreadsheet_id, filter_view_id):
        token = await credentials.get_access_token()
        return await sheets_filters.delete_filter_view(token, spreadsheet_id, filter_view_id)
    handlers["delete_filter_view"] = h_delete_filter_view

    async def h_list_filter_views(spreadsheet_id, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_filters.list_filter_views(token, spreadsheet_id, sheet_name)
    handlers["list_filter_views"] = h_list_filter_views

    async def h_conditional_format(spreadsheet_id, range, rule_type, condition_value=None, format_type="background", color="red"):
        token = await credentials.get_access_token()
        return await sheets_filters.conditional_format(token, spreadsheet_id, range, rule_type, condition_value, format_type, color)
    handlers["conditional_format"] = h_conditional_format

    async def h_data_validation(spreadsheet_id, range, validation_type, values=None, min_value=None, max_value=None, strict=True):
        token = await credentials.get_access_token()
        return await sheets_filters.data_validation(token, spreadsheet_id, range, validation_type, values, min_value, max_value, strict)
    handlers["data_validation"] = h_data_validation

    # Protection handlers
    async def h_create_named_range(spreadsheet_id, name, range):
        token = await credentials.get_access_token()
        return await sheets_protection.create_named_range(token, spreadsheet_id, name, range)
    handlers["create_named_range"] = h_create_named_range

    async def h_list_named_ranges(spreadsheet_id):
        token = await credentials.get_access_token()
        return await sheets_protection.list_named_ranges(token, spreadsheet_id)
    handlers["list_named_ranges"] = h_list_named_ranges

    async def h_delete_named_range(spreadsheet_id, named_range_id):
        token = await credentials.get_access_token()
        return await sheets_protection.delete_named_range(token, spreadsheet_id, named_range_id)
    handlers["delete_named_range"] = h_delete_named_range

    async def h_protect_range(spreadsheet_id, range, description=None, warning_only=False):
        token = await credentials.get_access_token()
        return await sheets_protection.protect_range(token, spreadsheet_id, range, description, warning_only)
    handlers["protect_range"] = h_protect_range

    async def h_list_protected_ranges(spreadsheet_id, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_protection.list_protected_ranges(token, spreadsheet_id, sheet_name)
    handlers["list_protected_ranges"] = h_list_protected_ranges

    async def h_delete_protected_range(spreadsheet_id, protected_range_id):
        token = await credentials.get_access_token()
        return await sheets_protection.delete_protected_range(token, spreadsheet_id, protected_range_id)
    handlers["delete_protected_range"] = h_delete_protected_range

    async def h_protect_sheet(spreadsheet_id, sheet_name, description=None, warning_only=False, editors=None, unprotected_ranges=None):
        token = await credentials.get_access_token()
        return await sheets_protection.protect_sheet(token, spreadsheet_id, sheet_name, description, warning_only, editors, unprotected_ranges)
    handlers["protect_sheet"] = h_protect_sheet

    # Advanced handlers
    async def h_find_replace(spreadsheet_id, find, replacement, range=None, match_case=False, match_entire_cell=False):
        token = await credentials.get_access_token()
        return await sheets_advanced.find_replace(token, spreadsheet_id, find, replacement, range, match_case, match_entire_cell)
    handlers["find_replace"] = h_find_replace

    async def h_copy_paste(spreadsheet_id, source_range, destination_range, paste_type="all"):
        token = await credentials.get_access_token()
        return await sheets_advanced.copy_paste(token, spreadsheet_id, source_range, destination_range, paste_type)
    handlers["copy_paste"] = h_copy_paste

    async def h_cut_paste(spreadsheet_id, source_range, destination):
        token = await credentials.get_access_token()
        return await sheets_advanced.cut_paste(token, spreadsheet_id, source_range, destination)
    handlers["cut_paste"] = h_cut_paste

    async def h_hide_sheet(spreadsheet_id, sheet_name):
        token = await credentials.get_access_token()
        return await sheets_advanced.hide_sheet(token, spreadsheet_id, sheet_name)
    handlers["hide_sheet"] = h_hide_sheet

    async def h_show_sheet(spreadsheet_id, sheet_name):
        token = await credentials.get_access_token()
        return await sheets_advanced.show_sheet(token, spreadsheet_id, sheet_name)
    handlers["show_sheet"] = h_show_sheet

    async def h_set_tab_color(spreadsheet_id, sheet_name, color):
        token = await credentials.get_access_token()
        return await sheets_advanced.set_tab_color(token, spreadsheet_id, sheet_name, color)
    handlers["set_tab_color"] = h_set_tab_color

    async def h_add_hyperlink(spreadsheet_id, cell, url, display_text=None):
        token = await credentials.get_access_token()
        return await sheets_advanced.add_hyperlink(token, spreadsheet_id, cell, url, display_text)
    handlers["add_hyperlink"] = h_add_hyperlink

    async def h_create_row_group(spreadsheet_id, sheet_name, start_row, end_row):
        token = await credentials.get_access_token()
        return await sheets_advanced.create_row_group(token, spreadsheet_id, sheet_name, start_row, end_row)
    handlers["create_row_group"] = h_create_row_group

    async def h_create_column_group(spreadsheet_id, sheet_name, start_column, end_column):
        token = await credentials.get_access_token()
        return await sheets_advanced.create_column_group(token, spreadsheet_id, sheet_name, start_column, end_column)
    handlers["create_column_group"] = h_create_column_group

    async def h_delete_row_group(spreadsheet_id, sheet_name, start_row, end_row):
        token = await credentials.get_access_token()
        return await sheets_advanced.delete_row_group(token, spreadsheet_id, sheet_name, start_row, end_row)
    handlers["delete_row_group"] = h_delete_row_group

    async def h_delete_column_group(spreadsheet_id, sheet_name, start_column, end_column):
        token = await credentials.get_access_token()
        return await sheets_advanced.delete_column_group(token, spreadsheet_id, sheet_name, start_column, end_column)
    handlers["delete_column_group"] = h_delete_column_group

    async def h_list_slicers(spreadsheet_id, sheet_name=None):
        token = await credentials.get_access_token()
        return await sheets_advanced.list_slicers(token, spreadsheet_id, sheet_name)
    handlers["list_slicers"] = h_list_slicers

    async def h_create_slicer(spreadsheet_id, sheet_name, data_range, column_index, title=None, anchor_row=0, anchor_col=0):
        token = await credentials.get_access_token()
        return await sheets_advanced.create_slicer(token, spreadsheet_id, sheet_name, data_range, column_index, title, anchor_row, anchor_col)
    handlers["create_slicer"] = h_create_slicer

    async def h_delete_slicer(spreadsheet_id, slicer_id):
        token = await credentials.get_access_token()
        return await sheets_advanced.delete_slicer(token, spreadsheet_id, slicer_id)
    handlers["delete_slicer"] = h_delete_slicer

    # Create tools with handlers
    tools = []
    for schema in SHEETS_SCHEMAS:
        tool = schema.model_copy(deep=True)
        handler = handlers.get(tool.name)
        if handler:
            tool.set_handler(handler)
        tools.append(tool)

    return tools
