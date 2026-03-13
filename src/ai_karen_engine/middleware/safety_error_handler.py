"""
Safety Error Handler for Safety Middleware.

This module provides error handling functionality for safety operations,
including error classification, recovery strategies, and error reporting.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from src.services.agents.agent_safety_types import SafetyLevel, RiskLevel

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Enum representing error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Enum representing error categories."""
    VALIDATION = "validation"
    AUTHORIZATION = "authorization"
    CONTENT_SAFETY = "content_safety"
    SYSTEM = "system"
    NETWORK = "network"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ErrorAction(str, Enum):
    """Enum representing error actions."""
    LOG = "log"
    WARN = "warn"
    BLOCK = "block"
    RETRY = "retry"
    FALLBACK = "fallback"
    ESCALATE = "escalate"


@dataclass
class SafetyError:
    """Data class for safety errors."""
    
    error_id: str
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    recovery_action: Optional[ErrorAction] = None


@dataclass
class ErrorHandlingStrategy:
    """Data class for error handling strategies."""
    
    error_category: ErrorCategory
    error_type: str
    action: ErrorAction
    max_retries: int = 0
    retry_delay: float = 1.0
    fallback_response: Optional[Dict[str, Any]] = None
    should_log: bool = True
    should_alert: bool = False
    alert_threshold: int = 3  # Number of errors before alerting


