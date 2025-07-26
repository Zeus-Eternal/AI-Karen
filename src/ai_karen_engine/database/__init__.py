"""Database package for AI-Karen multi-tenant architecture."""

from ai_karen_engine.database.models import (
    Base,
    Tenant,
    User,
    TenantConversation,
    TenantMemoryEntry,
)
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.migrations import MigrationManager

_default_client: Optional[MultiTenantPostgresClient] = None
_import_error: Optional[Exception] = None


def _get_default_client() -> MultiTenantPostgresClient:
    """Lazily initialize and return the default database client."""
    global _default_client, _import_error

    if _default_client is None:
        try:
            _default_client = MultiTenantPostgresClient()
        except Exception as exc:  # pragma: no cover - optional dependency issues
            _import_error = exc
            raise

    return _default_client


@asynccontextmanager
async def get_postgres_session() -> AsyncGenerator:
    """Yield an asynchronous Postgres session from the default client."""
    try:
        client = _get_default_client()
    except Exception as exc:
        raise ImportError(
            "Postgres session cannot be created due to missing dependencies"
        ) from exc

    async with client.get_async_session() as session:
        yield session

__all__ = [
    "Base",
    "Tenant", 
    "User",
    "TenantConversation",
    "TenantMemoryEntry",
    "MultiTenantPostgresClient",
    "MigrationManager",
    "get_postgres_session",
]
