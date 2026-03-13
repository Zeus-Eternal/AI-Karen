"""
Enhanced Response Formatting Models for CoPilot System

This module provides comprehensive type definitions and models for the response formatting
system with support for multiple output profiles, content types, and advanced formatting features.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
import json

try:
    from pydantic.v1 import BaseModel, Field, validator
except ImportError:
    try:
        from pydantic import BaseModel, Field, validator
    except ImportError:
        from ai_karen_engine.pydantic_stub import BaseModel, Field, validator


class OutputProfile(Enum):
    """Enhanced output profile enumeration with more options."""
    PLAIN = "plain"
    PRETTY = "pretty"
    DEV_DOC = "dev_doc"
    MINIMAL = "minimal"
    VERBOSE = "verbose"
    ACCESSIBLE = "accessible"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"


class LayoutType(Enum):
    """Enhanced layout type enumeration."""
    DEFAULT = "default"
    MENU = "menu"
    MOVIE_LIST = "movie_list"
    BULLET_LIST = "bullet_list"
    SYSTEM_STATUS = "system_status"
    CODE_BLOCK = "code_block"
    TABLE = "table"
    STEPS = "steps"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    TREE = "tree"
    GRID = "grid"
    ACCORDION = "accordion"
    TABS = "tabs"


class ContentType(Enum):
    """Content type enumeration for intelligent formatting."""
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
    """Display context for responsive formatting."""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    TERMINAL = "terminal"
    API = "api"
    PRINT = "print"
    EMBEDDED = "embedded"
    VOICE = "voice"


class ThemeMode(Enum):
    """Theme mode enumeration."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    HIGH_CONTRAST = "high_contrast"


class AccessibilityLevel(Enum):
    """Accessibility level enumeration."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL = "full"
    SCREEN_READER = "screen_reader"


class StreamingState(Enum):
    """Streaming state enumeration."""
    START = "start"
    CONTENT = "content"
    METADATA = "metadata"
    END = "end"
    ERROR = "error"


@dataclass
class LayoutHint:
    """Enhanced layout hint with more parameters."""
    layout_type: LayoutType
    confidence: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    content_type: Optional[ContentType] = None
    display_context: Optional[DisplayContext] = None
    accessibility_level: Optional[AccessibilityLevel] = None


@dataclass
class ResponseMetadata:
    """Comprehensive response metadata."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time: float = 0.0
    content_length: int = 0
    original_length: int = 0
    confidence_score: float = 0.0
    sources: List[str] = field(default_factory=list)
    model_used: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    formatting_applied: bool = True
    layout_confidence: float = 0.0
    content_type_detected: Optional[str] = None
    language_detected: Optional[str] = None
    theme_used: Optional[str] = None
    accessibility_features: List[str] = field(default_factory=list)
    interactive_elements: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormattingPreferences:
    """User formatting preferences."""
    output_profile: OutputProfile = OutputProfile.PRETTY
    theme_mode: ThemeMode = ThemeMode.AUTO
    accessibility_level: AccessibilityLevel = AccessibilityLevel.BASIC
    display_context: DisplayContext = DisplayContext.DESKTOP
    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    enable_syntax_highlighting: bool = True
    enable_interactive_elements: bool = True
    enable_animations: bool = True
    max_content_length: int = 10000
    custom_css_classes: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseContext:
    """Enhanced response context with comprehensive information."""
    user_query: str
    response_content: str
    user_preferences: FormattingPreferences = field(default_factory=FormattingPreferences)
    session_data: Dict[str, Any] = field(default_factory=dict)
    theme_context: Dict[str, Any] = field(default_factory=dict)
    detected_content_type: Optional[ContentType] = None
    confidence_score: float = 0.0
    display_context: DisplayContext = DisplayContext.DESKTOP
    accessibility_level: AccessibilityLevel = AccessibilityLevel.BASIC
    theme_mode: ThemeMode = ThemeMode.AUTO
    language: str = "en"
    is_streaming: bool = False
    stream_chunk_id: Optional[int] = None
    metadata: ResponseMetadata = field(default_factory=ResponseMetadata)


@dataclass
class FormattingConfig:
    """Enhanced configuration for response formatting."""
    output_profile: OutputProfile = OutputProfile.PRETTY
    default_layout: LayoutType = LayoutType.DEFAULT
    enable_markdown: bool = True
    enable_sections: bool = True
    enable_highlights: bool = True
    enable_syntax_highlighting: bool = True
    enable_interactive_elements: bool = True
    enable_responsive_formatting: bool = True
    enable_accessibility_features: bool = True
    enable_theme_support: bool = True
    max_content_length: int = 10000
    safe_mode: bool = True
    cache_enabled: bool = True
    performance_monitoring: bool = True
    custom_formatters: Dict[str, Any] = field(default_factory=dict)
    theme_configurations: Dict[str, Any] = field(default_factory=dict)
    accessibility_configurations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamingChunk:
    """Streaming response chunk with comprehensive metadata."""
    chunk_id: int
    content: str
    state: StreamingState
    metadata: ResponseMetadata = field(default_factory=ResponseMetadata)
    layout_hint: Optional[LayoutHint] = None
    formatting_applied: bool = False
    is_final_chunk: bool = False
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0