class SafetyErrorHandler:
    """
    Safety Error Handler for Safety Middleware.
    
    This class provides error handling functionality for safety operations,
    including error classification, recovery strategies, and error reporting.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize</think> Safety Error Handler."""
        self.config = config or {}
        
        # Initialize error handling strategies
        self._strategies: Dict[str, ErrorHandlingStrategy] = {}
        self._load_default_strategies()
        
        # Load custom strategies from config
        custom_strategies = self.config.get("custom_strategies", {})
        for strategy_key, strategy_data in custom_strategies.items():
            try:
                strategy = ErrorHandlingStrategy(
                    error_category=ErrorCategory(strategy_data.get("category", "unknown")),
                    error_type=strategy_data.get("error_type", ""),
                    action=ErrorAction(strategy_data.get("action", "log")),
                    max_retries=strategy_data.get("max_retries", 0),
                    retry_delay=strategy_data.get("retry_delay", 1.0),
                    fallback_response=strategy_data.get("fallback_response"),
                    should_log=strategy_data.get("should_log", True),
                    should_alert=strategy_data.get("should_alert", False),
                    alert_threshold=strategy_data.get("alert_threshold", 3)
                )
                self._strategies[strategy_key] = strategy
            except Exception as e:
                logger.warning(f"Failed to load custom strategy {strategy_key}: {e}")
        
        # Error tracking
        self._error_counts: Dict[str, int] = {}
        self._error_history: List[SafetyError] = []
        
        # Error handlers
        self._error_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        
        logger.info(f"Safety Error Handler initialized with {len(self._strategies)} strategies")
    
    def _load_default_strategies(self) -> None:
        """Load default error handling strategies."""
        default_strategies = [
            ErrorHandlingStrategy(
                error_category=ErrorCategory.VALIDATION,
                error_type="invalid_input",
                action=ErrorAction.WARN,
                should_log=True,
                fallback_response={
                    "error": "Invalid input",
                    "message": "The provided input is invalid",
                    "category": "validation"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.VALIDATION,
                error_type="missing_required_field",
                action=ErrorAction.WARN,
                should_log=True,
                fallback_response={
                    "error": "Missing required field",
                    "message": "A required field is missing from the input",
                    "category": "validation"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.AUTHORIZATION,
                error_type="unauthorized",
                action=ErrorAction.BLOCK,
                should_log=True,
                fallback_response={
                    "error": "Unauthorized",
                    "message": "You are not authorized to perform this action",
                    "category": "authorization"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.AUTHORIZATION,
                error_type="insufficient_permissions",
                action=ErrorAction.BLOCK,
                should_log=True,
                fallback_response={
                    "error": "Insufficient permissions",
                    "message": "You do not have sufficient permissions to perform this action",
                    "category": "authorization"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.CONTENT_SAFETY,
                error_type="unsafe_content_detected",
                action=ErrorAction.BLOCK,
                should_log=True,
                should_alert=True,
                fallback_response={
                    "error": "Content blocked",
                    "message": "The content was blocked due to safety concerns",
                    "category": "content_safety"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.CONTENT_SAFETY,
                error_type="content_check_failed",
                action=ErrorAction.WARN,
                should_log=True,
                fallback_response={
                    "error": "Content check failed",
                    "message": "Failed to check content safety",
                    "category": "content_safety"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.SYSTEM,
                error_type="service_unavailable",
                action=ErrorAction.RETRY,
                max_retries=3,
                retry_delay=2.0,
                should_log=True,
                should_alert=True,
                fallback_response={
                    "error": "Service unavailable",
                    "message": "The required service is currently unavailable",
                    "category": "system"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.NETWORK,
                error_type="connection_failed",
                action=ErrorAction.RETRY,
                max_retries=3,
                retry_delay=1.0,
                should_log=True,
                fallback_response={
                    "error": "Connection failed",
                    "message": "Failed to establish connection to required service",
                    "category": "network"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.TIMEOUT,
                error_type="operation_timeout",
                action=ErrorAction.FALLBACK,
                should_log=True,
                fallback_response={
                    "error": "Operation timeout",
                    "message": "The operation timed out",
                    "category": "timeout"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.CONFIGURATION,
                error_type="invalid_config",
                action=ErrorAction.BLOCK,
                should_log=True,
                should_alert=True,
                fallback_response={
                    "error": "Invalid configuration",
                    "message": "The system configuration is invalid",
                    "category": "configuration"
                }
            ),
            ErrorHandlingStrategy(
                error_category=ErrorCategory.UNKNOWN,
                error_type="unexpected_error",
                action=ErrorAction.ESCALATE,
                should_log=True,
                should_alert=True,
                fallback_response={
                    "error": "Unexpected error",
                    "message": "An unexpected error occurred",
                    "category": "unknown"
                }
            )
        ]
        
        for strategy in default_strategies:
            key = f"{strategy.error_category.value}.{strategy.error_type}"
            self._strategies[key] = strategy
    
    def _register_default_handlers(self) -> None:
        """Register default error handlers."""
        self._error_handlers["validation_error"] = self._handle_validation_error
        self._error_handlers["authorization_error"] = self._handle_authorization_error
        self._error_handlers["content_safety_error"] = self._handle_content_safety_error
        self._error_handlers["system_error"] = self._handle_system_error
        self._error_handlers["network_error"] = self._handle_network_error
        self._error_handlers["timeout_error"] = self._handle_timeout_error
        self._error_handlers["configuration_error"] = self._handle_configuration_error
        self._error_handlers["unknown_error"] = self._handle_unknown_error
    
    def register_error_handler(self, error_type: str, handler: Callable) -> bool:
        """
        Register a custom error handler.
        
        Args:
            error_type: Type of error to handle
            handler: Handler function
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            self._error_handlers[error_type] = handler
            logger.info(f"Registered error handler for: {error_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to register error handler for {error_type}: {e}")
            return False
    
    def unregister_error_handler(self, error_type: str) -> bool:
        """
        Unregister an error handler.
        
        Args:
            error_type: Type of error handler to remove
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        try:
            if error_type in self._error_handlers:
                del self._error_handlers[error_type]
                logger.info(f"Unregistered error handler for: {error_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister error handler for {error_type}: {e}")
            return False
    
    def get_error_handler(self, error_type: str) -> Optional[Callable]:
        """
        Get an error handler.
        
        Args:
            error_type: Type of error handler to get
            
        Returns:
            Handler function if found, None otherwise
        """
        return self._error_handlers.get(error_type)
    
    def add_strategy(self, strategy: ErrorHandlingStrategy) -> bool:
        """
        Add an error handling strategy.
        
        Args:
            strategy: Strategy to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            key = f"{strategy.error_category.value}.{strategy.error_type}"
            self._strategies[key] = strategy
            logger.info(f"Added error handling strategy: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to add error handling strategy: {e}")
            return False
    
    def remove_strategy(self, error_category: ErrorCategory, error_type: str) -> bool:
        """
        Remove an error handling strategy.
        
        Args:
            error_category: Category of error
            error_type: Type of error
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            key = f"{error_category.value}.{error_type}"
            if key in self._strategies:
                del self._strategies[key]
                logger.info(f"Removed error handling strategy: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove error handling strategy: {e}")
            return False
    
    def get_strategy(self, error_category: ErrorCategory, error_type: str) -> Optional[ErrorHandlingStrategy]:
        """
        Get an error handling strategy.
        
        Args:
            error_category: Category of error
            error_type: Type of error
            
        Returns:
            Strategy if found, None otherwise
        """
        key = f"{error_category.value}.{error_type}"
        return self._strategies.get(key)
    
    def classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> SafetyError:
        """
        Classify an error and create a SafetyError.
        
        Args:
            error: Exception to classify
            context: Optional context information
            
        Returns:
            Classified SafetyError
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine error category and severity
        category = ErrorCategory.UNKNOWN
        severity = ErrorSeverity.MEDIUM
        
        if isinstance(error, HTTPException):
            category = ErrorCategory.AUTHORIZATION
            severity = ErrorSeverity.HIGH if error.status_code >= 500 else ErrorSeverity.MEDIUM
        elif isinstance(error, ValueError):
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, PermissionError):
            category = ErrorCategory.AUTHORIZATION
            severity = ErrorSeverity.HIGH
        elif "timeout" in error_message.lower():
            category = ErrorCategory.TIMEOUT
            severity = ErrorSeverity.MEDIUM
        elif "connection" in error_message.lower():
            category = ErrorCategory.NETWORK
            severity = ErrorSeverity.MEDIUM
        elif "config" in error_message.lower():
            category = ErrorCategory.CONFIGURATION
            severity = ErrorSeverity.HIGH
        elif "safety" in error_message.lower():
            category = ErrorCategory.CONTENT_SAFETY
            severity = ErrorSeverity.HIGH
        elif "system" in error_message.lower():
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.HIGH
        
        # Generate error ID
        error_id = f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Get stack trace
        stack_trace = traceback.format_exc() if self.config.get("include_stack_trace", False) else None
        
        # Create safety error
        safety_error = SafetyError(
            error_id=error_id,
            error_type=error_type,
            category=category,
            severity=severity,
            message=error_message,
            details={},
            timestamp=datetime.utcnow(),
            stack_trace=stack_trace,
            context=context
        )
        
        # Get handling strategy
        strategy = self.get_strategy(category, error_type.lower())
        if strategy:
            safety_error.recovery_action = strategy.action
        
        return safety_error
    
    async def handle_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[JSONResponse]:
        """
        Handle an error.
        
        Args:
            error: Exception to handle
            request: Optional FastAPI request
            context: Optional context information
            
        Returns:
            JSONResponse if error should be handled, None otherwise
        """
        # Classify error
        safety_error = self.classify_error(error, context)
        
        # Track error
        self._track_error(safety_error)
        
        # Get handling strategy
        strategy = self.get_strategy(safety_error.category, safety_error.error_type.lower())
        
        if not strategy:
            # Default strategy
            strategy = ErrorHandlingStrategy(
                error_category=ErrorCategory.UNKNOWN,
                error_type=safety_error.error_type,
                action=ErrorAction.ESCALATE,
                should_log=True,
                should_alert=True
            )
        
        # Log error if needed
        if strategy.should_log:
            self._log_error(safety_error)
        
        # Check if we should alert
        if strategy.should_alert:
            self._check_alert_threshold(safety_error)
        
        # Get appropriate handler
        handler = self.get_error_handler(f"{safety_error.category.value}_error")
        
        if handler:
            try:
                return await handler(safety_error, strategy, request)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        
        # Default handling based on action
        if strategy.action == ErrorAction.BLOCK:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=strategy.fallback_response or {
                    "error": "Access denied",
                    "message": "The request was blocked due to safety concerns",
                    "category": safety_error.category.value
                }
            )
        elif strategy.action == ErrorAction.WARN:
            # Log warning but allow request to proceed
            return None
        elif strategy.action == ErrorAction.FALLBACK:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=strategy.fallback_response or {
                    "error": "Service unavailable",
                    "message": "The service is currently unavailable",
                    "category": safety_error.category.value
                }
            )
        elif strategy.action == ErrorAction.ESCALATE:
            # Log critical error and return server error
            logger.critical(f"Critical safety error: {safety_error.error_id} - {safety_error.message}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "An internal server error occurred",
                    "category": safety_error.category.value,
                    "error_id": safety_error.error_id
                }
            )
        
        # For other actions, allow request to proceed
        return None
    
    async def _handle_validation_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle validation errors."""
        if strategy.action == ErrorAction.BLOCK:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=strategy.fallback_response or {
                    "error": "Validation error",
                    "message": error.message,
                    "category": error.category.value
                }
            )
        
        return None
    
    async def _handle_authorization_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle authorization errors."""
        if strategy.action == ErrorAction.BLOCK:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=strategy.fallback_response or {
                    "error": "Authorization error",
                    "message": error.message,
                    "category": error.category.value
                }
            )
        
        return None
    
    async def _handle_content_safety_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle content safety errors."""
        if strategy.action == ErrorAction.BLOCK:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=strategy.fallback_response or {
                    "error": "Content safety error",
                    "message": error.message,
                    "category": error.category.value
                }
            )
        
        return None
    
    async def _handle_system_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle system errors."""
        if strategy.action == ErrorAction.FALLBACK:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=strategy.fallback_response or {
                    "error": "System error",
                    "message": error.message,
                    "category": error.category.value
                }
            )
        
        return None
    
    async def _handle_network_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle network errors."""
        if strategy.action == ErrorAction.FALLBACK:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=strategy.fallback_response or {
                    "error": "Network error",
                    "message": error.message,
                    "category": error.category.value
                }
            )
        
        return None
    
    async def _handle_timeout_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle timeout errors."""
        if strategy.action == ErrorAction.FALLBACK:
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content=strategy.fallback_response or {
                    "error": "Timeout error",
                    "message": error.message,
                    "category": error.category.value
                }
            )
        
        return None
    
    async def _handle_configuration_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle configuration errors."""
        if strategy.action == ErrorAction.BLOCK:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=strategy.fallback_response or {
                    "error": "Configuration error",
                    "message": error.message,
                    "category": error.category.value
                }
            )
        
        return None
    
    async def _handle_unknown_error(
        self,
        error: SafetyError,
        strategy: ErrorHandlingStrategy,
        request: Optional[Request] = None
    ) -> Optional[JSONResponse]:
        """Handle unknown errors."""
        if strategy.action == ErrorAction.ESCALATE:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=strategy.fallback_response or {
                    "error": "Unknown error",
                    "message": error.message,
                    "category": error.category.value,
                    "error_id": error.error_id
                }
            )
        
        return None
    
    def _track_error(self, error: SafetyError) -> None:
        """Track an error for statistics."""
        error_key = f"{error.category.value}.{error.error_type}"
        
        # Increment error count
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # Add to error history
        self._error_history.append(error)
        
        # Keep only the last 1000 errors
        if len(self._error_history) > 1000:
            self._error_history = self._error_history[-1000:]
    
    def _log_error(self, error: SafetyError) -> None:
        """Log an error."""
        log_method = logger.info
        if error.severity == ErrorSeverity.CRITICAL:
            log_method = logger.critical
        elif error.severity == ErrorSeverity.HIGH:
            log_method = logger.error
        elif error.severity == ErrorSeverity.MEDIUM:
            log_method = logger.warning
        
        log_method(
            f"SAFETY ERROR: {error.error_type} - {error.message}",
            extra={
                "error_id": error.error_id,
                "error_type": error.error_type,
                "category": error.category.value,
                "severity": error.severity.value,
                "recovery_action": error.recovery_action.value if error.recovery_action else None,
                "context": error.context
            }
        )
    
    def _check_alert_threshold(self, error: SafetyError) -> None:
        """Check if error count exceeds alert threshold."""
        error_key = f"{error.category.value}.{error.error_type}"
        error_count = self._error_counts.get(error_key, 0)
        
        # Get strategy for this error
        strategy = self.get_strategy(error.category, error.error_type.lower())
        if not strategy or not strategy.should_alert:
            return
        
        # Check if count exceeds threshold
        if error_count >= strategy.alert_threshold:
            logger.critical(
                f"SAFETY ALERT: Error threshold exceeded for {error_key}",
                extra={
                    "error_key": error_key,
                    "error_count": error_count,
                    "threshold": strategy.alert_threshold,
                    "error_type": error.error_type,
                    "category": error.category.value
                }
            )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        # Group errors by category
        errors_by_category = {}
        for error in self._error_history:
            category = error.category.value
            if category not in errors_by_category:
                errors_by_category[category] = []
            errors_by_category[category].append(error)
        
        # Group errors by type
        errors_by_type = {}
        for error in self._error_history:
            error_type = error.error_type
            if error_type not in errors_by_type:
                errors_by_type[error_type] = []
            errors_by_type[error_type].append(error)
        
        # Get recent errors (last 24 hours)
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_errors = [e for e in self._error_history if e.timestamp > cutoff_time]
        
        return {
            "total_errors": len(self._error_history),
            "unique_error_types": len(self._error_counts),
            "errors_by_category": {
                category: len(errors)
                for category, errors in errors_by_category.items()
            },
            "errors_by_type": {
                error_type: len(errors)
                for error_type, errors in errors_by_type.items()
            },
            "recent_errors_24h": len(recent_errors),
            "top_error_types": sorted(
                self._error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def clear_error_history(self) -> None:
        """Clear error history."""
        self._error_history.clear()
        self._error_counts.clear()
        logger.info("Error history cleared")