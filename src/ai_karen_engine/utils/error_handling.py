"""
Comprehensive Error Handling Utilities

Provides centralized error handling for the Model Library system with:
- Network error handling with retry mechanisms
- Disk space and permission error handling
- User-friendly error messages with resolution steps
- Error categorization and logging

This module implements comprehensive error handling as required by task 10.1.
"""

import logging
import os
import shutil
import time
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import requests
from requests.exceptions import (
    RequestException, ConnectionError, Timeout, HTTPError,
    TooManyRedirects, URLRequired, SSLError
)

logger = logging.getLogger("kari.error_handling")

class ErrorCategory(Enum):
    """Error categories for better error handling and user feedback."""
    NETWORK = "network"
    DISK_SPACE = "disk_space"
    PERMISSION = "permission"
    VALIDATION = "validation"
    SECURITY = "security"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    DOWNLOAD = "download"
    FILE_SYSTEM = "file_system"

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorInfo:
    """Comprehensive error information with user-friendly messages."""
    category: ErrorCategory
    severity: ErrorSeverity
    title: str
    message: str
    technical_details: str
    resolution_steps: List[str]
    retry_possible: bool = False
    user_action_required: bool = False
    error_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ModelLibraryError(Exception):
    """Base exception for Model Library operations."""
    
    def __init__(self, error_info: ErrorInfo, original_error: Optional[Exception] = None):
        self.error_info = error_info
        self.original_error = original_error
        super().__init__(error_info.message)

class NetworkError(ModelLibraryError):
    """Network-related errors."""
    pass

class DiskSpaceError(ModelLibraryError):
    """Disk space related errors."""
    pass

class PermissionError(ModelLibraryError):
    """Permission related errors."""
    pass

class ValidationError(ModelLibraryError):
    """Validation related errors."""
    pass

class SecurityError(ModelLibraryError):
    """Security related errors."""
    pass

