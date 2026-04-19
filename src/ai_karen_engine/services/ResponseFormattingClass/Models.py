from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .Enums import (
    AccessibilityLevel,
    ComplexityLevel,
    ContentType,
    DisplayContext,
    FormatType,
    SectionType,
)


class FormattingContext(BaseModel):
    display_context: DisplayContext = DisplayContext.DESKTOP
    accessibility_level: AccessibilityLevel = AccessibilityLevel.BASIC
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    content_length: int = 0
    technical_level: str = "intermediate"
    language: str = "en"
    request_type: str = "general"
    is_streaming: bool = False
    prefer_compact_output: bool = False
    prefer_source_panel: bool = False
    prefer_navigation_panel: bool = False


class NavigationAid(BaseModel):
    label: str
    target_id: str
    level: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentSection(BaseModel):
    content: str
    section_type: SectionType
    priority: int = 50
    format_hint: Optional[FormatType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    navigation_id: Optional[str] = None
    accessibility_text: Optional[str] = None


class FormattedResponse(BaseModel):
    content: str
    format_type: FormatType
    sections: List[ContentSection] = Field(default_factory=list)
    navigation_aids: List[NavigationAid] = Field(default_factory=list)
    accessibility_features: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    estimated_reading_time: Optional[int] = None
    preferred_renderer: str = "markdown"
    render_blocks_available: bool = True
    source_panel_recommended: bool = False
    navigation_panel_recommended: bool = False


@dataclass
class CodeBlockInfo:
    language: str
    code: str
    start: int
    end: int
    line_count: int = 0
    is_fenced: bool = True
    highlightable: bool = True


@dataclass
class CitationInfo:
    title: str
    url: str
    snippet: str = ""
    domain: str = ""
    source_type: str = "web"


@dataclass
class AnalysisResult:
    content_type: ContentType
    complexity: ComplexityLevel
    sections: List[ContentSection]
    code_blocks: List[CodeBlockInfo]
    data_structures: List[str]
    length: int
    reading_time: int
    technical_density: float
    citations: List[CitationInfo] = field(default_factory=list)
    has_tables: bool = False
    has_lists: bool = False
    has_headers: bool = False
    has_inline_code: bool = False
    is_long_form: bool = False