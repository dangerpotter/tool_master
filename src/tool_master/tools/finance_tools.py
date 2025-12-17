"""
Finance tools using Yahoo Finance (yfinance).

Provides stock quotes, news, price history, options, earnings,
analyst ratings, dividends, financials, and holder information.

Requires: yfinance library (pip install yfinance)
"""

import logging
from datetime import datetime
from typing import Optional

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

# Valid periods and intervals for price history
VALID_PERIODS = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
VALID_INTERVALS = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]

# Supported sectors
VALID_SECTORS = [
    "basic-materials", "communication-services", "consumer-cyclical",
    "consumer-defensive", "energy", "financial-services", "healthcare",
    "industrials", "real-estate", "technology", "utilities"
]

# Popular tickers by sector (curated list)
SECTOR_TICKERS = {
    "technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AVGO", "ORCL", "CRM", "AMD", "ADBE"],
    "healthcare": ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY"],
    "financial-services": ["JPM", "BAC", "WFC", "GS", "MS", "BLK", "SCHW", "AXP", "C", "SPGI"],
    "consumer-cyclical": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "MAR"],
    "consumer-defensive": ["PG", "KO", "PEP", "WMT", "COST", "PM", "MDLZ", "CL", "EL", "KHC"],
    "energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
    "industrials": ["CAT", "UNP", "HON", "UPS", "BA", "RTX", "DE", "LMT", "GE", "MMM"],
    "basic-materials": ["LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "NUE", "DOW", "CTVA"],
    "real-estate": ["PLD", "AMT", "EQIX", "PSA", "SPG", "O", "WELL", "DLR", "AVB", "EQR"],
    "utilities": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "XEL", "EXC", "WEC", "ED"],
    "communication-services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "TMUS", "CHTR", "EA"],
}


