"""
Dictionary and word tools using Free Dictionary API and Datamuse API.

Provides word definitions, synonyms, antonyms, rhymes, and similar words.
No API key required - completely free to use.

API Documentation:
- Free Dictionary: https://dictionaryapi.dev/
- Datamuse: https://www.datamuse.com/api/
"""

import asyncio
import logging
from typing import Optional

import httpx

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

FREE_DICTIONARY_BASE = "https://api.dictionaryapi.dev/api/v2/entries"
DATAMUSE_BASE = "https://api.datamuse.com/words"


async def _get_definition_async(word: str, language: str = "en") -> dict:
    """Get the definition of a word."""
    word = word.strip().lower()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FREE_DICTIONARY_BASE}/{language}/{word}")

            if response.status_code == 404:
                return {
                    "word": word,
                    "found": False,
                    "message": f"No definition found for '{word}'",
                }

            if response.status_code != 200:
                raise ValueError(f"Dictionary API error: {response.text}")

            data = response.json()

            if not data or not isinstance(data, list):
                return {
                    "word": word,
                    "found": False,
                    "message": f"No definition found for '{word}'",
                }

            entry = data[0]
            result = {
                "word": entry.get("word", word),
                "found": True,
                "phonetics": [],
                "meanings": [],
            }

            # Extract phonetics
            for phonetic in entry.get("phonetics", []):
                if phonetic.get("text"):
                    result["phonetics"].append({
                        "text": phonetic.get("text"),
                        "audio": phonetic.get("audio"),
                    })

            # Extract meanings
            for meaning in entry.get("meanings", []):
                meaning_data = {
                    "part_of_speech": meaning.get("partOfSpeech"),
                    "definitions": [],
                }

                for definition in meaning.get("definitions", [])[:3]:  # Limit to 3
                    def_data = {"definition": definition.get("definition")}
                    if definition.get("example"):
                        def_data["example"] = definition.get("example")
                    if definition.get("synonyms"):
                        def_data["synonyms"] = definition.get("synonyms")[:5]
                    if definition.get("antonyms"):
                        def_data["antonyms"] = definition.get("antonyms")[:5]
                    meaning_data["definitions"].append(def_data)

                result["meanings"].append(meaning_data)

            return result

    except httpx.TimeoutException:
        raise ValueError("Dictionary API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Dictionary API request failed: {str(e)}")


def _get_definition_sync(word: str, language: str = "en") -> dict:
    """Sync wrapper for get_definition."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _get_definition_async(word, language)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_definition_async(word, language))
    except RuntimeError:
        return asyncio.run(_get_definition_async(word, language))


async def _get_synonyms_async(word: str, max_results: int = 10) -> dict:
    """Get synonyms for a word using Datamuse API."""
    word = word.strip().lower()
    max_results = min(max(1, max_results), 50)

    params = {"rel_syn": word, "max": max_results}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(DATAMUSE_BASE, params=params)

            if response.status_code != 200:
                raise ValueError(f"Datamuse API error: {response.text}")

            data = response.json()

            synonyms = [item.get("word") for item in data if item.get("word")]

            return {
                "word": word,
                "synonyms": synonyms,
                "count": len(synonyms),
            }

    except httpx.TimeoutException:
        raise ValueError("Datamuse API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Datamuse API request failed: {str(e)}")


def _get_synonyms_sync(word: str, max_results: int = 10) -> dict:
    """Sync wrapper for get_synonyms."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _get_synonyms_async(word, max_results)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_synonyms_async(word, max_results))
    except RuntimeError:
        return asyncio.run(_get_synonyms_async(word, max_results))


async def _get_antonyms_async(word: str, max_results: int = 10) -> dict:
    """Get antonyms for a word using Datamuse API."""
    word = word.strip().lower()
    max_results = min(max(1, max_results), 50)

    params = {"rel_ant": word, "max": max_results}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(DATAMUSE_BASE, params=params)

            if response.status_code != 200:
                raise ValueError(f"Datamuse API error: {response.text}")

            data = response.json()

            antonyms = [item.get("word") for item in data if item.get("word")]

            return {
                "word": word,
                "antonyms": antonyms,
                "count": len(antonyms),
            }

    except httpx.TimeoutException:
        raise ValueError("Datamuse API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Datamuse API request failed: {str(e)}")


def _get_antonyms_sync(word: str, max_results: int = 10) -> dict:
    """Sync wrapper for get_antonyms."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _get_antonyms_async(word, max_results)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_get_antonyms_async(word, max_results))
    except RuntimeError:
        return asyncio.run(_get_antonyms_async(word, max_results))


async def _find_rhymes_async(word: str, max_results: int = 10) -> dict:
    """Find words that rhyme with the given word."""
    word = word.strip().lower()
    max_results = min(max(1, max_results), 50)

    params = {"rel_rhy": word, "max": max_results}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(DATAMUSE_BASE, params=params)

            if response.status_code != 200:
                raise ValueError(f"Datamuse API error: {response.text}")

            data = response.json()

            rhymes = []
            for item in data:
                if item.get("word"):
                    rhyme_data = {"word": item.get("word")}
                    if item.get("score"):
                        rhyme_data["score"] = item.get("score")
                    if item.get("numSyllables"):
                        rhyme_data["syllables"] = item.get("numSyllables")
                    rhymes.append(rhyme_data)

            return {
                "word": word,
                "rhymes": rhymes,
                "count": len(rhymes),
            }

    except httpx.TimeoutException:
        raise ValueError("Datamuse API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Datamuse API request failed: {str(e)}")


def _find_rhymes_sync(word: str, max_results: int = 10) -> dict:
    """Sync wrapper for find_rhymes."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _find_rhymes_async(word, max_results)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(_find_rhymes_async(word, max_results))
    except RuntimeError:
        return asyncio.run(_find_rhymes_async(word, max_results))


