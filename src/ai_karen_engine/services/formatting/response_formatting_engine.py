"""Canonical public facade for response formatting.

This module is the public import surface for runtime formatting.
Implementation lives in `ai_karen_engine.services.formatting.ResponseFormattingClass`.
"""

from ai_karen_engine.services.formatting.ResponseFormattingClass import (
    ResponseFormattingEngine,
    DisplayContext,
    AccessibilityLevel,
    FormatType,
    ContentType,
    SectionType,
    ComplexityLevel,
    FormattingContext,
    NavigationAid,
    ContentSection,
    FormattedResponse,
    CodeBlockInfo,
    CitationInfo,
    AnalysisResult,
)

__all__ = [
    "ResponseFormattingEngine",
    "DisplayContext",
    "AccessibilityLevel",
    "FormatType",
    "ContentType",
    "SectionType",
    "ComplexityLevel",
    "FormattingContext",
    "NavigationAid",
    "ContentSection",
    "FormattedResponse",
    "CodeBlockInfo",
    "CitationInfo",
    "AnalysisResult",
]
