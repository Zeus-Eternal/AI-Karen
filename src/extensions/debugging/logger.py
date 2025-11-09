"""
Extension Logger

Provides extension-specific logging capabilities with structured logging,
correlation tracking, and integration with the debugging system.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from threading import local
import traceback

from .models import LogEntry, LogLevel


class ExtensionLoggerContext:
    """Thread-local context for extension logging."""
    
    def __init__(self):
        self._local = local()
    
    def set_extension_context(self, extension_id: str, extension_name: str):
        """Set the current extension context."""
        self._local.extension_id = extension_id
        self._local.extension_name = extension_name
    
    def set_correlation_id(self, correlation_id: str):
        """Set the correlation ID for request tracking."""
        self._local.correlation_id = correlation_id
    
    def set_user_context(self, user_id: Optional[str], tenant_id: Optional[str]):
        """Set the user context."""
        self._local.user_id = user_id
        self._local.tenant_id = tenant_id
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current logging context."""
        return {
            'extension_id': getattr(self._local, 'extension_id', None),
            'extension_name': getattr(self._local, 'extension_name', None),
            'correlation_id': getattr(self._local, 'correlation_id', None),
            'user_id': getattr(self._local, 'user_id', None),
            'tenant_id': getattr(self._local, 'tenant_id', None)
        }
    
    def clear_context(self):
        """Clear the current logging context."""
        for attr in ['extension_id', 'extension_name', 'correlation_id', 'user_id', 'tenant_id']:
            if hasattr(self._local, attr):
                delattr(self._local, attr)


# Global context instance
_context = ExtensionLoggerContext()


class ExtensionLogHandler(logging.Handler):
    """Custom log handler for extension logging."""
    
    def __init__(self, debug_manager=None):
        super().__init__()
        self.debug_manager = debug_manager
        self.log_entries: List[LogEntry] = []
        self.max_entries = 10000  # Keep last 10k entries in memory
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record."""
        try:
            # Get context information
            context = _context.get_context()
            
            # Skip if no extension context
            if not context.get('extension_id'):
                return
            
            # Create log entry
            log_entry = LogEntry(
                id=str(uuid.uuid4()),
                extension_id=context['extension_id'],
                extension_name=context['extension_name'] or context['extension_id'],
                timestamp=datetime.utcnow(),
                level=self._map_log_level(record.levelno),
                message=record.getMessage(),
                source=record.name,
                metadata=self._extract_metadata(record),
                stack_trace=self._get_stack_trace(record),
                correlation_id=context.get('correlation_id'),
                user_id=context.get('user_id'),
                tenant_id=context.get('tenant_id')
            )
            
            # Store in memory
            self.log_entries.append(log_entry)
            if len(self.log_entries) > self.max_entries:
                self.log_entries.pop(0)
            
            # Send to debug manager if available
            if self.debug_manager:
                self.debug_manager.add_log_entry(log_entry)
                
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Error in ExtensionLogHandler: {e}")
    
    def _map_log_level(self, levelno: int) -> LogLevel:
        """Map Python log level to our LogLevel enum."""
        if levelno >= logging.CRITICAL:
            return LogLevel.CRITICAL
        elif levelno >= logging.ERROR:
            return LogLevel.ERROR
        elif levelno >= logging.WARNING:
            return LogLevel.WARNING
        elif levelno >= logging.INFO:
            return LogLevel.INFO
        else:
            return LogLevel.DEBUG
    
    def _extract_metadata(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract metadata from log record."""
        metadata = {}
        
        # Add standard fields
        if hasattr(record, 'funcName'):
            metadata['function'] = record.funcName
        if hasattr(record, 'lineno'):
            metadata['line_number'] = record.lineno
        if hasattr(record, 'pathname'):
            metadata['file_path'] = record.pathname
        
        # Add custom fields
        for key, value in record.__dict__.items():
            if key.startswith('ext_'):
                metadata[key[4:]] = value  # Remove 'ext_' prefix
        
        return metadata
    
    def _get_stack_trace(self, record: logging.LogRecord) -> Optional[str]:
        """Get stack trace if available."""
        if record.exc_info:
            return ''.join(traceback.format_exception(*record.exc_info))
        return None
    
    def get_logs(
        self,
        extension_id: Optional[str] = None,
        level: Optional[LogLevel] = None,
        limit: Optional[int] = None
    ) -> List[LogEntry]:
        """Get log entries with optional filtering."""
        logs = self.log_entries
        
        if extension_id:
            logs = [log for log in logs if log.extension_id == extension_id]
        
        if level:
            logs = [log for log in logs if log.level == level]
        
        if limit:
            logs = logs[-limit:]
        
        return logs