@dataclass
class SyntaxHighlightConfig:
    """Configuration for syntax highlighting."""
    language: str
    theme: str = "default"
    line_numbers: bool = True
    highlight_lines: List[int] = field(default_factory=list)
    wrap_lines: bool = True
    tab_size: int = 4
    show_whitespace: bool = False
    show_line_endings: bool = False


@dataclass
class TableFormattingConfig:
    """Configuration for table formatting."""
    headers: List[str]
    rows: List[List[str]]
    max_width: Optional[int] = None
    alignment: Optional[List[str]] = None  # 'left', 'center', 'right'
    header_style: str = "bold"
    border_style: str = "single"
    responsive: bool = True
    sortable: bool = False
    filterable: bool = False


@dataclass
class CodeBlockConfig:
    """Configuration for code block formatting."""
    language: str
    content: str
    line_numbers: bool = True
    syntax_highlighting: bool = True
    copy_button: bool = True
    execute_button: bool = False
    collapse_long_code: bool = True
    max_lines: int = 50
    show_file_path: bool = False
    file_path: Optional[str] = None


@dataclass
class AccessibilityConfig:
    """Configuration for accessibility features."""
    level: AccessibilityLevel = AccessibilityLevel.BASIC
    screen_reader_optimized: bool = False
    high_contrast: bool = False
    large_text: bool = False
    keyboard_navigation: bool = True
    aria_labels: bool = True
    alt_text: bool = True
    focus_indicators: bool = True
    skip_links: bool = True
    color_blind_friendly: bool = False


# Pydantic models for API requests/responses
class FormattingRequest:
    """Request model for formatting API."""
    content: str = Field(..., description="Content to format")
    output_profile: Optional[str] = Field(None, description="Output profile to use")
    layout_type: Optional[str] = Field(None, description="Layout type to force")
    display_context: Optional[str] = Field("desktop", description="Display context")
    theme_mode: Optional[str] = Field("auto", description="Theme mode")
    accessibility_level: Optional[str] = Field("basic", description="Accessibility level")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="Session data")
    
    @validator('output_profile')
    def validate_output_profile(cls, v):
        if v and v not in [p.value for p in OutputProfile]:
            raise ValueError(f"Invalid output profile: {v}")
        return v
    
    @validator('layout_type')
    def validate_layout_type(cls, v):
        if v and v not in [l.value for l in LayoutType]:
            raise ValueError(f"Invalid layout type: {v}")
        return v
    
    @validator('display_context')
    def validate_display_context(cls, v):
        if v not in [d.value for d in DisplayContext]:
            raise ValueError(f"Invalid display context: {v}")
        return v
    
    @validator('theme_mode')
    def validate_theme_mode(cls, v):
        if v not in [t.value for t in ThemeMode]:
            raise ValueError(f"Invalid theme mode: {v}")
        return v
    
    @validator('accessibility_level')
    def validate_accessibility_level(cls, v):
        if v not in [a.value for a in AccessibilityLevel]:
            raise ValueError(f"Invalid accessibility level: {v}")
        return v


class FormattingResponse:
    """Response model for formatting API."""
    formatted_content: str = Field(..., description="Formatted content")
    content_type: str = Field(..., description="Detected content type")
    layout_type: str = Field(..., description="Applied layout type")
    output_profile: str = Field(..., description="Used output profile")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    accessibility_features: List[str] = Field(default_factory=list, description="Accessibility features applied")
    interactive_elements: List[str] = Field(default_factory=list, description="Interactive elements included")
    theme_requirements: List[str] = Field(default_factory=list, description="Theme requirements")
    css_classes: List[str] = Field(default_factory=list, description="CSS classes applied")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence_score: float = Field(..., description="Confidence score for formatting decisions")


class StreamingFormattingRequest:
    """Request model for streaming formatting API."""
    content: str = Field(..., description="Content chunk to format")
    chunk_id: int = Field(..., description="Chunk sequence number")
    is_final: bool = Field(False, description="Whether this is the final chunk")
    formatting_context: Dict[str, Any] = Field(default_factory=dict, description="Formatting context")


