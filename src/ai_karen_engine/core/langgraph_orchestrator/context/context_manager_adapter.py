from typing import Optional, Any
import logging
from ai_karen_engine.memory.memory_service import WebUIMemoryService
from .context_manager import ContextManager

logger = logging.getLogger(__name__)

async def resolve_memory_service(orchestrator_instance: Any) -> Optional[Any]:
    """Resolve the shared memory service via the service registry if possible."""

    if (getattr(orchestrator_instance, "_memory_service", None) is not None or 
        getattr(orchestrator_instance, "_memory_resolution_failed", False)):
        return orchestrator_instance._memory_service

    try:
        from ai_karen_engine.core.service_registry import (
            get_memory_service,
        )  # Lazy import

        orchestrator_instance._memory_service = await get_memory_service()
    except Exception as exc:  # pragma: no cover - optional dependency
        if not getattr(orchestrator_instance, "_memory_resolution_failed", False):
            logger.warning("Memory service unavailable: %s", exc)
        try:
            orchestrator_instance._memory_service = WebUIMemoryService()
            logger.info("Fell back to direct WebUIMemoryService initialization")
        except Exception as fallback_exc:  # pragma: no cover - optional dependency
            logger.warning(
                "Direct memory service fallback unavailable: %s", fallback_exc
            )
            orchestrator_instance._memory_resolution_failed = True
            orchestrator_instance._memory_service = None

    return orchestrator_instance._memory_service

async def ensure_context_manager(orchestrator_instance: Any) -> ContextManager:
    """Return a context manager bound to the configured memory service."""

    if getattr(orchestrator_instance, "_context_manager", None) is not None:
        return orchestrator_instance._context_manager

    memory_service = await resolve_memory_service(orchestrator_instance)
    orchestrator_instance._context_manager = ContextManager(memory_service)
    return orchestrator_instance._context_manager
