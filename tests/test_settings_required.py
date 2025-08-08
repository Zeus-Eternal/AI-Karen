# mypy: ignore-errors
"""Tests for required configuration settings."""

import pytest
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class MiniSettings(BaseSettings):
    """Minimal settings model mirroring required fields."""

    secret_key: str = Field(..., env="SECRET_KEY")
    database_url: str = Field(..., env="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def test_missing_required_settings(monkeypatch):
    """Server startup should fail when mandatory settings are absent."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError) as exc:
        MiniSettings()
    message = str(exc.value)
    assert "database_url" in message
    assert "secret_key" in message
