"""Shared utility functions for Google Sheets tools.

Helper functions for color parsing, range parsing, spreadsheet ID extraction,
and common API operations used across all sheets modules.
"""

import logging
import re
from typing import Optional, Tuple, List, Any
from urllib.parse import quote, urlencode

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)

# Google API endpoints
SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"


def _check_httpx():
    """Raise ImportError if httpx is not available."""
    if httpx is None:
        raise ImportError("httpx is required. Install with: pip install tool-master[google]")


# =============================================================================
# Spreadsheet ID Extraction
# =============================================================================

def extract_spreadsheet_id(input_string: str) -> str:
    """Extract spreadsheet ID from various input formats.

    Handles:
    - Pure ID: "1A2DKm4FCTLMniMUWerd7_NgGQ8cAO2-7xHQOStYO7T0"
    - Full URL: "https://docs.google.com/spreadsheets/d/1A2DKm.../edit#gid=0"
    - Partial URL: "1A2DKm.../edit?gid=..."

    Args:
        input_string: Spreadsheet ID or URL containing the ID

    Returns:
        Clean spreadsheet ID
    """
    if not input_string:
        return input_string

    input_string = input_string.strip()

    # Pattern 1: Full Google Sheets URL
    url_pattern = r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)'
    match = re.search(url_pattern, input_string)
    if match:
        return match.group(1)

    # Pattern 2: ID followed by /edit or other path
    path_pattern = r'^([a-zA-Z0-9_-]+)/(?:edit|view|copy)'
    match = re.match(path_pattern, input_string)
    if match:
        return match.group(1)

    # Pattern 3: Just extract the first valid-looking ID segment
    id_pattern = r'^([a-zA-Z0-9_-]{25,})'
    match = re.match(id_pattern, input_string)
    if match:
        return match.group(1)

    return input_string


# =============================================================================
# Color Parsing
# =============================================================================

NAMED_COLORS = {
    "red": {"red": 1.0, "green": 0.0, "blue": 0.0},
    "green": {"red": 0.0, "green": 0.8, "blue": 0.0},
    "blue": {"red": 0.0, "green": 0.0, "blue": 1.0},
    "yellow": {"red": 1.0, "green": 1.0, "blue": 0.0},
    "orange": {"red": 1.0, "green": 0.647, "blue": 0.0},
    "purple": {"red": 0.5, "green": 0.0, "blue": 0.5},
    "pink": {"red": 1.0, "green": 0.753, "blue": 0.796},
    "black": {"red": 0.0, "green": 0.0, "blue": 0.0},
    "white": {"red": 1.0, "green": 1.0, "blue": 1.0},
    "gray": {"red": 0.5, "green": 0.5, "blue": 0.5},
    "lightgray": {"red": 0.827, "green": 0.827, "blue": 0.827},
    "darkgray": {"red": 0.412, "green": 0.412, "blue": 0.412},
    "cyan": {"red": 0.0, "green": 1.0, "blue": 1.0},
    "magenta": {"red": 1.0, "green": 0.0, "blue": 1.0},
    "lightblue": {"red": 0.678, "green": 0.847, "blue": 0.902},
    "lightgreen": {"red": 0.565, "green": 0.933, "blue": 0.565},
    "lightyellow": {"red": 1.0, "green": 1.0, "blue": 0.878},
    "lightpurple": {"red": 0.878, "green": 0.678, "blue": 1.0},
}


def parse_color(color_input: str) -> dict:
    """Parse color from hex code or name to Google Sheets RGB format (0-1 floats).

    Args:
        color_input: Color as hex code (#FF0000) or named color (red)

    Returns:
        Dict with 'red', 'green', 'blue' keys (0-1 floats)
    """
    color = color_input.strip().lower()

    # Named color
    if color in NAMED_COLORS:
        return NAMED_COLORS[color]

    # Hex color
    if color.startswith("#"):
        hex_str = color[1:]
        if len(hex_str) == 3:  # #RGB -> #RRGGBB
            hex_str = ''.join(c * 2 for c in hex_str)
        if len(hex_str) in (6, 8):
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            result = {"red": r, "green": g, "blue": b}
            if len(hex_str) == 8:
                result["alpha"] = int(hex_str[6:8], 16) / 255.0
            return result

    # Default to red if unrecognized
    return NAMED_COLORS["red"]


# =============================================================================
# Range Parsing
# =============================================================================

def col_to_index(col: str) -> int:
    """Convert column letter to 0-indexed number (A=0, B=1, AA=26)."""
    col = col.upper().strip()
    result = 0
    for char in col:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def index_to_col(index: int) -> str:
    """Convert 0-indexed number to column letter (0=A, 1=B, 26=AA)."""
    result = ""
    index += 1  # Convert to 1-indexed
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def parse_column_range(columns: str) -> Tuple[int, int]:
    """Convert column notation to 0-indexed range.

    Args:
        columns: Column in A1 notation ('B' or 'B:E')

    Returns:
        Tuple of (start_index, end_index) - end is exclusive

    Examples:
        'B' -> (1, 2)
        'B:E' -> (1, 5)
    """
    if ':' in columns:
        start, end = columns.split(':')
        return col_to_index(start), col_to_index(end) + 1
    else:
        idx = col_to_index(columns)
        return idx, idx + 1


