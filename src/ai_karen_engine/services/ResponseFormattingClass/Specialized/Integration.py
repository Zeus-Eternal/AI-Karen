"""
Integration layer for specialized response formatting.
Migrated from extension system to core services.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from .Base import ResponseContext
from .Registry import get_specialized_registry
from .Detector import ContentTypeDetector
from ..Models import FormattedResponse
from ..Enums import ContentType

logger = logging.getLogger(__name__)

class SpecializedFormattingIntegration:
    """
    Main integration point for specialized response formatting.
    """

    def __init__(self):
        self.registry = get_specialized_registry()
        self.detector = ContentTypeDetector()
        self._register_builtin_formatters()
        logger.info("Specialized formatting integration initialized")

    def _register_builtin_formatters(self):
        """Register all built-in specialized formatters."""
        try:
            from .Formatters.weather_formatter import WeatherResponseFormatter
            from .Formatters.movie_formatter import MovieResponseFormatter
            from .Formatters.recipe_formatter import RecipeResponseFormatter
            from .Formatters.news_formatter import News_ResponseFormatter
            from .Formatters.product_formatter import ProductResponseFormatter
            from .Formatters.travel_formatter import TravelResponseFormatter
            from .Formatters.code_formatter import CodeResponseFormatter
            
            self.registry.register_formatter(WeatherResponseFormatter())
            self.registry.register_formatter(MovieResponseFormatter())
            self.registry.register_formatter(RecipeResponseFormatter())
            self.registry.register_formatter(News_ResponseFormatter())
            self.registry.register_formatter(ProductResponseFormatter())
            self.registry.register_formatter(TravelResponseFormatter())
            self.registry.register_formatter(CodeResponseFormatter())
            
            logger.info("Built-in specialized formatters registered")
        except Exception as e:
            logger.error(f"Failed to register built-in formatters: {e}")

    async def format_response(
        self, user_query: str, response_content: str, **kwargs
    ) -> FormattedResponse:
        """
        Automatically detect content type and apply specialized formatting.
        """
        start_time = time.time()
        
        # Detect content type
        detection_result = await self.detector.detect_content_type(
            user_query, response_content
        )
        
        # Build context
        context = ResponseContext(
            user_query=user_query,
            response_content=response_content,
            user_preferences=kwargs.get("user_preferences", {}),
            theme_context=kwargs.get("theme_context", {}),
            session_data=kwargs.get("session_data", {}),
            detected_content_type=detection_result.content_type,
            confidence_score=detection_result.confidence
        )
        
        # Format response
        try:
            formatted = await self.registry.format_response(response_content, context)
            
            # Add detection metadata
            if "formatting_integration" not in formatted.metadata:
                formatted.metadata["formatting_integration"] = {
                    "version": "2.0.0",
                    "formatter_used": getattr(self.registry.find_best_formatter(response_content, context), "name", "unknown"),
                    "detection_confidence": detection_result.confidence,
                    "detected_type": detection_result.content_type.value,
                    "latency_ms": (time.time() - start_time) * 1000
                }
            
            return formatted
        except Exception as e:
            logger.error(f"Specialized formatting failed: {e}")
            # Fallback to a basic FormattedResponse
            from ..Enums import FormatType
            return FormattedResponse(
                content=response_content,
                format_type=FormatType.STANDARD_MARKDOWN,
                metadata={"error": str(e)}
            )

# Global instance
_integration_instance: Optional[SpecializedFormattingIntegration] = None

def get_specialized_integration() -> SpecializedFormattingIntegration:
    """Get the global specialized integration instance."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = SpecializedFormattingIntegration()
    return _integration_instance
