"""
Response Schemas — Pydantic models for outgoing responses.

Standardized response format for all API endpoints.
ErrorResponse ensures no internal details leak to clients.
"""

from pydantic import BaseModel
from typing import Optional


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    response: str
    sources: list[str] = []
    cached: bool = False


class HealthResponse(BaseModel):
    """Response from the health check endpoint."""

    status: str = "healthy"
    version: str = "1.0.0"
    pinecone: str = "connected"
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Standardized error response — safe for clients.

    Never includes internal details like tracebacks.
    The request_id can be used for support/debugging.
    """

    error: str           # Machine-readable error code
    message: str         # Human-readable message (generic)
    request_id: Optional[str] = None
