"""
Chat Service — Orchestrates the full chat pipeline.

Coordinates between:
  - SearchService (Pinecone vector search)
  - LLMService (OpenAI response generation)
  - ResponseCache (Redis caching)

This service contains zero security logic — security is handled
by the middleware and route-level dependencies.
"""

from typing import AsyncGenerator
from app.services.search_service import SearchService
from app.services.llm_service import LLMService
from app.utils.cache import ResponseCache
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates the search → LLM → cache pipeline."""

    def __init__(
        self,
        search_service: SearchService,
        llm_service: LLMService,
        cache: ResponseCache,
    ):
        self._search = search_service
        self._llm = llm_service
        self._cache = cache

    async def get_response(self, query: str) -> dict:
        """Process a chat query through the full pipeline.

        Flow:
          1. Check cache for existing response
          2. If cache miss → search Pinecone for context
          3. Format context into text
          4. Send to LLM for answer generation
          5. Cache the result
          6. Return response with sources

        Args:
            query: The user's sanitized and validated query.

        Returns:
            Dict with response, sources, and cached flag.
        """
        # 1. Check cache
        cached = await self._cache.get(query)
        if cached:
            logger.info(f"Cache HIT for query: '{query[:50]}...'")
            return {
                "response": cached["response"],
                "sources": cached.get("sources", []),
                "cached": True,
            }

        logger.info(f"Cache MISS for query: '{query[:50]}...'")

        # 2. Search Pinecone
        search_results = await self._search.search(query, top_k=3)

        # 3. Format context
        context = self._format_context(search_results)
        sources = self._extract_sources(search_results)

        # 4. Generate LLM response
        response = await self._llm.generate_response(query, context)

        # 5. Cache the result
        cache_data = {"response": response, "sources": sources}
        await self._cache.set(query, cache_data)

        # 6. Return
        return {
            "response": response,
            "sources": sources,
            "cached": False,
        }

    async def get_stream_response(self, query: str) -> AsyncGenerator[str, None]:
        """Process a chat query through the streaming pipeline with cache.

        Flow:
          - Cache HIT  → yield cached response word-by-word (simulated stream)
          - Cache MISS → stream from LLM + buffer tokens → cache when done

        Args:
            query: The user's sanitized and validated query.

        Yields:
            Individual token/word strings.
        """
        # 1. Check cache
        cached = await self._cache.get(query)
        if cached:
            logger.info(f"Stream Cache HIT for query: '{query[:50]}...'")
            # Simulate streaming from cached full response
            words = cached["response"].split(" ")
            for word in words:
                yield word + " "
            return

        logger.info(f"Stream Cache MISS for query: '{query[:50]}...'")

        # 2. Search Pinecone (before stream starts)
        search_results = await self._search.search(query, top_k=3)
        context = self._format_context(search_results)
        sources = self._extract_sources(search_results)

        # 3. Stream from LLM + buffer tokens
        full_response = []
        async for token in self._llm.generate_stream(query, context):
            full_response.append(token)
            yield token

        # 4. Stream completed → cache the full response
        complete_text = "".join(full_response)
        cache_data = {"response": complete_text, "sources": sources}
        await self._cache.set(query, cache_data)
        logger.info(f"Stream response cached | query='{query[:50]}...'")

    def _format_context(self, results: list[dict]) -> str:
        """Format Pinecone results into context text for the LLM.

        Args:
            results: List of search result dictionaries.

        Returns:
            Formatted context string.
        """
        if not results:
            return "Veritabanında ilgili bilgi bulunamadı."

        parts = []
        for i, result in enumerate(results, 1):
            text = result.get("text", "")
            brand = result.get("brand", "unknown")
            url = result.get("url", "")
            score = result.get("score", 0)

            part = (
                f"[Kaynak {i}] (Skor: {score:.2f})\n"
                f"Marka: {brand}\n"
                f"İçerik: {text}"
            )
            if url:
                part += f"\nURL: {url}"
            parts.append(part)

        return "\n\n---\n\n".join(parts)

    def _extract_sources(self, results: list[dict]) -> list[str]:
        """Extract source URLs from search results.

        Args:
            results: List of search result dictionaries.

        Returns:
            List of unique, non-empty URL strings.
        """
        urls = []
        for result in results:
            url = result.get("url", "")
            if url and url not in urls:
                urls.append(url)
        return urls
