"""
Circuit Breaker Pattern Implementation

This module provides circuit breaker functionality to prevent cascading failures
and provide fault tolerance for distributed systems and external dependencies.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from threading import Lock

from .error_classifier import ErrorClassification, ErrorCategory, ErrorSeverity


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"           # Normal operation, requests pass through
    OPEN = "open"               # Circuit is open, requests fail immediately
    HALF_OPEN = "half_open"     # Testing if service has recovered


class CircuitBreakerPolicy(Enum):
    """Circuit breaker opening policies."""
    
    FAILURE_COUNT = "failure_count"           # Open after N failures
    FAILURE_RATE = "failure_rate"             # Open after X% failure rate
    CONSECUTIVE_FAILURES = "consecutive_failures"  # Open after N consecutive failures
    HYBRID = "hybrid"                        # Combination of policies


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    # Basic configuration
    name: str
    failure_threshold: int = 5
    timeout: float = 60.0
    half_open_max_calls: int = 3
    
    # Policy configuration
    policy: CircuitBreakerPolicy = CircuitBreakerPolicy.FAILURE_COUNT
    failure_rate_threshold: float = 0.5
    consecutive_failure_threshold: int = 3
    min_samples: int = 10
    
    # Time-based configuration
    sliding_window_size: float = 300.0  # 5 minutes
    recovery_timeout: float = 30.0
    
    # Advanced configuration
    auto_reset: bool = True
    notify_on_state_change: bool = True
    metrics_enabled: bool = True
    
    # Exception filtering
    ignored_exceptions: List[type] = field(default_factory=list)
    tracked_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    request_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


class CircuitBreaker:
    """
    Circuit breaker implementation with multiple opening policies and metrics.
    
    Features:
    - Multiple opening policies (failure count, rate, consecutive)
    - Sliding window for time-based analysis
    - Half-open state for recovery testing
    - Comprehensive metrics and monitoring
    - Exception filtering
    - State change notifications
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.state_change_callbacks: List[Callable[[CircuitBreakerState, CircuitBreakerState], None]] = []
        self.lock = Lock()
        
        # State-specific tracking
        self.half_open_calls = 0
        self.last_state_change = datetime.utcnow()
    
    def can_execute(self) -> bool:
        """
        Check if operation can be executed through circuit breaker.
        
        Returns:
            True if operation can proceed, False otherwise
        """
        with self.lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            elif self.state == CircuitBreakerState.OPEN:
                # Check if timeout has passed
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                    return True
                return False
            elif self.state == CircuitBreakerState.HALF_OPEN:
                return self.half_open_calls < self.config.half_open_max_calls
            
            return False
    
    def record_success(self) -> None:
        """Record a successful operation."""
        with self.lock:
            now = datetime.utcnow()
            
            # Update metrics
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = now
            self.metrics.consecutive_failures = 0
            
            # Add to history
            self._add_to_history(now, success=True)
            
            # Handle state transitions
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_calls += 1
                # If we've had enough successes in half-open, close the circuit
                if self.half_open_calls >= self.config.half_open_max_calls:
                    self._transition_to_closed()
            elif self.state == CircuitBreakerState.CLOSED:
                # Reset consecutive failures on success
                self.metrics.consecutive_failures = 0
    
    def record_failure(self, exception: Exception) -> None:
        """Record a failed operation."""
        with self.lock:
            # Check if exception should be tracked
            if not self._should_track_exception(exception):
                return
            
            now = datetime.utcnow()
            
            # Update metrics
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = now
            self.metrics.consecutive_failures += 1
            
            # Add to history
            self._add_to_history(now, success=False, exception=exception)
            
            # Handle state transitions
            if self.state == CircuitBreakerState.CLOSED:
                if self._should_open_circuit():
                    self._transition_to_open()
            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open opens the circuit
                self._transition_to_open()
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        with self.lock:
            return self.state
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics."""
        with self.lock:
            return self.metrics
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self.lock:
            self._transition_to_closed()
    
    def force_open(self) -> None:
        """Force circuit breaker to open state."""
        with self.lock:
            self._transition_to_open()
    
    def add_state_change_callback(self, callback: Callable[[CircuitBreakerState, CircuitBreakerState], None]) -> None:
        """Add callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def remove_state_change_callback(self, callback: Callable[[CircuitBreakerState, CircuitBreakerState], None]) -> None:
        """Remove state change callback."""
        if callback in self.state_change_callbacks:
            self.state_change_callbacks.remove(callback)
    
    def _should_track_exception(self, exception: Exception) -> bool:
        """Check if exception should be tracked by circuit breaker."""
        # Check ignored exceptions first
        for ignored_type in self.config.ignored_exceptions:
            if isinstance(exception, ignored_type):
                return False
        
        # Check tracked exceptions
        for tracked_type in self.config.tracked_exceptions:
            if isinstance(exception, tracked_type):
                return True
        
        return False
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on policy."""
        if self.config.policy == CircuitBreakerPolicy.FAILURE_COUNT:
            return self.metrics.failed_requests >= self.config.failure_threshold
        
        elif self.config.policy == CircuitBreakerPolicy.FAILURE_RATE:
            if self.metrics.total_requests < self.config.min_samples:
                return False
            return self.metrics.get_failure_rate() >= self.config.failure_rate_threshold
        
        elif self.config.policy == CircuitBreakerPolicy.CONSECUTIVE_FAILURES:
            return self.metrics.consecutive_failures >= self.config.consecutive_failure_threshold
        
        elif self.config.policy == CircuitBreakerPolicy.HYBRID:
            # Hybrid: open if any condition is met
            conditions_met = 0
            
            if self.metrics.failed_requests >= self.config.failure_threshold:
                conditions_met += 1
            
            if (self.metrics.total_requests >= self.config.min_samples and 
                self.metrics.get_failure_rate() >= self.config.failure_rate_threshold):
                conditions_met += 1
            
            if self.metrics.consecutive_failures >= self.config.consecutive_failure_threshold:
                conditions_met += 1
            
            return conditions_met >= 2  # Require at least 2 conditions
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset from open to half-open."""
        if not self.config.auto_reset:
            return False
        
        if self.metrics.last_failure_time is None:
            return True
        
        time_since_failure = datetime.utcnow() - self.metrics.last_failure_time
        return time_since_failure.total_seconds() >= self.config.timeout
    
    def _transition_to_closed(self) -> None:
        """Transition to closed state."""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.half_open_calls = 0
        self.last_state_change = datetime.utcnow()
        
        self._record_state_change(old_state, self.state)
    
    def _transition_to_open(self) -> None:
        """Transition to open state."""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.half_open_calls = 0
        self.last_state_change = datetime.utcnow()
        
        self._record_state_change(old_state, self.state)
    
    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_calls = 0
        self.last_state_change = datetime.utcnow()
        
        self._record_state_change(old_state, self.state)
    
    def _record_state_change(self, old_state: CircuitBreakerState, new_state: CircuitBreakerState) -> None:
        """Record state change and notify callbacks."""
        change_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "old_state": old_state.value,
            "new_state": new_state.value,
            "reason": self._get_state_change_reason(old_state, new_state)
        }
        
        self.metrics.state_changes.append(change_record)
        
        # Notify callbacks
        if self.config.notify_on_state_change:
            for callback in self.state_change_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception:
                    # Don't let callback errors affect circuit breaker
                    pass
    
    def _get_state_change_reason(self, old_state: CircuitBreakerState, new_state: CircuitBreakerState) -> str:
        """Get human-readable reason for state change."""
        if old_state == CircuitBreakerState.CLOSED and new_state == CircuitBreakerState.OPEN:
            return f"Failure threshold reached: {self.metrics.failed_requests} failures"
        elif old_state == CircuitBreakerState.OPEN and new_state == CircuitBreakerState.HALF_OPEN:
            return "Timeout elapsed, attempting recovery"
        elif old_state == CircuitBreakerState.HALF_OPEN and new_state == CircuitBreakerState.CLOSED:
            return "Recovery successful, circuit closed"
        elif old_state == CircuitBreakerState.HALF_OPEN and new_state == CircuitBreakerState.OPEN:
            return "Recovery failed, circuit opened again"
        else:
            return "Manual state change"
    
    def _add_to_history(self, timestamp: datetime, success: bool, exception: Optional[Exception] = None) -> None:
        """Add request to history with sliding window."""
        if not self.config.metrics_enabled:
            return
        
        history_entry = {
            "timestamp": timestamp.isoformat(),
            "success": success,
            "exception_type": type(exception).__name__ if exception else None,
            "exception_message": str(exception) if exception else None
        }
        
        self.metrics.request_history.append(history_entry)
        
        # Maintain sliding window
        cutoff_time = timestamp - timedelta(seconds=self.config.sliding_window_size)
        self.metrics.request_history = [
            entry for entry in self.metrics.request_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers with centralized configuration and monitoring.
    
    Features:
    - Centralized circuit breaker management
    - Automatic configuration based on error classification
    - Global metrics and monitoring
    - Bulk operations
    - Configuration templates
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.config_templates: Dict[str, CircuitBreakerConfig] = {}
        self.lock = Lock()
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        """Initialize default configuration templates."""
        # Network services template
        self.config_templates["network_service"] = CircuitBreakerConfig(
            name="network_service",
            failure_threshold=5,
            timeout=30.0,
            policy=CircuitBreakerPolicy.CONSECUTIVE_FAILURES,
            consecutive_failure_threshold=3,
            half_open_max_calls=3
        )
        
        # Database template
        self.config_templates["database"] = CircuitBreakerConfig(
            name="database",
            failure_threshold=3,
            timeout=60.0,
            policy=CircuitBreakerPolicy.CONSECUTIVE_FAILURES,
            consecutive_failure_threshold=2,
            half_open_max_calls=2
        )
        
        # AI/ML services template
        self.config_templates["ai_service"] = CircuitBreakerConfig(
            name="ai_service",
            failure_threshold=10,
            timeout=120.0,
            policy=CircuitBreakerPolicy.FAILURE_RATE,
            failure_rate_threshold=0.3,
            min_samples=5,
            half_open_max_calls=5
        )
        
        # Critical services template
        self.config_templates["critical_service"] = CircuitBreakerConfig(
            name="critical_service",
            failure_threshold=2,
            timeout=15.0,
            policy=CircuitBreakerPolicy.CONSECUTIVE_FAILURES,
            consecutive_failure_threshold=2,
            half_open_max_calls=1
        )
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create circuit breaker with given name.
        
        Args:
            name: Circuit breaker name
            config: Optional configuration
            
        Returns:
            CircuitBreaker instance
        """
        with self.lock:
            if name not in self.circuit_breakers:
                if config is None:
                    config = self.config_templates.get("network_service", CircuitBreakerConfig(name=name))
                self.circuit_breakers[name] = CircuitBreaker(config)
            
            return self.circuit_breakers[name]
    
    def create_from_template(self, name: str, template_name: str) -> CircuitBreaker:
        """Create circuit breaker from template."""
        if template_name not in self.config_templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        config = CircuitBreakerConfig(
            name=name,
            **{k: v for k, v in self.config_templates[template_name].__dict__.items() if k != 'name'}
        )
        
        return self.get_circuit_breaker(name, config)
    
    def create_from_error_classification(
        self,
        name: str,
        classification: ErrorClassification
    ) -> CircuitBreaker:
        """Create circuit breaker configuration based on error classification."""
        # Select template based on error category
        template_name = "network_service"  # default
        
        if classification.category == ErrorCategory.DATABASE:
            template_name = "database"
        elif classification.category in [ErrorCategory.AI_PROCESSING, ErrorCategory.MODEL_UNAVAILABLE]:
            template_name = "ai_service"
        elif classification.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
            template_name = "critical_service"
        
        # Adjust configuration based on classification
        circuit_breaker = self.create_from_template(name, template_name)
        config = circuit_breaker.config
        
        # Adjust thresholds based on error characteristics
        if classification.retry_possible:
            config.timeout = max(config.timeout, 30.0)  # Longer timeout for retryable errors
        
        if classification.user_action_required:
            config.failure_threshold = min(config.failure_threshold, 3)  # Lower threshold for user-action errors
        
        return circuit_breaker
    
    def can_execute(self, name: str) -> bool:
        """Check if circuit breaker allows execution."""
        if name not in self.circuit_breakers:
            return True  # No circuit breaker means always allowed
        
        return self.circuit_breakers[name].can_execute()
    
    def record_success(self, name: str) -> None:
        """Record success for circuit breaker."""
        if name in self.circuit_breakers:
            self.circuit_breakers[name].record_success()
    
    def record_failure(self, name: str, exception: Exception) -> None:
        """Record failure for circuit breaker."""
        if name in self.circuit_breakers:
            self.circuit_breakers[name].record_failure(exception)
    
    def get_all_metrics(self) -> Dict[str, CircuitBreakerMetrics]:
        """Get metrics for all circuit breakers."""
        return {name: cb.get_metrics() for name, cb in self.circuit_breakers.items()}
    
    def get_open_circuit_breakers(self) -> List[str]:
        """Get list of currently open circuit breakers."""
        return [
            name for name, cb in self.circuit_breakers.items()
            if cb.get_state() == CircuitBreakerState.OPEN
        ]
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            cb.reset()
    
    def reset(self, name: str) -> None:
        """Reset specific circuit breaker."""
        if name in self.circuit_breakers:
            self.circuit_breakers[name].reset()
    
    def remove(self, name: str) -> bool:
        """Remove circuit breaker."""
        with self.lock:
            if name in self.circuit_breakers:
                del self.circuit_breakers[name]
                return True
            return False
    
    def add_template(self, name: str, config: CircuitBreakerConfig) -> None:
        """Add configuration template."""
        self.config_templates[name] = config
    
    def get_template(self, name: str) -> Optional[CircuitBreakerConfig]:
        """Get configuration template."""
        return self.config_templates.get(name)


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 60.0,
    policy: CircuitBreakerPolicy = CircuitBreakerPolicy.FAILURE_COUNT,
    **kwargs
):
    """Decorator for automatic circuit breaker protection."""
    def decorator(func):
        async def wrapper(*args, **func_kwargs):
            # Get or create circuit breaker
            config = CircuitBreakerConfig(
                name=name,
                failure_threshold=failure_threshold,
                timeout=timeout,
                policy=policy,
                **kwargs
            )
            cb = circuit_breaker_manager.get_circuit_breaker(name, config)
            
            # Check if operation can proceed
            if not cb.can_execute():
                raise Exception(f"Circuit breaker '{name}' is open")
            
            try:
                # Execute operation
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **func_kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, func, *args, **func_kwargs)
                
                # Record success
                cb.record_success()
                return result
                
            except Exception as e:
                # Record failure
                cb.record_failure(e)
                raise
        
        return wrapper
    return decorator