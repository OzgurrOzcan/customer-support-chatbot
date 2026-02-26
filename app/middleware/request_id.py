"""
Request ID Middleware — Injects a unique ID per request.

This ID is used for:
  1. Correlating log entries across the request lifecycle
  2. Debugging specific requests via support tickets
  3. Returning to the client in the X-Request-ID header
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID into every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use existing ID from header (e.g., from load balancer)
        # or generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
