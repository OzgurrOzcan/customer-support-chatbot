"""
CORS Middleware Configuration.

Restricts which origins can call the API.
Only allows the configured Next.js domain(s).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings


def setup_cors(app: FastAPI) -> None:
    """Add CORS middleware to the application.

    IMPORTANT: Never use allow_origins=["*"] in production.
    This would let any website call your API.
    """
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["X-API-Key", "Content-Type"],
        max_age=600,  # Cache preflight for 10 minutes
    )
