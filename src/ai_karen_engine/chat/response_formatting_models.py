"""
Shared Models and Enums for Response Formatting.
This file is the single source of truth for models used by the formatting system.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

# Optional Pydantic integration
try:
    from pydantic.v1 import BaseModel, Field, validator
except ImportError:
    try:
        from pydantic import BaseModel, Field, validator
    except ImportError:
        class BaseModel: pass
        def Field(*args, **kwargs): return None
        def validator(*args, **kwargs): return lambda x: x

# --- Core Enums ---

class OutputProfile(Enum):
    PLAIN = "plain"
    PRETTY = "pretty"
    DEV_DOC = "dev_doc"
    MINIMAL = "minimal"
    VERBOSE = "verbose"
    ACCESSIBLE = "accessible"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"

class LayoutType(Enum):
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

class StreamingState(Enum):
    START = "start"
    CONTENT = "content"
    METADATA = "metadata"
    END = "end"
    ERROR = "error"

# --- Responsive Enums & Config ---

class ScreenSize(Enum):
    EXTRA_SMALL = "extra_small"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"

class DeviceType(Enum):
    PHONE = "phone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    TV = "tv"
    WEARABLE = "wearable"
    UNKNOWN = "unknown"

@dataclass
class ResponsiveBreakpoint:
    name: str
    min_width: int
    max_width: Optional[int] = None
    layout_adaptations: Dict[str, Any] = field(default_factory=dict)

# --- Service Configuration & User Preferences ---

@dataclass
class FormattingConfig:
    """Configuration for the internal formatting service."""
    output_profile: OutputProfile = OutputProfile.PRETTY
    default_layout: LayoutType = LayoutType.DEFAULT
    enable_markdown: bool = True
    enable_sections: bool = True
    enable_highlights: bool = True
    enable_syntax_highlighting: bool = True
    enable_responsive_formatting: bool = True
    enable_accessibility_features: bool = True
    enable_theme_support: bool = True
    max_content_length: int = 20000
    safe_mode: bool = True
    cache_enabled: bool = True
    performance_monitoring: bool = True

@dataclass
class FormattingPreferences:
    """User-provided preferences for a single request context."""
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

# --- Request/Response Models ---

class FormattingRequest(BaseModel):
    """Request model for formatting API."""
    content: str
    output_profile: Optional[str] = None
    layout_type: Optional[str] = None
    display_context: Optional[str] = "desktop"
    theme_mode: Optional[str] = "auto"
    accessibility_level: Optional[str] = "basic"
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    session_data: Dict[str, Any] = Field(default_factory=dict)

class FormattingResponse(BaseModel):
    """Response model for formatting API."""
    formatted_content: str
    content_type: str
    layout_type: str
    output_profile: str
    metadata: Dict[str, Any]
    accessibility_features: List[str] = Field(default_factory=list)
    interactive_elements: List[str] = Field(default_factory=list)
    theme_requirements: List[str] = Field(default_factory=list)
    css_classes: List[str] = Field(default_factory=list)
    processing_time: float
    confidence_score: float

class StreamingFormattingResponse(BaseModel):
    """Response model for streaming formatting API."""
    chunk_id: int
    formatted_content: str
    state: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_final: bool = False
    progress: float = 0.0

# --- Contextual Persistence ---

@dataclass
class LayoutHint:
    layout_type: LayoutType
    confidence: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResponseMetadata:
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time: float = 0.0
    content_length: int = 0
    original_length: int = 0
    confidence_score: float = 0.0
    routing_confidence: float = 0.0
    routing_rationale: Optional[str] = None
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
    error: Optional[str] = None

@dataclass
class ResponseContext:
    user_query: str
    response_content: str
    user_preferences: Union[Dict[str, Any], FormattingPreferences] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
    theme_context: Dict[str, Any] = field(default_factory=dict)
    detected_content_type: Optional[str] = None
    confidence_score: float = 0.0
    display_context: DisplayContext = DisplayContext.DESKTOP
    accessibility_level: AccessibilityLevel = AccessibilityLevel.BASIC
    theme_mode: ThemeMode = ThemeMode.AUTO
    language: str = "en"
    is_streaming: bool = False
    stream_chunk_id: Optional[int] = None
    metadata: Optional[ResponseMetadata] = None

@dataclass
class StreamingChunk:
    chunk_id: int
    content: str
    state: StreamingState
    metadata: Optional[ResponseMetadata] = None
    layout_hint: Optional[LayoutHint] = None
    formatting_applied: bool = False
    is_final_chunk: bool = False
    error_message: Optional[str] = None
    progress: float = 0.0

@dataclass
class FormattingResult:
    formatted_content: str
    content_type: ContentType
    layout_type: LayoutType
    output_profile: OutputProfile
    metadata: ResponseMetadata
    css_classes: List[str] = field(default_factory=list)
    accessibility_features: List[str] = field(default_factory=list)
    interactive_elements: List[str] = field(default_factory=list)
    theme_requirements: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    confidence_score: float = 0.0

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