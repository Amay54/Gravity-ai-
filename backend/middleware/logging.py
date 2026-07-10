import time
from typing import Any

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware tracking API call durations, client IPs, response statuses, and associated transaction IDs.
    Utilizes Loguru contextualization to propagate tracing variables into all logs fired within the request context.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "-")

        # Extract metadata from headers/parameters
        session_id = request.query_params.get(
            "session_id", request.headers.get("x-session-id", "-")
        )
        user_id = request.headers.get("x-user-id", "-")
        client_host = request.client.host if request.client else "unknown"

        # Log request start with context tracing
        with logger.contextualize(
            request_id=request_id, session_id=session_id, user_id=user_id, execution_time="-"
        ):
            logger.info(
                f"HTTP Request: {request.method} {request.url.path} from client {client_host}"
            )

        try:
            response: Response = await call_next(request)
            duration = (time.perf_counter() - start_time) * 1000
            duration_str = f"{duration:.2f}ms"

            # Log successful response with contextual execution time
            with logger.contextualize(
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                execution_time=duration_str,
            ):
                logger.info(f"HTTP Response: {response.status_code}")
            return response

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            duration_str = f"{duration:.2f}ms"

            with logger.contextualize(
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                execution_time=duration_str,
            ):
                logger.error(
                    f"HTTP Request Failed: {request.method} {request.url.path} - Exception: {str(e)}"
                )
            raise
