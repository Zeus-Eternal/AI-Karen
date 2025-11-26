"""
Error handling and exceptions for the KARI extension system.

This module defines the exception hierarchy and error handling strategies
used throughout the extension system.
"""

from __future__ import annotations

import asyncio
import traceback
from typing import Any, Dict, Optional


class ExtensionError(Exception):
    """Base exception for extension-related errors."""
    
    def __init__(self, message: str, extension_id: Optional[str] = None, **kwargs):
        self.extension_id = extension_id
        self.details = kwargs
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "extension_id": self.extension_id,
            "details": self.details,
            "traceback": traceback.format_exc(),
        }


class ExtensionLoadError(ExtensionError):
    """Exception raised when an extension fails to load."""
    pass


class ExtensionValidationError(ExtensionError):
    """Exception raised when an extension fails validation."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None, **kwargs):
        self.validation_errors = validation_errors or []
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["validation_errors"] = self.validation_errors
        return result


class ExtensionExecutionError(ExtensionError):
    """Exception raised when an extension fails during execution."""
    
    def __init__(self, message: str, hook_point: Optional[str] = None, **kwargs):
        self.hook_point = hook_point
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["hook_point"] = self.hook_point
        return result


class ExtensionTimeoutError(ExtensionExecutionError):
    """Exception raised when an extension execution times out."""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, **kwargs):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["timeout_seconds"] = self.timeout_seconds
        return result


class ExtensionPermissionError(ExtensionError):
    """Exception raised when an extension lacks required permissions."""
    
    def __init__(self, message: str, required_permission: Optional[str] = None, **kwargs):
        self.required_permission = required_permission
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["required_permission"] = self.required_permission
        return result


class ExtensionRBACError(ExtensionError):
    """Exception raised when an extension RBAC check fails."""
    
    def __init__(self, message: str, required_role: Optional[str] = None, **kwargs):
        self.required_role = required_role
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["required_role"] = self.required_role
        return result


class ExtensionManifestError(ExtensionError):
    """Exception raised when there's an error in the extension manifest."""
    
    def __init__(self, message: str, manifest_path: Optional[str] = None, **kwargs):
        self.manifest_path = manifest_path
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["manifest_path"] = self.manifest_path
        return result


class ExtensionHookError(ExtensionExecutionError):
    """Exception raised when there's an error in hook execution."""
    
    def __init__(self, message: str, hook_name: Optional[str] = None, **kwargs):
        self.hook_name = hook_name
        super().__init__(message, hook_point=hook_name, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["hook_name"] = self.hook_name
        return result


class ExtensionDependencyError(ExtensionError):
    """Exception raised when there's an error with extension dependencies."""
    
    def __init__(self, message: str, missing_dependencies: Optional[list] = None, **kwargs):
        self.missing_dependencies = missing_dependencies or []
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["missing_dependencies"] = self.missing_dependencies
        return result


class ExtensionConfigurationError(ExtensionError):
    """Exception raised when there's an error in extension configuration."""
    
    def __init__(self, message: str, configuration_errors: Optional[list] = None, **kwargs):
        self.configuration_errors = configuration_errors or []
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["configuration_errors"] = self.configuration_errors
        return result


class ExtensionSystemError(ExtensionError):
    """Exception raised when there's a system-level error in the extension system."""
    pass


class ExtensionRegistryError(ExtensionSystemError):
    """Exception raised when there's an error in the extension registry."""
    
    def __init__(self, message: str, registry_operation: Optional[str] = None, **kwargs):
        self.registry_operation = registry_operation
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["registry_operation"] = self.registry_operation
        return result


class ExtensionDiscoveryError(ExtensionSystemError):
    """Exception raised when there's an error in extension discovery."""
    
    def __init__(self, message: str, discovery_path: Optional[str] = None, **kwargs):
        self.discovery_path = discovery_path
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["discovery_path"] = self.discovery_path
        return result


class ExtensionNotFoundError(ExtensionError):
    """Raised when an extension directory or file is not found."""
    
    def __init__(self, message: str, path: Optional[str] = None, **kwargs):
        self.path = path
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        result = super().to_dict()
        result["path"] = self.path
        return result


def format_extension_error(error: Exception) -> Dict[str, Any]:
    """
    Format an extension error for logging and API responses.
    
    Args:
        error: The exception to format
        
    Returns:
        A dictionary containing formatted error information
    """
    if isinstance(error, ExtensionError):
        return error.to_dict()
    else:
        return {
            "error_type": error.__class__.__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }


def safe_extension_operation(operation_name: str, extension_id: Optional[str] = None):
    """
    Decorator to safely execute extension operations and handle exceptions.
    
    Args:
        operation_name: Name of the operation for logging
        extension_id: ID of the extension being operated on
        
    Returns:
        A decorator function
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ExtensionError:
                # Re-raise extension errors as they are already properly formatted
                raise
            except Exception as e:
                # Convert other exceptions to ExtensionExecutionError
                raise ExtensionExecutionError(
                    f"Unexpected error during {operation_name}: {str(e)}",
                    extension_id=extension_id
                ) from e
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ExtensionError:
                # Re-raise extension errors as they are already properly formatted
                raise
            except Exception as e:
                # Convert other exceptions to ExtensionExecutionError
                raise ExtensionExecutionError(
                    f"Unexpected error during {operation_name}: {str(e)}",
                    extension_id=extension_id
                ) from e
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator