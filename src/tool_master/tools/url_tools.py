"""
URL and web tools using Microlink API.

Provides URL metadata extraction, screenshots, PDF generation, and URL expansion.
No API key required for basic usage (rate limited).

API Documentation: https://microlink.io/docs/api/getting-started/overview
"""

import asyncio
import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

MICROLINK_BASE = "https://api.microlink.io"


async def _extract_url_metadata_async(url: str) -> dict:
    """Extract metadata from a URL."""
    if not url.strip():
        raise ValueError("URL cannot be empty")

    params = {"url": url}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(MICROLINK_BASE, params=params)

            if response.status_code != 200:
                raise ValueError(f"URL metadata API error: {response.text}")

            result = response.json()

            if result.get("status") == "fail":
                error_msg = result.get("data", {}).get("message", "Failed to fetch URL")
                raise ValueError(f"URL metadata extraction failed: {error_msg}")

            data = result.get("data", {})

            metadata = {
                "url": data.get("url", url),
                "title": data.get("title"),
                "description": data.get("description"),
                "author": data.get("author"),
                "publisher": data.get("publisher"),
                "date": data.get("date"),
                "lang": data.get("lang"),
            }

            # Add image if available
            image = data.get("image")
            if image:
                metadata["image"] = {
                    "url": image.get("url"),
                    "width": image.get("width"),
                    "height": image.get("height"),
                    "type": image.get("type"),
                }

            # Add logo if available
            logo = data.get("logo")
            if logo:
                metadata["logo"] = {
                    "url": logo.get("url"),
                    "width": logo.get("width"),
                    "height": logo.get("height"),
                }

            return metadata

    except httpx.TimeoutException:
        raise ValueError("URL metadata API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"URL metadata API request failed: {str(e)}")


def _extract_url_metadata_sync(url: str) -> dict:
    """Sync wrapper for extract_url_metadata."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _extract_url_metadata_async(url)
                )
                return future.result(timeout=35)
        else:
            return loop.run_until_complete(_extract_url_metadata_async(url))
    except RuntimeError:
        return asyncio.run(_extract_url_metadata_async(url))


async def _take_screenshot_async(
    url: str,
    width: int = 1280,
    height: int = 800,
    full_page: bool = False,
) -> dict:
    """Take a screenshot of a webpage."""
    if not url.strip():
        raise ValueError("URL cannot be empty")

    width = min(max(320, width), 3840)
    height = min(max(240, height), 2160)

    params = {
        "url": url,
        "screenshot": "true",
        "viewport.width": width,
        "viewport.height": height,
    }

    if full_page:
        params["screenshot.fullPage"] = "true"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(MICROLINK_BASE, params=params)

            if response.status_code != 200:
                raise ValueError(f"Screenshot API error: {response.text}")

            result = response.json()

            if result.get("status") == "fail":
                error_msg = result.get("data", {}).get("message", "Failed to capture screenshot")
                raise ValueError(f"Screenshot capture failed: {error_msg}")

            data = result.get("data", {})
            screenshot = data.get("screenshot", {})

            return {
                "url": data.get("url", url),
                "title": data.get("title"),
                "screenshot": {
                    "url": screenshot.get("url"),
                    "width": screenshot.get("width"),
                    "height": screenshot.get("height"),
                    "type": screenshot.get("type"),
                    "size": screenshot.get("size"),
                },
                "viewport": {"width": width, "height": height},
                "full_page": full_page,
            }

    except httpx.TimeoutException:
        raise ValueError("Screenshot API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Screenshot API request failed: {str(e)}")


def _take_screenshot_sync(
    url: str,
    width: int = 1280,
    height: int = 800,
    full_page: bool = False,
) -> dict:
    """Sync wrapper for take_screenshot."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _take_screenshot_async(url, width, height, full_page),
                )
                return future.result(timeout=65)
        else:
            return loop.run_until_complete(
                _take_screenshot_async(url, width, height, full_page)
            )
    except RuntimeError:
        return asyncio.run(_take_screenshot_async(url, width, height, full_page))


