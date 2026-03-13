"""
Global Error Handler Integration

This module provides the main error handler that integrates all error handling
components including classification, retry, circuit breaker, recovery, and monitoring.
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import uuid
from .error_classifier import ErrorClassifier, ErrorClassification
from .retry_manager import RetryManager, RetryConfig, RetryStrategy
from .circuit_breaker import CircuitBreakerManager, CircuitBreakerConfig
from .error_recovery import ErrorRecoveryManager, RecoveryResult
from .error_monitoring import ErrorMonitor, ErrorAnalytics
from .error_context import ContextManager, ErrorContext, ContextScope, ContextType

T = TypeVar('T')


class ErrorHandler:
    """
    Global error handler that integrates all error handling components.
    
    Features:
    - Automatic error classification
    - Intelligent retry logic
    - Circuit breaker protection
    - Error recovery strategies
    - Comprehensive monitoring
    - Context preservation
    - User-friendly error messages
    """
    
    def __init__(self):
        # Initialize all components
        self.classifier = ErrorClassifier()
        self.retry_manager = RetryManager()
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.recovery_manager = ErrorRecoveryManager()
        self.monitor = ErrorMonitor()
        self.analytics = ErrorAnalytics(self.monitor)
        self.context_manager = ContextManager()
        
        # Configure component integration
        self.retry_manager.set_circuit_breaker_manager(self.circuit_breaker_manager)
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Configuration
        self.config = {
            "enable_retry": True,
            "enable_circuit_breaker": True,
            "enable_recovery": True,
            "enable_monitoring": True,
            "enable_context": True,
            "default_max_retries": 3,
            "default_timeout": 30.0,
        }
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[Callable] = None,
        **kwargs
    ) -> Union[T, RecoveryResult]:
        """
        Handle error with comprehensive error management.
        
        Args:
            error: The exception to handle
            context: Additional context information
            operation: Optional operation to retry/recover
            **kwargs: Additional parameters
            
        Returns:
            Result of error handling or recovery
        """
        start_time = datetime.utcnow()
        context = context or {}
        
        try:
            # Step 1: Classify error
            classification = self.classifier.classify_error(error, context)
            
            # Step 2: Create error context
            if self.config["enable_context"]:
                error_context = self._create_error_context(error, classification, context)
            else:
                error_context = None
            
            # Step 3: Record error for monitoring
            if self.config["enable_monitoring"]:
                self.monitor.record_error(error, classification, context)
            
            # Step 4: Attempt recovery
            if self.config["enable_recovery"] and operation:
                recovery_result = await self._attempt_recovery(
                    error, classification, context, operation, **kwargs
                )
                
                if recovery_result.final_status.value == "success":
                    return recovery_result.final_result
            
            # Step 5: Return error information
            return self._create_error_response(error, classification, context)
            
        except Exception as handling_error:
            # Error in error handling - fallback to basic response
            logging.error(f"Error in error handling: {handling_error}")
            return self._create_fallback_error_response(error, handling_error)
    
    async def execute_with_protection(
        self,
        operation: Callable[..., T],
        context: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        **kwargs
    ) -> T:
        """
        Execute operation with full error protection.
        
        Args:
            operation: The operation to execute
            context: Additional context
            retry_config: Optional retry configuration
            circuit_breaker_config: Optional circuit breaker configuration
            **kwargs: Operation arguments
            
        Returns:
            Result of operation execution
        """
        context = context or {}
        
        # Create error context for operation
        if self.config["enable_context"]:
            error_context = self.context_manager.create_context(
                error_id=str(uuid.uuid4()),
                scope=ContextScope.REQUEST,
                component=context.get("component"),
                operation=context.get("operation"),
                user_id=context.get("user_id"),
                session_id=context.get("session_id"),
                request_id=context.get("request_id")
            )
            
            # Add operation context
            error_context.add_entry(
                "operation_args",
                {"args": kwargs.get("args", []), "kwargs": kwargs.get("kwargs", {})},
                ContextType.REQUEST_DATA
            )
        
        # Get or create circuit breaker
        circuit_breaker_name = context.get("circuit_breaker_name", "default")
        if circuit_breaker_config:
            circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(
                circuit_breaker_name, circuit_breaker_config
            )
        else:
            circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(circuit_breaker_name)
        
        # Check circuit breaker
        if self.config["enable_circuit_breaker"] and not circuit_breaker.can_execute():
            error = Exception(f"Circuit breaker '{circuit_breaker_name}' is open")
            return await self.handle_error(error, context, operation, **kwargs)
        
        try:
            # Execute with retry if enabled
            if self.config["enable_retry"]:
                # Create retry config from classification if available
                if retry_config is None:
                    retry_config = RetryConfig(
                        max_retries=self.config["default_max_retries"],
                        base_delay=1.0,
                        strategy=RetryStrategy.EXPONENTIAL_BACKOFF
                    )
                
                result = await self.retry_manager.execute_with_retry(
                    operation, retry_config, **kwargs
                )
            else:
                # Execute without retry
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(**kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, operation, **kwargs)
            
            # Record success
            if self.config["enable_circuit_breaker"]:
                circuit_breaker.record_success()
            
            return result
            
        except Exception as error:
            # Record failure
            if self.config["enable_circuit_breaker"]:
                circuit_breaker.record_failure(error)
            
            # Handle error with full error management
            return await self.handle_error(error, context, operation, **kwargs)
    
    def _create_error_context(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> ErrorContext:
        """Create error context for preservation."""
        error_context = self.context_manager.create_context(
            error_id=str(uuid.uuid4()),
            scope=ContextScope.REQUEST,
            component=context.get("component"),
            operation=context.get("operation"),
            user_id=context.get("user_id"),
            session_id=context.get("session_id"),
            request_id=context.get("request_id")
        )
        
        # Add error information
        error_context.add_entry(
            "error",
            {
                "type": type(error).__name__,
                "message": str(error),
                "classification": classification,
                "traceback": traceback.format_exc()
            },
            ContextType.SYSTEM_STATE
        )
        
        # Add context information
        error_context.add_entry(
            "context_data",
            context,
            ContextType.REQUEST_DATA
        )
        
        return error_context
    
    async def _attempt_recovery(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: Dict[str, Any],
        operation: Callable,
        **kwargs
    ) -> RecoveryResult:
        """Attempt error recovery using recovery manager."""
        # Prepare recovery context
        recovery_context = {
            "error": error,
            "classification": classification,
            "original_context": context,
            "operation": lambda: operation(**kwargs),
            "operation_name": context.get("operation", "unknown"),
            "component": context.get("component"),
            "user_id": context.get("user_id"),
            "retry_possible": classification.retry_possible,
        }
        
        # Add alternative operations if available
        if context.get("alternative_operation"):
            recovery_context["alternative_operation"] = context["alternative_operation"]
        
        if context.get("cache_manager"):
            recovery_context["cache_manager"] = context["cache_manager"]
            recovery_context["cache_key"] = context.get("cache_key")
        
        # Execute recovery
        return await self.recovery_manager.recover_from_error(
            error, classification, recovery_context
        )
    
    def _create_error_response(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "error": True,
            "error_code": getattr(classification, 'pattern_name', 'UNKNOWN'),
            "category": classification.category.value,
            "severity": classification.severity.value,
            "title": classification.user_message or "Error occurred",
            "message": classification.user_message or str(error),
            "technical_details": classification.technical_details or str(error),
            "resolution_steps": classification.resolution_steps,
            "retry_possible": classification.retry_possible,
            "user_action_required": classification.user_action_required,
            "timestamp": datetime.utcnow().isoformat(),
            "context": {
                "component": context.get("component"),
                "operation": context.get("operation"),
                "user_id": context.get("user_id"),
                "request_id": context.get("request_id"),
            }
        }
    
    def _create_fallback_error_response(
        self,
        original_error: Exception,
        handling_error: Exception
    ) -> Dict[str, Any]:
        """Create fallback error response when error handling fails."""
        return {
            "error": True,
            "error_code": "HANDLING_FAILED",
            "category": "system",
            "severity": "critical",
            "title": "Critical Error in Error Handling",
            "message": "A critical error occurred while handling another error.",
            "technical_details": {
                "original_error": str(original_error),
                "handling_error": str(handling_error)
            },
            "resolution_steps": [
                "Contact system administrator immediately",
                "Restart the application if necessary"
            ],
            "retry_possible": False,
            "user_action_required": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def configure(self, **config) -> None:
        """Configure error handler settings."""
        self.config.update(config)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all components."""
        return {
            "error_classifier": {
                "patterns_count": len(self.classifier.patterns),
            },
            "retry_manager": self.retry_manager.get_retry_statistics(),
            "circuit_breaker": {
                "total_circuit_breakers": len(self.circuit_breaker_manager.circuit_breakers),
                "open_circuit_breakers": self.circuit_breaker_manager.get_open_circuit_breakers(),
                "metrics": self.circuit_breaker_manager.get_all_metrics(),
            },
            "recovery_manager": self.recovery_manager.get_recovery_statistics(),
            "monitor": self.monitor.get_metrics(),
            "context_manager": self.context_manager.get_statistics(),
        }
    
    def shutdown(self) -> None:
        """Shutdown error handler and cleanup resources."""
        self.monitor.stop_monitoring()
        
        # Clear all contexts
        for context_id in list(self.context_manager.contexts.keys()):
            self.context_manager.delete_context(context_id)


