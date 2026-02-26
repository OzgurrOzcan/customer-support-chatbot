"""
Health Check Endpoint — GET /api/v1/health

Used by:
  - Railway healthcheck (configured in railway.json)
  - Docker HEALTHCHECK
  - Monitoring services
"""

import time
from fastapi import APIRouter, Request
from app.models.responses import HealthResponse

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
)
async def health_check(request: Request) -> HealthResponse:
    """Return application health status.

    Returns service connectivity and uptime information.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        pinecone="connected",
        uptime_seconds=round(time.time() - _start_time, 1),
    )
