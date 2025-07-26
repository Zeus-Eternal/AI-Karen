"""
Core infrastructure for AI Karen engine.

This module provides the foundational components for the AI Karen engine including:
- Service infrastructure and dependency injection
- Error handling and logging
- FastAPI gateway and middleware
"""

from ai_karen_engine.core.services import (
    BaseService, ServiceConfig, ServiceStatus, ServiceContainer, 
    ServiceRegistry, get_container, get_registry, inject, service
)
from ai_karen_engine.core.errors import (
    KarenError, ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, ServiceError, PluginError, MemoryError, AIProcessingError,
    ErrorHandler, ErrorResponse, ErrorCode, error_middleware
)
from ai_karen_engine.core.logging import (
    KarenLogger, get_logger, configure_logging, LogLevel, LogFormat,
    logging_middleware, StructuredFormatter, JSONFormatter
)
from ai_karen_engine.core.gateway import create_app, KarenApp, setup_middleware, setup_routing

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
    "setup_routing"
]

from ai_karen_engine.core.default_models import (
    load_default_models,
    get_embedding_manager,
    get_spacy_client,
    get_classifier,
)

__all__ += [
    "load_default_models",
    "get_embedding_manager",
    "get_spacy_client",
    "get_classifier",
]