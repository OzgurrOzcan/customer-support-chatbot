"""
Shared FastAPI Dependencies.

Provides dependency injection functions for accessing
application services (search, LLM, cache) from route handlers.
"""

from fastapi import Request
from app.services.search_service import SearchService
from app.services.llm_service import LLMService
from app.services.chat_service import ChatService
from app.utils.cache import ResponseCache
from app.core.budget_limiter import BudgetLimiter


def get_search_service(request: Request) -> SearchService:
    """Inject SearchService from app state."""
    return request.app.state.search_service


def get_llm_service(request: Request) -> LLMService:
    """Inject LLMService from app state."""
    return request.app.state.llm_service


def get_cache(request: Request) -> ResponseCache:
    """Inject ResponseCache from app state."""
    return request.app.state.cache


def get_budget_limiter(request: Request) -> BudgetLimiter:
    """Inject BudgetLimiter from app state."""
    return request.app.state.budget_limiter


def get_chat_service(request: Request) -> ChatService:
    """Create and return a ChatService with all dependencies.

    The ChatService is created per-request but uses the
    shared (singleton) SearchService, LLMService, and ResponseCache.
    """
    return ChatService(
        search_service=request.app.state.search_service,
        llm_service=request.app.state.llm_service,
        cache=request.app.state.cache,
    )