class StreamingFormattingResponse:
    """Response model for streaming formatting API."""
    chunk_id: int = Field(..., description="Chunk sequence number")
    formatted_content: str = Field(..., description="Formatted chunk content")
    state: str = Field(..., description="Streaming state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    is_final: bool = Field(False, description="Whether this is the final chunk")
    progress: float = Field(0.0, description="Progress percentage (0.0-1.0)")


class ContentTypeDetectionRequest:
    """Request model for content type detection."""
    content: str = Field(..., description="Content to analyze")
    user_query: Optional[str] = Field(None, description="Original user query for context")
    context_hints: List[str] = Field(default_factory=list, description="Context hints for detection")


class ContentTypeDetectionResponse:
    """Response model for content type detection."""
    detected_type: str = Field(..., description="Detected content type")
    confidence: float = Field(..., description="Confidence score for detection")
    alternative_types: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative types with confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Detection metadata")


class UserProfileRequest:
    """Request model for user profile management."""
    user_id: str = Field(..., description="User ID")
    preferences: Dict[str, Any] = Field(..., description="User preferences")


class UserProfileResponse:
    """Response model for user profile management."""
    user_id: str = Field(..., description="User ID")
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Profile update timestamp")
    active_profile: str = Field(..., description="Active output profile")


# Utility functions for model conversion
def dict_to_output_profile(profile_dict: Dict[str, Any]) -> OutputProfile:
    """Convert dictionary to OutputProfile enum."""
    profile_value = profile_dict.get('value', profile_dict.get('profile', 'pretty'))
    try:
        return OutputProfile(profile_value)
    except ValueError:
        return OutputProfile.PRETTY


def dict_to_layout_type(layout_dict: Dict[str, Any]) -> LayoutType:
    """Convert dictionary to LayoutType enum."""
    layout_value = layout_dict.get('value', layout_dict.get('layout', 'default'))
    try:
        return LayoutType(layout_value)
    except ValueError:
        return LayoutType.DEFAULT


def dict_to_content_type(content_dict: Dict[str, Any]) -> ContentType:
    """Convert dictionary to ContentType enum."""
    content_value = content_dict.get('value', content_dict.get('type', 'text'))
    try:
        return ContentType(content_value)
    except ValueError:
        return ContentType.TEXT


def dict_to_display_context(context_dict: Dict[str, Any]) -> DisplayContext:
    """Convert dictionary to DisplayContext enum."""
    context_value = context_dict.get('value', context_dict.get('context', 'desktop'))
    try:
        return DisplayContext(context_value)
    except ValueError:
        return DisplayContext.DESKTOP


def dict_to_theme_mode(theme_dict: Dict[str, Any]) -> ThemeMode:
    """Convert dictionary to ThemeMode enum."""
    theme_value = theme_dict.get('value', theme_dict.get('theme', 'auto'))
    try:
        return ThemeMode(theme_value)
    except ValueError:
        return ThemeMode.AUTO


def dict_to_accessibility_level(accessibility_dict: Dict[str, Any]) -> AccessibilityLevel:
    """Convert dictionary to AccessibilityLevel enum."""
    accessibility_value = accessibility_dict.get('value', accessibility_dict.get('level', 'basic'))
    try:
        return AccessibilityLevel(accessibility_value)
    except ValueError:
        return AccessibilityLevel.BASIC


# Serialization utilities
def serialize_metadata(metadata: ResponseMetadata) -> Dict[str, Any]:
    """Serialize ResponseMetadata to dictionary."""
    return {
        "timestamp": metadata.timestamp.isoformat(),
        "processing_time": metadata.processing_time,
        "content_length": metadata.content_length,
        "original_length": metadata.original_length,
        "confidence_score": metadata.confidence_score,
        "sources": metadata.sources,
        "model_used": metadata.model_used,
        "user_id": metadata.user_id,
        "session_id": metadata.session_id,
        "formatting_applied": metadata.formatting_applied,
        "layout_confidence": metadata.layout_confidence,
        "content_type_detected": metadata.content_type_detected,
        "language_detected": metadata.language_detected,
        "theme_used": metadata.theme_used,
        "accessibility_features": metadata.accessibility_features,
        "interactive_elements": metadata.interactive_elements,
        "custom_metadata": metadata.custom_metadata
    }


def deserialize_metadata(data: Dict[str, Any]) -> ResponseMetadata:
    """Deserialize dictionary to ResponseMetadata."""
    timestamp = data.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    elif timestamp is None:
        timestamp = datetime.utcnow()
    
    return ResponseMetadata(
        timestamp=timestamp,
        processing_time=data.get("processing_time", 0.0),
        content_length=data.get("content_length", 0),
        original_length=data.get("original_length", 0),
        confidence_score=data.get("confidence_score", 0.0),
        sources=data.get("sources", []),
        model_used=data.get("model_used"),
        user_id=data.get("user_id"),
        session_id=data.get("session_id"),
        formatting_applied=data.get("formatting_applied", True),
        layout_confidence=data.get("layout_confidence", 0.0),
        content_type_detected=data.get("content_type_detected"),
        language_detected=data.get("language_detected"),
        theme_used=data.get("theme_used"),
        accessibility_features=data.get("accessibility_features", []),
        interactive_elements=data.get("interactive_elements", []),
        custom_metadata=data.get("custom_metadata", {})
    )