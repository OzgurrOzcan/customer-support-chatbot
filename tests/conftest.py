"""
Test Fixtures — Shared test configuration.

Provides mock services and test client for all tests.
Uses monkeypatch to set required environment variables
before the app starts.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
import os


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Set required environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("API_KEYS", '["test-api-key"]')
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("DEBUG", "true")


@pytest.fixture
def mock_search_service():
    """Mock SearchService for testing without Pinecone."""
    mock = AsyncMock()
    mock.search.return_value = [
        {
            "text": "Pepsi, Gelişim Pazarlama'nın ana ürünüdür.",
            "brand": "pepsi",
            "doc_type": "product_info",
            "url": "https://gelisimpazarlama.com/pepsi",
            "score": 0.95,
        }
    ]
    return mock


@pytest.fixture
def mock_llm_service():
    """Mock LLMService for testing without OpenAI."""
    mock = AsyncMock()
    mock.generate_response.return_value = (
        "Pepsi, Gelişim Pazarlama'nın dağıttığı popüler bir içecek markasıdır."
    )
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_cache():
    """Mock ResponseCache for testing without Redis."""
    mock = AsyncMock()
    mock.get.return_value = None  # Default: no cache hit
    mock.set.return_value = None
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_budget_limiter():
    """Mock BudgetLimiter for testing without Redis."""
    mock = AsyncMock()
    mock.check_ip_daily_limit.return_value = None
    mock.check_global_daily_limit.return_value = None
    mock.close = AsyncMock()
    return mock


@pytest.fixture
async def test_client(
    mock_search_service,
    mock_llm_service,
    mock_cache,
    mock_budget_limiter,
):
    """Create a test client with mocked services.

    Uses monkeypatch to inject mock services into app.state
    after the app is created but before tests run.
    """
    with patch("app.core.rate_limiter.limiter") as mock_limiter:
        # Disable rate limiting in tests
        mock_limiter.limit.return_value = lambda f: f

        from app.main import create_app

        app = create_app()

        # Override app state with mocks
        app.state.search_service = mock_search_service
        app.state.llm_service = mock_llm_service
        app.state.cache = mock_cache
        app.state.budget_limiter = mock_budget_limiter

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client
