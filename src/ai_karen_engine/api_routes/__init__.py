"""Modular API route collection for Kari."""

try:
    from fastapi import APIRouter
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "FastAPI is required for API routes. Install via `pip install fastapi`."
    ) from e

router = APIRouter()
