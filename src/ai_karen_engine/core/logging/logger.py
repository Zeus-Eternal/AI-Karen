"""
Enhanced logging system for AI Karen engine.
"""

import logging
import os
import sys
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime
import json

from ai_karen_engine.core.logging.formatters import StructuredFormatter, JSONFormatter, ColoredFormatter


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log output formats."""
    STRUCTURED = "structured"
    JSON = "json"
    SIMPLE = "simple"
    COLORED = "colored"


class KarenLogger:
    """
    Enhanced logger with structured logging and context management.
    """
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        self._context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs) -> None:
        """
        Set logging context that will be included in all log messages.
        
        Args:
            **kwargs: Context key-value pairs
        """
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all logging context."""
        self._context.clear()
    
    def remove_context(self, *keys) -> None:
        """
        Remove specific keys from logging context.
        
        Args:
            *keys: Context keys to remove
        """
        for key in keys:
            self._context.pop(key, None)
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """
        Log message with context.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context
        """
        # Merge context with additional kwargs
        context = {**self._context, **kwargs}
        
        # Create extra dict for structured logging
        extra = {
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'logger_name': self.name
        }
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        context = {**self._context, **kwargs}
        extra = {
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'logger_name': self.name
        }
        self.logger.exception(message, extra=extra)


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    format_type: LogFormat = LogFormat.STRUCTURED,
    log_file: Optional[str] = None,
    include_console: bool = True
) -> None:
    """
    Configure global logging settings.
    
    Args:
        level: Log level
        format_type: Log format type
        log_file: Optional log file path
        include_console: Whether to include console output
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.value))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Choose formatter for console
    console_formatter: logging.Formatter
    if format_type == LogFormat.JSON:
        console_formatter = JSONFormatter()
    elif format_type == LogFormat.COLORED:
        # Explicit colored output
        console_formatter = ColoredFormatter()
    elif format_type == LogFormat.STRUCTURED:
        # Structured by default; upgrade to colored if terminal supports it and env enabled
        use_color = sys.stdout.isatty() and os.getenv("KAREN_LOG_COLOR", "true").lower() in ("1", "true", "yes")
        console_formatter = ColoredFormatter() if use_color else StructuredFormatter()
    else:
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        # File handler should be structured or JSON; avoid ANSI codes in files
        file_formatter: logging.Formatter
        if format_type == LogFormat.JSON:
            file_formatter = JSONFormatter()
        elif format_type == LogFormat.STRUCTURED or format_type == LogFormat.COLORED:
            file_formatter = StructuredFormatter()
        else:
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str, level: LogLevel = LogLevel.INFO) -> KarenLogger:
    """
    Get a KarenLogger instance.
    
    Args:
        name: Logger name
        level: Log level
        
    Returns:
        KarenLogger instance
    """
    return KarenLogger(name, level)


# Configure logging from environment variables
class _DedupFilter(logging.Filter):
    """Filter that drops immediate duplicate log records within a short window.

    Helps suppress spammy repeats (e.g., identical SQL lines emitted by multiple handlers).
    """

    def __init__(self, window_seconds: float = 1.0):
        super().__init__(name="")
        self.window = window_seconds
        self._last_key: Optional[tuple] = None
        self._last_ts: float = 0.0

    def filter(self, record: logging.LogRecord) -> bool:  # True = allow
        try:
            import time as _time
            key = (record.name, record.levelno, record.getMessage())
            now = _time.time()
            if self._last_key == key and (now - self._last_ts) <= self.window:
                return False
            self._last_key = key
            self._last_ts = now
        except Exception:
            return True
        return True


def _configure_sqlalchemy_loggers() -> None:
    """Tune SQLAlchemy logger levels and propagation to avoid duplicate lines."""
    lvl = os.getenv("KAREN_SQLALCHEMY_LOG_LEVEL", "WARNING").upper()
    try:
        sa_level = getattr(logging, lvl)
    except Exception:
        sa_level = logging.WARNING

    # Core SQLAlchemy loggers
    sa_logger = logging.getLogger("sqlalchemy")
    sa_engine = logging.getLogger("sqlalchemy.engine")
    sa_pool = logging.getLogger("sqlalchemy.pool")

    for lg in (sa_logger, sa_engine, sa_pool):
        lg.setLevel(sa_level)
        # Clear custom handlers to prevent double-formatting
        lg.handlers.clear()
        # Allow propagation to root so our global formatter applies
        lg.propagate = True


def configure_from_env() -> None:
    """Configure logging from environment variables."""
    level = LogLevel(os.getenv("KAREN_LOG_LEVEL", "INFO"))
    fmt = os.getenv("KAREN_LOG_FORMAT", "structured").lower()
    if fmt not in {f.value for f in LogFormat}:  # backward compat
        fmt = "structured"
    format_type = LogFormat(fmt)
    log_file = os.getenv("KAREN_LOG_FILE")
    include_console = os.getenv("KAREN_LOG_CONSOLE", "true").lower() == "true"
    
    configure_logging(
        level=level,
        format_type=format_type,
        log_file=log_file,
        include_console=include_console
    )
    # Optionally add dedup filter to console handler
    dedup = os.getenv("KAREN_LOG_DEDUP", "true").lower() in ("1", "true", "yes")
    window = float(os.getenv("KAREN_LOG_DEDUP_WINDOW", "0.75"))
    if dedup:
        try:
            root = logging.getLogger()
            for h in root.handlers:
                # Avoid adding twice
                if not any(isinstance(f, _DedupFilter) for f in h.filters):
                    h.addFilter(_DedupFilter(window_seconds=window))
        except Exception:
            pass

    # Configure SQLAlchemy loggers post root-config
    _configure_sqlalchemy_loggers()


# Auto-configure on import if not already configured
if not logging.getLogger().handlers:
    configure_from_env()
