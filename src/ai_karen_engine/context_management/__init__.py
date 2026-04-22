"""
Context Management System for CoPilot

Provides comprehensive context persistence, file uploads, and context retrieval
for agent interactions with proper indexing, versioning, and access control.

This package is the persistent context domain. It owns stored contexts,
sharing, version history, file lifecycle, and search/scoring over saved
context records. Runtime orchestration should consume it through adapters,
not take ownership of it.
"""

from typing import TYPE_CHECKING

__all__ = [
    # Models
    "ContextEntry",
    "ContextFile",
    "ContextQuery",
    "ContextSearchResult",
    "ContextVersion",
    "ContextShare",
    "ContextAccessLog",
    "ContextType",
    "ContextFileType",
    "ContextAccessLevel",
    "ContextStatus",
    # Services
    "ContextManagementService",
    "FileUploadHandler",
    "ContextPreprocessor",
    "ContextRelevanceScorer",
]

_MODEL_EXPORTS = {
    "ContextEntry",
    "ContextFile",
    "ContextQuery",
    "ContextSearchResult",
    "ContextVersion",
    "ContextShare",
    "ContextAccessLog",
    "ContextType",
    "ContextFileType",
    "ContextAccessLevel",
    "ContextStatus",
}

_SERVICE_EXPORTS = {
    "ContextManagementService",
    "FileUploadHandler",
    "ContextPreprocessor",
    "ContextRelevanceScorer",
}

if TYPE_CHECKING:
    from .file_handler import FileUploadHandler
    from .models import (
        ContextAccessLevel,
        ContextAccessLog,
        ContextEntry,
        ContextFile,
        ContextFileType,
        ContextQuery,
        ContextSearchResult,
        ContextShare,
        ContextStatus,
        ContextType,
        ContextVersion,
    )
    from .preprocessor import ContextPreprocessor
    from .scoring import ContextRelevanceScorer
    from .service import ContextManagementService


def __getattr__(name: str):
    """Lazily expose context-management components to keep import surfaces narrow."""
    if name in _MODEL_EXPORTS:
        from . import models

        return getattr(models, name)

    if name == "ContextManagementService":
        from .service import ContextManagementService

        return ContextManagementService

    if name == "FileUploadHandler":
        from .file_handler import FileUploadHandler

        return FileUploadHandler

    if name == "ContextPreprocessor":
        from .preprocessor import ContextPreprocessor

        return ContextPreprocessor

    if name == "ContextRelevanceScorer":
        from .scoring import ContextRelevanceScorer

        return ContextRelevanceScorer

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Improve introspection for lazy exports."""
    return sorted(set(globals().keys()) | _MODEL_EXPORTS | _SERVICE_EXPORTS)
