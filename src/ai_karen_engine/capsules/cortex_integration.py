"""
CORTEX Integration for Capsule System

Integrates capsule discovery and execution with the CORTEX
intent resolution and dispatch system.

This module:
- Registers capsule capabilities as CORTEX intents
- Routes capsule execution through CORTEX dispatch
- Provides unified API for capsule + plugin execution
"""

import logging
from typing import Dict, Any, Optional, List

from ai_karen_engine.capsules.orchestrator import get_capsule_orchestrator
from ai_karen_engine.capsules.base_capsule import CapsuleExecutionError

logger = logging.getLogger(__name__)


class CapsuleCortexAdapter:
    """
    Adapter for integrating capsules with CORTEX dispatch.

    This adapter makes capsules discoverable and executable
    through the CORTEX intent resolution system.
    """

    def __init__(self):
        self.orchestrator = get_capsule_orchestrator()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the adapter and register capsule intents"""
        if self._initialized:
            return

        # Initialize orchestrator with auto-discovery
        self.orchestrator.initialize(auto_discover=True)

        logger.info("CORTEX capsule adapter initialized")
        self._initialized = True

    def resolve_capsule_intent(self, intent: str) -> Optional[str]:
        """
        Resolve an intent to a capsule ID.

        Args:
            intent: Intent string from CORTEX

        Returns:
            Capsule ID if found, None otherwise
        """
        return self.orchestrator.resolve_intent(intent)

    def execute_capsule_intent(
        self,
        intent: str,
        user_ctx: Dict[str, Any],
        query: str,
        context: Optional[Dict[str, Any]] = None,
        memory_context: Optional[List[Dict[str, Any]]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a capsule through CORTEX intent.

        Args:
            intent: Intent string resolved by CORTEX
            user_ctx: User context
            query: User query
            context: Optional context dict
            memory_context: Optional memory context
            correlation_id: Optional correlation ID

        Returns:
            Dict with result and metadata

        Raises:
            CapsuleExecutionError: If execution fails
        """
        capsule_id = self.resolve_capsule_intent(intent)

        if capsule_id is None:
            raise CapsuleExecutionError(f"No capsule found for intent: {intent}")

        # Build request from query and context
        request = {
            "query": query,
            **(context or {}),
        }

        # Execute capsule
        result = self.orchestrator.execute_capsule(
            capsule_id=capsule_id,
            request=request,
            user_ctx=user_ctx,
            correlation_id=correlation_id,
            memory_context=memory_context,
        )

        # Convert CapsuleResult to CORTEX-compatible dict
        return {
            "result": result.result,
            "metadata": result.metadata,
            "audit": result.audit,
            "security": result.security,
            "metrics": result.metrics,
            "errors": result.errors,
        }

    def list_capsule_intents(self) -> List[str]:
        """
        Get list of all capsule-based intents for CORTEX registration.

        Returns:
            List of intent strings
        """
        return list(self.orchestrator.registry.list_capsules())

    def get_capabilities(self) -> Dict[str, List[str]]:
        """
        Get mapping of capabilities to capsule IDs.

        Returns:
            Dict mapping capability -> list of capsule IDs
        """
        capabilities = {}
        for capsule_id in self.orchestrator.registry.list_capsules():
            caps = self.orchestrator.registry.get_capabilities(capsule_id)
            for cap in caps:
                if cap not in capabilities:
                    capabilities[cap] = []
                capabilities[cap].append(capsule_id)
        return capabilities


# Global adapter instance
_adapter: Optional[CapsuleCortexAdapter] = None


def get_cortex_adapter() -> CapsuleCortexAdapter:
    """Get or create global CORTEX adapter"""
    global _adapter
    if _adapter is None:
        _adapter = CapsuleCortexAdapter()
    return _adapter


def register_capsules_with_cortex() -> None:
    """
    Register all capsules with CORTEX dispatch system.

    This function should be called during app initialization to make
    capsules available through CORTEX intent resolution.
    """
    adapter = get_cortex_adapter()
    adapter.initialize()

    # Get all capsule intents
    intents = adapter.list_capsule_intents()

    logger.info(f"Registered {len(intents)} capsule intents with CORTEX")

    # Log capabilities
    capabilities = adapter.get_capabilities()
    logger.info(f"Registered {len(capabilities)} capsule capabilities")


async def dispatch_capsule_from_cortex(
    intent: str,
    user_ctx: Dict[str, Any],
    query: str,
    context: Optional[Dict[str, Any]] = None,
    memory_context: Optional[List[Dict[str, Any]]] = None,
    trace: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Dispatch handler for CORTEX integration.

    This function is designed to be called from CORTEX dispatch
    when a capsule intent is resolved.

    Args:
        intent: Resolved intent (capsule ID)
        user_ctx: User context
        query: User query
        context: Optional context
        memory_context: Optional memory context
        trace: Optional trace for debugging

    Returns:
        Dict with result and metadata
    """
    adapter = get_cortex_adapter()

    if trace is not None:
        trace.append({"stage": "capsule_dispatch", "intent": intent})

    try:
        result = adapter.execute_capsule_intent(
            intent=intent,
            user_ctx=user_ctx,
            query=query,
            context=context,
            memory_context=memory_context,
        )

        if trace is not None:
            trace.append({"stage": "capsule_executed", "success": True})

        return result

    except Exception as e:
        if trace is not None:
            trace.append({"stage": "capsule_error", "error": str(e)})
        raise


__all__ = [
    "CapsuleCortexAdapter",
    "get_cortex_adapter",
    "register_capsules_with_cortex",
    "dispatch_capsule_from_cortex",
]
