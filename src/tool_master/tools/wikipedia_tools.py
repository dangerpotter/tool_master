"""
Wikipedia tools using Wikipedia's REST API.

Provides search, article summaries, and random article retrieval.
"""

import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

WIKI_API_BASE = "https://en.wikipedia.org/w/rest.php/v1"
WIKI_SUMMARY_BASE = "https://en.wikipedia.org/api/rest_v1/page/summary"
USER_AGENT = "ToolMaster/1.0 (LLM tool library)"


async def _search_wikipedia_async(query: str, limit: int = 5) -> dict:
    """
    Search Wikipedia for articles matching a query (async).

    Args:
        query: Search terms
        limit: Maximum number of results (1-20)

    Returns:
        dict with search results
    """
    if not query or not query.strip():
        raise ValueError("Search query is required")

    query = query.strip()
    limit = max(1, min(20, limit))

    params = {"q": query, "limit": limit}
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WIKI_API_BASE}/search/page",
                params=params,
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Wikipedia search error {response.status_code}: {response.text}")
                raise ValueError(f"Wikipedia API error: {response.status_code}")

            data = response.json()
            pages = data.get("pages", [])

            if not pages:
                return {
                    "query": query,
                    "results": [],
                    "message": f"No Wikipedia articles found for '{query}'"
                }

            results = []
            for page in pages[:limit]:
                results.append({
                    "title": page.get("title"),
                    "description": page.get("description", ""),
                    "excerpt": page.get("excerpt", ""),
                    "key": page.get("key"),
                    "url": f"https://en.wikipedia.org/wiki/{page.get('key', '')}"
                })

            return {
                "query": query,
                "results": results,
                "count": len(results)
            }

    except httpx.TimeoutException:
        logger.error("Wikipedia search request timed out")
        raise ValueError("Wikipedia search timed out")
    except httpx.RequestError as e:
        logger.error(f"Wikipedia search request error: {e}")
        raise ValueError(f"Wikipedia request failed: {str(e)}")


async def _get_wikipedia_article_async(title: str) -> dict:
    """
    Get the summary/intro of a Wikipedia article (async).

    Args:
        title: Article title (can use spaces or underscores)

    Returns:
        dict with article summary
    """
    if not title or not title.strip():
        raise ValueError("Article title is required")

    title = title.strip()
    url_title = title.replace(" ", "_")

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                f"{WIKI_SUMMARY_BASE}/{url_title}",
                headers=headers
            )

            if response.status_code == 404:
                return {
                    "title": title,
                    "exists": False,
                    "error": f"No Wikipedia article found for '{title}'"
                }

            if response.status_code != 200:
                logger.error(f"Wikipedia summary error {response.status_code}: {response.text}")
                raise ValueError(f"Wikipedia API error: {response.status_code}")

            data = response.json()
            page_type = data.get("type", "standard")

            result = {
                "title": data.get("title"),
                "display_title": data.get("displaytitle"),
                "description": data.get("description", ""),
                "extract": data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "exists": True,
                "type": page_type
            }

            # Add thumbnail if available
            thumbnail = data.get("thumbnail")
            if thumbnail:
                result["thumbnail"] = {
                    "url": thumbnail.get("source"),
                    "width": thumbnail.get("width"),
                    "height": thumbnail.get("height")
                }

            # Add original image if available
            original = data.get("originalimage")
            if original:
                result["image"] = {
                    "url": original.get("source"),
                    "width": original.get("width"),
                    "height": original.get("height")
                }

            # Add coordinates if available
            coordinates = data.get("coordinates")
            if coordinates:
                result["coordinates"] = {
                    "latitude": coordinates.get("lat"),
                    "longitude": coordinates.get("lon")
                }

            if page_type == "disambiguation":
                result["message"] = "This is a disambiguation page - search for a more specific term"

            return result

    except httpx.TimeoutException:
        logger.error("Wikipedia summary request timed out")
        raise ValueError("Wikipedia request timed out")
    except httpx.RequestError as e:
        logger.error(f"Wikipedia summary request error: {e}")
        raise ValueError(f"Wikipedia request failed: {str(e)}")


async def _get_random_wikipedia_article_async() -> dict:
    """
    Get a random Wikipedia article summary (async).

    Returns:
        dict with random article summary
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                "https://en.wikipedia.org/api/rest_v1/page/random/summary",
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Wikipedia random error {response.status_code}: {response.text}")
                raise ValueError(f"Wikipedia API error: {response.status_code}")

            data = response.json()

            result = {
                "title": data.get("title"),
                "display_title": data.get("displaytitle"),
                "description": data.get("description", ""),
                "extract": data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "exists": True,
                "type": data.get("type", "standard")
            }

            thumbnail = data.get("thumbnail")
            if thumbnail:
                result["thumbnail"] = {
                    "url": thumbnail.get("source"),
                    "width": thumbnail.get("width"),
                    "height": thumbnail.get("height")
                }

            return result

    except httpx.TimeoutException:
        logger.error("Wikipedia random request timed out")
        raise ValueError("Wikipedia request timed out")
    except httpx.RequestError as e:
        logger.error(f"Wikipedia random request error: {e}")
        raise ValueError(f"Wikipedia request failed: {str(e)}")


# Sync wrappers
def _run_async(coro):
    """Run an async coroutine synchronously."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _search_wikipedia(query: str, limit: int = 5) -> dict:
    """Search Wikipedia (sync wrapper)."""
    return _run_async(_search_wikipedia_async(query, limit))


def _get_wikipedia_article(title: str) -> dict:
    """Get Wikipedia article (sync wrapper)."""
    return _run_async(_get_wikipedia_article_async(title))


def _get_random_wikipedia_article() -> dict:
    """Get random Wikipedia article (sync wrapper)."""
    return _run_async(_get_random_wikipedia_article_async())


# Tool definitions
search_wikipedia = Tool(
    name="search_wikipedia",
    description="Search Wikipedia for articles matching a query. Returns titles, descriptions, and excerpts.",
    parameters=[
        ToolParameter(
            name="query",
            type=ParameterType.STRING,
            description="Search terms to find Wikipedia articles (e.g., 'Albert Einstein', 'quantum mechanics', 'World War II')",
            required=True,
        ),
        ToolParameter(
            name="limit",
            type=ParameterType.INTEGER,
            description="Maximum number of results to return (1-20)",
            required=False,
            default=5,
        ),
    ],
    category="knowledge",
    tags=["wikipedia", "search", "knowledge", "encyclopedia"],
).set_handler(_search_wikipedia)


get_wikipedia_article = Tool(
    name="get_wikipedia_article",
    description="Get the summary/introduction of a specific Wikipedia article. Returns the extract, description, URL, and image if available.",
    parameters=[
        ToolParameter(
            name="title",
            type=ParameterType.STRING,
            description="The exact title of the Wikipedia article (e.g., 'Albert Einstein', 'Python (programming language)')",
            required=True,
        ),
    ],
    category="knowledge",
    tags=["wikipedia", "article", "knowledge", "encyclopedia"],
).set_handler(_get_wikipedia_article)


get_random_wikipedia_article = Tool(
    name="get_random_wikipedia_article",
    description="Get a random Wikipedia article summary. Useful for learning something new or when users want a random fact.",
    parameters=[],
    category="knowledge",
    tags=["wikipedia", "random", "knowledge", "encyclopedia"],
).set_handler(_get_random_wikipedia_article)
