"""
Global Error Handler for AI-Karen Production Chat System
Centralized error handling for all chat endpoints with comprehensive error management.
"""

import logging
import traceback
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timezone
from enum import Enum
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification and routing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Error categories for classification and routing."""
    NETWORK = "network"
    CONNECTIVITY = "connectivity"
    API_FAILURE = "api_failure"
    SYSTEM = "system"
    INFRASTRUCTURE = "infrastructure"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    APPLICATION = "application"
    BUSINESS_LOGIC = "business_logic"
    VALIDATION = "validation"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    AI_PROCESSING = "ai_processing"
    MODEL_UNAVAILABLE = "model_unavailable"
    LLM_PROVIDER = "llm_provider"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"
    RATE_LIMITING = "rate_limiting"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class ErrorInfo:
    """Comprehensive error information structure."""
    
    def __init__(
        self,
        type: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        title: str,
        message: str,
        technical_details: Optional[str] = None,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        retry_possible: bool = False,
        user_action_required: bool = False,
        resolution_steps: Optional[List[str]] = None,
        recovery_actions: Optional[List[Any]] = None
    ):
        self.id = f"err_{datetime.now().timestamp()}"
        self.type = type
        self.category = category
        self.severity = severity
        self.title = title
        self.message = message
        self.technical_details = technical_details
        self.stack_trace = stack_trace
        self.context = context or {}
        self.metadata = metadata or {}
        self.user_id = user_id
        self.session_id = session_id
        self.request_id = request_id
        self.component = component
        self.operation = operation
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.retry_possible = retry_possible
        self.user_action_required = user_action_required
        self.resolution_steps = resolution_steps or []
        self.recovery_actions = recovery_actions or []


class ErrorResponse:
    """Standardized error response format."""
    
    def __init__(
        self,
        error: ErrorInfo,
        success: bool = False,
        timestamp: Optional[datetime] = None,
        request_id: Optional[str] = None
    ):
        self.error = error
        self.success = success
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.request_id = request_id


class ErrorContext:
    """Error context information for better error handling."""
    
    def __init__(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.request_id = request_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.component = component
        self.operation = operation
        self.additional_data = additional_data or {}


class GlobalErrorHandler:
    """
    Global error handler for centralized error management.
    
    Features:
    - Error classification and routing
    - Automatic error recovery mechanisms
    - Error logging and monitoring
    - User-friendly error responses
    - Error rate limiting and circuit breaking
    """
    
    def __init__(self):
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self.error_history: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default handlers
        self._initialize_default_handlers()
    
    def _initialize_default_handlers(self):
        """Initialize default error handlers for common categories."""
        # Network errors
        self.register_error_handler(ErrorCategory.NETWORK, self._handle_network_error)
        self.register_error_handler(ErrorCategory.CONNECTIVITY, self._handle_connectivity_error)
        
        # System errors
        self.register_error_handler(ErrorCategory.SYSTEM, self._handle_system_error)
        self.register_error_handler(ErrorCategory.INFRASTRUCTURE, self._handle_infrastructure_error)
        
        # Database errors
        self.register_error_handler(ErrorCategory.DATABASE, self._handle_database_error)
        
        # Security errors
        self.register_error_handler(ErrorCategory.SECURITY, self._handle_security_error)
        self.register_error_handler(ErrorCategory.AUTHENTICATION, self._handle_authentication_error)
        self.register_error_handler(ErrorCategory.AUTHORIZATION, self._handle_authorization_error)
        
        # AI processing errors
        self.register_error_handler(ErrorCategory.AI_PROCESSING, self._handle_ai_processing_error)
        self.register_error_handler(ErrorCategory.MODEL_UNAVAILABLE, self._handle_model_unavailable_error)
        self.register_error_handler(ErrorCategory.LLM_PROVIDER, self._handle_llm_provider_error)
        
        # Validation errors
        self.register_error_handler(ErrorCategory.VALIDATION, self._handle_validation_error)
        
        # Timeout errors
        self.register_error_handler(ErrorCategory.TIMEOUT, self._handle_timeout_error)
        
        # Rate limiting errors
        self.register_error_handler(ErrorCategory.RATE_LIMITING, self._handle_rate_limiting_error)
    
    def register_error_handler(self, category: ErrorCategory, handler: Callable):
        """Register a custom error handler for a specific category."""
        if category not in self.error_handlers:
            self.error_handlers[category] = []
        self.error_handlers[category].append(handler)
        logger.info(f"Registered error handler for category: {category.value}")
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """Register a recovery strategy for a specific error category."""
        if category not in self.recovery_strategies:
            self.recovery_strategies[category] = []
        self.recovery_strategies[category].append(strategy)
        logger.info(f"Registered recovery strategy for category: {category.value}")
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """
        Handle an error with comprehensive error management.
        
        Args:
            error: The exception that occurred
            context: Error context information
            request: The HTTP request if available
            
        Returns:
            Standardized error response
        """
        try:
            # Classify error
            error_info = await self._classify_error(error, context, request)
            
            # Add to error history
            self.error_history.append(error_info)
            self._update_error_counts(error_info)
            
            # Check rate limits
            if await self._is_rate_limited(error_info):
                return self._create_rate_limit_response(error_info)
            
            # Log error
            await self._log_error(error_info)
            
            # Execute category-specific handlers
            await self._execute_error_handlers(error_info)
            
            # Create response
            response = self._create_error_response(error_info)
            
            return response
            
        except Exception as handling_error:
            logger.error(f"Error in error handler: {handling_error}")
            # Fallback response
            return self._create_fallback_response(error, context)
    
    async def _classify_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        request: Optional[Request] = None
    ) -> ErrorInfo:
        """Classify error and create comprehensive error information."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine category and severity
        category, severity = self._determine_category_and_severity(error)
        
        # Extract context information
        context_data = {}
        if context:
            context_data = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "request_id": context.request_id,
                "ip_address": context.ip_address,
                "user_agent": context.user_agent,
                "component": context.component,
                "operation": context.operation
            }
            if context.additional_data:
                context_data.update(context.additional_data)
        
        if request:
            context_data["method"] = request.method
            context_data["url"] = str(request.url)
            # Handle headers properly
            headers_dict = {}
            for key, value in request.headers.items():
                headers_dict[key] = value
            # Add headers properly to avoid type issues
            for key, value in headers_dict.items():
                context_data[f"headers.{key}"] = value
        
        # Generate resolution steps
        resolution_steps = self._generate_resolution_steps(category, error)
        
        return ErrorInfo(
            type=error_type,
            category=category,
            severity=severity,
            title=self._generate_error_title(category, error_type),
            message=error_message,
            technical_details=error_message,
            stack_trace=traceback.format_exc(),
            context=context_data,
            metadata={
                "original_exception": str(error),
                "exception_type": error_type,
                "module": error.__class__.__module__
            },
            user_id=context.user_id if context else None,
            session_id=context.session_id if context else None,
            request_id=context.request_id if context else None,
            component=context.component if context else None,
            operation=context.operation if context else None,
            retry_possible=self._is_retry_possible(category, error),
            user_action_required=self._requires_user_action(category, error),
            resolution_steps=resolution_steps
        )
    
    def _determine_category_and_severity(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Determine error category and severity based on exception type and message."""
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Network and connectivity errors
        if any(keyword in error_message for keyword in ["connection", "network", "dns", "timeout", "unreachable"]):
            if "timeout" in error_message:
                return ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        
        # Database errors
        if any(keyword in error_message for keyword in ["database", "sql", "connection pool", "transaction"]):
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH
        
        # Security errors
        if any(keyword in error_message for keyword in ["unauthorized", "forbidden", "authentication", "permission"]):
            if "unauthorized" in error_message:
                return ErrorCategory.AUTHENTICATION, ErrorSeverity.MEDIUM
            return ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM
        
        # Validation errors
        if any(keyword in error_message for keyword in ["validation", "invalid", "required", "format"]):
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        
        # AI processing errors
        if any(keyword in error_message for keyword in ["model", "ai", "llm", "inference", "generation"]):
            if "unavailable" in error_message:
                return ErrorCategory.MODEL_UNAVAILABLE, ErrorSeverity.HIGH
            return ErrorCategory.AI_PROCESSING, ErrorSeverity.MEDIUM
        
        # Rate limiting errors
        if "rate limit" in error_message or "too many requests" in error_message:
            return ErrorCategory.RATE_LIMITING, ErrorSeverity.MEDIUM
        
        # System errors
        if any(keyword in error_message for keyword in ["memory", "disk", "resource", "system"]):
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
        
        # Default to application error
        return ErrorCategory.APPLICATION, ErrorSeverity.MEDIUM
    
    def _generate_error_title(self, category: ErrorCategory, error_type: str) -> str:
        """Generate user-friendly error title based on category."""
        title_map = {
            ErrorCategory.NETWORK: "Network Connection Error",
            ErrorCategory.CONNECTIVITY: "Connection Problem",
            ErrorCategory.API_FAILURE: "Service Error",
            ErrorCategory.SYSTEM: "System Error",
            ErrorCategory.DATABASE: "Database Error",
            ErrorCategory.SECURITY: "Security Error",
            ErrorCategory.AUTHENTICATION: "Authentication Failed",
            ErrorCategory.AUTHORIZATION: "Access Denied",
            ErrorCategory.AI_PROCESSING: "AI Processing Error",
            ErrorCategory.MODEL_UNAVAILABLE: "AI Model Unavailable",
            ErrorCategory.LLM_PROVIDER: "AI Provider Error",
            ErrorCategory.VALIDATION: "Validation Error",
            ErrorCategory.TIMEOUT: "Request Timeout",
            ErrorCategory.RATE_LIMITING: "Rate Limit Exceeded",
            ErrorCategory.RESOURCE_EXHAUSTION: "Resource Exhausted"
        }
        
        return title_map.get(category, f"Error: {error_type}")
    
    def _generate_resolution_steps(self, category: ErrorCategory, error: Exception) -> List[str]:
        """Generate resolution steps based on error category."""
        if category == ErrorCategory.NETWORK:
            return [
                "Check your internet connection",
                "Try refreshing the page",
                "Contact your network administrator if the problem persists"
            ]
        
        elif category == ErrorCategory.AUTHENTICATION:
            return [
                "Check your login credentials",
                "Try logging out and logging back in",
                "Contact support if you continue to have issues"
            ]
        
        elif category == ErrorCategory.VALIDATION:
            return [
                "Check your input for required fields",
                "Ensure all data is in the correct format",
                "Review error messages for specific guidance"
            ]
        
        elif category == ErrorCategory.TIMEOUT:
            return [
                "Try the operation again",
                "Check if the service is experiencing high load",
                "Contact support if timeouts persist"
            ]
        
        elif category == ErrorCategory.RATE_LIMITING:
            return [
                "Wait a few minutes before trying again",
                "Reduce the frequency of your requests",
                "Consider upgrading your plan for higher limits"
            ]
        
        else:
            return [
                "Try refreshing the page",
                "Check your internet connection",
                "Contact support if the problem persists"
            ]
    
    def _is_retry_possible(self, category: ErrorCategory, error: Exception) -> bool:
        """Determine if error is retryable."""
        non_retryable_categories = {
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.VALIDATION,
            ErrorCategory.SECURITY
        }
        
        return category not in non_retryable_categories
    
    def _requires_user_action(self, category: ErrorCategory, error: Exception) -> bool:
        """Determine if user action is required to resolve error."""
        user_action_categories = {
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.VALIDATION
        }
        
        return category in user_action_categories
    
    async def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level based on severity."""
        log_message = f"Error {error_info.id}: {error_info.title} - {error_info.message}"
        
        if error_info.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            logger.warning(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
            logger.critical(log_message)
        
        # Log detailed information
        logger.debug(f"Error details: {error_info.__dict__}")
    
    async def _execute_error_handlers(self, error_info: ErrorInfo):
        """Execute category-specific error handlers."""
        handlers = self.error_handlers.get(error_info.category, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error_info)
                else:
                    handler(error_info)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")
    
    def _update_error_counts(self, error_info: ErrorInfo):
        """Update error counts for rate limiting."""
        key = f"{error_info.category.value}_{error_info.type}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        # Clean old entries (keep only last 1000 errors)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    async def _is_rate_limited(self, error_info: ErrorInfo) -> bool:
        """Check if error should be rate limited."""
        key = f"{error_info.category.value}_{error_info.type}"
        
        # Simple rate limiting: max 10 errors per minute per category
        if key not in self.rate_limits:
            self.rate_limits[key] = {"count": 0, "last_reset": datetime.now(timezone.utc)}
        
        now = datetime.now(timezone.utc)
        if (now - self.rate_limits[key]["last_reset"]).seconds > 60:
            self.rate_limits[key] = {"count": 1, "last_reset": now}
        else:
            self.rate_limits[key]["count"] += 1
        
        return self.rate_limits[key]["count"] > 10
    
    def _create_error_response(self, error_info: ErrorInfo) -> ErrorResponse:
        """Create standardized error response."""
        return ErrorResponse(
            error=error_info,
            request_id=error_info.request_id
        )
    
    def _create_rate_limit_response(self, error_info: ErrorInfo) -> ErrorResponse:
        """Create rate limit error response."""
        rate_limit_error = ErrorInfo(
            type="RateLimitError",
            category=ErrorCategory.RATE_LIMITING,
            severity=ErrorSeverity.MEDIUM,
            title="Rate Limit Exceeded",
            message="Too many errors have occurred. Please try again later.",
            user_id=error_info.user_id,
            session_id=error_info.session_id,
            request_id=error_info.request_id,
            retry_possible=True,
            user_action_required=True,
            resolution_steps=["Wait a few minutes before trying again"],
            context=error_info.context
        )
        
        return ErrorResponse(error=rate_limit_error, request_id=error_info.request_id)
    
    def _create_fallback_response(self, error: Exception, context: Optional[ErrorContext] = None) -> ErrorResponse:
        """Create fallback error response when error handling fails."""
        fallback_error = ErrorInfo(
            type="FallbackError",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            title="System Error",
            message="An unexpected error occurred. Please try again later.",
            technical_details=str(error),
            user_id=context.user_id if context else None,
            session_id=context.session_id if context else None,
            request_id=context.request_id if context else None,
            retry_possible=True,
            user_action_required=False,
            resolution_steps=["Try refreshing the page", "Contact support if the problem persists"],
            context={"original_error": str(error)} if context else None
        )
        
        return ErrorResponse(error=fallback_error, request_id=context.request_id if context else None)
    
    # Default error handlers
    async def _handle_network_error(self, error_info: ErrorInfo):
        """Handle network-related errors."""
        logger.info(f"Handling network error: {error_info.id}")
        # Implement network-specific error handling logic
    
    async def _handle_connectivity_error(self, error_info: ErrorInfo):
        """Handle connectivity errors."""
        logger.info(f"Handling connectivity error: {error_info.id}")
        # Implement connectivity-specific error handling logic
    
    async def _handle_system_error(self, error_info: ErrorInfo):
        """Handle system errors."""
        logger.error(f"Handling system error: {error_info.id}")
        # Implement system-specific error handling logic
    
    async def _handle_infrastructure_error(self, error_info: ErrorInfo):
        """Handle infrastructure errors."""
        logger.error(f"Handling infrastructure error: {error_info.id}")
        # Implement infrastructure-specific error handling logic
    
    async def _handle_database_error(self, error_info: ErrorInfo):
        """Handle database errors."""
        logger.error(f"Handling database error: {error_info.id}")
        # Implement database-specific error handling logic
    
    async def _handle_security_error(self, error_info: ErrorInfo):
        """Handle security errors."""
        logger.warning(f"Handling security error: {error_info.id}")
        # Implement security-specific error handling logic
    
    async def _handle_authentication_error(self, error_info: ErrorInfo):
        """Handle authentication errors."""
        logger.info(f"Handling authentication error: {error_info.id}")
        # Implement authentication-specific error handling logic
    
    async def _handle_authorization_error(self, error_info: ErrorInfo):
        """Handle authorization errors."""
        logger.warning(f"Handling authorization error: {error_info.id}")
        # Implement authorization-specific error handling logic
    
    async def _handle_ai_processing_error(self, error_info: ErrorInfo):
        """Handle AI processing errors."""
        logger.error(f"Handling AI processing error: {error_info.id}")
        # Implement AI processing-specific error handling logic
    
    async def _handle_model_unavailable_error(self, error_info: ErrorInfo):
        """Handle model unavailable errors."""
        logger.error(f"Handling model unavailable error: {error_info.id}")
        # Implement model unavailable-specific error handling logic
    
    async def _handle_llm_provider_error(self, error_info: ErrorInfo):
        """Handle LLM provider errors."""
        logger.error(f"Handling LLM provider error: {error_info.id}")
        # Implement LLM provider-specific error handling logic
    
    async def _handle_validation_error(self, error_info: ErrorInfo):
        """Handle validation errors."""
        logger.info(f"Handling validation error: {error_info.id}")
        # Implement validation-specific error handling logic
    
    async def _handle_timeout_error(self, error_info: ErrorInfo):
        """Handle timeout errors."""
        logger.warning(f"Handling timeout error: {error_info.id}")
        # Implement timeout-specific error handling logic
    
    async def _handle_rate_limiting_error(self, error_info: ErrorInfo):
        """Handle rate limiting errors."""
        logger.info(f"Handling rate limiting error: {error_info.id}")
        # Implement rate limiting-specific error handling logic


# Global error handler instance
global_error_handler = GlobalErrorHandler()


async def handle_chat_error(
    error: Exception,
    context: Optional[ErrorContext] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """
    FastAPI error handler for chat endpoints.
    
    Args:
        error: The exception that occurred
        context: Error context information
        request: The HTTP request
        
    Returns:
        JSON response with error information
    """
    error_response = await global_error_handler.handle_error(error, context, request)
    
    # Determine HTTP status code based on error category
    status_code_map = {
        ErrorCategory.VALIDATION: 400,
        ErrorCategory.AUTHENTICATION: 401,
        ErrorCategory.AUTHORIZATION: 403,
        ErrorCategory.RATE_LIMITING: 429,
        ErrorCategory.MODEL_UNAVAILABLE: 503,
        ErrorCategory.SYSTEM: 500,
        ErrorCategory.INFRASTRUCTURE: 503,
        ErrorCategory.DATABASE: 500,
    }
    
    status_code = status_code_map.get(error_response.error.category, 500)
    
    return JSONResponse(
        content=error_response.__dict__,
        status_code=status_code
    )


def get_error_handler() -> GlobalErrorHandler:
    """Get global error handler instance."""
    return global_error_handler