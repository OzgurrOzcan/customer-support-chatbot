"""
Security Headers Middleware.

Adds standard security headers to every response:
  - X-Content-Type-Options: nosniff — prevents MIME sniffing
  - X-Frame-Options: DENY — prevents clickjacking
  - X-XSS-Protection — enables browser XSS filter
  - Strict-Transport-Security — enforces HTTPS
  - Referrer-Policy — controls referrer information
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Strict transport security (HTTPS only)
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
