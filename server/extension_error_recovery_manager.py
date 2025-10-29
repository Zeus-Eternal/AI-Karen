"""
Extension Error Recovery Manager

Implements comprehensive error recovery strategies for extension authentication failures,
service unavailability, and network errors using the strategy pattern.

Requirements addressed:
- 3.1: Extension integration service error handling
- 3.2: Extension API calls with proper authentication
- 3.3: Authentication failures and retry logic
- 9.1: Graceful degradation when authentication fails
- 9.2: Fallback behavior for extension unavailability
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Extension error categories"""
    AUTHENTICATION = "authentication"
    SERVICE_UNAVAILABLE = "service_unavailable"
    NETWORK = "network"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(str, Enum):
    """Recovery strategies"""
    RETRY_WITH_REFRESH = "retry_with_refresh"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_TO_READONLY = "fallback_to_readonly"
    FALLBACK_TO_CACHED = "fallback_to_cached"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    SERVICE_RESTART = "service_restart"
    CONNECTION_RESET = "connection_reset"
    ESCALATE_TO_ADMIN = "escalate_to_admin"
    NO_RECOVERY = "no_recovery"


@dataclass
class ExtensionError:
    """Extension error information"""
    category: ErrorCategory
    severity: ErrorSeverity
    code: str
    message: str
    technical_details: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    endpoint: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class RecoveryAttempt:
    """Recovery attempt information"""
    error: ExtensionError
    strategy: RecoveryStrategy
    attempt_number: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    recovery_data: Optional[Dict[str, Any]] = None
    next_attempt_delay: Optional[float] = None


@dataclass
class RecoveryResult:
    """Recovery operation result"""
    success: bool
    strategy: RecoveryStrategy
    message: str
    fallback_data: Optional[Any] = None
    retry_after: Optional[float] = None
    requires_user_action: bool = False
    escalated: bool = False


class RecoveryStrategyInterface(ABC):
    """Abstract base class for recovery strategies"""
    
    @abstractmethod
    async def can_handle(self, error: ExtensionError) -> bool:
        """Check if this strategy can handle the given error"""
        pass
    
    @abstractmethod
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        """Execute the recovery strategy"""
        pass
    
    @abstractmethod
    def get_max_attempts(self) -> int:
        """Get maximum number of attempts for this strategy"""
        pass
    
    @abstractmethod
    def get_base_delay(self) -> float:
        """Get base delay between attempts in seconds"""
        pass


class AuthTokenRefreshStrategy(RecoveryStrategyInterface):
    """Recovery strategy for authentication token refresh"""
    
    def __init__(self, auth_manager=None):
        self.auth_manager = auth_manager
    
    async def can_handle(self, error: ExtensionError) -> bool:
        return (
            error.category == ErrorCategory.AUTHENTICATION and
            error.code in ['TOKEN_EXPIRED', 'TOKEN_INVALID'] and
            self.auth_manager is not None
        )
    
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        try:
            logger.info(f"Attempting token refresh for error: {error.code}")
            
            # Attempt to refresh the token
            if hasattr(self.auth_manager, 'refresh_token'):
                new_token = await self.auth_manager.refresh_token()
                if new_token:
                    return RecoveryResult(
                        success=True,
                        strategy=RecoveryStrategy.RETRY_WITH_REFRESH,
                        message="Authentication token refreshed successfully",
                        requires_user_action=False
                    )
            
            # If refresh fails, redirect to login
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.RETRY_WITH_REFRESH,
                message="Token refresh failed, user authentication required",
                requires_user_action=True
            )
            
        except Exception as e:
            logger.error(f"Token refresh strategy failed: {e}")
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.RETRY_WITH_REFRESH,
                message=f"Token refresh error: {str(e)}",
                requires_user_action=True
            )
    
    def get_max_attempts(self) -> int:
        return 2
    
    def get_base_delay(self) -> float:
        return 1.0