class ExtensionLogger:
    """
    Extension-specific logger with structured logging and debugging integration.
    
    Features:
    - Structured logging with metadata
    - Correlation ID tracking
    - User and tenant context
    - Integration with debugging system
    - Performance monitoring
    """
    
    def __init__(self, extension_id: str, extension_name: str, debug_manager=None):
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.debug_manager = debug_manager
        
        # Create logger instance
        self.logger = logging.getLogger(f"extension.{extension_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Add our custom handler
        self.handler = ExtensionLogHandler(debug_manager)
        self.handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.handler.setFormatter(formatter)
        
        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(self.handler)
        
        # Set extension context
        _context.set_extension_context(extension_id, extension_name)
    
    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None):
        """Context manager for correlation ID tracking."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        old_correlation_id = _context.get_context().get('correlation_id')
        _context.set_correlation_id(correlation_id)
        
        try:
            yield correlation_id
        finally:
            if old_correlation_id:
                _context.set_correlation_id(old_correlation_id)
            else:
                # Clear correlation ID if there wasn't one before
                context = _context.get_context()
                if hasattr(_context._local, 'correlation_id'):
                    delattr(_context._local, 'correlation_id')
    
    @contextmanager
    def user_context(self, user_id: Optional[str], tenant_id: Optional[str]):
        """Context manager for user context tracking."""
        old_context = _context.get_context()
        _context.set_user_context(user_id, tenant_id)
        
        try:
            yield
        finally:
            _context.set_user_context(
                old_context.get('user_id'),
                old_context.get('tenant_id')
            )
    
    def debug(self, message: str, **metadata):
        """Log debug message with metadata."""
        self._log_with_metadata(logging.DEBUG, message, metadata)
    
    def info(self, message: str, **metadata):
        """Log info message with metadata."""
        self._log_with_metadata(logging.INFO, message, metadata)
    
    def warning(self, message: str, **metadata):
        """Log warning message with metadata."""
        self._log_with_metadata(logging.WARNING, message, metadata)
    
    def error(self, message: str, exc_info=None, **metadata):
        """Log error message with metadata and optional exception info."""
        self._log_with_metadata(logging.ERROR, message, metadata, exc_info=exc_info)
    
    def critical(self, message: str, exc_info=None, **metadata):
        """Log critical message with metadata and optional exception info."""
        self._log_with_metadata(logging.CRITICAL, message, metadata, exc_info=exc_info)
    
    def _log_with_metadata(self, level: int, message: str, metadata: Dict[str, Any], exc_info=None):
        """Log message with metadata."""
        # Add metadata as extra fields
        extra = {}
        for key, value in metadata.items():
            extra[f'ext_{key}'] = value
        
        self.logger.log(level, message, exc_info=exc_info, extra=extra)
    
    def log_function_call(self, function_name: str, args: tuple = None, kwargs: Dict[str, Any] = None):
        """Log function call with parameters."""
        metadata = {
            'function_name': function_name,
            'args_count': len(args) if args else 0,
            'kwargs_keys': list(kwargs.keys()) if kwargs else []
        }
        
        # Don't log sensitive parameter values, just their presence
        self.debug(f"Function call: {function_name}", **metadata)
    
    def log_api_request(self, method: str, url: str, status_code: Optional[int] = None, 
                       response_time_ms: Optional[float] = None):
        """Log API request with details."""
        metadata = {
            'method': method,
            'url': url,
            'status_code': status_code,
            'response_time_ms': response_time_ms
        }
        
        level = logging.INFO
        if status_code and status_code >= 400:
            level = logging.ERROR if status_code >= 500 else logging.WARNING
        
        message = f"API {method} {url}"
        if status_code:
            message += f" -> {status_code}"
        if response_time_ms:
            message += f" ({response_time_ms:.1f}ms)"
        
        self._log_with_metadata(level, message, metadata)
    
    def log_database_query(self, query_type: str, table: str, duration_ms: Optional[float] = None,
                          rows_affected: Optional[int] = None):
        """Log database query with performance info."""
        metadata = {
            'query_type': query_type,
            'table': table,
            'duration_ms': duration_ms,
            'rows_affected': rows_affected
        }
        
        message = f"Database {query_type} on {table}"
        if duration_ms:
            message += f" ({duration_ms:.1f}ms)"
        if rows_affected is not None:
            message += f" - {rows_affected} rows"
        
        self.debug(message, **metadata)
    
    def log_plugin_execution(self, plugin_name: str, intent: str, success: bool,
                           duration_ms: Optional[float] = None, error: Optional[str] = None):
        """Log plugin execution with results."""
        metadata = {
            'plugin_name': plugin_name,
            'intent': intent,
            'success': success,
            'duration_ms': duration_ms,
            'error': error
        }
        
        message = f"Plugin {plugin_name} executed intent '{intent}'"
        if success:
            message += " successfully"
            level = logging.INFO
        else:
            message += " with error"
            level = logging.ERROR
        
        if duration_ms:
            message += f" ({duration_ms:.1f}ms)"
        
        self._log_with_metadata(level, message, metadata)
    
    def log_background_task(self, task_name: str, status: str, duration_ms: Optional[float] = None,
                           result: Optional[Dict[str, Any]] = None):
        """Log background task execution."""
        metadata = {
            'task_name': task_name,
            'status': status,
            'duration_ms': duration_ms,
            'result': result
        }
        
        message = f"Background task '{task_name}' {status}"
        if duration_ms:
            message += f" ({duration_ms:.1f}ms)"
        
        level = logging.INFO if status == 'completed' else logging.ERROR
        self._log_with_metadata(level, message, metadata)
    
    def get_logs(
        self,
        level: Optional[LogLevel] = None,
        limit: Optional[int] = None
    ) -> List[LogEntry]:
        """Get log entries for this extension."""
        return self.handler.get_logs(
            extension_id=self.extension_id,
            level=level,
            limit=limit
        )
    
    def export_logs(self, format: str = "json") -> str:
        """Export logs in specified format."""
        logs = self.get_logs()
        
        if format.lower() == "json":
            return json.dumps([log.to_dict() for log in logs], indent=2)
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                fieldnames = logs[0].to_dict().keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for log in logs:
                    writer.writerow(log.to_dict())
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


def get_extension_logger(extension_id: str, extension_name: str, debug_manager=None) -> ExtensionLogger:
    """Get or create an extension logger."""
    return ExtensionLogger(extension_id, extension_name, debug_manager)


# Convenience functions for common logging patterns
def log_extension_startup(logger: ExtensionLogger, version: str, config: Dict[str, Any]):
    """Log extension startup with version and config info."""
    logger.info(
        f"Extension starting up",
        version=version,
        config_keys=list(config.keys()),
        config_size=len(str(config))
    )


def log_extension_shutdown(logger: ExtensionLogger, reason: str = "normal"):
    """Log extension shutdown."""
    logger.info(f"Extension shutting down", reason=reason)


def log_performance_warning(logger: ExtensionLogger, operation: str, duration_ms: float, threshold_ms: float):
    """Log performance warning when operation exceeds threshold."""
    logger.warning(
        f"Performance warning: {operation} took {duration_ms:.1f}ms (threshold: {threshold_ms:.1f}ms)",
        operation=operation,
        duration_ms=duration_ms,
        threshold_ms=threshold_ms,
        performance_warning=True
    )