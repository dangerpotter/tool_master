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


def _format_hourly_response(data: dict) -> dict:
    """Format the WeatherAPI response to extract hourly forecasts."""
    location = data.get("location", {})
    forecast_days = data.get("forecast", {}).get("forecastday", [])

    result = {
        "location": {
            "name": location.get("name"),
            "region": location.get("region"),
            "country": location.get("country"),
            "localtime": location.get("localtime"),
            "timezone": location.get("tz_id"),
        },
        "hourly_forecast": [],
    }

    # Extract hourly data from each forecast day
    for day in forecast_days:
        hours = day.get("hour", [])
        for hour in hours:
            result["hourly_forecast"].append({
                "time": hour.get("time"),
                "temp_f": hour.get("temp_f"),
                "temp_c": hour.get("temp_c"),
                "feels_like_f": hour.get("feelslike_f"),
                "feels_like_c": hour.get("feelslike_c"),
                "condition": hour.get("condition", {}).get("text"),
                "chance_of_rain": hour.get("chance_of_rain"),
                "chance_of_snow": hour.get("chance_of_snow"),
                "humidity": hour.get("humidity"),
                "wind_mph": hour.get("wind_mph"),
                "wind_dir": hour.get("wind_dir"),
                "uv": hour.get("uv"),
                "visibility_miles": hour.get("vis_miles"),
                "precip_in": hour.get("precip_in"),
            })

    return result


