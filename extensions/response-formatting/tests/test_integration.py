"""
Unit tests for response formatting integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import (
    ResponseFormatter,
    FormattedResponse,
    ResponseContext,
    ContentType
)
from integration import (
    ResponseFormattingIntegration,
    get_response_formatting_integration,
    reset_response_formatting_integration
)
from content_detector import ContentDetectionResult


class MockFormatter(ResponseFormatter):
    """Mock formatter for testing."""
    
    def __init__(self, name: str, content_type: ContentType = ContentType.DEFAULT):
        super().__init__(name, "1.0.0")
        self._content_type = content_type
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        return "mock" in content.lower()
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        return FormattedResponse(
            content=f"<div class='mock-{self.name}'>{content}</div>",
            content_type=self._content_type,
            theme_requirements=[f"{self.name}-theme"],
            metadata={"formatter": self.name},
            css_classes=[f"mock-{self.name}"]
        )
    
    def get_theme_requirements(self) -> list:
        return [f"{self.name}-theme"]
    
    def get_supported_content_types(self) -> list:
        return [self._content_type]


class TestResponseFormattingIntegration:
    """Test the response formatting integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.integration = ResponseFormattingIntegration()
    
    @pytest.mark.asyncio
    async def test_format_response_basic(self):
        """Test basic response formatting."""
        query = "Tell me about movies"
        response = "Movies are a form of entertainment"
        
        # Mock content detection
        mock_detection = ContentDetectionResult(
            content_type=ContentType.MOVIE,
            confidence=0.8,
            reasoning="Detected movie content",
            detected_entities=["WORK_OF_ART"],
            keywords=["movie"]
        )
        
        with patch.object(self.integration.content_detector, 'detect_content_type', return_value=mock_detection):
            result = await self.integration.format_response(query, response)
        
        assert isinstance(result, FormattedResponse)
        assert result.content_type == ContentType.DEFAULT  # Default formatter used
        assert "content_detection" in result.metadata
        assert "formatting_integration" in result.metadata
    
    @pytest.mark.asyncio
    async def test_format_response_with_preferences(self):
        """Test formatting with user preferences and theme context."""
        query = "What's the weather?"
        response = "It's sunny today"
        preferences = {"theme": "dark"}
        theme_context = {"current_theme": "dark"}
        session_data = {"user_id": "123"}
        
        result = await self.integration.format_response(
            query, response, preferences, theme_context, session_data
        )
        
        assert isinstance(result, FormattedResponse)
        assert "formatting_integration" in result.metadata
    
    @pytest.mark.asyncio
    async def test_format_response_with_custom_formatter(self):
        """Test formatting with custom formatter."""
        # Register a custom formatter
        custom_formatter = MockFormatter("custom", ContentType.MOVIE)
        self.integration.register_formatter(custom_formatter)
        
        query = "Tell me about movies"
        response = "mock movie content"
        
        # Mock detection to return movie type
        mock_detection = ContentDetectionResult(
            content_type=ContentType.MOVIE,
            confidence=0.9,
            reasoning="Movie detected",
            detected_entities=[],
            keywords=["movie"]
        )
        
        with patch.object(self.integration.content_detector, 'detect_content_type', return_value=mock_detection):
            result = await self.integration.format_response(query, response)
        
        assert "mock-custom" in result.content
        assert result.metadata["formatter"] == "custom"
    
    @pytest.mark.asyncio
    async def test_format_response_error_handling(self):
        """Test error handling in response formatting."""
        
        # Mock content detector to raise an error
        with patch.object(self.integration.content_detector, 'detect_content_type', side_effect=Exception("Detection failed")):
            result = await self.integration.format_response("query", "response")
        
        # Should fall back to default formatting
        assert isinstance(result, FormattedResponse)
        assert result.metadata.get("is_fallback") is True
        assert "formatting_error" in result.metadata
    
    @pytest.mark.asyncio
    async def test_format_response_metrics_tracking(self):
        """Test that metrics are properly tracked."""
        initial_requests = self.integration._metrics['total_requests']
        initial_successful = self.integration._metrics['successful_formats']
        
        await self.integration.format_response("query", "response")
        
        assert self.integration._metrics['total_requests'] == initial_requests + 1
        assert self.integration._metrics['successful_formats'] == initial_successful + 1
    
    def test_register_formatter(self):
        """Test formatter registration."""
        formatter = MockFormatter("test-formatter")
        
        self.integration.register_formatter(formatter)
        
        registered = self.integration.registry.get_formatter("test-formatter")
        assert registered == formatter
    
    def test_unregister_formatter(self):
        """Test formatter unregistration."""
        formatter = MockFormatter("test-formatter")
        self.integration.register_formatter(formatter)
        
        result = self.integration.unregister_formatter("test-formatter")
        assert result is True
        
        registered = self.integration.registry.get_formatter("test-formatter")
        assert registered is None
    
    def test_get_available_formatters(self):
        """Test getting available formatters."""
        formatter = MockFormatter("test-formatter")
        self.integration.register_formatter(formatter)
        
        formatters = self.integration.get_available_formatters()
        
        assert len(formatters) >= 2  # Default + test formatter
        formatter_names = [f["name"] for f in formatters]
        assert "test-formatter" in formatter_names
        assert "default" in formatter_names
    
    def test_get_supported_content_types(self):
        """Test getting supported content types."""
        content_types = self.integration.get_supported_content_types()
        
        assert "default" in content_types
        assert len(content_types) >= 1
    
    @pytest.mark.asyncio
    async def test_detect_content_type(self):
        """Test content type detection."""
        query = "What's the weather?"
        response = "It's sunny today"
        
        result = await self.integration.detect_content_type(query, response)
        
        assert isinstance(result, ContentDetectionResult)
        assert isinstance(result.content_type, ContentType)
        assert 0.0 <= result.confidence <= 1.0
    
    def test_get_theme_requirements(self):
        """Test getting theme requirements for content type."""
        formatter = MockFormatter("movie-formatter", ContentType.MOVIE)
        self.integration.register_formatter(formatter)
        
        requirements = self.integration.get_theme_requirements(ContentType.MOVIE)
        
        assert "movie-formatter-theme" in requirements
    
    def test_get_integration_metrics(self):
        """Test getting integration metrics."""
        metrics = self.integration.get_integration_metrics()
        
        assert "total_requests" in metrics
        assert "successful_formats" in metrics
        assert "failed_formats" in metrics
        assert "fallback_uses" in metrics
        assert "content_type_detections" in metrics
        assert "registry_stats" in metrics
        assert "detector_stats" in metrics
    
    def test_reset_metrics(self):
        """Test resetting metrics."""
        # Generate some metrics
        self.integration._metrics['total_requests'] = 10
        self.integration._metrics['successful_formats'] = 8
        
        self.integration.reset_metrics()
        
        assert self.integration._metrics['total_requests'] == 0
        assert self.integration._metrics['successful_formats'] == 0
    
    @pytest.mark.asyncio
    async def test_validate_integration(self):
        """Test integration validation."""
        result = await self.integration.validate_integration()
        
        assert "registry_healthy" in result
        assert "detector_healthy" in result
        assert "theme_integration" in result
        assert "nlp_integration" in result
        assert "overall_healthy" in result
        assert "errors" in result
        
        # Should be healthy with default setup
        assert result["registry_healthy"] is True
        assert result["detector_healthy"] is True
    
    @pytest.mark.asyncio
    async def test_validate_integration_with_errors(self):
        """Test integration validation with errors."""
        
        # Mock registry to have no formatters
        with patch.object(self.integration.registry, 'list_formatters', return_value=[]):
            result = await self.integration.validate_integration()
        
        assert result["registry_healthy"] is False
        assert "No formatters registered" in result["errors"]
        assert result["overall_healthy"] is False
    
    @pytest.mark.asyncio
    async def test_validate_integration_theme_unavailable(self):
        """Test validation when theme manager is unavailable."""
        
        with patch('integration.get_available_themes', side_effect=ImportError("Theme manager not available")):
            result = await self.integration.validate_integration()
        
        assert result["theme_integration"] is False
        assert any("Theme manager not available" in error for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_validate_integration_nlp_unavailable(self):
        """Test validation when NLP services are unavailable."""
        
        with patch('integration.nlp_service_manager', side_effect=ImportError("NLP not available")):
            result = await self.integration.validate_integration()
        
        assert result["nlp_integration"] is False
        assert any("NLP service manager not available" in error for error in result["errors"])


class TestGlobalIntegration:
    """Test global integration functions."""
    
    def setup_method(self):
        """Reset global integration before each test."""
        reset_response_formatting_integration()
    
    def test_get_response_formatting_integration_singleton(self):
        """Test that get_response_formatting_integration returns singleton."""
        integration1 = get_response_formatting_integration()
        integration2 = get_response_formatting_integration()
        
        assert integration1 is integration2
    
    def test_reset_response_formatting_integration(self):
        """Test resetting global integration."""
        integration1 = get_response_formatting_integration()
        formatter = MockFormatter("test")
        integration1.register_formatter(formatter)
        
        reset_response_formatting_integration()
        
        integration2 = get_response_formatting_integration()
        assert integration1 is not integration2
        
        # New integration should not have the test formatter
        registered = integration2.registry.get_formatter("test")
        assert registered is None