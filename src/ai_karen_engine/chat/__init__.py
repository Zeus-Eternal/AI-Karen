"""
Chat module for AI Karen Engine.

This module provides chat-related functionality including conversation management,
message processing, and response formatting.
"""

from .response_formatter import (
    PrettyOutputLayer,
    FormattingConfig,
    SyntaxHighlightConfig,
    FormattingRequest,
    FormattingResponse,
    StreamingFormattingResponse
)

from .response_formatting_models import (
    OutputProfile,
    LayoutType,
    ContentType,
    DisplayContext,
    ThemeMode,
    AccessibilityLevel,
    StreamingState,
    LayoutHint,
    ResponseMetadata,
    FormattingPreferences,
    ResponseContext,
    StreamingChunk,
    FormattingResult
)

# Compatibility Mappings
EnhancedResponseFormatter = PrettyOutputLayer

def get_enhanced_response_formatter(*args, **kwargs):
    """Compatibility factory for EnhancedResponseFormatter."""
    return PrettyOutputLayer(*args, **kwargs)

__all__ = [
    "PrettyOutputLayer",
    "EnhancedResponseFormatter",
    "get_enhanced_response_formatter",
    "OutputProfile",
    "LayoutType",
    "ContentType",
    "DisplayContext",
    "ThemeMode",
    "AccessibilityLevel",
    "StreamingState",
    "LayoutHint",
    "ResponseMetadata",
    "FormattingPreferences",
    "ResponseContext",
    "StreamingChunk",
    "FormattingResult",
    "FormattingConfig",
    "SyntaxHighlightConfig",
    "FormattingRequest",
    "FormattingResponse",
    "StreamingFormattingResponse"
]
