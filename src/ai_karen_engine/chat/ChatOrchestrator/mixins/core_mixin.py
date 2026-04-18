from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime
from contextlib import suppress
from types import SimpleNamespace
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Union,
    AsyncIterator,
    cast,
    TYPE_CHECKING,
)

# Configure logger for this module
logger = logging.getLogger(__name__)


def _compact_session_turn(role: str, content: str, limit: int = 280) -> Dict[str, str]:
    return {
        "role": role,
        "content": str(content or "").strip()[:limit],
    }


# Optional hooks import with fallback
# Optional hooks import with fallback
try:
    from ai_karen_engine.hooks import (
        get_hook_manager,
        HookTypes,
        HookContext,
        HookExecutionSummary,
    )

    HOOKS_AVAILABLE = True
except ImportError:
    HOOKS_AVAILABLE = False

    class _HookTypesFallback:
        PRE_MESSAGE = "pre_message"
        MESSAGE_PROCESSED = "message_processed"
        POST_MESSAGE = "post_message"
        MESSAGE_FAILED = "message_failed"

    class _HookContextFallback:
        def __init__(
            self,
            hook_type: str,
            data: Dict[str, Any],
            user_context=None,
            metadata=None,
            timestamp=None,
        ):
            self.hook_type = hook_type
            self.data = data
            self.user_context = user_context or {}
            self.metadata = metadata or {}
            self.timestamp = timestamp or datetime.utcnow()

    class _HookExecutionSummaryFallback:
        def __init__(
            self,
            hook_type: str = "",
            total_hooks: int = 0,
            successful_hooks: int = 0,
            failed_hooks: int = 0,
            total_execution_time_ms: float = 0.0,
            results: Optional[list] = None,
            **kwargs,
        ):
            self.hook_type = hook_type
            self.total_hooks = total_hooks
            self.successful_hooks = successful_hooks
            self.failed_hooks = failed_hooks
            self.total_execution_time_ms = total_execution_time_ms
            self.results = results or []

    def _get_hook_manager_fallback() -> Optional[HookManager]:
        return None

    HookTypes = _HookTypesFallback  # type: ignore
    HookContext = _HookContextFallback  # type: ignore
    HookExecutionSummary = _HookExecutionSummaryFallback  # type: ignore
    get_hook_manager = _get_hook_manager_fallback  # type: ignore

# Type checking models and services
if TYPE_CHECKING:
    from ai_karen_engine.hooks.hook_manager import HookManager
    from ..models import (
        ProcessingStatus,
        ErrorType,
        ChatRequest,
        ProcessingResult,
        ChatResponse,
        ChatStreamChunk,
        ProcessingContext,
    )
else:
    from ..models import (
        ProcessingStatus,
        ErrorType,
        ChatRequest,
        ProcessingResult,
        ChatResponse,
        ChatStreamChunk,
        ProcessingContext,
    )

from ai_karen_engine.memory.nlp_service_manager import nlp_service_manager
from ai_karen_engine.models.shared_types import MessageRole
from ai_karen_engine.services.response_formatting_engine import (
    FormattingContext,
    DisplayContext,
    AccessibilityLevel,
)
from ai_karen_engine.services.response_policy_enforcer import ResponsePolicyEnforcer

if TYPE_CHECKING:
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol

    Base = ChatOrchestratorProtocol
else:
    Base = object


