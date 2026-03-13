"""
Unified logging system for AI Karen engine.
"""

from enum import Enum

from ai_karen_engine.core.logging.logger import (
    StructuredLogger as KarenLogger,
    get_structured_logger as get_logger,
    configure_logging,
    LogLevel
)

# Add LogFormat enum for compatibility
class LogFormat(Enum):
    """Log format options"""
    TEXT = "text"
    JSON = "json"
    STRUCTURED = "structured"
from ai_karen_engine.core.logging.middleware import logging_middleware
from ai_karen_engine.core.logging.formatters import StructuredFormatter, JSONFormatter

__all__ = [
    "KarenLogger",
    "get_logger", 
    "configure_logging",
    "LogLevel",
    "LogFormat",
    "logging_middleware",
    "StructuredFormatter",
    "JSONFormatter"
]