def _get_stock_quote(symbol: str) -> dict:
    """Get comprehensive stock/crypto information."""
    if not symbol:
        raise ValueError("Symbol is required")

    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")

    ticker = yf.Ticker(symbol.upper())
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"Could not find data for symbol: {symbol}")

    result = {
        "symbol": info.get("symbol", symbol.upper()),
        "name": info.get("longName") or info.get("shortName", "Unknown"),
        "type": info.get("quoteType", "Unknown"),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", "Unknown"),
        "price": {
            "current": info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "change": info.get("regularMarketChange"),
            "change_percent": info.get("regularMarketChangePercent"),
        },
        "volume": {
            "current": info.get("regularMarketVolume"),
            "average": info.get("averageVolume"),
            "average_10d": info.get("averageDailyVolume10Day"),
        },
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "eps": info.get("trailingEps"),
        "dividend_yield": info.get("dividendYield"),
        "52_week": {
            "high": info.get("fiftyTwoWeekHigh"),
            "low": info.get("fiftyTwoWeekLow"),
        },
        "50_day_avg": info.get("fiftyDayAverage"),
        "200_day_avg": info.get("twoHundredDayAverage"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }

    if info.get("quoteType") == "CRYPTOCURRENCY":
        result["circulating_supply"] = info.get("circulatingSupply")
        result["total_supply"] = info.get("totalSupply")

    return result


def _search_stocks(query: str, count: int = 10) -> dict:
    """Search for stocks, ETFs, crypto by name or symbol."""
    if not query:
        raise ValueError("Search query is required")

    count = max(1, min(25, count))

    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")

    results = []

    # Try direct symbol lookup
    ticker = yf.Ticker(query.upper())
    info = ticker.info

    if info and info.get("symbol"):
        results.append({
            "symbol": info.get("symbol"),
            "name": info.get("longName") or info.get("shortName", "Unknown"),
            "type": info.get("quoteType", "Unknown"),
            "exchange": info.get("exchange", "Unknown"),
        })

    # Try yfinance search if available
    try:
        search_results = yf.Search(query)
        if hasattr(search_results, 'quotes') and search_results.quotes:
            for quote in search_results.quotes[:count]:
                if quote.get("symbol") not in [r["symbol"] for r in results]:
                    results.append({
                        "symbol": quote.get("symbol"),
                        "name": quote.get("longname") or quote.get("shortname", "Unknown"),
                        "type": quote.get("quoteType", "Unknown"),
                        "exchange": quote.get("exchange", "Unknown"),
                    })
    except Exception:
        pass

    if not results:
        return {"query": query, "results": [], "message": "No matches found"}

    return {
        "query": query,
        "results": results[:count],
        "count": len(results[:count])
    }


def _get_top_stocks(entity_type: str = "companies", sector: str = "technology", count: int = 10) -> dict:
    """Get top performing entities by sector."""
    count = max(1, min(25, count))

    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")

    sector_key = sector.lower().replace(" ", "-")
    if sector_key not in SECTOR_TICKERS:
        sector_key = "technology"

    tickers_list = SECTOR_TICKERS.get(sector_key, SECTOR_TICKERS["technology"])

    results = []
    for symbol in tickers_list[:count]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info and info.get("regularMarketPrice"):
                results.append({
                    "symbol": symbol,
                    "name": info.get("longName") or info.get("shortName", symbol),
                    "price": info.get("regularMarketPrice"),
                    "change_percent": info.get("regularMarketChangePercent"),
                    "market_cap": info.get("marketCap"),
                    "volume": info.get("regularMarketVolume"),
                })
        except Exception:
            continue

    results.sort(key=lambda x: x.get("change_percent") or 0, reverse=True)

    return {
        "entity_type": entity_type,
        "sector": sector_key,
        "results": results,
        "count": len(results)
    }


def _get_price_history(symbol: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Get historical price data."""
    if not symbol:
        raise ValueError("Symbol is required")

    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")

    period = period.lower() if period else "1mo"
    interval = interval.lower() if interval else "1d"

    if period not in VALID_PERIODS:
        period = "1mo"
    if interval not in VALID_INTERVALS:
        interval = "1d"

    ticker = yf.Ticker(symbol.upper())
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        raise ValueError(f"No price history found for {symbol}")

    history_data = []
    for date, row in hist.iterrows():
        history_data.append({
            "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
            "open": round(row["Open"], 2) if row["Open"] else None,
            "high": round(row["High"], 2) if row["High"] else None,
            "low": round(row["Low"], 2) if row["Low"] else None,
            "close": round(row["Close"], 2) if row["Close"] else None,
            "volume": int(row["Volume"]) if row["Volume"] else None,
        })

    # Limit response size
    if len(history_data) > 100:
        step = len(history_data) // 100
        history_data = history_data[::step][:100]

    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        "data_points": len(history_data),
        "history": history_data
    }


def _get_earnings(symbol: str, period: str = "quarterly") -> dict:
    """Get earnings data and upcoming earnings date."""
    if not symbol:
        raise ValueError("Symbol is required")

    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")

    period = period.lower() if period else "quarterly"
    if period not in ["annual", "quarterly"]:
        period = "quarterly"

    ticker = yf.Ticker(symbol.upper())
    info = ticker.info

    result = {
        "symbol": symbol.upper(),
        "name": info.get("longName") or info.get("shortName", symbol),
        "period": period,
    }

    # Get earnings dates
    try:
        calendar = ticker.calendar
        if calendar is not None and not calendar.empty:
            if hasattr(calendar, 'to_dict'):
                cal_dict = calendar.to_dict()
                result["next_earnings_date"] = str(cal_dict.get("Earnings Date", [None])[0])
    except Exception:
        pass

    # Get earnings history
    try:
        if period == "quarterly":
            earnings = ticker.quarterly_earnings
        else:
            earnings = ticker.earnings

        if earnings is not None and not earnings.empty:
            earnings_list = []
            for date, row in earnings.iterrows():
                earnings_list.append({
                    "date": str(date),
                    "revenue": row.get("Revenue"),
                    "earnings": row.get("Earnings"),
                })
            result["earnings_history"] = earnings_list[:8]
    except Exception:
        result["earnings_history"] = []

    result["trailing_eps"] = info.get("trailingEps")
    result["forward_eps"] = info.get("forwardEps")
    result["peg_ratio"] = info.get("pegRatio")

    return result


def _get_analyst_ratings(symbol: str) -> dict:
    """Get analyst recommendations and price targets."""
    if not symbol:
        raise ValueError("Symbol is required")

    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")

    ticker = yf.Ticker(symbol.upper())
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"Could not find data for symbol: {symbol}")

    result = {
        "symbol": info.get("symbol", symbol.upper()),
        "name": info.get("longName") or info.get("shortName", "Unknown"),
        "current_price": info.get("regularMarketPrice"),
        "currency": info.get("currency", "USD"),
    }

    # Get price targets
    try:
        targets = ticker.analyst_price_targets
        if targets and isinstance(targets, dict):
            result["price_targets"] = {
                "low": targets.get("low"),
                "high": targets.get("high"),
                "mean": targets.get("mean"),
                "median": targets.get("median"),
            }
            if result["current_price"] and targets.get("mean"):
                upside = ((targets["mean"] - result["current_price"]) / result["current_price"]) * 100
                result["price_targets"]["upside_percent"] = round(upside, 2)
    except Exception:
        result["price_targets"] = None

    # Get recommendation summary
    try:
        rec_summary = ticker.recommendations_summary
        if rec_summary is not None and not rec_summary.empty:
            latest = rec_summary.iloc[0] if len(rec_summary) > 0 else None
            if latest is not None:
                result["recommendation_summary"] = {
                    "strong_buy": int(latest.get("strongBuy", 0)),
                    "buy": int(latest.get("buy", 0)),
                    "hold": int(latest.get("hold", 0)),
                    "sell": int(latest.get("sell", 0)),
                    "strong_sell": int(latest.get("strongSell", 0)),
                }
    except Exception:
        result["recommendation_summary"] = None

    return result


def _get_dividends(symbol: str, include_history: bool = False) -> dict:
    """Get dividend information including yield, payment dates, and history."""
    if not symbol:
        raise ValueError("Symbol is required")

    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")

    ticker = yf.Ticker(symbol.upper())
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"Could not find data for symbol: {symbol}")

    result = {
        "symbol": info.get("symbol", symbol.upper()),
        "name": info.get("longName") or info.get("shortName", "Unknown"),
        "current_price": info.get("regularMarketPrice"),
        "currency": info.get("currency", "USD"),
    }

    dividend_yield = info.get("dividendYield")
    result["dividend_yield"] = round(dividend_yield * 100, 2) if dividend_yield else None
    result["annual_dividend"] = info.get("dividendRate")
    result["payout_ratio"] = round(info.get("payoutRatio", 0) * 100, 2) if info.get("payoutRatio") else None

    ex_div_timestamp = info.get("exDividendDate")
    if ex_div_timestamp:
        try:
            result["ex_dividend_date"] = datetime.fromtimestamp(ex_div_timestamp).strftime("%Y-%m-%d")
        except Exception:
            result["ex_dividend_date"] = None
    else:
        result["ex_dividend_date"] = None

    if include_history:
        try:
            dividends = ticker.dividends
            if dividends is not None and not dividends.empty:
                recent_payments = []
                for date, amount in dividends.tail(8).items():
                    recent_payments.append({
                        "date": str(date.date()) if hasattr(date, 'date') else str(date),
                        "amount": round(float(amount), 4),
                    })
                result["recent_payments"] = list(reversed(recent_payments))
        except Exception:
            result["recent_payments"] = []

    if not result["dividend_yield"] and not result["annual_dividend"]:
        result["message"] = "This security does not pay dividends"

    return result

def _get_stock_news(symbol: str, count: int = 5) -> dict:
    """Get recent news articles for a stock or cryptocurrency."""
    if not symbol:
        raise ValueError("Symbol is required")
    count = max(1, min(20, count))
    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")
    ticker = yf.Ticker(symbol.upper())
    try:
        news = ticker.news
    except Exception:
        news = []
    if not news:
        return {"symbol": symbol.upper(), "articles": [], "message": "No news articles found"}
    articles = []
    for article in news[:count]:
        published = None
        if article.get("providerPublishTime"):
            try:
                published = datetime.fromtimestamp(article["providerPublishTime"]).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        articles.append({
            "title": article.get("title"),
            "publisher": article.get("publisher"),
            "link": article.get("link"),
            "published": published,
            "type": article.get("type"),
        })
    return {"symbol": symbol.upper(), "articles": articles, "count": len(articles)}


def _get_options(symbol: str, option_type: str = "both", date: Optional[str] = None) -> dict:
    """Get options chain data including calls and puts."""
    if not symbol:
        raise ValueError("Symbol is required")
    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")
    ticker = yf.Ticker(symbol.upper())
    try:
        expirations = ticker.options
    except Exception:
        expirations = []
    if not expirations:
        raise ValueError(f"No options data available for {symbol}")
    exp_date = date if date and date in expirations else expirations[0]
    try:
        opt_chain = ticker.option_chain(exp_date)
    except Exception as e:
        raise ValueError(f"Could not retrieve options for {symbol}: {str(e)}")
    result = {
        "symbol": symbol.upper(),
        "expiration_date": exp_date,
        "available_expirations": list(expirations[:10]),
    }
    def format_options(df, limit: int = 15):
        if df is None or df.empty:
            return []
        options_list = []
        for _, row in df.head(limit).iterrows():
            options_list.append({
                "strike": row.get("strike"),
                "last_price": row.get("lastPrice"),
                "bid": row.get("bid"),
                "ask": row.get("ask"),
                "volume": int(row.get("volume", 0)) if row.get("volume") else None,
                "open_interest": int(row.get("openInterest", 0)) if row.get("openInterest") else None,
                "implied_volatility": round(row.get("impliedVolatility", 0) * 100, 2) if row.get("impliedVolatility") else None,
                "in_the_money": row.get("inTheMoney"),
            })
        return options_list
    option_type = option_type.lower() if option_type else "both"
    if option_type in ["call", "both"]:
        result["calls"] = format_options(opt_chain.calls)
    if option_type in ["put", "both"]:
        result["puts"] = format_options(opt_chain.puts)
    return result


def _get_financials(symbol: str, period: str = "annual") -> dict:
    """Get key financial metrics from income statement, balance sheet, and cash flow."""
    if not symbol:
        raise ValueError("Symbol is required")
    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")
    period = period.lower() if period else "annual"
    if period not in ["annual", "quarterly"]:
        period = "annual"
    ticker = yf.Ticker(symbol.upper())
    info = ticker.info
    result = {
        "symbol": symbol.upper(),
        "name": info.get("longName") or info.get("shortName", symbol),
        "currency": info.get("financialCurrency") or info.get("currency", "USD"),
        "period": period,
    }
    def format_number(val):
        if val is None or (hasattr(val, '__len__') and len(val) == 0):
            return None
        try:
            val = float(val)
            if abs(val) >= 1e12:
                return f"{val/1e12:.2f}T"
            elif abs(val) >= 1e9:
                return f"{val/1e9:.2f}B"
            elif abs(val) >= 1e6:
                return f"{val/1e6:.2f}M"
            else:
                return f"{val:,.0f}"
        except (TypeError, ValueError):
            return None
    try:
        if period == "quarterly":
            income_stmt = ticker.quarterly_financials
            balance = ticker.quarterly_balance_sheet
            cashflow = ticker.quarterly_cashflow
        else:
            income_stmt = ticker.financials
            balance = ticker.balance_sheet
            cashflow = ticker.cashflow
        if income_stmt is not None and not income_stmt.empty:
            latest = income_stmt.iloc[:, 0] if len(income_stmt.columns) > 0 else {}
            result["income_statement"] = {
                "total_revenue": format_number(latest.get("Total Revenue")),
                "gross_profit": format_number(latest.get("Gross Profit")),
                "operating_income": format_number(latest.get("Operating Income")),
                "net_income": format_number(latest.get("Net Income")),
                "ebitda": format_number(latest.get("EBITDA")),
            }
        if balance is not None and not balance.empty:
            latest = balance.iloc[:, 0] if len(balance.columns) > 0 else {}
            result["balance_sheet"] = {
                "total_assets": format_number(latest.get("Total Assets")),
                "total_liabilities": format_number(latest.get("Total Liabilities Net Minority Interest")),
                "total_equity": format_number(latest.get("Total Equity Gross Minority Interest") or latest.get("Stockholders Equity")),
                "cash": format_number(latest.get("Cash And Cash Equivalents")),
                "total_debt": format_number(latest.get("Total Debt")),
            }
        if cashflow is not None and not cashflow.empty:
            latest = cashflow.iloc[:, 0] if len(cashflow.columns) > 0 else {}
            result["cash_flow"] = {
                "operating_cash_flow": format_number(latest.get("Operating Cash Flow")),
                "capital_expenditure": format_number(latest.get("Capital Expenditure")),
                "free_cash_flow": format_number(latest.get("Free Cash Flow")),
            }
    except Exception as e:
        logger.debug(f"Error getting financials for {symbol}: {e}")
        result["error"] = "Could not retrieve complete financial data"
    result["ratios"] = {
        "profit_margin": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else None,
        "operating_margin": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else None,
        "return_on_equity": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else None,
        "return_on_assets": round(info.get("returnOnAssets", 0) * 100, 2) if info.get("returnOnAssets") else None,
        "debt_to_equity": round(info.get("debtToEquity", 0), 2) if info.get("debtToEquity") else None,
        "current_ratio": round(info.get("currentRatio", 0), 2) if info.get("currentRatio") else None,
    }
    return result


def _get_holders(symbol: str) -> dict:
    """Get ownership information including institutional and insider holders."""
    if not symbol:
        raise ValueError("Symbol is required")
    try:
        import yfinance as yf
    except ImportError:
        raise ValueError("yfinance library not installed. Run: pip install yfinance")
    ticker = yf.Ticker(symbol.upper())
    info = ticker.info
    result = {
        "symbol": symbol.upper(),
        "name": info.get("longName") or info.get("shortName", symbol),
    }
    try:
        major = ticker.major_holders
        if major is not None and not major.empty:
            result["ownership_breakdown"] = {}
            for idx, row in major.iterrows():
                key = str(row.iloc[1]).lower().replace(" ", "_").replace("%", "pct")
                try:
                    value = str(row.iloc[0])
                    result["ownership_breakdown"][key] = value if "%" in value else float(value)
                except (ValueError, TypeError):
                    result["ownership_breakdown"][key] = str(row.iloc[0])
    except Exception:
        result["ownership_breakdown"] = None
    try:
        institutional = ticker.institutional_holders
        if institutional is not None and not institutional.empty:
            holders_list = []
            for _, row in institutional.head(10).iterrows():
                holders_list.append({
                    "holder": row.get("Holder"),
                    "shares": int(row.get("Shares", 0)) if row.get("Shares") else None,
                    "date_reported": str(row.get("Date Reported"))[:10] if row.get("Date Reported") else None,
                    "pct_out": round(row.get("% Out", 0) * 100, 2) if row.get("% Out") else None,
                    "value": int(row.get("Value", 0)) if row.get("Value") else None,
                })
            result["top_institutional_holders"] = holders_list
    except Exception:
        result["top_institutional_holders"] = []
    try:
        insiders = ticker.insider_transactions
        if insiders is not None and not insiders.empty:
            transactions = []
            for _, row in insiders.head(10).iterrows():
                transactions.append({
                    "insider": row.get("Insider"),
                    "position": row.get("Position"),
                    "transaction": row.get("Transaction"),
                    "shares": int(row.get("Shares", 0)) if row.get("Shares") else None,
                    "date": str(row.get("Start Date"))[:10] if row.get("Start Date") else None,
                })
            result["recent_insider_transactions"] = transactions
    except Exception:
        result["recent_insider_transactions"] = []
    return result

# Tool definitions
get_stock_quote = Tool(
    name="get_stock_quote",
    description="Get current stock/crypto price and key metrics including market cap, P/E ratio, 52-week range, and volume. Works with stocks (AAPL, MSFT), ETFs (SPY, QQQ), and crypto (BTC-USD, ETH-USD).",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'MSFT', 'BTC-USD', 'ETH-USD')",
            required=True,
        ),
    ],
    category="finance",
    tags=["stocks", "crypto", "quotes", "price", "finance"],
).set_handler(_get_stock_quote)


search_stocks = Tool(
    name="search_stocks",
    description="Search for stocks, ETFs, or crypto by name or symbol. Use when you need to find a ticker symbol.",
    parameters=[
        ToolParameter(
            name="query",
            type=ParameterType.STRING,
            description="Search term - company name, ticker, or keyword (e.g., 'Apple', 'electric vehicles', 'bitcoin')",
            required=True,
        ),
        ToolParameter(
            name="count",
            type=ParameterType.INTEGER,
            description="Maximum results to return (1-25)",
            required=False,
            default=10,
        ),
    ],
    category="finance",
    tags=["stocks", "search", "finance"],
).set_handler(_search_stocks)


get_top_stocks = Tool(
    name="get_top_stocks",
    description="Get top performing stocks or ETFs by sector.",
    parameters=[
        ToolParameter(
            name="entity_type",
            type=ParameterType.STRING,
            description="Type of entity: 'companies' or 'etfs'",
            required=False,
            default="companies",
            enum=["companies", "etfs"],
        ),
        ToolParameter(
            name="sector",
            type=ParameterType.STRING,
            description="Market sector",
            required=False,
            default="technology",
            enum=VALID_SECTORS,
        ),
        ToolParameter(
            name="count",
            type=ParameterType.INTEGER,
            description="Number of results (1-25)",
            required=False,
            default=10,
        ),
    ],
    category="finance",
    tags=["stocks", "top", "sector", "finance"],
).set_handler(_get_top_stocks)


get_price_history = Tool(
    name="get_price_history",
    description="Get historical price data for charting or analysis. Returns OHLCV data.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'SPY', 'BTC-USD')",
            required=True,
        ),
        ToolParameter(
            name="period",
            type=ParameterType.STRING,
            description="Time period for data",
            required=False,
            default="1mo",
            enum=VALID_PERIODS,
        ),
        ToolParameter(
            name="interval",
            type=ParameterType.STRING,
            description="Data interval/granularity",
            required=False,
            default="1d",
            enum=VALID_INTERVALS,
        ),
    ],
    category="finance",
    tags=["stocks", "history", "price", "charts", "finance"],
).set_handler(_get_price_history)


get_earnings = Tool(
    name="get_earnings",
    description="Get earnings data including historical earnings, EPS, and next earnings date.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')",
            required=True,
        ),
        ToolParameter(
            name="period",
            type=ParameterType.STRING,
            description="Earnings period type",
            required=False,
            default="quarterly",
            enum=["annual", "quarterly"],
        ),
    ],
    category="finance",
    tags=["stocks", "earnings", "eps", "finance"],
).set_handler(_get_earnings)


get_analyst_ratings = Tool(
    name="get_analyst_ratings",
    description="Get analyst recommendations (buy/hold/sell counts), price targets, and recent upgrades/downgrades.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'TSLA', 'GOOGL')",
            required=True,
        ),
    ],
    category="finance",
    tags=["stocks", "analyst", "ratings", "finance"],
).set_handler(_get_analyst_ratings)


get_dividends = Tool(
    name="get_dividends",
    description="Get dividend information including yield, payment dates, ex-dividend date, and payout ratio.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'KO', 'JNJ')",
            required=True,
        ),
        ToolParameter(
            name="include_history",
            type=ParameterType.BOOLEAN,
            description="Include last 8 dividend payment amounts",
            required=False,
            default=False,
        ),
    ],
    category="finance",
    tags=["stocks", "dividends", "income", "finance"],
).set_handler(_get_dividends)

get_stock_news = Tool(
    name="get_stock_news",
    description="Get recent news articles for a stock or cryptocurrency.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'TSLA', 'BTC-USD')",
            required=True,
        ),
        ToolParameter(
            name="count",
            type=ParameterType.INTEGER,
            description="Number of news articles to return (1-20)",
            required=False,
            default=5,
        ),
    ],
    category="finance",
    tags=["stocks", "news", "finance"],
).set_handler(_get_stock_news)


get_options = Tool(
    name="get_options",
    description="Get options chain data including calls and puts with strike prices, bids, asks, and implied volatility.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'SPY', 'TSLA')",
            required=True,
        ),
        ToolParameter(
            name="option_type",
            type=ParameterType.STRING,
            description="Type of options to return",
            required=False,
            default="both",
            enum=["call", "put", "both"],
        ),
        ToolParameter(
            name="date",
            type=ParameterType.STRING,
            description="Expiration date in YYYY-MM-DD format (optional, defaults to nearest expiration)",
            required=False,
        ),
    ],
    category="finance",
    tags=["stocks", "options", "derivatives", "finance"],
).set_handler(_get_options)


get_financials = Tool(
    name="get_financials",
    description="Get key financial metrics: revenue, profit margins, assets, debt, and cash flow. Returns highlights from income statement, balance sheet, and cash flow statement.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'MSFT', 'AMZN')",
            required=True,
        ),
        ToolParameter(
            name="period",
            type=ParameterType.STRING,
            description="Annual or quarterly financials",
            required=False,
            default="annual",
            enum=["annual", "quarterly"],
        ),
    ],
    category="finance",
    tags=["stocks", "financials", "fundamentals", "finance"],
).set_handler(_get_financials)


get_holders = Tool(
    name="get_holders",
    description="Get ownership information: percentage held by insiders and institutions, top institutional holders (Vanguard, Blackrock, etc.), and recent insider buying/selling activity.",
    parameters=[
        ToolParameter(
            name="symbol",
            type=ParameterType.STRING,
            description="Ticker symbol (e.g., 'AAPL', 'NVDA', 'TSLA')",
            required=True,
        ),
    ],
    category="finance",
    tags=["stocks", "holders", "institutional", "finance"],
).set_handler(_get_holders)
