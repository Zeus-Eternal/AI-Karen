"""
Safe Stage Runner for AI Karen Resilience Layer.

Executes optional stages through a resilient pipeline (flags, timeout, breaker, fallback).
"""

import asyncio
import logging
from typing import Callable, Any, Dict, Optional

from .feature_flags import get_feature_flags
from .circuit_breaker import get_breaker_registry
from .fallback_manager import get_fallback_manager
from .pipeline_policy import get_pipeline_policy

logger = logging.getLogger(__name__)

class SafeStageRunner:
    """Executes a stage safely, applying resilience patterns."""
    
    def __init__(self):
        self.flags = get_feature_flags()
        self.breakers = get_breaker_registry()
        self.fallbacks = get_fallback_manager()
        self.policies = get_pipeline_policy()
        
    async def run_stage(
        self,
        stage_name: str,
        flag_name: str,
        func: Callable,
        *args,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_overrides: Optional[Dict[str, bool]] = None,
        **kwargs
    ) -> Any:
        """
        Execute a stage safely with graceful degradation.
        1. Check feature flag
        2. Check circuit breaker
        3. Enforce timeout and retries
        4. Provide structured fallback on failure
        """
        # 1. Feature Flag Check
        if not self.flags.is_enabled(flag_name, tenant_id, user_id, request_overrides):
            logger.debug(f"Stage '{stage_name}' skipped: Feature flag '{flag_name}' disabled.")
            return self.fallbacks.get_fallback(stage_name, *args, **kwargs)
            
        breaker = self.breakers.get_breaker(stage_name)
        policy = self.policies.get_policy(stage_name)
        
        # 2. Circuit Breaker Check
        if not breaker.allow_request():
            logger.warning(f"Stage '{stage_name}' blocked: Circuit breaker OPEN.")
            return self.fallbacks.get_fallback(stage_name, *args, **kwargs)
            
        # 3. Execution with Timeout & Retries
        retries_left = policy.max_retries
        while retries_left >= 0:
            try:
                # Wrap sync functions in thread or assume async
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=policy.timeout_seconds)
                else:
                    # For sync functions, we use run_in_executor to avoid blocking the event loop
                    loop = asyncio.get_running_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: func(*args, **kwargs)),
                        timeout=policy.timeout_seconds
                    )
                
                breaker.record_success()
                return result
                
            except asyncio.TimeoutError:
                logger.error(f"Stage '{stage_name}' timed out after {policy.timeout_seconds}s.")
                breaker.record_failure()
                retries_left -= 1
            except Exception as e:
                logger.error(f"Stage '{stage_name}' failed: {str(e)}")
                breaker.record_failure()
                retries_left -= 1
                
        # 4. Record Failure and Fallback
        return self.fallbacks.get_fallback(stage_name, *args, **kwargs)

safe_runner = SafeStageRunner()

def get_safe_stage_runner() -> SafeStageRunner:
    return safe_runner