class ServiceRestartStrategy(RecoveryStrategyInterface):
    """Recovery strategy for service restart"""
    
    def __init__(self, service_recovery_manager=None):
        self.service_recovery_manager = service_recovery_manager
    
    async def can_handle(self, error: ExtensionError) -> bool:
        return (
            error.category == ErrorCategory.SERVICE_UNAVAILABLE and
            error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and
            self.service_recovery_manager is not None
        )
    
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        try:
            logger.info(f"Attempting service restart for error: {error.code}")
            
            service_name = context.get('service_name', 'extension_service')
            
            # Attempt service restart through service recovery manager
            if hasattr(self.service_recovery_manager, 'force_recovery'):
                success = await self.service_recovery_manager.force_recovery(service_name)
                if success:
                    return RecoveryResult(
                        success=True,
                        strategy=RecoveryStrategy.SERVICE_RESTART,
                        message=f"Service {service_name} restarted successfully",
                        retry_after=5.0  # Wait 5 seconds before retry
                    )
            
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.SERVICE_RESTART,
                message=f"Failed to restart service {service_name}",
                retry_after=30.0  # Wait longer before next attempt
            )
            
        except Exception as e:
            logger.error(f"Service restart strategy failed: {e}")
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.SERVICE_RESTART,
                message=f"Service restart error: {str(e)}",
                retry_after=60.0
            )
    
    def get_max_attempts(self) -> int:
        return 3
    
    def get_base_delay(self) -> float:
        return 10.0


class NetworkRetryStrategy(RecoveryStrategyInterface):
    """Recovery strategy for network errors with exponential backoff"""
    
    async def can_handle(self, error: ExtensionError) -> bool:
        return error.category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]
    
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        try:
            # Calculate exponential backoff delay
            delay = self.get_base_delay() * (2 ** error.retry_count)
            max_delay = 60.0  # Maximum 60 seconds
            delay = min(delay, max_delay)
            
            logger.info(f"Network retry strategy: waiting {delay} seconds before retry")
            
            return RecoveryResult(
                success=False,  # Will retry after delay
                strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                message=f"Network error, retrying in {delay:.1f} seconds",
                retry_after=delay
            )
            
        except Exception as e:
            logger.error(f"Network retry strategy failed: {e}")
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                message=f"Network retry error: {str(e)}",
                retry_after=30.0
            )
    
    def get_max_attempts(self) -> int:
        return 5
    
    def get_base_delay(self) -> float:
        return 2.0


