"""
Rate limiting middleware for API endpoints.
Prevents abuse and ensures fair resource distribution.
"""

import os
import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiter using Redis.

    Limits requests per IP address with burst capacity.
    """

    def __init__(
        self,
        app,
        redis_client: redis.Redis = None,
        rate_limit_per_minute: int = 60,
        burst_size: int = 20,
        enabled: bool = True
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit = rate_limit_per_minute
        self.burst_size = burst_size
        self.enabled = enabled
        self.refill_rate = rate_limit_per_minute / 60.0  # tokens per second

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""

        if not self.enabled or not self.redis_client:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host

        # Check rate limit
        allowed, retry_after = await self._check_rate_limit(client_ip)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content=f'{{"error": "Rate limit exceeded. Retry after {retry_after} seconds."}}',
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "Content-Type": "application/json"
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = await self._get_remaining_tokens(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, int(remaining)))

        return response

    async def _check_rate_limit(self, client_id: str) -> tuple[bool, int]:
        """
        Check if request is allowed using token bucket algorithm.

        Returns:
            (allowed, retry_after_seconds)
        """
        try:
            key = f"rate_limit:{client_id}"
            now = time.time()

            # Get current state from Redis
            pipe = self.redis_client.pipeline()
            pipe.get(f"{key}:tokens")
            pipe.get(f"{key}:last_refill")
            results = await pipe.execute()

            tokens = float(results[0]) if results[0] else self.burst_size
            last_refill = float(results[1]) if results[1] else now

            # Refill tokens based on time elapsed
            time_elapsed = now - last_refill
            new_tokens = min(
                self.burst_size,
                tokens + (time_elapsed * self.refill_rate)
            )

            # Check if we can allow this request
            if new_tokens >= 1.0:
                # Consume one token
                new_tokens -= 1.0

                # Update Redis
                pipe = self.redis_client.pipeline()
                pipe.setex(f"{key}:tokens", 60, str(new_tokens))
                pipe.setex(f"{key}:last_refill", 60, str(now))
                await pipe.execute()

                return True, 0
            else:
                # Calculate retry after
                tokens_needed = 1.0 - new_tokens
                retry_after = int(tokens_needed / self.refill_rate) + 1
                return False, retry_after

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, 0

    async def _get_remaining_tokens(self, client_id: str) -> float:
        """Get remaining tokens for client."""
        try:
            key = f"rate_limit:{client_id}"
            tokens = await self.redis_client.get(f"{key}:tokens")
            return float(tokens) if tokens else self.burst_size
        except Exception:
            return self.burst_size


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on system load.

    Reduces limits when system is under heavy load.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        base_rate: int = 60,
        min_rate: int = 10,
        max_rate: int = 120
    ):
        self.redis_client = redis_client
        self.base_rate = base_rate
        self.min_rate = min_rate
        self.max_rate = max_rate

    async def get_adaptive_rate(self) -> int:
        """
        Calculate adaptive rate based on system metrics.

        Returns:
            Adjusted rate limit per minute
        """
        try:
            # Get system metrics from Redis
            metrics_key = "system:metrics"
            metrics = await self.redis_client.hgetall(metrics_key)

            if not metrics:
                return self.base_rate

            # Calculate load factor
            avg_response_time = float(metrics.get(b"avg_response_time", 0))
            active_requests = int(metrics.get(b"active_requests", 0))
            cache_hit_rate = float(metrics.get(b"cache_hit_rate", 100))

            # Adjust rate based on metrics
            load_factor = 1.0

            # Reduce rate if response times are high
            if avg_response_time > 5.0:  # 5 seconds
                load_factor *= 0.5
            elif avg_response_time > 2.0:  # 2 seconds
                load_factor *= 0.7

            # Reduce rate if too many active requests
            if active_requests > 1000:
                load_factor *= 0.6
            elif active_requests > 500:
                load_factor *= 0.8

            # Increase rate if cache is performing well
            if cache_hit_rate > 80:
                load_factor *= 1.2
            elif cache_hit_rate > 60:
                load_factor *= 1.1

            # Calculate adjusted rate
            adjusted_rate = int(self.base_rate * load_factor)
            adjusted_rate = max(self.min_rate, min(self.max_rate, adjusted_rate))

            logger.debug(
                f"Adaptive rate: {adjusted_rate} "
                f"(factor: {load_factor:.2f}, "
                f"avg_time: {avg_response_time:.2f}s, "
                f"active: {active_requests})"
            )

            return adjusted_rate

        except Exception as e:
            logger.error(f"Adaptive rate calculation error: {e}")
            return self.base_rate


async def update_system_metrics(
    redis_client: redis.Redis,
    avg_response_time: float,
    active_requests: int,
    cache_hit_rate: float
):
    """Update system metrics in Redis for adaptive rate limiting."""
    try:
        metrics_key = "system:metrics"
        await redis_client.hset(
            metrics_key,
            mapping={
                "avg_response_time": str(avg_response_time),
                "active_requests": str(active_requests),
                "cache_hit_rate": str(cache_hit_rate),
                "timestamp": str(time.time())
            }
        )
        await redis_client.expire(metrics_key, 60)  # Expire after 1 minute
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")
