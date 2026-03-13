"""
Chat module for AI Karen Engine.

This module provides chat-related functionality including conversation management,
message processing, and response formatting.
"""

from .response_formatter import (
    PrettyOutputLayer,
    OutputProfile,
    LayoutType,
    LayoutHint,
    ResponseContext,
    FormattingConfig
)
from .response_formatter_integration import ResponseFormatterAdapter
try:
    from .enhanced_response_formatter import (
        EnhancedResponseFormatter,
        FormattingResult,
        get_enhanced_response_formatter
    )
    from .response_formatting_models import (
        ContentType,
        DisplayContext,
        ThemeMode,
        AccessibilityLevel,
        ResponseMetadata,
        StreamingChunk,
        FormattingPreferences
    )
except ImportError:
    # Fallback for circular dependency
    from enum import Enum
    
    # Create minimal fallback classes
    class ContentType(Enum):
        TEXT = "text"
        CODE = "code"
        MARKDOWN = "markdown"
        JSON = "json"
        XML = "xml"
        YAML = "yaml"
        SQL = "sql"
        HTML = "html"
        CSS = "css"
        JAVASCRIPT = "javascript"
        PYTHON = "python"
        DATA_TABLE = "data_table"
        LIST = "list"
        MENU = "menu"
        STEPS = "steps"
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"
        SUCCESS = "success"
    
    class DisplayContext(Enum):
        DESKTOP = "desktop"
        MOBILE = "mobile"
        TABLET = "tablet"
        TERMINAL = "terminal"
        API = "api"
        PRINT = "print"
        EMBEDDED = "embedded"
        VOICE = "voice"
    
    class ThemeMode(Enum):
        LIGHT = "light"
        DARK = "dark"
        AUTO = "auto"
        HIGH_CONTRAST = "high_contrast"
    
    class AccessibilityLevel(Enum):
        BASIC = "basic"
        ENHANCED = "enhanced"
        FULL = "full"
        SCREEN_READER = "screen_reader"
    
    class ResponseMetadata:
        def __init__(self, timestamp=None, processing_time=0.0, content_length=0,
                     original_length=0, confidence_score=0.0, sources=None, model_used=None,
                     user_id=None, session_id=None, formatting_applied=True,
                     layout_confidence=0.0, content_type_detected=None,
                     language_detected=None, theme_used=None,
                     accessibility_features=None, interactive_elements=None,
                     custom_metadata=None, error_message=None):
            self.timestamp = timestamp
            self.processing_time = processing_time
            self.content_length = content_length
            self.original_length = original_length
            self.confidence_score = confidence_score
            self.sources = sources or []
            self.model_used = model_used
            self.user_id = user_id
            self.session_id = session_id
            self.formatting_applied = formatting_applied
            self.layout_confidence = layout_confidence
            self.content_type_detected = content_type_detected
            self.language_detected = language_detected
            self.theme_used = theme_used
            self.accessibility_features = accessibility_features or []
            self.interactive_elements = interactive_elements or []
            self.custom_metadata = custom_metadata or {}
            self.error_message = error_message
    
    class StreamingChunk:
        def __init__(self, chunk_id, content, state, metadata=None, layout_hint=None,
                     formatting_applied=False, is_final_chunk=False, error_message=None,
                     progress=0.0):
            self.chunk_id = chunk_id
            self.content = content
            self.state = state
            self.metadata = metadata or ResponseMetadata()
            self.layout_hint = layout_hint
            self.formatting_applied = formatting_applied
            self.is_final_chunk = is_final_chunk
            self.error_message = error_message
            self.progress = progress
    
    class FormattingPreferences:
        def __init__(self, output_profile=None, theme_mode=None,
                     accessibility_level=None, display_context=None, language="en", timezone="UTC",
                     date_format="%Y-%m-%d %H:%M:%S",
                     enable_syntax_highlighting=True, enable_interactive_elements=True,
                     enable_animations=True, max_content_length=10000, custom_css_classes=None,
                     custom_settings=None):
            self.output_profile = output_profile
            self.theme_mode = theme_mode
            self.accessibility_level = accessibility_level
            self.display_context = display_context
            self.language = language
            self.timezone = timezone
            self.date_format = date_format
            self.enable_syntax_highlighting = enable_syntax_highlighting
            self.enable_interactive_elements = enable_interactive_elements
            self.enable_animations = enable_animations
            self.max_content_length = max_content_length
            self.custom_css_classes = custom_css_classes or []
            self.custom_settings = custom_settings or {}

__all__ = [
    "PrettyOutputLayer",
    "OutputProfile",
    "LayoutType",
    "LayoutHint",
    "ResponseContext",
    "FormattingConfig",
    "ResponseFormatterAdapter",
    "EnhancedResponseFormatter",
    "FormattingResult",
    "get_enhanced_response_formatter",
    "ContentType",
    "DisplayContext",
    "ThemeMode",
    "AccessibilityLevel",
    "ResponseMetadata",
    "StreamingChunk",
    "FormattingPreferences"
]
