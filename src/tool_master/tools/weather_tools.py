"""
Weather tools using WeatherAPI.com.

Provides current weather conditions and forecasts for any location.
Requires WEATHER_API_KEY environment variable.
"""

import os
import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_BASE = "https://api.weatherapi.com/v1"


def _format_weather_response(data: dict) -> dict:
    """Format the WeatherAPI response into a concise, useful format."""
    location = data.get("location", {})
    current = data.get("current", {})
    forecast = data.get("forecast", {}).get("forecastday", [])
    alerts = data.get("alerts", {}).get("alert", [])

    result = {
        "location": {
            "name": location.get("name"),
            "region": location.get("region"),
            "country": location.get("country"),
            "localtime": location.get("localtime"),
            "timezone": location.get("tz_id")
        },
        "current": {
            "temp_f": current.get("temp_f"),
            "temp_c": current.get("temp_c"),
            "feels_like_f": current.get("feelslike_f"),
            "feels_like_c": current.get("feelslike_c"),
            "condition": current.get("condition", {}).get("text"),
            "humidity": current.get("humidity"),
            "wind_mph": current.get("wind_mph"),
            "wind_dir": current.get("wind_dir"),
            "uv": current.get("uv"),
            "visibility_miles": current.get("vis_miles")
        },
        "forecast": [],
        "alerts": []
    }

    # Add air quality if available
    aqi = current.get("air_quality", {})
    if aqi:
        result["current"]["air_quality"] = {
            "us_epa_index": aqi.get("us-epa-index"),
            "pm2_5": round(aqi.get("pm2_5", 0), 1),
            "pm10": round(aqi.get("pm10", 0), 1)
        }

    # Format forecast days
    for day in forecast:
        day_data = day.get("day", {})
        result["forecast"].append({
            "date": day.get("date"),
            "high_f": day_data.get("maxtemp_f"),
            "low_f": day_data.get("mintemp_f"),
            "high_c": day_data.get("maxtemp_c"),
            "low_c": day_data.get("mintemp_c"),
            "condition": day_data.get("condition", {}).get("text"),
            "chance_of_rain": day_data.get("daily_chance_of_rain"),
            "chance_of_snow": day_data.get("daily_chance_of_snow"),
            "sunrise": day.get("astro", {}).get("sunrise"),
            "sunset": day.get("astro", {}).get("sunset")
        })

    # Add weather alerts (limit to 3)
    for alert in alerts[:3]:
        result["alerts"].append({
            "headline": alert.get("headline"),
            "severity": alert.get("severity"),
            "event": alert.get("event"),
            "effective": alert.get("effective"),
            "expires": alert.get("expires")
        })

    return result


async def _get_weather_async(location: str, days: int = 1) -> dict:
    """
    Get current weather and forecast for a location (async).

    Args:
        location: City name, address, lat/lon, or postal code
        days: Number of forecast days (1-7)

    Returns:
        dict with weather data or error message
    """
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        logger.error("WEATHER_API_KEY not set in environment")
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")

    days = max(1, min(7, days))

    params = {
        "key": api_key,
        "q": location,
        "days": days,
        "aqi": "yes",
        "alerts": "yes"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WEATHER_API_BASE}/forecast.json",
                params=params
            )

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                logger.error(f"Weather API error {response.status_code}: {error_msg}")
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            return _format_weather_response(data)

    except httpx.TimeoutException:
        logger.error("Weather API request timed out")
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        logger.error(f"Weather API request error: {e}")
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_weather_sync(location: str, days: int = 1) -> dict:
    """
    Get current weather and forecast for a location (sync).

    Args:
        location: City name, address, lat/lon, or postal code
        days: Number of forecast days (1-7)

    Returns:
        dict with weather data
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _get_weather_async(location, days)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_weather_async(location, days))
    except RuntimeError:
        return asyncio.run(_get_weather_async(location, days))


# Tool definition
get_weather = Tool(
    name="get_weather",
    description="Get current weather conditions and forecast for a location. Returns temperature, conditions, humidity, wind, UV index, air quality, and multi-day forecast.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The location to get weather for. Can be a city name (e.g., 'London'), city and country (e.g., 'Paris, France'), US zip code (e.g., '10001'), UK postcode, or coordinates (e.g., '48.8567,2.3508').",
            required=True,
        ),
        ToolParameter(
            name="days",
            type=ParameterType.INTEGER,
            description="Number of forecast days to include (1-7). Default is 1 for just today.",
            required=False,
            default=1,
        ),
    ],
    category="weather",
    tags=["weather", "forecast", "temperature", "conditions"],
).set_handler(_get_weather_sync)
