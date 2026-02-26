"""
FastAPI Application Factory — Entry Point.

Creates the FastAPI app with all middleware, routes, and services.
Uses the lifespan context manager to initialize and cleanup
services (Pinecone, OpenAI, Redis) once at startup/shutdown.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.v1.router import v1_router
from app.middleware.cors import setup_cors
from app.middleware.error_handler import global_exception_handler
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.core.logging_config import setup_logging
from app.core.budget_limiter import BudgetLimiter
from app.core.rate_limiter import limiter
from app.services.search_service import SearchService
from app.services.llm_service import LLMService
from app.utils.cache import ResponseCache

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request body size limiter middleware
# ---------------------------------------------------------------------------
class LimitRequestSizeMiddleware(BaseHTTPMiddleware):
    """Reject requests with body > 10KB to prevent memory abuse."""

    MAX_BODY_SIZE = 10_240  # 10KB — more than enough for a chat query

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "payload_too_large",
                    "message": "Request body too large. Maximum 10KB allowed.",
                },
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Application lifespan — startup & shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services at startup, clean up at shutdown."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    logger.info("🚀 Starting Gelişim Chatbot API...")

    # Initialize services ONCE (connection pooling)
    app.state.search_service = SearchService(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
    )
    app.state.llm_service = LLMService(
        api_key=settings.openai_api_key,
    )
    app.state.cache = ResponseCache(redis_url=settings.redis_url)

    # Budget Limiter (IP daily + Global daily)
    app.state.budget_limiter = BudgetLimiter(
        redis_url=settings.redis_url,
        ip_daily_limit=settings.ip_daily_limit,
        global_daily_limit=settings.global_daily_limit,
    )

    logger.info("✅ All services initialized successfully")

    yield

    # Graceful shutdown
    logger.info("🛑 Shutting down services...")
    await app.state.llm_service.close()
    await app.state.cache.close()
    await app.state.budget_limiter.close()
    logger.info("✅ Shutdown complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Production-ready chatbot API for Gelişim Pazarlama",
        docs_url="/docs" if settings.debug else None,  # Disable in prod
        redoc_url=None,
        lifespan=lifespan,
    )

    # --- Rate Limiter (slowapi) ---
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Middleware stack (order matters — executed bottom-to-top) ---
    app.add_middleware(LimitRequestSizeMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    setup_cors(app)

    # --- Global exception handler ---
    app.add_exception_handler(Exception, global_exception_handler)

    # --- Routes ---
    app.include_router(v1_router, prefix="/api/v1")

    return app


# Create the app instance (used by uvicorn: app.main:app)
app = create_app()
