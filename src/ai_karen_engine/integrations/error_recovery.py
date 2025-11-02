"""
Error Recovery System for LLM Providers

Comprehensive error handling and recovery mechanisms for provider failures.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING
import asyncio
from datetime import datetime, timedelta

from ai_karen_engine.integrations.registry import get_registry

if TYPE_CHECKING:
    from ai_karen_engine.integrations.registry import LLMRegistry

logger = logging.getLogger("kari.error_recovery")


class ErrorType(Enum):
    """Classification of provider errors."""
    CONFIGURATION_ERROR = "configuration_error"
    AUTHENTICATION_ERROR = "authentication_error"
    NETWORK_ERROR = "network_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    MODEL_UNAVAILABLE = "model_unavailable"
    CAPABILITY_MISSING = "capability_missing"
    TIMEOUT_ERROR = "timeout_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVER_ERROR = "server_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ClassifiedError:
    """Classified error with recovery information."""
    error_type: ErrorType
    provider_name: str
    original_error: Exception
    error_message: str
    recovery_suggestions: List[str]
    is_recoverable: bool
    estimated_recovery_time: Optional[int] = None
    retry_count: int = 0


@dataclass
class RecoveryAction:
    """Action to take for error recovery."""
    action_type: str  # retry, fallback, skip, degraded_mode
    delay_seconds: Optional[float] = None
    alternative_provider: Optional[str] = None
    user_message: Optional[str] = None
    admin_message: Optional[str] = None
    max_attempts: int = 3


@dataclass
class RetryAttempt:
    """Record of a retry attempt."""
    timestamp: datetime
    provider_name: str
    error_type: ErrorType
    attempt_number: int
    success: bool
    error_message: Optional[str] = None
    delay_used: Optional[float] = None


@dataclass
class RetryResult:
    """Result of retry operation."""
    success: bool
    result: Any = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    final_error: Optional[Exception] = None
    total_time: float = 0.0


@dataclass
class AuthRecoveryResult:
    """Result of authentication recovery attempt."""
    success: bool
    new_key_valid: bool = False
    error_message: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)


@dataclass
class RateLimitAction:
    """Action for rate limit handling."""
    should_retry: bool
    delay_seconds: int
    alternative_provider: Optional[str] = None
    user_message: Optional[str] = None


class ErrorRecoverySystem:
    """Comprehensive error recovery system for LLM providers."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        registry: Optional["LLMRegistry"] = None,
    ):
        """
        Initialize error recovery system.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff
            registry: Optional registry instance for provider metadata
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.retry_history: Dict[str, List[RetryAttempt]] = {}
        self.error_patterns: Dict[str, List[ClassifiedError]] = {}
        self.recovery_stats: Dict[str, Dict[str, int]] = {}
        self._registry: Optional["LLMRegistry"] = registry or get_registry()

    def classify_error(self, provider_name: str, error: Exception, context: Dict[str, Any] = None) -> ClassifiedError:
        """
        Classify an error and determine recovery strategy.
        
        Args:
            provider_name: Name of the provider that failed
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            ClassifiedError with recovery information
        """
        error_str = str(error).lower()
        context = context or {}
        
        # Classify error type
        error_type = self._determine_error_type(error_str, error)
        
        # Determine if recoverable
        is_recoverable = self._is_recoverable_error(error_type, error_str)
        
        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions(error_type, provider_name, error_str)
        
        # Estimate recovery time
        recovery_time = self._estimate_recovery_time(error_type, error_str)
        
        classified_error = ClassifiedError(
            error_type=error_type,
            provider_name=provider_name,
            original_error=error,
            error_message=str(error),
            recovery_suggestions=recovery_suggestions,
            is_recoverable=is_recoverable,
            estimated_recovery_time=recovery_time
        )
        
        # Store error pattern for analysis
        if provider_name not in self.error_patterns:
            self.error_patterns[provider_name] = []
        self.error_patterns[provider_name].append(classified_error)
        
        return classified_error

    def _determine_error_type(self, error_str: str, error: Exception) -> ErrorType:
        """Determine the type of error based on error message and exception."""
        # Authentication errors
        if any(pattern in error_str for pattern in [
            "api key", "unauthorized", "invalid key", "authentication", "401"
        ]):
            return ErrorType.AUTHENTICATION_ERROR
            
        # Rate limiting
        if any(pattern in error_str for pattern in [
            "rate limit", "too many requests", "429", "quota exceeded"
        ]):
            if "quota" in error_str:
                return ErrorType.QUOTA_EXCEEDED
            return ErrorType.RATE_LIMIT_ERROR
            
        # Network errors
        if any(pattern in error_str for pattern in [
            "connection", "timeout", "network", "dns", "unreachable", "502", "503", "504"
        ]):
            if "timeout" in error_str:
                return ErrorType.TIMEOUT_ERROR
            return ErrorType.NETWORK_ERROR
            
        # Model errors
        if any(pattern in error_str for pattern in [
            "model not found", "model unavailable", "invalid model", "model does not exist"
        ]):
            return ErrorType.MODEL_UNAVAILABLE
            
        # Capability errors
        if any(pattern in error_str for pattern in [
            "not supported", "capability", "feature not available", "function calling"
        ]):
            return ErrorType.CAPABILITY_MISSING
            
        # Server errors
        if any(pattern in error_str for pattern in [
            "server error", "internal error", "500", "502", "503"
        ]):
            return ErrorType.SERVER_ERROR
            
        # Configuration errors
        if any(pattern in error_str for pattern in [
            "configuration", "invalid parameter", "missing required", "400"
        ]):
            return ErrorType.CONFIGURATION_ERROR
            
        return ErrorType.UNKNOWN_ERROR

    def _is_recoverable_error(self, error_type: ErrorType, error_str: str) -> bool:
        """Determine if an error is recoverable."""
        # Always recoverable
        recoverable_types = {
            ErrorType.RATE_LIMIT_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR,
            ErrorType.SERVER_ERROR
        }
        
        # Never recoverable
        non_recoverable_types = {
            ErrorType.AUTHENTICATION_ERROR,
            ErrorType.CONFIGURATION_ERROR,
            ErrorType.MODEL_UNAVAILABLE,
            ErrorType.CAPABILITY_MISSING
        }
        
        if error_type in recoverable_types:
            return True
        elif error_type in non_recoverable_types:
            return False
        else:
            # For unknown errors, check specific patterns
            return not any(pattern in error_str for pattern in [
                "invalid", "forbidden", "not found", "unauthorized"
            ])

    def _generate_recovery_suggestions(self, error_type: ErrorType, provider_name: str, error_str: str) -> List[str]:
        """Generate recovery suggestions based on error type."""
        suggestions = []
        
        if error_type == ErrorType.AUTHENTICATION_ERROR:
            suggestions.extend([
                f"Check {provider_name.upper()}_API_KEY environment variable",
                "Verify API key is valid and not expired",
                "Ensure API key has necessary permissions",
                "Try regenerating the API key from provider dashboard"
            ])
            
        elif error_type == ErrorType.RATE_LIMIT_ERROR:
            suggestions.extend([
                "Wait for rate limit to reset",
                "Consider upgrading to higher tier plan",
                "Implement request batching",
                "Use alternative provider temporarily"
            ])
            
        elif error_type == ErrorType.QUOTA_EXCEEDED:
            suggestions.extend([
                "Check account billing and usage limits",
                "Upgrade to higher quota plan",
                "Wait for quota reset period",
                "Use alternative provider"
            ])
            
        elif error_type == ErrorType.NETWORK_ERROR:
            suggestions.extend([
                "Check internet connectivity",
                "Verify firewall settings",
                "Try different network or VPN",
                "Check provider service status"
            ])
            
        elif error_type == ErrorType.TIMEOUT_ERROR:
            suggestions.extend([
                "Increase timeout settings",
                "Check network stability",
                "Try smaller request sizes",
                "Use streaming for long responses"
            ])
            
        elif error_type == ErrorType.MODEL_UNAVAILABLE:
            suggestions.extend([
                "Check available models list",
                "Use alternative model",
                "Verify model name spelling",
                "Check if model requires special access"
            ])
            
        elif error_type == ErrorType.SERVER_ERROR:
            suggestions.extend([
                "Retry after brief delay",
                "Check provider status page",
                "Use alternative provider",
                "Report issue to provider support"
            ])
            
        elif error_type == ErrorType.CONFIGURATION_ERROR:
            suggestions.extend([
                "Review configuration parameters",
                "Check parameter formats and ranges",
                "Consult provider documentation",
                "Validate all required fields"
            ])
            
        return suggestions

    def _estimate_recovery_time(self, error_type: ErrorType, error_str: str) -> Optional[int]:
        """Estimate recovery time in seconds."""
        if error_type == ErrorType.RATE_LIMIT_ERROR:
            # Try to extract retry-after from error message
            import re
            match = re.search(r'retry after (\d+)', error_str)
            if match:
                return int(match.group(1))
            return 60  # Default 1 minute
            
        elif error_type == ErrorType.TIMEOUT_ERROR:
            return 30  # 30 seconds
            
        elif error_type == ErrorType.NETWORK_ERROR:
            return 60  # 1 minute
            
        elif error_type == ErrorType.SERVER_ERROR:
            return 120  # 2 minutes
            
        elif error_type == ErrorType.QUOTA_EXCEEDED:
            return 3600  # 1 hour
            
        return None  # No estimate for other types

    def handle_provider_error(self, provider_name: str, error: Exception, context: Dict[str, Any] = None) -> RecoveryAction:
        """
        Handle provider-specific errors with appropriate recovery actions.
        
        Args:
            provider_name: Name of the provider that failed
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            RecoveryAction with recommended action
        """
        classified_error = self.classify_error(provider_name, error, context)
        
        # Update recovery stats
        if provider_name not in self.recovery_stats:
            self.recovery_stats[provider_name] = {}
        error_type_str = classified_error.error_type.value
        self.recovery_stats[provider_name][error_type_str] = \
            self.recovery_stats[provider_name].get(error_type_str, 0) + 1
        
        # Determine recovery action
        if not classified_error.is_recoverable:
            return RecoveryAction(
                action_type="fallback",
                user_message=f"Provider {provider_name} unavailable: {classified_error.error_message}",
                admin_message=f"Non-recoverable error in {provider_name}: {classified_error.error_message}"
            )
        
        # For recoverable errors, determine retry strategy
        if classified_error.error_type == ErrorType.RATE_LIMIT_ERROR:
            delay = classified_error.estimated_recovery_time or 60
            return RecoveryAction(
                action_type="retry",
                delay_seconds=delay,
                max_attempts=2,  # Fewer retries for rate limits
                user_message=f"Rate limited, retrying in {delay} seconds",
                admin_message=f"Rate limit hit for {provider_name}, waiting {delay}s"
            )
            
        elif classified_error.error_type in [ErrorType.TIMEOUT_ERROR, ErrorType.NETWORK_ERROR, ErrorType.SERVER_ERROR]:
            return RecoveryAction(
                action_type="retry",
                delay_seconds=self.base_delay,
                max_attempts=self.max_retries,
                user_message="Temporary connectivity issue, retrying...",
                admin_message=f"Retrying {provider_name} after {classified_error.error_type.value}"
            )
            
        else:
            # Unknown recoverable error
            return RecoveryAction(
                action_type="retry",
                delay_seconds=self.base_delay * 2,
                max_attempts=2,
                user_message="Temporary issue, retrying...",
                admin_message=f"Unknown recoverable error in {provider_name}: {classified_error.error_message}"
            )

    def retry_with_backoff(self, operation: Callable, provider_name: str, max_attempts: int = None) -> RetryResult:
        """
        Retry operation with exponential backoff.
        
        Args:
            operation: Function to retry
            provider_name: Name of the provider
            max_attempts: Maximum retry attempts (uses default if None)
            
        Returns:
            RetryResult with operation result and attempt history
        """
        max_attempts = max_attempts or self.max_retries
        attempts = []
        start_time = time.time()
        
        for attempt in range(max_attempts):
            attempt_start = time.time()
            
            try:
                result = operation()
                
                # Record successful attempt
                attempt_record = RetryAttempt(
                    timestamp=datetime.now(),
                    provider_name=provider_name,
                    error_type=ErrorType.UNKNOWN_ERROR,  # No error
                    attempt_number=attempt + 1,
                    success=True
                )
                attempts.append(attempt_record)
                
                # Update retry history
                if provider_name not in self.retry_history:
                    self.retry_history[provider_name] = []
                self.retry_history[provider_name].extend(attempts)
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=time.time() - start_time
                )
                
            except Exception as ex:
                # Classify the error
                classified_error = self.classify_error(provider_name, ex)
                
                # Calculate delay for next attempt
                delay = min(self.base_delay * (2 ** attempt), 60)  # Cap at 60 seconds
                
                # Record failed attempt
                attempt_record = RetryAttempt(
                    timestamp=datetime.now(),
                    provider_name=provider_name,
                    error_type=classified_error.error_type,
                    attempt_number=attempt + 1,
                    success=False,
                    error_message=str(ex),
                    delay_used=delay if attempt < max_attempts - 1 else None
                )
                attempts.append(attempt_record)
                
                # Check if we should continue retrying
                if not classified_error.is_recoverable or attempt >= max_attempts - 1:
                    break
                    
                # Wait before next attempt
                logger.warning(f"Attempt {attempt + 1} failed for {provider_name}, retrying in {delay}s: {ex}")
                time.sleep(delay)
        
        # Update retry history
        if provider_name not in self.retry_history:
            self.retry_history[provider_name] = []
        self.retry_history[provider_name].extend(attempts)
        
        return RetryResult(
            success=False,
            attempts=attempts,
            final_error=attempts[-1].error_message if attempts else None,
            total_time=time.time() - start_time
        )

    def handle_rate_limit(self, provider_name: str, retry_after: Optional[int] = None) -> RateLimitAction:
        """
        Handle rate limit errors with appropriate delays.
        
        Args:
            provider_name: Name of the rate-limited provider
            retry_after: Retry-after value from response headers
            
        Returns:
            RateLimitAction with recommended action
        """
        # Use provided retry-after or calculate based on provider
        if retry_after:
            delay = min(retry_after, 300)  # Cap at 5 minutes
        else:
            # Default delays by provider
            provider_delays = {
                "openai": 60,
                "anthropic": 60,
                "google": 30,
                "deepseek": 30,
                "local": 5
            }
            delay = provider_delays.get(provider_name.lower(), 60)
        
        alternative_provider = self._select_alternative_provider(provider_name)

        if alternative_provider:
            user_message = (
                f"Rate limited by {provider_name}, switching to {alternative_provider}"
                f" after waiting {delay} seconds"
            )
        else:
            user_message = (
                f"Rate limited by {provider_name}, waiting {delay} seconds before retry"
            )

        return RateLimitAction(
            should_retry=True,
            delay_seconds=delay,
            alternative_provider=alternative_provider,
            user_message=user_message,
        )

    def _select_alternative_provider(self, provider_name: str) -> Optional[str]:
        """Select an alternative provider using registry metadata."""

        if not self._registry:
            logger.debug("Registry unavailable, cannot determine alternative provider")
            return None

        try:
            healthy_providers = set(self._registry.list_llm_providers(healthy_only=True))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Failed to list healthy providers from registry: %s", exc
            )
            healthy_providers = set()

        try:
            spec = self._registry.get_provider_spec(provider_name)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Unable to load provider spec for %s: %s", provider_name, exc
            )
            spec = None

        candidate_names: List[str] = []

        if spec and spec.can_fallback_to:
            candidate_names.extend(spec.can_fallback_to)

        if not candidate_names and healthy_providers:
            # Choose highest priority healthy provider
            ranked: List[Tuple[int, str]] = []
            for candidate in healthy_providers:
                if candidate == provider_name:
                    continue
                candidate_spec = self._registry.get_provider_spec(candidate)
                if not candidate_spec:
                    continue
                ranked.append((candidate_spec.fallback_priority, candidate))

            if ranked:
                ranked.sort(reverse=True)
                return ranked[0][1]
            return None

        for candidate in candidate_names:
            if candidate == provider_name:
                continue
            if healthy_providers and candidate not in healthy_providers:
                continue
            return candidate

        # As a last resort pick any other provider
        if not healthy_providers:
            try:
                all_providers = self._registry.list_llm_providers(healthy_only=False)
            except Exception:  # pragma: no cover - defensive logging
                return None
        else:
            all_providers = list(healthy_providers)

        for candidate in all_providers:
            if candidate != provider_name:
                return candidate

        return None

    def recover_authentication(self, provider_name: str) -> AuthRecoveryResult:
        """
        Attempt to recover from authentication errors.
        
        Args:
            provider_name: Name of the provider with auth issues
            
        Returns:
            AuthRecoveryResult with recovery status
        """
        suggestions = [
            f"Check {provider_name.upper()}_API_KEY environment variable",
            "Verify API key is valid and not expired",
            "Ensure API key has necessary permissions"
        ]
        
        # For now, we can't automatically fix auth issues
        # This would require integration with key management systems
        return AuthRecoveryResult(
            success=False,
            new_key_valid=False,
            error_message="Authentication recovery requires manual intervention",
            recovery_suggestions=suggestions
        )

    def get_error_statistics(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get error statistics for analysis.
        
        Args:
            provider_name: Specific provider to analyze (all if None)
            
        Returns:
            Dictionary with error statistics
        """
        if provider_name:
            providers = [provider_name] if provider_name in self.error_patterns else []
        else:
            providers = list(self.error_patterns.keys())
        
        stats = {}
        
        for provider in providers:
            errors = self.error_patterns.get(provider, [])
            retries = self.retry_history.get(provider, [])
            
            # Error type distribution
            error_types = {}
            for error in errors:
                error_type = error.error_type.value
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Retry statistics
            total_retries = len(retries)
            successful_retries = sum(1 for r in retries if r.success)
            retry_success_rate = successful_retries / total_retries if total_retries > 0 else 0
            
            # Recent error patterns (last hour)
            recent_cutoff = datetime.now() - timedelta(hours=1)
            recent_errors = [e for e in errors if hasattr(e, 'timestamp') and e.timestamp > recent_cutoff]
            
            stats[provider] = {
                "total_errors": len(errors),
                "error_types": error_types,
                "total_retries": total_retries,
                "successful_retries": successful_retries,
                "retry_success_rate": retry_success_rate,
                "recent_errors": len(recent_errors),
                "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
            }
        
        return stats

    def clear_history(self, provider_name: Optional[str] = None, older_than_hours: int = 24):
        """
        Clear error history older than specified time.
        
        Args:
            provider_name: Specific provider to clear (all if None)
            older_than_hours: Clear entries older than this many hours
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        providers = [provider_name] if provider_name else list(self.retry_history.keys())
        
        for provider in providers:
            if provider in self.retry_history:
                self.retry_history[provider] = [
                    attempt for attempt in self.retry_history[provider]
                    if attempt.timestamp > cutoff_time
                ]
            
            if provider in self.error_patterns:
                # Note: error_patterns don't have timestamps by default
                # This would need to be added to ClassifiedError if needed
                pass