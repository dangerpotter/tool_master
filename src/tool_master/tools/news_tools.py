"""
News tools using NewsAPI.

Provides news search, top headlines, and news source discovery.
Requires NEWS_API_KEY environment variable.

API Documentation: https://newsapi.org/docs
"""

import asyncio
import logging
import os
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

NEWS_API_BASE = "https://newsapi.org/v2"
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def _get_api_key() -> str:
    """Get the NewsAPI key from environment."""
    key = os.getenv("NEWS_API_KEY") or NEWS_API_KEY
    if not key:
        raise ValueError(
            "NEWS_API_KEY environment variable not set. "
            "Get a free API key at https://newsapi.org/register"
        )
    return key


async def _search_news_async(
    query: str,
    language: str = "en",
    sort_by: str = "relevancy",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page_size: int = 10,
) -> dict:
    """Search for news articles by keyword."""
    api_key = _get_api_key()

    if not query.strip():
        raise ValueError("Search query cannot be empty")

    page_size = min(max(1, page_size), 100)

    params = {
        "q": query,
        "language": language,
        "sortBy": sort_by,
        "pageSize": page_size,
        "apiKey": api_key,
    }

    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{NEWS_API_BASE}/everything", params=params)

            data = response.json()

            if data.get("status") == "error":
                error_msg = data.get("message", "Unknown error")
                raise ValueError(f"NewsAPI error: {error_msg}")

            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "author": article.get("author"),
                    "source": article.get("source", {}).get("name"),
                    "url": article.get("url"),
                    "image_url": article.get("urlToImage"),
                    "published_at": article.get("publishedAt"),
                })

            return {
                "query": query,
                "total_results": data.get("totalResults", 0),
                "articles_returned": len(articles),
                "articles": articles,
            }

    except httpx.TimeoutException:
        raise ValueError("NewsAPI request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"NewsAPI request failed: {str(e)}")


def _search_news_sync(
    query: str,
    language: str = "en",
    sort_by: str = "relevancy",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page_size: int = 10,
) -> dict:
    """Sync wrapper for search_news."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _search_news_async(
                        query, language, sort_by, from_date, to_date, page_size
                    ),
                )
                return future.result(timeout=20)
        else:
            return loop.run_until_complete(
                _search_news_async(
                    query, language, sort_by, from_date, to_date, page_size
                )
            )
    except RuntimeError:
        return asyncio.run(
            _search_news_async(query, language, sort_by, from_date, to_date, page_size)
        )


async def _get_top_headlines_async(
    country: str = "us",
    category: Optional[str] = None,
    query: Optional[str] = None,
    page_size: int = 10,
) -> dict:
    """Get top news headlines."""
    api_key = _get_api_key()

    page_size = min(max(1, page_size), 100)

    params = {
        "country": country,
        "pageSize": page_size,
        "apiKey": api_key,
    }

    if category:
        params["category"] = category
    if query:
        params["q"] = query

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{NEWS_API_BASE}/top-headlines", params=params)

            data = response.json()

            if data.get("status") == "error":
                error_msg = data.get("message", "Unknown error")
                raise ValueError(f"NewsAPI error: {error_msg}")

            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "author": article.get("author"),
                    "source": article.get("source", {}).get("name"),
                    "url": article.get("url"),
                    "image_url": article.get("urlToImage"),
                    "published_at": article.get("publishedAt"),
                })

            return {
                "country": country,
                "category": category,
                "total_results": data.get("totalResults", 0),
                "articles_returned": len(articles),
                "articles": articles,
            }

    except httpx.TimeoutException:
        raise ValueError("NewsAPI request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"NewsAPI request failed: {str(e)}")


def _get_top_headlines_sync(
    country: str = "us",
    category: Optional[str] = None,
    query: Optional[str] = None,
    page_size: int = 10,
) -> dict:
    """Sync wrapper for get_top_headlines."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _get_top_headlines_async(country, category, query, page_size),
                )
                return future.result(timeout=20)
        else:
            return loop.run_until_complete(
                _get_top_headlines_async(country, category, query, page_size)
            )
    except RuntimeError:
        return asyncio.run(
            _get_top_headlines_async(country, category, query, page_size)
        )


