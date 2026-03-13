"""
Circuit Breaker Implementation for AI-Karen Production Chat System
Provides automatic service protection and failure handling.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerPolicy(Enum):
    """Circuit breaker policies."""
    FAILURE_COUNT = "failure_count"
    FAILURE_RATE = "failure_rate"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    HYBRID = "hybrid"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    timeout: int = 60  # seconds
    half_open_max_calls: int = 3
    policy: CircuitBreakerPolicy = CircuitBreakerPolicy.CONSECUTIVE_FAILURES
    failure_rate_threshold: float = 0.5  # 50%
    consecutive_failure_threshold: int = 3
    min_samples: int = 10
    auto_reset: bool = True
    reset_timeout: int = 300  # seconds


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    failure_history: List[datetime] = field(default_factory=list)


class CircuitBreaker:
    """
    Circuit breaker implementation for service protection.
    
    Features:
    - Multiple failure detection policies
    - Automatic state transitions
    - Configurable timeouts and thresholds
    - Metrics collection
    - Health check integration
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        health_check: Optional[Callable] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.health_check = health_check
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.half_open_calls = 0
        self.last_state_change = datetime.now(timezone.utc)
        self.lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized with policy: {self.config.policy.value}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result if successful
            
        Raises:
            Exception: Original exception or circuit breaker exception
        """
        async with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    self.last_state_change = datetime.now(timezone.utc)
                    logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")
            
            if self.state == CircuitBreakerState.HALF_OPEN and self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' half-open limit exceeded")
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record success
            await self._record_success()
            
            return result
            
        except Exception as e:
            # Record failure
            await self._record_failure()
            
            # Re-raise the original exception
            raise e
    
    async def _record_success(self):
        """Record a successful call."""
        async with self.lock:
            self.metrics.total_calls += 1
            self.metrics.successful_calls += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = datetime.now(timezone.utc)
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_calls += 1
                
                # Check if we should close the circuit
                if self.half_open_calls >= self.config.half_open_max_calls:
                    self.state = CircuitBreakerState.CLOSED
                    self.last_state_change = datetime.now(timezone.utc)
                    logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
            
            logger.debug(f"Circuit breaker '{self.name}' recorded success. State: {self.state.value}")
    
    async def _record_failure(self):
        """Record a failed call."""
        async with self.lock:
            self.metrics.total_calls += 1
            self.metrics.failed_calls += 1
            self.metrics.consecutive_failures += 1
            self.metrics.last_failure_time = datetime.now(timezone.utc)
            self.metrics.failure_history.append(datetime.now(timezone.utc))
            
            # Keep only recent failures (last hour)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            self.metrics.failure_history = [
                failure_time for failure_time in self.metrics.failure_history
                if failure_time > cutoff_time
            ]
            
            # Check if we should open the circuit
            if self._should_open_circuit():
                self.state = CircuitBreakerState.OPEN
                self.last_state_change = datetime.now(timezone.utc)
                logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN")
            
            logger.debug(f"Circuit breaker '{self.name}' recorded failure. State: {self.state.value}")
    
    def _should_open_circuit(self) -> bool:
        """Determine if the circuit should be opened based on policy."""
        if self.state == CircuitBreakerState.OPEN:
            return False
        
        if self.config.policy == CircuitBreakerPolicy.FAILURE_COUNT:
            return self.metrics.failed_calls >= self.config.failure_threshold
        
        elif self.config.policy == CircuitBreakerPolicy.CONSECUTIVE_FAILURES:
            return self.metrics.consecutive_failures >= self.config.consecutive_failure_threshold
        
        elif self.config.policy == CircuitBreakerPolicy.FAILURE_RATE:
            if self.metrics.total_calls < self.config.min_samples:
                return False
            failure_rate = self.metrics.failed_calls / self.metrics.total_calls
            return failure_rate >= self.config.failure_rate_threshold
        
        elif self.config.policy == CircuitBreakerPolicy.HYBRID:
            # Check consecutive failures first
            if self.metrics.consecutive_failures >= self.config.consecutive_failure_threshold:
                return True
            
            # Then check failure rate if we have enough samples
            if self.metrics.total_calls >= self.config.min_samples:
                failure_rate = self.metrics.failed_calls / self.metrics.total_calls
                return failure_rate >= self.config.failure_rate_threshold
            
            # Finally check total failure count
            return self.metrics.failed_calls >= self.config.failure_threshold
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Determine if we should attempt to reset the circuit."""
        if not self.config.auto_reset:
            return False
        
        if self.metrics.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.now(timezone.utc) - self.metrics.last_failure_time).seconds
        return time_since_failure >= self.config.timeout
    
    async def force_open(self):
        """Force the circuit breaker to open state."""
        async with self.lock:
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = datetime.now(timezone.utc)
            logger.warning(f"Circuit breaker '{self.name}' forced to OPEN")
    
    async def force_close(self):
        """Force the circuit breaker to closed state."""
        async with self.lock:
            self.state = CircuitBreakerState.CLOSED
            self.half_open_calls = 0
            self.last_state_change = datetime.now(timezone.utc)
            logger.info(f"Circuit breaker '{self.name}' forced to CLOSED")
    
    async def reset(self):
        """Reset the circuit breaker metrics and state."""
        async with self.lock:
            self.state = CircuitBreakerState.CLOSED
            self.metrics = CircuitBreakerMetrics()
            self.half_open_calls = 0
            self.last_state_change = datetime.now(timezone.utc)
            logger.info(f"Circuit breaker '{self.name}' reset")
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.state
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.metrics.total_calls,
            "successful_calls": self.metrics.successful_calls,
            "failed_calls": self.metrics.failed_calls,
            "consecutive_failures": self.metrics.consecutive_failures,
            "failure_rate": (
                self.metrics.failed_calls / self.metrics.total_calls
                if self.metrics.total_calls > 0 else 0
            ),
            "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
            "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "half_open_calls": self.half_open_calls,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout": self.config.timeout,
                "half_open_max_calls": self.config.half_open_max_calls,
                "policy": self.config.policy.value,
                "failure_rate_threshold": self.config.failure_rate_threshold,
                "consecutive_failure_threshold": self.config.consecutive_failure_threshold,
                "min_samples": self.config.min_samples,
                "auto_reset": self.config.auto_reset
            }
        }


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.lock = asyncio.Lock()
    
    async def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        health_check: Optional[Callable] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        async with self.lock:
            if name not in self.circuit_breakers:
                self.circuit_breakers[name] = CircuitBreaker(name, config, health_check)
                logger.info(f"Created circuit breaker '{name}'")
            
            return self.circuit_breakers[name]
    
    async def remove_circuit_breaker(self, name: str):
        """Remove a circuit breaker."""
        async with self.lock:
            if name in self.circuit_breakers:
                del self.circuit_breakers[name]
                logger.info(f"Removed circuit breaker '{name}'")
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        return {
            name: cb.get_metrics()
            for name, cb in self.circuit_breakers.items()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers."""
        async with self.lock:
            for cb in self.circuit_breakers.values():
                await cb.reset()
            logger.info("Reset all circuit breakers")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all circuit breakers."""
        results = {}
        
        for name, cb in self.circuit_breakers.items():
            try:
                if cb.health_check:
                    is_healthy = await cb.health_check()
                    results[name] = is_healthy
                else:
                    # Default health check based on state
                    results[name] = cb.state != CircuitBreakerState.OPEN
            except Exception as e:
                logger.error(f"Health check failed for circuit breaker '{name}': {e}")
                results[name] = False
        
        return results


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager."""
    return circuit_breaker_manager


# Decorator for circuit breaker protection
def circuit_breaker_protected(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    health_check: Optional[Callable] = None
):
    """Decorator to protect a function with circuit breaker."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            cb = await circuit_breaker_manager.get_circuit_breaker(name, config, health_check)
            return await cb.call(func, *args, **kwargs)
        return wrapper
    return decorator