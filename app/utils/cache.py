"""
Redis Response Cache — Caches chat responses to avoid duplicate API calls.

Key design decisions:
  1. SHA256 hash of query → deterministic, fixed-length cache keys
  2. 5-minute TTL → data stays fresh enough
  3. Graceful degradation → if Redis is down, app continues without cache
  4. JSON serialization for complex response objects
"""

import redis.asyncio as redis
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    """Redis-based response cache with automatic TTL.

    If Redis is unavailable, all operations silently return
    None/pass — the app degrades gracefully to uncached mode.
    """

    DEFAULT_TTL = 300  # 5 minutes

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis connection.

        Args:
            redis_url: Redis connection URL.
        """
        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._available = True
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, running without cache: {e}")
            self._redis = None
            self._available = False

    def _make_key(self, query: str) -> str:
        """Create a deterministic cache key from query text.

        Uses SHA256 hash for fixed-length keys regardless
        of query length.

        Args:
            query: The user's query text.

        Returns:
            Redis key string.
        """
        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
        return f"chat:cache:{query_hash}"

    async def get(self, query: str) -> dict | None:
        """Look up a cached response.

        Args:
            query: The user's query text.

        Returns:
            Cached response dict, or None on miss/error.
        """
        if not self._available:
            return None

        try:
            key = self._make_key(query)
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache read error (continuing without cache): {e}")
            return None

    async def set(
        self, query: str, data: dict, ttl: int = DEFAULT_TTL
    ) -> None:
        """Store a response in the cache.

        Args:
            query: The user's query text (used to generate key).
            data: The response data to cache.
            ttl: Time-to-live in seconds (default: 5 minutes).
        """
        if not self._available:
            return

        try:
            key = self._make_key(query)
            await self._redis.set(key, json.dumps(data), ex=ttl)
        except Exception as e:
            logger.warning(f"Cache write error (continuing without cache): {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis cache connection closed")
