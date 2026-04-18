"""
Base response formatter interface and core data models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Enumeration of supported content types for response formatting."""
    MOVIE = "movie"
    RECIPE = "recipe"
    WEATHER = "weather"
    NEWS = "news"
    PRODUCT = "product"
    TRAVEL = "travel"
    CODE = "code"
    DEFAULT = "default"


@dataclass
class FormattedResponse:
    """Container for formatted response data."""
    content: str
    content_type: ContentType
    theme_requirements: List[str]
    metadata: Dict[str, Any]
    css_classes: List[str]
    has_images: bool = False
    has_interactive_elements: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "content_type": self.content_type.value,
            "theme_requirements": self.theme_requirements,
            "metadata": self.metadata,
            "css_classes": self.css_classes,
            "has_images": self.has_images,
            "has_interactive_elements": self.has_interactive_elements
        }


@dataclass
class ResponseContext:
    """Context information for response formatting."""
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


class ResponseFormatter(ABC):
    """
    Abstract base class for response formatters.
    
    All response formatters must inherit from this class and implement
    the required methods. This ensures consistent behavior across all
    formatting plugins.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """
        Determine if this formatter can handle the given content.
        
        Args:
            content: The raw response content to format
            context: Additional context information
            
        Returns:
            True if this formatter can handle the content, False otherwise
        """
        pass
    
    @abstractmethod
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format the response content according to this formatter's rules.
        
        Args:
            content: The raw response content to format
            context: Additional context information
            
        Returns:
            FormattedResponse object containing the formatted content and metadata
            
        Raises:
            FormattingError: If formatting fails
        """
        pass
    
    @abstractmethod
    def get_theme_requirements(self) -> List[str]:
        """
        Get the theme requirements for this formatter.
        
        Returns:
            List of theme component names required by this formatter
        """
        pass
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get the content types supported by this formatter.
        
        Returns:
            List of ContentType enums this formatter supports
        """
        return [ContentType.DEFAULT]
    
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """
        Get confidence score for formatting this content.
        
        Args:
            content: The raw response content
            context: Additional context information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        return 0.5 if self.can_format(content, context) else 0.0
    
    def validate_content(self, content: str, context: ResponseContext) -> bool:
        """
        Validate that the content is safe and appropriate for formatting.
        
        Args:
            content: The raw response content
            context: Additional context information
            
        Returns:
            True if content is valid and safe, False otherwise
        """
        if not content or not content.strip():
            return False
        
        # Basic safety checks
        if len(content) > 100000:  # 100KB limit
            self.logger.warning(f"Content too large for formatting: {len(content)} chars")
            return False
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this formatter.
        
        Returns:
            Dictionary containing formatter metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "supported_content_types": [ct.value for ct in self.get_supported_content_types()],
            "theme_requirements": self.get_theme_requirements()
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}')"
    
    def __repr__(self) -> str:
        return self.__str__()


class FormattingError(Exception):
    """Exception raised when response formatting fails."""
    
    def __init__(self, message: str, formatter_name: str = None, original_error: Exception = None):
        self.formatter_name = formatter_name
        self.original_error = original_error
        super().__init__(message)
    
    def __str__(self) -> str:
        msg = super().__str__()
        if self.formatter_name:
            msg = f"[{self.formatter_name}] {msg}"
        if self.original_error:
            msg = f"{msg} (caused by: {self.original_error})"
        return msg


class DefaultResponseFormatter(ResponseFormatter):
    """
    Default response formatter that provides basic formatting.
    
    This formatter is used as a fallback when no specific formatter
    can handle the content.
    """
    
    def __init__(self):
        super().__init__("default", "1.0.0")
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """Default formatter can handle any content."""
        return self.validate_content(content, context)
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """Apply basic formatting to the content."""
        if not self.validate_content(content, context):
            raise FormattingError("Invalid content for default formatting", self.name)
        
        # Apply basic HTML formatting
        formatted_content = self._apply_basic_formatting(content)
        
        return FormattedResponse(
            content=formatted_content,
            content_type=ContentType.DEFAULT,
            theme_requirements=self.get_theme_requirements(),
            metadata={
                "formatter": self.name,
                "original_length": len(content),
                "formatted_length": len(formatted_content)
            },
            css_classes=["response-default", "formatted-response"]
        )
    
    def get_theme_requirements(self) -> List[str]:
        """Default formatter requires basic typography theme components."""
        return ["typography", "spacing", "colors"]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """Default formatter supports the default content type."""
        return [ContentType.DEFAULT]
    
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """Default formatter has low confidence - used as fallback."""
        return 0.1 if self.can_format(content, context) else 0.0
    
    def _apply_basic_formatting(self, content: str) -> str:
        """Apply basic HTML formatting to content."""
        # Convert line breaks to HTML
        formatted = content.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
        # Wrap in paragraph tags if not already wrapped
        if not formatted.startswith('<'):
            formatted = f'<p>{formatted}</p>'
        
        # Add basic styling classes
        formatted = f'<div class="response-content default-formatting">{formatted}</div>'
        
        return formatted