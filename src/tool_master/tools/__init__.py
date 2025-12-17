"""Built-in tool implementations."""

# DateTime tools
from tool_master.tools.datetime_tools import (
    get_current_time,
    get_unix_timestamp,
    format_date,
    parse_date,
    get_time_difference,
)

# Dice tools
from tool_master.tools.dice_tools import roll_dice

# Weather tools
from tool_master.tools.weather_tools import (
    get_weather,
    get_hourly_weather,
    search_weather_locations,
    get_weather_alerts,
    get_air_quality,
    get_timezone,
    get_astronomy,
    get_historical_weather,
    get_future_weather,
    get_marine_weather,
    get_sports_events,
)

# Wikipedia tools
from tool_master.tools.wikipedia_tools import (
    search_wikipedia,
    get_wikipedia_article,
    get_random_wikipedia_article,
)

# Finance tools
from tool_master.tools.finance_tools import (
    get_stock_quote,
    search_stocks,
    get_top_stocks,
    get_price_history,
    get_earnings,
    get_analyst_ratings,
    get_dividends,
    get_stock_news,
    get_options,
    get_financials,
    get_holders,
)

# Currency tools
from tool_master.tools.currency_tools import (
    convert_currency,
    get_exchange_rates,
    get_historical_rates,
    get_rate_history,
    list_currencies,
)

# Dictionary tools
from tool_master.tools.dictionary_tools import (
    get_definition,
    get_synonyms,
    get_antonyms,
    find_rhymes,
    find_similar_words,
)

# Translation tools
from tool_master.tools.translation_tools import (
    translate_text,
    detect_language,
    list_supported_languages,
)

# Geocoding tools
from tool_master.tools.geocoding_tools import (
    geolocate_ip,
    geocode_address,
    reverse_geocode,
    lookup_zipcode,
)

# URL tools
from tool_master.tools.url_tools import (
    extract_url_metadata,
    take_screenshot,
    generate_pdf,
    expand_url,
)

# Text analysis tools
from tool_master.tools.text_analysis_tools import (
    detect_text_language,
    analyze_sentiment,
    extract_noun_phrases,
    get_word_frequency,
    correct_spelling,
)

# News tools
from tool_master.tools.news_tools import (
    search_news,
    get_top_headlines,
    get_news_sources,
)

# File format tools
from tool_master.tools.file_tools import (
    # Excel
    read_excel,
    write_excel,
    list_excel_sheets,
    read_excel_sheet_info,
    # CSV
    read_csv,
    write_csv,
    csv_to_excel,
    # JSON
    read_json,
    write_json,
    validate_json,
    # PDF
    read_pdf_text,
    read_pdf_metadata,
    count_pdf_pages,
    # PowerPoint
    read_pptx_text,
    read_pptx_structure,
    # Image
    read_image_metadata,
    resize_image,
    convert_image_format,
)

__all__ = [
    # DateTime
    "get_current_time",
    "get_unix_timestamp",
    "format_date",
    "parse_date",
    "get_time_difference",
    # Dice
    "roll_dice",
    # Weather
    "get_weather",
    "get_hourly_weather",
    "search_weather_locations",
    "get_weather_alerts",
    "get_air_quality",
    "get_timezone",
    "get_astronomy",
    "get_historical_weather",
    "get_future_weather",
    "get_marine_weather",
    "get_sports_events",
    # Wikipedia
    "search_wikipedia",
    "get_wikipedia_article",
    "get_random_wikipedia_article",
    # Finance
    "get_stock_quote",
    "search_stocks",
    "get_top_stocks",
    "get_price_history",
    "get_earnings",
    "get_analyst_ratings",
    "get_dividends",
    "get_stock_news",
    "get_options",
    "get_financials",
    "get_holders",
    # Currency
    "convert_currency",
    "get_exchange_rates",
    "get_historical_rates",
    "get_rate_history",
    "list_currencies",
    # Dictionary
    "get_definition",
    "get_synonyms",
    "get_antonyms",
    "find_rhymes",
    "find_similar_words",
    # Translation
    "translate_text",
    "detect_language",
    "list_supported_languages",
    # Geocoding
    "geolocate_ip",
    "geocode_address",
    "reverse_geocode",
    "lookup_zipcode",
    # URL
    "extract_url_metadata",
    "take_screenshot",
    "generate_pdf",
    "expand_url",
    # Text Analysis
    "detect_text_language",
    "analyze_sentiment",
    "extract_noun_phrases",
    "get_word_frequency",
    "correct_spelling",
    # News
    "search_news",
    "get_top_headlines",
    "get_news_sources",
    # File Format - Excel
    "read_excel",
    "write_excel",
    "list_excel_sheets",
    "read_excel_sheet_info",
    # File Format - CSV
    "read_csv",
    "write_csv",
    "csv_to_excel",
    # File Format - JSON
    "read_json",
    "write_json",
    "validate_json",
    # File Format - PDF
    "read_pdf_text",
    "read_pdf_metadata",
    "count_pdf_pages",
    # File Format - PowerPoint
    "read_pptx_text",
    "read_pptx_structure",
    # File Format - Image
    "read_image_metadata",
    "resize_image",
    "convert_image_format",
]
