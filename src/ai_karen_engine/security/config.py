from __future__ import annotations

"""Configuration models for authentication services."""

from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class JWTConfig:
    """JWT related settings."""

    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expiry: timedelta = timedelta(minutes=15)
    refresh_token_expiry: timedelta = timedelta(days=7)


@dataclass
class SessionConfig:
    """Session management settings."""

    session_timeout: timedelta = timedelta(hours=1)
    cookie_name: str = "session"


@dataclass
class FeatureToggles:
    """Feature switches for authentication behaviour."""

    use_database: bool = False
    enable_intelligent_checks: bool = False
    enable_refresh_tokens: bool = True
    enable_rate_limiter: bool = False
    enable_audit_logging: bool = False


@dataclass
class AuthConfig:
    """Top level authentication configuration grouping settings."""

    jwt: JWTConfig = field(default_factory=JWTConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    features: FeatureToggles = field(default_factory=FeatureToggles)

