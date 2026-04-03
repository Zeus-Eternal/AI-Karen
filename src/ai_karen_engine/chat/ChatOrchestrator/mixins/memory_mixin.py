from __future__ import annotations
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING, cast

from ai_karen_engine.chat.ChatOrchestrator.utils import resolve_tenant_id
from ai_karen_engine.core.memory.curated_recall import (
    DEFAULT_CURATED_MEMORY_CLASSES,
)

if TYPE_CHECKING:
    from ai_karen_engine.chat.ChatOrchestrator.models import ChatRequest, ProcessingContext, ProcessingResult
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    Base = object

logger = logging.getLogger(__name__)


def _coerce_curated_candidate(candidate: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(candidate, dict):
        return None
    content = str(candidate.get("content") or candidate.get("text") or "").strip()
    memory_class = str(candidate.get("memory_class") or "").strip()
    if not content or memory_class not in DEFAULT_CURATED_MEMORY_CLASSES:
        return None
    return {
        "content": content,
        "memory_class": memory_class,
        "importance": int(candidate.get("importance") or 7),
        "tags": list(candidate.get("tags") or []),
        "metadata": dict(candidate.get("metadata") or {}),
    }

class ChatMemoryMixin(Base):
    """Methods for memory writeback and persistence with full shard attribution."""

    async def _orchestrate_post_response_memory_writeback(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        result: ProcessingResult
    ) -> Dict[str, Any]:
        """
        Orchestrate transactional memory writeback with shard linking (attribution).
        Memory writes only occur AFTER successful response generation.
        """
        from ai_karen_engine.chat.dependencies import get_memory_service
        from services.memory.unified_memory_service import ContextHit
        
        # Transactional guard: Only write back if response generation succeeded
        if not result.success or not result.response or not request.user_id:
            logger.debug(f"Skipping memory writeback for {context.correlation_id}: response not successful")
            return {"queued": False, "linked_shards": 0, "reason": "response_not_successful"}

        if bool((request.metadata or {}).get("skip_memory_writeback")):
            logger.debug(
                "Skipping memory writeback for %s: canonical Stage 1 runtime requested",
                context.correlation_id,
            )
            return {"queued": False, "linked_shards": 0, "reason": "stage1_runtime_skip"}

        try:
            memory_service = get_memory_service()
            if memory_service is None or not hasattr(memory_service, "queue_interaction_writeback"):
                logger.warning(f"Memory service not available for writeback: {context.correlation_id}")
                return {"queued": False, "linked_shards": 0, "reason": "memory_service_unavailable"}

            # Step 1: Normalize context hits from retrieved memories (Attribution)
            from services.memory.internal.memory_writeback import InteractionType
            
            normalized_hits: List[ContextHit] = []
            raw_memories = result.context.get("memories", []) if isinstance(result.context, dict) else []
            
            for item in raw_memories:
                if not isinstance(item, dict):
                    continue
                memory_id = str(item.get("id") or "").strip()
                text = str(item.get("content") or "").strip()
                if not memory_id or not text:
                    continue
                
                # Handle timestamp parsing
                created_at_raw = item.get("created_at")
                try:
                    created_at = datetime.fromisoformat(str(created_at_raw)) if created_at_raw else datetime.utcnow()
                except Exception:
                    created_at = datetime.utcnow()
                
                normalized_hits.append(
                    ContextHit(
                        id=memory_id,
                        text=text,
                        preview=str(text)[:200],
                        score=float(item.get("combined_score") or item.get("similarity_score") or 0.0),
                        tags=list((item.get("metadata", {}) or {}).get("tags", [])),
                        meta=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
                        importance=int((item.get("metadata", {}) or {}).get("importance", 5)),
                        decay_tier=str((item.get("metadata", {}) or {}).get("decay_tier", "short")),
                        created_at=created_at,
                        user_id=request.user_id,
                        org_id=str(context.metadata.get("org_id")) if context.metadata.get("org_id") else None,
                    )
                )

            # Step 2: Link response to source memory shards
            shard_links = []
            if normalized_hits and hasattr(memory_service, "link_response_to_shards"):
                shard_links = await memory_service.link_response_to_shards(
                    response_id=context.correlation_id,
                    response_content=result.response,
                    source_context_hits=normalized_hits,
                    user_id=request.user_id,
                    org_id=str(context.metadata.get("org_id")) if context.metadata.get("org_id") else None,
                    correlation_id=context.correlation_id,
                )

            # Stage 3: only explicit curated artifacts are promotable.
            raw_candidates = []
            for source in (
                (request.metadata or {}).get("curated_writeback_candidates"),
                result.structured_content.get("curated_writeback_candidates"),
                result.context.get("curated_writeback_candidates")
                if isinstance(result.context, dict)
                else None,
            ):
                if isinstance(source, list):
                    raw_candidates.extend(source)

            curated_candidates = [
                candidate
                for candidate in (
                    _coerce_curated_candidate(candidate)
                    for candidate in raw_candidates
                )
                if candidate is not None
            ]

            if not curated_candidates:
                return {
                    "queued": False,
                    "linked_shards": len(shard_links),
                    "normalized_hits": len(normalized_hits),
                    "reason": "no_curated_artifacts",
                }

            writeback_ids: List[str] = []
            for candidate in curated_candidates:
                tags = ["chat", "response", "curated_memory", candidate["memory_class"]]
                tags.extend(candidate["tags"])
                writeback_id = await memory_service.queue_interaction_writeback(
                    content=candidate["content"],
                    interaction_type=InteractionType.COPILOT_RESPONSE,
                    user_id=request.user_id,
                    org_id=str(context.metadata.get("org_id")) if context.metadata.get("org_id") else None,
                    session_id=request.session_id,
                    source_shards=shard_links,
                    tags=tags,
                    importance=max(1, min(10, candidate["importance"])),
                    metadata={
                        "conversation_id": request.conversation_id,
                        "user_message": request.message[:1000],
                        "llm": result.llm_metadata or {},
                        "surface": "chat_orchestrator",
                        "orchestrated_by": "ChatOrchestrator",
                        "curation_eligible": not result.used_fallback and result.success,
                        "curated": True,
                        "memory_class": candidate["memory_class"],
                        **candidate["metadata"],
                    },
                    correlation_id=context.correlation_id,
                )
                if writeback_id:
                    writeback_ids.append(str(writeback_id))

            return {
                "queued": bool(writeback_ids),
                "linked_shards": len(shard_links),
                "writeback_id": writeback_ids[0] if writeback_ids else None,
                "writeback_ids": writeback_ids,
                "curated_candidates": len(curated_candidates),
                "normalized_hits": len(normalized_hits)
            }
        except Exception as exc:
            logger.error(f"Memory writeback orchestration failed for {context.correlation_id}: {exc}")
            return {"queued": False, "linked_shards": 0, "error": str(exc), "reason": "writeback_exception"}
