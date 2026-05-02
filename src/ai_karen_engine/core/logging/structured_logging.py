from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .logger import get_logger
from .context import bind_log_context

class StructuredLoggingService:
    """
    Phase 4.1.d compatibility shim.
    Delegates to the canonical core.logging system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger("kari.legacy.core")
        self.configured = True

    def configure_logging(self):
        pass

    def get_logger(self, name: str) -> logging.Logger:
        return get_logger(name) # type: ignore

    def log_api_request(self, **kwargs):
        self.logger.event("runtime.request.api", **kwargs)

    def log_memory_access(self, **kwargs):
        self.logger.event("memory.access", **kwargs)

class PIIRedactor:
    """
    Compatibility shim for legacy PIIRedactor.
    """
    @staticmethod
    def redact_pii(text: str) -> str:
        from .redaction import redact_text
        return redact_text(text)

def get_structured_logging_service() -> StructuredLoggingService:
    return StructuredLoggingService()

__all__ = ["StructuredLoggingService", "get_structured_logging_service", "PIIRedactor"]