async def _find_similar_words_async(
    word: str, match_type: str = "meaning", max_results: int = 10
) -> dict:
    """Find similar words based on meaning, sound, or spelling."""
    word = word.strip().lower()
    match_type = match_type.lower()
    max_results = min(max(1, max_results), 50)

    # Map match types to Datamuse parameters
    param_map = {
        "meaning": "ml",  # Means like
        "sound": "sl",  # Sounds like
        "spelling": "sp",  # Spelled like
    }

    if match_type not in param_map:
        raise ValueError(
            f"Invalid match_type '{match_type}'. Must be one of: meaning, sound, spelling"
        )

    params = {param_map[match_type]: word, "max": max_results}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(DATAMUSE_BASE, params=params)

            if response.status_code != 200:
                raise ValueError(f"Datamuse API error: {response.text}")

            data = response.json()

            similar = []
            for item in data:
                if item.get("word"):
                    word_data = {"word": item.get("word")}
                    if item.get("score"):
                        word_data["score"] = item.get("score")
                    similar.append(word_data)

            return {
                "word": word,
                "match_type": match_type,
                "similar_words": similar,
                "count": len(similar),
            }

    except httpx.TimeoutException:
        raise ValueError("Datamuse API request timed out")
    except httpx.RequestError as e:
        raise ValueError(f"Datamuse API request failed: {str(e)}")


def _find_similar_words_sync(
    word: str, match_type: str = "meaning", max_results: int = 10
) -> dict:
    """Sync wrapper for find_similar_words."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _find_similar_words_async(word, match_type, max_results),
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                _find_similar_words_async(word, match_type, max_results)
            )
    except RuntimeError:
        return asyncio.run(_find_similar_words_async(word, match_type, max_results))


# Tool definitions

get_definition = Tool(
    name="get_definition",
    description="Get the definition of a word including phonetics, meanings, examples, and related words. Returns detailed dictionary information.",
    parameters=[
        ToolParameter(
            name="word",
            type=ParameterType.STRING,
            description="The word to look up.",
            required=True,
        ),
        ToolParameter(
            name="language",
            type=ParameterType.STRING,
            description="Language code for the dictionary (e.g., 'en' for English, 'es' for Spanish). Default is 'en'.",
            required=False,
            default="en",
        ),
    ],
    category="dictionary",
    tags=["dictionary", "definition", "words", "language"],
).set_handler(_get_definition_sync)


get_synonyms = Tool(
    name="get_synonyms",
    description="Get synonyms (words with similar meaning) for a given word.",
    parameters=[
        ToolParameter(
            name="word",
            type=ParameterType.STRING,
            description="The word to find synonyms for.",
            required=True,
        ),
        ToolParameter(
            name="max_results",
            type=ParameterType.INTEGER,
            description="Maximum number of synonyms to return (1-50). Default is 10.",
            required=False,
            default=10,
        ),
    ],
    category="dictionary",
    tags=["dictionary", "synonyms", "words", "language", "thesaurus"],
).set_handler(_get_synonyms_sync)


get_antonyms = Tool(
    name="get_antonyms",
    description="Get antonyms (words with opposite meaning) for a given word.",
    parameters=[
        ToolParameter(
            name="word",
            type=ParameterType.STRING,
            description="The word to find antonyms for.",
            required=True,
        ),
        ToolParameter(
            name="max_results",
            type=ParameterType.INTEGER,
            description="Maximum number of antonyms to return (1-50). Default is 10.",
            required=False,
            default=10,
        ),
    ],
    category="dictionary",
    tags=["dictionary", "antonyms", "words", "language", "thesaurus"],
).set_handler(_get_antonyms_sync)


find_rhymes = Tool(
    name="find_rhymes",
    description="Find words that rhyme with a given word. Useful for poetry, songwriting, or word games.",
    parameters=[
        ToolParameter(
            name="word",
            type=ParameterType.STRING,
            description="The word to find rhymes for.",
            required=True,
        ),
        ToolParameter(
            name="max_results",
            type=ParameterType.INTEGER,
            description="Maximum number of rhyming words to return (1-50). Default is 10.",
            required=False,
            default=10,
        ),
    ],
    category="dictionary",
    tags=["dictionary", "rhymes", "words", "poetry", "creative"],
).set_handler(_find_rhymes_sync)


find_similar_words = Tool(
    name="find_similar_words",
    description="Find words similar to a given word based on meaning, sound, or spelling. Useful for finding alternative words or solving word puzzles.",
    parameters=[
        ToolParameter(
            name="word",
            type=ParameterType.STRING,
            description="The word to find similar words for.",
            required=True,
        ),
        ToolParameter(
            name="match_type",
            type=ParameterType.STRING,
            description="How to match similar words: 'meaning' (semantically similar), 'sound' (sounds like), or 'spelling' (spelled similarly). Default is 'meaning'.",
            required=False,
            default="meaning",
            enum=["meaning", "sound", "spelling"],
        ),
        ToolParameter(
            name="max_results",
            type=ParameterType.INTEGER,
            description="Maximum number of similar words to return (1-50). Default is 10.",
            required=False,
            default=10,
        ),
    ],
    category="dictionary",
    tags=["dictionary", "similar", "words", "language", "thesaurus"],
).set_handler(_find_similar_words_sync)