class GracefulDegradationStrategy(RecoveryStrategyInterface):
    """Recovery strategy for graceful degradation"""
    
    def __init__(self, degradation_manager=None):
        self.degradation_manager = degradation_manager
    
    async def can_handle(self, error: ExtensionError) -> bool:
        return error.severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]
    
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        try:
            logger.info(f"Applying graceful degradation for error: {error.code}")
            
            # Get fallback data based on operation
            fallback_data = self._get_fallback_data(error.operation, context)
            
            # Apply degradation if manager is available
            if self.degradation_manager and hasattr(self.degradation_manager, 'apply_degradation'):
                await self.degradation_manager.apply_degradation(error.category, error.operation)
            
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                message="Extension features are temporarily limited",
                fallback_data=fallback_data
            )
            
        except Exception as e:
            logger.error(f"Graceful degradation strategy failed: {e}")
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                message=f"Degradation error: {str(e)}"
            )
    
    def _get_fallback_data(self, operation: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback data for the operation"""
        if operation == "list_extensions":
            return {
                "extensions": [],
                "total": 0,
                "message": "Extension list temporarily unavailable"
            }
        elif operation == "background_tasks":
            return {
                "tasks": [],
                "total": 0,
                "message": "Background tasks temporarily unavailable"
            }
        else:
            return {
                "message": "Feature temporarily unavailable",
                "fallback": True
            }
    
    def get_max_attempts(self) -> int:
        return 1  # Immediate fallback
    
    def get_base_delay(self) -> float:
        return 0.0


class CachedDataStrategy(RecoveryStrategyInterface):
    """Recovery strategy using cached data"""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
    
    async def can_handle(self, error: ExtensionError) -> bool:
        return (
            error.category in [ErrorCategory.SERVICE_UNAVAILABLE, ErrorCategory.NETWORK] and
            self.cache_manager is not None
        )
    
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        try:
            logger.info(f"Attempting cached data recovery for error: {error.code}")
            
            # Try to get cached data
            cache_key = f"{error.operation}:{error.endpoint}"
            cached_data = None
            
            if hasattr(self.cache_manager, 'get'):
                cached_data = await self.cache_manager.get(cache_key)
            
            if cached_data:
                return RecoveryResult(
                    success=True,
                    strategy=RecoveryStrategy.FALLBACK_TO_CACHED,
                    message="Using cached data while service is unavailable",
                    fallback_data=cached_data
                )
            else:
                # No cached data available, fall back to graceful degradation
                return RecoveryResult(
                    success=False,
                    strategy=RecoveryStrategy.FALLBACK_TO_CACHED,
                    message="No cached data available, using limited functionality"
                )
            
        except Exception as e:
            logger.error(f"Cached data strategy failed: {e}")
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.FALLBACK_TO_CACHED,
                message=f"Cache access error: {str(e)}"
            )
    
    def get_max_attempts(self) -> int:
        return 1
    
    def get_base_delay(self) -> float:
        return 0.0


class ReadOnlyFallbackStrategy(RecoveryStrategyInterface):
    """Recovery strategy for read-only fallback"""
    
    async def can_handle(self, error: ExtensionError) -> bool:
        return error.category == ErrorCategory.PERMISSION
    
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        try:
            logger.info(f"Applying read-only fallback for error: {error.code}")
            
            # Provide read-only version of the data
            readonly_data = self._get_readonly_data(error.operation, context)
            
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.FALLBACK_TO_READONLY,
                message="Extension features are available in read-only mode",
                fallback_data=readonly_data
            )
            
        except Exception as e:
            logger.error(f"Read-only fallback strategy failed: {e}")
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.FALLBACK_TO_READONLY,
                message=f"Read-only fallback error: {str(e)}"
            )
    
    def _get_readonly_data(self, operation: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get read-only version of data"""
        if operation == "list_extensions":
            return {
                "extensions": context.get("cached_extensions", []),
                "total": len(context.get("cached_extensions", [])),
                "readonly": True,
                "message": "Extension list in read-only mode"
            }
        else:
            return {
                "readonly": True,
                "message": "Feature available in read-only mode"
            }
    
    def get_max_attempts(self) -> int:
        return 1
    
    def get_base_delay(self) -> float:
        return 0.0


class EscalationStrategy(RecoveryStrategyInterface):
    """Recovery strategy for escalating to admin"""
    
    async def can_handle(self, error: ExtensionError) -> bool:
        return (
            error.severity == ErrorSeverity.CRITICAL or
            error.category == ErrorCategory.CONFIGURATION
        )
    
    async def execute(self, error: ExtensionError, context: Dict[str, Any]) -> RecoveryResult:
        try:
            logger.critical(f"Escalating error to admin: {error.code} - {error.message}")
            
            # Log critical alert with full context
            logger.critical(
                "CRITICAL EXTENSION ERROR - ADMIN INTERVENTION REQUIRED",
                extra={
                    "error_code": error.code,
                    "error_category": error.category.value,
                    "error_severity": error.severity.value,
                    "endpoint": error.endpoint,
                    "operation": error.operation,
                    "user_id": error.user_id,
                    "tenant_id": error.tenant_id,
                    "context": error.context,
                    "timestamp": error.timestamp.isoformat()
                }
            )
            
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ESCALATE_TO_ADMIN,
                message="Critical error escalated to system administrator",
                requires_user_action=True,
                escalated=True
            )
            
        except Exception as e:
            logger.error(f"Escalation strategy failed: {e}")
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ESCALATE_TO_ADMIN,
                message=f"Escalation error: {str(e)}",
                escalated=True
            )
    
    def get_max_attempts(self) -> int:
        return 1
    
    def get_base_delay(self) -> float:
        return 0.0


