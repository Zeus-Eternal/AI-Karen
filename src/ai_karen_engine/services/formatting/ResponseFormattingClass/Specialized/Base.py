"""
Base classes for specialized response formatters.
Migrated from extension system to core services.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..Models import FormattedResponse
from ..Enums import ContentType

@dataclass
class ResponseContext:
    """Context information for specialized response formatting."""
    user_query: str
    response_content: str
    user_preferences: Dict[str, Any]
    theme_context: Dict[str, Any]
    session_data: Dict[str, Any]
    detected_content_type: Optional[ContentType] = None
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_query": self.user_query,
            "response_content": self.response_content,
            "user_preferences": self.user_preferences,
            "theme_context": self.theme_context,
            "session_data": self.session_data,
            "detected_content_type": self.detected_content_type.value if self.detected_content_type else None,
            "confidence_score": self.confidence_score
        }

class SpecializedFormatter(ABC):
    """
    Abstract base class for specialized response formatters.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """Determine if this formatter can handle the given content."""
        pass
    
    @abstractmethod
    async def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """Format the response content according to this formatter's rules."""
        pass
    
    @abstractmethod
    def get_theme_requirements(self) -> List[str]:
        """Get the theme requirements for this formatter."""
        pass
    
    def get_supported_content_types(self) -> List[ContentType]:
        """Get the content types supported by this formatter."""
        return [ContentType.DEFAULT]
    
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """Get confidence score for formatting this content."""
        return 0.5 if self.can_format(content, context) else 0.0

class FormattingError(Exception):
    """Exception raised when specialized formatting fails."""
    def __init__(self, message: str, formatter_name: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.formatter_name = formatter_name
        self.original_error = original_error
