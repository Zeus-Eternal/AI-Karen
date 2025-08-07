"""Configuration models for authentication services."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Optional, Union, Dict, Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - yaml is optional
    yaml = None


def _env_bool(value: Optional[str], default: bool) -> bool:
    """Convert environment string to boolean with a default."""

    if value is None:
        return default
    return value.lower() in {"1", "true", "yes"}


def _load_env_file(file_path: Union[str, Path]) -> None:
    """Simple .env file parser that updates os.environ."""

    for line in Path(file_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass
class JWTConfig:
    """JWT related settings."""

    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expiry: timedelta = timedelta(minutes=15)
    refresh_token_expiry: timedelta = timedelta(days=7)
    password_reset_token_expiry: timedelta = timedelta(hours=1)

    @classmethod
    def from_env(cls) -> "JWTConfig":
        """Create configuration from environment variables."""

        defaults = cls()
        access_minutes = int(
            os.getenv(
                "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
                str(int(defaults.access_token_expiry.total_seconds() // 60)),
            )
        )
        refresh_days = int(
            os.getenv(
                "AUTH_REFRESH_TOKEN_EXPIRE_DAYS",
                str(int(defaults.refresh_token_expiry.total_seconds() // 86400)),
            )
        )
        reset_hours = int(
            os.getenv(
                "AUTH_PASSWORD_RESET_TOKEN_EXPIRE_HOURS",
                str(int(defaults.password_reset_token_expiry.total_seconds() // 3600)),
            )
        )
        return cls(
            secret_key=os.getenv("AUTH_SECRET_KEY", defaults.secret_key),
            algorithm=os.getenv("AUTH_ALGORITHM", defaults.algorithm),
            access_token_expiry=timedelta(minutes=access_minutes),
            refresh_token_expiry=timedelta(days=refresh_days),
            password_reset_token_expiry=timedelta(hours=reset_hours),
        )


@dataclass
class SessionConfig:
    """Session management settings."""

    session_timeout: timedelta = timedelta(hours=1)
    cookie_name: str = "session"
    storage_backend: str = "memory"
    redis_url: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SessionConfig":
        """Create configuration from environment variables."""

        defaults = cls()
        timeout_seconds = int(
            os.getenv(
                "AUTH_SESSION_TIMEOUT_SECONDS",
                str(int(defaults.session_timeout.total_seconds())),
            )
        )
        return cls(
            session_timeout=timedelta(seconds=timeout_seconds),
            cookie_name=os.getenv("AUTH_SESSION_COOKIE_NAME", defaults.cookie_name),
            storage_backend=os.getenv("AUTH_SESSION_BACKEND", defaults.storage_backend),
            redis_url=os.getenv(
                "AUTH_SESSION_REDIS_URL",
                os.getenv("REDIS_URL", defaults.redis_url or ""),
            )
            or None,
        )


@dataclass
class FeatureToggles:
    """Feature switches for authentication behaviour."""

    use_database: bool = False
    enable_intelligent_checks: bool = False
    enable_refresh_tokens: bool = True
    enable_rate_limiter: bool = False
    enable_audit_logging: bool = False

    @classmethod
    def from_env(cls) -> "FeatureToggles":
        """Create feature toggles from environment variables."""

        defaults = cls()
        return cls(
            use_database=_env_bool(
                os.getenv("AUTH_USE_DATABASE"), defaults.use_database
            ),
            enable_intelligent_checks=_env_bool(
                os.getenv("AUTH_ENABLE_INTELLIGENT_CHECKS"),
                defaults.enable_intelligent_checks,
            ),
            enable_refresh_tokens=_env_bool(
                os.getenv("AUTH_ENABLE_REFRESH_TOKENS"),
                defaults.enable_refresh_tokens,
            ),
            enable_rate_limiter=_env_bool(
                os.getenv("AUTH_ENABLE_RATE_LIMITER"),
                defaults.enable_rate_limiter,
            ),
            enable_audit_logging=_env_bool(
                os.getenv("AUTH_ENABLE_AUDIT_LOGGING"),
                defaults.enable_audit_logging,
            ),
        )


@dataclass
class RateLimiterConfig:
    """Rate limiter settings."""

    max_calls: int = 5
    period_seconds: int = 60

    @classmethod
    def from_env(cls) -> "RateLimiterConfig":
        defaults = cls()
        return cls(
            max_calls=int(
                os.getenv("AUTH_RATE_LIMIT_MAX_CALLS", str(defaults.max_calls))
            ),
            period_seconds=int(
                os.getenv(
                    "AUTH_RATE_LIMIT_PERIOD_SECONDS",
                    str(defaults.period_seconds),
                )
            ),
        )


@dataclass
class AuthConfig:
    """Top level authentication configuration grouping settings."""

    jwt: JWTConfig = field(default_factory=JWTConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    features: FeatureToggles = field(default_factory=FeatureToggles)
    rate_limiter: RateLimiterConfig = field(default_factory=RateLimiterConfig)

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Create configuration using environment variables."""

        return cls(
            jwt=JWTConfig.from_env(),
            session=SessionConfig.from_env(),
            features=FeatureToggles.from_env(),
            rate_limiter=RateLimiterConfig.from_env(),
        )

    @classmethod
    def _from_mapping(cls, data: Dict[str, Any]) -> "AuthConfig":
        """Create configuration from a mapping structure."""

        jwt_data = data.get("jwt", {})
        session_data = data.get("session", {})
        feature_data = data.get("features", {})
        rate_data = data.get("rate_limiter", {})

        jwt_cfg = JWTConfig(
            secret_key=jwt_data.get("secret_key", JWTConfig().secret_key),
            algorithm=jwt_data.get("algorithm", JWTConfig().algorithm),
            access_token_expiry=timedelta(
                minutes=jwt_data.get(
                    "access_token_expiry_minutes",
                    int(JWTConfig().access_token_expiry.total_seconds() // 60),
                )
            ),
            refresh_token_expiry=timedelta(
                days=jwt_data.get(
                    "refresh_token_expiry_days",
                    int(JWTConfig().refresh_token_expiry.total_seconds() // 86400),
                )
            ),
            password_reset_token_expiry=timedelta(
                hours=jwt_data.get(
                    "password_reset_token_expiry_hours",
                    int(
                        JWTConfig().password_reset_token_expiry.total_seconds()
                        // 3600
                    ),
                )
            ),
        )

        session_cfg = SessionConfig(
            session_timeout=timedelta(
                seconds=session_data.get(
                    "session_timeout_seconds",
                    int(SessionConfig().session_timeout.total_seconds()),
                )
            ),
            cookie_name=session_data.get("cookie_name", SessionConfig().cookie_name),
            storage_backend=session_data.get(
                "storage_backend", SessionConfig().storage_backend
            ),
            redis_url=session_data.get(
                "redis_url", SessionConfig().redis_url
            ),
        )

        feature_cfg = FeatureToggles(
            use_database=feature_data.get(
                "use_database", FeatureToggles().use_database
            ),
            enable_intelligent_checks=feature_data.get(
                "enable_intelligent_checks",
                FeatureToggles().enable_intelligent_checks,
            ),
            enable_refresh_tokens=feature_data.get(
                "enable_refresh_tokens", FeatureToggles().enable_refresh_tokens
            ),
            enable_rate_limiter=feature_data.get(
                "enable_rate_limiter", FeatureToggles().enable_rate_limiter
            ),
            enable_audit_logging=feature_data.get(
                "enable_audit_logging", FeatureToggles().enable_audit_logging
            ),
        )

        rate_cfg = RateLimiterConfig(
            max_calls=rate_data.get("max_calls", RateLimiterConfig().max_calls),
            period_seconds=rate_data.get(
                "period_seconds", RateLimiterConfig().period_seconds
            ),
        )

        return cls(
            jwt=jwt_cfg,
            session=session_cfg,
            features=feature_cfg,
            rate_limiter=rate_cfg,
        )

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "AuthConfig":
        """Load configuration from a JSON or YAML file."""

        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".json":
            data = json.loads(path.read_text() or "{}")
        elif suffix in {".yaml", ".yml"}:
            if yaml is None:
                raise ValueError("PyYAML is required to load YAML configuration")
            data = yaml.safe_load(path.read_text()) or {}
        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")

        return cls._from_mapping(data)

    @classmethod
    def from_env_file(cls, file_path: Union[str, Path]) -> "AuthConfig":
        """Load configuration from a .env file."""

        _load_env_file(file_path)
        return cls.from_env()

    def validate(self) -> None:
        """Validate mandatory settings and raise clear errors."""

        errors = []
        if not self.jwt.secret_key or self.jwt.secret_key == "change-me":
            errors.append("AUTH_SECRET_KEY must be set")

        if self.session.storage_backend == "redis" and not self.session.redis_url:
            errors.append(
                "AUTH_SESSION_REDIS_URL required when storage_backend='redis'"
            )

        if errors:
            raise ValueError("Invalid authentication configuration: " + "; ".join(errors))

    @classmethod
    def load(
        cls,
        file_path: Optional[Union[str, Path]] = None,
        env: Optional[str] = None,
    ) -> "AuthConfig":
        """Load configuration from .env, JSON, YAML, or environment variables."""

        path: Optional[Path] = None
        if file_path:
            path = Path(file_path)
        else:
            env = env or os.getenv("APP_ENV") or os.getenv("ENV")
            candidates = []
            if env:
                candidates = [
                    Path(f".env.{env}"),
                    Path(f"auth_config.{env}.json"),
                    Path(f"auth_config.{env}.yaml"),
                    Path(f"auth_config.{env}.yml"),
                ]
            else:
                candidates = [
                    Path(".env"),
                    Path("auth_config.json"),
                    Path("auth_config.yaml"),
                    Path("auth_config.yml"),
                ]
            path = next((p for p in candidates if p.exists()), None)

        if path and path.exists():
            if path.suffix.lower() == ".env":
                config = cls.from_env_file(path)
            else:
                config = cls.from_file(path)
        else:
            config = cls.from_env()

        config.validate()
        return config
