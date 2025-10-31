"""
Response formatter plugin registry system.

This module provides the registry for managing response formatter plugins,
integrating with the existing extensions SDK architecture.
"""

import logging
from typing import Dict, List, Optional, Type, Any
from threading import RLock
import importlib
import inspect

from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType, DefaultResponseFormatter, FormattingError

logger = logging.getLogger(__name__)


class ResponseFormatterRegistry:
    """
    Registry for managing response formatter plugins.
    
    This registry integrates with the existing extensions SDK to provide
    a centralized way to register, discover, and use response formatters.
    """
    
    def __init__(self):
        self._formatters: Dict[str, ResponseFormatter] = {}
        self._formatters_by_type: Dict[ContentType, List[ResponseFormatter]] = {}
        self._lock = RLock()
        self._default_formatter = DefaultResponseFormatter()
        
        # Register the default formatter
        self.register_formatter(self._default_formatter)
        
        logger.info("Response formatter registry initialized")
    
    def register_formatter(self, formatter: ResponseFormatter) -> None:
        """
        Register a response formatter.
        
        Args:
            formatter: The formatter instance to register
            
        Raises:
            ValueError: If formatter is invalid or already registered
        """
        if not isinstance(formatter, ResponseFormatter):
            raise ValueError(f"Formatter must be an instance of ResponseFormatter, got {type(formatter)}")
        
        with self._lock:
            if formatter.name in self._formatters:
                logger.warning(f"Formatter '{formatter.name}' is already registered, replacing")
            
            self._formatters[formatter.name] = formatter
            
            # Index by content types
            for content_type in formatter.get_supported_content_types():
                if content_type not in self._formatters_by_type:
                    self._formatters_by_type[content_type] = []
                
                # Remove existing instance if re-registering
                self._formatters_by_type[content_type] = [
                    f for f in self._formatters_by_type[content_type] 
                    if f.name != formatter.name
                ]
                self._formatters_by_type[content_type].append(formatter)
            
            logger.info(f"Registered formatter: {formatter.name} v{formatter.version}")
    
    def unregister_formatter(self, formatter_name: str) -> bool:
        """
        Unregister a response formatter.
        
        Args:
            formatter_name: Name of the formatter to unregister
            
        Returns:
            True if formatter was unregistered, False if not found
        """
        with self._lock:
            if formatter_name not in self._formatters:
                return False
            
            # Don't allow unregistering the default formatter
            if formatter_name == self._default_formatter.name:
                logger.warning("Cannot unregister default formatter")
                return False
            
            formatter = self._formatters.pop(formatter_name)
            
            # Remove from content type index
            for content_type in formatter.get_supported_content_types():
                if content_type in self._formatters_by_type:
                    self._formatters_by_type[content_type] = [
                        f for f in self._formatters_by_type[content_type]
                        if f.name != formatter_name
                    ]
            
            logger.info(f"Unregistered formatter: {formatter_name}")
            return True
    
    def get_formatter(self, formatter_name: str) -> Optional[ResponseFormatter]:
        """
        Get a formatter by name.
        
        Args:
            formatter_name: Name of the formatter to retrieve
            
        Returns:
            The formatter instance or None if not found
        """
        with self._lock:
            return self._formatters.get(formatter_name)
    
    def get_formatters_for_content_type(self, content_type: ContentType) -> List[ResponseFormatter]:
        """
        Get all formatters that support a specific content type.
        
        Args:
            content_type: The content type to find formatters for
            
        Returns:
            List of formatters that support the content type
        """
        with self._lock:
            return self._formatters_by_type.get(content_type, []).copy()
    
    def find_best_formatter(self, content: str, context: ResponseContext) -> ResponseFormatter:
        """
        Find the best formatter for the given content and context.
        
        Args:
            content: The content to format
            context: The formatting context
            
        Returns:
            The best formatter for the content (default formatter as fallback)
        """
        with self._lock:
            best_formatter = self._default_formatter
            best_score = 0.0
            
            # If we have a detected content type, prioritize those formatters
            if context.detected_content_type:
                candidates = self.get_formatters_for_content_type(context.detected_content_type)
            else:
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
            
            logger.debug(f"Selected formatter: {best_formatter.name} (score: {best_score})")
            return best_formatter
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format a response using the best available formatter.
        
        Args:
            content: The content to format
            context: The formatting context
            
        Returns:
            The formatted response
            
        Raises:
            FormattingError: If all formatters fail
        """
        formatter = self.find_best_formatter(content, context)
        
        try:
            return formatter.format_response(content, context)
        except Exception as e:
            logger.error(f"Formatter {formatter.name} failed: {e}")
            
            # Try default formatter as fallback if not already used
            if formatter != self._default_formatter:
                try:
                    logger.info("Falling back to default formatter")
                    return self._default_formatter.format_response(content, context)
                except Exception as fallback_error:
                    logger.error(f"Default formatter also failed: {fallback_error}")
                    raise FormattingError(
                        f"All formatters failed. Primary: {e}, Fallback: {fallback_error}",
                        formatter.name,
                        e
                    )
            else:
                raise FormattingError(f"Default formatter failed: {e}", formatter.name, e)
    
    def list_formatters(self) -> List[Dict[str, Any]]:
        """
        List all registered formatters with their metadata.
        
        Returns:
            List of formatter metadata dictionaries
        """
        with self._lock:
            return [formatter.get_metadata() for formatter in self._formatters.values()]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get all content types supported by registered formatters.
        
        Returns:
            List of supported content types
        """
        with self._lock:
            return list(self._formatters_by_type.keys())
    
    def load_formatter_from_module(self, module_path: str, class_name: str) -> bool:
        """
        Dynamically load a formatter from a module.
        
        Args:
            module_path: Python module path (e.g., 'extensions.response_formatting.movie')
            class_name: Name of the formatter class
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            module = importlib.import_module(module_path)
            formatter_class = getattr(module, class_name)
            
            if not inspect.isclass(formatter_class) or not issubclass(formatter_class, ResponseFormatter):
                logger.error(f"Class {class_name} is not a valid ResponseFormatter")
                return False
            
            formatter_instance = formatter_class()
            self.register_formatter(formatter_instance)
            
            logger.info(f"Loaded formatter {class_name} from {module_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load formatter {class_name} from {module_path}: {e}")
            return False
    
    def validate_formatter(self, formatter: ResponseFormatter) -> List[str]:
        """
        Validate a formatter implementation.
        
        Args:
            formatter: The formatter to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not isinstance(formatter, ResponseFormatter):
            errors.append("Must be an instance of ResponseFormatter")
            return errors
        
        if not formatter.name or not formatter.name.strip():
            errors.append("Formatter must have a non-empty name")
        
        if not formatter.version or not formatter.version.strip():
            errors.append("Formatter must have a non-empty version")
        
        try:
            theme_reqs = formatter.get_theme_requirements()
            if not isinstance(theme_reqs, list):
                errors.append("get_theme_requirements() must return a list")
        except Exception as e:
            errors.append(f"get_theme_requirements() failed: {e}")
        
        try:
            content_types = formatter.get_supported_content_types()
            if not isinstance(content_types, list):
                errors.append("get_supported_content_types() must return a list")
            elif not all(isinstance(ct, ContentType) for ct in content_types):
                errors.append("get_supported_content_types() must return ContentType enums")
        except Exception as e:
            errors.append(f"get_supported_content_types() failed: {e}")
        
        return errors
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the registry.
        
        Returns:
            Dictionary containing registry statistics
        """
        with self._lock:
            return {
                "total_formatters": len(self._formatters),
                "formatters_by_type": {
                    ct.value: len(formatters) 
                    for ct, formatters in self._formatters_by_type.items()
                },
                "formatter_names": list(self._formatters.keys()),
                "supported_content_types": [ct.value for ct in self.get_supported_content_types()]
            }
    
    def clear_registry(self) -> None:
        """
        Clear all formatters except the default formatter.
        
        This is primarily used for testing.
        """
        with self._lock:
            self._formatters.clear()
            self._formatters_by_type.clear()
            
            # Re-register default formatter
            self.register_formatter(self._default_formatter)
            
            logger.info("Registry cleared, default formatter re-registered")


# Global registry instance
_registry_instance: Optional[ResponseFormatterRegistry] = None
_registry_lock = RLock()


def get_formatter_registry() -> ResponseFormatterRegistry:
    """
    Get the global formatter registry instance.
    
    Returns:
        The global ResponseFormatterRegistry instance
    """
    global _registry_instance
    
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = ResponseFormatterRegistry()
    
    return _registry_instance


def reset_formatter_registry() -> None:
    """
    Reset the global formatter registry.
    
    This is primarily used for testing.
    """
    global _registry_instance
    
    with _registry_lock:
        _registry_instance = None