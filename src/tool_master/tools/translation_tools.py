"""
Translation tools using MyMemory API.

Provides text translation and language detection.
No API key required - free tier allows 1000 words/day (10000 with email).

API Documentation: https://mymemory.translated.net/doc/spec.php
"""

import asyncio
import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

MYMEMORY_BASE = "https://api.mymemory.translated.net"

# Common language codes supported by MyMemory
SUPPORTED_LANGUAGES = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fa": "Persian",
    "fi": "Finnish",
    "fr": "French",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sq": "Albanian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Filipino",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
}


async def _translate_text_async(
    text: str, source_language: str, target_language: str
) -> dict:
    """Translate text from one language to another."""
    source_language = source_language.lower()
    target_language = target_language.lower()

    if not text.strip():
        raise ValueError("Text to translate cannot be empty")

    # MyMemory uses langpair format: "en|es"
    langpair = f"{source_language}|{target_language}"

    params = {"q": text, "langpair": langpair}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{MYMEMORY_BASE}/get", params=params)

            if response.status_code != 200:
                raise ValueError(f"Translation API error: {response.text}")

            data = response.json()

            response_data = data.get("responseData", {})
            translated_text = response_data.get("translatedText", "")

            # Check for error responses
            if data.get("responseStatus") != 200:
                error_msg = data.get("responseDetails", "Translation failed")
                raise ValueError(f"Translation error: {error_msg}")

            # Get match quality (0-100)
            match_quality = response_data.get("match", 0)

            result = {
                "original_text": text,
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "match_quality": match_quality,
            }

            # Include alternative translations if available
            matches = data.get("matches", [])
            if len(matches) > 1:
                alternatives = []
                for match in matches[1:4]:  # Get up to 3 alternatives
                    if match.get("translation") != translated_text:
                        alternatives.append({
                            "translation": match.get("translation"),
                            "quality": match.get("quality"),
                            "source": match.get("created-by"),
                        })
                if alternatives:
                    result["alternatives"] = alternatives

            return result

    except httpx.TimeoutException:
        raise ValueError("Translation API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Translation API request failed: {str(e)}")


def _translate_text_sync(
    text: str, source_language: str, target_language: str
) -> dict:
    """Sync wrapper for translate_text."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _translate_text_async(text, source_language, target_language),
                )
                return future.result(timeout=20)
        else:
            return loop.run_until_complete(
                _translate_text_async(text, source_language, target_language)
            )
    except RuntimeError:
        return asyncio.run(
            _translate_text_async(text, source_language, target_language)
        )


async def _detect_language_async(text: str) -> dict:
    """Detect the language of given text."""
    if not text.strip():
        raise ValueError("Text for language detection cannot be empty")

    # Use translation to auto-detect: source "autodetect" to any language
    params = {"q": text, "langpair": "autodetect|en"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MYMEMORY_BASE}/get", params=params)

            if response.status_code != 200:
                raise ValueError(f"Language detection API error: {response.text}")

            data = response.json()

            # Extract detected language from response
            detected_lang = data.get("responseData", {}).get(
                "detectedLanguage", "unknown"
            )

            # The API returns the detected language code
            # Sometimes it's in the match data
            matches = data.get("matches", [])
            if matches and not detected_lang:
                detected_lang = matches[0].get("source-language", "unknown")

            # Get language name if we have it
            lang_code = detected_lang.lower() if detected_lang else "unknown"
            lang_name = SUPPORTED_LANGUAGES.get(lang_code, "Unknown")

            return {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "detected_language": lang_code,
                "language_name": lang_name,
                "confidence": "high" if lang_code in SUPPORTED_LANGUAGES else "low",
            }

    except httpx.TimeoutException:
        raise ValueError("Language detection API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Language detection API request failed: {str(e)}")


def _detect_language_sync(text: str) -> dict:
    """Sync wrapper for detect_language."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _detect_language_async(text)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_detect_language_async(text))
    except RuntimeError:
        return asyncio.run(_detect_language_async(text))


def _list_supported_languages_sync() -> dict:
    """List all supported language codes and their names."""
    languages = [
        {"code": code, "name": name} for code, name in sorted(SUPPORTED_LANGUAGES.items())
    ]

    return {
        "count": len(languages),
        "languages": languages,
    }


# Tool definitions

translate_text = Tool(
    name="translate_text",
    description="Translate text from one language to another. Supports 50+ languages including major world languages.",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to translate.",
            required=True,
        ),
        ToolParameter(
            name="source_language",
            type=ParameterType.STRING,
            description="Source language code (e.g., 'en' for English, 'es' for Spanish, 'fr' for French, 'de' for German, 'zh' for Chinese).",
            required=True,
        ),
        ToolParameter(
            name="target_language",
            type=ParameterType.STRING,
            description="Target language code (e.g., 'en' for English, 'es' for Spanish, 'fr' for French, 'de' for German, 'zh' for Chinese).",
            required=True,
        ),
    ],
    category="translation",
    tags=["translation", "language", "text", "multilingual"],
).set_handler(_translate_text_sync)


detect_language = Tool(
    name="detect_language",
    description="Detect the language of given text. Returns the language code and name.",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to detect the language of.",
            required=True,
        ),
    ],
    category="translation",
    tags=["translation", "language", "detection", "text"],
).set_handler(_detect_language_sync)


list_supported_languages = Tool(
    name="list_supported_languages",
    description="Get a list of all supported language codes and their full names for translation.",
    parameters=[],
    category="translation",
    tags=["translation", "language", "reference"],
).set_handler(_list_supported_languages_sync)
