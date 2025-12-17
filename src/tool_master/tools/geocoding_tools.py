"""
Geocoding tools using IP-API, Nominatim, and Zippopotam APIs.

Provides IP geolocation, address geocoding, reverse geocoding, and postal code lookup.
No API key required - all APIs are free to use with rate limits.

API Documentation:
- IP-API: https://ip-api.com/docs/
- Nominatim: https://nominatim.org/release-docs/develop/api/
- Zippopotam: https://www.zippopotam.us/
"""

import asyncio
import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

IP_API_BASE = "http://ip-api.com/json"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
ZIPPOPOTAM_BASE = "https://api.zippopotam.us"

# User-Agent required by Nominatim's usage policy
NOMINATIM_HEADERS = {
    "User-Agent": "ToolMaster/1.0 (LLM Tool Library; https://github.com/tool-master)"
}


async def _geolocate_ip_async(ip_address: Optional[str] = None) -> dict:
    """Get location information for an IP address."""
    # If no IP provided, the API will use the caller's IP
    url = f"{IP_API_BASE}/{ip_address}" if ip_address else IP_API_BASE

    params = {
        "fields": "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

            if response.status_code != 200:
                raise ValueError(f"IP geolocation API error: {response.text}")

            data = response.json()

            if data.get("status") == "fail":
                raise ValueError(
                    f"IP geolocation failed: {data.get('message', 'Unknown error')}"
                )

            return {
                "ip": data.get("query"),
                "location": {
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "region": data.get("regionName"),
                    "region_code": data.get("region"),
                    "city": data.get("city"),
                    "postal_code": data.get("zip"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon"),
                    "timezone": data.get("timezone"),
                },
                "network": {
                    "isp": data.get("isp"),
                    "organization": data.get("org"),
                    "as": data.get("as"),
                },
            }

    except httpx.TimeoutException:
        raise ValueError("IP geolocation API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"IP geolocation API request failed: {str(e)}")


def _geolocate_ip_sync(ip_address: Optional[str] = None) -> dict:
    """Sync wrapper for geolocate_ip."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _geolocate_ip_async(ip_address)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_geolocate_ip_async(ip_address))
    except RuntimeError:
        return asyncio.run(_geolocate_ip_async(ip_address))


async def _geocode_address_async(address: str, limit: int = 5) -> dict:
    """Convert an address to geographic coordinates."""
    if not address.strip():
        raise ValueError("Address cannot be empty")

    limit = min(max(1, limit), 10)

    params = {"q": address, "format": "json", "limit": limit, "addressdetails": 1}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NOMINATIM_BASE}/search", params=params, headers=NOMINATIM_HEADERS
            )

            if response.status_code != 200:
                raise ValueError(f"Geocoding API error: {response.text}")

            data = response.json()

            if not data:
                return {
                    "query": address,
                    "found": False,
                    "results": [],
                    "message": f"No results found for '{address}'",
                }

            results = []
            for item in data:
                result = {
                    "display_name": item.get("display_name"),
                    "latitude": float(item.get("lat", 0)),
                    "longitude": float(item.get("lon", 0)),
                    "type": item.get("type"),
                    "importance": item.get("importance"),
                }

                # Add address components if available
                address_details = item.get("address", {})
                if address_details:
                    result["address"] = {
                        "house_number": address_details.get("house_number"),
                        "road": address_details.get("road"),
                        "city": address_details.get("city")
                        or address_details.get("town")
                        or address_details.get("village"),
                        "state": address_details.get("state"),
                        "country": address_details.get("country"),
                        "postal_code": address_details.get("postcode"),
                    }

                results.append(result)

            return {
                "query": address,
                "found": True,
                "count": len(results),
                "results": results,
            }

    except httpx.TimeoutException:
        raise ValueError("Geocoding API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Geocoding API request failed: {str(e)}")


def _geocode_address_sync(address: str, limit: int = 5) -> dict:
    """Sync wrapper for geocode_address."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _geocode_address_async(address, limit)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_geocode_address_async(address, limit))
    except RuntimeError:
        return asyncio.run(_geocode_address_async(address, limit))


async def _reverse_geocode_async(latitude: float, longitude: float) -> dict:
    """Convert geographic coordinates to an address."""
    params = {"lat": latitude, "lon": longitude, "format": "json", "addressdetails": 1}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NOMINATIM_BASE}/reverse", params=params, headers=NOMINATIM_HEADERS
            )

            if response.status_code != 200:
                raise ValueError(f"Reverse geocoding API error: {response.text}")

            data = response.json()

            if data.get("error"):
                return {
                    "coordinates": {"latitude": latitude, "longitude": longitude},
                    "found": False,
                    "message": data.get("error"),
                }

            address = data.get("address", {})

            return {
                "coordinates": {"latitude": latitude, "longitude": longitude},
                "found": True,
                "display_name": data.get("display_name"),
                "address": {
                    "house_number": address.get("house_number"),
                    "road": address.get("road"),
                    "neighborhood": address.get("neighbourhood")
                    or address.get("suburb"),
                    "city": address.get("city")
                    or address.get("town")
                    or address.get("village"),
                    "county": address.get("county"),
                    "state": address.get("state"),
                    "country": address.get("country"),
                    "country_code": address.get("country_code"),
                    "postal_code": address.get("postcode"),
                },
            }

    except httpx.TimeoutException:
        raise ValueError("Reverse geocoding API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Reverse geocoding API request failed: {str(e)}")


def _reverse_geocode_sync(latitude: float, longitude: float) -> dict:
    """Sync wrapper for reverse_geocode."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _reverse_geocode_async(latitude, longitude)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                _reverse_geocode_async(latitude, longitude)
            )
    except RuntimeError:
        return asyncio.run(_reverse_geocode_async(latitude, longitude))


async def _lookup_zipcode_async(postal_code: str, country_code: str = "us") -> dict:
    """Get location information for a postal/zip code."""
    postal_code = postal_code.strip()
    country_code = country_code.lower()

    if not postal_code:
        raise ValueError("Postal code cannot be empty")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ZIPPOPOTAM_BASE}/{country_code}/{postal_code}"
            )

            if response.status_code == 404:
                return {
                    "postal_code": postal_code,
                    "country_code": country_code.upper(),
                    "found": False,
                    "message": f"No results found for postal code '{postal_code}' in {country_code.upper()}",
                }

            if response.status_code != 200:
                raise ValueError(f"Postal code lookup API error: {response.text}")

            data = response.json()

            places = []
            for place in data.get("places", []):
                places.append({
                    "name": place.get("place name"),
                    "state": place.get("state"),
                    "state_abbreviation": place.get("state abbreviation"),
                    "latitude": float(place.get("latitude", 0)),
                    "longitude": float(place.get("longitude", 0)),
                })

            return {
                "postal_code": data.get("post code", postal_code),
                "country": data.get("country"),
                "country_code": data.get("country abbreviation", country_code.upper()),
                "found": True,
                "places": places,
            }

    except httpx.TimeoutException:
        raise ValueError("Postal code lookup API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Postal code lookup API request failed: {str(e)}")


def _lookup_zipcode_sync(postal_code: str, country_code: str = "us") -> dict:
    """Sync wrapper for lookup_zipcode."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _lookup_zipcode_async(postal_code, country_code)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                _lookup_zipcode_async(postal_code, country_code)
            )
    except RuntimeError:
        return asyncio.run(_lookup_zipcode_async(postal_code, country_code))


