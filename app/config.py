"""
Pydantic Settings — Secure environment variable loading.

All configuration is loaded from environment variables.
Pydantic will raise a validation error at startup if any required
variable is missing, preventing the app from starting in a
misconfigured state.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- API Keys (Required) ---
    openai_api_key: str
    pinecone_api_key: str

    # --- Application ---
    app_name: str = "Gelisim Chatbot API"
    debug: bool = False

    # --- Security ---
    api_key_header: str = "X-API-Key"
    api_keys: list[str] = []  # Keys your Next.js frontend uses

    # --- CORS ---
    allowed_origins: list[str] = ["http://localhost:3000"]

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Budget Limits (Denial of Wallet protection) ---
    ip_daily_limit: int = 200        # Max requests per IP per day
    global_daily_limit: int = 2000   # Max total requests per day

    # --- Pinecone ---
    pinecone_index_name: str = "gelisim-bot-index"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings — loaded once at startup."""
    return Settings()