async def _generate_pdf_async(url: str) -> dict:
    """Generate a PDF from a webpage."""
    if not url.strip():
        raise ValueError("URL cannot be empty")

    params = {"url": url, "pdf": "true"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(MICROLINK_BASE, params=params)

            if response.status_code != 200:
                raise ValueError(f"PDF generation API error: {response.text}")

            result = response.json()

            if result.get("status") == "fail":
                error_msg = result.get("data", {}).get("message", "Failed to generate PDF")
                raise ValueError(f"PDF generation failed: {error_msg}")

            data = result.get("data", {})
            pdf = data.get("pdf", {})

            return {
                "url": data.get("url", url),
                "title": data.get("title"),
                "pdf": {
                    "url": pdf.get("url"),
                    "size": pdf.get("size"),
                },
            }

    except httpx.TimeoutException:
        raise ValueError("PDF generation API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"PDF generation API request failed: {str(e)}")


def _generate_pdf_sync(url: str) -> dict:
    """Sync wrapper for generate_pdf."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _generate_pdf_async(url))
                return future.result(timeout=65)
        else:
            return loop.run_until_complete(_generate_pdf_async(url))
    except RuntimeError:
        return asyncio.run(_generate_pdf_async(url))


async def _expand_url_async(url: str) -> dict:
    """Expand a shortened URL to its final destination."""
    if not url.strip():
        raise ValueError("URL cannot be empty")

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Use HEAD request to follow redirects without downloading content
            response = await client.head(url)

            # Get the final URL after all redirects
            final_url = str(response.url)

            # Check if there were any redirects
            redirect_history = []
            if response.history:
                for redirect in response.history:
                    redirect_history.append({
                        "url": str(redirect.url),
                        "status_code": redirect.status_code,
                    })

            return {
                "original_url": url,
                "final_url": final_url,
                "is_redirect": url != final_url,
                "redirect_count": len(redirect_history),
                "redirect_history": redirect_history if redirect_history else None,
                "status_code": response.status_code,
            }

    except httpx.TimeoutException:
        raise ValueError("URL expansion request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"URL expansion request failed: {str(e)}")


def _expand_url_sync(url: str) -> dict:
    """Sync wrapper for expand_url."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _expand_url_async(url))
                return future.result(timeout=20)
        else:
            return loop.run_until_complete(_expand_url_async(url))
    except RuntimeError:
        return asyncio.run(_expand_url_async(url))


# Tool definitions

extract_url_metadata = Tool(
    name="extract_url_metadata",
    description="Extract metadata from a URL including title, description, author, images, and other Open Graph/meta information.",
    parameters=[
        ToolParameter(
            name="url",
            type=ParameterType.STRING,
            description="The URL to extract metadata from (e.g., 'https://example.com/article').",
            required=True,
        ),
    ],
    category="url",
    tags=["url", "metadata", "web", "scraping", "opengraph"],
).set_handler(_extract_url_metadata_sync)


take_screenshot = Tool(
    name="take_screenshot",
    description="Capture a screenshot of a webpage. Returns a URL to the generated screenshot image.",
    parameters=[
        ToolParameter(
            name="url",
            type=ParameterType.STRING,
            description="The URL of the webpage to screenshot (e.g., 'https://example.com').",
            required=True,
        ),
        ToolParameter(
            name="width",
            type=ParameterType.INTEGER,
            description="Viewport width in pixels (320-3840). Default is 1280.",
            required=False,
            default=1280,
        ),
        ToolParameter(
            name="height",
            type=ParameterType.INTEGER,
            description="Viewport height in pixels (240-2160). Default is 800.",
            required=False,
            default=800,
        ),
        ToolParameter(
            name="full_page",
            type=ParameterType.BOOLEAN,
            description="Whether to capture the full scrollable page. Default is false (viewport only).",
            required=False,
            default=False,
        ),
    ],
    category="url",
    tags=["url", "screenshot", "web", "image", "capture"],
).set_handler(_take_screenshot_sync)


generate_pdf = Tool(
    name="generate_pdf",
    description="Generate a PDF document from a webpage. Returns a URL to the generated PDF file.",
    parameters=[
        ToolParameter(
            name="url",
            type=ParameterType.STRING,
            description="The URL of the webpage to convert to PDF (e.g., 'https://example.com').",
            required=True,
        ),
    ],
    category="url",
    tags=["url", "pdf", "web", "document", "convert"],
).set_handler(_generate_pdf_sync)


expand_url = Tool(
    name="expand_url",
    description="Expand a shortened URL (like bit.ly, t.co, etc.) to its final destination. Shows the redirect chain.",
    parameters=[
        ToolParameter(
            name="url",
            type=ParameterType.STRING,
            description="The shortened URL to expand (e.g., 'https://bit.ly/xxxxx').",
            required=True,
        ),
    ],
    category="url",
    tags=["url", "redirect", "expand", "shortener"],
).set_handler(_expand_url_sync)