class GlobalErrorHandler:
    """
    Global singleton error handler for application-wide error management.
    
    Provides a single point of access to error handling functionality
    with automatic initialization and configuration.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.handler = ErrorHandler()
            self._initialized = True
    
    async def handle_error(self, error: Exception, **kwargs) -> Any:
        """Handle error using global handler."""
        return await self.handler.handle_error(error, **kwargs)
    
    async def execute_with_protection(self, operation: Callable, **kwargs) -> Any:
        """Execute operation with protection using global handler."""
        return await self.handler.execute_with_protection(operation, **kwargs)
    
    def configure(self, **config) -> None:
        """Configure global error handler."""
        self.handler.configure(**config)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from global handler."""
        return self.handler.get_statistics()
    
    def shutdown(self) -> None:
        """Shutdown global error handler."""
        self.handler.shutdown()


# Global error handler instance
global_error_handler = GlobalErrorHandler()


def handle_errors(
    enable_retry: bool = True,
    enable_circuit_breaker: bool = True,
    enable_recovery: bool = True,
    max_retries: int = 3,
    **kwargs
):
    """Decorator for automatic error handling."""
    def decorator(func):
        async def wrapper(*args, **func_kwargs):
            # Create operation context
            context = {
                "operation": func.__name__,
                "component": kwargs.get("component"),
                "enable_retry": enable_retry,
                "enable_circuit_breaker": enable_circuit_breaker,
                "enable_recovery": enable_recovery,
                "max_retries": max_retries,
                **kwargs
            }
            
            # Execute with protection
            return await global_error_handler.execute_with_protection(
                operation=func,
                context=context,
                args=args,
                kwargs=func_kwargs
            )
        
        return wrapper
    return decorator


async def safe_execute(
    operation: Callable,
    *args,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Safely execute operation with error handling.
    
    Args:
        operation: Operation to execute
        *args: Operation arguments
        default_return: Default return value on error
        **kwargs: Operation keyword arguments
        
    Returns:
        Operation result or default_return on error
    """
    try:
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, operation, *args, **kwargs)
    except Exception:
        return default_return