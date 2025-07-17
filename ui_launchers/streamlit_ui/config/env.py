"""Helper utilities for environment-based configuration."""
from __future__ import annotations

import os
from pathlib import Path
from distutils.util import strtobool


def get_data_dir() -> str:
    """Return the directory for local UI data files."""
    return os.getenv("KARI_UI_DATA_DIR", str(Path(__file__).resolve().parents[1] / "data"))


def get_setting(name: str, default: str | None = None) -> str | None:
    """Fetch a string setting from the environment with optional default."""
    return os.getenv(name, default)


def get_bool_setting(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return bool(strtobool(value))
    except ValueError:
        return default


def get_int_setting(name: str, default: int | None = None) -> int | None:
    """Return an integer env var if set and valid."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "get_data_dir",
    "get_setting",
    "get_bool_setting",
    "get_int_setting",
]
