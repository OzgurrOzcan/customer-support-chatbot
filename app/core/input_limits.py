"""
Input Limits — Character and token limits at the API layer.

Defense-in-depth: Even though the Next.js frontend has character
limits, an attacker can bypass the frontend entirely using
curl/Postman. This module ensures the API itself enforces limits.

Prevents cost attacks where each request contains massive input
text (e.g., 1,000,000 characters) that gets tokenized and billed.
"""

from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Limits
MAX_QUERY_CHARS = 1000       # Maximum character count
MAX_QUERY_TOKENS_EST = 350   # Estimated token limit (~1 token ≈ 3 chars for Turkish)


def estimate_token_count(text: str) -> int:
    """Rough token estimate for Turkish text.

    Turkish averages ~1 token per 3 characters.
    This is not exact but sufficient for a fast upper-bound check.
    For precise counting, use tiktoken — but it adds latency.
    """
    return len(text) // 3 + 1


def validate_query_size(query: str, client_ip: str = "unknown") -> None:
    """Validate query size at the API layer.

    This check runs IN ADDITION to the Pydantic model validation
    (max_length=1000). Double-layer defense:
      - Pydantic: schema-level format validation
      - This function: token-based cost control + logging

    Args:
        query: The user's query string.
        client_ip: Client IP for logging.

    Raises:
        HTTPException 400: If the query exceeds limits.
    """
    # Layer 1: Character limit
    if len(query) > MAX_QUERY_CHARS:
        logger.warning(
            f"Query too long | ip={client_ip} | "
            f"chars={len(query)} | limit={MAX_QUERY_CHARS}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Sorgunuz çok uzun ({len(query)} karakter). "
                f"Maksimum {MAX_QUERY_CHARS} karakter gönderebilirsiniz."
            ),
        )

    # Layer 2: Token estimation check
    estimated_tokens = estimate_token_count(query)
    if estimated_tokens > MAX_QUERY_TOKENS_EST:
        logger.warning(
            f"Query estimated tokens too high | ip={client_ip} | "
            f"est_tokens={estimated_tokens} | limit={MAX_QUERY_TOKENS_EST}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sorgunuz çok karmaşık/uzun. Lütfen daha kısa bir soru sorun.",
        )
