"""Lightweight server package exports with lazy loading.

Historically this module eagerly imported a large collection of server
utilities so that downstream modules could access them via
``ai_karen_engine.server``. Those imports pulled in heavy dependencies
including NLP pipelines and database clients during application start-up,
which made simple tasks—like instantiating a FastAPI test client—very
slow or even caused timeouts when optional models (spaCy, transformers)
were missing.

To keep import-time side effects minimal we now expose the same public
symbols via on-demand imports. This keeps compatibility with existing
``from ai_karen_engine.server import <Symbol>`` statements while avoiding
the expensive initialization until a symbol is actually used.
"""

from importlib import import_module
from typing import Any, Dict

__all__ = [
    "HTTPRequestValidator",
    "ValidationConfig",
    "ValidationResult",
    "EnhancedLogger",
    "LoggingConfig",
    "SecurityEvent",
    "SecurityEventType",
    "ThreatLevel",
    "DataSanitizer",
    "SecurityAlertManager",
    "get_enhanced_logger",
    "init_enhanced_logging",
]

_LAZY_IMPORTS: Dict[str, str] = {
    "HTTPRequestValidator": "ai_karen_engine.server.http_validator",
    "ValidationConfig": "ai_karen_engine.server.http_validator",
    "ValidationResult": "ai_karen_engine.server.http_validator",
    "EnhancedLogger": "ai_karen_engine.server.enhanced_logger",
    "LoggingConfig": "ai_karen_engine.server.enhanced_logger",
    "SecurityEvent": "ai_karen_engine.server.enhanced_logger",
    "SecurityEventType": "ai_karen_engine.server.enhanced_logger",
    "ThreatLevel": "ai_karen_engine.server.enhanced_logger",
    "DataSanitizer": "ai_karen_engine.server.enhanced_logger",
    "SecurityAlertManager": "ai_karen_engine.server.enhanced_logger",
    "get_enhanced_logger": "ai_karen_engine.server.enhanced_logger",
    "init_enhanced_logging": "ai_karen_engine.server.enhanced_logger",
}


def __getattr__(name: str) -> Any:
    """Load server utilities lazily on first access.

    This prevents heavyweight optional dependencies from being imported
    unless the caller explicitly uses the associated functionality.
    """

    module_path = _LAZY_IMPORTS.get(name)
    if not module_path:
        raise AttributeError(name)

    module = import_module(module_path)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> Any:  # pragma: no cover - trivial helper
    return sorted(set(__all__ + list(globals().keys())))
