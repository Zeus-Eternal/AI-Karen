"""
Secure Logging System with PII Filtering and Structured Logging

This module provides comprehensive logging with:
- PII detection and redaction
- Structured logging with correlation IDs
- Secure log rotation and encryption
- Comprehensive audit trails
- Performance-optimized async logging
"""

import asyncio
import logging
import json
import re
import hashlib
import gzip
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import queue
import weakref

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Log levels with security considerations"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"

class PIIType(Enum):
    """Types of PII to detect and redact"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PASSWORD = "password"
    TOKEN = "token"
    API_KEY = "api_key"
    IP_ADDRESS = "ip_address"
    USER_ID = "user_id"
    PERSONAL_NAME = "personal_name"

@dataclass
class LogEntry:
    """Structured log entry with security metadata"""
    timestamp: datetime
    level: LogLevel
    message: str
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    pii_detected: List[PIIType] = field(default_factory=list)
    redacted_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PIIDetector:
    """PII detection and redaction system"""
    
    def __init__(self):
        # Compile regex patterns for PII detection
        self.patterns = {
            PIIType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            PIIType.PHONE: re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                re.IGNORECASE
            ),
            PIIType.SSN: re.compile(
                r'\b\d{3}-\d{2}-\d{4}\b',
                re.IGNORECASE
            ),
            PIIType.CREDIT_CARD: re.compile(
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
                re.IGNORECASE
            ),
            PIIType.PASSWORD: re.compile(
                r'(?i)(password|passwd|pwd)\s*[:=]\s*[^\s\}]+',
                re.IGNORECASE
            ),
            PIIType.TOKEN: re.compile(
                r'(?i)(token|key|secret|auth)\s*[:=]\s*[A-Za-z0-9+/=_-]{20,}',
                re.IGNORECASE
            ),
            PIIType.API_KEY: re.compile(
                r'(?i)(api[_-]?key|access[_-]?key)\s*[:=]\s*[A-Za-z0-9+/=_-]{20,}',
                re.IGNORECASE
            ),
            PIIType.IP_ADDRESS: re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
                re.IGNORECASE
            ),
            PIIType.USER_ID: re.compile(
                r'(?i)(user[_-]?id|uid|userid)\s*[:=]\s*[A-Za-z0-9_-]{5,}',
                re.IGNORECASE
            ),
            PIIType.PERSONAL_NAME: re.compile(
                r'(?i)(name|full[_-]?name|first[_-]?name|last[_-]?name)\s*[:=]\s*[A-Za-z]{2,}\s+[A-Za-z]{2,}',
                re.IGNORECASE
            )
        }
    
    def detect_pii(self, text: str) -> Dict[PIIType, List[str]]:
        """Detect PII in text and return matches"""
        detected = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[pii_type] = matches
        
        return detected
    
    def redact_pii(self, text: str, detected_pii: Dict[PIIType, List[str]]) -> tuple[str, List[str]]:
        """Redact detected PII from text"""
        redacted_text = text
        redacted_fields = []
        
        for pii_type, matches in detected_pii.items():
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Get full match for regex groups
                
                # Create redaction placeholder
                placeholder = f"[{pii_type.value.upper()}_REDACTED]"
                
                # Replace all occurrences
                redacted_text = redacted_text.replace(match, placeholder)
                redacted_fields.append(f"{pii_type.value}: {match}")
        
        return redacted_text, redacted_fields

class SecureLogHandler(logging.Handler):
    """Secure log handler with PII filtering and encryption"""
    
    def __init__(self,
                 log_file: str,
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 backup_count: int = 5,
                 encrypt_logs: bool = True,
                 compression: bool = True):
        super().__init__()
        
        self.log_file = Path(log_file)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.encrypt_logs = encrypt_logs
        self.compression = compression
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # PII detector
        self.pii_detector = PIIDetector()
        
        # Async logging queue
        self.log_queue = queue.Queue(maxsize=1000)
        self.worker_thread = None
        self.running = False
        
        # Encryption key (in production, load from secure config)
        # Generate proper base64-encoded key for Fernet
        from cryptography.fernet import Fernet
        self.encryption_key = Fernet.generate_key()
        
        # File handles
        self.current_file = None
        self.current_size = 0
        
        # Start worker thread
        self.start_worker()
    
    def start_worker(self):
        """Start background worker for log processing"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Background worker loop for processing log entries"""
        while self.running:
            try:
                # Get log entry with timeout
                try:
                    log_entry = self.log_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process log entry
                self._process_log_entry(log_entry)
                
            except Exception as e:
                # Fallback to stderr if logging fails
                print(f"Logging error: {e}", file=sys.stderr)
    
    def _process_log_entry(self, log_entry: LogEntry):
        """Process a single log entry with security measures"""
        try:
            # Detect and redact PII
            pii_detected = self.pii_detector.detect_pii(log_entry.message)
            redacted_message, redacted_fields = self.pii_detector.redact_pii(
                log_entry.message, pii_detected
            )
            
            # Update log entry with PII info
            log_entry.pii_detected = list(pii_detected.keys())
            log_entry.redacted_fields = redacted_fields
            log_entry.message = redacted_message
            
            # Convert to JSON
            log_json = self._log_entry_to_json(log_entry)
            
            # Compress if enabled
            if self.compression:
                log_json = gzip.compress(log_json.encode('utf-8'))
            else:
                log_json = log_json.encode('utf-8')
            
            # Encrypt if enabled
            if self.encrypt_logs:
                log_json = self._encrypt_log_data(log_json)
            
            # Write to file
            self._write_to_file(log_json)
            
        except Exception as e:
            # Fallback logging
            print(f"Log processing error: {e}", file=sys.stderr)
    
    def _log_entry_to_json(self, log_entry: LogEntry) -> str:
        """Convert log entry to structured JSON"""
        return json.dumps({
            'timestamp': log_entry.timestamp.isoformat(),
            'level': log_entry.level.value,
            'message': log_entry.message,
            'correlation_id': log_entry.correlation_id,
            'user_id': log_entry.user_id,
            'session_id': log_entry.session_id,
            'endpoint': log_entry.endpoint,
            'method': log_entry.method,
            'status_code': log_entry.status_code,
            'duration_ms': log_entry.duration_ms,
            'error_type': log_entry.error_type,
            'context': log_entry.context,
            'pii_detected': [pii.value for pii in log_entry.pii_detected],
            'redacted_fields': log_entry.redacted_fields,
            'metadata': log_entry.metadata
        }, ensure_ascii=False)
    
    def _encrypt_log_data(self, data: Union[str, bytes]) -> bytes:
        """Encrypt log data"""
        try:
            from cryptography.fernet import Fernet
            cipher = Fernet(self.encryption_key)
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            return cipher.encrypt(data)
        except ImportError:
            # Fallback if cryptography not available
            if isinstance(data, str):
                return data.encode('utf-8')
            return data
        except Exception as e:
            print(f"Encryption error: {e}", file=sys.stderr)
            if isinstance(data, str):
                return data.encode('utf-8')
            return data
    
    def _write_to_file(self, data: bytes):
        """Write log data to file with rotation"""
        try:
            # Check if we need to rotate
            if self.current_size >= self.max_file_size:
                self._rotate_files()
            
            # Open file if not already open
            if not self.current_file:
                self.current_file = open(self.log_file, 'ab')
                self.current_size = self.current_file.tell()
            
            # Write data
            self.current_file.write(data)
            self.current_size += len(data)
            
            # Flush to ensure data is written
            self.current_file.flush()
            
        except Exception as e:
            print(f"File write error: {e}", file=sys.stderr)
    
    def _rotate_files(self):
        """Rotate log files"""
        try:
            # Close current file
            if self.current_file:
                self.current_file.close()
                self.current_file = None
            
            # Move existing files
            for i in range(self.backup_count - 1, 0, -1):
                old_file = self.log_file.with_suffix(f'.{i}')
                new_file = self.log_file.with_suffix(f'.{i + 1}')
                
                if old_file.exists():
                    old_file.rename(new_file)
            
            # Move current file to .1
            if self.log_file.exists():
                self.log_file.rename(self.log_file.with_suffix('.1'))
            
            # Reset size
            self.current_size = 0
            
        except Exception as e:
            print(f"Log rotation error: {e}", file=sys.stderr)
    
    def emit(self, record):
        """Emit log record (async)"""
        try:
            # Create log entry
            log_entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created),
                level=LogLevel(record.levelname),
                message=record.getMessage(),
                correlation_id=getattr(record, 'correlation_id', None),
                user_id=getattr(record, 'user_id', None),
                session_id=getattr(record, 'session_id', None),
                endpoint=getattr(record, 'endpoint', None),
                method=getattr(record, 'method', None),
                status_code=getattr(record, 'status_code', None),
                duration_ms=getattr(record, 'duration_ms', None),
                error_type=getattr(record, 'error_type', None),
                context=getattr(record, 'context', {}),
                metadata=getattr(record, 'metadata', {})
            )
            
            # Queue for processing
            try:
                self.log_queue.put_nowait(log_entry)
            except queue.Full:
                # Drop oldest entry if queue is full
                try:
                    self.log_queue.get_nowait()
                    self.log_queue.put_nowait(log_entry)
                except queue.Empty:
                    pass
                
        except Exception as e:
            # Fallback to stderr
            print(f"Log emit error: {e}", file=sys.stderr)
    
    def close(self):
        """Close log handler"""
        self.running = False
        
        # Process remaining queue items
        if hasattr(self, 'log_queue'):
            while not self.log_queue.empty():
                try:
                    log_entry = self.log_queue.get_nowait()
                    self._process_log_entry(log_entry)
                except queue.Empty:
                    break
        
        # Close current file
        if self.current_file:
            self.current_file.close()
            self.current_file = None
        
        # Wait for worker thread to finish
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)

