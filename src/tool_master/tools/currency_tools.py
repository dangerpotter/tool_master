"""
Currency exchange tools using Frankfurter API.

Provides currency conversion and exchange rate data.
No API key required - completely free to use.

API Documentation: https://www.frankfurter.app/docs/
"""

import asyncio
import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

FRANKFURTER_BASE = "https://api.frankfurter.app"


async def _convert_currency_async(
    amount: float, from_currency: str, to_currency: str
) -> dict:
    """Convert an amount from one currency to another."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return {
            "amount": amount,
            "from": from_currency,
            "to": to_currency,
            "result": amount,
            "rate": 1.0,
        }

    params = {"amount": amount, "from": from_currency, "to": to_currency}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FRANKFURTER_BASE}/latest", params=params)

            if response.status_code != 200:
                raise ValueError(f"Currency conversion failed: {response.text}")

            data = response.json()
            converted_amount = data.get("rates", {}).get(to_currency)

            if converted_amount is None:
                raise ValueError(f"Could not convert to {to_currency}")

            return {
                "amount": data.get("amount", amount),
                "from": from_currency,
                "to": to_currency,
                "result": converted_amount,
                "rate": converted_amount / amount if amount else 0,
                "date": data.get("date"),
            }

    except httpx.TimeoutException:
        raise ValueError("Currency API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Currency API request failed: {str(e)}")


def _convert_currency_sync(
    amount: float, from_currency: str, to_currency: str
) -> dict:
    """Sync wrapper for convert_currency."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _convert_currency_async(amount, from_currency, to_currency),
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                _convert_currency_async(amount, from_currency, to_currency)
            )
    except RuntimeError:
        return asyncio.run(
            _convert_currency_async(amount, from_currency, to_currency)
        )


async def _get_exchange_rates_async(
    base_currency: str, symbols: Optional[str] = None
) -> dict:
    """Get current exchange rates for a base currency."""
    base_currency = base_currency.upper()
    params = {"from": base_currency}

    if symbols:
        params["to"] = symbols.upper()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FRANKFURTER_BASE}/latest", params=params)

            if response.status_code != 200:
                raise ValueError(f"Failed to get exchange rates: {response.text}")

            data = response.json()
            return {
                "base": base_currency,
                "date": data.get("date"),
                "rates": data.get("rates", {}),
            }

    except httpx.TimeoutException:
        raise ValueError("Currency API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Currency API request failed: {str(e)}")


def _get_exchange_rates_sync(
    base_currency: str, symbols: Optional[str] = None
) -> dict:
    """Sync wrapper for get_exchange_rates."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _get_exchange_rates_async(base_currency, symbols),
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                _get_exchange_rates_async(base_currency, symbols)
            )
    except RuntimeError:
        return asyncio.run(_get_exchange_rates_async(base_currency, symbols))


async def _get_historical_rates_async(
    date: str, base_currency: str, symbols: Optional[str] = None
) -> dict:
    """Get exchange rates for a specific historical date."""
    base_currency = base_currency.upper()
    params = {"from": base_currency}

    if symbols:
        params["to"] = symbols.upper()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FRANKFURTER_BASE}/{date}", params=params)

            if response.status_code != 200:
                raise ValueError(f"Failed to get historical rates: {response.text}")

            data = response.json()
            return {
                "base": base_currency,
                "date": data.get("date"),
                "rates": data.get("rates", {}),
            }

    except httpx.TimeoutException:
        raise ValueError("Currency API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Currency API request failed: {str(e)}")


def _get_historical_rates_sync(
    date: str, base_currency: str, symbols: Optional[str] = None
) -> dict:
    """Sync wrapper for get_historical_rates."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _get_historical_rates_async(date, base_currency, symbols),
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                _get_historical_rates_async(date, base_currency, symbols)
            )
    except RuntimeError:
        return asyncio.run(
            _get_historical_rates_async(date, base_currency, symbols)
        )


async def _get_rate_history_async(
    from_currency: str, to_currency: str, start_date: str, end_date: str
) -> dict:
    """Get exchange rate history over a date range."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    params = {"from": from_currency, "to": to_currency}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{FRANKFURTER_BASE}/{start_date}..{end_date}", params=params
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to get rate history: {response.text}")

            data = response.json()
            rates = data.get("rates", {})

            # Format as list of date/rate pairs for easier consumption
            history = []
            for date_str, rate_dict in sorted(rates.items()):
                rate = rate_dict.get(to_currency)
                if rate is not None:
                    history.append({"date": date_str, "rate": rate})

            return {
                "from": from_currency,
                "to": to_currency,
                "start_date": data.get("start_date", start_date),
                "end_date": data.get("end_date", end_date),
                "history": history,
            }

    except httpx.TimeoutException:
        raise ValueError("Currency API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Currency API request failed: {str(e)}")


def _get_rate_history_sync(
    from_currency: str, to_currency: str, start_date: str, end_date: str
) -> dict:
    """Sync wrapper for get_rate_history."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _get_rate_history_async(
                        from_currency, to_currency, start_date, end_date
                    ),
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                _get_rate_history_async(
                    from_currency, to_currency, start_date, end_date
                )
            )
    except RuntimeError:
        return asyncio.run(
            _get_rate_history_async(from_currency, to_currency, start_date, end_date)
        )


