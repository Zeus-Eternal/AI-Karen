"""
Structured Logging Service

This service provides structured logging for the entire system.
"""

import logging
import json
import sys
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import traceback

from .internal.logging_impl import LoggingBackend


@dataclass
class LogEntry:
    """A structured log entry."""
    timestamp: datetime
    level: str
    message: str
    logger_name: str
    module: str = ""
    function: str = ""
    line_no: int = 0
    user_id: str = ""
    session_id: str = ""
    request_id: str = ""
    metadata: Dict[str, Any] = None
    exception: Dict[str, Any] = None


class StructuredLoggingService:
    """
    Structured Logging Service provides structured logging for the entire system.
    
    This service ensures consistent log formatting, automatic metadata
    enrichment, and multiple output targets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Structured Logging Service.
        
        Args:
            config: Configuration for logging
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Logging backends
        self.backends: List[LoggingBackend] = []
        
        # Global metadata
        self.global_metadata: Dict[str, Any] = config.get("global_metadata", {})
        
        # Initialize backends
        self._initialize_backends()
        
        # Configure standard logging
        self._configure_standard_logging()
    
    def _initialize_backends(self):
        """Initialize logging backends."""
        # Implementation would initialize actual logging backends
        # (e.g., console, file, Elasticsearch, etc.)
        self.logger.info("Initialized logging backends")
    
    def _configure_standard_logging(self):
        """Configure Python's standard logging to use structured logging."""
        # Create a handler that uses our structured logging
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self._get_formatter())
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
    
    def _get_formatter(self):
        """Get a log formatter."""
        return logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        logger_name: str,
        **kwargs
    ) -> LogEntry:
        """Create a structured log entry."""
        # Get caller information
        frame = kwargs.pop("frame", None)
        if frame:
            module = frame.f_globals.get("__name__", "")
            function = frame.f_code.co_name
            line_no = frame.f_lineno
        else:
            module = kwargs.pop("module", "")
            function = kwargs.pop("function", "")
            line_no = kwargs.pop("line_no", 0)
        
        # Create entry
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            logger_name=logger_name,
            module=module,
            function=function,
            line_no=line_no,
            metadata=kwargs.pop("metadata", {}),
            exception=kwargs.pop("exception", None)
        )
        
        # Add global metadata
        if self.global_metadata:
            if entry.metadata is None:
                entry.metadata = {}
            entry.metadata.update(self.global_metadata)
        
        # Add remaining kwargs as metadata
        for key, value in kwargs.items():
            if entry.metadata is None:
                entry.metadata = {}
            entry.metadata[key] = value
        
        return entry
    
    def _log_to_backends(self, entry: LogEntry):
        """Log an entry to all backends."""
        for backend in self.backends:
            try:
                backend.log(entry)
            except Exception as e:
                # Use standard logging to avoid recursion
                self.logger.error(f"Error logging to backend: {e}")
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        import inspect
        frame = inspect.currentframe().f_back
        entry = self._create_log_entry("DEBUG", message, __name__, frame=frame, **kwargs)
        self._log_to_backends(entry)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        import inspect
        frame = inspect.currentframe().f_back
        entry = self._create_log_entry("INFO", message, __name__, frame=frame, **kwargs)
        self._log_to_backends(entry)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        import inspect
        frame = inspect.currentframe().f_back
        entry = self._create_log_entry("WARNING", message, __name__, frame=frame, **kwargs)
        self._log_to_backends(entry)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        import inspect
        frame = inspect.currentframe().f_back
        entry = self._create_log_entry("ERROR", message, __name__, frame=frame, **kwargs)
        self._log_to_backends(entry)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        import inspect
        frame = inspect.currentframe().f_back
        entry = self._create_log_entry("CRITICAL", message, __name__, frame=frame, **kwargs)
        self._log_to_backends(entry)
    
    def exception(self, message: str, **kwargs):
        """Log an exception with traceback."""
        import inspect
        frame = inspect.currentframe().f_back
        
        # Get current exception info
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Create exception dict
        exception_dict = {
            "type": exc_type.__name__ if exc_type else None,
            "message": str(exc_value) if exc_value else None,
            "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback) if exc_traceback else None
        }
        
        entry = self._create_log_entry(
            "ERROR",
            message,
            __name__,
            frame=frame,
            exception=exception_dict,
            **kwargs
        )
        self._log_to_backends(entry)
    
    def with_context(self, **context):
        """
        Create a logger with bound context.
        
        Args:
            **context: Context to bind to the logger
            
        Returns:
            A logger with bound context
        """
        return BoundLogger(self, context)
    
    def add_backend(self, backend: "LoggingBackend"):
        """
        Add a logging backend.
        
        Args:
            backend: The logging backend to add
        """
        self.backends.append(backend)
        self.logger.info(f"Added logging backend: {type(backend).__name__}")
    
    def set_global_metadata(self, metadata: Dict[str, Any]):
        """
        Set global metadata for all log entries.
        
        Args:
            metadata: Global metadata to set
        """
        self.global_metadata.update(metadata)
        self.logger.info(f"Updated global metadata: {list(metadata.keys())}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.
        
        Returns:
            Dictionary of logging statistics
        """
        stats = {
            "backend_count": len(self.backends),
            "global_metadata_keys": list(self.global_metadata.keys())
        }
        
        # Collect stats from backends
        for backend in self.backends:
            if hasattr(backend, "get_stats"):
                backend_stats = backend.get_stats()
                stats[f"backend_{type(backend).__name__}"] = backend_stats
        
        return stats


class BoundLogger:
    """A logger with bound context."""
    
    def __init__(self, logging_service: StructuredLoggingService, context: Dict[str, Any]):
        """
        Initialize the Bound Logger.
        
        Args:
            logging_service: The parent logging service
            context: Bound context
        """
        self.logging_service = logging_service
        self.context = context
    
    def debug(self, message: str, **kwargs):
        """Log a debug message with bound context."""
        self.logging_service.debug(message, **{**self.context, **kwargs})
    
    def info(self, message: str, **kwargs):
        """Log an info message with bound context."""
        self.logging_service.info(message, **{**self.context, **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log a warning message with bound context."""
        self.logging_service.warning(message, **{**self.context, **kwargs})
    
    def error(self, message: str, **kwargs):
        """Log an error message with bound context."""
        self.logging_service.error(message, **{**self.context, **kwargs})
    
    def critical(self, message: str, **kwargs):
        """Log a critical message with bound context."""
        self.logging_service.critical(message, **{**self.context, **kwargs})
    
    def exception(self, message: str, **kwargs):
        """Log an exception with bound context."""
        self.logging_service.exception(message, **{**self.context, **kwargs})
