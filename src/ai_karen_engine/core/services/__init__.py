"""
Core service infrastructure for AI Karen engine.

This module provides base service classes, dependency injection framework,
and service lifecycle management.
"""

from .base import BaseService, ServiceConfig, ServiceStatus
from .container import ServiceContainer, inject, service, get_container
from .registry import ServiceRegistry, get_registry

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