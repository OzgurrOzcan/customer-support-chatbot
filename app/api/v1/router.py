"""
V1 Router — Aggregates all v1 API routes.

Centralizes route registration so main.py only needs
a single include_router() call.
"""

from fastapi import APIRouter
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router

v1_router = APIRouter()
v1_router.include_router(chat_router)
v1_router.include_router(health_router)
