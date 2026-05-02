from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ai_karen_engine.core.logging.logger import get_logger
from ai_karen_engine.core.logging.context import bind_log_context

class StructuredLoggingService:
    """
    Compatibility wrapper for the legacy StructuredLoggingService.
    All calls are routed to the centralized core.logging system.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = get_logger("kari.legacy.monitoring")
        if config and "global_metadata" in config:
             bind_log_context(**config["global_metadata"])

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        self.logger.exception(message, extra=kwargs)
    
    def with_context(self, **context):
        return BoundLogger(self, context)
    
    def log_api_request(self, **kwargs):
        """Standardized API request logging."""
        self.logger.event("runtime.request.api", **kwargs)

class BoundLogger:
    def __init__(self, service: StructuredLoggingService, context: Dict[str, Any]):
        self.service = service
        self.context = context
    
    def _merge(self, kwargs):
        return {**self.context, **kwargs}

    def debug(self, message: str, **kwargs):
        self.service.debug(message, **self._merge(kwargs))
    
    def info(self, message: str, **kwargs):
        self.service.info(message, **self._merge(kwargs))
    
    def warning(self, message: str, **kwargs):
        self.service.warning(message, **self._merge(kwargs))
    
    def error(self, message: str, **kwargs):
        self.service.error(message, **self._merge(kwargs))
    
    def critical(self, message: str, **kwargs):
        self.service.critical(message, **self._merge(kwargs))
    
    def exception(self, message: str, **kwargs):
        self.service.exception(message, **self._merge(kwargs))

_service: Optional[StructuredLoggingService] = None

def get_structured_logging_service(config: Dict[str, Any] = None) -> StructuredLoggingService:
    global _service
    if _service is None:
        _service = StructuredLoggingService(config)
    return _service
