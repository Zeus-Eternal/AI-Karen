"""
Integration layer for response formatting system with existing Kari infrastructure.

This module provides the integration points with the existing extensions SDK,
theme system, and LLM orchestrator.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
from dataclasses import asdict

from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType
from registry import get_formatter_registry, ResponseFormatterRegistry
from content_detector import ContentTypeDetector, ContentDetectionResult
from formatters.movie_formatter import MovieResponseFormatter
from formatters.recipe_formatter import RecipeResponseFormatter
from formatters.weather_formatter import WeatherResponseFormatter
from formatters.news_formatter import NewsResponseFormatter
from formatters.product_formatter import ProductResponseFormatter

logger = logging.getLogger(__name__)


class ResponseFormattingIntegration:
    """
    Main integration class for the response formatting system.
    
    This class provides the primary interface for integrating response formatting
    with the existing Kari infrastructure, including the LLM orchestrator,
    theme system, and extensions SDK.
    """
    
    def __init__(self):
        self.registry = get_formatter_registry()
        self.content_detector = ContentTypeDetector()
        self.logger = logging.getLogger(__name__)
        self._metrics = {
            'total_requests': 0,
            'successful_formats': 0,
            'failed_formats': 0,
            'fallback_uses': 0,
            'content_type_detections': {}
        }
        
        # Register built-in formatters
        self._register_builtin_formatters()
        
        logger.info("Response formatting integration initialized")
    
    def _register_builtin_formatters(self):
        """Register built-in formatters."""
        try:
            # Register movie formatter
            movie_formatter = MovieResponseFormatter()
            self.registry.register_formatter(movie_formatter)
            logger.info("Registered built-in movie formatter")
            
            # Register recipe formatter
            recipe_formatter = RecipeResponseFormatter()
            self.registry.register_formatter(recipe_formatter)
            logger.info("Registered built-in recipe formatter")
            
            # Register weather formatter
            weather_formatter = WeatherResponseFormatter()
            self.registry.register_formatter(weather_formatter)
            logger.info("Registered built-in weather formatter")
            
            # Register news formatter
            news_formatter = NewsResponseFormatter()
            self.registry.register_formatter(news_formatter)
            logger.info("Registered built-in news formatter")
            
            # Register product formatter
            product_formatter = ProductResponseFormatter()
            self.registry.register_formatter(product_formatter)
            logger.info("Registered built-in product formatter")
        except Exception as e:
            logger.error(f"Failed to register built-in formatters: {e}")
    
    async def format_response(
        self,
        user_query: str,
        response_content: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        theme_context: Optional[Dict[str, Any]] = None,
        session_data: Optional[Dict[str, Any]] = None
    ) -> FormattedResponse:
        """
        Format a response using the intelligent formatting system.
        
        Args:
            user_query: The original user query
            response_content: The AI response content to format
            user_preferences: User formatting preferences
            theme_context: Current theme context
            session_data: Session-specific data
            
        Returns:
            FormattedResponse with formatted content and metadata
        """
        self._metrics['total_requests'] += 1
        
        try:
            # Detect content type
            detection_result = await self.content_detector.detect_content_type(
                user_query, response_content
            )
            
            # Update metrics
            content_type_key = detection_result.content_type.value
            self._metrics['content_type_detections'][content_type_key] = (
                self._metrics['content_type_detections'].get(content_type_key, 0) + 1
            )
            
            # Create response context
            context = ResponseContext(
                user_query=user_query,
                response_content=response_content,
                user_preferences=user_preferences or {},
                theme_context=theme_context or {},
                session_data=session_data or {},
                detected_content_type=detection_result.content_type,
                confidence_score=detection_result.confidence
            )
            
            # Format the response
            formatted_response = self.registry.format_response(response_content, context)
            
            # Add detection metadata
            formatted_response.metadata.update({
                'content_detection': asdict(detection_result),
                'formatting_integration': {
                    'version': '1.0.0',
                    'formatter_used': formatted_response.metadata.get('formatter', 'unknown'),
                    'detection_confidence': detection_result.confidence
                }
            })
            
            self._metrics['successful_formats'] += 1
            
            logger.debug(
                f"Successfully formatted response: type={detection_result.content_type.value}, "
                f"confidence={detection_result.confidence:.2f}"
            )
            
            return formatted_response
            
        except Exception as e:
            self._metrics['failed_formats'] += 1
            logger.error(f"Response formatting failed: {e}")
            
            # Return basic formatted response as fallback
            try:
                fallback_context = ResponseContext(
                    user_query=user_query,
                    response_content=response_content,
                    user_preferences=user_preferences or {},
                    theme_context=theme_context or {},
                    session_data=session_data or {},
                    detected_content_type=ContentType.DEFAULT,
                    confidence_score=0.1
                )
                
                fallback_response = self.registry._default_formatter.format_response(
                    response_content, fallback_context
                )
                
                fallback_response.metadata['formatting_error'] = str(e)
                fallback_response.metadata['is_fallback'] = True
                
                self._metrics['fallback_uses'] += 1
                
                return fallback_response
                
            except Exception as fallback_error:
                logger.error(f"Even fallback formatting failed: {fallback_error}")
                raise
    
    def register_formatter(self, formatter: ResponseFormatter) -> None:
        """
        Register a new response formatter.
        
        Args:
            formatter: The formatter to register
        """
        self.registry.register_formatter(formatter)
        logger.info(f"Registered formatter: {formatter.name}")
    
    def unregister_formatter(self, formatter_name: str) -> bool:
        """
        Unregister a response formatter.
        
        Args:
            formatter_name: Name of the formatter to unregister
            
        Returns:
            True if unregistered successfully
        """
        result = self.registry.unregister_formatter(formatter_name)
        if result:
            logger.info(f"Unregistered formatter: {formatter_name}")
        return result
    
    def get_available_formatters(self) -> List[Dict[str, Any]]:
        """
        Get information about all available formatters.
        
        Returns:
            List of formatter metadata dictionaries
        """
        return self.registry.list_formatters()
    
    def get_supported_content_types(self) -> List[str]:
        """
        Get all supported content types.
        
        Returns:
            List of content type names
        """
        return [ct.value for ct in self.registry.get_supported_content_types()]
    
    async def detect_content_type(
        self, 
        user_query: str, 
        response_content: str
    ) -> ContentDetectionResult:
        """
        Detect content type without formatting.
        
        Args:
            user_query: The user query
            response_content: The response content
            
        Returns:
            ContentDetectionResult with detection information
        """
        return await self.content_detector.detect_content_type(user_query, response_content)
    
    def get_theme_requirements(self, content_type: ContentType) -> List[str]:
        """
        Get theme requirements for a specific content type.
        
        Args:
            content_type: The content type to get requirements for
            
        Returns:
            List of theme component names required
        """
        formatters = self.registry.get_formatters_for_content_type(content_type)
        
        all_requirements = set()
        for formatter in formatters:
            all_requirements.update(formatter.get_theme_requirements())
        
        return list(all_requirements)
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the formatting integration.
        
        Returns:
            Dictionary with integration metrics
        """
        return {
            **self._metrics,
            'registry_stats': self.registry.get_registry_stats(),
            'detector_stats': self.content_detector.get_detection_stats()
        }
    
    def reset_metrics(self) -> None:
        """Reset integration metrics."""
        self._metrics = {
            'total_requests': 0,
            'successful_formats': 0,
            'failed_formats': 0,
            'fallback_uses': 0,
            'content_type_detections': {}
        }
        logger.info("Integration metrics reset")
    
    async def validate_integration(self) -> Dict[str, Any]:
        """
        Validate the integration setup.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'registry_healthy': True,
            'detector_healthy': True,
            'theme_integration': True,
            'nlp_integration': True,
            'errors': []
        }
        
        try:
            # Test registry
            formatters = self.registry.list_formatters()
            if not formatters:
                validation_results['registry_healthy'] = False
                validation_results['errors'].append("No formatters registered")
            
            # Test content detector
            test_result = await self.content_detector.detect_content_type(
                "test query", "test response"
            )
            if not test_result:
                validation_results['detector_healthy'] = False
                validation_results['errors'].append("Content detector not working")
            
            # Test theme integration
            try:
                from ui_logic.themes.theme_manager import get_available_themes
                themes = get_available_themes()
                if not themes:
                    validation_results['theme_integration'] = False
                    validation_results['errors'].append("No themes available")
            except ImportError:
                validation_results['theme_integration'] = False
                validation_results['errors'].append("Theme manager not available")
            
            # Test NLP integration
            try:
                from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
                if not nlp_service_manager.is_ready():
                    validation_results['nlp_integration'] = False
                    validation_results['errors'].append("NLP services not ready")
            except ImportError:
                validation_results['nlp_integration'] = False
                validation_results['errors'].append("NLP service manager not available")
            
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {e}")
        
        validation_results['overall_healthy'] = (
            validation_results['registry_healthy'] and
            validation_results['detector_healthy'] and
            len(validation_results['errors']) == 0
        )
        
        return validation_results


# Global integration instance
_integration_instance: Optional[ResponseFormattingIntegration] = None


def get_response_formatting_integration() -> ResponseFormattingIntegration:
    """
    Get the global response formatting integration instance.
    
    Returns:
        The global ResponseFormattingIntegration instance
    """
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = ResponseFormattingIntegration()
    
    return _integration_instance


def reset_response_formatting_integration() -> None:
    """
    Reset the global integration instance.
    
    This is primarily used for testing.
    """
    global _integration_instance
    _integration_instance = None