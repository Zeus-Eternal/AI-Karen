"""
Unit tests for response formatter registry.
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
from registry import (
    ResponseFormatterRegistry,
    get_formatter_registry,
    reset_formatter_registry
)


class MockFormatter(ResponseFormatter):
    """Mock formatter for testing."""
    
    def __init__(self, name: str, content_types: List[ContentType] = None, confidence: float = 0.8):
        super().__init__(name, "1.0.0")
        self._content_types = content_types or [ContentType.DEFAULT]
        self._confidence = confidence
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        return "mock" in content.lower()
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        return FormattedResponse(
            content=f"<div class='mock'>{content}</div>",
            content_type=self._content_types[0],
            theme_requirements=["mock"],
            metadata={"formatter": self.name},
            css_classes=["mock-formatted"]
        )
    
    def get_theme_requirements(self) -> List[str]:
        return ["mock"]
    
    def get_supported_content_types(self) -> List[ContentType]:
        return self._content_types
    
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        return self._confidence if self.can_format(content, context) else 0.0


class TestResponseFormatterRegistry:
    """Test the response formatter registry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ResponseFormatterRegistry()
    
    def test_initialization(self):
        """Test registry initialization."""
        assert len(self.registry._formatters) == 1  # Default formatter
        assert "default" in self.registry._formatters
        assert isinstance(self.registry._default_formatter, DefaultResponseFormatter)
    
    def test_register_formatter(self):
        """Test formatter registration."""
        formatter = MockFormatter("test-formatter")
        
        self.registry.register_formatter(formatter)
        
        assert "test-formatter" in self.registry._formatters
        assert self.registry._formatters["test-formatter"] == formatter
        assert ContentType.DEFAULT in self.registry._formatters_by_type
        assert formatter in self.registry._formatters_by_type[ContentType.DEFAULT]
    
    def test_register_formatter_invalid_type(self):
        """Test registering invalid formatter type."""
        with pytest.raises(ValueError) as exc_info:
            self.registry.register_formatter("not a formatter")
        
        assert "must be an instance of ResponseFormatter" in str(exc_info.value)
    
    def test_register_formatter_replace_existing(self):
        """Test replacing existing formatter."""
        formatter1 = MockFormatter("test-formatter")
        formatter2 = MockFormatter("test-formatter")
        
        self.registry.register_formatter(formatter1)
        assert self.registry._formatters["test-formatter"] == formatter1
        
        # Should replace existing
        self.registry.register_formatter(formatter2)
        assert self.registry._formatters["test-formatter"] == formatter2
    
    def test_unregister_formatter(self):
        """Test formatter unregistration."""
        formatter = MockFormatter("test-formatter")
        self.registry.register_formatter(formatter)
        
        # Should unregister successfully
        result = self.registry.unregister_formatter("test-formatter")
        assert result is True
        assert "test-formatter" not in self.registry._formatters
    
    def test_unregister_nonexistent_formatter(self):
        """Test unregistering non-existent formatter."""
        result = self.registry.unregister_formatter("nonexistent")
        assert result is False
    
    def test_unregister_default_formatter(self):
        """Test that default formatter cannot be unregistered."""
        result = self.registry.unregister_formatter("default")
        assert result is False
        assert "default" in self.registry._formatters
    
    def test_get_formatter(self):
        """Test getting formatter by name."""
        formatter = MockFormatter("test-formatter")
        self.registry.register_formatter(formatter)
        
        retrieved = self.registry.get_formatter("test-formatter")
        assert retrieved == formatter
        
        # Non-existent formatter
        assert self.registry.get_formatter("nonexistent") is None
    
    def test_get_formatters_for_content_type(self):
        """Test getting formatters by content type."""
        movie_formatter = MockFormatter("movie", [ContentType.MOVIE])
        recipe_formatter = MockFormatter("recipe", [ContentType.RECIPE])
        
        self.registry.register_formatter(movie_formatter)
        self.registry.register_formatter(recipe_formatter)
        
        movie_formatters = self.registry.get_formatters_for_content_type(ContentType.MOVIE)
        assert movie_formatter in movie_formatters
        assert recipe_formatter not in movie_formatters
        
        recipe_formatters = self.registry.get_formatters_for_content_type(ContentType.RECIPE)
        assert recipe_formatter in recipe_formatters
        assert movie_formatter not in recipe_formatters
    
    def test_find_best_formatter(self):
        """Test finding the best formatter."""
        low_confidence = MockFormatter("low", confidence=0.3)
        high_confidence = MockFormatter("high", confidence=0.9)
        
        self.registry.register_formatter(low_confidence)
        self.registry.register_formatter(high_confidence)
        
        context = ResponseContext(
            user_query="test",
            response_content="mock content",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        best = self.registry.find_best_formatter("mock content", context)
        assert best == high_confidence
    
    def test_find_best_formatter_with_detected_type(self):
        """Test finding formatter with detected content type."""
        movie_formatter = MockFormatter("movie", [ContentType.MOVIE], 0.8)
        default_formatter = MockFormatter("default", [ContentType.DEFAULT], 0.9)
        
        self.registry.register_formatter(movie_formatter)
        self.registry.register_formatter(default_formatter)
        
        context = ResponseContext(
            user_query="test",
            response_content="mock content",
            user_preferences={},
            theme_context={},
            session_data={},
            detected_content_type=ContentType.MOVIE
        )
        
        # Should prioritize movie formatter even with lower confidence
        best = self.registry.find_best_formatter("mock content", context)
        assert best == movie_formatter
    
    def test_find_best_formatter_fallback_to_default(self):
        """Test fallback to default formatter."""
        context = ResponseContext(
            user_query="test",
            response_content="no matching content",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        best = self.registry.find_best_formatter("no matching content", context)
        assert best == self.registry._default_formatter
    
    def test_format_response(self):
        """Test formatting response."""
        formatter = MockFormatter("test-formatter")
        self.registry.register_formatter(formatter)
        
        context = ResponseContext(
            user_query="test",
            response_content="mock content",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        result = self.registry.format_response("mock content", context)
        
        assert isinstance(result, FormattedResponse)
        assert "mock" in result.content
        assert result.metadata["formatter"] == "test-formatter"
    
    def test_format_response_fallback_on_error(self):
        """Test fallback to default formatter on error."""
        
        class FailingFormatter(ResponseFormatter):
            def __init__(self):
                super().__init__("failing", "1.0.0")
            
            def can_format(self, content: str, context: ResponseContext) -> bool:
                return True
            
            def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
                raise ValueError("Formatting failed")
            
            def get_theme_requirements(self) -> List[str]:
                return []
            
            def get_confidence_score(self, content: str, context: ResponseContext) -> float:
                return 0.9
        
        failing_formatter = FailingFormatter()
        self.registry.register_formatter(failing_formatter)
        
        context = ResponseContext(
            user_query="test",
            response_content="test content",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        # Should fall back to default formatter
        result = self.registry.format_response("test content", context)
        assert isinstance(result, FormattedResponse)
        assert result.content_type == ContentType.DEFAULT
    
    def test_list_formatters(self):
        """Test listing formatters."""
        formatter = MockFormatter("test-formatter")
        self.registry.register_formatter(formatter)
        
        formatters = self.registry.list_formatters()
        
        assert len(formatters) == 2  # Default + test formatter
        formatter_names = [f["name"] for f in formatters]
        assert "default" in formatter_names
        assert "test-formatter" in formatter_names
    
    def test_get_supported_content_types(self):
        """Test getting supported content types."""
        movie_formatter = MockFormatter("movie", [ContentType.MOVIE])
        self.registry.register_formatter(movie_formatter)
        
        content_types = self.registry.get_supported_content_types()
        
        assert ContentType.DEFAULT in content_types
        assert ContentType.MOVIE in content_types
    
    def test_validate_formatter(self):
        """Test formatter validation."""
        # Valid formatter
        valid_formatter = MockFormatter("valid")
        errors = self.registry.validate_formatter(valid_formatter)
        assert len(errors) == 0
        
        # Invalid formatter (not a ResponseFormatter)
        errors = self.registry.validate_formatter("not a formatter")
        assert len(errors) > 0
        assert "must be an instance of ResponseFormatter" in errors[0]
        
        # Formatter with empty name
        class InvalidFormatter(ResponseFormatter):
            def __init__(self):
                super().__init__("", "1.0.0")
            
            def can_format(self, content: str, context: ResponseContext) -> bool:
                return True
            
            def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
                return FormattedResponse(
                    content="", content_type=ContentType.DEFAULT,
                    theme_requirements=[], metadata={}, css_classes=[]
                )
            
            def get_theme_requirements(self) -> List[str]:
                return []
        
        invalid_formatter = InvalidFormatter()
        errors = self.registry.validate_formatter(invalid_formatter)
        assert len(errors) > 0
        assert "non-empty name" in errors[0]
    
    def test_get_registry_stats(self):
        """Test getting registry statistics."""
        movie_formatter = MockFormatter("movie", [ContentType.MOVIE])
        self.registry.register_formatter(movie_formatter)
        
        stats = self.registry.get_registry_stats()
        
        assert stats["total_formatters"] == 2  # Default + movie
        assert "default" in stats["formatter_names"]
        assert "movie" in stats["formatter_names"]
        assert "default" in stats["supported_content_types"]
        assert "movie" in stats["supported_content_types"]
    
    def test_clear_registry(self):
        """Test clearing registry."""
        formatter = MockFormatter("test-formatter")
        self.registry.register_formatter(formatter)
        
        assert len(self.registry._formatters) == 2
        
        self.registry.clear_registry()
        
        # Should only have default formatter
        assert len(self.registry._formatters) == 1
        assert "default" in self.registry._formatters
        assert "test-formatter" not in self.registry._formatters


class TestGlobalRegistry:
    """Test global registry functions."""
    
    def setup_method(self):
        """Reset global registry before each test."""
        reset_formatter_registry()
    
    def test_get_formatter_registry_singleton(self):
        """Test that get_formatter_registry returns singleton."""
        registry1 = get_formatter_registry()
        registry2 = get_formatter_registry()
        
        assert registry1 is registry2
    
    def test_reset_formatter_registry(self):
        """Test resetting global registry."""
        registry1 = get_formatter_registry()
        formatter = MockFormatter("test")
        registry1.register_formatter(formatter)
        
        reset_formatter_registry()
        
        registry2 = get_formatter_registry()
        assert registry1 is not registry2
        assert "test" not in registry2._formatters