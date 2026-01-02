"""Redis client for caching and state management.

Provides async Redis operations for:
- Upload state tracking
- Rate limiting
- Session caching
"""

import json
from typing import Any, Optional

import redis.asyncio as redis

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("redis_connected", url=settings.redis_url)
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis_connection_closed")


class RedisCache:
    """High-level Redis cache operations."""

    def __init__(self, prefix: str = "magone"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        """Generate prefixed key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        client = await get_redis()
        return await client.get(self._key(key))

    async def get_json(self, key: str) -> Optional[dict]:
        """Get a JSON value from cache."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a value in cache with optional TTL (seconds)."""
        client = await get_redis()
        return await client.set(self._key(key), value, ex=ttl)

    async def set_json(
        self,
        key: str,
        value: dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a JSON value in cache."""
        return await self.set(key, json.dumps(value), ttl)

    async def delete(self, key: str) -> int:
        """Delete a key from cache."""
        client = await get_redis()
        return await client.delete(self._key(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = await get_redis()
        return await client.exists(self._key(key)) > 0

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        client = await get_redis()
        return await client.incr(self._key(key))

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key."""
        client = await get_redis()
        return await client.expire(self._key(key), ttl)

    async def hset(self, key: str, field: str, value: str) -> int:
        """Set a hash field."""
        client = await get_redis()
        return await client.hset(self._key(key), field, value)

    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get a hash field."""
        client = await get_redis()
        return await client.hget(self._key(key), field)

    async def hgetall(self, key: str) -> dict:
        """Get all hash fields."""
        client = await get_redis()
        return await client.hgetall(self._key(key))

    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields."""
        client = await get_redis()
        return await client.hdel(self._key(key), *fields)

    async def sadd(self, key: str, *members: str) -> int:
        """Add members to a set."""
        client = await get_redis()
        return await client.sadd(self._key(key), *members)

    async def smembers(self, key: str) -> set:
        """Get all set members."""
        client = await get_redis()
        return await client.smembers(self._key(key))

    async def sismember(self, key: str, member: str) -> bool:
        """Check if member is in set."""
        client = await get_redis()
        return await client.sismember(self._key(key), member)


# Default cache instance
cache = RedisCache()
