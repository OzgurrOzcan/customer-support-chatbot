"""
Search Service — Pinecone vector search with brand filtering.

CRITICAL architecture decisions:
  1. Pinecone client is initialized ONCE at startup
  2. Brand filter narrows search space before vector similarity
  3. Uses Pinecone Inference API for embedding generation
  4. input_type="query" is required for E5 models

Ported from the original search.py and adapted for async FastAPI.
"""

from pinecone import Pinecone
from app.services.brand_detector import detect_brand
from app.core.exceptions import SearchError
import logging
import asyncio

logger = logging.getLogger(__name__)


class SearchService:
    """Pinecone vector search service.

    Initialized once at application startup. Uses the Pinecone
    Inference API for query embedding generation with the
    multilingual-e5-large model.
    """

    def __init__(self, api_key: str, index_name: str = "gelisim-bot-index"):
        """Initialize Pinecone client and index.

        This is called once in the FastAPI lifespan.
        The client is reused across all requests.
        """
        try:
            self._pc = Pinecone(api_key=api_key)
            self._index = self._pc.Index(index_name)
            self._api_key = api_key
            logger.info(f"✅ Pinecone index '{index_name}' connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Pinecone: {e}")
            raise SearchError(f"Pinecone connection failed: {e}")

    async def search(
        self, query: str, top_k: int = 3, max_retries: int = 3
    ) -> list[dict]:
        """Perform semantic search with brand filtering and retry logic.

        Steps:
          1. Detect brand from query text
          2. Generate query embedding via Pinecone Inference
          3. Query Pinecone with brand filter (retry on transient errors)
          4. Return formatted results

        Args:
            query: User's search query.
            top_k: Number of top results to return.
            max_retries: Number of retry attempts for transient errors.

        Returns:
            List of matched documents with text, brand, type, url, score.
        """
        brand = detect_brand(query)
        brand_filter = {"brand": brand}

        logger.info(
            f"Searching | query='{query[:50]}...' | "
            f"brand={brand} | top_k={top_k}"
        )

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                # Run Pinecone operations in thread pool (sync SDK → async)
                results = await asyncio.to_thread(
                    self._search_sync, query, brand_filter, top_k
                )
                return results

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 2 ** (attempt - 1)  # 1s, 2s, 4s...
                    logger.warning(
                        f"Search attempt {attempt}/{max_retries} failed: {e} "
                        f"| Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Search failed after {max_retries} attempts: {e}",
                        exc_info=True,
                    )

        raise SearchError(f"Search operation failed after {max_retries} attempts: {last_error}")

    def _search_sync(
        self, query: str, brand_filter: dict, top_k: int
    ) -> list[dict]:
        """Synchronous Pinecone search (runs in thread pool).

        Pinecone Python SDK is synchronous, so we wrap it
        with asyncio.to_thread() in the async method above.
        """
        # 1. Generate embedding with Pinecone Inference API
        embedding_response = self._pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={"input_type": "query"},
        )
        query_vector = embedding_response[0]["values"]

        # 2. Query Pinecone with brand filter
        results = self._index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=brand_filter,
        )

        # 3. Format results
        formatted = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            formatted.append({
                "text": meta.get("text", ""),
                "brand": meta.get("brand", "unknown"),
                "doc_type": meta.get("doc_type", "unknown"),
                "url": meta.get("url", ""),
                "score": float(match.get("score", 0)),
            })

        logger.info(f"Search returned {len(formatted)} results")
        return formatted
