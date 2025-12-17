"""
Text analysis tools using local Python libraries.

Provides language detection, sentiment analysis, noun phrase extraction,
word frequency analysis, and spelling correction.

No API required - all processing is done locally for privacy and no rate limits.

Dependencies:
- langdetect: Language detection
- textblob: Sentiment analysis, noun phrases, spelling correction
"""

import logging
from collections import Counter
from typing import Optional

from tool_master.schemas.tool import ParameterType, Tool, ToolParameter

logger = logging.getLogger(__name__)

# Language code to name mapping for common languages
LANGUAGE_NAMES = {
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
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "pa": "Punjabi",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "sq": "Albanian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Tagalog",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
}


def _detect_text_language_sync(text: str) -> dict:
    """Detect the language of given text using langdetect."""
    try:
        from langdetect import detect, detect_langs
    except ImportError:
        raise ValueError(
            "langdetect library not installed. Install with: pip install langdetect"
        )

    if not text.strip():
        raise ValueError("Text for language detection cannot be empty")

    try:
        # Get the most likely language
        detected = detect(text)

        # Get probability scores for top languages
        probabilities = detect_langs(text)
        top_languages = []
        for lang_prob in probabilities[:3]:
            lang_code = str(lang_prob.lang)
            top_languages.append({
                "language": lang_code,
                "language_name": LANGUAGE_NAMES.get(lang_code, "Unknown"),
                "probability": round(lang_prob.prob, 4),
            })

        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "detected_language": detected,
            "language_name": LANGUAGE_NAMES.get(detected, "Unknown"),
            "confidence": top_languages[0]["probability"] if top_languages else 0,
            "alternatives": top_languages[1:] if len(top_languages) > 1 else [],
        }

    except Exception as e:
        raise ValueError(f"Language detection failed: {str(e)}")


def _analyze_sentiment_sync(text: str) -> dict:
    """Analyze the sentiment of text using TextBlob."""
    try:
        from textblob import TextBlob
    except ImportError:
        raise ValueError(
            "textblob library not installed. Install with: pip install textblob"
        )

    if not text.strip():
        raise ValueError("Text for sentiment analysis cannot be empty")

    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1

        # Determine sentiment label
        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Determine subjectivity label
        if subjectivity > 0.6:
            subjectivity_label = "subjective"
        elif subjectivity < 0.4:
            subjectivity_label = "objective"
        else:
            subjectivity_label = "mixed"

        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "sentiment": sentiment,
            "polarity": round(polarity, 4),
            "polarity_description": "Ranges from -1 (negative) to 1 (positive)",
            "subjectivity": round(subjectivity, 4),
            "subjectivity_label": subjectivity_label,
            "subjectivity_description": "Ranges from 0 (objective) to 1 (subjective)",
        }

    except Exception as e:
        raise ValueError(f"Sentiment analysis failed: {str(e)}")


def _extract_noun_phrases_sync(text: str) -> dict:
    """Extract noun phrases from text using TextBlob."""
    try:
        from textblob import TextBlob
    except ImportError:
        raise ValueError(
            "textblob library not installed. Install with: pip install textblob"
        )

    if not text.strip():
        raise ValueError("Text for noun phrase extraction cannot be empty")

    try:
        blob = TextBlob(text)
        noun_phrases = list(blob.noun_phrases)

        # Count occurrences and sort by frequency
        phrase_counts = Counter(noun_phrases)
        sorted_phrases = [
            {"phrase": phrase, "count": count}
            for phrase, count in phrase_counts.most_common()
        ]

        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "noun_phrases": sorted_phrases,
            "total_count": len(noun_phrases),
            "unique_count": len(phrase_counts),
        }

    except Exception as e:
        raise ValueError(f"Noun phrase extraction failed: {str(e)}")


