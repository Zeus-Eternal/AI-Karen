"""
Registry for specialized response formatters.
Migrated from extension system to core services.
"""

import logging
from typing import Dict, List, Optional, Any
from threading import RLock

from .Base import SpecializedFormatter, ResponseContext, FormattingError
from ..Models import FormattedResponse
from ..Enums import ContentType, FormatType

logger = logging.getLogger(__name__)

class DefaultSpecializedFormatter(SpecializedFormatter):
    """Fallback formatter that returns content as standard markdown."""
    def __init__(self):
        super().__init__("default", "1.0.0")
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        return True
    
    async def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        return FormattedResponse(
            content=content,
            format_type=FormatType.STANDARD_MARKDOWN,
            metadata={"formatter": "default"}
        )
    
    def get_theme_requirements(self) -> List[str]:
        return ["typography"]

class SpecializedFormatterRegistry:
    """
    Registry for managing specialized response formatters.
    """

    def __init__(self):
        self._formatters: Dict[str, SpecializedFormatter] = {}
        self._formatters_by_type: Dict[ContentType, List[SpecializedFormatter]] = {}
        self._lock = RLock()
        self._default_formatter = DefaultSpecializedFormatter()

        # Register the default formatter
        self.register_formatter(self._default_formatter)

        logger.info("Specialized response formatter registry initialized")

    def register_formatter(self, formatter: SpecializedFormatter) -> None:
        """Register a response formatter."""
        if not isinstance(formatter, SpecializedFormatter):
            raise ValueError(
                f"Formatter must be an instance of SpecializedFormatter, got {type(formatter)}"
            )

        with self._lock:
            self._formatters[formatter.name] = formatter

            # Index by content types
            for content_type in formatter.get_supported_content_types():
                if content_type not in self._formatters_by_type:
                    self._formatters_by_type[content_type] = []

                self._formatters_by_type[content_type] = [
                    f for f in self._formatters_by_type[content_type]
                    if f.name != formatter.name
                ]
                self._formatters_by_type[content_type].append(formatter)

            logger.info(f"Registered specialized formatter: {formatter.name}")

    def find_best_formatter(
        self, content: str, context: ResponseContext
    ) -> SpecializedFormatter:
        """Find the best formatter for the given content and context."""
        with self._lock:
            best_formatter = self._default_formatter
            best_score = 0.0

            candidates = []
            if context.detected_content_type:
                candidates = self._formatters_by_type.get(context.detected_content_type, [])
            
            if not candidates:
                candidates = list(self._formatters.values())

            for formatter in candidates:
                try:
                    if formatter.can_format(content, context):
                        score = formatter.get_confidence_score(content, context)
                        if score > best_score:
                            best_formatter = formatter
                            best_score = score
                except Exception as e:
                    logger.warning(f"Error checking formatter {formatter.name}: {e}")
                    continue

            return best_formatter

    async def format_response(
        self, content: str, context: ResponseContext
    ) -> FormattedResponse:
        """Format a response using the best available specialized formatter."""
        formatter = self.find_best_formatter(content, context)

        try:
            return await formatter.format_response(content, context)
        except Exception as e:
            logger.error(f"Specialized formatter {formatter.name} failed: {e}")

            if formatter != self._default_formatter:
                return await self._default_formatter.format_response(content, context)
            else:
                raise FormattingError(
                    f"Default formatter failed: {e}", formatter.name, e
                )

# Global registry instance
_registry_instance: Optional[SpecializedFormatterRegistry] = None
_registry_lock = RLock()

def get_specialized_registry() -> SpecializedFormatterRegistry:
    """Get the global specialized formatter registry instance."""
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = SpecializedFormatterRegistry()
    return _registry_instance
