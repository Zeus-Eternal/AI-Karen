"""
Custom log formatters for AI Karen engine.
"""

import logging
import json
from typing import Any, Dict
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter that includes context and metadata.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with structured information.
        
        Args:
            record: Log record
            
        Returns:
            Formatted log message
        """
        # Get basic information
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()
        
        # Get context if available
        context = getattr(record, 'context', {})
        
        # Build structured message
        parts = [
            f"[{timestamp}]",
            f"[{level}]",
            f"[{logger_name}]",
            message
        ]
        
        # Add context if present
        if context:
            context_str = " ".join([f"{k}={v}" for k, v in context.items()])
            parts.append(f"[{context_str}]")
        
        # Add exception info if present
        if record.exc_info:
            parts.append(f"[exception={self.formatException(record.exc_info)}]")
        
        return " ".join(parts)


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted log message
        """
        # Build log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add context if available
        context = getattr(record, 'context', {})
        if context:
            log_entry["context"] = context
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info', 'context'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record
            
        Returns:
            Colored formatted log message
        """
        # Get color for level
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Build message
        message = record.getMessage()
        
        # Get context if available
        context = getattr(record, 'context', {})
        context_str = ""
        if context:
            context_str = f" [{' '.join([f'{k}={v}' for k, v in context.items()])}]"
        
        # Format final message
        formatted = f"{color}[{timestamp}] [{record.levelname:8}] [{record.name}]{reset} {message}{context_str}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted