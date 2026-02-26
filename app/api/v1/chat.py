"""
Chat Endpoint — POST /api/v1/chat

The main entry point for the chatbot. Implements all security
checks in the correct order:

  1. API Key verification (dependency)
  2. Rate limiting (slowapi decorator)
  3. Budget check — IP daily + Global daily (BudgetLimiter)
  4. Input validation — character/token limits (InputLimiter)
  5. Prompt injection detection (TextSanitizer)
  6. Cache check → Search → LLM → Cache store (ChatService)
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse

from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.core.security import verify_api_key
from app.core.rate_limiter import limiter
from app.core.input_limits import validate_query_size
from app.api.dependencies import get_chat_service, get_budget_limiter
from app.services.chat_service import ChatService
from app.core.budget_limiter import BudgetLimiter
from app.utils.text_sanitizer import detect_prompt_injection

import logging

router = APIRouter(tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message and get a response",
    responses={
        400: {"description": "Invalid input (too long, injection detected)"},
        401: {"description": "Missing API key"},
        403: {"description": "Invalid API key"},
        429: {"description": "Rate limit or daily limit exceeded"},
    },
)
@limiter.limit("20/minute")  # Per-IP per-minute limit
async def chat(
    request: Request,
    body: ChatRequest,
    api_key: str = Depends(verify_api_key),
    budget: BudgetLimiter = Depends(get_budget_limiter),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Main chat endpoint.

    Security Flow:
      API Key → Rate Limit → Budget Check → Input Limits →
      Prompt Injection → Cache → Search → LLM → Respond
    """
    client_ip = request.client.host if request.client else "unknown"

    # Step 1: Budget check (IP daily + Global daily)
    await budget.check_ip_daily_limit(request)
    await budget.check_global_daily_limit(request)

    # Step 2: Character/Token limits (defense-in-depth)
    validate_query_size(body.query, client_ip=client_ip)

    # Step 3: Prompt injection detection
    if detect_prompt_injection(body.query):
        logger.warning(
            f"Prompt injection blocked | ip={client_ip} | "
            f"query='{body.query[:50]}...'"
        )
        return ChatResponse(
            response="Bu sorguyu işleyemiyorum. Lütfen farklı bir soru sorun.",
            sources=[],
            cached=False,
        )

    # Step 4: Process through chat pipeline
    result = await chat_service.get_response(body.query)

    logger.info(
        f"Chat response sent | ip={client_ip} | "
        f"cached={result['cached']} | "
        f"query='{body.query[:50]}...'"
    )

    return ChatResponse(
        response=result["response"],
        sources=result["sources"],
        cached=result["cached"],
    )


@router.post(
    "/chat/stream",
    summary="Send a chat message and get a streaming SSE response",
    responses={
        401: {"description": "Missing API key"},
        403: {"description": "Invalid API key"},
        429: {"description": "Rate limit or daily limit exceeded"},
    },
)
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    api_key: str = Depends(verify_api_key),
    budget: BudgetLimiter = Depends(get_budget_limiter),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    Instead of waiting for the full response, tokens are sent
    to the client as they arrive from OpenAI. This reduces
    perceived latency by ~2 seconds.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Security checks (same as non-streaming)
    await budget.check_ip_daily_limit(request)
    await budget.check_global_daily_limit(request)
    validate_query_size(body.query, client_ip=client_ip)

    if detect_prompt_injection(body.query):
        return ChatResponse(
            response="Bu sorguyu işleyemiyorum. Lütfen farklı bir soru sorun.",
            sources=[],
            cached=False,
        )

    # Stream response with cache support
    async def event_generator():
        try:
            async for token in chat_service.get_stream_response(body.query):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error | ip={client_ip} | error={e}")
            yield f"data: [ERROR] Bir hata oluştu: {type(e).__name__}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
