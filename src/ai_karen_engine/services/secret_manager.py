"""Canonical secret manager service boundary."""

from ai_karen_engine.models.secret_manager import (  # noqa: F401
    SecretManager,
    get_secret_manager,
)

__all__ = ["SecretManager", "get_secret_manager"]

