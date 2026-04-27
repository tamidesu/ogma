from typing import Optional

import redis.asyncio as aioredis
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_redis: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    global _redis
    try:
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        # Verify connection
        await _redis.ping()
        logger.info("redis_connected", url=settings.redis_url)
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e))
        _redis = None


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
        logger.info("redis_disconnected")


async def get_redis() -> aioredis.Redis | None:
    return _redis
