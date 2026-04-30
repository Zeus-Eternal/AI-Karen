from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, List

from ai_karen_engine.core.runtime.chat_runtime_control_plane import get_chat_runtime_control_plane

logger = logging.getLogger(__name__)


class ChatRuntimeService:
    """Canonical chat runtime service for route-level orchestration helpers."""

    async def ensure_control_plane_ready(self, user_context: Optional[dict[str, Any]] = None):
        control_plane = await get_chat_runtime_control_plane()
        return await control_plane.get_runtime_response(user_context=user_context)

    async def get_orchestrator(self):
        """Canonical runtime entrypoint for orchestrator access across routes."""
        from ai_karen_engine.core.langgraph_orchestrator import get_default_orchestrator

        return await get_default_orchestrator()

    async def build_router_fallback_assist_payload(
        self,
        *,
        request: Any,
        correlation_id: str,
        conversation_id: str,
        start_time: float,
        request_config_metadata: Dict[str, Any],
        actual_mode: str,
        transport: str,
        failure: Exception,
        streaming_enabled: bool = False,
        metadata_normalizer: Any,
    ) -> Optional[Dict[str, Any]]:
        """Use provider router fallback when orchestration fails before answering."""
        from ai_karen_engine.services.models.routing.llm_router_service import ChatRequest, LLMRouter

        router = LLMRouter()
        user_preferences = {
            "preferred_llm_provider": request.preferred_llm_provider,
            "preferred_model": request.preferred_model,
        }
        text = ""
        metadata: Dict[str, Any] = {}

        try:
            async for chunk in router.process_chat_request(
                ChatRequest(
                    message=request.message,
                    stream=False,
                    preferred_model=request.preferred_model,
                    conversation_id=conversation_id,
                    max_tokens=120,
                ),
                user_preferences=user_preferences,
            ):
                if isinstance(chunk, str):
                    text += chunk
                elif isinstance(chunk, dict):
                    chunk_metadata = chunk.get("metadata")
                    if isinstance(chunk_metadata, dict):
                        metadata.update(chunk_metadata)
        except Exception as router_error:
            logger.warning("Direct provider router fallback failed after orchestrator error: %s", router_error, extra={"correlation_id": correlation_id})
            requested_provider = request.preferred_llm_provider or "orchestrator"
            requested_model = request.preferred_model or "auto"
            try:
                fallback = await router.generate_with_degraded_runtime_fallback(
                    request=ChatRequest(
                        message=request.message,
                        stream=False,
                        preferred_model=request.preferred_model,
                        conversation_id=conversation_id,
                        max_tokens=120,
                    ),
                    requested_provider=requested_provider,
                    requested_model=requested_model,
                    failure_reason=str(failure),
                )
                text = str(fallback.get("content") or "")
                metadata.update(fallback.get("metadata") or {})
            except Exception as fallback_error:
                logger.error("Router degraded fallback failed after orchestrator error: %s", fallback_error, extra={"correlation_id": correlation_id})
                return None

        if not text.strip():
            return None

        response_metadata = metadata_normalizer(
            metadata=metadata,
            request=request,
            final_state=None,
            correlation_id=correlation_id,
            conversation_id=conversation_id,
            start_time=start_time,
            request_config_metadata=request_config_metadata,
            streaming_enabled=streaming_enabled,
            transport=transport,
            actual_response_mode=actual_mode,
        )
        response_metadata["orchestrator_error"] = {"type": type(failure).__name__, "message": str(failure)[:300]}

        return {"answer": text.strip(), "structured_content": {}, "actions": [], "metadata": response_metadata}

    def build_router_fallback_sse_events(self, payload: Dict[str, Any], correlation_id: str) -> List[Dict[str, Any]]:
        metadata = payload.get("metadata") or {}
        llm_metadata = metadata.get("llm") or {}
        requested_provider = llm_metadata.get("requested_provider")
        requested_model = llm_metadata.get("requested_model")
        actual_provider = llm_metadata.get("actual_provider")
        answer = str(payload.get("answer") or "").strip()

        events: List[Dict[str, Any]] = [{"type": "status", "content": "Selecting provider...", "correlation_id": correlation_id, "metadata": {**metadata, "status": "provider_selection", "requested_provider": requested_provider, "requested_model": requested_model}}]
        if requested_provider and actual_provider and str(requested_provider).lower() != str(actual_provider).lower():
            events.extend([
                {"type": "status", "content": "Requested provider unavailable; trying fallback.", "correlation_id": correlation_id, "metadata": {**metadata, "status": "provider_failed", "fallback_next": actual_provider}},
                {"type": "status", "content": f"Fallback provider selected: {actual_provider}", "correlation_id": correlation_id, "metadata": {**metadata, "status": "fallback_provider_selected"}},
            ])
        if answer:
            events.append({"type": "content", "content": answer, "correlation_id": correlation_id, "metadata": metadata})
        events.append({"type": "complete", "content": "", "correlation_id": correlation_id, "metadata": {**metadata, "status": "completed", "content_length": len(answer)}})
        return events


_chat_runtime_service: Optional[ChatRuntimeService] = None


def get_chat_runtime_service() -> ChatRuntimeService:
    global _chat_runtime_service
    if _chat_runtime_service is None:
        _chat_runtime_service = ChatRuntimeService()
    return _chat_runtime_service
