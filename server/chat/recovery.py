"""
Recovery Mechanisms for AI-Karen Production Chat System
Provides automatic and manual recovery strategies for error resolution.
"""

import logging
import asyncio
import time
import random
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Recovery strategy types."""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_TO_ALTERNATIVE = "fallback_to_alternative"
    FALLBACK_MODEL = "fallback_model"
    USER_ACTION_REQUIRED = "user_action_required"
    INCREASE_TIMEOUT = "increase_timeout"
    DEGRADE_SERVICE = "degrade_service"
    RESET_CONNECTION = "reset_connection"
    CLEAR_CACHE = "clear_cache"
    RESTART_SERVICE = "restart_service"
    SWITCH_ENDPOINT = "switch_endpoint"
    USE_CACHED_RESPONSE = "use_cached_response"


class RecoveryStatus(Enum):
    """Recovery status types."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    ABANDONED = "abandoned"


@dataclass
class RecoveryAction:
    """Recovery action configuration."""
    id: str
    strategy: RecoveryStrategy
    description: str
    priority: int
    max_attempts: int
    timeout: int
    requires_user_input: bool
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RecoveryAttempt:
    """Recovery attempt information."""
    action: RecoveryAction
    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RecoveryStatus = RecoveryStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RecoveryResult(BaseModel):
    """Recovery result information."""
    final_status: RecoveryStatus
    successful_action: Optional[RecoveryAction] = None
    failed_actions: List[RecoveryAttempt] = field(default_factory=list)
    successful_actions: List[RecoveryAttempt] = field(default_factory=list)
    total_duration: float = 0.0
    final_result: Optional[Any] = None
    final_error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RecoveryConfig:
    """Recovery system configuration."""
    
    def __init__(
        self,
        max_concurrent_recoveries: int = 5,
        default_retry_attempts: int = 3,
        default_backoff_base: float = 1.0,
        default_backoff_max: float = 30.0,
        default_timeout: int = 30000,
        enable_jitter: bool = True,
        jitter_factor: float = 0.1
    ):
        self.max_concurrent_recoveries = max_concurrent_recoveries
        self.default_retry_attempts = default_retry_attempts
        self.default_backoff_base = default_backoff_base
        self.default_backoff_max = default_backoff_max
        self.default_timeout = default_timeout
        self.enable_jitter = enable_jitter
        self.jitter_factor = jitter_factor


class BackoffStrategy:
    """Backoff strategy implementations."""
    
    @staticmethod
    def exponential_backoff(attempt: int, base: float, max_delay: float, jitter: bool = True) -> float:
        """Calculate exponential backoff delay."""
        delay = min(base * (2 ** attempt), max_delay)
        
        if jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
    
    @staticmethod
    def linear_backoff(attempt: int, base: float, max_delay: float, jitter: bool = True) -> float:
        """Calculate linear backoff delay."""
        delay = min(base * (attempt + 1), max_delay)
        
        if jitter:
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
    
    @staticmethod
    def fibonacci_backoff(attempt: int, base: float, max_delay: float, jitter: bool = True) -> float:
        """Calculate Fibonacci backoff delay."""
        fib_sequence = [0, 1]
        for i in range(2, attempt + 2):
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        
        delay = min(base * fib_sequence[min(attempt + 1, len(fib_sequence) - 1)], max_delay)
        
        if jitter:
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
    
    @staticmethod
    def fixed_delay(attempt: int, delay: float, jitter: bool = True) -> float:
        """Calculate fixed delay."""
        if jitter:
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


