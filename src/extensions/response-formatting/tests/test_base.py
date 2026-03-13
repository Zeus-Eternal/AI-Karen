"""
Unit tests for base response formatter functionality.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import (
    ResponseFormatter,
    FormattedResponse,
    ResponseContext,
    ContentType,
    DefaultResponseFormatter,
    FormattingError
)


class TestResponseFormatter:
    """Test the abstract ResponseFormatter base class."""
    
    def test_abstract_methods_raise_not_implemented(self):
        """Test that abstract methods raise NotImplementedError."""
        
        class IncompleteFormatter(ResponseFormatter):
            pass
        
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            IncompleteFormatter("test")
    
    def test_concrete_implementation_works(self):
        """Test that a complete implementation works correctly."""
        
        class TestFormatter(ResponseFormatter):
            def can_format(self, content: str, context: ResponseContext) -> bool:
                return "test" in content.lower()
            
            def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
                return FormattedResponse(
                    content=f"<div>{content}</div>",
                    content_type=ContentType.DEFAULT,
                    theme_requirements=["test"],
                    metadata={"formatter": self.name},
                    css_classes=["test-class"]
                )
            
            def get_theme_requirements(self) -> List[str]:
                return ["test"]
        
        formatter = TestFormatter("test-formatter", "1.0.0")
        
        assert formatter.name == "test-formatter"
        assert formatter.version == "1.0.0"
        assert formatter.get_supported_content_types() == [ContentType.DEFAULT]
    
    def test_validate_content(self):
        """Test content validation."""
        
        class TestFormatter(ResponseFormatter):
            def can_format(self, content: str, context: ResponseContext) -> bool:
                return True
            
            def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
                return FormattedResponse(
                    content=content,
                    content_type=ContentType.DEFAULT,
                    theme_requirements=[],
                    metadata={},
                    css_classes=[]
                )
            
            def get_theme_requirements(self) -> List[str]:
                return []
        
        formatter = TestFormatter("test")
        context = ResponseContext(
            user_query="test",
            response_content="test",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        # Valid content
        assert formatter.validate_content("Valid content", context) is True
        
        # Empty content
        assert formatter.validate_content("", context) is False
        assert formatter.validate_content("   ", context) is False
        
        # Too large content
        large_content = "x" * 100001
        assert formatter.validate_content(large_content, context) is False
    
    def test_get_confidence_score(self):
        """Test confidence score calculation."""
        
        class TestFormatter(ResponseFormatter):
            def can_format(self, content: str, context: ResponseContext) -> bool:
                return "test" in content.lower()
            
            def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
                return FormattedResponse(
                    content=content,
                    content_type=ContentType.DEFAULT,
                    theme_requirements=[],
                    metadata={},
                    css_classes=[]
                )
            
            def get_theme_requirements(self) -> List[str]:
                return []
        
        formatter = TestFormatter("test")
        context = ResponseContext(
            user_query="test query",
            response_content="test response",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        # Should return 0.5 for content it can format
        assert formatter.get_confidence_score("test content", context) == 0.5
        
        # Should return 0.0 for content it cannot format
        assert formatter.get_confidence_score("other content", context) == 0.0
    
    def test_get_metadata(self):
        """Test metadata generation."""
        
        class TestFormatter(ResponseFormatter):
            def can_format(self, content: str, context: ResponseContext) -> bool:
                return True
            
            def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
                return FormattedResponse(
                    content=content,
                    content_type=ContentType.MOVIE,
                    theme_requirements=["movie"],
                    metadata={},
                    css_classes=[]
                )
            
            def get_theme_requirements(self) -> List[str]:
                return ["movie"]
            
            def get_supported_content_types(self) -> List[ContentType]:
                return [ContentType.MOVIE]
        
        formatter = TestFormatter("movie-formatter", "2.0.0")
        metadata = formatter.get_metadata()
        
        assert metadata["name"] == "movie-formatter"
        assert metadata["version"] == "2.0.0"
        assert metadata["supported_content_types"] == ["movie"]
        assert metadata["theme_requirements"] == ["movie"]


class TestDefaultResponseFormatter:
    """Test the default response formatter."""
    
    def test_initialization(self):
        """Test default formatter initialization."""
        formatter = DefaultResponseFormatter()
        
        assert formatter.name == "default"
        assert formatter.version == "1.0.0"
        assert formatter.get_supported_content_types() == [ContentType.DEFAULT]
        assert formatter.get_theme_requirements() == ["typography", "spacing", "colors"]
    
    def test_can_format(self):
        """Test can_format method."""
        formatter = DefaultResponseFormatter()
        context = ResponseContext(
            user_query="test",
            response_content="test",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        # Should handle valid content
        assert formatter.can_format("Valid content", context) is True
        
        # Should reject invalid content
        assert formatter.can_format("", context) is False
        assert formatter.can_format("   ", context) is False
    
    def test_format_response(self):
        """Test response formatting."""
        formatter = DefaultResponseFormatter()
        context = ResponseContext(
            user_query="test query",
            response_content="test response",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        content = "This is a test response.\n\nWith multiple paragraphs."
        result = formatter.format_response(content, context)
        
        assert isinstance(result, FormattedResponse)
        assert result.content_type == ContentType.DEFAULT
        assert "response-content" in result.content
        assert "default-formatting" in result.content
        assert "response-default" in result.css_classes
        assert "formatted-response" in result.css_classes
        assert result.metadata["formatter"] == "default"
        assert result.metadata["original_length"] == len(content)
    
    def test_format_response_invalid_content(self):
        """Test formatting with invalid content."""
        formatter = DefaultResponseFormatter()
        context = ResponseContext(
            user_query="test",
            response_content="",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        with pytest.raises(FormattingError) as exc_info:
            formatter.format_response("", context)
        
        assert "Invalid content" in str(exc_info.value)
        assert exc_info.value.formatter_name == "default"
    
    def test_get_confidence_score(self):
        """Test confidence score for default formatter."""
        formatter = DefaultResponseFormatter()
        context = ResponseContext(
            user_query="test",
            response_content="test",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        # Should have low confidence (fallback formatter)
        assert formatter.get_confidence_score("Valid content", context) == 0.1
        assert formatter.get_confidence_score("", context) == 0.0
    
    def test_apply_basic_formatting(self):
        """Test basic HTML formatting."""
        formatter = DefaultResponseFormatter()
        
        # Test paragraph formatting
        content = "Line 1\n\nLine 2\nLine 3"
        result = formatter._apply_basic_formatting(content)
        
        assert "<p>" in result
        assert "</p>" in result
        assert "<br>" in result
        assert "response-content" in result
        assert "default-formatting" in result


class TestFormattedResponse:
    """Test the FormattedResponse data class."""
    
    def test_initialization(self):
        """Test FormattedResponse initialization."""
        response = FormattedResponse(
            content="<div>Test</div>",
            content_type=ContentType.MOVIE,
            theme_requirements=["movie"],
            metadata={"test": "value"},
            css_classes=["movie-card"]
        )
        
        assert response.content == "<div>Test</div>"
        assert response.content_type == ContentType.MOVIE
        assert response.theme_requirements == ["movie"]
        assert response.metadata == {"test": "value"}
        assert response.css_classes == ["movie-card"]
        assert response.has_images is False
        assert response.has_interactive_elements is False
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        response = FormattedResponse(
            content="<div>Test</div>",
            content_type=ContentType.RECIPE,
            theme_requirements=["recipe"],
            metadata={"ingredients": 5},
            css_classes=["recipe-card"],
            has_images=True,
            has_interactive_elements=True
        )
        
        result = response.to_dict()
        
        assert result["content"] == "<div>Test</div>"
        assert result["content_type"] == "recipe"
        assert result["theme_requirements"] == ["recipe"]
        assert result["metadata"] == {"ingredients": 5}
        assert result["css_classes"] == ["recipe-card"]
        assert result["has_images"] is True
        assert result["has_interactive_elements"] is True


class TestResponseContext:
    """Test the ResponseContext data class."""
    
    def test_initialization(self):
        """Test ResponseContext initialization."""
        context = ResponseContext(
            user_query="What's the weather?",
            response_content="It's sunny today",
            user_preferences={"theme": "light"},
            theme_context={"current": "light"},
            session_data={"user_id": "123"}
        )
        
        assert context.user_query == "What's the weather?"
        assert context.response_content == "It's sunny today"
        assert context.user_preferences == {"theme": "light"}
        assert context.theme_context == {"current": "light"}
        assert context.session_data == {"user_id": "123"}
        assert context.detected_content_type is None
        assert context.confidence_score == 0.0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        context = ResponseContext(
            user_query="Recipe for pasta",
            response_content="Here's a pasta recipe",
            user_preferences={},
            theme_context={},
            session_data={},
            detected_content_type=ContentType.RECIPE,
            confidence_score=0.8
        )
        
        result = context.to_dict()
        
        assert result["user_query"] == "Recipe for pasta"
        assert result["response_content"] == "Here's a pasta recipe"
        assert result["detected_content_type"] == "recipe"
        assert result["confidence_score"] == 0.8


class TestFormattingError:
    """Test the FormattingError exception."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        error = FormattingError("Test error")
        
        assert str(error) == "Test error"
        assert error.formatter_name is None
        assert error.original_error is None
    
    def test_error_with_formatter_name(self):
        """Test error with formatter name."""
        error = FormattingError("Test error", formatter_name="test-formatter")
        
        assert str(error) == "[test-formatter] Test error"
        assert error.formatter_name == "test-formatter"
    
    def test_error_with_original_error(self):
        """Test error with original exception."""
        original = ValueError("Original error")
        error = FormattingError("Test error", original_error=original)
        
        assert "Test error" in str(error)
        assert "Original error" in str(error)
        assert error.original_error == original
    
    def test_error_with_all_fields(self):
        """Test error with all fields."""
        original = ValueError("Original error")
        error = FormattingError(
            "Test error", 
            formatter_name="test-formatter",
            original_error=original
        )
        
        error_str = str(error)
        assert "[test-formatter]" in error_str
        assert "Test error" in error_str
        assert "Original error" in error_str