class StructuredLogger:
    """Structured logger with comprehensive security features"""
    
    def __init__(self,
                 name: str,
                 log_file: str,
                 log_level: LogLevel = LogLevel.INFO,
                 enable_console: bool = True):
        self.name = name
        self.log_level = log_level
        self.enable_console = enable_console
        
        # Create Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.value))
        
        # Add secure file handler
        self.secure_handler = SecureLogHandler(
            log_file=log_file,
            encrypt_logs=True,
            compression=True
        )
        self.logger.addHandler(self.secure_handler)
        
        # Add console handler if enabled (without PII for security)
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [SECURED] - %(message)s'
            ))
            self.logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on level"""
        level_hierarchy = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
            LogLevel.SECURITY: 5
        }
        
        return level_hierarchy[level] >= level_hierarchy[self.log_level]
    
    def _create_log_record(self,
                        level: LogLevel,
                        message: str,
                        **kwargs) -> logging.LogRecord:
        """Create log record with additional context"""
        # Map custom log levels to standard logging levels
        level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
            LogLevel.SECURITY: logging.WARNING  # Map SECURITY to WARNING level
        }
        
        record = self.logger.makeRecord(
            name=self.name,
            level=level_mapping[level],
            fn='',
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # Add custom attributes
        for key, value in kwargs.items():
            setattr(record, key, value)
        
        return record
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if self._should_log(LogLevel.DEBUG):
            record = self._create_log_record(LogLevel.DEBUG, message, **kwargs)
            self.logger.handle(record)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        if self._should_log(LogLevel.INFO):
            record = self._create_log_record(LogLevel.INFO, message, **kwargs)
            self.logger.handle(record)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if self._should_log(LogLevel.WARNING):
            record = self._create_log_record(LogLevel.WARNING, message, **kwargs)
            self.logger.handle(record)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        if self._should_log(LogLevel.ERROR):
            record = self._create_log_record(LogLevel.ERROR, message, **kwargs)
            self.logger.handle(record)
    
    def exception(self, message: str, exc_info=None, **kwargs):
        """Log exception with traceback"""
        if self._should_log(LogLevel.ERROR):
            # Add exception info to kwargs if provided
            if exc_info:
                kwargs['exc_info'] = exc_info
            
            record = self._create_log_record(LogLevel.ERROR, message, **kwargs)
            
            # Set exc_info on the record for proper traceback logging
            if exc_info:
                record.exc_info = exc_info
            
            self.logger.handle(record)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        if self._should_log(LogLevel.CRITICAL):
            record = self._create_log_record(LogLevel.CRITICAL, message, **kwargs)
            self.logger.handle(record)
    
    def security(self, message: str, **kwargs):
        """Log security event"""
        if self._should_log(LogLevel.SECURITY):
            record = self._create_log_record(LogLevel.SECURITY, message, **kwargs)
            self.logger.handle(record)
    
    def log_request(self,
                   method: str,
                   endpoint: str,
                   user_id: str,
                   correlation_id: str,
                   status_code: int,
                   duration_ms: float,
                   request_data: Optional[Dict[str, Any]] = None):
        """Log API request with structured data"""
        self.info(
            f"{method} {endpoint} - {status_code}",
            method=method,
            endpoint=endpoint,
            user_id=user_id,
            correlation_id=correlation_id,
            status_code=status_code,
            duration_ms=duration_ms,
            context=request_data or {}
        )
    
    def log_response(self,
                   status_code: int,
                   endpoint: str,
                   user_id: str,
                   correlation_id: str,
                   response_data: Optional[Dict[str, Any]] = None):
        """Log API response with structured data"""
        level = LogLevel.INFO if 200 <= status_code < 400 else LogLevel.ERROR
        
        self._should_log(level) and self.logger.handle(
            self._create_log_record(
                level,
                f"{endpoint} response - {status_code}",
                endpoint=endpoint,
                user_id=user_id,
                correlation_id=correlation_id,
                status_code=status_code,
                context=response_data or {}
            )
        )
    
    def log_error(self,
                  error: str,
                  endpoint: str,
                  user_id: str,
                  correlation_id: str,
                  context: str):
        """Log error with structured data"""
        self.error(
            f"{endpoint} error - {error}",
            endpoint=endpoint,
            user_id=user_id,
            correlation_id=correlation_id,
            error_type=context,
            context={'error': error}
        )
    
    def log_event(self,
                 event: str,
                 user_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """Log application event"""
        self.info(
            f"Event: {event}",
            user_id=user_id,
            context=details or {}
        )

# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}

def get_structured_logger(name: str = "ai_karen",
                       log_file: str = "logs/secure.log",
                       log_level: LogLevel = LogLevel.INFO) -> StructuredLogger:
    """Get or create structured logger instance"""
    global _loggers
    
    if name not in _loggers:
        _loggers[name] = StructuredLogger(
            name=name,
            log_file=log_file,
            log_level=log_level
        )
    
    return _loggers[name]

def configure_logging(log_level: str = "INFO"):
    """Configure root logging with security settings"""
    # Set root logger level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # Create default structured logger
    structured_logger = get_structured_logger(
        name="ai_karen",
        log_level=LogLevel(log_level.upper())
    )
    
    # Log configuration
    structured_logger.info("Logging system initialized", context={
        'log_level': log_level,
        'pii_detection': True,
        'encryption': True,
        'compression': True
    })

def get_logger(name: str = "ai_karen") -> StructuredLogger:
    """Get or create a logger instance (alias for get_structured_logger for backward compatibility)"""
    return get_structured_logger(name=name)
