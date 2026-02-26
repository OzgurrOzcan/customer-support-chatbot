"""
Brand Detector — Detects brand names in user queries using fuzzy matching.

Uses rapidfuzz for fuzzy string matching (same logic as pinecone_ingest/search.py).
Each word in the query is compared against KNOWN_BRANDS using fuzz.ratio.
If similarity >= 84%, the brand is considered a match.
"""

from rapidfuzz import process, fuzz
import logging

logger = logging.getLogger(__name__)

# Known brands (must match Pinecone metadata values exactly)
KNOWN_BRANDS: list[str] = [
    "pepsi",
    "pürsu",
    "doğanay",
    "kızılay",
    "pınar",
    "golf",
    "lipton",
    "fruko",
    "erikli",
    "fritolay",
    "yedigün",
]

# Default brand filter when no brand is detected
DEFAULT_BRAND = "sirket_genel"

# Minimum fuzzy match score (0-100) to accept a brand match
FUZZY_SCORE_CUTOFF = 84


def detect_brand(query: str) -> str:
    """Detect brand name from user query using fuzzy matching.

    Splits the query into words and compares each word against
    KNOWN_BRANDS using rapidfuzz ratio scorer. The first word
    that matches with a score >= 84% is returned as the detected brand.

    Args:
        query: The user's input query.

    Returns:
        The detected brand name, or "sirket_genel" for general queries.
    """
    query_lower = query.lower()
    query_words = query_lower.split()

    for word in query_words:
        result = process.extractOne(
            word,
            KNOWN_BRANDS,
            scorer=fuzz.ratio,
            score_cutoff=FUZZY_SCORE_CUTOFF,
        )
        if result:
            detected_brand = result[0]  # (match, score, index)
            logger.info(
                f"Fuzzy brand match: '{word}' → '{detected_brand}' "
                f"(score: {result[1]:.0f})"
            )
            return detected_brand

    return DEFAULT_BRAND