async def _get_news_sources_async(
    category: Optional[str] = None,
    language: Optional[str] = None,
    country: Optional[str] = None,
) -> dict:
    """Get available news sources."""
    api_key = _get_api_key()

    params = {"apiKey": api_key}

    if category:
        params["category"] = category
    if language:
        params["language"] = language
    if country:
        params["country"] = country

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{NEWS_API_BASE}/top-headlines/sources", params=params)

            data = response.json()

            if data.get("status") == "error":
                error_msg = data.get("message", "Unknown error")
                raise ValueError(f"NewsAPI error: {error_msg}")

            sources = []
            for source in data.get("sources", []):
                sources.append({
                    "id": source.get("id"),
                    "name": source.get("name"),
                    "description": source.get("description"),
                    "url": source.get("url"),
                    "category": source.get("category"),
                    "language": source.get("language"),
                    "country": source.get("country"),
                })

            return {
                "filters": {
                    "category": category,
                    "language": language,
                    "country": country,
                },
                "count": len(sources),
                "sources": sources,
            }

    except httpx.TimeoutException:
        raise ValueError("NewsAPI request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"NewsAPI request failed: {str(e)}")


def _get_news_sources_sync(
    category: Optional[str] = None,
    language: Optional[str] = None,
    country: Optional[str] = None,
) -> dict:
    """Sync wrapper for get_news_sources."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _get_news_sources_async(category, language, country),
                )
                return future.result(timeout=20)
        else:
            return loop.run_until_complete(
                _get_news_sources_async(category, language, country)
            )
    except RuntimeError:
        return asyncio.run(_get_news_sources_async(category, language, country))


# Tool definitions

search_news = Tool(
    name="search_news",
    description="Search for news articles by keyword. Returns articles from thousands of sources worldwide. Requires NEWS_API_KEY.",
    parameters=[
        ToolParameter(
            name="query",
            type=ParameterType.STRING,
            description="Keywords or phrases to search for in article titles and bodies.",
            required=True,
        ),
        ToolParameter(
            name="language",
            type=ParameterType.STRING,
            description="Language code for articles (e.g., 'en', 'es', 'fr', 'de'). Default is 'en'.",
            required=False,
            default="en",
        ),
        ToolParameter(
            name="sort_by",
            type=ParameterType.STRING,
            description="How to sort results: 'relevancy', 'popularity', or 'publishedAt'. Default is 'relevancy'.",
            required=False,
            default="relevancy",
            enum=["relevancy", "popularity", "publishedAt"],
        ),
        ToolParameter(
            name="from_date",
            type=ParameterType.STRING,
            description="Oldest article date in ISO 8601 format (e.g., '2024-01-15' or '2024-01-15T00:00:00').",
            required=False,
        ),
        ToolParameter(
            name="to_date",
            type=ParameterType.STRING,
            description="Newest article date in ISO 8601 format.",
            required=False,
        ),
        ToolParameter(
            name="page_size",
            type=ParameterType.INTEGER,
            description="Number of articles to return (1-100). Default is 10.",
            required=False,
            default=10,
        ),
    ],
    category="news",
    tags=["news", "search", "articles", "media"],
).set_handler(_search_news_sync)


get_top_headlines = Tool(
    name="get_top_headlines",
    description="Get top news headlines by country and/or category. Returns breaking news and headlines. Requires NEWS_API_KEY.",
    parameters=[
        ToolParameter(
            name="country",
            type=ParameterType.STRING,
            description="Two-letter country code (e.g., 'us', 'gb', 'de', 'fr'). Default is 'us'.",
            required=False,
            default="us",
        ),
        ToolParameter(
            name="category",
            type=ParameterType.STRING,
            description="News category to filter by.",
            required=False,
            enum=[
                "business",
                "entertainment",
                "general",
                "health",
                "science",
                "sports",
                "technology",
            ],
        ),
        ToolParameter(
            name="query",
            type=ParameterType.STRING,
            description="Keywords to filter headlines by.",
            required=False,
        ),
        ToolParameter(
            name="page_size",
            type=ParameterType.INTEGER,
            description="Number of headlines to return (1-100). Default is 10.",
            required=False,
            default=10,
        ),
    ],
    category="news",
    tags=["news", "headlines", "breaking", "media"],
).set_handler(_get_top_headlines_sync)


get_news_sources = Tool(
    name="get_news_sources",
    description="Get available news sources. Filter by category, language, or country. Requires NEWS_API_KEY.",
    parameters=[
        ToolParameter(
            name="category",
            type=ParameterType.STRING,
            description="News category to filter sources by.",
            required=False,
            enum=[
                "business",
                "entertainment",
                "general",
                "health",
                "science",
                "sports",
                "technology",
            ],
        ),
        ToolParameter(
            name="language",
            type=ParameterType.STRING,
            description="Language code to filter sources by (e.g., 'en', 'es', 'fr').",
            required=False,
        ),
        ToolParameter(
            name="country",
            type=ParameterType.STRING,
            description="Two-letter country code to filter sources by (e.g., 'us', 'gb').",
            required=False,
        ),
    ],
    category="news",
    tags=["news", "sources", "media", "publishers"],
).set_handler(_get_news_sources_sync)
