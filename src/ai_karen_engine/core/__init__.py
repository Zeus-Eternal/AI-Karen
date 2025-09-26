"""
Core infrastructure for AI Karen engine.

This module provides the foundational components for the AI Karen engine including:
- Service infrastructure and dependency injection
- Error handling and logging
- FastAPI gateway and middleware
"""

# mypy: ignore-errors

from ai_karen_engine.core.errors import (  # type: ignore
    AIProcessingError,
    AuthenticationError,
    AuthorizationError,
    ErrorCode,
    ErrorHandler,
    ErrorResponse,
    KarenError,
    MemoryError,
    NotFoundError,
    PluginError,
    ServiceError,
    ValidationError,
    error_middleware,
)
from ai_karen_engine.core.gateway import (  # type: ignore
    KarenApp,
    create_app,
    setup_middleware,
    setup_routing,
)
from ai_karen_engine.core.logging import (  # type: ignore
    JSONFormatter,
    KarenLogger,
    LogFormat,
    LogLevel,
    StructuredFormatter,
    configure_logging,
    get_logger,
    logging_middleware,
)
from ai_karen_engine.core.services import (  # type: ignore
    BaseService,
    ServiceConfig,
    ServiceContainer,
    ServiceRegistry,
    ServiceStatus,
    get_container,
    get_registry,
    inject,
    service,
)

# Service Classification System
from ai_karen_engine.core.service_classification import (  # type: ignore
    ServiceClassification,
    DeploymentMode,
    ServiceConfig as ClassifiedServiceConfig,
    ResourceRequirements,
    ServiceConfigurationLoader,
    DependencyGraphAnalyzer,
    ServiceConfigurationValidator,
)

# Note: ClassifiedServiceRegistry import moved to avoid circular dependencies
# Import it directly when needed: from ai_karen_engine.core.classified_service_registry import ClassifiedServiceRegistry

__all__ = [
    # Services
    "BaseService",
    "ServiceConfig",
    "ServiceStatus",
    "ServiceContainer",
    "ServiceRegistry",
    "get_container",
    "get_registry",
    "inject",
    "service",
    # Service Classification
    "ServiceClassification",
    "DeploymentMode",
    "ClassifiedServiceConfig",
    "ResourceRequirements",
    "ServiceConfigurationLoader",
    "DependencyGraphAnalyzer",
    "ServiceConfigurationValidator",
    # "ClassifiedServiceRegistry",  # Import directly to avoid circular dependencies
    # "ServiceLifecycleState",
    # "ClassifiedServiceInfo",
    # Errors
    "KarenError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ServiceError",
    "PluginError",
    "MemoryError",
    "AIProcessingError",
    "ErrorHandler",
    "ErrorResponse",
    "ErrorCode",
    "error_middleware",
    # Logging
    "KarenLogger",
    "get_logger",
    "configure_logging",
    "LogLevel",
    "LogFormat",
    "logging_middleware",
    "StructuredFormatter",
    "JSONFormatter",
    # Gateway
    "create_app",
    "KarenApp",
    "setup_middleware",
    "setup_routing",
]

_LAZY_IMPORTS = {
    "load_default_models": "ai_karen_engine.core.default_models",
    "get_embedding_manager": "ai_karen_engine.core.default_models",
    "get_spacy_client": "ai_karen_engine.core.default_models",
    "get_classifier": "ai_karen_engine.core.default_models",
    "generate_degraded_mode_response": "ai_karen_engine.core.degraded_mode",
    "HealthChecker": "ai_karen_engine.core.health_checker",
    "ProviderStatus": "ai_karen_engine.core.health_checker",
    "build_response_envelope": "ai_karen_engine.core.response_envelope",
}

__all__ += list(_LAZY_IMPORTS.keys())


def __getattr__(name):
    """Lazily import heavy core modules on first access.

    Some core helpers pull in large dependency graphs (e.g. NLP services and
    database layers). Importing them eagerly causes circular import problems
    when low-level infrastructure modules – such as the database client – are
    imported early during application start-up.  By deferring these imports
    until they are actually needed we keep the public API unchanged while
    avoiding import-time recursion.
    """

    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        attr = getattr(module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(name)
