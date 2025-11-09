"""
FastAPI dependency providers for database services.

Provides singleton instances of all database services for dependency injection.
"""

from functools import lru_cache
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.database.factory import (
    get_database_client as _get_database_client,
    get_conversation_manager as _get_conversation_manager,
    get_memory_manager as _get_memory_manager,
    get_tenant_manager as _get_tenant_manager,
    get_database_service_factory,
)


# Database client dependencies
@lru_cache()
def get_database_client_dependency():
    """
    FastAPI dependency for database client.

    Returns:
        MultiTenantPostgresClient or DatabaseClient instance
    """
    return _get_database_client()


# Manager dependencies
@lru_cache()
def get_conversation_manager_dependency():
    """
    FastAPI dependency for conversation manager.

    Returns:
        ConversationManager instance or None if unavailable
    """
    return _get_conversation_manager()


@lru_cache()
def get_memory_manager_dependency():
    """
    FastAPI dependency for memory manager.

    Returns:
        MemoryManager instance or None if unavailable
    """
    return _get_memory_manager()


@lru_cache()
def get_tenant_manager_dependency():
    """
    FastAPI dependency for tenant manager.

    Returns:
        TenantManager instance or None if unavailable
    """
    return _get_tenant_manager()


# Factory dependency
@lru_cache()
def get_database_factory_dependency():
    """
    FastAPI dependency for database service factory.

    Returns:
        DatabaseServiceFactory instance
    """
    return get_database_service_factory()


# Session dependencies
def get_db_session() -> Session:
    """
    FastAPI dependency for synchronous database session.

    Yields:
        SQLAlchemy Session instance

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    db_client = _get_database_client()
    if not db_client:
        raise RuntimeError("Database client not initialized")

    session = db_client.get_session()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database session.

    Yields:
        AsyncSession instance

    Usage:
        async with get_async_db_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    db_client = _get_database_client()
    if not db_client:
        raise RuntimeError("Database client not initialized")

    async with db_client.get_async_session() as session:
        yield session


def get_async_db_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database session.

    Yields:
        AsyncSession instance

    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_async_db_session_dependency)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    db_client = _get_database_client()
    if not db_client:
        raise RuntimeError("Database client not initialized")

    return db_client.get_async_session()


# Health check dependency
def get_database_health_check():
    """
    FastAPI dependency for database health check.

    Returns:
        Dictionary of database service health statuses

    Usage:
        @app.get("/health/database")
        def database_health(health: dict = Depends(get_database_health_check)):
            return health
    """
    factory = get_database_service_factory()
    return factory.health_check()


# Tenant context dependency
def get_current_tenant_id(tenant_id: Optional[str] = None) -> str:
    """
    FastAPI dependency for extracting tenant ID from request context.

    Args:
        tenant_id: Optional tenant ID from request (header, query, etc.)

    Returns:
        Tenant ID string

    Raises:
        HTTPException: If tenant_id is missing

    Usage:
        @app.get("/tenant-data")
        def get_tenant_data(
            tenant_id: str = Depends(get_current_tenant_id),
            db: Session = Depends(get_db_session)
        ):
            return db.query(TenantData).filter_by(tenant_id=tenant_id).all()
    """
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    return tenant_id


# Transaction management dependency
class DatabaseTransaction:
    """
    Context manager for database transactions in FastAPI routes.

    Usage:
        @app.post("/items")
        def create_item(
            item: Item,
            transaction: DatabaseTransaction = Depends()
        ):
            with transaction.session() as session:
                session.add(item)
                session.commit()
                return item
    """

    def __init__(self):
        self.db_client = _get_database_client()
        if not self.db_client:
            raise RuntimeError("Database client not initialized")

    def session(self):
        """Get a transactional session context manager."""
        return self.db_client.session_scope()

    async def async_session(self):
        """Get an async transactional session context manager."""
        return self.db_client.get_async_session()


def get_database_transaction() -> DatabaseTransaction:
    """
    FastAPI dependency for database transaction management.

    Returns:
        DatabaseTransaction instance

    Usage:
        @app.post("/items")
        def create_item(
            item: Item,
            transaction: DatabaseTransaction = Depends(get_database_transaction)
        ):
            with transaction.session() as session:
                session.add(item)
                session.commit()
                return item
    """
    return DatabaseTransaction()


__all__ = [
    # Client dependencies
    "get_database_client_dependency",
    # Manager dependencies
    "get_conversation_manager_dependency",
    "get_memory_manager_dependency",
    "get_tenant_manager_dependency",
    # Factory dependency
    "get_database_factory_dependency",
    # Session dependencies
    "get_db_session",
    "get_async_db_session",
    "get_async_db_session_dependency",
    # Health check
    "get_database_health_check",
    # Tenant context
    "get_current_tenant_id",
    # Transaction management
    "DatabaseTransaction",
    "get_database_transaction",
]