class RecoveryEngine:
    """
    Recovery engine for automatic and manual error recovery.
    
    Features:
    - Multiple recovery strategies
    - Configurable backoff strategies
    - Concurrent recovery management
    - Recovery attempt tracking
    - Success/failure analysis
    """
    
    def __init__(self, config: Optional[RecoveryConfig] = None):
        self.config = config or RecoveryConfig()
        self.active_recoveries: Dict[str, RecoveryAttempt] = {}
        self.recovery_history: List[RecoveryResult] = []
        self.recovery_strategies: Dict[RecoveryStrategy, Callable] = {}
        self.lock = asyncio.Lock()
        
        # Initialize default recovery strategies
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize default recovery strategies."""
        self.recovery_strategies[RecoveryStrategy.RETRY_WITH_BACKOFF] = self._retry_with_backoff
        self.recovery_strategies[RecoveryStrategy.FALLBACK_TO_ALTERNATIVE] = self._fallback_to_alternative
        self.recovery_strategies[RecoveryStrategy.FALLBACK_MODEL] = self._fallback_model
        self.recovery_strategies[RecoveryStrategy.USER_ACTION_REQUIRED] = self._user_action_required
        self.recovery_strategies[RecoveryStrategy.INCREASE_TIMEOUT] = self._increase_timeout
        self.recovery_strategies[RecoveryStrategy.DEGRADE_SERVICE] = self._degrade_service
        self.recovery_strategies[RecoveryStrategy.RESET_CONNECTION] = self._reset_connection
        self.recovery_strategies[RecoveryStrategy.CLEAR_CACHE] = self._clear_cache
        self.recovery_strategies[RecoveryStrategy.RESTART_SERVICE] = self._restart_service
        self.recovery_strategies[RecoveryStrategy.SWITCH_ENDPOINT] = self._switch_endpoint
        self.recovery_strategies[RecoveryStrategy.USE_CACHED_RESPONSE] = self._use_cached_response
    
    def register_recovery_strategy(self, strategy: RecoveryStrategy, handler: Callable):
        """Register a custom recovery strategy."""
        self.recovery_strategies[strategy] = handler
        logger.info(f"Registered recovery strategy: {strategy.value}")
    
    async def execute_recovery(
        self,
        actions: List[RecoveryAction],
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> RecoveryResult:
        """
        Execute recovery actions in priority order.
        
        Args:
            actions: List of recovery actions to execute
            context: Recovery context information
            error_info: Original error information
            
        Returns:
            Recovery result with status and details
        """
        recovery_id = f"recovery_{int(time.time())}_{random.randint(1000, 9999)}"
        
        logger.info(f"Starting recovery {recovery_id} with {len(actions)} actions")
        
        start_time = time.time()
        successful_actions = []
        failed_actions = []
        final_status = RecoveryStatus.FAILED
        successful_action = None
        
        # Sort actions by priority (higher priority first)
        sorted_actions = sorted(actions, key=lambda x: x.priority, reverse=True)
        
        for action in sorted_actions:
            # Check if we've exceeded concurrent recovery limit
            if len(self.active_recoveries) >= self.config.max_concurrent_recoveries:
                logger.warning(f"Concurrent recovery limit reached for {recovery_id}")
                break
            
            # Create recovery attempt
            attempt = RecoveryAttempt(
                action=action,
                attempt_number=len(successful_actions) + len(failed_actions) + 1,
                start_time=datetime.now(timezone.utc),
                metadata=context or {}
            )
            
            self.active_recoveries[recovery_id] = attempt
            
            try:
                # Execute recovery strategy
                logger.info(f"Executing recovery strategy: {action.strategy.value} for {recovery_id}")
                
                strategy_handler = self.recovery_strategies.get(action.strategy)
                if not strategy_handler:
                    raise ValueError(f"Unknown recovery strategy: {action.strategy.value}")
                
                attempt.status = RecoveryStatus.IN_PROGRESS
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    strategy_handler(action, context, error_info),
                    timeout=action.timeout / 1000  # Convert ms to seconds
                )
                
                # Success
                attempt.end_time = datetime.now(timezone.utc)
                attempt.status = RecoveryStatus.SUCCESS
                attempt.result = result
                
                successful_actions.append(attempt)
                successful_action = action
                final_status = RecoveryStatus.SUCCESS
                
                logger.info(f"Recovery strategy {action.strategy.value} succeeded for {recovery_id}")
                break
                
            except asyncio.TimeoutError:
                attempt.end_time = datetime.now(timezone.utc)
                attempt.status = RecoveryStatus.FAILED
                attempt.error = f"Recovery timed out after {action.timeout}ms"
                failed_actions.append(attempt)
                
                logger.warning(f"Recovery strategy {action.strategy.value} timed out for {recovery_id}")
                
            except Exception as e:
                attempt.end_time = datetime.now(timezone.utc)
                attempt.status = RecoveryStatus.FAILED
                attempt.error = str(e)
                failed_actions.append(attempt)
                
                logger.error(f"Recovery strategy {action.strategy.value} failed for {recovery_id}: {e}")
            
            finally:
                # Remove from active recoveries
                if recovery_id in self.active_recoveries:
                    del self.active_recoveries[recovery_id]
        
        # Create recovery result
        total_duration = time.time() - start_time
        
        result = RecoveryResult(
            final_status=final_status,
            successful_action=successful_action,
            failed_actions=failed_actions,
            successful_actions=successful_actions,
            total_duration=total_duration,
            final_result=successful_actions[-1].result if successful_actions else None,
            final_error=failed_actions[-1].error if failed_actions else None,
            metadata={
                "recovery_id": recovery_id,
                "context": context,
                "error_info": str(error_info) if error_info else None,
                "actions_executed": len(successful_actions) + len(failed_actions)
            }
        )
        
        # Add to history
        self.recovery_history.append(result)
        
        # Keep only recent history (last 1000 recoveries)
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-1000:]
        
        logger.info(f"Recovery {recovery_id} completed with status: {final_status.value}")
        
        return result
    
    # Default recovery strategy implementations
    async def _retry_with_backoff(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Retry operation with exponential backoff."""
        original_operation = context.get("operation") if context else None
        if not original_operation:
            raise ValueError("No operation provided for retry strategy")
        
        last_error = None
        
        for attempt in range(action.max_attempts):
            try:
                # Execute original operation
                if asyncio.iscoroutinefunction(original_operation):
                    result = await original_operation()
                else:
                    result = original_operation()
                
                logger.info(f"Retry succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                
                # Don't wait after last attempt
                if attempt < action.max_attempts - 1:
                    # Calculate backoff delay
                    delay = BackoffStrategy.exponential_backoff(
                        attempt,
                        self.config.default_backoff_base,
                        self.config.default_backoff_max,
                        self.config.enable_jitter
                    )
                    
                    logger.info(f"Waiting {delay:.2f}s before retry attempt {attempt + 2}")
                    await asyncio.sleep(delay)
        
        raise last_error or Exception("All retry attempts failed")
    
    async def _fallback_to_alternative(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Fallback to alternative service or endpoint."""
        alternative_service = context.get("alternative_service") if context else None
        if not alternative_service:
            raise ValueError("No alternative service provided")
        
        logger.info(f"Falling back to alternative service: {alternative_service}")
        
        # Simulate fallback logic
        await asyncio.sleep(1.0)  # Simulate service switch
        
        # In real implementation, this would call the alternative service
        return {"service": alternative_service, "status": "fallback_success"}
    
    async def _fallback_model(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Fallback to alternative AI model."""
        fallback_model = context.get("fallback_model", "gpt-3.5-turbo") if context else "gpt-3.5-turbo"
        
        logger.info(f"Falling back to model: {fallback_model}")
        
        # Simulate model fallback
        await asyncio.sleep(2.0)  # Simulate model loading
        
        return {"model": fallback_model, "status": "model_fallback_success"}
    
    async def _user_action_required(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Wait for user action to resolve error."""
        logger.info("User action required for recovery")
        
        # In a real implementation, this would wait for user input
        # For now, we'll simulate user action completion
        await asyncio.sleep(1.0)
        
        return {"user_action": "completed", "status": "user_recovery_success"}
    
    async def _increase_timeout(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Increase timeout and retry operation."""
        original_operation = context.get("operation") if context else None
        new_timeout = context.get("new_timeout", 60000) if context else 60000  # 60 seconds default
        
        if not original_operation:
            raise ValueError("No operation provided for timeout increase")
        
        logger.info(f"Increasing timeout to {new_timeout}ms and retrying")
        
        # Execute with increased timeout
        try:
            if asyncio.iscoroutinefunction(original_operation):
                result = await asyncio.wait_for(original_operation(), timeout=new_timeout / 1000)
            else:
                # For sync functions, we can't easily change timeout
                result = original_operation()
            
            return result
            
        except Exception as e:
            raise Exception(f"Operation failed even with increased timeout: {e}")
    
    async def _degrade_service(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Degrade service functionality to maintain availability."""
        degradation_level = context.get("degradation_level", "basic") if context else "basic"
        
        logger.info(f"Degrading service to level: {degradation_level}")
        
        # Simulate service degradation
        await asyncio.sleep(0.5)
        
        return {"degradation_level": degradation_level, "status": "degraded_success"}
    
    async def _reset_connection(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Reset connection and retry."""
        logger.info("Resetting connection")
        
        # Simulate connection reset
        await asyncio.sleep(0.5)
        
        return {"connection": "reset", "status": "reset_success"}
    
    async def _clear_cache(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Clear cache and retry."""
        cache_key = context.get("cache_key") if context else None
        
        logger.info(f"Clearing cache: {cache_key or 'all'}")
        
        # Simulate cache clearing
        await asyncio.sleep(0.2)
        
        return {"cache": "cleared", "status": "cache_clear_success"}
    
    async def _restart_service(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Restart service component."""
        service_name = context.get("service_name", "unknown") if context else "unknown"
        
        logger.info(f"Restarting service: {service_name}")
        
        # Simulate service restart
        await asyncio.sleep(3.0)
        
        return {"service": service_name, "status": "restart_success"}
    
    async def _switch_endpoint(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Switch to alternative endpoint."""
        new_endpoint = context.get("new_endpoint") if context else None
        if not new_endpoint:
            raise ValueError("No new endpoint provided")
        
        logger.info(f"Switching to endpoint: {new_endpoint}")
        
        # Simulate endpoint switch
        await asyncio.sleep(1.0)
        
        return {"endpoint": new_endpoint, "status": "endpoint_switch_success"}
    
    async def _use_cached_response(
        self,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
        error_info: Optional[Any] = None
    ) -> Any:
        """Use cached response if available."""
        cache_key = context.get("cache_key") if context else None
        if not cache_key:
            raise ValueError("No cache key provided")
        
        logger.info(f"Using cached response for key: {cache_key}")
        
        # Simulate cache lookup
        await asyncio.sleep(0.1)
        
        # In real implementation, this would return actual cached data
        return {"cache_key": cache_key, "data": "cached_response", "status": "cache_hit"}
    
    def get_recovery_metrics(self) -> Dict[str, Any]:
        """Get recovery system metrics."""
        if not self.recovery_history:
            return {
                "total_recoveries": 0,
                "success_rate": 0,
                "average_duration": 0,
                "most_common_strategy": None,
                "recent_failures": []
            }
        
        total_recoveries = len(self.recovery_history)
        successful_recoveries = len([r for r in self.recovery_history if r.final_status == RecoveryStatus.SUCCESS])
        success_rate = (successful_recoveries / total_recoveries) * 100
        
        total_duration = sum(r.total_duration for r in self.recovery_history)
        average_duration = total_duration / total_recoveries
        
        # Most common successful strategy
        successful_strategies = []
        for result in self.recovery_history:
            if result.successful_action:
                successful_strategies.append(result.successful_action.strategy)
        
        most_common_strategy = None
        if successful_strategies:
            from collections import Counter
            strategy_counts = Counter(successful_strategies)
            most_common_strategy = strategy_counts.most_common(1)[0][0].value
        
        # Recent failures (last 10)
        recent_failures = [
            {
                "timestamp": r.metadata.get("recovery_id") if r.metadata else "unknown",
                "error": r.final_error,
                "actions_attempted": len(r.failed_actions) + len(r.successful_actions)
            }
            for r in self.recovery_history[-10:]
            if r.final_status == RecoveryStatus.FAILED
        ]
        
        return {
            "total_recoveries": total_recoveries,
            "success_rate": success_rate,
            "average_duration": average_duration,
            "most_common_strategy": most_common_strategy,
            "recent_failures": recent_failures,
            "active_recoveries": len(self.active_recoveries)
        }
    
    async def clear_history(self):
        """Clear recovery history."""
        async with self.lock:
            self.recovery_history.clear()
            logger.info("Recovery history cleared")


# Global recovery engine
recovery_engine = RecoveryEngine()


def get_recovery_engine() -> RecoveryEngine:
    """Get global recovery engine."""
    return recovery_engine