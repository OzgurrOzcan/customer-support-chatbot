"""
Budget Limiter — IP-based daily + Global daily request limits.

Prevents "Denial of Wallet" attacks where an attacker stays
under per-minute rate limits but sends requests all day long,
accumulating massive OpenAI API costs.

Uses Redis atomic INCR for thread-safe counting.
Keys auto-expire daily via TTL (86400 seconds).
"""

import redis.asyncio as redis
from datetime import datetime, timezone
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)


class BudgetLimiter:
    """IP-based and global daily request limits.

    Protects against slow-burn cost attacks that bypass
    per-minute rate limiting.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ip_daily_limit: int = 200,
        global_daily_limit: int = 5000,
    ):
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._ip_daily_limit = ip_daily_limit
        self._global_daily_limit = global_daily_limit

    def _get_today_key(self, prefix: str) -> str:
        """Create a Redis key based on today's UTC date.

        Keys automatically become stale when the date changes.
        The TTL ensures Redis cleans them up.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"budget:{prefix}:{today}"

    async def check_ip_daily_limit(self, request: Request) -> None:
        """Check per-IP daily request limit.

        Each IP can make at most `ip_daily_limit` requests per day.
        Raises HTTP 429 if exceeded.
        """
        client_ip = request.client.host if request.client else "unknown"
        key = self._get_today_key(f"ip:{client_ip}")

        # Atomic increment + set TTL on first request
        current = await self._redis.incr(key)
        if current == 1:
            await self._redis.expire(key, 86400)

        if current > self._ip_daily_limit:
            logger.warning(
                f"IP daily limit exceeded | ip={client_ip} | "
                f"count={current} | limit={self._ip_daily_limit}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Günlük istek limitinize ulaştınız "
                    f"({self._ip_daily_limit} istek/gün). "
                    f"Yarın tekrar deneyebilirsiniz."
                ),
                headers={"Retry-After": "86400"},
            )

    async def check_global_daily_limit(self, request: Request) -> None:
        """Check global daily request limit.

        When total requests from ALL IPs exceed the global limit,
        the entire system temporarily stops accepting requests.
        This is the last line of defense against distributed attacks.
        """
        key = self._get_today_key("global")

        current = await self._redis.incr(key)
        if current == 1:
            await self._redis.expire(key, 86400)

        if current > self._global_daily_limit:
            logger.critical(
                f"GLOBAL daily limit exceeded | "
                f"count={current} | limit={self._global_daily_limit}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Sistem günlük kapasiteye ulaştı. Lütfen yarın tekrar deneyin.",
                headers={"Retry-After": "86400"},
            )

    async def get_usage_stats(self) -> dict:
        """Return current usage statistics (for monitoring)."""
        global_key = self._get_today_key("global")
        global_count = await self._redis.get(global_key)
        return {
            "global_today": int(global_count) if global_count else 0,
            "global_limit": self._global_daily_limit,
            "ip_limit": self._ip_daily_limit,
        }

    async def close(self) -> None:
        """Close Redis connection."""
        await self._redis.close()
