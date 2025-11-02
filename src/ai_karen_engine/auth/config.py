"""Compatibility authentication configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class JWTConfig:
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60


@dataclass
class AuthConfig:
    jwt: JWTConfig = field(default_factory=JWTConfig)

    @classmethod
    def from_env(cls, overrides: Dict[str, Any] | None = None) -> "AuthConfig":
        config = cls()
        if overrides:
            for key, value in overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        return config


__all__ = ["AuthConfig", "JWTConfig"]
