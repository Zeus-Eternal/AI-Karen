"""
FastAPI dependency providers for extension services.

Provides singleton instances of all extension services for dependency injection.
"""

from functools import lru_cache
from typing import Optional

from ai_karen_engine.extensions.factory import (
    get_extension_manager as _get_extension_manager,
    get_extension_registry as _get_extension_registry,
    get_marketplace_client as _get_marketplace_client,
    get_extension_service_factory,
)


# Extension service dependencies
@lru_cache()
def get_extension_manager_dependency():
    """
    FastAPI dependency for ExtensionManager.

    Returns:
        ExtensionManager instance or None if unavailable
    """
    return _get_extension_manager()


@lru_cache()
def get_extension_registry_dependency():
    """
    FastAPI dependency for ExtensionRegistry.

    Returns:
        ExtensionRegistry instance or None if unavailable
    """
    return _get_extension_registry()


@lru_cache()
def get_marketplace_client_dependency():
    """
    FastAPI dependency for MarketplaceClient.

    Returns:
        MarketplaceClient instance or None if unavailable
    """
    return _get_marketplace_client()


# Factory dependency
@lru_cache()
def get_extension_factory_dependency():
    """
    FastAPI dependency for extension service factory.

    Returns:
        ExtensionServiceFactory instance
    """
    return get_extension_service_factory()


# Health check dependency
def get_extension_health_check():
    """
    FastAPI dependency for extension service health check.

    Returns:
        Dictionary of service health statuses
    """
    factory = get_extension_service_factory()
    return factory.health_check()


__all__ = [
    "get_extension_manager_dependency",
    "get_extension_registry_dependency",
    "get_marketplace_client_dependency",
    "get_extension_factory_dependency",
    "get_extension_health_check",
]