def parse_row_range(rows: str) -> Tuple[int, int]:
    """Convert row notation to 0-indexed range.

    Args:
        rows: Row number or range ('5' or '5:10')

    Returns:
        Tuple of (start_index, end_index) - end is exclusive, 0-indexed

    Examples:
        '5' -> (4, 5)
        '5:10' -> (4, 10)
    """
    if ':' in rows:
        start, end = rows.split(':')
        return int(start) - 1, int(end)
    else:
        idx = int(rows) - 1
        return idx, idx + 1


def parse_a1_range(range_notation: str) -> dict:
    """Parse A1 notation range into components.

    Args:
        range_notation: Range like 'Sheet1!A1:D10' or 'A1:D10'

    Returns:
        Dict with sheet_name, start_row, start_col, end_row, end_col (0-indexed)
    """
    sheet_name = None
    cell_range = range_notation

    # Extract sheet name if present
    if '!' in range_notation:
        sheet_name, cell_range = range_notation.split('!', 1)
        # Remove quotes from sheet name if present
        sheet_name = sheet_name.strip("'")

    # Parse the cell range
    if ':' in cell_range:
        start, end = cell_range.split(':')
    else:
        start = end = cell_range

    # Parse start cell
    start_match = re.match(r'^([A-Za-z]+)(\d+)$', start)
    end_match = re.match(r'^([A-Za-z]+)(\d+)$', end)

    result = {"sheet_name": sheet_name}

    if start_match:
        result["start_col"] = col_to_index(start_match.group(1))
        result["start_row"] = int(start_match.group(2)) - 1

    if end_match:
        result["end_col"] = col_to_index(end_match.group(1)) + 1  # Exclusive
        result["end_row"] = int(end_match.group(2))  # Exclusive

    return result


# =============================================================================
# API Helpers
# =============================================================================

async def get_sheet_id(access_token: str, spreadsheet_id: str, sheet_name: Optional[str] = None) -> Optional[int]:
    """Get the sheet ID for a sheet name.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        sheet_name: Sheet name (uses first sheet if None)

    Returns:
        Sheet ID (integer) or None if not found
    """
    _check_httpx()

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{spreadsheet_id}?fields=sheets.properties"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)

        if response.status_code != 200:
            return None

        data = response.json()
        sheets = data.get("sheets", [])

        if not sheets:
            return None

        if sheet_name is None:
            # Return first sheet
            return sheets[0]["properties"]["sheetId"]

        # Find by name
        for sheet in sheets:
            if sheet["properties"]["title"] == sheet_name:
                return sheet["properties"]["sheetId"]

        return None


async def batch_update(access_token: str, spreadsheet_id: str, requests: list) -> dict:
    """Execute a batchUpdate request on a spreadsheet.

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID
        requests: List of update request objects

    Returns:
        Dict with response data, or error
    """
    _check_httpx()

    url = f"{SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {"requests": requests}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                return {"error": f"batchUpdate failed: {error_msg}"}

            return response.json()

        except Exception as e:
            logger.error(f"Error in batchUpdate: {e}")
            return {"error": str(e)}


async def get_spreadsheet_metadata(access_token: str, spreadsheet_id: str) -> dict:
    """Get metadata about a spreadsheet (title, sheets, etc).

    Args:
        access_token: Valid Google OAuth access token
        spreadsheet_id: Google Sheets ID

    Returns:
        Dict with spreadsheet metadata, or error
    """
    _check_httpx()

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SHEETS_API_BASE}/{spreadsheet_id}?fields=properties,sheets.properties"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)

            if response.status_code == 404:
                return {"error": "Spreadsheet not found"}

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"error": error_msg}

            data = response.json()
            props = data.get("properties", {})
            sheets = data.get("sheets", [])

            return {
                "spreadsheet_id": spreadsheet_id,
                "title": props.get("title"),
                "locale": props.get("locale"),
                "timezone": props.get("timeZone"),
                "sheets": [
                    {
                        "title": s["properties"]["title"],
                        "sheet_id": s["properties"]["sheetId"],
                        "index": s["properties"].get("index", 0),
                        "row_count": s["properties"].get("gridProperties", {}).get("rowCount"),
                        "col_count": s["properties"].get("gridProperties", {}).get("columnCount"),
                        "hidden": s["properties"].get("hidden", False),
                    }
                    for s in sheets
                ],
                "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
            }

        except Exception as e:
            logger.error(f"Error getting spreadsheet metadata: {e}")
            return {"error": str(e)}


def build_grid_range(
    sheet_id: int,
    start_row: Optional[int] = None,
    end_row: Optional[int] = None,
    start_col: Optional[int] = None,
    end_col: Optional[int] = None,
) -> dict:
    """Build a GridRange object for the Sheets API.

    Args:
        sheet_id: Sheet ID
        start_row: Start row (0-indexed, inclusive)
        end_row: End row (0-indexed, exclusive)
        start_col: Start column (0-indexed, inclusive)
        end_col: End column (0-indexed, exclusive)

    Returns:
        GridRange dict
    """
    grid_range = {"sheetId": sheet_id}
    if start_row is not None:
        grid_range["startRowIndex"] = start_row
    if end_row is not None:
        grid_range["endRowIndex"] = end_row
    if start_col is not None:
        grid_range["startColumnIndex"] = start_col
    if end_col is not None:
        grid_range["endColumnIndex"] = end_col
    return grid_range
