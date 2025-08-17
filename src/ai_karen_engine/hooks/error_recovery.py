"""
Hook System Error Recovery with Circuit Breaker Patterns

This module extends existing hook system error handling with:
- Circuit breaker patterns for hook execution
- Retry logic with exponential backoff
- Hook bypass mechanisms for system stability
- Error recovery strategies
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

from ai_karen_engine.hooks import HookContext, HookTypes, get_hook_manager

logger = logging.getLogger(__name__)


class HookErrorType(Enum):
    """Types of hook system errors."""
    
    EXECUTION_TIMEOUT = "execution_timeout"
    SYSTEM_OVERLOAD = "system_overload"
    HOOK_FAILURE = "hook_failure"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class RecoveryStrategy(Enum):
    """Recovery strategies for hook errors."""
    
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    HOOK_BYPASS = "hook_bypass"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FALLBACK_HOOK = "fallback_hook"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    
    failure_threshold: int = 5
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


@dataclass
class HookCircuitBreakerState:
    """State of a hook circuit breaker."""
    
    state: str = "closed"  # closed, open, half_open
    failure_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0
    success_count: int = 0
    total_calls: int = 0


class HookErrorRecoveryManager:
    """Manages error recovery for hook system."""
    
    def __init__(self):
        self.hook_manager = get_hook_manager()
        self.circuit_breakers: Dict[str, HookCircuitBreakerState] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.circuit_breaker_configs: Dict[str, CircuitBreakerConfig] = {}
        self.error_history: Dict[str, List[Dict[str, Any]]] = {}
        self.bypass_hooks: set = set()
        
        # Default configurations
        self.default_retry_config = RetryConfig()
        self.default_circuit_breaker_config = CircuitBreakerConfig()
        
        # Initialize circuit breakers for common hook types
        self._initialize_circuit_breakers()
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for common hook types."""
        common_hook_types = [
            HookTypes.PRE_MESSAGE,
            HookTypes.POST_MESSAGE,
            HookTypes.PLUGIN_EXECUTION_START,
            HookTypes.PLUGIN_EXECUTION_END,
            HookTypes.EXTENSION_ACTIVATED,
            HookTypes.EXTENSION_DEACTIVATED,
            HookTypes.MEMORY_STORE,
            HookTypes.MEMORY_RETRIEVE,
            HookTypes.LLM_REQUEST,
            HookTypes.LLM_RESPONSE,
            HookTypes.SYSTEM_ERROR
        ]
        
        for hook_type in common_hook_types:
            self.circuit_breakers[hook_type] = HookCircuitBreakerState()
            self.circuit_breaker_configs[hook_type] = CircuitBreakerConfig()
            self.retry_configs[hook_type] = RetryConfig()
            self.error_history[hook_type] = []
    
    async def execute_hook_with_recovery(
        self,
        hook_type: str,
        context: HookContext,
        recovery_strategy: Optional[RecoveryStrategy] = None
    ) -> Dict[str, Any]:
        """Execute hook with error recovery mechanisms."""
        
        # Check if hook is bypassed
        if hook_type in self.bypass_hooks:
            logger.info(f"Hook {hook_type} is bypassed")
            return self._create_bypass_response(hook_type, "hook_bypassed")
        
        # Check circuit breaker
        if not self._can_execute_hook(hook_type):
            logger.warning(f"Circuit breaker open for hook {hook_type}")
            return self._create_bypass_response(hook_type, "circuit_breaker_open")
        
        # Determine recovery strategy
        if recovery_strategy is None:
            recovery_strategy = self._determine_recovery_strategy(hook_type)
        
        # Execute with appropriate strategy
        try:
            if recovery_strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                return await self._execute_with_retry(hook_type, context)
            elif recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                return await self._execute_with_circuit_breaker(hook_type, context)
            elif recovery_strategy == RecoveryStrategy.HOOK_BYPASS:
                return self._create_bypass_response(hook_type, "strategy_bypass")
            elif recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                return await self._execute_with_degradation(hook_type, context)
            elif recovery_strategy == RecoveryStrategy.FALLBACK_HOOK:
                return await self._execute_with_fallback(hook_type, context)
            else:
                # Default execution
                return await self._execute_hook_safely(hook_type, context)
        
        except Exception as e:
            logger.error(f"Hook recovery failed for {hook_type}: {e}")
            self._record_hook_failure(hook_type, e)
            return self._create_error_response(hook_type, e)
    
    async def _execute_with_retry(
        self,
        hook_type: str,
        context: HookContext
    ) -> Dict[str, Any]:
        """Execute hook with retry logic and exponential backoff."""
        retry_config = self.retry_configs.get(hook_type, self.default_retry_config)
        
        last_exception = None
        for attempt in range(retry_config.max_attempts):
            try:
                # Calculate delay for this attempt
                if attempt > 0:
                    delay = min(
                        retry_config.base_delay * (retry_config.backoff_multiplier ** (attempt - 1)),
                        retry_config.max_delay
                    )
                    
                    # Add jitter if enabled
                    if retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.info(f"Retrying hook {hook_type} after {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                
                # Execute hook
                result = await self._execute_hook_safely(hook_type, context)
                
                # Record success
                self._record_hook_success(hook_type)
                
                # Add retry metadata
                result["retry_metadata"] = {
                    "attempts": attempt + 1,
                    "max_attempts": retry_config.max_attempts,
                    "strategy": "retry_with_backoff"
                }
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Hook {hook_type} attempt {attempt + 1} failed: {e}")
                
                # Record failure
                self._record_hook_failure(hook_type, e)
                
                # If this is the last attempt, don't continue
                if attempt == retry_config.max_attempts - 1:
                    break
        
        # All retries failed
        logger.error(f"Hook {hook_type} failed after {retry_config.max_attempts} attempts")
        return self._create_error_response(hook_type, last_exception, retry_exhausted=True)
    
    async def _execute_with_circuit_breaker(
        self,
        hook_type: str,
        context: HookContext
    ) -> Dict[str, Any]:
        """Execute hook with circuit breaker pattern."""
        circuit_breaker = self.circuit_breakers.get(hook_type)
        if not circuit_breaker:
            # Initialize if not exists
            circuit_breaker = HookCircuitBreakerState()
            self.circuit_breakers[hook_type] = circuit_breaker
        
        config = self.circuit_breaker_configs.get(hook_type, self.default_circuit_breaker_config)
        
        # Update circuit breaker state
        self._update_circuit_breaker_state(hook_type, config)
        
        # Check if we can execute
        if circuit_breaker.state == "open":
            return self._create_bypass_response(hook_type, "circuit_breaker_open")
        
        try:
            # Execute hook
            result = await self._execute_hook_safely(hook_type, context)
            
            # Record success
            self._record_circuit_breaker_success(hook_type)
            
            result["circuit_breaker_metadata"] = {
                "state": circuit_breaker.state,
                "failure_count": circuit_breaker.failure_count,
                "strategy": "circuit_breaker"
            }
            
            return result
            
        except Exception as e:
            # Record failure
            self._record_circuit_breaker_failure(hook_type, e)
            
            # Check if circuit breaker should open
            if circuit_breaker.failure_count >= config.failure_threshold:
                circuit_breaker.state = "open"
                circuit_breaker.last_failure_time = time.time()
                logger.warning(f"Circuit breaker opened for hook {hook_type}")
            
            return self._create_error_response(hook_type, e, circuit_breaker_triggered=True)
    
    async def _execute_with_degradation(
        self,
        hook_type: str,
        context: HookContext
    ) -> Dict[str, Any]:
        """Execute hook with graceful degradation."""
        try:
            # Try normal execution with shorter timeout
            result = await asyncio.wait_for(
                self._execute_hook_safely(hook_type, context),
                timeout=5.0  # Shorter timeout for degraded mode
            )
            
            result["degradation_metadata"] = {
                "mode": "normal",
                "strategy": "graceful_degradation"
            }
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Hook {hook_type} timed out in degraded mode, bypassing")
            return self._create_bypass_response(hook_type, "degraded_timeout")
        
        except Exception as e:
            logger.warning(f"Hook {hook_type} failed in degraded mode: {e}")
            
            # Try to extract partial results or provide minimal functionality
            degraded_result = self._create_degraded_response(hook_type, context, e)
            return degraded_result
    
    async def _execute_with_fallback(
        self,
        hook_type: str,
        context: HookContext
    ) -> Dict[str, Any]:
        """Execute hook with fallback to alternative hooks."""
        try:
            # Try primary hook
            result = await self._execute_hook_safely(hook_type, context)
            
            result["fallback_metadata"] = {
                "used_fallback": False,
                "strategy": "fallback_hook"
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"Primary hook {hook_type} failed, trying fallback: {e}")
            
            # Try fallback hooks
            fallback_hooks = self._get_fallback_hooks(hook_type)
            
            for fallback_hook in fallback_hooks:
                try:
                    # Create fallback context
                    fallback_context = HookContext(
                        hook_type=fallback_hook,
                        data={**context.data, "fallback_from": hook_type},
                        user_context=context.user_context
                    )
                    
                    result = await self._execute_hook_safely(fallback_hook, fallback_context)
                    
                    result["fallback_metadata"] = {
                        "used_fallback": True,
                        "fallback_hook": fallback_hook,
                        "original_hook": hook_type,
                        "strategy": "fallback_hook"
                    }
                    
                    logger.info(f"Successfully used fallback hook {fallback_hook} for {hook_type}")
                    return result
                    
                except Exception as fallback_error:
                    logger.warning(f"Fallback hook {fallback_hook} also failed: {fallback_error}")
                    continue
            
            # All fallbacks failed
            logger.error(f"All fallback hooks failed for {hook_type}")
            return self._create_error_response(hook_type, e, fallback_exhausted=True)
    
    async def _execute_hook_safely(
        self,
        hook_type: str,
        context: HookContext
    ) -> Dict[str, Any]:
        """Execute hook with basic safety measures."""
        try:
            # Execute with timeout
            summary = await asyncio.wait_for(
                self.hook_manager.trigger_hooks(context),
                timeout=30.0  # Default timeout
            )
            
            return {
                "success": True,
                "hook_type": hook_type,
                "summary": summary.__dict__ if hasattr(summary, '__dict__') else str(summary),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except asyncio.TimeoutError:
            raise Exception(f"Hook {hook_type} execution timed out")
        except Exception as e:
            raise Exception(f"Hook {hook_type} execution failed: {str(e)}")
    
    def _can_execute_hook(self, hook_type: str) -> bool:
        """Check if hook can be executed based on circuit breaker state."""
        circuit_breaker = self.circuit_breakers.get(hook_type)
        if not circuit_breaker:
            return True
        
        if circuit_breaker.state == "closed":
            return True
        
        if circuit_breaker.state == "open":
            config = self.circuit_breaker_configs.get(hook_type, self.default_circuit_breaker_config)
            
            # Check if timeout has passed
            if time.time() - circuit_breaker.last_failure_time > config.timeout_seconds:
                circuit_breaker.state = "half_open"
                circuit_breaker.half_open_calls = 0
                return True
            
            return False
        
        if circuit_breaker.state == "half_open":
            config = self.circuit_breaker_configs.get(hook_type, self.default_circuit_breaker_config)
            return circuit_breaker.half_open_calls < config.half_open_max_calls
        
        return False
    
    def _determine_recovery_strategy(self, hook_type: str) -> RecoveryStrategy:
        """Determine the best recovery strategy for a hook type."""
        # Get error history for this hook
        history = self.error_history.get(hook_type, [])
        
        if not history:
            return RecoveryStrategy.RETRY_WITH_BACKOFF
        
        # Analyze recent errors
        recent_errors = [e for e in history if time.time() - e["timestamp"] < 300]  # Last 5 minutes
        
        if len(recent_errors) >= 10:
            # Too many recent errors, bypass
            return RecoveryStrategy.HOOK_BYPASS
        elif len(recent_errors) >= 5:
            # Moderate errors, use circuit breaker
            return RecoveryStrategy.CIRCUIT_BREAKER
        elif any(e.get("error_type") == "timeout" for e in recent_errors):
            # Timeout issues, use graceful degradation
            return RecoveryStrategy.GRACEFUL_DEGRADATION
        else:
            # Default to retry
            return RecoveryStrategy.RETRY_WITH_BACKOFF
    
    def _update_circuit_breaker_state(self, hook_type: str, config: CircuitBreakerConfig):
        """Update circuit breaker state based on configuration."""
        circuit_breaker = self.circuit_breakers.get(hook_type)
        if not circuit_breaker:
            return
        
        if circuit_breaker.state == "half_open":
            # Check if we should close or open the circuit
            if circuit_breaker.success_count >= config.success_threshold:
                circuit_breaker.state = "closed"
                circuit_breaker.failure_count = 0
                circuit_breaker.success_count = 0
                logger.info(f"Circuit breaker closed for hook {hook_type}")
    
    def _record_hook_success(self, hook_type: str):
        """Record successful hook execution."""
        circuit_breaker = self.circuit_breakers.get(hook_type)
        if circuit_breaker:
            circuit_breaker.success_count += 1
            circuit_breaker.total_calls += 1
    
    def _record_hook_failure(self, hook_type: str, error: Exception):
        """Record failed hook execution."""
        # Record in error history
        if hook_type not in self.error_history:
            self.error_history[hook_type] = []
        
        self.error_history[hook_type].append({
            "timestamp": time.time(),
            "error": str(error),
            "error_type": self._classify_error(error)
        })
        
        # Keep only recent history
        cutoff_time = time.time() - 3600  # 1 hour
        self.error_history[hook_type] = [
            e for e in self.error_history[hook_type] 
            if e["timestamp"] > cutoff_time
        ]
    
    def _record_circuit_breaker_success(self, hook_type: str):
        """Record successful execution for circuit breaker."""
        circuit_breaker = self.circuit_breakers.get(hook_type)
        if circuit_breaker:
            circuit_breaker.success_count += 1
            circuit_breaker.total_calls += 1
            
            if circuit_breaker.state == "half_open":
                config = self.circuit_breaker_configs.get(hook_type, self.default_circuit_breaker_config)
                if circuit_breaker.success_count >= config.success_threshold:
                    circuit_breaker.state = "closed"
                    circuit_breaker.failure_count = 0
                    circuit_breaker.success_count = 0
                    logger.info(f"Circuit breaker closed for hook {hook_type}")
    
    def _record_circuit_breaker_failure(self, hook_type: str, error: Exception):
        """Record failed execution for circuit breaker."""
        circuit_breaker = self.circuit_breakers.get(hook_type)
        if circuit_breaker:
            circuit_breaker.failure_count += 1
            circuit_breaker.total_calls += 1
            circuit_breaker.last_failure_time = time.time()
        
        # Also record in general error history
        self._record_hook_failure(hook_type, error)
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type."""
        error_msg = str(error).lower()
        
        if "timeout" in error_msg:
            return "timeout"
        elif "overload" in error_msg or "too many" in error_msg:
            return "overload"
        elif "connection" in error_msg or "network" in error_msg:
            return "network"
        elif "memory" in error_msg or "resource" in error_msg:
            return "resource"
        else:
            return "unknown"
    
    def _get_fallback_hooks(self, hook_type: str) -> List[str]:
        """Get fallback hooks for a given hook type."""
        fallback_mapping = {
            HookTypes.PRE_MESSAGE: ["message_validation", "basic_preprocessing"],
            HookTypes.POST_MESSAGE: ["message_logging", "basic_postprocessing"],
            HookTypes.LLM_REQUEST: ["simple_llm_request"],
            HookTypes.LLM_RESPONSE: ["simple_llm_response"],
            HookTypes.MEMORY_STORE: ["basic_memory_store"],
            HookTypes.MEMORY_RETRIEVE: ["basic_memory_retrieve"]
        }
        
        return fallback_mapping.get(hook_type, [])
    
    def _create_bypass_response(self, hook_type: str, reason: str) -> Dict[str, Any]:
        """Create response when hook is bypassed."""
        return {
            "success": True,
            "bypassed": True,
            "hook_type": hook_type,
            "bypass_reason": reason,
            "message": f"Hook {hook_type} was bypassed due to {reason}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_error_response(
        self,
        hook_type: str,
        error: Exception,
        retry_exhausted: bool = False,
        circuit_breaker_triggered: bool = False,
        fallback_exhausted: bool = False
    ) -> Dict[str, Any]:
        """Create error response."""
        return {
            "success": False,
            "hook_type": hook_type,
            "error": str(error),
            "error_type": self._classify_error(error),
            "retry_exhausted": retry_exhausted,
            "circuit_breaker_triggered": circuit_breaker_triggered,
            "fallback_exhausted": fallback_exhausted,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_degraded_response(
        self,
        hook_type: str,
        context: HookContext,
        error: Exception
    ) -> Dict[str, Any]:
        """Create degraded response with minimal functionality."""
        return {
            "success": True,
            "degraded": True,
            "hook_type": hook_type,
            "degraded_reason": str(error),
            "message": f"Hook {hook_type} running in degraded mode",
            "limited_functionality": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def bypass_hook(self, hook_type: str):
        """Temporarily bypass a hook type."""
        self.bypass_hooks.add(hook_type)
        logger.info(f"Hook {hook_type} bypassed")
    
    def enable_hook(self, hook_type: str):
        """Re-enable a bypassed hook type."""
        self.bypass_hooks.discard(hook_type)
        logger.info(f"Hook {hook_type} enabled")
    
    def reset_circuit_breaker(self, hook_type: str):
        """Reset circuit breaker for a hook type."""
        if hook_type in self.circuit_breakers:
            self.circuit_breakers[hook_type] = HookCircuitBreakerState()
            logger.info(f"Circuit breaker reset for hook {hook_type}")
    
    def get_hook_health_status(self, hook_type: str) -> Dict[str, Any]:
        """Get health status for a hook type."""
        circuit_breaker = self.circuit_breakers.get(hook_type)
        error_history = self.error_history.get(hook_type, [])
        
        recent_errors = [e for e in error_history if time.time() - e["timestamp"] < 300]
        
        return {
            "hook_type": hook_type,
            "is_bypassed": hook_type in self.bypass_hooks,
            "circuit_breaker_state": circuit_breaker.state if circuit_breaker else "unknown",
            "failure_count": circuit_breaker.failure_count if circuit_breaker else 0,
            "total_calls": circuit_breaker.total_calls if circuit_breaker else 0,
            "recent_errors": len(recent_errors),
            "last_error": error_history[-1] if error_history else None,
            "health_score": self._calculate_health_score(hook_type)
        }
    
    def _calculate_health_score(self, hook_type: str) -> float:
        """Calculate health score (0-1) for a hook type."""
        if hook_type in self.bypass_hooks:
            return 0.0
        
        circuit_breaker = self.circuit_breakers.get(hook_type)
        if not circuit_breaker or circuit_breaker.total_calls == 0:
            return 1.0
        
        if circuit_breaker.state == "open":
            return 0.0
        elif circuit_breaker.state == "half_open":
            return 0.5
        
        # Calculate based on success rate
        success_rate = 1.0 - (circuit_breaker.failure_count / circuit_breaker.total_calls)
        return max(0.0, min(1.0, success_rate))


# Global instance
_hook_error_recovery_manager: Optional[HookErrorRecoveryManager] = None


def get_hook_error_recovery_manager() -> HookErrorRecoveryManager:
    """Get the global hook error recovery manager instance."""
    global _hook_error_recovery_manager
    if _hook_error_recovery_manager is None:
        _hook_error_recovery_manager = HookErrorRecoveryManager()
    return _hook_error_recovery_manager


__all__ = [
    "HookErrorRecoveryManager",
    "HookErrorType",
    "RecoveryStrategy",
    "CircuitBreakerConfig",
    "RetryConfig",
    "get_hook_error_recovery_manager"
]