class ChatCoreMixin(Base):
    """Main message processing logic for ChatOrchestrator."""

    _INTERNAL_ANALYSIS_PREFIX_MARKERS = (
        "since the user has greeted again without a specific new request",
        "this is not a complete meaningful response",
    )

    _INTERNAL_ANALYSIS_LINE_PATTERNS = (
        r"^\s*in summary:\s*$",
        r"^\s*let'?s see if we can make sure the chat response is complete.*$",
        r"^\s*i(?:'|\u2019)ll acknowledge their greeting and be ready to assist.*$",
    )

    @staticmethod
    def _is_low_information_response_text(content: str) -> bool:
        text = str(content or "").strip()
        if not text:
            return True
        if len(text) == 1 and not text.isalnum():
            return True
        punctuation_only_chars = set(".-_=`'\"!?,:;()[]{}|/\\ \n\t")
        return all(ch in punctuation_only_chars for ch in text)

    @staticmethod
    def _serialize_format_model(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if hasattr(value, "model_dump"):
            try:
                return dict(value.model_dump())
            except Exception:
                return {}
        if hasattr(value, "dict"):
            try:
                return dict(value.dict())
            except Exception:
                return {}
        return {}

    @classmethod
    def _strip_internal_analysis_leakage(cls, content: str) -> str:
        """Remove known internal-analysis scaffold text from model-visible output."""
        cleaned = str(content or "").replace("\r\n", "\n")
        lowered = cleaned.lower()

        for marker in cls._INTERNAL_ANALYSIS_PREFIX_MARKERS:
            index = lowered.find(marker)
            if index >= 0:
                cleaned = cleaned[:index]
                lowered = cleaned.lower()

        for pattern in cls._INTERNAL_ANALYSIS_LINE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

        cleaned = re.sub(r"^\s*=+\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    async def _format_response_with_engine(
        self,
        content: str,
        turn_context: Any,
    ) -> tuple[str, Dict[str, Any]]:
        """Format assistant content with the formatting engine."""
        raw_content = str(content or "")
        if not raw_content.strip():
            return raw_content, {}

        raw_content = self._strip_internal_analysis_leakage(raw_content)
        if not raw_content.strip():
            return "I'm here and ready to help. What would you like to work on?", {}

        formatting_engine = getattr(self, "formatting_engine", None)
        if formatting_engine is None:
            return raw_content, {}

        try:
            policy_payload: Dict[str, Any] = {}
            policy_enforcer = getattr(self, "response_policy_enforcer", None)
            if policy_enforcer is None:
                policy_enforcer = ResponsePolicyEnforcer()
                setattr(self, "response_policy_enforcer", policy_enforcer)

            user_prompt = str(getattr(turn_context, "message", "") or "").strip()
            policy_result = await policy_enforcer.enforce(
                user_prompt=user_prompt,
                content=raw_content,
                regenerate=None,
            )
            raw_content = self._strip_internal_analysis_leakage(policy_result.content)
            if not raw_content.strip():
                raw_content = "I'm here and ready to help. What would you like to work on?"
            policy_payload = dict(policy_result.metadata or {})

            if hasattr(self, "_build_formatting_context"):
                formatting_context = self._build_formatting_context(  # type: ignore[attr-defined]
                    turn_context,
                    content_length=len(raw_content),
                )
            else:
                formatting_context = FormattingContext(
                    display_context=DisplayContext.DESKTOP,
                    accessibility_level=AccessibilityLevel.BASIC,
                    content_length=len(raw_content),
                )

            formatting_context.content_length = len(raw_content)
            formatted = await formatting_engine.format_response(  # type: ignore[attr-defined]
                content=raw_content,
                context=formatting_context,
            )

            sections = [
                self._serialize_format_model(section) for section in formatted.sections
            ]
            navigation_aids = [
                self._serialize_format_model(nav) for nav in formatted.navigation_aids
            ]
            formatting_payload = {
                "render_type": formatted.format_type.value,
                "formatted": True,
                "response_policy": policy_payload,
                "formatting": {
                    "format_type": formatted.format_type.value,
                    "sections": sections,
                    "navigation_aids": navigation_aids,
                    "accessibility_features": dict(
                        formatted.accessibility_features or {}
                    ),
                    "estimated_reading_time": formatted.estimated_reading_time,
                    "formatter_metadata": dict(formatted.metadata or {}),
                },
            }
            return formatted.content, formatting_payload
        except Exception as exc:
            logger.warning(
                "formatting failed for response; falling back to raw content: %s",
                exc,
            )
            return raw_content, {}

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        """Canonical non-streaming chat lifecycle with durable persistence."""
        if request.stream or request.streaming:
            raise ValueError("handle_chat only supports non-streaming chat requests")

        user_message_record = await self._persist_user_message(request)
        conversation_state = await self._resolve_conversation_state(
            request, user_message_record
        )
        working_context = await self._build_working_context(request, conversation_state)
        execution_path = await self._select_execution_path(request, working_context)
        generation_result = await self._execute_generation(
            request, working_context, execution_path
        )
        finalized = await self._finalize_response(
            request=request,
            generation_result=generation_result,
            execution_path=execution_path,
            working_context=working_context,
            user_message_record=user_message_record,
        )
        persisted = await self._persist_assistant_message(request, finalized)
        await self._post_response_writeback(request, persisted, working_context)
        await self._emit_chat_telemetry(request, persisted, working_context)
        return persisted

    async def handle_chat_stream(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Canonical streaming chat lifecycle with durable persistence."""
        if not (request.stream or request.streaming):
            raise ValueError("handle_chat_stream requires a streaming chat request")

        user_message_record = await self._persist_user_message(request)
        conversation_state = await self._resolve_conversation_state(
            request, user_message_record
        )
        working_context = await self._build_working_context(request, conversation_state)
        execution_path = await self._select_execution_path(request, working_context)
        raw_stream = await self.process_message(request)
        if not hasattr(raw_stream, "__aiter__"):
            raise RuntimeError(
                "Non-streaming result returned during streaming Stage 1 execution"
            )

        async def canonical_stream() -> AsyncGenerator[ChatStreamChunk, None]:
            collected_response = ""
            final_chunk_metadata: Dict[str, Any] = {}
            stream_failed = False

            async for chunk in cast(AsyncIterator[ChatStreamChunk], raw_stream):
                chunk_metadata = dict(chunk.metadata or {})
                if chunk.type == "metadata":
                    chunk_metadata.setdefault("request_id", request.request_id)
                    chunk_metadata.setdefault(
                        "conversation_id", request.conversation_id
                    )
                    chunk_metadata.setdefault("execution_path", execution_path)
                    yield ChatStreamChunk(
                        type=chunk.type,
                        content=chunk.content,
                        correlation_id=request.correlation_id,
                        metadata=chunk_metadata,
                    )
                    continue

                if chunk.type == "content":
                    collected_response += chunk.content or ""
                    yield ChatStreamChunk(
                        type=chunk.type,
                        content=chunk.content,
                        correlation_id=request.correlation_id,
                        metadata=chunk_metadata,
                    )
                    continue

                if chunk.type == "error":
                    stream_failed = True
                    yield ChatStreamChunk(
                        type=chunk.type,
                        content=chunk.content,
                        correlation_id=request.correlation_id,
                        metadata=chunk_metadata,
                    )
                    continue

                if chunk.type == "complete":
                    final_chunk_metadata = chunk_metadata
                    continue

                yield ChatStreamChunk(
                    type=chunk.type,
                    content=chunk.content,
                    correlation_id=request.correlation_id,
                    metadata=chunk_metadata,
                )

            if stream_failed or not collected_response.strip():
                return

            interim_response = ChatResponse(
                request_id=request.request_id,
                response=collected_response,
                correlation_id=request.correlation_id,
                conversation_id=request.conversation_id,
                assistant_message_id=None,
                processing_time=float(
                    final_chunk_metadata.get("processing_time") or 0.0
                ),
                status=ProcessingStatus.COMPLETED,
                used_fallback=bool(final_chunk_metadata.get("used_fallback")),
                context_used=bool(working_context.get("recent_messages")),
                execution_path=execution_path,
                metadata={
                    "streaming": True,
                    "retry_count": final_chunk_metadata.get("retry_count", 0),
                    "memory_writeback": final_chunk_metadata.get("memory_writeback"),
                },
                error=None,
                error_type=None,
            )
            finalized = await self._finalize_response(
                request=request,
                generation_result=interim_response,
                execution_path=execution_path,
                working_context=working_context,
                user_message_record=user_message_record,
            )
            persisted = await self._persist_assistant_message(request, finalized)
            await self._post_response_writeback(request, persisted, working_context)
            await self._emit_chat_telemetry(request, persisted, working_context)

            completion_metadata = dict(final_chunk_metadata)
            completion_metadata.update(
                {
                    "formatted_content": persisted.response,
                    "request_id": persisted.request_id,
                    "conversation_id": persisted.conversation_id,
                    "assistant_message_id": persisted.assistant_message_id,
                    "execution_path": persisted.execution_path,
                    "status": persisted.status.value
                    if hasattr(persisted.status, "value")
                    else str(persisted.status),
                    "telemetry": persisted.telemetry,
                    "persistence": (persisted.metadata or {}).get("persistence", {}),
                    "writeback": (persisted.metadata or {}).get("writeback", {}),
                    "working_context": (persisted.metadata or {}).get(
                        "working_context", {}
                    ),
                    "render_type": (persisted.metadata or {}).get("render_type"),
                    "formatted": (persisted.metadata or {}).get("formatted", False),
                    "formatting": (persisted.metadata or {}).get("formatting", {}),
                    "canonical_runtime": request.metadata.get("canonical_runtime", {}),
                }
            )
            yield ChatStreamChunk(
                type="complete",
                content=persisted.response,
                correlation_id=request.correlation_id,
                metadata=completion_metadata,
            )

        return canonical_stream()

    async def _persist_user_message(self, request: ChatRequest) -> Dict[str, Any]:
        """Persist the user turn before any generation occurs."""
        if self.conversation_manager is None:
            raise RuntimeError(
                "Conversation manager is unavailable for durable user message persistence"
            )
        if not hasattr(self.conversation_manager, "create_user_message"):
            raise RuntimeError(
                "Conversation manager does not implement create_user_message"
            )
        return await self.conversation_manager.create_user_message(request)

    async def _resolve_conversation_state(
        self,
        request: ChatRequest,
        user_message_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve the current durable conversation state from Postgres."""
        if self.conversation_manager is None:
            return {"user_message": user_message_record, "recent_messages": []}

        recent_messages: List[Dict[str, Any]] = []
        if hasattr(self.conversation_manager, "load_recent_messages"):
            recent_messages = await self.conversation_manager.load_recent_messages(
                tenant_id=request.tenant_id or request.org_id or "default",
                conversation_id=request.conversation_id,
                limit=20,
            )

        return {
            "conversation_id": request.conversation_id,
            "user_message": user_message_record,
            "recent_messages": recent_messages,
        }

    async def _build_working_context(
        self,
        request: ChatRequest,
        conversation_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assemble the Stage 2 working context from durable history plus Redis session state."""
        session_scope_id = request.session_id or request.conversation_id
        recent_messages = list(conversation_state.get("recent_messages") or [])
        persisted_user_id = str(
            (conversation_state.get("user_message") or {}).get("id") or ""
        ).strip()
        if persisted_user_id:
            recent_messages = [
                item
                for item in recent_messages
                if str(item.get("id") or "").strip() != persisted_user_id
            ]

        session_state: Dict[str, Any] = {}
        session_state_status = "unavailable"
        session_state_manager = getattr(self, "session_state_manager", None)
        if session_state_manager is not None and session_scope_id:
            try:
                session_state = await session_state_manager.get_session_state(
                    tenant_id=request.tenant_id or request.org_id or "default",
                    user_id=request.user_id,
                    session_id=session_scope_id,
                )
                session_state_status = "loaded" if session_state else "empty"
            except Exception as exc:
                logger.warning(
                    "Stage 2 session state load failed for %s: %s",
                    request.correlation_id,
                    exc,
                )
                session_state = {}
                session_state_status = "error"

        existing_request_context = dict(request.metadata.get("request_context") or {})
        compact_summary = (
            str(session_state.get("compact_summary") or "").strip() or None
        )
        recalled_items: List[Dict[str, Any]] = list(
            existing_request_context.get("recalled_items") or []
        )
        user_facts: List[Dict[str, Any]] = list(
            existing_request_context.get("user_facts") or []
        )
        project_facts: List[Dict[str, Any]] = list(
            existing_request_context.get("project_facts") or []
        )
        episodic_items: List[Dict[str, Any]] = list(
            existing_request_context.get("episodic_items") or []
        )
        semantic_long_term_items: List[Dict[str, Any]] = list(
            existing_request_context.get("semantic_long_term_items") or []
        )
        curated_recall_status = (
            "prefilled"
            if (
                recalled_items
                or user_facts
                or project_facts
                or episodic_items
                or semantic_long_term_items
            )
            else "unavailable"
        )
        if request.include_context and getattr(self, "memory_processor", None):
            try:
                parsed_message = await nlp_service_manager.parse_message(
                    request.message
                )
                embeddings = await nlp_service_manager.get_embeddings(request.message)
                raw_context = await self._retrieve_context(
                    embeddings,
                    parsed_message,
                    request.user_id,
                    request.conversation_id,
                )
                recalled_items = list(
                    raw_context.get("recalled_items")
                    or raw_context.get("memories")
                    or []
                )
                user_facts = list(raw_context.get("user_facts") or [])
                project_facts = list(raw_context.get("project_facts") or [])
                episodic_items = list(raw_context.get("episodic_items") or [])
                semantic_long_term_items = list(
                    raw_context.get("semantic_long_term_items") or []
                )
                curated_recall_status = "loaded" if recalled_items else "empty"
            except Exception as exc:
                logger.warning(
                    "Stage 4 canonical recall build failed for %s: %s",
                    request.correlation_id,
                    exc,
                )
                curated_recall_status = "error"

        request_context = existing_request_context
        request_context["recent_messages"] = recent_messages
        request_context["session_state"] = session_state
        request_context["recalled_items"] = recalled_items
        request_context["user_facts"] = user_facts
        request_context["project_facts"] = project_facts
        request_context["episodic_items"] = episodic_items
        request_context["semantic_long_term_items"] = semantic_long_term_items
        if compact_summary:
            request_context["compact_summary"] = compact_summary
        else:
            request_context.pop("compact_summary", None)
        request.metadata["request_context"] = request_context
        request.metadata["canonical_runtime"] = {
            "stage": "stage2",
            "recent_message_count": len(recent_messages),
            "persistence_backend": "postgres",
            "session_state_backend": "redis",
            "session_state_status": session_state_status,
            "session_scope_id": session_scope_id,
            "session_turn_count": len(list(session_state.get("recent_turns") or []))
            if isinstance(session_state, dict)
            else 0,
            "compact_summary_present": bool(compact_summary),
            "curated_recall_status": curated_recall_status,
            "recalled_item_count": len(recalled_items),
            "user_fact_count": len(user_facts),
            "project_fact_count": len(project_facts),
            "episodic_item_count": len(episodic_items),
            "semantic_long_term_count": len(semantic_long_term_items),
        }
        request.metadata.setdefault("skip_memory_writeback", True)

        return {
            "recent_messages": recent_messages,
            "session_state": session_state,
            "recalled_items": recalled_items,
            "user_facts": user_facts,
            "project_facts": project_facts,
            "episodic_items": episodic_items,
            "semantic_long_term_items": semantic_long_term_items,
            "system_context": {"mode": "standard_chat"},
            "compact_summary": compact_summary,
        }

    async def _select_execution_path(
        self,
        request: ChatRequest,
        working_context: Dict[str, Any],
    ) -> str:
        """Select the Stage 1 execution path."""
        return "direct_llm"

    async def _execute_generation(
        self,
        request: ChatRequest,
        working_context: Dict[str, Any],
        execution_path: str,
    ) -> ChatResponse:
        """Execute generation through the existing orchestrator path."""
        response = await self.process_message(request)
        if not isinstance(response, ChatResponse):
            raise RuntimeError(
                "Streaming result returned during non-streaming Stage 1 execution"
            )
        return response

    async def _finalize_response(
        self,
        request: ChatRequest,
        generation_result: ChatResponse,
        execution_path: str,
        working_context: Dict[str, Any],
        user_message_record: Dict[str, Any],
    ) -> ChatResponse:
        """Finalize response metadata before assistant persistence."""
        metadata = dict(generation_result.metadata or {})
        formatting_payload: Dict[str, Any] = {}
        llm_metadata = dict(metadata.get("llm") or {})
        cached_output_formatting = llm_metadata.get("output_formatting")
        if (
            isinstance(cached_output_formatting, dict)
            and cached_output_formatting.get("formatted") is True
        ):
            formatting_payload = dict(cached_output_formatting)
            generation_result.response = str(
                generation_result.response or ""
            )
        else:
            formatted_content, formatting_payload = (
                await self._format_response_with_engine(
                    generation_result.response,
                    request,
                )
            )
            generation_result.response = formatted_content

        if formatting_payload:
            metadata.update(formatting_payload)
            llm_block = dict(metadata.get("llm") or {})
            llm_block["output_formatting"] = formatting_payload
            metadata["llm"] = llm_block
        metadata["execution_path"] = execution_path
        metadata["canonical_runtime"] = dict(
            request.metadata.get("canonical_runtime") or {}
        )
        metadata["working_context"] = {
            "recent_messages": len(working_context.get("recent_messages") or []),
            "recalled_items": len(working_context.get("recalled_items") or []),
            "user_facts": len(working_context.get("user_facts") or []),
            "project_facts": len(working_context.get("project_facts") or []),
            "episodic_items": len(working_context.get("episodic_items") or []),
            "semantic_long_term_items": len(
                working_context.get("semantic_long_term_items") or []
            ),
            "session_turns": len(
                list(
                    (working_context.get("session_state") or {}).get("recent_turns")
                    or []
                )
            ),
            "session_summary_present": bool(working_context.get("compact_summary")),
        }
        memory_classification = dict(
            (generation_result.structured_content or {}).get("memory_classification")
            or {}
        )
        if memory_classification:
            metadata["working_context"]["memory_classification"] = memory_classification
        metadata["persistence"] = {
            "canonical_store": "postgres",
            "user_message_id": user_message_record.get("id"),
            "assistant_message_id": None,
            "assistant_persisted": False,
        }

        telemetry = dict(generation_result.telemetry or {})
        telemetry.update(
            {
                "request_id": request.request_id,
                "conversation_id": request.conversation_id,
                "execution_path": execution_path,
            }
        )

        generation_result.request_id = request.request_id
        generation_result.correlation_id = (
            request.correlation_id or generation_result.correlation_id
        )
        generation_result.conversation_id = request.conversation_id
        generation_result.execution_path = execution_path
        generation_result.metadata = metadata
        generation_result.telemetry = telemetry

        if (
            generation_result.status == ProcessingStatus.COMPLETED
            and generation_result.used_fallback
        ):
            generation_result.status = ProcessingStatus.DEGRADED

        return generation_result

    async def _persist_assistant_message(
        self,
        request: ChatRequest,
        response: ChatResponse,
    ) -> ChatResponse:
        """Persist the finalized assistant response exactly once."""
        if self.conversation_manager is None:
            return response
        if not hasattr(self.conversation_manager, "create_assistant_message"):
            return response

        assistant_record = await self.conversation_manager.create_assistant_message(
            request, response
        )
        metadata = dict(response.metadata or {})
        persistence = dict(metadata.get("persistence") or {})
        persistence["assistant_message_id"] = assistant_record.get("id")
        persistence["assistant_persisted"] = bool(assistant_record)
        persistence["persisted_at"] = assistant_record.get("created_at")
        metadata["persistence"] = persistence

        response.assistant_message_id = assistant_record.get("id")
        response.metadata = metadata
        return response

    async def _post_response_writeback(
        self,
        request: ChatRequest,
        response: ChatResponse,
        working_context: Dict[str, Any],
    ) -> None:
        """Write Redis continuity and Stage 4 curated promotion from the canonical spine."""
        metadata = dict(response.metadata or {})
        session_writeback: Dict[str, Any] = {
            "saved": False,
            "backend": "redis",
            "reason": "session_state_manager_unavailable",
        }

        session_scope_id = request.session_id or request.conversation_id
        session_state_manager = getattr(self, "session_state_manager", None)
        if session_state_manager is not None and session_scope_id:
            recent_messages = list(working_context.get("recent_messages") or [])
            prior_session_state = dict(working_context.get("session_state") or {})
            recent_turns = []
            prior_turns = list(prior_session_state.get("recent_turns") or [])
            for item in prior_turns[-4:]:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role") or "").strip().lower()
                content = str(item.get("content") or "").strip()
                if role not in {"user", "assistant"} or not content:
                    continue
                recent_turns.append(_compact_session_turn(role, content))
            for item in recent_messages[-4:]:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role") or "").strip().lower()
                content = str(item.get("content") or "").strip()
                if role not in {"user", "assistant"} or not content:
                    continue
                recent_turns.append(_compact_session_turn(role, content))
            recent_turns.extend(
                [
                    _compact_session_turn("user", request.message),
                    _compact_session_turn("assistant", response.response),
                ]
            )
            recent_turns = recent_turns[-6:]
            compact_summary = " | ".join(
                f"{turn['role']}: {turn['content'][:120]}" for turn in recent_turns[-4:]
            )[:1000]
            session_state = {
                "conversation_id": request.conversation_id,
                "last_user_message": str(request.message or "").strip()[:280],
                "last_assistant_response": str(response.response or "").strip()[:280],
                "recent_turns": recent_turns,
                "compact_summary": compact_summary,
            }
            try:
                await session_state_manager.put_session_state(
                    tenant_id=request.tenant_id or request.org_id or "default",
                    user_id=request.user_id,
                    session_id=session_scope_id,
                    state=session_state,
                )
                session_writeback = {
                    "saved": True,
                    "backend": "redis",
                    "session_scope_id": session_scope_id,
                    "recent_turn_count": len(recent_turns),
                }
            except Exception as exc:
                logger.warning(
                    "Stage 2 session state writeback failed for %s: %s",
                    request.correlation_id,
                    exc,
                )
                session_writeback = {
                    "saved": False,
                    "backend": "redis",
                    "reason": "session_state_writeback_error",
                    "error": str(exc),
                }

        stage4_writeback: Dict[str, Any] = {}
        structured_content = dict(response.structured_content or {})
        has_stage4_payload = bool(
            structured_content.get("memory_classification")
            or structured_content.get("curated_writeback_candidates")
        )
        if has_stage4_payload and hasattr(
            self, "_orchestrate_post_response_memory_writeback"
        ):
            request_context = dict(request.metadata.get("request_context") or {})
            writeback_context_payload = dict(
                request.metadata.get("integrated_context") or {}
            )
            if not isinstance(writeback_context_payload.get("memories"), list):
                writeback_context_payload["memories"] = list(
                    request_context.get("recalled_items") or []
                )
            writeback_context_payload.setdefault(
                "user_facts", list(request_context.get("user_facts") or [])
            )
            writeback_context_payload.setdefault(
                "project_facts", list(request_context.get("project_facts") or [])
            )
            writeback_context_payload.setdefault(
                "episodic_items", list(request_context.get("episodic_items") or [])
            )
            writeback_context_payload.setdefault(
                "semantic_long_term_items",
                list(request_context.get("semantic_long_term_items") or []),
            )
            writeback_request = request.model_copy(deep=True)
            writeback_request.metadata = dict(writeback_request.metadata or {})
            writeback_request.metadata.pop("skip_memory_writeback", None)
            writeback_context = ProcessingContext(request=writeback_request)
            writeback_context.correlation_id = request.correlation_id
            if request.org_id and not writeback_context.metadata.get("org_id"):
                writeback_context.metadata["org_id"] = request.org_id
            writeback_result = ProcessingResult(
                success=response.status != ProcessingStatus.FAILED
                and bool(response.response),
                response=response.response,
                llm_metadata=dict(metadata.get("llm") or {}),
                processing_time=response.processing_time,
                used_fallback=response.used_fallback,
                structured_content=structured_content,
                actions=list(response.actions or []),
                context=writeback_context_payload,
                correlation_id=request.correlation_id,
            )
            try:
                stage4_writeback = (
                    await self._orchestrate_post_response_memory_writeback(
                        writeback_request,
                        writeback_context,
                        writeback_result,
                    )
                )
            except Exception as exc:
                logger.warning(
                    "Stage 4 canonical memory writeback failed for %s: %s",
                    request.correlation_id,
                    exc,
                )
                stage4_writeback = {
                    "queued": False,
                    "reason": "canonical_writeback_exception",
                    "error": str(exc),
                }

        metadata["memory_writeback"] = stage4_writeback
        metadata["writeback"] = {
            "memory_promotion": "queued"
            if stage4_writeback.get("queued")
            else "skipped",
            "reason": (
                stage4_writeback.get("reason")
                or (
                    "stage4_canonical_runtime"
                    if has_stage4_payload
                    else "stage2_canonical_runtime"
                )
            ),
            "memory_writeback": stage4_writeback,
            "session_state": session_writeback,
        }
        response.metadata = metadata

    async def _emit_chat_telemetry(
        self,
        request: ChatRequest,
        response: ChatResponse,
        working_context: Dict[str, Any],
    ) -> None:
        """Emit lightweight Stage 1 lifecycle telemetry."""
        telemetry = dict(response.telemetry or {})
        telemetry["lifecycle"] = {
            "request_id": request.request_id,
            "correlation_id": request.correlation_id,
            "conversation_id": request.conversation_id,
            "assistant_message_id": response.assistant_message_id,
            "status": response.status.value
            if hasattr(response.status, "value")
            else str(response.status),
        }
        response.telemetry = telemetry

    async def process_message(
        self, request: ChatRequest
    ) -> Union[ChatResponse, AsyncGenerator[ChatStreamChunk, None]]:
        """
        Process a chat message with full NLP integration and error handling.
        """
        context = ProcessingContext(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            session_id=request.session_id,
            metadata=request.metadata,
            request=request,
        )

        await self._register_context(context)
        self._total_requests += 1

        if request.stream:

            async def streaming_wrapper() -> AsyncGenerator[ChatStreamChunk, None]:
                task = asyncio.current_task()
                if task:
                    await self._register_task(context.correlation_id, task)
                try:
                    async for chunk in self._process_streaming(request, context):
                        if context.cancel_event.is_set():
                            context.status = ProcessingStatus.CANCELLED
                            context.cancelled = True
                            yield ChatStreamChunk(
                                type="error",
                                content="Generation cancelled",
                                correlation_id=context.correlation_id,
                                metadata={
                                    "error_type": ErrorType.REQUEST_CANCELLED.value
                                },
                            )
                            break
                        yield chunk
                except asyncio.CancelledError:
                    context.status = ProcessingStatus.CANCELLED
                    context.cancelled = True
                    yield ChatStreamChunk(
                        type="error",
                        content="Generation cancelled",
                        correlation_id=context.correlation_id,
                        metadata={"error_type": ErrorType.REQUEST_CANCELLED.value},
                    )
                finally:
                    await self._cleanup_context(context.correlation_id)

            return streaming_wrapper()

        task = asyncio.current_task()
        if task:
            await self._register_task(context.correlation_id, task)

        try:
            return await self._process_traditional(request, context)
        finally:
            await self._cleanup_context(context.correlation_id)

    async def _process_traditional(
        self, request: ChatRequest, context: ProcessingContext
    ) -> ChatResponse:
        """Process message with traditional request-response pattern."""
        context.processing_start = datetime.utcnow()
        context.status = ProcessingStatus.PROCESSING

        start_time = time.time()
        hook_manager: Any = get_hook_manager()

        pre_message_context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={
                "message": request.message,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id,
                "timestamp": context.request_timestamp.isoformat(),
                "correlation_id": context.correlation_id,
                "attachments": request.attachments,
                "metadata": request.metadata,
            },
            user_context={
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id,
            },
        )

        pre_hook_summary = (
            await self._trigger_hooks_with_timeout(hook_manager, pre_message_context)
            if HOOKS_AVAILABLE and hook_manager
            else HookExecutionSummary(
                hook_type="pre_message",
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )
        )

        result: Optional[ProcessingResult] = None
        processing_time: float = 0.0

        try:
            # Result can be a ProcessingResult or AsyncIterator depending on the model/provider
            result_or_gen = await self._process_with_retry(request, context)

            if isinstance(result_or_gen, ProcessingResult):
                result = result_or_gen
            elif hasattr(result_or_gen, "__aiter__"):
                # Pathological case: streaming iterator returned in non-streaming path
                # We collect it into a single response
                full_content = ""
                async for chunk in cast(AsyncIterator[str], result_or_gen):
                    full_content += chunk
                result = ProcessingResult(
                    success=True,
                    response=full_content,
                    correlation_id=context.correlation_id,
                    llm_metadata={"source": "sync_collection_fallback"},
                    processing_time=time.time() - start_time,
                )
            else:
                # It's a tuple (ai_response, llm_metadata, used_fallback)
                ai_response, llm_metadata, used_fallback = cast(
                    tuple[str, Dict[str, Any], bool], result_or_gen
                )
                result = ProcessingResult(
                    success=True,
                    response=ai_response,
                    llm_metadata=llm_metadata,
                    used_fallback=used_fallback,
                    correlation_id=context.correlation_id,
                    processing_time=time.time() - start_time,
                )

            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)

            if result and result.success:
                self._successful_requests += 1
                context.status = ProcessingStatus.COMPLETED

                memory_writeback = (
                    await self._orchestrate_post_response_memory_writeback(
                        request, context, result
                    )
                )

                message_processed_context = HookContext(
                    hook_type=HookTypes.MESSAGE_PROCESSED,
                    data={
                        "message": request.message,
                        "response": result.response,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        "correlation_id": context.correlation_id,
                        "processing_time": processing_time,
                        "parsed_message": result.parsed_message.__dict__
                        if result.parsed_message
                        else None,
                        "embeddings_count": len(result.embeddings)
                        if result.embeddings
                        else 0,
                        "context_used": bool(result.context),
                        "used_fallback": result.used_fallback,
                        "retry_count": context.retry_count,
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                    },
                )

                processed_hook_summary = (
                    await self._trigger_hooks_with_timeout(
                        hook_manager, message_processed_context
                    )
                    if HOOKS_AVAILABLE and hook_manager
                    else HookExecutionSummary(
                        hook_type="message_processed",
                        total_hooks=0,
                        successful_hooks=0,
                        failed_hooks=0,
                        total_execution_time_ms=0.0,
                        results=[],
                    )
                )

                metadata = {
                    "parsed_entities": len(result.parsed_message.entities)
                    if result.parsed_message
                    else 0,
                    "embedding_dimension": len(result.embeddings)
                    if result.embeddings
                    else 0,
                    "retry_count": context.retry_count,
                    "pre_hooks_executed": pre_hook_summary.successful_hooks,
                    "processed_hooks_executed": processed_hook_summary.successful_hooks,
                    **context.metadata,
                }

                if result.context:
                    metadata["context_summary"] = result.context.get(
                        "context_summary", "Context retrieved"
                    )
                    metadata["memories_used"] = len(result.context.get("memories", []))
                    metadata["retrieval_time"] = result.context.get(
                        "retrieval_time", 0.0
                    )
                    metadata["total_memories_considered"] = result.context.get(
                        "total_memories_considered", 0
                    )

                post_message_context = HookContext(
                    hook_type=HookTypes.POST_MESSAGE,
                    data={
                        "message": request.message,
                        "response": result.response,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        "correlation_id": context.correlation_id,
                        "processing_time": processing_time,
                        "metadata": metadata,
                        "hook_results": {
                            "pre_message": [
                                r.__dict__ for r in pre_hook_summary.results
                            ],
                            "message_processed": [
                                r.__dict__ for r in processed_hook_summary.results
                            ],
                        },
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                    },
                )

                post_hook_summary = (
                    await self._trigger_hooks_with_timeout(
                        hook_manager, post_message_context
                    )
                    if HOOKS_AVAILABLE and hook_manager
                    else HookExecutionSummary(
                        hook_type="post_message",
                        total_hooks=0,
                        successful_hooks=0,
                        failed_hooks=0,
                        total_execution_time_ms=0.0,
                        results=[],
                    )
                )

                metadata["post_hooks_executed"] = post_hook_summary.successful_hooks
                metadata["total_hooks_executed"] = (
                    pre_hook_summary.successful_hooks
                    + processed_hook_summary.successful_hooks
                    + post_hook_summary.successful_hooks
                )

                if result.llm_metadata:
                    metadata["llm"] = result.llm_metadata
                metadata["memory_writeback"] = memory_writeback

                return ChatResponse(
                    request_id=request.request_id,
                    response=result.response or "",
                    correlation_id=context.correlation_id,
                    conversation_id=request.conversation_id,
                    assistant_message_id=None,
                    processing_time=processing_time,
                    status=context.status,
                    used_fallback=result.used_fallback,
                    context_used=bool(result.context),
                    execution_path=None,
                    structured_content=result.structured_content or {},
                    actions=result.actions or [],
                    metadata=metadata,
                    error=result.error,
                    error_type=result.error_type,
                )
            else:
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED

                eff_res = (
                    result
                    if result
                    else ProcessingResult(
                        success=False,
                        error="Invalid response type",
                        error_type=ErrorType.UNKNOWN_ERROR,
                        correlation_id=context.correlation_id,
                    )
                )

                message_failed_context = HookContext(
                    hook_type=HookTypes.MESSAGE_FAILED,
                    data={
                        "message": request.message,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        "correlation_id": context.correlation_id,
                        "processing_time": processing_time,
                        "error": eff_res.error,
                        "error_type": eff_res.error_type.value
                        if eff_res.error_type
                        else "unknown",
                        "retry_count": context.retry_count,
                        "used_fallback": eff_res.used_fallback,
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                    },
                )

                failed_hook_summary = (
                    await self._trigger_hooks_with_timeout(
                        hook_manager, message_failed_context
                    )
                    if HOOKS_AVAILABLE and hook_manager
                    else HookExecutionSummary(
                        hook_type="message_failed",
                        total_hooks=0,
                        successful_hooks=0,
                        failed_hooks=0,
                        total_execution_time_ms=0.0,
                        results=[],
                    )
                )

                error_metadata = {
                    "error": eff_res.error,
                    "error_type": eff_res.error_type.value
                    if eff_res.error_type
                    else "unknown",
                    "retry_count": context.retry_count,
                    "pre_hooks_executed": pre_hook_summary.successful_hooks,
                    "failed_hooks_executed": failed_hook_summary.successful_hooks,
                }

                if eff_res.llm_metadata:
                    error_metadata["llm"] = eff_res.llm_metadata

            error_message = eff_res.error if eff_res.error else "Unknown error occurred"
            logger.error(
                f"Chat processing failed with error message: {error_message}",
                extra={
                    "correlation_id": context.correlation_id,
                    "error": error_message,
                },
            )
            return ChatResponse(
                request_id=request.request_id,
                response=f"I apologize, but I encountered an error processing your message: {error_message}",
                correlation_id=context.correlation_id,
                conversation_id=request.conversation_id,
                assistant_message_id=None,
                processing_time=processing_time,
                status=context.status,
                used_fallback=True,
                context_used=False,
                execution_path=None,
                metadata=error_metadata,
                error=error_message,
                error_type=eff_res.error_type,
            )

        except asyncio.CancelledError:
            context.status = ProcessingStatus.CANCELLED
            context.cancelled = True
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            self._failed_requests += 1
            context.status = ProcessingStatus.FAILED
            logger.error(f"Unexpected error in chat processing: {e}", exc_info=True)
            return ChatResponse(
                request_id=request.request_id,
                response="I apologize, but I encountered an unexpected error. Please try again.",
                correlation_id=context.correlation_id,
                conversation_id=request.conversation_id,
                assistant_message_id=None,
                processing_time=processing_time,
                status=ProcessingStatus.FAILED,
                used_fallback=True,
                context_used=False,
                execution_path=None,
                error=str(e),
                error_type=ErrorType.UNKNOWN_ERROR,
                metadata={"error": str(e)},
            )
        finally:
            context.processing_end = datetime.utcnow()

    async def _process_streaming(
        self, request: ChatRequest, context: ProcessingContext
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Process message with streaming response and intermediate status emissions."""
        start_time = time.time()
        context.processing_start = datetime.utcnow()
        context.status = ProcessingStatus.PROCESSING
        hook_manager: Any = get_hook_manager()

        yield ChatStreamChunk(
            type="metadata",
            content="",
            correlation_id=context.correlation_id,
            metadata={"status": "initializing"},
        )

        pre_message_context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={
                "message": request.message,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id,
                "timestamp": context.request_timestamp.isoformat(),
                "correlation_id": context.correlation_id,
                "attachments": request.attachments,
                "metadata": request.metadata,
                "streaming": True,
            },
            user_context={
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id,
            },
        )

        if HOOKS_AVAILABLE and hook_manager:
            pre_hook_summary = await hook_manager.trigger_hooks(pre_message_context)
        else:
            pre_hook_summary = HookExecutionSummary(
                hook_type="pre_message_streaming",
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )

        try:
            if context.cancel_event.is_set():
                raise asyncio.CancelledError()

            yield ChatStreamChunk(
                type="metadata",
                content="",
                correlation_id=context.correlation_id,
                metadata={
                    "status": "processing",
                    "user_id": context.user_id,
                    "conversation_id": context.conversation_id,
                    "pre_hooks_executed": pre_hook_summary.successful_hooks,
                },
            )

            yield ChatStreamChunk(
                type="metadata",
                content="",
                correlation_id=context.correlation_id,
                metadata={
                    "status": "extracting_context",
                    "detail": "Retrieving memories, context, and preparing the prompt...",
                },
            )

            result_or_gen = await self._process_with_retry(
                request, context, stream=True
            )

            if context.cancel_event.is_set():
                raise asyncio.CancelledError()

            if context.retry_count > 0:
                yield ChatStreamChunk(
                    type="metadata",
                    content="",
                    correlation_id=context.correlation_id,
                    metadata={"status": "retrying"},
                )

            yield ChatStreamChunk(
                type="metadata",
                content="",
                correlation_id=context.correlation_id,
                metadata={"status": "generating_response"},
            )

            result: Optional[ProcessingResult] = None
            full_response = ""

            # Handle AsyncIterator (standard streaming)
            if hasattr(result_or_gen, "__aiter__"):
                async for token in cast(AsyncIterator[str], result_or_gen):
                    if context.cancel_event.is_set():
                        break
                    full_response += token
                    yield ChatStreamChunk(
                        type="content",
                        content=token,
                        correlation_id=context.correlation_id,
                    )

                result = ProcessingResult(
                    success=True,
                    response=full_response,
                    correlation_id=context.correlation_id,
                    llm_metadata={"streaming": True},
                    processing_time=time.time() - start_time,
                )
                if self._is_low_information_response_text(full_response):
                    result = ProcessingResult(
                        success=False,
                        error="Provider returned low-information output",
                        error_type=ErrorType.AI_MODEL_ERROR,
                        correlation_id=context.correlation_id,
                        processing_time=time.time() - start_time,
                    )
            # Handle direct ProcessingResult (e.g. if streaming failed and returned a regular response)
            elif isinstance(result_or_gen, ProcessingResult):
                result = result_or_gen
                if result.success and result.response:
                    yield ChatStreamChunk(
                        type="content",
                        content=result.response,
                        correlation_id=context.correlation_id,
                    )

            if result and result.success and result.response:
                yield ChatStreamChunk(
                    type="metadata",
                    content="",
                    correlation_id=context.correlation_id,
                    metadata={"status": "post_processing"},
                )

                memory_writeback = (
                    await self._orchestrate_post_response_memory_writeback(
                        request, context, result
                    )
                )

                completion_metadata = {
                    "processing_time": result.processing_time,
                    "used_fallback": result.used_fallback,
                    "retry_count": context.retry_count,
                    "memory_writeback": memory_writeback,
                }

                yield ChatStreamChunk(
                    type="complete",
                    content="",
                    correlation_id=context.correlation_id,
                    metadata=completion_metadata,
                )
                self._successful_requests += 1
                context.status = ProcessingStatus.COMPLETED
            elif result:
                error_metadata = {
                    "error_type": result.error_type.value
                    if result.error_type
                    else "unknown",
                    "retry_count": context.retry_count,
                }
                yield ChatStreamChunk(
                    type="error",
                    content=result.error or "Processing failed",
                    correlation_id=context.correlation_id,
                    metadata=error_metadata,
                )
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED
            else:
                yield ChatStreamChunk(
                    type="error",
                    content="An unexpected error occurred during streaming.",
                    correlation_id=context.correlation_id,
                    metadata={"error_type": ErrorType.UNKNOWN_ERROR.value},
                )
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED

        except asyncio.CancelledError:
            context.status = ProcessingStatus.CANCELLED
            context.cancelled = True
            yield ChatStreamChunk(
                type="error",
                content="Generation cancelled",
                correlation_id=context.correlation_id,
                metadata={"error_type": ErrorType.REQUEST_CANCELLED.value},
            )
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield ChatStreamChunk(
                type="error",
                content=f"Streaming error: {str(e)}",
                correlation_id=context.correlation_id,
                metadata={"error_type": ErrorType.UNKNOWN_ERROR.value},
            )
            self._failed_requests += 1
            context.status = ProcessingStatus.FAILED
        finally:
            context.processing_end = datetime.utcnow()

    async def _process_with_retry(
        self, request: ChatRequest, context: ProcessingContext, stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Process message with retry logic and exponential backoff."""
        last_error = None
        last_error_type = ErrorType.UNKNOWN_ERROR

        for attempt in range(self.retry_config.max_attempts):
            context.retry_count = attempt
            if context.cancel_event.is_set():
                raise asyncio.CancelledError()

            if attempt > 0:
                context.status = ProcessingStatus.RETRYING
                self._retry_attempts += 1

                delay = (
                    min(
                        self.retry_config.initial_delay
                        * (self.retry_config.backoff_factor ** (attempt - 1)),
                        self.retry_config.max_delay,
                    )
                    if self.retry_config.exponential_backoff
                    else self.retry_config.initial_delay
                )
                await asyncio.sleep(delay)

            try:
                result = await self._process_message_core(
                    request, context, stream=stream
                )
                if stream and hasattr(result, "__aiter__"):
                    return cast(AsyncIterator[str], result)

                if isinstance(result, ProcessingResult) and result.success:
                    return result
                elif isinstance(result, ProcessingResult):
                    last_error = (
                        result.error if hasattr(result, "error") else "Unknown error"
                    )
                    last_error_type = result.error_type or ErrorType.UNKNOWN_ERROR
            except asyncio.CancelledError:
                context.status = ProcessingStatus.CANCELLED
                context.cancelled = True
                raise
            except asyncio.TimeoutError:
                last_error = f"Processing timeout after {self.timeout_seconds}s"
                last_error_type = ErrorType.TIMEOUT_ERROR
            except Exception as e:
                last_error = str(e)
                last_error_type = ErrorType.UNKNOWN_ERROR

        return ProcessingResult(
            success=False,
            error=last_error,
            error_type=last_error_type,
            correlation_id=context.correlation_id,
        )

    async def _process_message_core(
        self, request: ChatRequest, context: ProcessingContext, stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Core message processing with NLP integration."""
        start_time = time.time()
        try:
            return await asyncio.wait_for(
                self._process_message_internal(request, context, stream=stream),
                timeout=self.timeout_seconds,
            )
        except asyncio.CancelledError:
            return ProcessingResult(
                success=False,
                error="Processing cancelled",
                error_type=ErrorType.REQUEST_CANCELLED,
                processing_time=time.time() - start_time,
                correlation_id=context.correlation_id,
            )
        except asyncio.TimeoutError:
            return ProcessingResult(
                success=False,
                error=f"Processing timeout after {self.timeout_seconds}s",
                error_type=ErrorType.TIMEOUT_ERROR,
                processing_time=time.time() - start_time,
                correlation_id=context.correlation_id,
            )

    async def _process_message_internal(
        self, request: ChatRequest, context: ProcessingContext, stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Internal message processing with enhanced instruction processing and context integration."""
        start_time = time.time()
        parsed_message = None
        embeddings = None
        used_fallback = False

        if context.cancel_event.is_set():
            raise asyncio.CancelledError()

        try:
            try:
                parsed_message = await nlp_service_manager.parse_message(
                    request.message
                )
                if parsed_message.used_fallback:
                    used_fallback = True
                    self._fallback_usage += 1
            except Exception as e:
                return ProcessingResult(
                    success=False,
                    error=f"Message parsing failed: {str(e)}",
                    error_type=ErrorType.NLP_PARSING_ERROR,
                    processing_time=time.time() - start_time,
                    correlation_id=context.correlation_id,
                )

            try:
                from ai_karen_engine.chat.instruction_processor import (
                    InstructionContext,
                )

                instruction_context = InstructionContext(
                    user_id=request.user_id,
                    conversation_id=request.conversation_id,
                    session_id=request.session_id,
                    message_history=[request.message],
                    metadata=request.metadata,
                )
                extracted_instructions = (
                    await self.instruction_processor.extract_instructions(
                        request.message, instruction_context
                    )
                )
                if extracted_instructions:
                    await self.instruction_processor.store_instructions(
                        extracted_instructions, instruction_context
                    )
                active_instructions = (
                    await self.instruction_processor.get_active_instructions(
                        instruction_context
                    )
                )
            except Exception as e:
                active_instructions = []

            try:
                embeddings = await nlp_service_manager.get_embeddings(request.message)
            except Exception as e:
                return ProcessingResult(
                    success=False,
                    error=f"Embedding generation failed: {str(e)}",
                    error_type=ErrorType.EMBEDDING_ERROR,
                    processing_time=time.time() - start_time,
                    correlation_id=context.correlation_id,
                )

            extracted_memories = []
            if self.memory_processor:
                try:
                    extracted_memories = await self.memory_processor.extract_memories(
                        request.message,
                        parsed_message,
                        embeddings,
                        request.user_id,
                        request.conversation_id,
                    )
                except Exception:
                    extracted_memories = []

            attachment_context = {}
            if request.attachments and self.file_attachment_service:
                try:
                    attachment_context = await self._process_attachments(
                        request.attachments, request.user_id, request.conversation_id
                    )
                except Exception:
                    pass

            integrated_context = None
            if request.include_context:
                try:
                    raw_context = await self._retrieve_context(
                        embeddings,
                        parsed_message,
                        request.user_id,
                        request.conversation_id,
                    )
                    if attachment_context:
                        raw_context["attachments"] = attachment_context
                    if active_instructions:
                        raw_context["instructions"] = [
                            {
                                "type": inst.type.value,
                                "content": inst.content,
                                "priority": inst.priority.value,
                                "scope": inst.scope.value,
                                "confidence": inst.confidence,
                            }
                            for inst in active_instructions
                        ]
                    integrated_context = (
                        await self.context_integrator.integrate_context(
                            raw_context,
                            request.message,
                            request.user_id,
                            request.conversation_id,
                        )
                    )
                    context.metadata["integrated_context"] = (
                        integrated_context.to_dict() if integrated_context else {}
                    )
                except Exception:
                    pass
            elif active_instructions:
                context.metadata["integrated_context"] = {
                    "instructions": [
                        {
                            "type": inst.type.value,
                            "content": inst.content,
                            "priority": inst.priority.value,
                            "scope": inst.scope.value,
                            "confidence": inst.confidence,
                        }
                        for inst in active_instructions
                    ]
                }

            try:
                result = await self._generate_ai_response_enhanced(
                    request.message,
                    parsed_message,
                    embeddings,
                    integrated_context,
                    active_instructions,
                    context,
                    stream=stream,
                )

                if stream and isinstance(result, AsyncIterator):
                    return result

                res_tuple = cast(tuple[str, dict[str, Any], bool], result)
                ai_response, llm_metadata, llm_used_fallback = res_tuple
                generation_success = (
                    True  # LLM generation succeeded regardless of fallback usage
                )

                ai_response, formatting_payload = await self._format_response_with_engine(
                    ai_response,
                    request,
                )
                if formatting_payload:
                    llm_metadata["output_formatting"] = formatting_payload

                structured_content: Dict[str, Any] = {}
                if self.memory_processor and extracted_memories:
                    try:
                        structured_content.update(
                            self.memory_processor.build_stage4_writeback_payload(
                                request.message,
                                ai_response,
                                extracted_memories,
                                include_episodic_summary=not (
                                    used_fallback or llm_used_fallback
                                ),
                            )
                        )
                    except Exception:
                        pass

                synth_result = ProcessingResult(
                    success=generation_success,
                    response=ai_response,
                    parsed_message=parsed_message,
                    embeddings=embeddings,
                    context=integrated_context.to_dict() if integrated_context else {},
                    processing_time=time.time() - start_time,
                    used_fallback=used_fallback or llm_used_fallback,
                    correlation_id=context.correlation_id,
                    llm_metadata=llm_metadata,
                    structured_content=structured_content,
                )

                return synth_result

            except Exception as e:
                return ProcessingResult(
                    success=False,
                    error=f"AI response generation failed: {str(e)}",
                    error_type=ErrorType.AI_MODEL_ERROR,
                    processing_time=time.time() - start_time,
                    correlation_id=context.correlation_id,
                    llm_metadata={},
                )

        except asyncio.CancelledError:
            raise
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"Unexpected processing error: {str(e)}",
                error_type=ErrorType.UNKNOWN_ERROR,
                processing_time=time.time() - start_time,
                correlation_id=context.correlation_id,
            )

    async def cancel_processing(
        self,
        *,
        conversation_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> List[str]:
        """Cancel active processing contexts."""
        if not conversation_id and not correlation_id:
            raise ValueError(
                "Either conversation_id or correlation_id must be provided"
            )

        async with self._contexts_lock:
            snapshot = list(self._active_contexts.items())
        target_ids = [
            cid
            for cid, ctx in snapshot
            if (correlation_id and cid == correlation_id)
            or (conversation_id and ctx.conversation_id == conversation_id)
        ]

        cancelled = []
        for cid in target_ids:
            async with self._contexts_lock:
                ctx = self._active_contexts.get(cid)
            if not ctx:
                continue
            if not ctx.cancel_event.is_set():
                ctx.cancel_event.set()
                ctx.cancelled = True
                ctx.status = ProcessingStatus.CANCELLED
            async with self._tasks_lock:
                task = self._active_tasks.get(cid)
                if task and not task.done():
                    task.cancel()
            cancelled.append(cid)
        return cancelled

    async def _register_context(self, context: ProcessingContext) -> None:
        async with self._contexts_lock:
            self._active_contexts[context.correlation_id] = context

    async def _register_task(self, correlation_id: str, task: asyncio.Task) -> None:
        async with self._tasks_lock:
            self._active_tasks[correlation_id] = task

    async def _cleanup_context(self, correlation_id: str) -> None:
        async with self._tasks_lock:
            task = self._active_tasks.pop(correlation_id, None)
        current_task = asyncio.current_task()
        if task and task is not current_task and not task.done():
            with suppress(asyncio.CancelledError):
                task.cancel()
        async with self._contexts_lock:
            self._active_contexts.pop(correlation_id, None)

    async def _retrieve_context(
        self,
        embeddings: List[float],
        parsed_message: Any,
        user_id: str,
        conversation_id: str,
    ) -> Dict[str, Any]:
        """Retrieve relevant context."""
        if not self.memory_processor:
            return {
                "memories": [],
                "conversation_history": [],
                "user_preferences": {},
                "entities": [
                    {"text": ent[0], "label": ent[1]} for ent in parsed_message.entities
                ],
                "embedding_similarity_threshold": 0.7,
                "context_summary": "Memory processor not available",
            }

        try:
            memory_context = await self.memory_processor.get_relevant_context(
                embeddings, parsed_message, user_id, conversation_id
            )
            return memory_context.to_dict()
        except Exception as e:
            return {
                "memories": [],
                "entities": [
                    {"text": ent[0], "label": ent[1]} for ent in parsed_message.entities
                ],
                "preferences": [],
                "facts": [],
                "relationships": [],
                "context_summary": f"Context retrieval failed: {str(e)}",
                "retrieval_time": 0.0,
                "total_memories_considered": 0,
                "embedding_similarity_threshold": 0.7,
            }

    async def _process_attachments(
        self, attachments: List[Dict[str, Any]], user_id: str, conversation_id: str
    ) -> Dict[str, Any]:
        """Process file attachments."""
        if not self.file_attachment_service:
            return {"error": "File attachment service not available"}
        attachment_context: Dict[str, Any] = {
            "files": [],
            "total_files": len(attachments),
            "processing_errors": [],
        }
        for attachment in attachments:
            attachment_id = attachment.get("id") or attachment.get("file_id")
            if not attachment_id:
                continue
            try:
                file_info = await self.file_attachment_service.get_file_info(
                    attachment_id
                )
                if not file_info:
                    attachment_context["processing_errors"].append(
                        f"File {attachment_id} not found"
                    )
                    continue
                attachment_context["files"].append(
                    {
                        "file_id": attachment_id,
                        "status": file_info.processing_status.value,
                    }
                )
            except Exception as e:
                attachment_context["processing_errors"].append(
                    f"Failed to process {attachment_id}: {str(e)}"
                )
        return attachment_context

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        avg_processing_time = (
            sum(self._processing_times) / len(self._processing_times)
            if self._processing_times
            else 0.0
        )
        success_rate = (
            self._successful_requests / self._total_requests
            if self._total_requests > 0
            else 0.0
        )
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "success_rate": success_rate,
            "retry_attempts": self._retry_attempts,
            "fallback_usage": self._fallback_usage,
            "avg_processing_time": avg_processing_time,
            "active_contexts": len(self._active_contexts),
        }

    def get_active_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active processing contexts."""
        return {
            correlation_id: {
                "user_id": ctx.user_id,
                "conversation_id": ctx.conversation_id,
                "status": ctx.status.value,
            }
            for correlation_id, ctx in self._active_contexts.items()
        }

    def reset_stats(self):
        """Reset processing statistics."""
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._retry_attempts = 0
        self._fallback_usage = 0
        self._processing_times.clear()
        logger.info("ChatOrchestrator statistics reset")
