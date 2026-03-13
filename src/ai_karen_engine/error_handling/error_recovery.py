"""
Error Recovery System with Intelligent Recovery Strategies

This module provides comprehensive error recovery mechanisms with automatic fallbacks,
recovery strategies, and intelligent decision-making based on error classification.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .error_classifier import ErrorClassification, ErrorCategory, ErrorSeverity

T = TypeVar('T')


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    
    # Retry-based strategies
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    RETRY_WITH_JITTER = "retry_with_jitter"
    RETRY_WITH_EXPONENTIAL_BACKOFF = "retry_with_exponential_backoff"
    
    # Fallback strategies
    FALLBACK_TO_CACHE = "fallback_to_cache"
    FALLBACK_TO_DEFAULT = "fallback_to_default"
    FALLBACK_TO_ALTERNATIVE = "fallback_to_alternative"
    FALLBACK_TO_SIMPLIFIED = "fallback_to_simplified"
    
    # Resource-based strategies
    FREE_RESOURCES = "free_resources"
    INCREASE_TIMEOUT = "increase_timeout"
    REDUCE_LOAD = "reduce_load"
    
    # Service-based strategies
    RESTART_SERVICE = "restart_service"
    SWITCH_ENDPOINT = "switch_endpoint"
    DEGRADE_SERVICE = "degrade_service"
    
    # User-based strategies
    USER_ACTION_REQUIRED = "user_action_required"
    PROMPT_USER_RETRY = "prompt_user_retry"
    NOTIFY_USER = "notify_user"
    
    # System-based strategies
    LOG_AND_CONTINUE = "log_and_continue"
    CIRCUIT_BREAKER = "circuit_breaker"
    ISOLATE_COMPONENT = "isolate_component"
    
    # AI/ML specific strategies
    FALLBACK_MODEL = "fallback_model"
    TRUNCATE_CONTEXT = "truncate_context"
    REDUCE_COMPLEXITY = "reduce_complexity"
    
    # No recovery
    NO_RECOVERY = "no_recovery"


class RecoveryStatus(Enum):
    """Status of recovery attempts."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    ABANDONED = "abandoned"