class ExtensionErrorRecoveryManager:
    """
    Comprehensive error recovery manager for extension authentication and service failures.
    
    Implements the strategy pattern to handle different types of errors with appropriate
    recovery mechanisms including authentication refresh, service restart, graceful
    degradation, and fallback to cached data.
    """
    
    def __init__(
        self,
        auth_manager=None,
        service_recovery_manager=None,
        degradation_manager=None,
        cache_manager=None
    ):
        self.auth_manager = auth_manager
        self.service_recovery_manager = service_recovery_manager
        self.degradation_manager = degradation_manager
        self.cache_manager = cache_manager
        
        # Recovery strategies
        self.strategies: List[RecoveryStrategyInterface] = []
        self._initialize_strategies()
        
        # Recovery tracking
        self.active_recoveries: Dict[str, RecoveryAttempt] = {}
        self.recovery_history: List[RecoveryAttempt] = []
        self.error_patterns: Dict[str, List[ExtensionError]] = {}
        
        # Configuration
        self.config = {
            "max_concurrent_recoveries": 10,
            "history_retention_hours": 24,
            "pattern_detection_window_minutes": 15,
            "pattern_threshold": 5,
            "global_circuit_breaker_threshold": 10,
            "circuit_breaker_reset_time_minutes": 5
        }
        
        # Circuit breaker state
        self.circuit_breaker_open = False
        self.circuit_breaker_opened_at: Optional[datetime] = None
        self.global_error_count = 0
        self.last_error_reset: datetime = datetime.now(timezone.utc)
    
    def _initialize_strategies(self):
        """Initialize recovery strategies in priority order"""
        self.strategies = [
            AuthTokenRefreshStrategy(self.auth_manager),
            ServiceRestartStrategy(self.service_recovery_manager),
            CachedDataStrategy(self.cache_manager),
            ReadOnlyFallbackStrategy(),
            NetworkRetryStrategy(),
            GracefulDegradationStrategy(self.degradation_manager),
            EscalationStrategy()
        ]
    
    async def handle_error(
        self,
        error: ExtensionError,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """
        Handle an extension error with appropriate recovery strategy.
        
        Args:
            error: The extension error to handle
            context: Additional context for recovery
            
        Returns:
            RecoveryResult with recovery outcome
        """
        if context is None:
            context = {}
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.NO_RECOVERY,
                message="Circuit breaker is open, recovery temporarily disabled",
                retry_after=60.0
            )
        
        # Update error tracking
        self._track_error(error)
        
        # Check for error patterns
        if self._detect_error_pattern(error):
            logger.warning(f"Error pattern detected for {error.category.value}")
            # Could trigger additional actions like circuit breaker
        
        # Generate recovery key
        recovery_key = self._generate_recovery_key(error)
        
        # Check if recovery is already in progress
        if recovery_key in self.active_recoveries:
            existing_attempt = self.active_recoveries[recovery_key]
            if existing_attempt.completed_at is None:
                return RecoveryResult(
                    success=False,
                    strategy=existing_attempt.strategy,
                    message="Recovery already in progress",
                    retry_after=5.0
                )
        
        # Find appropriate recovery strategy
        strategy = await self._select_recovery_strategy(error)
        if not strategy:
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.NO_RECOVERY,
                message="No suitable recovery strategy found"
            )
        
        # Create recovery attempt
        attempt = RecoveryAttempt(
            error=error,
            strategy=strategy.__class__.__name__.replace('Strategy', '').lower(),
            attempt_number=error.retry_count + 1,
            started_at=datetime.now(timezone.utc)
        )
        
        self.active_recoveries[recovery_key] = attempt
        
        try:
            # Execute recovery strategy
            logger.info(f"Executing recovery strategy {strategy.__class__.__name__} for error {error.code}")
            result = await strategy.execute(error, context)
            
            # Update attempt
            attempt.completed_at = datetime.now(timezone.utc)
            attempt.success = result.success
            attempt.recovery_data = {
                "message": result.message,
                "fallback_data": result.fallback_data,
                "requires_user_action": result.requires_user_action,
                "escalated": result.escalated
            }
            
            if not result.success and result.retry_after:
                attempt.next_attempt_delay = result.retry_after
            
            # Move to history
            self.recovery_history.append(attempt)
            del self.active_recoveries[recovery_key]
            
            # Update circuit breaker
            if result.success:
                self._reset_circuit_breaker()
            else:
                self._increment_error_count()
            
            return result
            
        except Exception as e:
            logger.error(f"Recovery strategy execution failed: {e}")
            
            # Update attempt with error
            attempt.completed_at = datetime.now(timezone.utc)
            attempt.success = False
            attempt.error_message = str(e)
            
            # Move to history
            self.recovery_history.append(attempt)
            if recovery_key in self.active_recoveries:
                del self.active_recoveries[recovery_key]
            
            # Increment error count
            self._increment_error_count()
            
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.NO_RECOVERY,
                message=f"Recovery execution failed: {str(e)}"
            )
    
    async def _select_recovery_strategy(self, error: ExtensionError) -> Optional[RecoveryStrategyInterface]:
        """Select the most appropriate recovery strategy for the error"""
        for strategy in self.strategies:
            try:
                if await strategy.can_handle(error):
                    # Check if we haven't exceeded max attempts for this strategy
                    strategy_name = strategy.__class__.__name__
                    strategy_attempts = sum(
                        1 for attempt in self.recovery_history
                        if (attempt.error.code == error.code and 
                            attempt.strategy == strategy_name.replace('Strategy', '').lower() and
                            attempt.started_at > datetime.now(timezone.utc) - timedelta(hours=1))
                    )
                    
                    if strategy_attempts < strategy.get_max_attempts():
                        return strategy
                    else:
                        logger.debug(f"Strategy {strategy_name} exceeded max attempts for error {error.code}")
                        
            except Exception as e:
                logger.error(f"Error checking strategy {strategy.__class__.__name__}: {e}")
                continue
        
        return None
    
    def _generate_recovery_key(self, error: ExtensionError) -> str:
        """Generate a unique key for tracking recovery attempts"""
        return f"{error.category.value}:{error.code}:{error.endpoint}:{error.operation}"
    
    def _track_error(self, error: ExtensionError):
        """Track error for pattern detection"""
        pattern_key = f"{error.category.value}:{error.code}"
        
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = []
        
        self.error_patterns[pattern_key].append(error)
        
        # Clean up old errors outside the detection window
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=self.config["pattern_detection_window_minutes"]
        )
        
        self.error_patterns[pattern_key] = [
            e for e in self.error_patterns[pattern_key]
            if e.timestamp >= cutoff_time
        ]
    
    def _detect_error_pattern(self, error: ExtensionError) -> bool:
        """Detect if there's an error pattern that might indicate a systemic issue"""
        pattern_key = f"{error.category.value}:{error.code}"
        
        if pattern_key in self.error_patterns:
            recent_errors = len(self.error_patterns[pattern_key])
            return recent_errors >= self.config["pattern_threshold"]
        
        return False
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if the circuit breaker is open"""
        if not self.circuit_breaker_open:
            return False
        
        # Check if circuit breaker should be reset
        if self.circuit_breaker_opened_at:
            reset_time = self.circuit_breaker_opened_at + timedelta(
                minutes=self.config["circuit_breaker_reset_time_minutes"]
            )
            
            if datetime.now(timezone.utc) >= reset_time:
                self._reset_circuit_breaker()
                return False
        
        return True
    
    def _increment_error_count(self):
        """Increment global error count and check circuit breaker"""
        now = datetime.now(timezone.utc)
        
        # Reset count if it's been more than an hour
        if now - self.last_error_reset > timedelta(hours=1):
            self.global_error_count = 0
            self.last_error_reset = now
        
        self.global_error_count += 1
        
        # Open circuit breaker if threshold exceeded
        if self.global_error_count >= self.config["global_circuit_breaker_threshold"]:
            self.circuit_breaker_open = True
            self.circuit_breaker_opened_at = now
            logger.warning(
                f"Circuit breaker opened due to {self.global_error_count} errors in the last hour"
            )
    
    def _reset_circuit_breaker(self):
        """Reset the circuit breaker"""
        if self.circuit_breaker_open:
            self.circuit_breaker_open = False
            self.circuit_breaker_opened_at = None
            logger.info("Circuit breaker reset")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics and metrics"""
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        
        recent_attempts = [
            attempt for attempt in self.recovery_history
            if attempt.started_at >= last_24h
        ]
        
        successful_attempts = [attempt for attempt in recent_attempts if attempt.success]
        failed_attempts = [attempt for attempt in recent_attempts if not attempt.success]
        
        # Strategy success rates
        strategy_stats = {}
        for attempt in recent_attempts:
            strategy = attempt.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"total": 0, "successful": 0}
            
            strategy_stats[strategy]["total"] += 1
            if attempt.success:
                strategy_stats[strategy]["successful"] += 1
        
        # Calculate success rates
        for strategy, stats in strategy_stats.items():
            stats["success_rate"] = stats["successful"] / stats["total"] if stats["total"] > 0 else 0
        
        # Error pattern statistics
        pattern_stats = {}
        for pattern_key, errors in self.error_patterns.items():
            recent_pattern_errors = [e for e in errors if e.timestamp >= last_24h]
            if recent_pattern_errors:
                pattern_stats[pattern_key] = len(recent_pattern_errors)
        
        return {
            "total_attempts_24h": len(recent_attempts),
            "successful_attempts_24h": len(successful_attempts),
            "failed_attempts_24h": len(failed_attempts),
            "success_rate_24h": len(successful_attempts) / len(recent_attempts) if recent_attempts else 0,
            "active_recoveries": len(self.active_recoveries),
            "strategy_statistics": strategy_stats,
            "error_patterns": pattern_stats,
            "circuit_breaker_open": self.circuit_breaker_open,
            "circuit_breaker_opened_at": self.circuit_breaker_opened_at.isoformat() if self.circuit_breaker_opened_at else None,
            "global_error_count": self.global_error_count,
            "last_error_reset": self.last_error_reset.isoformat()
        }
    
    def get_active_recoveries(self) -> List[Dict[str, Any]]:
        """Get information about active recovery attempts"""
        return [
            {
                "recovery_key": key,
                "error_code": attempt.error.code,
                "error_category": attempt.error.category.value,
                "strategy": attempt.strategy,
                "attempt_number": attempt.attempt_number,
                "started_at": attempt.started_at.isoformat(),
                "duration_seconds": (datetime.now(timezone.utc) - attempt.started_at).total_seconds()
            }
            for key, attempt in self.active_recoveries.items()
        ]
    
    def clear_recovery_history(self):
        """Clear recovery history"""
        self.recovery_history.clear()
        self.error_patterns.clear()
        logger.info("Recovery history cleared")
    
    def force_circuit_breaker_reset(self):
        """Force reset the circuit breaker (admin function)"""
        self._reset_circuit_breaker()
        self.global_error_count = 0
        self.last_error_reset = datetime.now(timezone.utc)
        logger.info("Circuit breaker force reset by admin")


