"""
Request Schemas — Pydantic models for incoming requests.

Validates and sanitizes all user input at the API boundary.
Uses field validators to strip whitespace, remove control
characters, and enforce length limits.
"""

from pydantic import BaseModel, Field, field_validator
import re


class ChatRequest(BaseModel):
    """Validated chat request from the Next.js frontend.

    Attributes:
        query: User's question (2-1000 characters after sanitization).
    """

    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="User's question (2-1000 chars)",
        examples=["Pepsi ürünleri nelerdir?"],
    )

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Clean and validate the query string.

        Steps:
          1. Strip leading/trailing whitespace
          2. Remove null bytes and control characters
          3. Collapse multiple spaces/newlines into single space
          4. Verify minimum length after sanitization
        """
        # 1. Strip whitespace
        v = v.strip()

        # 2. Remove null bytes and control characters
        v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)

        # 3. Collapse multiple spaces/newlines
        v = re.sub(r"\s+", " ", v)

        # 4. Check for emptiness after sanitization
        if not v or len(v) < 2:
            raise ValueError("Query is too short after sanitization.")

        return v
