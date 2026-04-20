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
    Tuple,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize memory query tracking attributes
        self._memory_query_counts: Dict[str, int] = {}
        self._max_memory_queries_per_request: int = 5  # Default limit

    _INTERNAL_ANALYSIS_PREFIX_MARKERS = (
        "since the user has greeted again without a specific new request",
        "this is not a complete meaningful response",
        "to complete the session continuity summary",
        "session continuity summary:",
    )

    _INTERNAL_ANALYSIS_LINE_PATTERNS = (
        r"^\s*in summary:\s*$",
        r"^\s*let'?s see if we can make sure the chat response is complete.*$",
        r"^\s*i(?:'|\u2019)ll acknowledge their greeting and be ready to assist.*$",
        r"^\s*to complete the session continuity summary.*$",
        r"^\s*session continuity summary:\s*.*$",
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
        original = str(content or "").replace("\r\n", "\n")
        cleaned = original
        lowered = cleaned.lower()

        for marker in cls._INTERNAL_ANALYSIS_PREFIX_MARKERS:
            index = lowered.find(marker)
            # Only trim from marker onward when scaffold appears near the beginning.
            # This prevents accidental truncation of otherwise valid long responses.
            if 0 <= index <= 240:
                cleaned = cleaned[:index]
                lowered = cleaned.lower()

        for pattern in cls._INTERNAL_ANALYSIS_LINE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

        cleaned = re.sub(r"^\s*=+\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            return cleaned
        return original.strip()

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
                raw_content = (
                    "I'm here and ready to help. What would you like to work on?"
                )
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

            # Use rich engine first if available
            rich_engine = getattr(self, "rich_formatting_engine", None)
            formatted_content = raw_content
            rich_metadata = {}
            from ...services.ResponseFormattingClass import Enums

            FormatType = Enums.FormatType  # Ensure FormatType is available

            if rich_engine:
                try:
                    user_prompt = str(
                        getattr(turn_context, "message", "") or ""
                    ).strip()
                    rich_formatted = await rich_engine.format_response(
                        user_query=user_prompt, response_content=raw_content
                    )

                    # If we got specialized formatting (like HTML cards), use it directly
                    if rich_formatted.format_type != FormatType.STANDARD_MARKDOWN:
                        formatting_payload = {
                            "render_type": rich_formatted.format_type.value,
                            "formatted": True,
                            "response_policy": policy_payload,
                            "rich_metadata": rich_formatted.metadata,
                            "formatting": {
                                "format_type": rich_formatted.format_type.value,
                                "sections": [],
                                "navigation_aids": [],
                                "accessibility_features": {},
                                "estimated_reading_time": 0,
                                "formatter_metadata": dict(
                                    rich_formatted.metadata or {}
                                ),
                            },
                        }
                        return rich_formatted.content, formatting_payload

                    formatted_content = rich_formatted.content
                    rich_metadata = rich_formatted.metadata
                except Exception as e:
                    logger.warning(f"Rich formatting engine failed: {e}")

            formatted = await formatting_engine.format_response(  # type: ignore[attr-defined]
                content=formatted_content,
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
                "rich_metadata": rich_metadata,
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

        correlation_id = request.correlation_id

        from ai_karen_engine.chat.telemetry import track_latency

        with track_latency("total_request", correlation_id):
            with track_latency("persist_user_message", correlation_id):
                user_message_record = await self._persist_user_message(request)

            with track_latency("resolve_conversation_state", correlation_id):
                conversation_state = await self._resolve_conversation_state(
                    request, user_message_record
                )

            with track_latency("build_working_context", correlation_id):
                working_context = await self._build_working_context(
                    request, conversation_state
                )

            with track_latency("select_execution_path", correlation_id):
                execution_path = await self._select_execution_path(
                    request, working_context
                )

            with track_latency("execute_generation", correlation_id):
                generation_result = await self._execute_generation(
                    request, working_context, execution_path
                )

            with track_latency("finalize_response", correlation_id):
                finalized = await self._finalize_response(
                    request=request,
                    generation_result=generation_result,
                    execution_path=execution_path,
                    working_context=working_context,
                    user_message_record=user_message_record,
                )

            with track_latency("persist_assistant_message", correlation_id):
                persisted = await self._persist_assistant_message(request, finalized)

            with track_latency("post_response_writeback", correlation_id):
                await self._post_response_writeback(request, persisted, working_context)

            with track_latency("emit_chat_telemetry", correlation_id):
                await self._emit_chat_telemetry(request, persisted, working_context)

        return persisted

    async def handle_chat_stream(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Canonical streaming chat lifecycle with durable persistence."""
        if not (request.stream or request.streaming):
            raise ValueError("handle_chat_stream requires a streaming chat request")

        correlation_id = request.correlation_id

        from ai_karen_engine.chat.telemetry import track_latency

        with track_latency("stream_total_request", correlation_id):
            with track_latency("stream_persist_user_message", correlation_id):
                user_message_record = await self._persist_user_message(request)

            with track_latency("stream_resolve_conversation_state", correlation_id):
                conversation_state = await self._resolve_conversation_state(
                    request, user_message_record
                )

            with track_latency("stream_build_working_context", correlation_id):
                working_context = await self._build_working_context(
                    request, conversation_state
                )

            with track_latency("stream_select_execution_path", correlation_id):
                execution_path = await self._select_execution_path(
                    request, working_context
                )

            with track_latency("stream_process_message", correlation_id):
                raw_stream = self._execute_generation_stream(
                    request, working_context, execution_path
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
                    # We continue to yield the completion chunk at the very end
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

            with track_latency("stream_finalize_response", correlation_id):
                finalized = await self._finalize_response(
                    request=request,
                    generation_result=interim_response,
                    execution_path=execution_path,
                    working_context=working_context,
                    user_message_record=user_message_record,
                )

            with track_latency("stream_persist_assistant_message", correlation_id):
                persisted = await self._persist_assistant_message(request, finalized)

            with track_latency("stream_post_response_writeback", correlation_id):
                await self._post_response_writeback(request, persisted, working_context)

            with track_latency("stream_emit_chat_telemetry", correlation_id):
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

        return await canonical_stream()

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
        parsed_message = None
        embeddings = None
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
            "parsed_message": parsed_message,
            "embeddings": embeddings,
        }

    async def _select_execution_path(
        self,
        request: ChatRequest,
        working_context: Dict[str, Any],
    ) -> str:
        """Select the Stage 1 execution path."""
        return "direct_llm"

    async def _execute_generation_with_retry(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        parsed_message: Any,
        embeddings: Optional[List[float]],
        integrated_context: Optional[Any],
        active_instructions: List[Any],
        stream: bool = False,
    ) -> Union[Tuple[str, Dict[str, Any], bool], AsyncIterator[str]]:
        """Shared retry logic for LLM generation without re-triggering context assembly."""
        last_error = None

        for attempt in range(self.retry_config.max_attempts):
            context.retry_count = attempt
            if context.cancel_event.is_set():
                raise asyncio.CancelledError()

            if attempt > 0:
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
                # Direct call to generation enhanced, bypassing redundant _process_message_internal
                return await self._generate_ai_response_enhanced(
                    message=request.message,
                    parsed_message=parsed_message,
                    embeddings=embeddings,
                    integrated_context=integrated_context,
                    active_instructions=active_instructions,
                    context=context,
                    stream=stream,
                )
            except (asyncio.CancelledError, asyncio.TimeoutError):
                raise
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                last_error = e

        raise last_error or RuntimeError("Generation failed after multiple attempts")

    async def _execute_generation(
        self,
        request: ChatRequest,
        working_context: Dict[str, Any],
        execution_path: str,
    ) -> ChatResponse:
        """Execute generation through the existing orchestrator path using built context."""
        from ai_karen_engine.chat.telemetry import track_latency

        correlation_id = request.correlation_id
        start_time = time.time()

        # Create a processing context to satisfy the LLM Mixin interface
        context = ProcessingContext(request=request)
        context.status = ProcessingStatus.PROCESSING
        context.processing_start = datetime.utcnow()

        # Extract pre-built context components
        parsed_message = working_context.get("parsed_message")
        embeddings = working_context.get("embeddings")

        # Get instructions from instruction processor (Step 4 gating)
        active_instructions = []
        try:
            from ai_karen_engine.chat.instruction_processor import InstructionContext

            instruction_context = InstructionContext(
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                session_id=request.session_id,
                message_history=[request.message],
                metadata=request.metadata,
            )
            active_instructions = (
                await self.instruction_processor.get_active_instructions(
                    instruction_context
                )
            )
        except Exception:
            active_instructions = []

        # Integrate context
        integrated_context = None
        try:
            integrated_context = await self.context_integrator.integrate_context(
                working_context.get("request_context") or working_context,
                request.message,
                request.user_id,
                request.conversation_id,
            )
        except Exception:
            pass

        # Execute generation
        try:
            with track_latency("llm_generation_core", correlation_id):
                result = await self._execute_generation_with_retry(
                    request=request,
                    context=context,
                    parsed_message=parsed_message,
                    embeddings=embeddings,
                    integrated_context=integrated_context,
                    active_instructions=active_instructions,
                    stream=False,
                )

            res_tuple = cast(tuple[str, dict[str, Any], bool], result)
            ai_response, llm_metadata, llm_used_fallback = res_tuple

            processing_time = time.time() - start_time
            return ChatResponse(
                request_id=request.request_id,
                response=ai_response,
                correlation_id=correlation_id,
                conversation_id=request.conversation_id,
                assistant_message_id=None,
                processing_time=processing_time,
                status=ProcessingStatus.COMPLETED,
                used_fallback=llm_used_fallback,
                context_used=bool(integrated_context),
                execution_path=execution_path,
                structured_content={},
                actions=[],
                metadata={"llm": llm_metadata},
                telemetry={},
                error=None,
                error_type=None,
            )

        except Exception as e:
            logger.error(f"Generation failed in _execute_generation: {e}")
            raise

    async def _execute_generation_stream(
        self,
        request: ChatRequest,
        working_context: Dict[str, Any],
        execution_path: str,
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Execute streaming generation through the existing orchestrator path using built context."""
        from ai_karen_engine.chat.telemetry import track_latency

        correlation_id = request.correlation_id
        start_time = time.time()

        # Create a processing context to satisfy the LLM Mixin interface
        context = ProcessingContext(request=request)
        context.status = ProcessingStatus.PROCESSING
        context.processing_start = datetime.utcnow()

        # Extract pre-built context components
        parsed_message = working_context.get("parsed_message")
        embeddings = working_context.get("embeddings")

        # Get instructions from instruction processor
        active_instructions = []
        try:
            from ai_karen_engine.chat.instruction_processor import InstructionContext

            instruction_context = InstructionContext(
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                session_id=request.session_id,
                message_history=[request.message],
                metadata=request.metadata,
            )
            active_instructions = (
                await self.instruction_processor.get_active_instructions(
                    instruction_context
                )
            )
        except Exception:
            active_instructions = []

        # Integrate context
        integrated_context = None
        try:
            integrated_context = await self.context_integrator.integrate_context(
                working_context.get("request_context") or working_context,
                request.message,
                request.user_id,
                request.conversation_id,
            )
        except Exception:
            pass

        # Execute streaming generation
        try:
            with track_latency("llm_generation_stream_core", correlation_id):
                raw_stream = await self._execute_generation_with_retry(
                    request=request,
                    context=context,
                    parsed_message=parsed_message,
                    embeddings=embeddings,
                    integrated_context=integrated_context,
                    active_instructions=active_instructions,
                    stream=True,
                )

            if not hasattr(raw_stream, "__aiter__"):
                raise RuntimeError(
                    "Non-streaming result returned during _execute_generation_stream"
                )

            async for chunk_text in cast(AsyncIterator[str], raw_stream):
                yield ChatStreamChunk(
                    type="content",
                    content=chunk_text,
                    correlation_id=correlation_id,
                    metadata={"execution_path": execution_path},
                )

            # Metadata and completion chunks are handled by the caller or specialized yielders
            yield ChatStreamChunk(
                type="complete",
                content="",
                correlation_id=correlation_id,
                metadata={
                    "processing_time": time.time() - start_time,
                    "execution_path": execution_path,
                },
            )

        except Exception as e:
            logger.error(
                f"Streaming generation failed in _execute_generation_stream: {e}"
            )
            yield ChatStreamChunk(
                type="error",
                content=str(e),
                correlation_id=correlation_id,
                metadata={"error_type": ErrorType.AI_MODEL_ERROR},
            )

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
            generation_result.response = str(generation_result.response or "")
        else:
            (
                formatted_content,
                formatting_payload,
            ) = await self._format_response_with_engine(
                generation_result.response,
                request,
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
        Process a chat message using the optimized canonical paths.
        This provides backward compatibility while ensuring all paths use the hot-path optimizations.
        """
        if request.stream or request.streaming:
            return self.handle_chat_stream(request)
        else:
            return await self.handle_chat(request)

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

        # Clear memory query count for this request
        if hasattr(self, "_memory_query_counts"):
            context_obj = None
            # Try to get the context from the cache before it was removed
            async with self._contexts_lock:
                context_obj = self._active_contexts.get(correlation_id)

            if context_obj:
                context_key = f"{context_obj.user_id}:{context_obj.conversation_id}"
                self._memory_query_counts.pop(context_key, None)

    async def _retrieve_context(
        self,
        embeddings: List[float],
        parsed_message: Any,
        user_id: str,
        conversation_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve relevant context with request-scoped memoization."""
        context_key = f"{user_id}:{conversation_id}"

        # Check if we have cached context in orchestrator state
        if not force_refresh and hasattr(self, "_context_cache"):
            cached_context = self._context_cache.get(context_key)
            if cached_context:
                logger.debug(f"Using cached context for {context_key}")
                return cached_context.get("context")

        # Check query count for throttling
        if hasattr(self, "_memory_query_counts"):
            query_count = self._memory_query_counts.get(context_key, 0)
            if query_count >= self._max_memory_queries_per_request:
                logger.warning(f"Memory query limit exceeded for {context_key}")
                return self._context_cache.get(context_key, {}).get("context", {})

            # Increment counter
            self._memory_query_counts[context_key] = query_count + 1

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
            result = memory_context.to_dict()

            # Cache the result
            if not hasattr(self, "_context_cache"):
                self._context_cache = {}

            self._context_cache[context_key] = {
                "context": result,
                "timestamp": time.time(),
                "user_id": user_id,
                "conversation_id": conversation_id,
            }

            # Limit cache size (max 100 entries)
            if len(self._context_cache) > 100:
                oldest_key = min(
                    self._context_cache.keys(),
                    key=lambda k: self._context_cache[k]["timestamp"],
                )
                del self._context_cache[oldest_key]

            return result
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
