"""
Intelligent Retry Manager with Exponential Backoff

This module provides comprehensive retry logic with various strategies including
exponential backoff, jitter, circuit breaker integration, and adaptive retry
strategies based on error classification.
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic

from .error_classifier import ErrorClassification, ErrorCategory, ErrorSeverity

T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategies for different scenarios."""
    
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    ADAPTIVE = "adaptive"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"


class RetryState(Enum):
    """States in the retry lifecycle."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ABANDONED = "abandoned"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    # Basic retry settings
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    
    # Advanced retry settings
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    jitter_factor: float = 0.1
    
    # Timeout settings
    overall_timeout: Optional[float] = None
    per_attempt_timeout: Optional[float] = None
    
    # Retry condition settings
    retry_on_exceptions: List[type] = field(default_factory=lambda: [Exception])
    dont_retry_on_exceptions: List[type] = field(default_factory=list)
    
    # Success condition settings
    success_condition: Optional[Callable[[Any], bool]] = None
    
    # Circuit breaker integration
    use_circuit_breaker: bool = True
    circuit_breaker_name: Optional[str] = None
    
    # Adaptive retry settings
    enable_adaptive: bool = False
    success_threshold: float = 0.8
    failure_threshold: float = 0.5
    
    # Metadata
    name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class RetryAttempt:
    """Information about a single retry attempt."""
    
    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    delay_before: float = 0.0
    exception: Optional[Exception] = None
    result: Optional[Any] = None
    state: RetryState = RetryState.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryResult:
    """Result of a retry operation."""
    
    final_state: RetryState
    total_attempts: int
    total_duration: float
    successful_result: Optional[Any] = None
    final_exception: Optional[Exception] = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RetryStrategyBase(ABC):
    """Base class for retry strategies."""
    
    @abstractmethod
    def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        """Calculate delay for a specific attempt."""
        pass
    
    @abstractmethod
    def should_retry(self, attempt: int, max_retries: int, **kwargs) -> bool:
        """Determine if operation should be retried."""
        pass


class ExponentialBackoffStrategy(RetryStrategyBase):
    """Exponential backoff retry strategy with jitter."""
    
    def calculate_delay(self, attempt: int, base_delay: float, 
                       backoff_multiplier: float = 2.0, 
                       max_delay: float = 60.0,
                       jitter: bool = True,
                       jitter_factor: float = 0.1,
                       **kwargs) -> float:
        """Calculate exponential backoff delay."""
        delay = base_delay * (backoff_multiplier ** attempt)
        delay = min(delay, max_delay)
        
        if jitter:
            jitter_amount = delay * jitter_factor
            delay = delay - jitter_amount + (random.random() * 2 * jitter_amount)
        
        return max(0, delay)
    
    def should_retry(self, attempt: int, max_retries: int, **kwargs) -> bool:
        """Determine if should retry based on attempt count."""
        return attempt < max_retries


class LinearBackoffStrategy(RetryStrategyBase):
    """Linear backoff retry strategy."""
    
    def calculate_delay(self, attempt: int, base_delay: float,
                       max_delay: float = 60.0,
                       jitter: bool = True,
                       jitter_factor: float = 0.1,
                       **kwargs) -> float:
        """Calculate linear backoff delay."""
        delay = base_delay * (attempt + 1)
        delay = min(delay, max_delay)
        
        if jitter:
            jitter_amount = delay * jitter_factor
            delay = delay - jitter_amount + (random.random() * 2 * jitter_amount)
        
        return max(0, delay)
    
    def should_retry(self, attempt: int, max_retries: int, **kwargs) -> bool:
        """Determine if should retry based on attempt count."""
        return attempt < max_retries


class FibonacciBackoffStrategy(RetryStrategyBase):
    """Fibonacci backoff retry strategy."""
    
    def __init__(self):
        self.fib_cache = {0: 0, 1: 1}
    
    def _fibonacci(self, n: int) -> int:
        """Calculate Fibonacci number with caching."""
        if n in self.fib_cache:
            return self.fib_cache[n]
        
        result = self._fibonacci(n - 1) + self._fibonacci(n - 2)
        self.fib_cache[n] = result
        return result
    
    def calculate_delay(self, attempt: int, base_delay: float,
                       max_delay: float = 60.0,
                       jitter: bool = True,
                       jitter_factor: float = 0.1,
                       **kwargs) -> float:
        """Calculate Fibonacci backoff delay."""
        fib_value = self._fibonacci(attempt + 1)
        delay = base_delay * fib_value
        delay = min(delay, max_delay)
        
        if jitter:
            jitter_amount = delay * jitter_factor
            delay = delay - jitter_amount + (random.random() * 2 * jitter_amount)
        
        return max(0, delay)
    
    def should_retry(self, attempt: int, max_retries: int, **kwargs) -> bool:
        """Determine if should retry based on attempt count."""
        return attempt < max_retries


class AdaptiveRetryStrategy(RetryStrategyBase):
    """Adaptive retry strategy that adjusts based on success rates."""
    
    def __init__(self):
        self.success_history: List[bool] = []
        self.max_history = 100
    
    def calculate_delay(self, attempt: int, base_delay: float,
                       max_delay: float = 60.0,
                       backoff_multiplier: float = 2.0,
                       jitter: bool = True,
                       jitter_factor: float = 0.1,
                       **kwargs) -> float:
        """Calculate adaptive delay based on success history."""
        if not self.success_history:
            # Fallback to exponential backoff
            delay = base_delay * (backoff_multiplier ** attempt)
        else:
            # Calculate success rate
            recent_success_rate = sum(self.success_history[-10:]) / min(len(self.success_history), 10)
            
            if recent_success_rate > 0.8:
                # High success rate - use shorter delays
                delay = base_delay * (1.2 ** attempt)
            elif recent_success_rate > 0.5:
                # Medium success rate - standard exponential backoff
                delay = base_delay * (backoff_multiplier ** attempt)
            else:
                # Low success rate - longer delays
                delay = base_delay * (backoff_multiplier ** (attempt + 1))
        
        delay = min(delay, max_delay)
        
        if jitter:
            jitter_amount = delay * jitter_factor
            delay = delay - jitter_amount + (random.random() * 2 * jitter_amount)
        
        return max(0, delay)
    
    def should_retry(self, attempt: int, max_retries: int, **kwargs) -> bool:
        """Determine if should retry based on attempt count and success history."""
        if attempt >= max_retries:
            return False
        
        # If success rate is very low, reduce max retries
        if len(self.success_history) >= 5:
            recent_success_rate = sum(self.success_history[-5:]) / 5
            if recent_success_rate < 0.2 and attempt >= 2:
                return False
        
        return True
    
    def record_success(self, success: bool) -> None:
        """Record success/failure for adaptive learning."""
        self.success_history.append(success)
        if len(self.success_history) > self.max_history:
            self.success_history.pop(0)


class RetryManager:
    """
    Intelligent retry manager with multiple strategies and error classification.
    
    Features:
    - Multiple retry strategies (exponential, linear, fibonacci, adaptive)
    - Jitter to prevent thundering herd
    - Circuit breaker integration
    - Adaptive retry based on success rates
    - Per-operation timeout handling
    - Comprehensive retry metrics
    - Error classification-based retry decisions
    """
    
    def __init__(self):
        self.strategies = {
            RetryStrategy.EXPONENTIAL_BACKOFF: ExponentialBackoffStrategy(),
            RetryStrategy.LINEAR_BACKOFF: LinearBackoffStrategy(),
            RetryStrategy.FIBONACCI_BACKOFF: FibonacciBackoffStrategy(),
            RetryStrategy.ADAPTIVE: AdaptiveRetryStrategy(),
        }
        self.retry_history: Dict[str, List[RetryResult]] = {}
        self.circuit_breaker_manager = None  # Will be injected
    
    def set_circuit_breaker_manager(self, circuit_breaker_manager) -> None:
        """Set circuit breaker manager for integration."""
        self.circuit_breaker_manager = circuit_breaker_manager
    
    async def execute_with_retry(
        self,
        operation: Callable[..., T],
        config: RetryConfig,
        *args,
        **kwargs
    ) -> T:
        """
        Execute operation with retry logic.
        
        Args:
            operation: The operation to execute
            config: Retry configuration
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Result of the operation
            
        Raises:
            Last exception if all retries fail
        """
        start_time = time.time()
        attempts = []
        final_state = RetryState.FAILED
        final_exception = None
        successful_result = None
        
        # Check circuit breaker if enabled
        if config.use_circuit_breaker and self.circuit_breaker_manager:
            circuit_breaker_name = config.circuit_breaker_name or config.name or "default"
            if not self.circuit_breaker_manager.can_execute(circuit_breaker_name):
                final_state = RetryState.CIRCUIT_BREAKER_OPEN
                final_exception = Exception("Circuit breaker is open")
                return self._create_retry_result(
                    final_state, attempts, start_time, final_exception, successful_result
                )
        
        strategy = self.strategies.get(config.strategy, self.strategies[RetryStrategy.EXPONENTIAL_BACKOFF])
        
        for attempt in range(config.max_retries + 1):  # +1 for initial attempt
            attempt_start = datetime.utcnow()
            
            # Calculate delay before this attempt (except first attempt)
            delay_before = 0.0
            if attempt > 0:
                delay_before = strategy.calculate_delay(
                    attempt=attempt - 1,
                    base_delay=config.base_delay,
                    max_delay=config.max_delay,
                    backoff_multiplier=config.backoff_multiplier,
                    jitter=config.jitter,
                )
                await asyncio.sleep(delay_before)
            
            retry_attempt = RetryAttempt(
                attempt_number=attempt,
                start_time=attempt_start,
                delay_before=delay_before
            )
            
            try:
                # Execute with timeout if configured
                if config.per_attempt_timeout:
                    result = await asyncio.wait_for(
                        self._execute_operation(operation, *args, **kwargs),
                        timeout=config.per_attempt_timeout
                    )
                else:
                    result = await self._execute_operation(operation, *args, **kwargs)
                
                # Check success condition if provided
                if config.success_condition and not config.success_condition(result):
                    raise ValueError("Success condition not met")
                
                # Success!
                retry_attempt.end_time = datetime.utcnow()
                retry_attempt.result = result
                retry_attempt.state = RetryState.SUCCESS
                attempts.append(retry_attempt)
                
                # Record success for adaptive strategy
                if isinstance(strategy, AdaptiveRetryStrategy):
                    strategy.record_success(True)
                
                # Record circuit breaker success if enabled
                if config.use_circuit_breaker and self.circuit_breaker_manager:
                    circuit_breaker_name = config.circuit_breaker_name or config.name or "default"
                    self.circuit_breaker_manager.record_success(circuit_breaker_name)
                
                final_state = RetryState.SUCCESS
                successful_result = result
                break
                
            except Exception as e:
                retry_attempt.end_time = datetime.utcnow()
                retry_attempt.exception = e
                retry_attempt.state = RetryState.FAILED
                attempts.append(retry_attempt)
                
                # Record failure for adaptive strategy
                if isinstance(strategy, AdaptiveRetryStrategy):
                    strategy.record_success(False)
                
                # Check if we should retry this exception
                if not self._should_retry_exception(e, config):
                    final_exception = e
                    break
                
                # Check if we should continue retrying
                if not strategy.should_retry(attempt, config.max_retries):
                    final_exception = e
                    break
                
                # Check overall timeout
                if config.overall_timeout and (time.time() - start_time) > config.overall_timeout:
                    final_state = RetryState.ABANDONED
                    final_exception = TimeoutError("Overall timeout exceeded")
                    break
                
                # Record circuit breaker failure if enabled
                if config.use_circuit_breaker and self.circuit_breaker_manager:
                    circuit_breaker_name = config.circuit_breaker_name or config.name or "default"
                    self.circuit_breaker_manager.record_failure(circuit_breaker_name)
                
                final_exception = e
        
        # If we never succeeded, final_exception should be the last one
        if final_exception is None and attempts:
            final_exception = attempts[-1].exception
        
        return self._create_retry_result(
            final_state, attempts, start_time, final_exception, successful_result
        )
    
    async def _execute_operation(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """Execute operation, handling both sync and async operations."""
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            # Run sync operation in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, operation, *args, **kwargs)
    
    def _should_retry_exception(self, exception: Exception, config: RetryConfig) -> bool:
        """Determine if exception should be retried."""
        # Check explicit non-retry exceptions
        for exc_type in config.dont_retry_on_exceptions:
            if isinstance(exception, exc_type):
                return False
        
        # Check explicit retry exceptions
        for exc_type in config.retry_on_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        # Default behavior - retry most exceptions except critical ones
        critical_exceptions = (
            KeyboardInterrupt,
            SystemExit,
            MemoryError,
            OverflowError,
            RecursionError,
        )
        
        return not isinstance(exception, critical_exceptions)
    
    def _create_retry_result(
        self,
        final_state: RetryState,
        attempts: List[RetryAttempt],
        start_time: float,
        final_exception: Optional[Exception],
        successful_result: Optional[Any]
    ) -> T:
        """Create retry result and handle final state."""
        total_duration = time.time() - start_time
        
        result = RetryResult(
            final_state=final_state,
            total_attempts=len(attempts),
            total_duration=total_duration,
            successful_result=successful_result,
            final_exception=final_exception,
            attempts=attempts
        )
        
        # Store retry history
        if attempts and hasattr(attempts[0], 'metadata'):
            operation_name = attempts[0].metadata.get('operation_name', 'unknown')
            if operation_name not in self.retry_history:
                self.retry_history[operation_name] = []
            self.retry_history[operation_name].append(result)
        
        # Raise exception if failed
        if final_state in [RetryState.FAILED, RetryState.ABANDONED, RetryState.CIRCUIT_BREAKER_OPEN]:
            if final_exception:
                raise final_exception
            else:
                raise Exception("Operation failed after retries")
        
        if successful_result is not None:
            return successful_result
        else:
            raise final_exception or Exception("Operation failed with no result")
    
    def create_config_for_error_classification(
        self,
        classification: ErrorClassification,
        base_config: Optional[RetryConfig] = None
    ) -> RetryConfig:
        """Create retry configuration based on error classification."""
        config = base_config or RetryConfig()
        
        # Adjust retry strategy based on error category
        if classification.category in [ErrorCategory.NETWORK, ErrorCategory.CONNECTIVITY]:
            config.strategy = RetryStrategy.EXPONENTIAL_BACKOFF
            config.max_retries = 5
            config.base_delay = 2.0
            config.jitter = True
        elif classification.category == ErrorCategory.TIMEOUT:
            config.strategy = RetryStrategy.EXPONENTIAL_BACKOFF
            config.max_retries = 3
            config.base_delay = 1.0
            config.jitter = True
        elif classification.category == ErrorCategory.RESOURCE_EXHAUSTION:
            config.strategy = RetryStrategy.LINEAR_BACKOFF
            config.max_retries = 2
            config.base_delay = 5.0
            config.jitter = False
        elif classification.category in [ErrorCategory.VALIDATION, ErrorCategory.AUTHORIZATION]:
            config.strategy = RetryStrategy.NO_RETRY
            config.max_retries = 0
        elif classification.category == ErrorCategory.AI_PROCESSING:
            config.strategy = RetryStrategy.ADAPTIVE
            config.max_retries = 3
            config.base_delay = 1.0
            config.enable_adaptive = True
        else:
            config.strategy = RetryStrategy.EXPONENTIAL_BACKOFF
            config.max_retries = 3
            config.base_delay = 1.0
        
        # Adjust based on severity
        if classification.severity == ErrorSeverity.CRITICAL:
            config.max_retries = min(config.max_retries, 2)
            config.base_delay = min(config.base_delay, 1.0)
        elif classification.severity == ErrorSeverity.LOW:
            config.max_retries = max(config.max_retries, 5)
        
        # Set retry possibility from classification
        if not classification.retry_possible:
            config.strategy = RetryStrategy.NO_RETRY
            config.max_retries = 0
        
        return config
    
    def get_retry_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get retry statistics for analysis."""
        stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "abandoned_operations": 0,
            "average_attempts": 0.0,
            "average_duration": 0.0,
            "success_rate": 0.0,
        }
        
        results_to_analyze = []
        if operation_name and operation_name in self.retry_history:
            results_to_analyze = self.retry_history[operation_name]
        else:
            for results in self.retry_history.values():
                results_to_analyze.extend(results)
        
        if not results_to_analyze:
            return stats
        
        stats["total_operations"] = len(results_to_analyze)
        
        successful_count = sum(1 for r in results_to_analyze if r.final_state == RetryState.SUCCESS)
        failed_count = sum(1 for r in results_to_analyze if r.final_state == RetryState.FAILED)
        abandoned_count = sum(1 for r in results_to_analyze if r.final_state == RetryState.ABANDONED)
        
        stats["successful_operations"] = successful_count
        stats["failed_operations"] = failed_count
        stats["abandoned_operations"] = abandoned_count
        
        if results_to_analyze:
            stats["average_attempts"] = sum(r.total_attempts for r in results_to_analyze) / len(results_to_analyze)
            stats["average_duration"] = sum(r.total_duration for r in results_to_analyze) / len(results_to_analyze)
            stats["success_rate"] = successful_count / len(results_to_analyze)
        
        return stats
    
    def clear_history(self, operation_name: Optional[str] = None) -> None:
        """Clear retry history."""
        if operation_name and operation_name in self.retry_history:
            del self.retry_history[operation_name]
        else:
            self.retry_history.clear()


# Global retry manager instance
retry_manager = RetryManager()


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    jitter: bool = True,
    **kwargs
):
    """Decorator for automatic retry with configuration."""
    def decorator(func):
        async def wrapper(*args, **func_kwargs):
            config = RetryConfig(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                strategy=strategy,
                jitter=jitter,
                name=func.__name__,
                **kwargs
            )
            return await retry_manager.execute_with_retry(func, config, *args, **func_kwargs)
        return wrapper
    return decorator