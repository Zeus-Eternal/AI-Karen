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


__all__ = ["get_data_dir", "get_setting"]
