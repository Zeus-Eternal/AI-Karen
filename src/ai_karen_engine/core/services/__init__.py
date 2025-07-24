"""
Core service infrastructure for AI Karen engine.

This module provides base service classes, dependency injection framework,
and service lifecycle management.
"""

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus
from ai_karen_engine.core.services.container import ServiceContainer, inject, service, get_container
from ai_karen_engine.core.services.registry import ServiceRegistry, get_registry

__all__ = [
    "BaseService",
    "ServiceConfig", 
    "ServiceStatus",
    "ServiceContainer",
    "ServiceRegistry",
    "get_container",
    "get_registry",
    "inject",
    "service"
]
