import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware that generates or captures a request ID header to enable execution auditing.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Check if client sent an ID, otherwise create a new UUID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Save request ID to state so downstream routes/loggers can read it
        request.state.request_id = request_id

        response: Response = await call_next(request)

        # Inject the ID into response headers for client tracing
        response.headers["X-Request-ID"] = request_id
        return response
