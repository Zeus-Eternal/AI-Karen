"""
LangGraph Orchestration Foundation

This module implements the core orchestration backbone using LangGraph for
human-in-the-loop workflows with typed state management and checkpointing.

Graph Structure:
auth_gate → safety_gate → memory_fetch → intent_detect → planner →
router_select → tool_exec → response_synth → approval_gate → memory_write
"""

from typing import (
    Dict,
    Any,
    List,
    Optional,
    TypedDict,
    Annotated,
    Literal,
    Deque,
    Tuple,
    cast,
)
from dataclasses import dataclass, field, replace, asdict
import asyncio
from collections import deque
import logging
import os
import re
import time
from datetime import datetime, timezone
import uuid

from ai_karen_engine.auth.auth_service import (
    AuthService,
    get_auth_service,
    user_account_to_dict,
)
from ai_karen_engine.memory.distilbert_service import DistilBertService, SafetyResult
from ai_karen_engine.services.llm_router import ChatRequest, LLMRouter
from ai_karen_engine.memory.profile_manager import Guardrails, ProfileManager
from ai_karen_engine.services.tool_service import ToolInput, ToolOutput, ToolService
from ai_karen_engine.models.shared_types import ToolType
from ai_karen_engine.memory.memory_service import (
    MemoryType,
    UISource,
    WebUIMemoryService,
)

from ai_karen_engine.services.response_formatting_engine import (
    ResponseFormattingEngine,
    FormattingContext,
    DisplayContext,
    AccessibilityLevel,
)
from ai_karen_engine.services.ResponseFormattingClass.Specialized.Integration import (
    get_specialized_integration,
)
from ai_karen_engine.services.response_policy_enforcer import ResponsePolicyEnforcer
from ai_karen_engine.services.response_formatting.response_formatter import (
    PrettyOutputLayer,
)
from ai_karen_engine.copilotkit.session_state_manager import SessionStateManager
from ai_karen_engine.utils.chat_helpers import (
    build_user_identity_line,
    build_structured_context_sections,
    wants_long_form_markdown_article,
    strip_internal_analysis_leakage,
    is_low_information_content,
)

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool

from ai_karen_engine.agent_medusa.agent_medusa_node import medusa_node

# Import new unified components
from .nodes import (
    auth_gate_node,
    safety_gate_node,
    memory_fetch_node,
    intent_detect_node,
    planner_node,
    router_select_node,
    tool_exec_node,
    response_synth_node,
    approval_gate_node,
    memory_write_node,
    stream_process_node,
)
from .runtime_policy import runtime_policy_enforcer_node
from .formatting.response_formatter_pipeline import response_formatter_node
from .diagnostics import DiagnosticsEngine

# Import consolidated classes from separate modules
from .context.context_manager import ContextManager
from .decision_engine import DecisionEngine

# Import contracts
from .contracts.orchestration_state import (
    LangGraphOrchestrationState,
    create_initial_state,
    create_streaming_initial_state,
)
from .contracts.orchestration_config import LangGraphOrchestrationConfig

# Import from contracts module
from .contracts.orchestration_state import (
    LangGraphOrchestrationState,
    create_initial_state,
    create_streaming_initial_state,
)
from .contracts.orchestration_config import LangGraphOrchestrationConfig

logger = logging.getLogger(__name__)


