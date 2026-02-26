"""
Global Exception Handler — Catches ALL unhandled exceptions.

NEVER leaks internal details (file paths, library versions,
stack traces, connection strings) to the client.
Logs the full error internally for debugging.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and return a safe response.

    The full traceback is logged internally, but the client
    only receives a generic error message and request ID.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Log the FULL error internally
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "traceback": traceback.format_exc(),
        },
    )

    # Return a GENERIC message to the client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
        },
    )
