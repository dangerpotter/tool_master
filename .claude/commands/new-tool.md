---
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "AskUserQuestion"]
argument-hint: "<tool_name> <category>"
description: "Scaffold a new tool file with handler and Tool definition"
---

# New Tool Scaffolding

Create a new tool file for Tool Master following project conventions.

## Arguments
Parse `$ARGUMENTS` to extract:
- **tool_name**: First argument (e.g., "dice" creates `dice_tools.py`)
- **category**: Second argument (e.g., "games")

If arguments are missing, ask the user for them.

## Context

### Existing tool files:
! dir /b src\tool_master\tools\*.py

### Reference files:
@src/tool_master/schemas/tool.py
@src/tool_master/tools/dice_tools.py
@src/tool_master/tools/currency_tools.py
@src/tool_master/tools/weather_tools.py
@src/tool_master/tools/__init__.py

## Instructions

### Step 1: Ask for template type
Use AskUserQuestion to ask which template to use:

1. **Standalone** - No external dependencies, sync handler only (like dice_tools.py)
2. **No-Auth API** - Uses httpx for HTTP requests, no API key needed (like currency_tools.py)
3. **API Key Required** - Uses httpx + requires environment variable for API key (like weather_tools.py)

### Step 2: Create the tool file

Create `src/tool_master/tools/{tool_name}_tools.py` using the appropriate template below.

#### Standalone Template
```python
"""
{Category} tools.

Description of what these tools do.
"""

from typing import Optional

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter


def _{tool_name}_handler(param1: str) -> dict:
    """
    Handler description.

    Args:
        param1: Description of param1

    Returns:
        dict with results
    """
    # TODO: Implement
    return {"result": param1}


{tool_name} = Tool(
    name="{tool_name}",
    description="Description of what the tool does",
    parameters=[
        ToolParameter(
            name="param1",
            type=ParameterType.STRING,
            description="What this parameter does",
            required=True,
        ),
    ],
    category="{category}",
    tags=["{category}", "{tool_name}"],
).set_handler(_{tool_name}_handler)
```

#### No-Auth API Template
```python
"""
{Category} tools using [API Name].

Description of what these tools do.
No API key required.

API Documentation: https://example.com/docs
"""

import asyncio
import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

API_BASE = "https://api.example.com"


async def _{tool_name}_async(param1: str) -> dict:
    """
    Async implementation.

    Args:
        param1: Description of param1

    Returns:
        dict with results
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/endpoint", params={"q": param1})

            if response.status_code != 200:
                raise ValueError(f"API error: {response.text}")

            data = response.json()
            return {"result": data}

    except httpx.TimeoutException:
        raise ValueError("API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"API request failed: {str(e)}")


def _{tool_name}_sync(param1: str) -> dict:
    """Sync wrapper for {tool_name}."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _{tool_name}_async(param1),
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_{tool_name}_async(param1))
    except RuntimeError:
        return asyncio.run(_{tool_name}_async(param1))


{tool_name} = Tool(
    name="{tool_name}",
    description="Description of what the tool does",
    parameters=[
        ToolParameter(
            name="param1",
            type=ParameterType.STRING,
            description="What this parameter does",
            required=True,
        ),
    ],
    category="{category}",
    tags=["{category}", "{tool_name}"],
).set_handler(_{tool_name}_sync)
```

#### API Key Required Template
```python
"""
{Category} tools using [API Name].

Description of what these tools do.
Requires {TOOL_NAME_UPPER}_API_KEY environment variable.

API Documentation: https://example.com/docs
"""

import asyncio
import logging
import os
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

{TOOL_NAME_UPPER}_API_KEY = os.getenv("{TOOL_NAME_UPPER}_API_KEY")
API_BASE = "https://api.example.com"


async def _{tool_name}_async(param1: str) -> dict:
    """
    Async implementation.

    Args:
        param1: Description of param1

    Returns:
        dict with results
    """
    api_key = os.getenv("{TOOL_NAME_UPPER}_API_KEY") or {TOOL_NAME_UPPER}_API_KEY
    if not api_key:
        raise ValueError(
            "{TOOL_NAME_UPPER}_API_KEY not configured. "
            "Set the {TOOL_NAME_UPPER}_API_KEY environment variable."
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_BASE}/endpoint",
                params={"key": api_key, "q": param1},
            )

            if response.status_code != 200:
                raise ValueError(f"API error: {response.text}")

            data = response.json()
            return {"result": data}

    except httpx.TimeoutException:
        raise ValueError("API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"API request failed: {str(e)}")


def _{tool_name}_sync(param1: str) -> dict:
    """Sync wrapper for {tool_name}."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _{tool_name}_async(param1),
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_{tool_name}_async(param1))
    except RuntimeError:
        return asyncio.run(_{tool_name}_async(param1))


{tool_name} = Tool(
    name="{tool_name}",
    description="Description of what the tool does",
    parameters=[
        ToolParameter(
            name="param1",
            type=ParameterType.STRING,
            description="What this parameter does",
            required=True,
        ),
    ],
    category="{category}",
    tags=["{category}", "{tool_name}"],
).set_handler(_{tool_name}_sync)
```

### Step 3: Update exports

Edit `src/tool_master/tools/__init__.py`:

1. Add import in the appropriate section (create new category comment if needed):
```python
# {Category} tools
from tool_master.tools.{tool_name}_tools import (
    {tool_name},
)
```

2. Add to `__all__` list in corresponding section:
```python
    # {Category}
    "{tool_name}",
```

### Step 4: Summary

After creating the file and updating exports, summarize:
- File created: `src/tool_master/tools/{tool_name}_tools.py`
- Template used: (Standalone/No-Auth API/API Key Required)
- Exports updated in `__init__.py`
- Remind user to implement the actual handler logic and update CLAUDE.md tool count if needed
