"""Modular API route collection for Kari."""

try:
    from fastapi import APIRouter
except Exception:  # pragma: no cover - fallback for minimal envs
    from ai_karen_engine.fastapi_stub import APIRouter

router = APIRouter()
