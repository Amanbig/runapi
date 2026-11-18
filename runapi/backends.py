"""Pluggable state backends (in-memory or Redis) for rate limiting and token revocation.

In-memory backends are per-process: with several workers each one keeps its own
counters. Set ``CACHE_BACKEND=redis`` and ``REDIS_URL`` (install ``runapi[redis]``)
to share state across workers and hosts.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("runapi")


def _require_redis():
    try:
        import redis  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "The Redis backend needs the 'redis' package. Install with: pip install runapi[redis]"
        ) from exc


# --------------------------------------------------------------------------- #
# Rate limiting
# --------------------------------------------------------------------------- #
class RateLimitBackend:
    """Counts hits per key inside a fixed window."""

    async def hit(self, key: str, period: int) -> Tuple[int, float]:
        """Record a hit. Returns ``(count_in_window, seconds_until_window_resets)``."""
        raise NotImplementedError


class MemoryRateLimitBackend(RateLimitBackend):
    """Fixed-window counter held in process memory."""

    def __init__(self):
        self._windows: Dict[str, List[float]] = {}  # key -> [count, window_start]
        self._lock = asyncio.Lock()
        self._last_purge = time.time()

    async def hit(self, key: str, period: int) -> Tuple[int, float]:
        now = time.time()
        async with self._lock:
            if now - self._last_purge > period:
                self._purge(now, period)
            window = self._windows.get(key)
            if window is None or now > window[1] + period:
                window = self._windows[key] = [0, now]
            window[0] += 1
            return int(window[0]), max(window[1] + period - now, 0.0)

    def _purge(self, now: float, period: int) -> None:
        """Drop expired windows so memory does not grow with every client seen."""
        self._last_purge = now
        for key in [k for k, (_, start) in self._windows.items() if now > start + period]:
            del self._windows[key]


class RedisRateLimitBackend(RateLimitBackend):
    """Fixed-window counter stored in Redis (shared across workers).

    Fails open: if Redis is unreachable the request is allowed and an error is logged.
    """

    def __init__(self, client: Any, prefix: str = "runapi:rl:"):
        self.client = client
        self.prefix = prefix

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> "RedisRateLimitBackend":
        _require_redis()
        import redis.asyncio as aioredis

        return cls(aioredis.from_url(url), **kwargs)

    async def hit(self, key: str, period: int) -> Tuple[int, float]:
        redis_key = f"{self.prefix}{key}"
        try:
            count = await self.client.incr(redis_key)
            if count == 1:
                await self.client.expire(redis_key, period)
            ttl = await self.client.ttl(redis_key)
            if ttl is None or ttl < 0:  # key lost its expiry; restore it
                await self.client.expire(redis_key, period)
                ttl = period
            return int(count), float(ttl)
        except Exception:
            logger.exception("Redis rate limit backend unavailable; allowing request")
            return 0, float(period)


# --------------------------------------------------------------------------- #
# Token revocation
# --------------------------------------------------------------------------- #
class TokenBlacklist:
    """In-memory store of revoked token ids (``jti``).

    Subclass and override ``add``/``is_revoked`` for other storage.
    """

    def __init__(self):
        self._revoked: Dict[str, float] = {}

    def add(self, jti: str, expires_at: float) -> None:
        self._purge()
        self._revoked[jti] = expires_at

    def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked

    def _purge(self) -> None:
        now = time.time()
        for key in [k for k, exp in self._revoked.items() if exp < now]:
            del self._revoked[key]


class RedisTokenBlacklist(TokenBlacklist):
    """Revoked token ids stored in Redis with a TTL equal to the token's remaining life.

    Uses a synchronous client because token verification is synchronous. If Redis is
    unreachable, revocation checks fail closed (the token is treated as revoked).
    """

    def __init__(self, client: Any, prefix: str = "runapi:revoked:"):
        self.client = client
        self.prefix = prefix

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> "RedisTokenBlacklist":
        _require_redis()
        import redis

        return cls(redis.Redis.from_url(url), **kwargs)

    def add(self, jti: str, expires_at: float) -> None:
        ttl = max(int(expires_at - time.time()) + 1, 1)
        self.client.setex(f"{self.prefix}{jti}", ttl, "1")

    def is_revoked(self, jti: str) -> bool:
        try:
            return bool(self.client.exists(f"{self.prefix}{jti}"))
        except Exception:
            logger.exception("Redis token blacklist unavailable; rejecting token")
            return True


def uses_redis(config: Any) -> Optional[str]:
    """Return the Redis URL when the config selects the Redis backend, else None."""
    if config.cache_backend == "redis":
        if not config.redis_url:
            raise ValueError("CACHE_BACKEND=redis requires REDIS_URL")
        return config.redis_url
    return None
