import time
from typing import Any

from fastapi import Request, Response, status
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    HTTP Rate Limiting Middleware implementing an in-memory sliding window algorithm.
    """

    def __init__(self, app: Any, requests_per_minute: int = 120) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_timestamps: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Retrieve client request timestamps history
        timestamps = self.client_timestamps.get(client_ip, [])

        # Evict timestamps older than 60 seconds (sliding window)
        timestamps = [t for t in timestamps if now - t < 60]

        # Verify if count exceeds maximum requests allowance
        if len(timestamps) >= self.requests_per_minute:
            request_id = getattr(request.state, "request_id", "untracked")
            logger.warning(
                f"[{request_id}] Rate limit exceeded for IP: {client_ip}. Requests in window: {len(timestamps)}"
            )
            return Response(
                content="Too Many Requests. Rate limit exceeded.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Append current request time and update log store
        timestamps.append(now)
        self.client_timestamps[client_ip] = timestamps

        return await call_next(request)
