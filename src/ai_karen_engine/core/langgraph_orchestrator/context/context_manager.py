from typing import Dict, Any, List, Optional
    
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    """Thin adapter over the current memory/context stack for LangGraph."""

    def __init__(self, memory_service: Optional[Any] = None):
        self.memory_service = memory_service

    async def build_context(
        self,
        *,
        user_id: str,
        session_id: Optional[str],
        prompt: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        user_settings: Optional[Dict[str, Any]] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "user_id": user_id,
            "session_id": session_id,
            "prompt": prompt,
            "conversation_history": conversation_history or [],
            "user_settings": user_settings or {},
            "memories": memories or [],
        }

        memory_service = self.memory_service
        if memory_service is not None and hasattr(memory_service, "build_context"):
            try:
                retrieved_context = await memory_service.build_context(
                    tenant_id=user_id,
                    query=prompt,
                    user_id=user_id,
                    session_id=session_id,
                    conversation_id=session_id,
                )
                if isinstance(retrieved_context, dict):
                    context.update(retrieved_context)
            except TypeError:
                logger.debug(
                    "Memory service build_context signature mismatch; using local context adapter"
                )
            except Exception as exc:
                logger.warning("Context build fallback triggered: %s", exc)

        return context

    def clear_context_cache(self) -> None:
        """Compatibility no-op for legacy orchestrator cleanup."""
        return None
