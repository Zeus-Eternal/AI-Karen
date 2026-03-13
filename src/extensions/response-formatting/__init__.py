"""
Intelligent Response Formatting Plugin System

This extension provides intelligent response formatting based on content type and context.
It integrates with the existing extensions SDK and theme system to provide beautiful,
contextual formatting for different types of AI responses.
"""

from base import ResponseFormatter, FormattedResponse, ContentType
from registry import ResponseFormatterRegistry
from content_detector import ContentTypeDetector
from integration import ResponseFormattingIntegration

__version__ = "1.0.0"
__all__ = [
    "ResponseFormatter",
    "FormattedResponse", 
    "ContentType",
    "ResponseFormatterRegistry",
    "ContentTypeDetector",
    "ResponseFormattingIntegration"
]