from __future__ import annotations

from fastapi import FastAPI

from ai_karen_engine.api_routes.monitoring.health import router as health_router


def register_health_endpoints(app: FastAPI) -> None:
    """Register health endpoints on the FastAPI app."""
    app.include_router(health_router)


__all__ = ["register_health_endpoints"]