class LangGraphOrchestrator:
    """Main orchestration class using LangGraph for workflow management."""

    def __init__(
        self,
        config: Optional[LangGraphOrchestrationConfig] = None,
        *,
        auth_service: Optional[Any] = None,
        safety_service: Optional[DistilBertService] = None,
        memory_service: Optional[Any] = None,
        decision_engine: Optional[DecisionEngine] = None,
        tool_service: Optional[ToolService] = None,
        llm_router: Optional[LLMRouter] = None,
        profile_manager: Optional[ProfileManager] = None,
        context_manager: Optional[ContextManager] = None,
        session_state_manager: Optional[SessionStateManager] = None,
    ):
        self.config = config or LangGraphOrchestrationConfig()
        self.checkpointer = MemorySaver() if self.config.checkpoint_enabled else None
        self.graph = None
        self._build_graph()

        # Runtime telemetry
        self._start_time = datetime.now(timezone.utc)
        self._stats_lock = asyncio.Lock()
        self._config_lock = asyncio.Lock()
        self._active_sessions: Dict[str, datetime] = {}
        self._total_processed: int = 0
        self._total_failed: int = 0
        self._latency_samples: Deque[float] = deque(maxlen=1000)
        self._last_error: Optional[Dict[str, Any]] = None

        # Dependency handles (lazily resolved when not provided)
        self._auth_service: Optional[Any] = auth_service
        self._auth_service_lock = asyncio.Lock()
        self._auth_service_failed = False
        self._safety_service: Optional[DistilBertService] = safety_service
        self._memory_service: Optional[Any] = memory_service
        self._context_manager: Optional[ContextManager] = context_manager
        self._session_state_manager: Optional[SessionStateManager] = (
            session_state_manager
        )
        self._decision_engine: DecisionEngine = decision_engine or DecisionEngine()
        self._tool_service: Optional[ToolService] = tool_service
        self._llm_router: LLMRouter = llm_router or LLMRouter()
        self._profile_manager: ProfileManager = profile_manager or ProfileManager()

        # Track fallback resolutions so we only warn once per dependency.
        self._memory_resolution_failed = False
        self._tool_resolution_failed = False
        self._session_state_resolution_failed = False

    # --- Dependencies and Handlers ---

    async def _ensure_auth_service(self) -> Optional[Any]:
        """Resolve the authentication service on first use."""

        if self._auth_service_failed:
            return None

        if self._auth_service is not None:
            return self._auth_service

        async with self._auth_service_lock:
            if self._auth_service is None and not self._auth_service_failed:
                try:
                    self._auth_service = await get_auth_service()
                except Exception as exc:  # pragma: no cover - depends on environment
                    logger.warning("Auth service unavailable: %s", exc)
                    self._auth_service_failed = True
                    return None

        return self._auth_service

    async def _ensure_context_manager(self) -> ContextManager:
        """Return a context manager bound to the configured memory service."""

        if self._context_manager is not None:
            return self._context_manager

        memory_service = await self._resolve_memory_service()
        self._context_manager = ContextManager(memory_service)
        return self._context_manager

    async def _resolve_memory_service(self) -> Optional[Any]:
        """Resolve the shared memory service via the service registry if possible."""

        if self._memory_service is not None or self._memory_resolution_failed:
            return self._memory_service

        try:
            from ai_karen_engine.core.service_registry import (
                get_memory_service,
            )  # Lazy import

            self._memory_service = await get_memory_service()
        except Exception as exc:  # pragma: no cover - optional dependency
            if not self._memory_resolution_failed:
                logger.warning("Memory service unavailable: %s", exc)
            try:
                self._memory_service = WebUIMemoryService()
                logger.info("Fell back to direct WebUIMemoryService initialization")
            except Exception as fallback_exc:  # pragma: no cover - optional dependency
                logger.warning(
                    "Direct memory service fallback unavailable: %s", fallback_exc
                )
                self._memory_resolution_failed = True
                self._memory_service = None

        return self._memory_service

    async def _ensure_session_state_manager(self) -> Optional[SessionStateManager]:
        """Resolve session state manager lazily."""
        if (
            self._session_state_manager is not None
            or self._session_state_resolution_failed
        ):
            return self._session_state_manager

        try:
            # Try to resolve via service registry or direct instantiation if available
            self._session_state_manager = SessionStateManager(
                memory_service=await self._resolve_memory_service()
            )
        except Exception as exc:
            if not self._session_state_resolution_failed:
                logger.warning("Session state manager unavailable: %s", exc)
            self._session_state_resolution_failed = True
            self._session_state_manager = None

        return self._session_state_manager

    async def _ensure_tool_service(self) -> Optional[ToolService]:
        """Resolve tool execution service lazily."""

        if self._tool_service is not None or self._tool_resolution_failed:
            return self._tool_service

        try:
            if self._tool_service is None:
                from ai_karen_engine.core.service_registry import get_tool_service

                self._tool_service = await get_tool_service()
        except Exception as exc:  # pragma: no cover - optional dependency
            if not self._tool_resolution_failed:
                logger.warning("Tool service unavailable: %s", exc)
            self._tool_resolution_failed = True
            self._tool_service = ToolService()

        if self._tool_service is None:
            self._tool_service = ToolService()

        return self._tool_service

    def _build_graph(self):
        """Build the orchestration graph with all nodes and edges"""
        workflow = StateGraph(LangGraphOrchestrationState)

        # Add nodes using extracted components
        workflow.add_node(
            "auth_gate",
            lambda state: auth_gate_node(state, auth_service=self._auth_service),
        )
        workflow.add_node(
            "safety_gate",
            lambda state: safety_gate_node(
                state, profile_manager=self._profile_manager
            ),
        )
        workflow.add_node(
            "memory_fetch",
            lambda state: memory_fetch_node(
                state, context_manager=self._context_manager
            ),
        )
        workflow.add_node(
            "intent_detect",
            lambda state: intent_detect_node(
                state, decision_engine=self._decision_engine
            ),
        )
        workflow.add_node("planner", planner_node)
        workflow.add_node(
            "router_select",
            lambda state: router_select_node(
                state,
                llm_router=self._llm_router,
                profile_manager=self._profile_manager,
            ),
        )
        workflow.add_node("medusa_node", medusa_node)
        workflow.add_node("tool_exec", tool_exec_node)
        workflow.add_node("response_synth", response_synth_node)
        workflow.add_node("approval_gate", approval_gate_node)
        workflow.add_node("memory_write", memory_write_node)
        workflow.add_node("response_formatter", response_formatter_node)

        # Define the flow
        workflow.add_edge(START, "auth_gate")

        # Conditional edges based on configuration
        if self.config.enable_auth_gate:
            workflow.add_conditional_edges(
                "auth_gate",
                self._should_continue_after_auth,
                {
                    "continue": "safety_gate"
                    if self.config.enable_safety_gate
                    else "memory_fetch",
                    "reject": END,
                },
            )
        else:
            workflow.add_edge(
                "auth_gate",
                "safety_gate" if self.config.enable_safety_gate else "memory_fetch",
            )

        if self.config.enable_safety_gate:
            workflow.add_conditional_edges(
                "safety_gate",
                self._should_continue_after_safety,
                {
                    "continue": "memory_fetch"
                    if self.config.enable_memory_fetch
                    else "intent_detect",
                    "reject": END,
                    "review": "approval_gate",
                },
            )

        if self.config.enable_memory_fetch:
            workflow.add_edge("memory_fetch", "intent_detect")

        workflow.add_edge("intent_detect", "planner")
        workflow.add_edge("planner", "router_select")

        # Route to Medusa or Normal Tool Execution
        workflow.add_conditional_edges(
            "router_select",
            self._should_use_medusa,
            {"medusa": "medusa_node", "normal": "tool_exec"},
        )

        workflow.add_edge("medusa_node", "response_synth")
        workflow.add_edge("tool_exec", "response_synth")

        if self.config.enable_approval_gate:
            workflow.add_conditional_edges(
                "response_synth",
                self._should_require_approval,
                {"approve": "memory_write", "review": "approval_gate"},
            )
            workflow.add_conditional_edges(
                "approval_gate",
                self._check_approval_status,
                {
                    "approved": "memory_write",
                    "rejected": END,
                    "pending": "approval_gate",  # Wait for human input
                },
            )
        else:
            workflow.add_edge("response_synth", "memory_write")

        workflow.add_edge("memory_write", "response_formatter")
        workflow.add_edge("response_formatter", END)

        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)

    # --- Operational Methods ---

    def _should_use_medusa(self, state: LangGraphOrchestrationState) -> str:
        """Determine if AgentMedusa should handle the request."""
        intent = state.get("detected_intent", "")
        # Extension and Routing intents go to Medusa
        if intent in (
            "routing.select",
            "routing.profile",
            "admin_panel",
            "extension.action",
            "agent_complex_reasoning",
        ):
            return "medusa"

        # Check if medusa is explicitly requested in config
        if state.get("request_config", {}).get("use_medusa"):
            return "medusa"

        return "normal"

    def _should_continue_after_auth(self, state: LangGraphOrchestrationState) -> str:
        """Determine if processing should continue after auth gate"""
        auth_status = state.get("auth_status")
        return "continue" if auth_status == "authenticated" else "reject"

    def _should_continue_after_safety(self, state: LangGraphOrchestrationState) -> str:
        """Determine if processing should continue after safety gate"""
        safety_status = state.get("safety_status")
        if safety_status == "safe":
            return "continue"
        elif safety_status == "review_required":
            return "review"
        else:
            return "reject"

    def _should_require_approval(self, state: LangGraphOrchestrationState) -> str:
        """Determine if human approval is required"""
        # Check if approval is required based on various factors
        safety_flags = state.get("safety_flags", [])
        tool_results = state.get("tool_results", [])

        # Require approval if there are safety flags or sensitive tools were used
        if safety_flags or any("sensitive" in str(result) for result in tool_results):
            state["requires_approval"] = True
            return "review"
        else:
            return "approve"

    def _check_approval_status(self, state: LangGraphOrchestrationState) -> str:
        """Check the current approval status"""
        approval_status = state.get("approval_status", "pending")
        return approval_status

    async def run_dry_run_analysis(
        self,
        *,
        message: str,
        session_id: Optional[str] = None,
        user: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Simulate orchestration without side effects for diagnostics."""

        diagnostics_engine = DiagnosticsEngine(
            decision_engine=self._decision_engine,
            context_manager=await self._ensure_context_manager(),
            llm_router=self._llm_router,
            profile_manager=self._profile_manager,
        )

        return await diagnostics_engine.run_dry_run_analysis(
            message=message,
            session_id=session_id,
            user=user,
            context=context,
        )

    async def process(
        self,
        messages: List[BaseMessage],
        user_id: str,
        session_id: str = None,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Process a conversation through the orchestration graph

        Args:
            messages: List of conversation messages
            user_id: User identifier
            session_id: Session identifier (optional)
            config: Additional configuration (optional)

        Returns:
            Final state after processing
        """
        if not session_id:
            session_id = f"{user_id}_{datetime.now(timezone.utc).isoformat()}"

        # Initialize state
        runtime_config = config or {}

        initial_state = create_initial_state(
            messages, user_id, session_id, runtime_config
        )

        start_time = datetime.now(timezone.utc)
        error_message: Optional[str] = None

        await self._register_session(session_id)

        try:
            # Process through the graph
            thread_config = {"configurable": {"thread_id": session_id}}
            final_state = await self.graph.ainvoke(initial_state, config=thread_config)

            return final_state

        except Exception as e:
            error_message = str(e)
            logger.error(f"Orchestration processing error: {e}")
            initial_state["errors"].append(f"Processing error: {error_message}")
            return initial_state

        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._finalize_session(session_id, duration, error_message)

    async def stream_process(
        self,
        messages: List[BaseMessage],
        user_id: str,
        session_id: str = None,
        config: Dict[str, Any] = None,
    ):
        """
        Stream process a conversation through the orchestration graph

        Args:
            messages: List of conversation messages
            user_id: User identifier
            session_id: Session identifier (optional)
            config: Additional configuration (optional)

        Yields:
            State updates during processing
        """
        if not session_id:
            session_id = f"{user_id}_{datetime.now(timezone.utc).isoformat()}"

        # Initialize state (same as process method)
        runtime_config = config or {}

        initial_state = create_streaming_initial_state(
            messages, user_id, session_id, runtime_config
        )

        start_time = datetime.now(timezone.utc)
        error_message: Optional[str] = None

        await self._register_session(session_id)

        try:
            thread_config = {"configurable": {"thread_id": session_id}}

            # Stream through the graph
            async for chunk in self.graph.astream(initial_state, config=thread_config):
                yield chunk

        except Exception as e:
            error_message = str(e)
            logger.error(f"Orchestration streaming error: {e}")
            yield {"error": f"Streaming error: {error_message}"}

        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._finalize_session(session_id, duration, error_message)

    async def _register_session(self, session_id: str) -> None:
        """Register an active orchestration session for telemetry."""

        async with self._stats_lock:
            self._active_sessions[session_id] = datetime.now(timezone.utc)

    async def _finalize_session(
        self,
        session_id: str,
        duration: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Finalize bookkeeping for a session."""

        async with self._stats_lock:
            self._active_sessions.pop(session_id, None)
            if duration is not None:
                self._latency_samples.append(max(duration, 0.0))
            self._total_processed += 1

            if error_message:
                self._total_failed += 1
                self._last_error = {
                    "message": error_message,
                    "timestamp": datetime.now(timezone.utc),
                }

    async def update_configuration(
        self, updates: Dict[str, Any]
    ) -> LangGraphOrchestrationConfig:
        """Update orchestrator configuration and rebuild the graph."""

        if not updates:
            return self.config

        allowed_fields = set(LangGraphOrchestrationConfig.__annotations__.keys())
        sanitized_updates = {
            key: value
            for key, value in updates.items()
            if key in allowed_fields and value is not None
        }

        if not sanitized_updates:
            return self.config

        async with self._config_lock:
            self.config = replace(self.config, **sanitized_updates)
            self.checkpointer = (
                MemorySaver() if self.config.checkpoint_enabled else None
            )
            self._build_graph()
            return self.config

    async def get_runtime_status(self) -> Dict[str, Any]:
        """Return telemetry snapshot for orchestration runtime."""

        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        async with self._stats_lock:
            active_sessions = len(self._active_sessions)
            total_processed = self._total_processed
            failed_sessions = self._total_failed
            latency_samples = list(self._latency_samples)
            last_error = self._last_error.copy() if self._last_error else None

        average_latency = (
            sum(latency_samples) / len(latency_samples) if latency_samples else 0.0
        )
        p95_latency = self._percentile(latency_samples, 0.95)

        return {
            "active_sessions": active_sessions,
            "total_processed": total_processed,
            "failed_sessions": failed_sessions,
            "uptime": uptime,
            "average_latency": average_latency,
            "p95_latency": p95_latency,
            "last_error": last_error,
        }

    @staticmethod
    def _percentile(samples: List[float], percentile: float) -> float:
        """Calculate percentile for latency samples."""

        if not samples:
            return 0.0

        ordered = sorted(samples)
        index = max(
            0, min(len(ordered) - 1, int(round(percentile * (len(ordered) - 1))))
        )
        return ordered[index]

    async def shutdown(self) -> None:
        """Gracefully release orchestrator resources."""

        logger.info("Shutting down LangGraph orchestrator")

        try:
            await self._llm_router.shutdown()
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logger.warning("LLM router shutdown encountered an error: %s", exc)

        if self._context_manager:
            self._context_manager.clear_context_cache()

        async with self._stats_lock:
            self._active_sessions.clear()
            self._latency_samples.clear()


# Factory function for easy instantiation
def create_orchestrator(
    config: LangGraphOrchestrationConfig = None,
) -> LangGraphOrchestrator:
    """Create a new LangGraph orchestrator instance"""
    return LangGraphOrchestrator(config)


# Default orchestrator instance
default_orchestrator = None


def get_default_orchestrator() -> LangGraphOrchestrator:
    """Get the default orchestrator instance (singleton)"""
    global default_orchestrator
    if default_orchestrator is None:
        default_orchestrator = create_orchestrator()
    return default_orchestrator
