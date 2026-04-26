from __future__ import annotations

from fastapi import FastAPI

from ai_karen_engine.api_routes.admin.admin import router as admin_router


def register_admin_endpoints(app: FastAPI, settings=None) -> None:
    """Register admin endpoints on the FastAPI app."""
    app.include_router(admin_router)


__all__ = ["register_admin_endpoints"]
