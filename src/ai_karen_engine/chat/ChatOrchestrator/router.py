from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ai_karen_engine.chat.ChatOrchestrator.models import FallbackContext, FallbackDecision
from ai_karen_engine.core.degraded_mode import get_degraded_mode_manager, DegradedModeReason

logger = logging.getLogger(__name__)

class FallbackRouter:
    """Central authority for fallback decisions across the orchestrator."""

    def __init__(self):
        self.degraded_mode_manager = get_degraded_mode_manager()

    def create_fallback_context(
        self, correlation_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> FallbackContext:
        """Initialize a new fallback context for a request."""
        return FallbackContext(correlation_id=correlation_id, metadata=metadata or {})

    def get_trial_plan(self, request: Any) -> List[Dict[str, str]]:
        """
        Generate a sequence of model/provider trials based on request metadata.
        Standardizes the primary -> secondary -> local fallback chain.
        """
        from ai_karen_engine.config.config_manager import get_default_model, get_default_provider
        
        # Primary selection from request or global default
        primary_model = request.metadata.get("model_id") or get_default_model()
        primary_provider = request.metadata.get("provider") or get_default_provider()
        
        plan = [{"model_id": primary_model, "provider": primary_provider}]
        
        # Add local fallback if different from primary
        local_model = "Phi-3-mini-4k-instruct-q4.gguf"
        if primary_model != local_model:
            plan.append({"model_id": local_model, "provider": "llamacpp"})
            
        return plan

    def record_fallback_attempt(
        self,
        context: FallbackContext,
        provider: str,
        level: str,
        reason: str,
    ) -> None:
        """Track an attempted model failure in the context."""
        context.attempt_count += 1
        context.providers_attempted.append(provider)
        context.fallback_level = level
        context.decision_history.append(f"{level}:{provider} ({reason})")
        logger.info(
            "Recorded fallback attempt %d for %s: %s (%s)",
            context.attempt_count,
            context.correlation_id,
            provider,
            reason,
        )

    def should_enter_degraded_mode(
        self, context: FallbackContext, last_error: Optional[Exception] = None
    ) -> bool:
        """Determine if we should give up and use core helper models."""
        if context.attempt_count >= 3:
            return True
        if context.fallback_level == "local":
            return True
        return False

    def activate_degraded_mode(self, context: FallbackContext, reason: str) -> None:
        """Trigger global degraded mode state."""
        logger.error(
            "Activating degraded mode for %s: %s", context.correlation_id, reason
        )
        # Fix: Align with DegradedModeManager.activate_degraded_mode signature
        self.degraded_mode_manager.activate_degraded_mode(
            reason=DegradedModeReason.ALL_PROVIDERS_FAILED,
            failed_providers=context.providers_attempted
        )
