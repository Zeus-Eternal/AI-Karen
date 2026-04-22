"""
Core service infrastructure for AI Karen engine.

This module provides base service classes, dependency injection framework,
and service lifecycle management.
"""

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus
from ai_karen_engine.core.services.container import ServiceContainer, inject, service, get_container
from ai_karen_engine.core.services.registry import (
    ServiceRegistry,
    ServiceMetadataRegistry,
    get_registry,
    get_metadata_registry,
)
from ai_karen_engine.core.services.service_registry import (
    ServiceRegistry as RuntimeServiceRegistry,
    get_service_registry,
    get_langgraph_orchestrator,
    get_memory_service,
    get_tool_service,
    initialize_services,
)
from ai_karen_engine.core.services.service_classification import (
    ServiceClassification,
    DeploymentMode,
    ServiceConfig as ClassifiedServiceConfig,
    ResourceRequirements,
    ServiceConfigurationLoader,
    DependencyGraphAnalyzer,
    ServiceConfigurationValidator,
)
from ai_karen_engine.core.services.classified_service_registry import (
    ClassifiedServiceRegistry,
    ClassifiedServiceInfo,
    ServiceLifecycleState,
    get_classified_registry,
)
from ai_karen_engine.core.services.service_lifecycle_manager import (
    ServiceLifecycleManager,
    StartupMode,
)

__all__ = [
    "BaseService",
    "ServiceConfig",
    "ServiceStatus",
    "ServiceContainer",
    "ServiceRegistry",
    "ServiceMetadataRegistry",
    "get_container",
    "get_registry",
    "get_metadata_registry",
    "inject",
    "service",
    "RuntimeServiceRegistry",
    "get_service_registry",
    "get_langgraph_orchestrator",
    "get_memory_service",
    "get_tool_service",
    "initialize_services",
    "ServiceClassification",
    "DeploymentMode",
    "ClassifiedServiceConfig",
    "ResourceRequirements",
    "ServiceConfigurationLoader",
    "DependencyGraphAnalyzer",
    "ServiceConfigurationValidator",
    "ClassifiedServiceRegistry",
    "ClassifiedServiceInfo",
    "ServiceLifecycleState",
    "get_classified_registry",
    "ServiceLifecycleManager",
    "StartupMode",
]
