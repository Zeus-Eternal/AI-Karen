"""
Core infrastructure for AI Karen engine.

This module provides the foundational components for the AI Karen engine including:
- Service infrastructure and dependency injection
- Error handling and logging
- FastAPI gateway and middleware
"""

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

from ai_karen_engine.core.default_models import (  # type: ignore
    get_classifier,
    get_embedding_manager,
    get_spacy_client,
    load_default_models,
)

__all__ += [
    "load_default_models",
    "get_embedding_manager",
    "get_spacy_client",
    "get_classifier",
]
