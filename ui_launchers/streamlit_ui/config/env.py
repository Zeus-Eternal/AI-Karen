"""Helper utilities for environment-based configuration."""
from __future__ import annotations

import os
from pathlib import Path


def get_data_dir() -> str:
    """Return the directory for local UI data files."""
    return os.getenv("KARI_UI_DATA_DIR", str(Path(__file__).resolve().parents[1] / "data"))


def get_setting(name: str, default: str | None = None) -> str | None:
    """Fetch a string setting from the environment with optional default."""
    return os.getenv(name, default)


def get_bool_setting(name: str, default: bool = False) -> bool:
    """Return a boolean env var value supporting common truthy strings."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).lower() in {"1", "true", "yes", "y", "on"}


def get_int_setting(name: str, default: int = 0) -> int:
    """Return an integer env var value with fallback on parse error."""
    val = os.getenv(name)
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


__all__ = [
    "get_data_dir",
    "get_setting",
    "get_bool_setting",
    "get_int_setting",
]