async def _get_hourly_weather_async(location: str, days: int = 1) -> dict:
    """
    Get hourly weather forecast for a location (async).

    Args:
        location: City name, address, lat/lon, or postal code
        days: Number of forecast days (1-3, WeatherAPI free tier limit for hourly)

    Returns:
        dict with hourly weather data
    """
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        logger.error("WEATHER_API_KEY not set in environment")
        raise ValueError(
            "Weather API key not configured. Set WEATHER_API_KEY environment variable."
        )

    if not location:
        raise ValueError("Location is required")

    # Limit to 3 days for hourly data (API limitation)
    days = max(1, min(3, days))

    params = {
        "key": api_key,
        "q": location,
        "days": days,
        "aqi": "no",
        "alerts": "no",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WEATHER_API_BASE}/forecast.json", params=params
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
            return _format_hourly_response(data)

    except httpx.TimeoutException:
        logger.error("Weather API request timed out")
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        logger.error(f"Weather API request error: {e}")
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_hourly_weather_sync(location: str, days: int = 1) -> dict:
    """Sync wrapper for get_hourly_weather."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _get_hourly_weather_async(location, days)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_hourly_weather_async(location, days))
    except RuntimeError:
        return asyncio.run(_get_hourly_weather_async(location, days))


get_hourly_weather = Tool(
    name="get_hourly_weather",
    description="Get hourly weather forecast for a location. Returns hour-by-hour temperature, conditions, precipitation chances, humidity, and wind for up to 3 days.",
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
            description="Number of forecast days to include (1-3). Default is 1. Each day includes 24 hourly forecasts.",
            required=False,
            default=1,
        ),
    ],
    category="weather",
    tags=["weather", "forecast", "hourly", "temperature", "conditions"],
).set_handler(_get_hourly_weather_sync)


# =============================================================================
# search_weather_locations - Location autocomplete/search
# =============================================================================


async def _search_weather_locations_async(query: str) -> dict:
    """Search for locations matching a query (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not query:
        raise ValueError("Query is required")

    params = {"key": api_key, "q": query}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/search.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            return {
                "query": query,
                "results": [
                    {
                        "name": loc.get("name"),
                        "region": loc.get("region"),
                        "country": loc.get("country"),
                        "lat": loc.get("lat"),
                        "lon": loc.get("lon"),
                        "id": loc.get("id"),
                    }
                    for loc in data
                ],
            }

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _search_weather_locations_sync(query: str) -> dict:
    """Sync wrapper for search_weather_locations."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _search_weather_locations_async(query))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_search_weather_locations_async(query))
    except RuntimeError:
        return asyncio.run(_search_weather_locations_async(query))


search_weather_locations = Tool(
    name="search_weather_locations",
    description="Search for locations by name for weather queries. Returns matching locations with coordinates. Useful for autocomplete or finding the exact location ID.",
    parameters=[
        ToolParameter(
            name="query",
            type=ParameterType.STRING,
            description="Partial or full location name to search for (e.g., 'Lon' will match London, Long Beach, etc.)",
            required=True,
        ),
    ],
    category="weather",
    tags=["weather", "location", "search", "autocomplete"],
).set_handler(_search_weather_locations_sync)


# =============================================================================
# get_weather_alerts - Severe weather alerts
# =============================================================================


async def _get_weather_alerts_async(location: str) -> dict:
    """Get weather alerts for a location (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")

    params = {"key": api_key, "q": location}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/alerts.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            location_data = data.get("location", {})
            alerts = data.get("alerts", {}).get("alert", [])

            return {
                "location": {
                    "name": location_data.get("name"),
                    "region": location_data.get("region"),
                    "country": location_data.get("country"),
                    "localtime": location_data.get("localtime"),
                },
                "alert_count": len(alerts),
                "alerts": [
                    {
                        "headline": alert.get("headline"),
                        "severity": alert.get("severity"),
                        "urgency": alert.get("urgency"),
                        "event": alert.get("event"),
                        "category": alert.get("category"),
                        "certainty": alert.get("certainty"),
                        "effective": alert.get("effective"),
                        "expires": alert.get("expires"),
                        "areas": alert.get("areas"),
                        "description": alert.get("desc"),
                        "instruction": alert.get("instruction"),
                    }
                    for alert in alerts
                ],
            }

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_weather_alerts_sync(location: str) -> dict:
    """Sync wrapper for get_weather_alerts."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_weather_alerts_async(location))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_weather_alerts_async(location))
    except RuntimeError:
        return asyncio.run(_get_weather_alerts_async(location))


get_weather_alerts = Tool(
    name="get_weather_alerts",
    description="Get severe weather alerts and warnings for a location. Returns government-issued alerts including floods, storms, heat waves, and other weather emergencies with severity, urgency, and safety instructions.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The location to get alerts for. Can be a city name, coordinates, zip code, etc.",
            required=True,
        ),
    ],
    category="weather",
    tags=["weather", "alerts", "warnings", "severe", "emergency"],
).set_handler(_get_weather_alerts_sync)


# =============================================================================
# get_air_quality - Dedicated air quality data
# =============================================================================


async def _get_air_quality_async(location: str) -> dict:
    """Get air quality data for a location (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")

    params = {"key": api_key, "q": location, "aqi": "yes"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/current.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            location_data = data.get("location", {})
            aqi = data.get("current", {}).get("air_quality", {})

            # Map EPA index to description
            epa_descriptions = {
                1: "Good",
                2: "Moderate",
                3: "Unhealthy for sensitive groups",
                4: "Unhealthy",
                5: "Very Unhealthy",
                6: "Hazardous",
            }

            # Map UK DEFRA index to band
            defra_bands = {
                1: "Low", 2: "Low", 3: "Low",
                4: "Moderate", 5: "Moderate", 6: "Moderate",
                7: "High", 8: "High", 9: "High",
                10: "Very High",
            }

            us_epa = aqi.get("us-epa-index")
            gb_defra = aqi.get("gb-defra-index")

            return {
                "location": {
                    "name": location_data.get("name"),
                    "region": location_data.get("region"),
                    "country": location_data.get("country"),
                    "localtime": location_data.get("localtime"),
                },
                "air_quality": {
                    "us_epa_index": us_epa,
                    "us_epa_description": epa_descriptions.get(us_epa, "Unknown"),
                    "gb_defra_index": gb_defra,
                    "gb_defra_band": defra_bands.get(gb_defra, "Unknown"),
                    "pollutants": {
                        "co": {"value": round(aqi.get("co", 0), 2), "unit": "μg/m³", "name": "Carbon Monoxide"},
                        "no2": {"value": round(aqi.get("no2", 0), 2), "unit": "μg/m³", "name": "Nitrogen Dioxide"},
                        "o3": {"value": round(aqi.get("o3", 0), 2), "unit": "μg/m³", "name": "Ozone"},
                        "so2": {"value": round(aqi.get("so2", 0), 2), "unit": "μg/m³", "name": "Sulphur Dioxide"},
                        "pm2_5": {"value": round(aqi.get("pm2_5", 0), 2), "unit": "μg/m³", "name": "PM2.5"},
                        "pm10": {"value": round(aqi.get("pm10", 0), 2), "unit": "μg/m³", "name": "PM10"},
                    },
                },
            }

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_air_quality_sync(location: str) -> dict:
    """Sync wrapper for get_air_quality."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_air_quality_async(location))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_air_quality_async(location))
    except RuntimeError:
        return asyncio.run(_get_air_quality_async(location))


get_air_quality = Tool(
    name="get_air_quality",
    description="Get detailed air quality data for a location. Returns US EPA index, UK DEFRA index, and pollutant levels (CO, NO2, O3, SO2, PM2.5, PM10) with health descriptions.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The location to get air quality for. Can be a city name, coordinates, zip code, etc.",
            required=True,
        ),
    ],
    category="weather",
    tags=["weather", "air quality", "pollution", "aqi", "health"],
).set_handler(_get_air_quality_sync)


# =============================================================================
# get_timezone - Timezone information
# =============================================================================


async def _get_timezone_async(location: str) -> dict:
    """Get timezone info for a location (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")

    params = {"key": api_key, "q": location}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/timezone.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            loc = data.get("location", {})

            return {
                "location": {
                    "name": loc.get("name"),
                    "region": loc.get("region"),
                    "country": loc.get("country"),
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon"),
                },
                "timezone": {
                    "id": loc.get("tz_id"),
                    "localtime": loc.get("localtime"),
                    "localtime_epoch": loc.get("localtime_epoch"),
                },
            }

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_timezone_sync(location: str) -> dict:
    """Sync wrapper for get_timezone."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_timezone_async(location))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_timezone_async(location))
    except RuntimeError:
        return asyncio.run(_get_timezone_async(location))


get_timezone = Tool(
    name="get_timezone",
    description="Get timezone information for a location. Returns the timezone ID (e.g., 'America/New_York'), current local time, and coordinates.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The location to get timezone for. Can be a city name, coordinates, zip code, etc.",
            required=True,
        ),
    ],
    category="weather",
    tags=["weather", "timezone", "time", "location"],
).set_handler(_get_timezone_sync)


# =============================================================================
# get_astronomy - Sun and moon data
# =============================================================================


async def _get_astronomy_async(location: str, date: Optional[str] = None) -> dict:
    """Get astronomy data for a location (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")

    params = {"key": api_key, "q": location}
    if date:
        params["dt"] = date

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/astronomy.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            loc = data.get("location", {})
            astro = data.get("astronomy", {}).get("astro", {})

            return {
                "location": {
                    "name": loc.get("name"),
                    "region": loc.get("region"),
                    "country": loc.get("country"),
                    "localtime": loc.get("localtime"),
                },
                "astronomy": {
                    "sunrise": astro.get("sunrise"),
                    "sunset": astro.get("sunset"),
                    "moonrise": astro.get("moonrise"),
                    "moonset": astro.get("moonset"),
                    "moon_phase": astro.get("moon_phase"),
                    "moon_illumination": astro.get("moon_illumination"),
                    "is_moon_up": astro.get("is_moon_up") == 1,
                    "is_sun_up": astro.get("is_sun_up") == 1,
                },
            }

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_astronomy_sync(location: str, date: Optional[str] = None) -> dict:
    """Sync wrapper for get_astronomy."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_astronomy_async(location, date))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_astronomy_async(location, date))
    except RuntimeError:
        return asyncio.run(_get_astronomy_async(location, date))


get_astronomy = Tool(
    name="get_astronomy",
    description="Get astronomy data for a location including sunrise, sunset, moonrise, moonset, moon phase, and moon illumination percentage.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The location to get astronomy data for. Can be a city name, coordinates, zip code, etc.",
            required=True,
        ),
        ToolParameter(
            name="date",
            type=ParameterType.STRING,
            description="Date in YYYY-MM-DD format. Defaults to today if not provided.",
            required=False,
        ),
    ],
    category="weather",
    tags=["weather", "astronomy", "sun", "moon", "sunrise", "sunset"],
).set_handler(_get_astronomy_sync)


# =============================================================================
# get_historical_weather - Past weather data
# =============================================================================


async def _get_historical_weather_async(location: str, date: str) -> dict:
    """Get historical weather data for a location (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")
    if not date:
        raise ValueError("Date is required (YYYY-MM-DD format)")

    params = {"key": api_key, "q": location, "dt": date}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/history.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            loc = data.get("location", {})
            forecast_days = data.get("forecast", {}).get("forecastday", [])

            result = {
                "location": {
                    "name": loc.get("name"),
                    "region": loc.get("region"),
                    "country": loc.get("country"),
                },
                "historical_data": [],
            }

            for day in forecast_days:
                day_data = day.get("day", {})
                astro = day.get("astro", {})
                hours = day.get("hour", [])

                result["historical_data"].append({
                    "date": day.get("date"),
                    "day_summary": {
                        "max_temp_f": day_data.get("maxtemp_f"),
                        "min_temp_f": day_data.get("mintemp_f"),
                        "max_temp_c": day_data.get("maxtemp_c"),
                        "min_temp_c": day_data.get("mintemp_c"),
                        "avg_temp_f": day_data.get("avgtemp_f"),
                        "avg_temp_c": day_data.get("avgtemp_c"),
                        "total_precip_in": day_data.get("totalprecip_in"),
                        "total_precip_mm": day_data.get("totalprecip_mm"),
                        "avg_humidity": day_data.get("avghumidity"),
                        "condition": day_data.get("condition", {}).get("text"),
                        "uv": day_data.get("uv"),
                    },
                    "astro": {
                        "sunrise": astro.get("sunrise"),
                        "sunset": astro.get("sunset"),
                    },
                    "hourly": [
                        {
                            "time": h.get("time"),
                            "temp_f": h.get("temp_f"),
                            "temp_c": h.get("temp_c"),
                            "condition": h.get("condition", {}).get("text"),
                            "humidity": h.get("humidity"),
                            "precip_in": h.get("precip_in"),
                        }
                        for h in hours[::3]  # Every 3 hours to reduce data
                    ],
                })

            return result

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_historical_weather_sync(location: str, date: str) -> dict:
    """Sync wrapper for get_historical_weather."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_historical_weather_async(location, date))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_historical_weather_async(location, date))
    except RuntimeError:
        return asyncio.run(_get_historical_weather_async(location, date))


get_historical_weather = Tool(
    name="get_historical_weather",
    description="Get historical weather data for a past date. Returns temperature, precipitation, humidity, and conditions for any date from January 1, 2010 onwards.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The location to get historical weather for. Can be a city name, coordinates, zip code, etc.",
            required=True,
        ),
        ToolParameter(
            name="date",
            type=ParameterType.STRING,
            description="The historical date in YYYY-MM-DD format. Must be on or after 2010-01-01.",
            required=True,
        ),
    ],
    category="weather",
    tags=["weather", "history", "historical", "past"],
).set_handler(_get_historical_weather_sync)


# =============================================================================
# get_future_weather - Long-range forecast (14-300 days)
# =============================================================================


async def _get_future_weather_async(location: str, date: str) -> dict:
    """Get future weather prediction for a location (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")
    if not date:
        raise ValueError("Date is required (YYYY-MM-DD format, 14-300 days from today)")

    params = {"key": api_key, "q": location, "dt": date}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/future.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            loc = data.get("location", {})
            forecast_days = data.get("forecast", {}).get("forecastday", [])

            result = {
                "location": {
                    "name": loc.get("name"),
                    "region": loc.get("region"),
                    "country": loc.get("country"),
                },
                "future_forecast": [],
            }

            for day in forecast_days:
                day_data = day.get("day", {})
                astro = day.get("astro", {})

                result["future_forecast"].append({
                    "date": day.get("date"),
                    "prediction": {
                        "max_temp_f": day_data.get("maxtemp_f"),
                        "min_temp_f": day_data.get("mintemp_f"),
                        "max_temp_c": day_data.get("maxtemp_c"),
                        "min_temp_c": day_data.get("mintemp_c"),
                        "avg_temp_f": day_data.get("avgtemp_f"),
                        "avg_temp_c": day_data.get("avgtemp_c"),
                        "total_precip_in": day_data.get("totalprecip_in"),
                        "total_precip_mm": day_data.get("totalprecip_mm"),
                        "avg_humidity": day_data.get("avghumidity"),
                        "condition": day_data.get("condition", {}).get("text"),
                        "chance_of_rain": day_data.get("daily_chance_of_rain"),
                        "chance_of_snow": day_data.get("daily_chance_of_snow"),
                        "uv": day_data.get("uv"),
                    },
                    "astro": {
                        "sunrise": astro.get("sunrise"),
                        "sunset": astro.get("sunset"),
                    },
                })

            return result

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_future_weather_sync(location: str, date: str) -> dict:
    """Sync wrapper for get_future_weather."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_future_weather_async(location, date))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_future_weather_async(location, date))
    except RuntimeError:
        return asyncio.run(_get_future_weather_async(location, date))


get_future_weather = Tool(
    name="get_future_weather",
    description="Get long-range weather prediction for a future date (14-300 days ahead). Returns predicted temperature, precipitation, and conditions. Useful for travel planning and events.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The location to get future weather for. Can be a city name, coordinates, zip code, etc.",
            required=True,
        ),
        ToolParameter(
            name="date",
            type=ParameterType.STRING,
            description="The future date in YYYY-MM-DD format. Must be 14-300 days from today.",
            required=True,
        ),
    ],
    category="weather",
    tags=["weather", "future", "prediction", "forecast", "long-range"],
).set_handler(_get_future_weather_sync)


# =============================================================================
# get_marine_weather - Marine/sailing forecast with tides
# =============================================================================


async def _get_marine_weather_async(location: str, days: int = 1) -> dict:
    """Get marine weather for a location (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not location:
        raise ValueError("Location is required")

    days = max(1, min(7, days))
    params = {"key": api_key, "q": location, "days": days, "tides": "yes"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/marine.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()
            loc = data.get("location", {})
            forecast_days = data.get("forecast", {}).get("forecastday", [])

            result = {
                "location": {
                    "name": loc.get("name"),
                    "region": loc.get("region"),
                    "country": loc.get("country"),
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon"),
                },
                "marine_forecast": [],
            }

            for day in forecast_days:
                day_data = day.get("day", {})
                astro = day.get("astro", {})
                tides = day.get("day", {}).get("tides", [{}])[0].get("tide", []) if day.get("day", {}).get("tides") else []
                hours = day.get("hour", [])

                # Get key hourly marine data (every 6 hours)
                marine_hours = []
                for h in hours[::6]:
                    marine_hours.append({
                        "time": h.get("time"),
                        "temp_f": h.get("temp_f"),
                        "temp_c": h.get("temp_c"),
                        "condition": h.get("condition", {}).get("text"),
                        "wind_mph": h.get("wind_mph"),
                        "wind_kph": h.get("wind_kph"),
                        "wind_dir": h.get("wind_dir"),
                        "gust_mph": h.get("gust_mph"),
                        "gust_kph": h.get("gust_kph"),
                        "vis_miles": h.get("vis_miles"),
                        "sig_wave_ht_mt": h.get("sig_ht_mt"),
                        "swell_ht_mt": h.get("swell_ht_mt"),
                        "swell_ht_ft": h.get("swell_ht_ft"),
                        "swell_dir": h.get("swell_dir_16_point"),
                        "swell_period_secs": h.get("swell_period_secs"),
                        "water_temp_f": h.get("water_temp_f"),
                        "water_temp_c": h.get("water_temp_c"),
                    })

                result["marine_forecast"].append({
                    "date": day.get("date"),
                    "day_summary": {
                        "max_temp_f": day_data.get("maxtemp_f"),
                        "min_temp_f": day_data.get("mintemp_f"),
                        "condition": day_data.get("condition", {}).get("text"),
                        "max_wind_mph": day_data.get("maxwind_mph"),
                        "uv": day_data.get("uv"),
                    },
                    "astro": {
                        "sunrise": astro.get("sunrise"),
                        "sunset": astro.get("sunset"),
                        "moonrise": astro.get("moonrise"),
                        "moonset": astro.get("moonset"),
                        "moon_phase": astro.get("moon_phase"),
                    },
                    "tides": [
                        {
                            "time": t.get("tide_time"),
                            "height_mt": t.get("tide_height_mt"),
                            "type": t.get("tide_type"),
                        }
                        for t in tides
                    ],
                    "hourly_marine": marine_hours,
                })

            return result

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_marine_weather_sync(location: str, days: int = 1) -> dict:
    """Sync wrapper for get_marine_weather."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_marine_weather_async(location, days))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_marine_weather_async(location, days))
    except RuntimeError:
        return asyncio.run(_get_marine_weather_async(location, days))


get_marine_weather = Tool(
    name="get_marine_weather",
    description="Get marine and sailing weather forecast including wave height, swell data, water temperature, and tide times. Best for coastal locations or ocean coordinates.",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="Coastal location or ocean coordinates (e.g., 'Miami Beach' or '25.7617,-80.1918').",
            required=True,
        ),
        ToolParameter(
            name="days",
            type=ParameterType.INTEGER,
            description="Number of forecast days (1-7). Default is 1.",
            required=False,
            default=1,
        ),
    ],
    category="weather",
    tags=["weather", "marine", "sailing", "tides", "ocean", "waves"],
).set_handler(_get_marine_weather_sync)


# =============================================================================
# get_sports_events - Sports events with weather
# =============================================================================


async def _get_sports_events_async(query: str) -> dict:
    """Get sports events for a query (async)."""
    api_key = os.getenv("WEATHER_API_KEY") or WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured. Set WEATHER_API_KEY environment variable.")

    if not query:
        raise ValueError("Query is required (e.g., 'football', 'cricket', 'golf', or a location)")

    params = {"key": api_key, "q": query}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WEATHER_API_BASE}/sports.json", params=params)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise ValueError(f"Weather API error: {error_msg}")

            data = response.json()

            result = {
                "query": query,
                "sports": {},
            }

            # Process each sport category
            for sport in ["football", "cricket", "golf"]:
                events = data.get(sport, [])
                if events:
                    result["sports"][sport] = [
                        {
                            "stadium": e.get("stadium"),
                            "country": e.get("country"),
                            "region": e.get("region"),
                            "tournament": e.get("tournament"),
                            "match": e.get("match"),
                            "start": e.get("start"),
                        }
                        for e in events
                    ]

            return result

    except httpx.TimeoutException:
        raise ValueError("Weather API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Weather API request failed: {str(e)}")


def _get_sports_events_sync(query: str) -> dict:
    """Sync wrapper for get_sports_events."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_sports_events_async(query))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_sports_events_async(query))
    except RuntimeError:
        return asyncio.run(_get_sports_events_async(query))


get_sports_events = Tool(
    name="get_sports_events",
    description="Get upcoming sports events (football, cricket, golf) for a location or sport type. Useful for finding events where weather conditions matter.",
    parameters=[
        ToolParameter(
            name="query",
            type=ParameterType.STRING,
            description="Search query - can be a sport type ('football', 'cricket', 'golf') or a location name.",
            required=True,
        ),
    ],
    category="weather",
    tags=["weather", "sports", "events", "football", "cricket", "golf"],
).set_handler(_get_sports_events_sync)
