"""
Custom exception classes for AI Karen engine.
"""

from typing import Any, Dict, Optional


class KarenError(Exception):
    """
    Base exception class for all AI Karen errors.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "KAREN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }


class ValidationError(KarenError):
    """Raised when input validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field
        self.value = value
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["value"] = str(value)


class AuthenticationError(KarenError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(KarenError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class NotFoundError(KarenError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "NOT_FOUND", details)
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id:
            self.details["resource_id"] = resource_id


class ServiceError(KarenError):
    """Raised when a service operation fails."""
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "SERVICE_ERROR", details)
        self.service_name = service_name
        self.operation = operation
        if service_name:
            self.details["service_name"] = service_name
        if operation:
            self.details["operation"] = operation


class PluginError(KarenError):
    """Raised when plugin execution fails."""
    
    def __init__(
        self, 
        message: str, 
        plugin_name: Optional[str] = None,
        plugin_version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "PLUGIN_ERROR", details)
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version
        if plugin_name:
            self.details["plugin_name"] = plugin_name
        if plugin_version:
            self.details["plugin_version"] = plugin_version


class MemoryError(KarenError):
    """Raised when memory operations fail."""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        memory_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "MEMORY_ERROR", details)
        self.operation = operation
        self.memory_id = memory_id
        if operation:
            self.details["operation"] = operation
        if memory_id:
            self.details["memory_id"] = memory_id


class AIProcessingError(KarenError):
    """Raised when AI processing fails."""
    
    def __init__(
        self, 
        message: str, 
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "AI_PROCESSING_ERROR", details)
        self.model = model
        self.prompt = prompt
        if model:
            self.details["model"] = model
        if prompt:
            self.details["prompt"] = prompt[:100] + "..." if len(prompt) > 100 else prompt


class RateLimitError(KarenError):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded", 
        limit: Optional[int] = None,
        window: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)
        self.limit = limit
        self.window = window
        if limit:
            self.details["limit"] = limit
        if window:
            self.details["window"] = window


class ConfigurationError(KarenError):
    """Raised when configuration is invalid."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_key = config_key
        self.config_value = config_value
        if config_key:
            self.details["config_key"] = config_key
        if config_value is not None:
            self.details["config_value"] = str(config_value)