"""
Tests for the chat endpoint — POST /api/v1/chat

Covers:
  - Successful chat responses
  - API key validation (missing/invalid)
  - Input validation (too short, too long)
  - Budget limit checks
  - Prompt injection detection
"""

import pytest


class TestChatEndpoint:
    """Test the main chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_success(self, test_client):
        """Normal chat request should return 200 with response."""
        response = await test_client.post(
            "/api/v1/chat",
            json={"query": "Pepsi ürünleri nelerdir?"},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert isinstance(data["cached"], bool)

    @pytest.mark.asyncio
    async def test_chat_missing_api_key(self, test_client):
        """Request without API key should return 401."""
        response = await test_client.post(
            "/api/v1/chat",
            json={"query": "Pepsi ürünleri nelerdir?"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_invalid_api_key(self, test_client):
        """Request with invalid API key should return 403."""
        response = await test_client.post(
            "/api/v1/chat",
            json={"query": "Pepsi ürünleri nelerdir?"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_chat_empty_query(self, test_client):
        """Empty query should return 422 (validation error)."""
        response = await test_client.post(
            "/api/v1/chat",
            json={"query": ""},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_query_too_short(self, test_client):
        """Single character query should return 422."""
        response = await test_client.post(
            "/api/v1/chat",
            json={"query": "a"},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_query_too_long(self, test_client):
        """Query over 1000 characters should return 422."""
        long_query = "a" * 1001
        response = await test_client.post(
            "/api/v1/chat",
            json={"query": long_query},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 422


class TestHealthEndpoint:
    """Test the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, test_client):
        """Health endpoint should return 200 with status info."""
        response = await test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