class ErrorHandler:
    """
    Comprehensive error handler for Model Library operations.
    
    Provides:
    - Network error handling with retry mechanisms
    - Disk space and permission error handling
    - User-friendly error messages with resolution steps
    - Error categorization and logging
    """
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.retry_strategies = self._initialize_retry_strategies()
    
    def _initialize_error_patterns(self) -> Dict[str, ErrorInfo]:
        """Initialize common error patterns with user-friendly messages."""
        return {
            # Network Errors
            "connection_error": ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                title="Connection Failed",
                message="Unable to connect to the model repository. Please check your internet connection.",
                technical_details="Network connection could not be established",
                resolution_steps=[
                    "Check your internet connection",
                    "Verify that the repository URL is accessible",
                    "Try again in a few moments",
                    "Check if you're behind a firewall or proxy"
                ],
                retry_possible=True,
                error_code="NET_001"
            ),
            
            "timeout_error": ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                title="Request Timeout",
                message="The request took too long to complete. The server may be busy.",
                technical_details="Request exceeded timeout limit",
                resolution_steps=[
                    "Try again in a few moments",
                    "Check your internet connection speed",
                    "The server may be experiencing high load"
                ],
                retry_possible=True,
                error_code="NET_002"
            ),
            
            "ssl_error": ErrorInfo(
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.HIGH,
                title="Security Certificate Error",
                message="There's a problem with the security certificate of the model repository.",
                technical_details="SSL certificate verification failed",
                resolution_steps=[
                    "Check your system date and time",
                    "Update your system certificates",
                    "Contact your system administrator if the problem persists"
                ],
                retry_possible=False,
                user_action_required=True,
                error_code="SEC_001"
            ),
            
            "http_error": ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                title="Server Error",
                message="The model repository returned an error. The model may not be available.",
                technical_details="HTTP error response from server",
                resolution_steps=[
                    "Try again later",
                    "Check if the model is still available",
                    "Contact support if the problem persists"
                ],
                retry_possible=True,
                error_code="NET_003"
            ),
            
            # Disk Space Errors
            "insufficient_disk_space": ErrorInfo(
                category=ErrorCategory.DISK_SPACE,
                severity=ErrorSeverity.HIGH,
                title="Insufficient Disk Space",
                message="Not enough disk space available to download the model.",
                technical_details="Available disk space is less than required",
                resolution_steps=[
                    "Free up disk space by deleting unnecessary files",
                    "Remove unused models from the Model Library",
                    "Consider moving the models directory to a drive with more space",
                    "Check disk usage in system settings"
                ],
                retry_possible=True,
                user_action_required=True,
                error_code="DISK_001"
            ),
            
            "disk_write_error": ErrorInfo(
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.HIGH,
                title="Cannot Write to Disk",
                message="Unable to write files to disk. This may be due to permissions or disk issues.",
                technical_details="File write operation failed",
                resolution_steps=[
                    "Check if you have write permissions to the models directory",
                    "Ensure the disk is not full",
                    "Check if the disk is healthy (run disk check)",
                    "Try running the application as administrator"
                ],
                retry_possible=True,
                user_action_required=True,
                error_code="DISK_002"
            ),
            
            # Permission Errors
            "permission_denied": ErrorInfo(
                category=ErrorCategory.PERMISSION,
                severity=ErrorSeverity.HIGH,
                title="Permission Denied",
                message="You don't have permission to access the required files or directories.",
                technical_details="File system permission denied",
                resolution_steps=[
                    "Run the application as administrator",
                    "Check file and directory permissions",
                    "Ensure you have write access to the models directory",
                    "Contact your system administrator"
                ],
                retry_possible=True,
                user_action_required=True,
                error_code="PERM_001"
            ),
            
            # Validation Errors
            "invalid_model_id": ErrorInfo(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                title="Invalid Model",
                message="The specified model was not found or is not available.",
                technical_details="Model ID validation failed",
                resolution_steps=[
                    "Check the model name and try again",
                    "Refresh the model library",
                    "Verify the model is still available"
                ],
                retry_possible=False,
                error_code="VAL_001"
            ),
            
            "checksum_validation_failed": ErrorInfo(
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.HIGH,
                title="File Integrity Check Failed",
                message="The downloaded model file appears to be corrupted or tampered with.",
                technical_details="Checksum validation failed",
                resolution_steps=[
                    "Delete the corrupted file and try downloading again",
                    "Check your internet connection stability",
                    "Contact support if the problem persists"
                ],
                retry_possible=True,
                error_code="SEC_002"
            ),
            
            # Download Errors
            "download_interrupted": ErrorInfo(
                category=ErrorCategory.DOWNLOAD,
                severity=ErrorSeverity.MEDIUM,
                title="Download Interrupted",
                message="The download was interrupted and could not be completed.",
                technical_details="Download process was interrupted",
                resolution_steps=[
                    "Try downloading again",
                    "Check your internet connection",
                    "Ensure your computer doesn't go to sleep during downloads"
                ],
                retry_possible=True,
                error_code="DL_001"
            ),
            
            "download_corrupted": ErrorInfo(
                category=ErrorCategory.DOWNLOAD,
                severity=ErrorSeverity.HIGH,
                title="Download Corrupted",
                message="The downloaded file appears to be corrupted.",
                technical_details="Downloaded file failed integrity checks",
                resolution_steps=[
                    "Delete the corrupted file",
                    "Try downloading again",
                    "Check your internet connection stability",
                    "Contact support if the problem persists"
                ],
                retry_possible=True,
                error_code="DL_002"
            )
        }
    
    def _initialize_retry_strategies(self) -> Dict[ErrorCategory, Dict[str, Any]]:
        """Initialize retry strategies for different error categories."""
        return {
            ErrorCategory.NETWORK: {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "backoff_factor": 2.0,
                "jitter": True
            },
            ErrorCategory.DOWNLOAD: {
                "max_retries": 5,
                "base_delay": 2.0,
                "max_delay": 120.0,
                "backoff_factor": 2.0,
                "jitter": True
            },
            ErrorCategory.DISK_SPACE: {
                "max_retries": 1,
                "base_delay": 5.0,
                "max_delay": 5.0,
                "backoff_factor": 1.0,
                "jitter": False
            },
            ErrorCategory.PERMISSION: {
                "max_retries": 2,
                "base_delay": 1.0,
                "max_delay": 5.0,
                "backoff_factor": 1.5,
                "jitter": False
            }
        }
    
    def handle_network_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Handle network-related errors with specific error types."""
        if isinstance(error, SSLError):
            error_info = replace(self.error_patterns["ssl_error"])
        elif isinstance(error, ConnectionError):
            error_info = replace(self.error_patterns["connection_error"])
        elif isinstance(error, Timeout):
            error_info = replace(self.error_patterns["timeout_error"])
        elif isinstance(error, HTTPError):
            error_info = replace(self.error_patterns["http_error"])
            # Add HTTP status code to message
            if hasattr(error, 'response') and error.response:
                status_code = error.response.status_code
                error_info = replace(error_info, 
                    message=error_info.message + f" (HTTP {status_code})",
                    technical_details=error_info.technical_details + f" - Status code: {status_code}"
                )
        else:
            # Generic network error
            error_info = ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                title="Network Error",
                message="A network error occurred while communicating with the server.",
                technical_details=str(error),
                resolution_steps=[
                    "Check your internet connection",
                    "Try again in a few moments",
                    "Contact support if the problem persists"
                ],
                retry_possible=True,
                error_code="NET_999"
            )
        
        error_info = replace(error_info,
            context=context or {},
            technical_details=error_info.technical_details + f" - Original error: {str(error)}"
        )
        
        logger.error(f"Network error: {error_info.title} - {error_info.message}", 
                    extra={"error_code": error_info.error_code, "context": context})
        
        return error_info
    
    def handle_disk_space_error(self, required_space: int, available_space: int, 
                               path: str, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Handle disk space related errors."""
        # Add specific space information
        required_gb = required_space / (1024**3)
        available_gb = available_space / (1024**3)
        
        error_info = replace(self.error_patterns["insufficient_disk_space"],
            message=(
                f"Not enough disk space available. Required: {required_gb:.2f}GB, "
                f"Available: {available_gb:.2f}GB"
            ),
            technical_details=(
                f"Required space: {required_space} bytes, Available space: {available_space} bytes, "
                f"Path: {path}"
            ),
            context={
                "required_space": required_space,
                "available_space": available_space,
                "path": path,
                **(context or {})
            }
        )
        
        logger.error(f"Disk space error: {error_info.message}", 
                    extra={"error_code": error_info.error_code, "context": error_info.context})
        
        return error_info
    
    def handle_permission_error(self, path: str, operation: str, 
                               context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Handle permission related errors."""
        error_info = replace(self.error_patterns["permission_denied"],
            message=f"Permission denied when trying to {operation} '{path}'",
            technical_details=f"Operation: {operation}, Path: {path}",
            context={
                "path": path,
                "operation": operation,
                **(context or {})
            }
        )
        
        logger.error(f"Permission error: {error_info.message}", 
                    extra={"error_code": error_info.error_code, "context": error_info.context})
        
        return error_info
    
    def handle_validation_error(self, validation_type: str, details: str,
                               context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Handle validation related errors."""
        if validation_type == "model_id":
            error_info = replace(self.error_patterns["invalid_model_id"])
        elif validation_type == "checksum":
            error_info = replace(self.error_patterns["checksum_validation_failed"])
        else:
            error_info = ErrorInfo(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                title="Validation Error",
                message=f"Validation failed: {details}",
                technical_details=f"Validation type: {validation_type}, Details: {details}",
                resolution_steps=[
                    "Check the input and try again",
                    "Refresh the data and retry",
                    "Contact support if the problem persists"
                ],
                retry_possible=False,
                error_code="VAL_999"
            )
        
        error_info = replace(error_info,
            context={
                "validation_type": validation_type,
                "details": details,
                **(context or {})
            }
        )
        
        logger.error(f"Validation error: {error_info.message}", 
                    extra={"error_code": error_info.error_code, "context": error_info.context})
        
        return error_info
    
    def handle_download_error(self, error_type: str, details: str,
                             context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Handle download related errors."""
        if error_type == "interrupted":
            error_info = replace(self.error_patterns["download_interrupted"])
        elif error_type == "corrupted":
            error_info = replace(self.error_patterns["download_corrupted"])
        else:
            error_info = ErrorInfo(
                category=ErrorCategory.DOWNLOAD,
                severity=ErrorSeverity.MEDIUM,
                title="Download Error",
                message=f"Download failed: {details}",
                technical_details=f"Error type: {error_type}, Details: {details}",
                resolution_steps=[
                    "Try downloading again",
                    "Check your internet connection",
                    "Contact support if the problem persists"
                ],
                retry_possible=True,
                error_code="DL_999"
            )
        
        error_info = replace(error_info,
            context={
                "error_type": error_type,
                "details": details,
                **(context or {})
            }
        )
        
        logger.error(f"Download error: {error_info.message}", 
                    extra={"error_code": error_info.error_code, "context": error_info.context})
        
        return error_info
    
    def should_retry(self, error_info: ErrorInfo, attempt: int) -> bool:
        """Determine if an operation should be retried based on error info and attempt count."""
        if not error_info.retry_possible:
            return False
        
        strategy = self.retry_strategies.get(error_info.category)
        if not strategy:
            return False
        
        return attempt < strategy["max_retries"]
    
    def calculate_retry_delay(self, error_info: ErrorInfo, attempt: int) -> float:
        """Calculate delay before retry using exponential backoff."""
        strategy = self.retry_strategies.get(error_info.category)
        if not strategy:
            return 1.0
        
        delay = strategy["base_delay"] * (strategy["backoff_factor"] ** attempt)
        delay = min(delay, strategy["max_delay"])
        
        # Add jitter to prevent thundering herd
        if strategy.get("jitter", False):
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def execute_with_retry(self, operation: Callable, error_handler: Callable[[Exception], ErrorInfo],
                          context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute an operation with automatic retry logic."""
        attempt = 0
        last_error_info = None
        
        while True:
            try:
                return operation()
            except Exception as e:
                error_info = error_handler(e)
                last_error_info = error_info
                
                if not self.should_retry(error_info, attempt):
                    logger.error(f"Operation failed after {attempt + 1} attempts: {error_info.message}")
                    raise ModelLibraryError(error_info, e)
                
                delay = self.calculate_retry_delay(error_info, attempt)
                logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {error_info.message}")
                
                time.sleep(delay)
                attempt += 1
    
    def validate_disk_space(self, path: Union[str, Path], required_space: int) -> None:
        """Validate available disk space and raise appropriate error if insufficient."""
        try:
            path = Path(path)
            stat = shutil.disk_usage(path)
            available_space = stat.free
            
            # Add 15% buffer for safety
            required_with_buffer = int(required_space * 1.15)
            
            if available_space < required_with_buffer:
                error_info = self.handle_disk_space_error(
                    required_with_buffer, available_space, str(path)
                )
                raise DiskSpaceError(error_info)
                
        except OSError as e:
            error_info = self.handle_permission_error(str(path), "check disk space")
            raise PermissionError(error_info, e)
    
    def validate_file_permissions(self, path: Union[str, Path], operation: str = "access") -> None:
        """Validate file permissions and raise appropriate error if insufficient."""
        try:
            path = Path(path)
            
            if operation == "write":
                # Check if we can write to the directory
                if path.is_file():
                    parent_dir = path.parent
                else:
                    parent_dir = path
                
                if not os.access(parent_dir, os.W_OK):
                    error_info = self.handle_permission_error(str(path), "write to")
                    raise PermissionError(error_info)
            
            elif operation == "read":
                if not os.access(path, os.R_OK):
                    error_info = self.handle_permission_error(str(path), "read from")
                    raise PermissionError(error_info)
            
        except OSError as e:
            error_info = self.handle_permission_error(str(path), operation)
            raise PermissionError(error_info, e)
    
    def create_error_response(self, error_info: ErrorInfo) -> Dict[str, Any]:
        """Create a standardized error response for API endpoints."""
        return {
            "error": True,
            "error_code": error_info.error_code,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "title": error_info.title,
            "message": error_info.message,
            "technical_details": error_info.technical_details,
            "resolution_steps": error_info.resolution_steps,
            "retry_possible": error_info.retry_possible,
            "user_action_required": error_info.user_action_required,
            "context": error_info.context or {}
        }

# Global error handler instance
error_handler = ErrorHandler()

# Convenience functions for common error handling patterns
def handle_network_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
    """Convenience function for handling network errors."""
    return error_handler.handle_network_error(error, context)

def handle_disk_space_error(required_space: int, available_space: int, 
                           path: str, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
    """Convenience function for handling disk space errors."""
    return error_handler.handle_disk_space_error(required_space, available_space, path, context)

def handle_permission_error(path: str, operation: str, 
                           context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
    """Convenience function for handling permission errors."""
    return error_handler.handle_permission_error(path, operation, context)

def handle_validation_error(validation_type: str, details: str,
                           context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
    """Convenience function for handling validation errors."""
    return error_handler.handle_validation_error(validation_type, details, context)

def handle_download_error(error_type: str, details: str,
                         context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
    """Convenience function for handling download errors."""
    return error_handler.handle_download_error(error_type, details, context)

def validate_disk_space(path: Union[str, Path], required_space: int) -> None:
    """Convenience function for validating disk space."""
    error_handler.validate_disk_space(path, required_space)

def validate_file_permissions(path: Union[str, Path], operation: str = "access") -> None:
    """Convenience function for validating file permissions."""
    error_handler.validate_file_permissions(path, operation)

def execute_with_retry(operation: Callable, error_handler_func: Callable[[Exception], ErrorInfo],
                      context: Optional[Dict[str, Any]] = None) -> Any:
    """Convenience function for executing operations with retry logic."""
    return error_handler.execute_with_retry(operation, error_handler_func, context)