async def _list_currencies_async() -> dict:
    """Get list of all supported currencies."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FRANKFURTER_BASE}/currencies")

            if response.status_code != 200:
                raise ValueError(f"Failed to list currencies: {response.text}")

            currencies = response.json()
            return {
                "count": len(currencies),
                "currencies": currencies,
            }

    except httpx.TimeoutException:
        raise ValueError("Currency API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Currency API request failed: {str(e)}")


def _list_currencies_sync() -> dict:
    """Sync wrapper for list_currencies."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _list_currencies_async())
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_list_currencies_async())
    except RuntimeError:
        return asyncio.run(_list_currencies_async())


# Tool definitions

convert_currency = Tool(
    name="convert_currency",
    description="Convert an amount from one currency to another using current exchange rates. Returns the converted amount and the exchange rate used.",
    parameters=[
        ToolParameter(
            name="amount",
            type=ParameterType.NUMBER,
            description="The amount to convert.",
            required=True,
        ),
        ToolParameter(
            name="from_currency",
            type=ParameterType.STRING,
            description="The source currency code (e.g., 'USD', 'EUR', 'GBP').",
            required=True,
        ),
        ToolParameter(
            name="to_currency",
            type=ParameterType.STRING,
            description="The target currency code (e.g., 'USD', 'EUR', 'GBP').",
            required=True,
        ),
    ],
    category="currency",
    tags=["currency", "exchange", "conversion", "finance"],
).set_handler(_convert_currency_sync)


get_exchange_rates = Tool(
    name="get_exchange_rates",
    description="Get current exchange rates for a base currency. Returns rates for all supported currencies or specific ones if specified.",
    parameters=[
        ToolParameter(
            name="base_currency",
            type=ParameterType.STRING,
            description="The base currency code (e.g., 'USD', 'EUR'). Rates will be relative to this currency.",
            required=True,
        ),
        ToolParameter(
            name="symbols",
            type=ParameterType.STRING,
            description="Comma-separated list of target currency codes to get rates for (e.g., 'GBP,JPY,CAD'). If not specified, returns all available rates.",
            required=False,
        ),
    ],
    category="currency",
    tags=["currency", "exchange", "rates", "finance"],
).set_handler(_get_exchange_rates_sync)


get_historical_rates = Tool(
    name="get_historical_rates",
    description="Get exchange rates for a specific historical date. Useful for looking up past conversion rates.",
    parameters=[
        ToolParameter(
            name="date",
            type=ParameterType.STRING,
            description="The date to get rates for in YYYY-MM-DD format (e.g., '2023-01-15'). Must be a date when markets were open.",
            required=True,
        ),
        ToolParameter(
            name="base_currency",
            type=ParameterType.STRING,
            description="The base currency code (e.g., 'USD', 'EUR').",
            required=True,
        ),
        ToolParameter(
            name="symbols",
            type=ParameterType.STRING,
            description="Comma-separated list of target currency codes (e.g., 'GBP,JPY'). If not specified, returns all available rates.",
            required=False,
        ),
    ],
    category="currency",
    tags=["currency", "exchange", "rates", "historical", "finance"],
).set_handler(_get_historical_rates_sync)


get_rate_history = Tool(
    name="get_rate_history",
    description="Get exchange rate history between two currencies over a date range. Useful for analyzing currency trends.",
    parameters=[
        ToolParameter(
            name="from_currency",
            type=ParameterType.STRING,
            description="The source currency code (e.g., 'USD').",
            required=True,
        ),
        ToolParameter(
            name="to_currency",
            type=ParameterType.STRING,
            description="The target currency code (e.g., 'EUR').",
            required=True,
        ),
        ToolParameter(
            name="start_date",
            type=ParameterType.STRING,
            description="Start date in YYYY-MM-DD format (e.g., '2023-01-01').",
            required=True,
        ),
        ToolParameter(
            name="end_date",
            type=ParameterType.STRING,
            description="End date in YYYY-MM-DD format (e.g., '2023-12-31').",
            required=True,
        ),
    ],
    category="currency",
    tags=["currency", "exchange", "rates", "historical", "trends", "finance"],
).set_handler(_get_rate_history_sync)


list_currencies = Tool(
    name="list_currencies",
    description="Get a list of all supported currency codes and their full names.",
    parameters=[],
    category="currency",
    tags=["currency", "reference", "finance"],
).set_handler(_list_currencies_sync)
