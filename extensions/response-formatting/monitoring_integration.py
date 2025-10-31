"""
Response Formatting Monitoring Integration

Integrates response formatting system with production monitoring to track
success/failure rates, performance, and fallback usage.

Requirements: 5.8, 7.1
"""

import time
import logging
from typing import Any, Dict, Optional
from functools import wraps

from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


def with_response_formatting_monitoring(formatter_type: str):
    """
    Decorator to add monitoring to response formatting operations.
    
    Args:
        formatter_type: Type of formatter being monitored
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Import here to avoid circular imports
                from ai_karen_engine.services.production_monitoring_service import (
                    get_production_monitoring_service
                )
                
                monitoring_service = get_production_monitoring_service()
                
                # Execute the formatting function
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Determine content type from result or args
                content_type = "unknown"
                if hasattr(result, 'content_type'):
                    content_type = result.content_type
                elif len(args) > 1 and isinstance(args[1], dict):
                    content_type = args[1].get('content_type', 'unknown')
                
                # Record success
                monitoring_service.record_response_formatting_success(
                    formatter_type=formatter_type,
                    content_type=content_type,
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                # Calculate duration for failed operation
                duration_ms = (time.time() - start_time) * 1000
                
                try:
                    from ai_karen_engine.services.production_monitoring_service import (
                        get_production_monitoring_service
                    )
                    
                    monitoring_service = get_production_monitoring_service()
                    
                    # Record failure
                    monitoring_service.record_response_formatting_failure(
                        formatter_type=formatter_type,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                    
                except Exception as monitoring_error:
                    logger.error(f"Error recording formatting failure: {monitoring_error}")
                
                # Re-raise the original exception
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Import here to avoid circular imports
                from ai_karen_engine.services.production_monitoring_service import (
                    get_production_monitoring_service
                )
                
                monitoring_service = get_production_monitoring_service()
                
                # Execute the formatting function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Determine content type from result or args
                content_type = "unknown"
                if hasattr(result, 'content_type'):
                    content_type = result.content_type
                elif len(args) > 1 and isinstance(args[1], dict):
                    content_type = args[1].get('content_type', 'unknown')
                
                # Record success
                monitoring_service.record_response_formatting_success(
                    formatter_type=formatter_type,
                    content_type=content_type,
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                # Calculate duration for failed operation
                duration_ms = (time.time() - start_time) * 1000
                
                try:
                    from ai_karen_engine.services.production_monitoring_service import (
                        get_production_monitoring_service
                    )
                    
                    monitoring_service = get_production_monitoring_service()
                    
                    # Record failure
                    monitoring_service.record_response_formatting_failure(
                        formatter_type=formatter_type,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                    
                except Exception as monitoring_error:
                    logger.error(f"Error recording formatting failure: {monitoring_error}")
                
                # Re-raise the original exception
                raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def record_response_formatting_fallback(
    original_formatter: str,
    fallback_reason: str,
    context: Optional[Dict[str, Any]] = None
):
    """
    Record response formatting fallback usage.
    
    Args:
        original_formatter: The formatter that failed
        fallback_reason: Reason for fallback
        context: Additional context information
    """
    try:
        from ai_karen_engine.services.production_monitoring_service import (
            get_production_monitoring_service
        )
        
        monitoring_service = get_production_monitoring_service()
        monitoring_service.record_response_formatting_fallback(
            original_formatter=original_formatter,
            fallback_reason=fallback_reason
        )
        
        logger.info(
            f"Response formatting fallback: {original_formatter} -> default "
            f"(reason: {fallback_reason})"
        )
        
    except Exception as e:
        logger.error(f"Error recording formatting fallback: {e}")


class ResponseFormattingMonitor:
    """
    Context manager for monitoring response formatting operations.
    """
    
    def __init__(self, formatter_type: str, content_type: str = "unknown"):
        self.formatter_type = formatter_type
        self.content_type = content_type
        self.start_time = None
        self.monitoring_service = None
    
    def __enter__(self):
        self.start_time = time.time()
        
        try:
            from ai_karen_engine.services.production_monitoring_service import (
                get_production_monitoring_service
            )
            self.monitoring_service = get_production_monitoring_service()
        except Exception as e:
            logger.error(f"Error initializing monitoring service: {e}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None or self.monitoring_service is None:
            return
        
        duration_ms = (time.time() - self.start_time) * 1000
        
        try:
            if exc_type is None:
                # Success case
                self.monitoring_service.record_response_formatting_success(
                    formatter_type=self.formatter_type,
                    content_type=self.content_type,
                    duration_ms=duration_ms
                )
            else:
                # Failure case
                self.monitoring_service.record_response_formatting_failure(
                    formatter_type=self.formatter_type,
                    error_type=exc_type.__name__ if exc_type else "UnknownError",
                    error_message=str(exc_val) if exc_val else "Unknown error"
                )
        except Exception as e:
            logger.error(f"Error recording formatting metrics: {e}")


# Convenience functions for common monitoring scenarios

def monitor_movie_formatting(func):
    """Decorator for movie response formatting monitoring"""
    return with_response_formatting_monitoring("movie")(func)


def monitor_recipe_formatting(func):
    """Decorator for recipe response formatting monitoring"""
    return with_response_formatting_monitoring("recipe")(func)


def monitor_weather_formatting(func):
    """Decorator for weather response formatting monitoring"""
    return with_response_formatting_monitoring("weather")(func)


def monitor_news_formatting(func):
    """Decorator for news response formatting monitoring"""
    return with_response_formatting_monitoring("news")(func)


def monitor_product_formatting(func):
    """Decorator for product response formatting monitoring"""
    return with_response_formatting_monitoring("product")(func)


def monitor_travel_formatting(func):
    """Decorator for travel response formatting monitoring"""
    return with_response_formatting_monitoring("travel")(func)


def monitor_code_formatting(func):
    """Decorator for code response formatting monitoring"""
    return with_response_formatting_monitoring("code")(func)


def monitor_default_formatting(func):
    """Decorator for default response formatting monitoring"""
    return with_response_formatting_monitoring("default")(func)