# Tool definitions

geolocate_ip = Tool(
    name="geolocate_ip",
    description="Get geographic location information for an IP address. Returns country, region, city, coordinates, timezone, and ISP information.",
    parameters=[
        ToolParameter(
            name="ip_address",
            type=ParameterType.STRING,
            description="The IP address to look up (e.g., '8.8.8.8'). If not provided, returns location for the current/caller's IP.",
            required=False,
        ),
    ],
    category="geocoding",
    tags=["geocoding", "ip", "location", "geolocation"],
).set_handler(_geolocate_ip_sync)


geocode_address = Tool(
    name="geocode_address",
    description="Convert a street address, city name, or place name to geographic coordinates (latitude/longitude). Uses OpenStreetMap data.",
    parameters=[
        ToolParameter(
            name="address",
            type=ParameterType.STRING,
            description="The address or place name to geocode (e.g., '1600 Pennsylvania Avenue, Washington DC' or 'Eiffel Tower, Paris').",
            required=True,
        ),
        ToolParameter(
            name="limit",
            type=ParameterType.INTEGER,
            description="Maximum number of results to return (1-10). Default is 5.",
            required=False,
            default=5,
        ),
    ],
    category="geocoding",
    tags=["geocoding", "address", "coordinates", "location"],
).set_handler(_geocode_address_sync)


reverse_geocode = Tool(
    name="reverse_geocode",
    description="Convert geographic coordinates (latitude/longitude) to a street address. Uses OpenStreetMap data.",
    parameters=[
        ToolParameter(
            name="latitude",
            type=ParameterType.NUMBER,
            description="The latitude coordinate (e.g., 40.7128 for New York City).",
            required=True,
        ),
        ToolParameter(
            name="longitude",
            type=ParameterType.NUMBER,
            description="The longitude coordinate (e.g., -74.0060 for New York City).",
            required=True,
        ),
    ],
    category="geocoding",
    tags=["geocoding", "coordinates", "address", "location", "reverse"],
).set_handler(_reverse_geocode_sync)


lookup_zipcode = Tool(
    name="lookup_zipcode",
    description="Get location information for a postal/zip code. Returns city name, state, and coordinates.",
    parameters=[
        ToolParameter(
            name="postal_code",
            type=ParameterType.STRING,
            description="The postal or zip code to look up (e.g., '90210', '10001', 'SW1A 1AA').",
            required=True,
        ),
        ToolParameter(
            name="country_code",
            type=ParameterType.STRING,
            description="Two-letter country code (e.g., 'us', 'gb', 'de', 'fr', 'ca'). Default is 'us'.",
            required=False,
            default="us",
        ),
    ],
    category="geocoding",
    tags=["geocoding", "zipcode", "postal", "location"],
).set_handler(_lookup_zipcode_sync)
