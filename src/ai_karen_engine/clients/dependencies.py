"""
FastAPI dependency providers for client services.

Provides singleton instances of all client services for dependency injection.
"""

from functools import lru_cache
from typing import Optional

from ai_karen_engine.clients.factory import (
    get_redis_client as _get_redis_client,
    get_postgres_client as _get_postgres_client,
    get_milvus_client as _get_milvus_client,
    get_nlp_service as _get_nlp_service,
    get_embedding_manager as _get_embedding_manager,
    get_client_service_factory,
)


# Database client dependencies
@lru_cache()
def get_redis_client_dependency():
    """
    FastAPI dependency for Redis client.

    Returns:
        RedisClient instance or None if unavailable
    """
    return _get_redis_client()


@lru_cache()
def get_postgres_client_dependency():
    """
    FastAPI dependency for Postgres client.

    Returns:
        PostgresClient instance or None if unavailable
    """
    return _get_postgres_client()


@lru_cache()
def get_milvus_client_dependency():
    """
    FastAPI dependency for Milvus vector database client.

    Returns:
        MilvusClient instance or None if unavailable
    """
    return _get_milvus_client()


# NLP and embedding dependencies
@lru_cache()
def get_nlp_service_dependency():
    """
    FastAPI dependency for NLP service.

    Returns:
        NLPService instance or None if unavailable
    """
    return _get_nlp_service()


@lru_cache()
def get_embedding_manager_dependency():
    """
    FastAPI dependency for embedding manager.

    Returns:
        EmbeddingManager instance or None if unavailable
    """
    return _get_embedding_manager()


# Factory dependency
@lru_cache()
def get_client_factory_dependency():
    """
    FastAPI dependency for client service factory.

    Returns:
        ClientServiceFactory instance
    """
    return get_client_service_factory()


# Health check dependency
def get_client_health_check():
    """
    FastAPI dependency for client service health check.

    Returns:
        Dictionary of service health statuses
    """
    factory = get_client_service_factory()
    return factory.health_check()


__all__ = [
    "get_redis_client_dependency",
    "get_postgres_client_dependency",
    "get_milvus_client_dependency",
    "get_nlp_service_dependency",
    "get_embedding_manager_dependency",
    "get_client_factory_dependency",
    "get_client_health_check",
]
