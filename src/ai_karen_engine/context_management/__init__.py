"""
Context Management System for CoPilot

Provides comprehensive context persistence, file uploads, and context retrieval
for agent interactions with proper indexing, versioning, and access control.
"""

from typing import Any

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


def __getattr__(name: str) -> Any:
    """Lazily expose context-management components to keep import surfaces narrow."""
    if name in {
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
    }:
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
