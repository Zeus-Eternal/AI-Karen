# mypy: ignore-errors
"""
Configuration management for Kari FastAPI Server.
Handles environment loading, settings validation, and sys.path setup.
"""

# Load environment variables first, before any other imports
from dotenv import load_dotenv
import os
import sys
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file and ensure critical variables are set
load_dotenv(dotenv_path=".env")

# Determine runtime environment early for safe defaults handling
RUNTIME_ENV = (
    os.getenv("ENVIRONMENT")
    or os.getenv("KARI_ENV")
    or os.getenv("ENV")
    or "development"
).lower()

# Ensure critical environment variables are set
# - In development/test: provide sensible defaults if missing
# - In production: do NOT inject insecure defaults; require explicit configuration
required_env_vars = {
    "KARI_DUCKDB_PASSWORD": "dev-duckdb-pass",
    "KARI_JOB_ENC_KEY": "MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo=",
    "KARI_JOB_SIGNING_KEY": "dev-job-key-456",
    "KARI_MODEL_SIGNING_KEY": "dev-signing-key-1234567890abcdef",
    "SECRET_KEY": "super-secret-key-change-me",
    "AUTH_SECRET_KEY": "your-super-secret-jwt-key-change-in-production",
    "DATABASE_URL": "postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen",
    "POSTGRES_URL": "postgresql+asyncpg://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen",
    "AUTH_DATABASE_URL": "postgresql+asyncpg://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen",
    # Provide a dev-friendly default with password to avoid AUTH warnings.
    # Override in your environment for real deployments.
    "REDIS_URL": "redis://:dev-redis-pass@localhost:6379/0"
}

if RUNTIME_ENV in {"development", "dev", "local", "test", "testing"}:
    for var_name, default_value in required_env_vars.items():
        if not os.getenv(var_name):
            os.environ[var_name] = default_value
else:
    _missing = [k for k in required_env_vars.keys() if not os.getenv(k)]
    if _missing:
        # Fail fast in production for missing critical secrets/connections
        raise RuntimeError(
            "Missing required environment variables in production: " + ", ".join(_missing)
        )

# Ensure src/ is on sys.path when running directly from repo root
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src_path = os.path.join(_repo_root, "src")
if os.path.isdir(_src_path) and _src_path not in sys.path:
    sys.path.insert(0, _src_path)


class Settings(BaseSettings):
    app_name: str = "Kari AI Server"
    environment: str = "development"
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # Long-lived token settings for API stability
    long_lived_token_expire_hours: int = 24  # 24 hours for long-lived tokens
    enable_long_lived_tokens: bool = True
    database_url: str = "postgresql://user:password@localhost:5432/kari_prod"
    kari_cors_origins: str = Field(
        default="http://localhost:8010,http://127.0.0.1:8010,http://localhost:8020,http://127.0.0.1:8020,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
        alias="cors_origins",
    )
    prometheus_enabled: bool = True
    https_redirect: bool = False
    rate_limit: str = "300/minute"
    debug: bool = Field(default=False, env="KARI_DEBUG_MODE")
    plugin_dir: str = "/app/plugins"
    llm_refresh_interval: int = 3600
    
    # Performance Optimization Settings
    enable_performance_optimization: bool = Field(default=True, env="ENABLE_PERFORMANCE_OPTIMIZATION")
    deployment_mode: str = Field(default="development", env="DEPLOYMENT_MODE")
    cpu_threshold: float = Field(default=80.0, env="CPU_THRESHOLD")
    memory_threshold: float = Field(default=85.0, env="MEMORY_THRESHOLD")
    response_time_threshold: float = Field(default=2.0, env="RESPONSE_TIME_THRESHOLD")
    enable_lazy_loading: bool = Field(default=True, env="ENABLE_LAZY_LOADING")
    enable_gpu_offloading: bool = Field(default=True, env="ENABLE_GPU_OFFLOADING")
    enable_service_consolidation: bool = Field(default=True, env="ENABLE_SERVICE_CONSOLIDATION")
    max_startup_time: float = Field(default=30.0, env="MAX_STARTUP_TIME")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # HTTP Request Validation Settings (Requirements 4.1, 4.2, 4.3, 4.4)
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    max_headers_count: int = Field(default=100, env="MAX_HEADERS_COUNT")
    max_header_size: int = Field(default=8192, env="MAX_HEADER_SIZE")
    enable_request_validation: bool = Field(default=True, env="ENABLE_REQUEST_VALIDATION")
    enable_security_analysis: bool = Field(default=True, env="ENABLE_SECURITY_ANALYSIS")
    log_invalid_requests: bool = Field(default=True, env="LOG_INVALID_REQUESTS")
    validation_rate_limit_per_minute: int = Field(default=100, env="VALIDATION_RATE_LIMIT_PER_MINUTE")
    
    # Security validation patterns (configurable)
    blocked_user_agents: str = Field(
        default="sqlmap,nikto,nmap,masscan,zap",
        env="BLOCKED_USER_AGENTS"
    )
    suspicious_headers: str = Field(
        default="x-forwarded-host,x-cluster-client-ip,x-real-ip",
        env="SUSPICIOUS_HEADERS"
    )
    
    # Protocol-level error handling settings
    max_invalid_requests_per_connection: int = Field(default=10, env="MAX_INVALID_REQUESTS_PER_CONNECTION")
    enable_protocol_error_handling: bool = Field(default=True, env="ENABLE_PROTOCOL_ERROR_HANDLING")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()