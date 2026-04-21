"""
Dependencies Compatibility Layer.

This module provides compatibility dependencies for services that were previously
in the chat directory. Since the original services were removed during demolition,
this provides basic functionality with warnings.
"""

from .code_execution_service import (
    get_code_execution_service,
    CodeExecutionService,
)
from .file_attachment_service import (
    get_file_attachment_service,
    FileAttachmentService,
    get_hook_enabled_file_service,
    HookEnabledFileService,
    get_multimedia_service,
    MultimediaService,
)
from .tool_service import get_tool_service

__all__ = [
    "get_code_execution_service",
    "CodeExecutionService",
    "get_file_attachment_service",
    "FileAttachmentService",
    "get_hook_enabled_file_service",
    "HookEnabledFileService",
    "get_multimedia_service",
    "MultimediaService",
    "get_tool_service",
]
