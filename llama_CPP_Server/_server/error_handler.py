#!/usr/bin/env python3
"""
Comprehensive error handling and user guidance for llama.cpp server

This module provides centralized error handling, logging, and user guidance
for all components of the llama.cpp server.
"""

import os
import sys
import logging
import traceback
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class ErrorLevel(Enum):
    """Error severity levels"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class ErrorCategory(Enum):
    """Error categories"""
    SYSTEM = 0
    NETWORK = 1
    FILESYSTEM = 2
    CONFIGURATION = 3
    MODEL = 4
    INSTALLATION = 5
    PERMISSION = 6
    SECURITY = 7
    UNKNOWN = 8


@dataclass
class ErrorInfo:
    """Structured error information"""
    level: ErrorLevel
    category: ErrorCategory
    code: str
    message: str
    details: Optional[str] = None
    resolution: Optional[str] = None
    timestamp: Optional[datetime] = None
    traceback: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ErrorHandler:
    """Centralized error handling and user guidance"""
    
    # Error code prefixes by category
    ERROR_CODE_PREFIXES = {
        ErrorCategory.SYSTEM: "SYS",
        ErrorCategory.NETWORK: "NET",
        ErrorCategory.FILESYSTEM: "FS",
        ErrorCategory.CONFIGURATION: "CFG",
        ErrorCategory.MODEL: "MDL",
        ErrorCategory.INSTALLATION: "INS",
        ErrorCategory.PERMISSION: "PERM",
        ErrorCategory.SECURITY: "SEC",
        ErrorCategory.UNKNOWN: "UNK"
    }
    
    # Error messages and resolutions
    ERROR_DATABASE = {
        # System errors
        "SYS001": {
            "message": "Insufficient system resources",
            "resolution": "Close other applications or upgrade your system resources"
        },
        "SYS002": {
            "message": "Unsupported operating system",
            "resolution": "Your operating system is not supported. Please use a supported OS"
        },
        "SYS003": {
            "message": "Python version not supported",
            "resolution": "Please install Python 3.8 or higher"
        },
        
        # Network errors
        "NET001": {
            "message": "Connection refused",
            "resolution": "Check if the server is running and accessible"
        },
        "NET002": {
            "message": "Connection timeout",
            "resolution": "Check your network connection and try again"
        },
        "NET003": {
            "message": "DNS resolution failed",
            "resolution": "Check your DNS settings and network connection"
        },
        
        # Filesystem errors
        "FS001": {
            "message": "File not found",
            "resolution": "Check if the file exists and the path is correct"
        },
        "FS002": {
            "message": "Permission denied",
            "resolution": "Check file permissions and run with appropriate privileges"
        },
        "FS003": {
            "message": "Insufficient disk space",
            "resolution": "Free up disk space or choose a different location"
        },
        
        # Configuration errors
        "CFG001": {
            "message": "Invalid configuration",
            "resolution": "Check your configuration file for errors"
        },
        "CFG002": {
            "message": "Missing required configuration",
            "resolution": "Provide all required configuration values"
        },
        "CFG003": {
            "message": "Configuration file not found",
            "resolution": "Create a configuration file or use default settings"
        },
        
        # Model errors
        "MDL001": {
            "message": "Model not found",
            "resolution": "Check if the model file exists and the path is correct"
        },
        "MDL002": {
            "message": "Invalid model format",
            "resolution": "Use a valid GGUF model format"
        },
        "MDL003": {
            "message": "Model loading failed",
            "resolution": "Check if the model is compatible and not corrupted"
        },
        
        # Installation errors
        "INS001": {
            "message": "Installation failed",
            "resolution": "Check installation logs and try again"
        },
        "INS002": {
            "message": "Dependencies not found",
            "resolution": "Install required dependencies before proceeding"
        },
        "INS003": {
            "message": "Virtual environment creation failed",
            "resolution": "Check permissions and available disk space"
        },
        
        # Permission errors
        "PERM001": {
            "message": "Insufficient privileges",
            "resolution": "Run with appropriate privileges or change file permissions"
        },
        "PERM002": {
            "message": "Access denied",
            "resolution": "Check file permissions and ownership"
        },
        
        # Security errors
        "SEC001": {
            "message": "Authentication failed",
            "resolution": "Check your credentials and try again"
        },
        "SEC002": {
            "message": "Authorization failed",
            "resolution": "You do not have permission to perform this action"
        },
        "SEC003": {
            "message": "Invalid API key",
            "resolution": "Check your API key and ensure it has the required permissions"
        },
        "SEC004": {
            "message": "JWT token expired",
            "resolution": "Refresh your token or log in again"
        },
        "SEC005": {
            "message": "Account locked",
            "resolution": "Your account has been locked due to too many failed login attempts"
        },
        "SEC006": {
            "message": "Rate limit exceeded",
            "resolution": "Too many requests. Please wait and try again later"
        },
        "SEC007": {
            "message": "IP address blocked",
            "resolution": "Your IP address has been blocked by security policies"
        },
        "SEC008": {
            "message": "Invalid encryption key",
            "resolution": "The encryption key is invalid or corrupted"
        }
    }
    
    def __init__(self, log_file: Optional[Union[str, Path]] = None):
        """Initialize the error handler
        
        Args:
            log_file: Path to log file. If None, logs to console only.
        """
        self.log_file = Path(log_file) if log_file else None
        self.error_history: List[ErrorInfo] = []
        self.custom_handlers: Dict[str, Callable] = {}
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging configuration"""
        # Create log directory if needed
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.log_file) if self.log_file else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger("llama_cpp_server")
    
    def _format_error_code(self, category: ErrorCategory, code: str) -> str:
        """Format error code with category prefix"""
        prefix = self.ERROR_CODE_PREFIXES.get(category, "UNK")
        return f"{prefix}{code}"
    
    def _get_error_info(self, error_code: str) -> Dict[str, str]:
        """Get error information from database"""
        return self.ERROR_DATABASE.get(error_code, {
            "message": "Unknown error",
            "resolution": "Contact support for assistance"
        })
    
    def _capture_traceback(self) -> str:
        """Capture current traceback"""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type and exc_value and exc_traceback:
            return "".join(traceback.format_exception(
                exc_type, exc_value, exc_traceback
            ))
        return ""
    
    def handle_error(
        self,
        category: ErrorCategory,
        code: str,
        details: Optional[str] = None,
        level: ErrorLevel = ErrorLevel.ERROR,
        include_traceback: bool = True
    ) -> ErrorInfo:
        """Handle an error with logging and user guidance
        
        Args:
            category: Error category
            code: Error code (without prefix)
            details: Additional error details
            level: Error severity level
            include_traceback: Whether to include traceback information
            
        Returns:
            ErrorInfo object with structured error information
        """
        # Format error code
        error_code = self._format_error_code(category, code)
        
        # Get error information from database
        error_info = self._get_error_info(error_code)
        
        # Create ErrorInfo object
        error = ErrorInfo(
            level=level,
            category=category,
            code=error_code,
            message=error_info["message"],
            details=details,
            resolution=error_info["resolution"],
            traceback=self._capture_traceback() if include_traceback else None
        )
        
        # Add to error history
        self.error_history.append(error)
        
        # Log the error
        log_message = f"[{error.code}] {error.message}"
        if details:
            log_message += f" - {details}"
        
        if error.resolution:
            log_message += f" - Resolution: {error.resolution}"
        
        if level == ErrorLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == ErrorLevel.INFO:
            self.logger.info(log_message)
        elif level == ErrorLevel.WARNING:
            self.logger.warning(log_message)
        elif level == ErrorLevel.ERROR:
            self.logger.error(log_message)
        elif level == ErrorLevel.CRITICAL:
            self.logger.critical(log_message)
        
        # Log traceback if available
        if error.traceback:
            self.logger.debug(f"Traceback for {error.code}:\n{error.traceback}")
        
        # Call custom handler if registered
        if error_code in self.custom_handlers:
            try:
                self.custom_handlers[error_code](error)
            except Exception as e:
                self.logger.error(f"Custom error handler failed for {error_code}: {e}")
        
        return error
    
    def register_custom_handler(self, error_code: str, handler: Callable) -> None:
        """Register a custom handler for a specific error code
        
        Args:
            error_code: Error code to handle
            handler: Handler function that takes an ErrorInfo object
        """
        self.custom_handlers[error_code] = handler
    
    def handle_exception(self, exception: Exception) -> ErrorInfo:
        """Handle an exception with appropriate error code
        
        Args:
            exception: Exception to handle
            
        Returns:
            ErrorInfo object with structured error information
        """
        # Determine error category and code based on exception type
        if isinstance(exception, FileNotFoundError):
            return self.handle_error(
                ErrorCategory.FILESYSTEM,
                "FS001",
                str(exception),
                ErrorLevel.ERROR
            )
        elif isinstance(exception, PermissionError):
            return self.handle_error(
                ErrorCategory.PERMISSION,
                "PERM001",
                str(exception),
                ErrorLevel.ERROR
            )
        elif isinstance(exception, ConnectionError):
            return self.handle_error(
                ErrorCategory.NETWORK,
                "NET001",
                str(exception),
                ErrorLevel.ERROR
            )
        elif isinstance(exception, (ValueError, KeyError)):
            return self.handle_error(
                ErrorCategory.CONFIGURATION,
                "CFG001",
                str(exception),
                ErrorLevel.ERROR
            )
        elif isinstance(exception, MemoryError):
            return self.handle_error(
                ErrorCategory.SYSTEM,
                "SYS001",
                str(exception),
                ErrorLevel.CRITICAL
            )
        else:
            # Default handling for unknown exceptions
            return self.handle_error(
                ErrorCategory.UNKNOWN,
                "001",
                f"{type(exception).__name__}: {str(exception)}",
                ErrorLevel.ERROR
            )
    
    def get_user_guidance(self, error_code: str) -> str:
        """Get user guidance for an error code
        
        Args:
            error_code: Error code to get guidance for
            
        Returns:
            User guidance text
        """
        error_info = self._get_error_info(error_code)
        guidance = f"Error: {error_info['message']}\n"
        guidance += f"Resolution: {error_info['resolution']}"
        
        # Add additional guidance based on error code
        if error_code.startswith("CFG"):
            guidance += "\n\nCheck your configuration file for syntax errors and missing values."
        elif error_code.startswith("FS"):
            guidance += "\n\nEnsure file paths are correct and you have appropriate permissions."
        elif error_code.startswith("NET"):
            guidance += "\n\nCheck your network connection and firewall settings."
        elif error_code.startswith("SYS"):
            guidance += "\n\nEnsure your system meets the minimum requirements."
        elif error_code.startswith("MDL"):
            guidance += "\n\nEnsure the model file is a valid GGUF format and not corrupted."
        elif error_code.startswith("INS"):
            guidance += "\n\nCheck installation logs for detailed error information."
        elif error_code.startswith("PERM"):
            guidance += "\n\nRun with appropriate privileges or change file permissions."
        elif error_code.startswith("SEC"):
            guidance += "\n\nCheck your security settings, credentials, and contact your system administrator if the issue persists."
        
        return guidance
    
    def save_error_report(self, file_path: Union[str, Path]) -> bool:
        """Save error report to file
        
        Args:
            file_path: Path to save error report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write("Llama.cpp Server Error Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"System: {platform.system()} {platform.release()}\n")
                f.write(f"Python: {platform.python_version()}\n\n")
                
                f.write("Error History:\n")
                f.write("-" * 20 + "\n")
                
                for error in self.error_history:
                    f.write(f"\n[{error.code}] {error.message}\n")
                    f.write(f"Level: {error.level.name}\n")
                    f.write(f"Category: {error.category.name}\n")
                    f.write(f"Timestamp: {error.timestamp.isoformat()}\n")
                    
                    if error.details:
                        f.write(f"Details: {error.details}\n")
                    
                    if error.resolution:
                        f.write(f"Resolution: {error.resolution}\n")
                    
                    if error.traceback:
                        f.write(f"Traceback:\n{error.traceback}\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save error report: {e}")
            return False
    
    def clear_error_history(self) -> None:
        """Clear error history"""
        self.error_history.clear()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics
        
        Returns:
            Dictionary with error statistics
        """
        stats = {
            "total_errors": len(self.error_history),
            "by_level": {},
            "by_category": {},
            "by_code": {}
        }
        
        for error in self.error_history:
            # Count by level
            level_name = error.level.name
            stats["by_level"][level_name] = stats["by_level"].get(level_name, 0) + 1
            
            # Count by category
            category_name = error.category.name
            stats["by_category"][category_name] = stats["by_category"].get(category_name, 0) + 1
            
            # Count by code
            stats["by_code"][error.code] = stats["by_code"].get(error.code, 0) + 1
        
        return stats


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(
    category: ErrorCategory,
    code: str,
    details: Optional[str] = None,
    level: ErrorLevel = ErrorLevel.ERROR,
    include_traceback: bool = True
) -> ErrorInfo:
    """Global error handling function
    
    Args:
        category: Error category
        code: Error code (without prefix)
        details: Additional error details
        level: Error severity level
        include_traceback: Whether to include traceback information
        
    Returns:
        ErrorInfo object with structured error information
    """
    return error_handler.handle_error(category, code, details, level, include_traceback)


def handle_exception(exception: Exception) -> ErrorInfo:
    """Global exception handling function
    
    Args:
        exception: Exception to handle
        
    Returns:
        ErrorInfo object with structured error information
    """
    return error_handler.handle_exception(exception)


def get_user_guidance(error_code: str) -> str:
    """Get user guidance for an error code
    
    Args:
        error_code: Error code to get guidance for
        
    Returns:
        User guidance text
    """
    return error_handler.get_user_guidance(error_code)