def _get_word_frequency_sync(
    text: str, top_n: int = 20, exclude_stopwords: bool = True
) -> dict:
    """Get word frequency counts from text."""
    try:
        from textblob import TextBlob
    except ImportError:
        raise ValueError(
            "textblob library not installed. Install with: pip install textblob"
        )

    if not text.strip():
        raise ValueError("Text for word frequency analysis cannot be empty")

    # Common English stopwords
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
        "can", "could", "did", "do", "does", "doing", "done", "for", "from", "had",
        "has", "have", "having", "he", "her", "here", "hers", "him", "his", "how",
        "i", "if", "in", "into", "is", "it", "its", "just", "me", "might", "more",
        "most", "my", "no", "not", "now", "of", "on", "only", "or", "other", "our",
        "out", "over", "own", "s", "same", "she", "should", "so", "some", "such",
        "t", "than", "that", "the", "their", "them", "then", "there", "these",
        "they", "this", "those", "through", "to", "too", "under", "up", "very",
        "was", "we", "were", "what", "when", "where", "which", "while", "who",
        "whom", "why", "will", "with", "would", "you", "your", "yours",
    }

    top_n = min(max(1, top_n), 100)

    try:
        blob = TextBlob(text.lower())
        words = blob.words

        # Filter out non-alphabetic tokens and optionally stopwords
        filtered_words = []
        for word in words:
            word_str = str(word)
            if word_str.isalpha():
                if not exclude_stopwords or word_str not in STOPWORDS:
                    filtered_words.append(word_str)

        # Count word frequencies
        word_counts = Counter(filtered_words)
        top_words = [
            {"word": word, "count": count}
            for word, count in word_counts.most_common(top_n)
        ]

        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "word_frequencies": top_words,
            "total_words": len(filtered_words),
            "unique_words": len(word_counts),
            "stopwords_excluded": exclude_stopwords,
        }

    except Exception as e:
        raise ValueError(f"Word frequency analysis failed: {str(e)}")


def _correct_spelling_sync(text: str) -> dict:
    """Suggest spelling corrections for text using TextBlob."""
    try:
        from textblob import TextBlob, Word
    except ImportError:
        raise ValueError(
            "textblob library not installed. Install with: pip install textblob"
        )

    if not text.strip():
        raise ValueError("Text for spelling correction cannot be empty")

    try:
        blob = TextBlob(text)
        corrected = blob.correct()

        # Find individual word corrections
        corrections = []
        original_words = blob.words
        corrected_words = corrected.words

        for i, (orig, corr) in enumerate(zip(original_words, corrected_words)):
            orig_str = str(orig)
            corr_str = str(corr)
            if orig_str.lower() != corr_str.lower():
                # Get spelling suggestions for the original word
                word = Word(orig_str)
                suggestions = word.spellcheck()[:3]  # Top 3 suggestions
                corrections.append({
                    "original": orig_str,
                    "corrected": corr_str,
                    "suggestions": [
                        {"word": s[0], "confidence": round(s[1], 4)}
                        for s in suggestions
                    ],
                })

        return {
            "original_text": text,
            "corrected_text": str(corrected),
            "has_corrections": len(corrections) > 0,
            "correction_count": len(corrections),
            "corrections": corrections,
        }

    except Exception as e:
        raise ValueError(f"Spelling correction failed: {str(e)}")


# Tool definitions

detect_text_language = Tool(
    name="detect_text_language",
    description="Detect the language of given text. Returns the detected language code, name, and confidence level.",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to detect the language of.",
            required=True,
        ),
    ],
    category="text_analysis",
    tags=["text", "language", "detection", "nlp"],
).set_handler(_detect_text_language_sync)


analyze_sentiment = Tool(
    name="analyze_sentiment",
    description="Analyze the sentiment (positive/negative/neutral) and subjectivity of text. Returns polarity score (-1 to 1) and subjectivity score (0 to 1).",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to analyze sentiment for.",
            required=True,
        ),
    ],
    category="text_analysis",
    tags=["text", "sentiment", "analysis", "nlp", "opinion"],
).set_handler(_analyze_sentiment_sync)


extract_noun_phrases = Tool(
    name="extract_noun_phrases",
    description="Extract noun phrases (key topics/entities) from text. Useful for identifying main subjects and themes.",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to extract noun phrases from.",
            required=True,
        ),
    ],
    category="text_analysis",
    tags=["text", "noun_phrases", "extraction", "nlp", "topics"],
).set_handler(_extract_noun_phrases_sync)


get_word_frequency = Tool(
    name="get_word_frequency",
    description="Count word frequencies in text. Useful for finding the most common words and analyzing vocabulary.",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to analyze word frequencies for.",
            required=True,
        ),
        ToolParameter(
            name="top_n",
            type=ParameterType.INTEGER,
            description="Number of top words to return (1-100). Default is 20.",
            required=False,
            default=20,
        ),
        ToolParameter(
            name="exclude_stopwords",
            type=ParameterType.BOOLEAN,
            description="Whether to exclude common stopwords (the, a, is, etc.). Default is true.",
            required=False,
            default=True,
        ),
    ],
    category="text_analysis",
    tags=["text", "frequency", "words", "nlp", "vocabulary"],
).set_handler(_get_word_frequency_sync)


correct_spelling = Tool(
    name="correct_spelling",
    description="Check and suggest spelling corrections for text. Returns the corrected text and details about each correction.",
    parameters=[
        ToolParameter(
            name="text",
            type=ParameterType.STRING,
            description="The text to check and correct spelling for.",
            required=True,
        ),
    ],
    category="text_analysis",
    tags=["text", "spelling", "correction", "nlp", "grammar"],
).set_handler(_correct_spelling_sync)
