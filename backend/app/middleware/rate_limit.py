import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings
from app.core.exceptions import RateLimitExceededError

logger = structlog.get_logger(__name__)

# Paths exempt from rate limiting
_EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Attach request_id for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        if request.url.path in _EXEMPT_PATHS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # Rate limit by user_id (from JWT) or IP
        try:
            from app.db.redis import get_redis
            redis = await get_redis()

            client_key = self._get_client_key(request)
            bucket_key = f"rl:{client_key}:{int(time.time() // 60)}"

            count = await redis.incr(bucket_key)
            if count == 1:
                await redis.expire(bucket_key, 90)  # 1.5min window

            remaining = max(0, settings.rate_limit_per_minute - count)
            limit_hit = count > settings.rate_limit_per_minute

        except Exception:
            # Redis down — fail open (don't block requests)
            limit_hit = False
            remaining = settings.rate_limit_per_minute

        if limit_hit:
            raise RateLimitExceededError()

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        return response

    def _get_client_key(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            # Use token tail as cheap key (avoids decoding)
            return f"token:{auth[-16:]}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host if request.client else 'unknown'}"
