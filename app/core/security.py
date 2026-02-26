"""
API Key Authentication — Validates X-API-Key header.

The API key is stored in the Next.js server-side environment
and sent ONLY from server-side API routes. It is NEVER exposed
to the browser client.
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

# Look for the API key in the "X-API-Key" header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """
    Validate the API key from the request header.

    Raises:
        HTTPException 401: If no API key is provided.
        HTTPException 403: If the API key is invalid.

    Returns:
        The validated API key string.
    """
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header.",
        )

    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
