"""
Custom Exception Classes for the application.

These exceptions are caught by the global error handler
and translated to safe HTTP responses.
"""

from fastapi import HTTPException, status


class ServiceUnavailableError(HTTPException):
    """Raised when an external service (Pinecone, OpenAI) is unreachable."""

    def __init__(self, service_name: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Servis geçici olarak erişilemiyor: {service_name}. Lütfen tekrar deneyin.",
        )


class SearchError(Exception):
    """Raised when Pinecone search fails."""

    def __init__(self, message: str = "Search operation failed"):
        self.message = message
        super().__init__(self.message)


class LLMError(Exception):
    """Raised when OpenAI API call fails."""

    def __init__(self, message: str = "LLM generation failed"):
        self.message = message
        super().__init__(self.message)


class PromptInjectionError(Exception):
    """Raised when prompt injection is detected."""

    def __init__(self, query_preview: str = ""):
        self.message = f"Prompt injection detected: {query_preview[:50]}..."
        super().__init__(self.message)
