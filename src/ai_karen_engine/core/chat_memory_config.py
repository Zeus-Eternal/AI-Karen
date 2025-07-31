# src/ai_karen_engine/core/chat_memory_config.py

"""
Chat Memory & Auth Configuration
- Unified Redis hot storage + vector-DB memory settings
- Production authentication settings (JWT, rate limits, etc.)
- Loads from `.env` by default, ignores any extra vars
"""

from __future__ import annotations

from pathlib import Path

try:
    # Pydantic v2
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict

    V2 = True
except ImportError:
    # Pydantic v1 fallback
    from pydantic import BaseSettings, Field

    V2 = False

# Optional: load .env at import time if python-dotenv is present
# so that environment variables are populated for BaseSettings
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class ChatMemorySettings(BaseSettings):
    """Configuration for chat memory (Redis + vector DB)"""

    # Redis (hot) settings
    short_term_days: int = Field(1, description="Keep full turns for this many days")
    tail_turns: int = Field(3, description="Keep these many last turns hot")

    # Vector DB (long‐term) settings
    long_term_days: int = Field(30, description="How long to keep vectors (days)")

    # Summarization
    summarize_threshold_tokens: int = Field(
        3000, description="Token threshold to trigger summary"
    )
    max_summary_length: int = Field(
        300, description="Max length of generated summary (tokens)"
    )

    # Performance
    batch_size: int = Field(10, description="Batch size for vector ops")
    cache_ttl_seconds: int = Field(300, description="Cache TTL (seconds)")

    if V2:
        model_config = SettingsConfigDict(
            env_prefix="CHAT_MEMORY_",
            extra="ignore",
        )
    else:

        class Config:
            env_prefix = "CHAT_MEMORY_"
            extra = "ignore"


class ProductionAuthSettings(BaseSettings):
    """Production authentication config (JWT, sessions, rate limits)"""

    # Database & Redis URLs
    database_url: str = Field(
        "postgresql://karen_user:karen_secure_pass_change_me@postgres:5432/ai_karen",
        env=["POSTGRES_URL", "DATABASE_URL"],
    )
    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")

    # JWT / security
    secret_key: str = Field("changeme", description="JWT secret key (override!)")
    algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(30, description="Access token TTL (min)")
    refresh_token_expire_days: int = Field(7, description="Refresh token TTL (days)")

    # Password hashing
    password_hash_rounds: int = Field(12, description="Bcrypt rounds")

    # Session management
    session_expire_hours: int = Field(24, description="Session expiry (hours)")
    max_sessions_per_user: int = Field(5, description="Concurrent sessions/user")

    # Rate limiting
    login_rate_limit: int = Field(5, description="Login attempts per minute")
    api_rate_limit: int = Field(100, description="API requests per minute")

    if V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )
    else:

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            extra = "ignore"


class ProductionSettings(BaseSettings):
    """Main production settings"""

    # Core
    environment: str = Field("production", description="Environment name")
    debug: bool = Field(False, description="Enable debug logging")

    # DB & Redis
    database_url: str = Field(
        "postgresql://karen_user:karen_secure_pass_change_me@postgres:5432/ai_karen",
        env=["POSTGRES_URL", "DATABASE_URL"],
    )
    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")

    # Vector DB / Milvus
    vector_index_name: str = Field(
        "karen_chat_memory", description="Milvus/Vectordb index name"
    )
    milvus_host: str = Field("localhost", description="Milvus host")
    milvus_port: int = Field(19530, description="Milvus port")

    # Authentication
    auth: ProductionAuthSettings = ProductionAuthSettings()

    # Chat memory
    chat_memory: ChatMemorySettings = ChatMemorySettings()

    # Logging
    log_level: str = Field("INFO", description="Global log level")
    log_format: str = Field("json", description="Log format")

    if V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )
    else:

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            extra = "ignore"


# Single, global settings instance
settings = ProductionSettings()
