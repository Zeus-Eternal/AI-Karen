# mypy: ignore-errors
"""
Middleware configuration wrapper for Kari FastAPI Server.
Provides a thin shim that re-exports configure_middleware from ai_karen_engine.server.middleware.
"""

from ai_karen_engine.server.middleware import configure_middleware

# Re-export the configure_middleware function to maintain compatibility
__all__ = ["configure_middleware"]