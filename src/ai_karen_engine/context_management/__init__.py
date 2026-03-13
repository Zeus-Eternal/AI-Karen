"""
Context Management System for CoPilot

Provides comprehensive context persistence, file uploads, and context retrieval
for agent interactions with proper indexing, versioning, and access control.
"""

from .models import (
    ContextEntry,
    ContextFile,
    ContextQuery,
    ContextSearchResult,
    ContextVersion,
    ContextShare,
    ContextAccessLog,
    ContextType,
    ContextFileType,
    ContextAccessLevel,
    ContextStatus,
)

from .service import ContextManagementService
from .file_handler import FileUploadHandler
from .preprocessor import ContextPreprocessor
from .scoring import ContextRelevanceScorer

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