"""
Rate Limiter — Per-minute and burst protection using slowapi.

Uses Redis as backend storage so limits work correctly
across multiple Uvicorn workers.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=settings.redis_url,
    strategy="fixed-window",
)
