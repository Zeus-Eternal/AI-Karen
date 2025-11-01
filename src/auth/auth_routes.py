"""Re-export production authentication API routes."""

from ai_karen_engine.api_routes.production_auth_routes import router  # noqa: F401

__all__ = ["router"]