# Global instance
_recovery_manager: Optional[ExtensionErrorRecoveryManager] = None


def initialize_extension_error_recovery_manager(
    auth_manager=None,
    service_recovery_manager=None,
    degradation_manager=None,
    cache_manager=None
) -> ExtensionErrorRecoveryManager:
    """Initialize the global extension error recovery manager"""
    global _recovery_manager
    
    _recovery_manager = ExtensionErrorRecoveryManager(
        auth_manager=auth_manager,
        service_recovery_manager=service_recovery_manager,
        degradation_manager=degradation_manager,
        cache_manager=cache_manager
    )
    
    logger.info("Extension error recovery manager initialized")
    return _recovery_manager


def get_extension_error_recovery_manager() -> Optional[ExtensionErrorRecoveryManager]:
    """Get the global extension error recovery manager"""
    return _recovery_manager


def shutdown_extension_error_recovery_manager():
    """Shutdown the global extension error recovery manager"""
    global _recovery_manager
    _recovery_manager = None
    logger.info("Extension error recovery manager shutdown")


# Convenience functions
async def handle_extension_error(
    error: ExtensionError,
    context: Optional[Dict[str, Any]] = None
) -> RecoveryResult:
    """Handle an extension error using the global recovery manager"""
    manager = get_extension_error_recovery_manager()
    if not manager:
        return RecoveryResult(
            success=False,
            strategy=RecoveryStrategy.NO_RECOVERY,
            message="Error recovery manager not initialized"
        )
    
    return await manager.handle_error(error, context)