@dataclass
class RecoveryAction:
    """A specific recovery action to be taken."""
    
    strategy: RecoveryStrategy
    description: str
    priority: int = 0
    max_attempts: int = 3
    timeout: float = 30.0
    requires_user_input: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAttempt:
    """Information about a recovery attempt."""
    
    action: RecoveryAction
    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RecoveryStatus = RecoveryStatus.PENDING
    result: Optional[Any] = None
    exception: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Result of recovery process."""
    
    final_status: RecoveryStatus
    successful_action: Optional[RecoveryAction] = None
    failed_actions: List[RecoveryAttempt] = field(default_factory=list)
    successful_actions: List[RecoveryAttempt] = field(default_factory=list)
    total_duration: float = 0.0
    final_result: Optional[Any] = None
    final_exception: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RecoveryActionBase(ABC):
    """Base class for recovery actions."""
    
    def __init__(self, action: RecoveryAction):
        self.action = action
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the recovery action."""
        pass
    
    @abstractmethod
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if action can be executed."""
        pass
    
    @abstractmethod
    def get_estimated_duration(self) -> float:
        """Get estimated execution duration."""
        pass


class RetryWithBackoffAction(RecoveryActionBase):
    """Retry action with exponential backoff."""
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute retry with backoff."""
        operation = context.get("operation")
        if not operation:
            raise ValueError("No operation provided for retry")
        
        max_retries = self.action.metadata.get("max_retries", 3)
        base_delay = self.action.metadata.get("base_delay", 1.0)
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation()
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, operation)
            except Exception as e:
                if attempt == max_retries:
                    raise e
                
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if retry can be executed."""
        return "operation" in context and context.get("retry_possible", True)
    
    def get_estimated_duration(self) -> float:
        """Get estimated duration for retry."""
        max_retries = self.action.metadata.get("max_retries", 3)
        base_delay = self.action.metadata.get("base_delay", 1.0)
        # Rough estimate: sum of delays
        return sum(base_delay * (2 ** i) for i in range(max_retries))


class FallbackToCacheAction(RecoveryActionBase):
    """Fallback to cached response."""
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute fallback to cache."""
        cache_key = context.get("cache_key")
        cache_manager = context.get("cache_manager")
        
        if not cache_key or not cache_manager:
            raise ValueError("Cache key or cache manager not provided")
        
        cached_value = await cache_manager.get(cache_key)
        if cached_value is None:
            raise ValueError("No cached value found")
        
        return cached_value
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if cache fallback can be executed."""
        return (
            "cache_key" in context and
            "cache_manager" in context and
            context.get("cache_available", False)
        )
    
    def get_estimated_duration(self) -> float:
        """Get estimated duration for cache access."""
        return 0.1  # Cache access is typically fast


class FallbackToAlternativeAction(RecoveryActionBase):
    """Fallback to alternative service/method."""
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute fallback to alternative."""
        alternative_operation = context.get("alternative_operation")
        if not alternative_operation:
            raise ValueError("No alternative operation provided")
        
        if asyncio.iscoroutinefunction(alternative_operation):
            return await alternative_operation()
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, alternative_operation)
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if alternative fallback can be executed."""
        return "alternative_operation" in context
    
    def get_estimated_duration(self) -> float:
        """Get estimated duration for alternative operation."""
        return self.action.timeout


class FreeResourcesAction(RecoveryActionBase):
    """Free system resources."""
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute resource cleanup."""
        cleanup_actions = context.get("cleanup_actions", [])
        
        for cleanup_action in cleanup_actions:
            try:
                if asyncio.iscoroutinefunction(cleanup_action):
                    await cleanup_action()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, cleanup_action)
            except Exception as e:
                logging.warning(f"Cleanup action failed: {e}")
        
        return True
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if resource cleanup can be executed."""
        return "cleanup_actions" in context
    
    def get_estimated_duration(self) -> float:
        """Get estimated duration for resource cleanup."""
        return 5.0  # Typical cleanup time


class UserActionRequiredAction(RecoveryActionBase):
    """Require user action for recovery."""
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute user action requirement."""
        user_message = context.get("user_message", "User action required")
        action_prompt = context.get("action_prompt", "Please resolve the issue and retry")
        
        # In a real implementation, this would trigger user notification
        # For now, we'll just raise an exception with the user message
        raise Exception(f"{user_message}: {action_prompt}")
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if user action can be requested."""
        return True  # User action can always be requested
    
    def get_estimated_duration(self) -> float:
        """Get estimated duration for user action."""
        return float('inf')  # Depends on user


class ErrorRecoveryManager:
    """
    Intelligent error recovery manager with multiple strategies and decision-making.
    
    Features:
    - Multiple recovery strategies
    - Priority-based action selection
    - Automatic strategy selection based on error classification
    - Recovery attempt tracking and metrics
    - User action integration
    - Resource management
    - Service degradation support
    """
    
    def __init__(self):
        self.action_handlers = {
            RecoveryStrategy.RETRY_WITH_BACKOFF: RetryWithBackoffAction,
            RecoveryStrategy.FALLBACK_TO_CACHE: FallbackToCacheAction,
            RecoveryStrategy.FALLBACK_TO_ALTERNATIVE: FallbackToAlternativeAction,
            RecoveryStrategy.FREE_RESOURCES: FreeResourcesAction,
            RecoveryStrategy.USER_ACTION_REQUIRED: UserActionRequiredAction,
        }
        self.recovery_history: Dict[str, List[RecoveryResult]] = {}
        self.custom_strategies: Dict[str, RecoveryActionBase] = {}
    
    def register_strategy(self, strategy: RecoveryStrategy, handler_class: type) -> None:
        """Register a custom recovery strategy handler."""
        self.action_handlers[strategy] = handler_class
    
    def register_custom_strategy(self, name: str, handler: RecoveryActionBase) -> None:
        """Register a custom recovery strategy instance."""
        self.custom_strategies[name] = handler
    
    async def recover_from_error(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """
        Attempt to recover from an error using intelligent strategies.
        
        Args:
            error: The exception that occurred
            classification: Error classification result
            context: Additional context for recovery
            
        Returns:
            RecoveryResult with recovery attempt details
        """
        start_time = datetime.utcnow()
        context = context or {}
        context["error"] = error
        context["classification"] = classification
        
        # Generate recovery actions based on classification
        recovery_actions = self._generate_recovery_actions(classification, context)
        
        if not recovery_actions:
            return RecoveryResult(
                final_status=RecoveryStatus.FAILED,
                final_exception=error,
                total_duration=(datetime.utcnow() - start_time).total_seconds(),
                metadata={"reason": "No recovery actions available"}
            )
        
        # Sort actions by priority
        recovery_actions.sort(key=lambda x: x.priority, reverse=True)
        
        # Execute recovery actions
        successful_actions = []
        failed_actions = []
        final_result = None
        final_exception = error
        final_status = RecoveryStatus.FAILED
        
        for action in recovery_actions:
            attempt = await self._execute_recovery_action(action, context)
            
            if attempt.status == RecoveryStatus.SUCCESS:
                successful_actions.append(attempt)
                final_result = attempt.result
                final_exception = None
                final_status = RecoveryStatus.SUCCESS
                break
            else:
                failed_actions.append(attempt)
        
        total_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Store recovery history
        operation_name = context.get("operation_name", "unknown")
        if operation_name not in self.recovery_history:
            self.recovery_history[operation_name] = []
        
        recovery_result = RecoveryResult(
            final_status=final_status,
            successful_action=successful_actions[0].action if successful_actions else None,
            failed_actions=failed_actions,
            successful_actions=successful_actions,
            total_duration=total_duration,
            final_result=final_result,
            final_exception=final_exception,
            metadata={
                "error_type": type(error).__name__,
                "error_category": classification.category.value,
                "error_severity": classification.severity.value,
                "actions_attempted": len(failed_actions) + len(successful_actions),
            }
        )
        
        self.recovery_history[operation_name].append(recovery_result)
        
        return recovery_result
    
    def _generate_recovery_actions(
        self,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> List[RecoveryAction]:
        """Generate recovery actions based on error classification."""
        actions = []
        
        # Generate actions based on error category
        if classification.category == ErrorCategory.NETWORK:
            actions.extend(self._generate_network_recovery_actions(classification, context))
        elif classification.category == ErrorCategory.TIMEOUT:
            actions.extend(self._generate_timeout_recovery_actions(classification, context))
        elif classification.category == ErrorCategory.RESOURCE_EXHAUSTION:
            actions.extend(self._generate_resource_recovery_actions(classification, context))
        elif classification.category == ErrorCategory.DATABASE:
            actions.extend(self._generate_database_recovery_actions(classification, context))
        elif classification.category == ErrorCategory.AI_PROCESSING:
            actions.extend(self._generate_ai_recovery_actions(classification, context))
        elif classification.category == ErrorCategory.VALIDATION:
            actions.extend(self._generate_validation_recovery_actions(classification, context))
        
        # Add actions based on recovery strategies from classification
        for strategy_name in classification.recovery_strategies:
            try:
                strategy = RecoveryStrategy(strategy_name)
                action = self._create_recovery_action(strategy, classification, context)
                if action:
                    actions.append(action)
            except ValueError:
                # Unknown strategy, skip
                continue
        
        # Add user action if required
        if classification.user_action_required:
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.USER_ACTION_REQUIRED,
                description="User action required to resolve error",
                priority=10,
                requires_user_input=True,
                metadata={
                    "user_message": classification.user_message,
                    "resolution_steps": classification.resolution_steps
                }
            ))
        
        return actions
    
    def _generate_network_recovery_actions(
        self,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> List[RecoveryAction]:
        """Generate network-specific recovery actions."""
        actions = []
        
        if classification.retry_possible:
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                description="Retry network operation with exponential backoff",
                priority=80,
                metadata={
                    "max_retries": 3,
                    "base_delay": 2.0
                }
            ))
        
        # Add fallback to alternative endpoint if available
        if context.get("alternative_endpoint"):
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK_TO_ALTERNATIVE,
                description="Use alternative network endpoint",
                priority=70,
                metadata={
                    "alternative_endpoint": context["alternative_endpoint"]
                }
            ))
        
        return actions
    
    def _generate_timeout_recovery_actions(
        self,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> List[RecoveryAction]:
        """Generate timeout-specific recovery actions."""
        actions = []
        
        # Increase timeout and retry
        if classification.retry_possible:
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.INCREASE_TIMEOUT,
                description="Increase timeout and retry operation",
                priority=75,
                metadata={
                    "timeout_multiplier": 2.0,
                    "max_retries": 2
                }
            ))
        
        # Reduce complexity if possible
        if context.get("can_reduce_complexity", False):
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.REDUCE_COMPLEXITY,
                description="Reduce operation complexity and retry",
                priority=60,
                metadata={
                    "complexity_reduction": 0.5
                }
            ))
        
        return actions
    
    def _generate_resource_recovery_actions(
        self,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> List[RecoveryAction]:
        """Generate resource-specific recovery actions."""
        actions = []
        
        # Free resources
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.FREE_RESOURCES,
            description="Free system resources and retry",
            priority=85,
            metadata={
                "cleanup_memory": True,
                "cleanup_temp_files": True
            }
        ))
        
        # Reduce load
        if context.get("can_reduce_load", False):
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.REDUCE_LOAD,
                description="Reduce system load and retry",
                priority=70,
                metadata={
                    "load_reduction": 0.3
                }
            ))
        
        return actions
    
    def _generate_database_recovery_actions(
        self,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> List[RecoveryAction]:
        """Generate database-specific recovery actions."""
        actions = []
        
        if classification.retry_possible:
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                description="Retry database operation with backoff",
                priority=80,
                metadata={
                    "max_retries": 2,
                    "base_delay": 1.0
                }
            ))
        
        # Switch to read replica if available
        if context.get("read_replica_available", False):
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.SWITCH_ENDPOINT,
                description="Switch to read replica",
                priority=75,
                metadata={
                    "endpoint_type": "read_replica"
                }
            ))
        
        return actions
    
    def _generate_ai_recovery_actions(
        self,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> List[RecoveryAction]:
        """Generate AI-specific recovery actions."""
        actions = []
        
        # Fallback to alternative model
        if context.get("alternative_models"):
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK_MODEL,
                description="Use alternative AI model",
                priority=85,
                metadata={
                    "models": context["alternative_models"]
                }
            ))
        
        # Truncate context if too large
        if "context_too_large" in classification.recovery_strategies:
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.TRUNCATE_CONTEXT,
                description="Truncate context and retry",
                priority=70,
                metadata={
                    "max_tokens": 4000
                }
            ))
        
        return actions
    
    def _generate_validation_recovery_actions(
        self,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> List[RecoveryAction]:
        """Generate validation-specific recovery actions."""
        actions = []
        
        # User action required for validation errors
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.USER_ACTION_REQUIRED,
            description="User action required to fix validation error",
            priority=90,
            requires_user_input=True,
            metadata={
                "user_message": classification.user_message,
                "resolution_steps": classification.resolution_steps
            }
        ))
        
        return actions
    
    def _create_recovery_action(
        self,
        strategy: RecoveryStrategy,
        classification: ErrorClassification,
        context: Dict[str, Any]
    ) -> Optional[RecoveryAction]:
        """Create recovery action from strategy."""
        # Map strategies to default actions
        strategy_descriptions = {
            RecoveryStrategy.RETRY_WITH_BACKOFF: "Retry operation with exponential backoff",
            RecoveryStrategy.FALLBACK_TO_CACHE: "Use cached response if available",
            RecoveryStrategy.FALLBACK_TO_ALTERNATIVE: "Use alternative service/method",
            RecoveryStrategy.FREE_RESOURCES: "Free system resources",
            RecoveryStrategy.INCREASE_TIMEOUT: "Increase operation timeout",
            RecoveryStrategy.DEGRADE_SERVICE: "Degrade service functionality",
        }
        
        description = strategy_descriptions.get(strategy, f"Execute {strategy.value} recovery")
        
        return RecoveryAction(
            strategy=strategy,
            description=description,
            priority=50,  # Default priority
            metadata={}
        )
    
    async def _execute_recovery_action(
        self,
        action: RecoveryAction,
        context: Dict[str, Any]
    ) -> RecoveryAttempt:
        """Execute a single recovery action."""
        attempt = RecoveryAttempt(
            action=action,
            attempt_number=1,
            start_time=datetime.utcnow()
        )
        
        try:
            # Get handler for action
            handler_class = self.action_handlers.get(action.strategy)
            if not handler_class:
                raise ValueError(f"No handler for strategy: {action.strategy}")
            
            handler = handler_class(action)
            
            # Check if action can be executed
            if not handler.can_execute(context):
                attempt.status = RecoveryStatus.FAILED
                attempt.exception = Exception("Action cannot be executed in current context")
                attempt.end_time = datetime.utcnow()
                return attempt
            
            # Execute action with timeout
            result = await asyncio.wait_for(
                handler.execute(context),
                timeout=action.timeout
            )
            
            attempt.result = result
            attempt.status = RecoveryStatus.SUCCESS
            attempt.end_time = datetime.utcnow()
            
        except asyncio.TimeoutError:
            attempt.status = RecoveryStatus.FAILED
            attempt.exception = Exception(f"Recovery action timed out after {action.timeout}s")
            attempt.end_time = datetime.utcnow()
            
        except Exception as e:
            attempt.status = RecoveryStatus.FAILED
            attempt.exception = e
            attempt.end_time = datetime.utcnow()
        
        return attempt
    
    def get_recovery_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get recovery statistics for analysis."""
        stats = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "average_duration": 0.0,
            "success_rate": 0.0,
            "most_common_strategies": {},
        }
        
        results_to_analyze = []
        if operation_name and operation_name in self.recovery_history:
            results_to_analyze = self.recovery_history[operation_name]
        else:
            for results in self.recovery_history.values():
                results_to_analyze.extend(results)
        
        if not results_to_analyze:
            return stats
        
        stats["total_recoveries"] = len(results_to_analyze)
        
        successful_count = sum(1 for r in results_to_analyze if r.final_status == RecoveryStatus.SUCCESS)
        failed_count = sum(1 for r in results_to_analyze if r.final_status == RecoveryStatus.FAILED)
        
        stats["successful_recoveries"] = successful_count
        stats["failed_recoveries"] = failed_count
        
        if results_to_analyze:
            stats["average_duration"] = sum(r.total_duration for r in results_to_analyze) / len(results_to_analyze)
            stats["success_rate"] = successful_count / len(results_to_analyze)
        
        # Calculate most common strategies
        strategy_counts = {}
        for result in results_to_analyze:
            if result.successful_action:
                strategy = result.successful_action.strategy.value
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        if strategy_counts:
            stats["most_common_strategies"] = dict(
                sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            )
        
        return stats


# Global error recovery manager instance
error_recovery_manager = ErrorRecoveryManager()