def create_extension_error(
    category: ErrorCategory,
    severity: ErrorSeverity,
    code: str,
    message: str,
    **kwargs
) -> ExtensionError:
    """Create an extension error with the given parameters"""
    return ExtensionError(
        category=category,
        severity=severity,
        code=code,
        message=message,
        **kwargs
    )


# Error factory functions for common error types
def create_auth_token_expired_error(endpoint: str, operation: str, **kwargs) -> ExtensionError:
    """Create a token expired error"""
    return create_extension_error(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        code="TOKEN_EXPIRED",
        message="Authentication token has expired",
        endpoint=endpoint,
        operation=operation,
        **kwargs
    )


def create_service_unavailable_error(endpoint: str, operation: str, **kwargs) -> ExtensionError:
    """Create a service unavailable error"""
    return create_extension_error(
        category=ErrorCategory.SERVICE_UNAVAILABLE,
        severity=ErrorSeverity.HIGH,
        code="SERVICE_UNAVAILABLE",
        message="Extension service is temporarily unavailable",
        endpoint=endpoint,
        operation=operation,
        **kwargs
    )


def create_network_error(endpoint: str, operation: str, **kwargs) -> ExtensionError:
    """Create a network error"""
    return create_extension_error(
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        code="NETWORK_ERROR",
        message="Network connection failed",
        endpoint=endpoint,
        operation=operation,
        **kwargs
    )


def create_permission_denied_error(endpoint: str, operation: str, **kwargs) -> ExtensionError:
    """Create a permission denied error"""
    return create_extension_error(
        category=ErrorCategory.PERMISSION,
        severity=ErrorSeverity.HIGH,
        code="PERMISSION_DENIED",
        message="Insufficient permissions for this operation",
        endpoint=endpoint,
        operation=operation,
        **kwargs
    )