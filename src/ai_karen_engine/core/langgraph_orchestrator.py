"""
LangGraph Orchestration Foundation

This module implements the core orchestration backbone using LangGraph for
human-in-the-loop workflows with typed state management and checkpointing.

Graph Structure:
auth_gate → safety_gate → memory_fetch → intent_detect → planner → 
router_select → tool_exec → response_synth → approval_gate → memory_write
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal, Deque, Tuple, cast
from dataclasses import dataclass, field, replace, asdict
import asyncio
from collections import deque
import logging
import os
from datetime import datetime, timezone
import uuid

from ai_karen_engine.auth.auth_service import AuthService, get_auth_service, user_account_to_dict
from ai_karen_engine.core.cortex.routing_intents import resolve_routing_intent
from ai_karen_engine.core.response.analyzer import SpacyAnalyzer, AnalysisContext
from ai_karen_engine.core.reasoning.synthesis import (
    MetacognitiveMonitor,
)
from ai_karen_engine.services.distilbert_service import DistilBertService, SafetyResult
from ai_karen_engine.services.llm_router import ChatRequest, LLMRouter
from ai_karen_engine.memory.profile_manager import Guardrails, ProfileManager
from ai_karen_engine.services.tool_service import ToolInput, ToolOutput, ToolService
from ai_karen_engine.models.shared_types import ToolType
from ai_karen_engine.memory.memory_service import MemoryType, UISource, WebUIMemoryService

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool

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
                logger.debug("Memory service build_context signature mismatch; using local context adapter")
            except Exception as exc:
                logger.warning("Context build fallback triggered: %s", exc)

        return context

    def clear_context_cache(self) -> None:
        """Compatibility no-op for legacy orchestrator cleanup."""
        return None


class DecisionEngine:
    """Adapter exposing the legacy intent-analysis surface via the reasoning stack."""

    def __init__(
        self,
        analyzer: Optional[SpacyAnalyzer] = None,
        classifier: Optional[DistilBertService] = None,
    ):
        self._analyzer = analyzer or SpacyAnalyzer()
        self._classifier = classifier or DistilBertService()
        self._metacognition = MetacognitiveMonitor()

    @staticmethod
    def _suggest_tools(intent: str) -> List[str]:
        mapping = {
            "greeting": [],
            "weather_query": ["weather"],
            "time_query": ["time"],
            "book_query": ["search_books"],
            "information_retrieval": ["search_memory"],
            "technical_question": ["search_docs"],
            "debug_error": ["search_logs"],
            "documentation": ["search_docs"],
            "troubleshoot": ["search_logs"],
            "system_config": ["search_docs"],
        }
        return mapping.get(intent, [])

    @staticmethod
    def _normalize_cortex_intent(cortex_intent: str, analyzer_intent: str) -> str:
        normalized = (cortex_intent or "").strip().lower()
        if normalized in {"", "unknown", "general", "general_assist"}:
            return analyzer_intent

        cortex_to_response = {
            "greeting": "casual_chat",
            "search": "information_retrieval",
            "memory": "information_retrieval",
            "diagnostics": "troubleshoot",
            "system_status": "system_config",
            "audit_log": "documentation",
            "logout": "casual_chat",
            "routing.select": "system_config",
            "routing.profile": "system_config",
            "admin_panel": "system_config",
        }
        return cortex_to_response.get(normalized, normalized)

    @staticmethod
    def _normalize_classifier_intent(classifier_intent: str, analyzer_intent: str) -> str:
        normalized = (classifier_intent or "").strip().lower()
        if normalized in {"", "unknown"}:
            return analyzer_intent

        classifier_to_response = {
            "information_seeking": "information_retrieval",
            "task_completion": "how_to_guide",
            "problem_solving": "troubleshoot",
            "creative_assistance": "creative_task",
            "decision_making": "business_advice",
            "social_interaction": "casual_chat",
        }
        return classifier_to_response.get(normalized, analyzer_intent)

    async def analyze_intent(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = await self._analyzer.analyze_comprehensive(
            prompt,
            context=AnalysisContext(
                user_id=str((context or {}).get("user_id") or "") or None,
                session_id=str((context or {}).get("session_id") or "") or None,
                interaction_history=cast(List[Dict[str, Any]], (context or {}).get("conversation_history") or []),
                system_capabilities=cast(Dict[str, Any], context or {}),
            ),
        )
        context_dict = context or {}
        cortex_intent, cortex_meta = resolve_routing_intent(prompt, context_dict)
        analyzer_intent = result.intent.primary_intent.value
        cortex_confidence = 0.0
        if isinstance(cortex_meta, dict):
            raw_confidence = cortex_meta.get("confidence")
            if isinstance(raw_confidence, (int, float)):
                cortex_confidence = float(raw_confidence)

        classifier_intent = "unknown"
        classifier_confidence = 0.0
        classifier_entities: List[Dict[str, Any]] = []
        try:
            classifier_result = await self._classifier.detect_intent(prompt)
            classifier_intent = classifier_result.intent
            classifier_confidence = classifier_result.confidence
            classifier_entities = classifier_result.entities
        except Exception as exc:
            logger.debug("DistilBERT intent classification unavailable: %s", exc)

        if cortex_intent and cortex_intent.lower() not in {"unknown", ""}:
            primary_intent = self._normalize_cortex_intent(cortex_intent, analyzer_intent)
        else:
            primary_intent = self._normalize_classifier_intent(classifier_intent, analyzer_intent)

        reasoning_state = self._metacognition.monitor_reasoning_process(
            query=prompt,
            current_output=primary_intent,
            context=[
                str(context_dict.get("context_summary", "")),
            ] if context else None,
        )
        strategy = self._metacognition.select_strategy(
            query=prompt,
            task_type=primary_intent,
            current_state=reasoning_state,
        )
        raw_entities = result.entities.get("entities", []) if isinstance(result.entities, dict) else []

        normalized_entities: List[Dict[str, Any]] = []
        for entity in raw_entities:
            if isinstance(entity, dict):
                normalized_entities.append(entity)
            elif hasattr(entity, "text"):
                normalized_entities.append(
                    {
                        "type": getattr(entity, "label_", "unknown"),
                        "value": getattr(entity, "text", ""),
                    }
                )
        for entity in classifier_entities:
            if isinstance(entity, dict):
                normalized_entities.append(entity)

        return {
            "primary_intent": primary_intent,
            "intent": primary_intent,
            "confidence": max(
                result.intent.confidence,
                classifier_confidence,
                cortex_confidence,
                reasoning_state.confidence,
            ),
            "suggested_tools": self._suggest_tools(primary_intent),
            "entities": normalized_entities,
            "requires_clarification": result.intent.confidence < 0.45 or bool(reasoning_state.knowledge_gaps),
            "sentiment": result.sentiment.primary_sentiment.value,
            "persona_recommendation": result.persona_recommendation,
            "metadata": {
                **result.metadata,
                "intent_source": "cortex+response_analyzer",
                "cortex_intent": cortex_intent,
                "cortex_meta": cortex_meta,
                "classifier_intent": classifier_intent,
                "classifier_confidence": classifier_confidence,
                "analyzer_intent": analyzer_intent,
                "analyzer_confidence": result.intent.confidence,
                "reasoning_trace": [
                    f"intent={primary_intent}",
                    f"cortex={cortex_intent}",
                    f"strategy={strategy.value}",
                    f"state={reasoning_state.cognitive_state.value}",
                ],
                "strategy_used": strategy.value,
                "quality_score": reasoning_state.performance_estimate,
                "knowledge_gaps": reasoning_state.knowledge_gaps,
                "metacognitive_state": reasoning_state.cognitive_state.value,
                "reasoning_confidence": reasoning_state.confidence,
                "reasoning_certainty": reasoning_state.certainty,
            },
            "context": context or {},
        }


class OrchestrationState(TypedDict):
    """Typed state for the orchestration graph"""
    # Input/Output
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    tenant_id: Optional[str]

    # Authentication & Authorization
    auth_status: Optional[str]  # "authenticated", "failed", "pending"
    user_permissions: Optional[Dict[str, Any]]
    auth_context: Optional[Dict[str, Any]]
    user_profile: Optional[Dict[str, Any]]

    # Safety & Guardrails
    safety_status: Optional[str]  # "safe", "unsafe", "review_required"
    safety_flags: Optional[List[str]]
    safety_evaluation: Optional[Dict[str, Any]]

    # Memory & Context
    memory_context: Optional[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, Any]]]
    
    # Intent & Planning
    detected_intent: Optional[str]
    intent_confidence: Optional[float]
    execution_plan: Optional[Dict[str, Any]]
    intent_analysis: Optional[Dict[str, Any]]
    
    # Routing & Execution
    selected_provider: Optional[str]
    selected_model: Optional[str]
    routing_reason: Optional[str]
    tool_calls: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]
    tool_execution_metadata: Optional[Dict[str, Any]]

    # Response Generation
    response: Optional[str]
    response_metadata: Optional[Dict[str, Any]]
    
    # Human-in-the-loop
    requires_approval: Optional[bool]
    approval_status: Optional[str]  # "pending", "approved", "rejected"
    approval_reason: Optional[str]
    
    # Error Handling
    errors: List[str]
    warnings: List[str]
    
    # Streaming Support
    streaming_enabled: Optional[bool]
    stream_chunks: Optional[List[str]]
    request_config: Optional[Dict[str, Any]]


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration system"""
    enable_auth_gate: bool = True
    enable_safety_gate: bool = True
    enable_memory_fetch: bool = True
    enable_approval_gate: bool = False
    streaming_enabled: bool = False
    checkpoint_enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300


class LangGraphOrchestrator:
    """Main orchestration class using LangGraph for workflow management."""

    def __init__(
        self,
        config: OrchestrationConfig = None,
        *,
        auth_service: Optional[Any] = None,
        safety_service: Optional[DistilBertService] = None,
        memory_service: Optional[Any] = None,
        decision_engine: Optional[DecisionEngine] = None,
        tool_service: Optional[ToolService] = None,
        llm_router: Optional[LLMRouter] = None,
        profile_manager: Optional[ProfileManager] = None,
        context_manager: Optional[ContextManager] = None,
    ):
        self.config = config or OrchestrationConfig()
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
        self._decision_engine: DecisionEngine = decision_engine or DecisionEngine()
        self._tool_service: Optional[ToolService] = tool_service
        self._llm_router: LLMRouter = llm_router or LLMRouter()
        self._profile_manager: ProfileManager = profile_manager or ProfileManager()

        # Track fallback resolutions so we only warn once per dependency.
        self._memory_resolution_failed = False
        self._tool_resolution_failed = False

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

    @staticmethod
    def _serialize_user_account(user: Any) -> Optional[Dict[str, Any]]:
        """Normalise user objects (dataclasses or dicts) into dictionaries."""

        if user is None:
            return None

        if isinstance(user, dict):
            return user

        try:
            return user_account_to_dict(user)
        except Exception:
            if hasattr(user, "__dict__"):
                return {k: getattr(user, k) for k in dir(user) if not k.startswith("_")}
        return None

    @staticmethod
    def _derive_permissions(user_profile: Dict[str, Any]) -> Dict[str, bool]:
        """Map user roles to orchestrator permissions."""

        roles = {role.lower() for role in user_profile.get("roles", [])}
        is_active = user_profile.get("is_active", True)

        return {
            "chat": is_active,
            "tools": bool(roles.intersection({"admin", "developer", "power_user"})),
            "model_management": "admin" in roles,
            "analytics": bool(roles.intersection({"admin", "analyst"})),
        }

    def _ensure_safety_service(self) -> DistilBertService:
        """Lazy instantiate the safety service."""

        if self._safety_service is None:
            self._safety_service = DistilBertService()
        return self._safety_service

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
            from ai_karen_engine.core.service_registry import get_memory_service  # Lazy import

            self._memory_service = await get_memory_service()
        except Exception as exc:  # pragma: no cover - optional dependency
            if not self._memory_resolution_failed:
                logger.warning("Memory service unavailable: %s", exc)
            try:
                self._memory_service = WebUIMemoryService()
                logger.info("Fell back to direct WebUIMemoryService initialization")
            except Exception as fallback_exc:  # pragma: no cover - optional dependency
                logger.warning("Direct memory service fallback unavailable: %s", fallback_exc)
                self._memory_resolution_failed = True
                self._memory_service = None

        return self._memory_service

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

    @staticmethod
    def _message_to_history_entry(message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain messages into serialisable history entries."""

        role = "system"
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"

        return {
            "role": role,
            "content": getattr(message, "content", str(message)),
            "type": message.__class__.__name__,
        }
        
    def _build_graph(self):
        """Build the orchestration graph with all nodes and edges"""
        workflow = StateGraph(OrchestrationState)
        
        # Add nodes
        workflow.add_node("auth_gate", self._auth_gate)
        workflow.add_node("safety_gate", self._safety_gate)
        workflow.add_node("memory_fetch", self._memory_fetch)
        workflow.add_node("intent_detect", self._intent_detect)
        workflow.add_node("planner", self._planner)
        workflow.add_node("router_select", self._router_select)
        workflow.add_node("tool_exec", self._tool_exec)
        workflow.add_node("response_synth", self._response_synth)
        workflow.add_node("approval_gate", self._approval_gate)
        workflow.add_node("memory_write", self._memory_write)
        
        # Define the flow
        workflow.add_edge(START, "auth_gate")
        
        # Conditional edges based on configuration
        if self.config.enable_auth_gate:
            workflow.add_conditional_edges(
                "auth_gate",
                self._should_continue_after_auth,
                {
                    "continue": "safety_gate" if self.config.enable_safety_gate else "memory_fetch",
                    "reject": END
                }
            )
        else:
            workflow.add_edge("auth_gate", "safety_gate" if self.config.enable_safety_gate else "memory_fetch")
            
        if self.config.enable_safety_gate:
            workflow.add_conditional_edges(
                "safety_gate",
                self._should_continue_after_safety,
                {
                    "continue": "memory_fetch" if self.config.enable_memory_fetch else "intent_detect",
                    "reject": END,
                    "review": "approval_gate"
                }
            )
        
        if self.config.enable_memory_fetch:
            workflow.add_edge("memory_fetch", "intent_detect")
        
        workflow.add_edge("intent_detect", "planner")
        workflow.add_edge("planner", "router_select")
        workflow.add_edge("router_select", "tool_exec")
        workflow.add_edge("tool_exec", "response_synth")
        
        if self.config.enable_approval_gate:
            workflow.add_conditional_edges(
                "response_synth",
                self._should_require_approval,
                {
                    "approve": "memory_write",
                    "review": "approval_gate"
                }
            )
            workflow.add_conditional_edges(
                "approval_gate",
                self._check_approval_status,
                {
                    "approved": "memory_write",
                    "rejected": END,
                    "pending": "approval_gate"  # Wait for human input
                }
            )
        else:
            workflow.add_edge("response_synth", "memory_write")
            
        workflow.add_edge("memory_write", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
    async def _auth_gate(self, state: OrchestrationState) -> OrchestrationState:
        """Authentication and authorization gate"""
        logger.info(f"Auth gate processing for user: {state.get('user_id')}")

        try:
            errors = state.setdefault("errors", [])
            warnings = state.setdefault("warnings", [])
            service = await self._ensure_auth_service()
            auth_context = state.get("auth_context") or {}
            token = (
                auth_context.get("access_token")
                or auth_context.get("token")
                or state.get("access_token")
            )

            user: Optional[Any] = None

            if service and token:
                if hasattr(service, "validate_token"):
                    user = await service.validate_token(token)
                elif hasattr(service, "verify_token"):
                    user = await service.verify_token(token)

            if user is None and service and state.get("user_id"):
                if hasattr(service, "get_user"):
                    user = await service.get_user(state["user_id"])

            user_profile = self._serialize_user_account(user)

            # Fall back to legacy behaviour when auth service is unavailable
            allow_anonymous = bool(auth_context.get("allow_anonymous"))
            if user_profile is None and state.get("user_id") and (not service or allow_anonymous):
                if allow_anonymous:
                    warnings.append("Anonymous copilot access enabled; granting limited chat access")
                else:
                    warnings.append("Auth service unavailable; granting limited chat access")
                user_profile = {
                    "user_id": state["user_id"],
                    "email": state.get("user_id"),
                    "roles": ["user"],
                    "is_active": True,
                }

            if user_profile:
                state["user_profile"] = user_profile
                state["auth_status"] = (
                    "authenticated" if user_profile.get("is_active", True) else "failed"
                )
                state["user_permissions"] = self._derive_permissions(user_profile)
                tenant_id = (
                    user_profile.get("tenant_id")
                    or state.get("tenant_id")
                    or "default"
                )
                state["tenant_id"] = tenant_id
                auth_context["last_validated_at"] = datetime.now(timezone.utc).isoformat()
                if token:
                    auth_context["token_present"] = True
                state["auth_context"] = auth_context

                if state["auth_status"] != "authenticated":
                    errors.append("Account is inactive")
            else:
                state["auth_status"] = "failed"
                errors.append("Authentication required")

        except Exception as e:
            logger.error(f"Auth gate error: {e}")
            state["auth_status"] = "failed"
            state.setdefault("errors", []).append(f"Authentication error: {str(e)}")
            
        return state
    
    async def _safety_gate(self, state: OrchestrationState) -> OrchestrationState:
        """Safety and guardrails gate"""
        logger.info("Safety gate processing")

        try:
            errors = state.setdefault("errors", [])
            warnings = state.setdefault("warnings", [])
            messages = state.get("messages", [])

            if not messages:
                state["safety_status"] = "safe"
                state["safety_evaluation"] = {"reason": "no_messages"}
                return state

            last_message = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

            profile = self._profile_manager.get_active_profile()
            guardrails: Optional[Guardrails] = getattr(profile, "guardrails", None)

            if guardrails and not guardrails.content_filtering:
                state["safety_status"] = "safe"
                state["safety_evaluation"] = {"reason": "guardrails_disabled"}
                return state

            safety_service = self._ensure_safety_service()
            evaluation: SafetyResult = await safety_service.filter_safety(last_message)
            state["safety_evaluation"] = asdict(evaluation)

            if not evaluation.is_safe and evaluation.flagged_categories:
                state["safety_status"] = "review_required"
                state["safety_flags"] = evaluation.flagged_categories
                state["requires_approval"] = True
                warnings.append(
                    "Safety service flagged content for review: "
                    + ", ".join(evaluation.flagged_categories)
                )
            elif evaluation.is_safe:
                state["safety_status"] = "safe"
                state["safety_flags"] = []
            else:
                state["safety_status"] = "unsafe"
                errors.append("Content failed safety evaluation")

        except Exception as e:
            logger.error(f"Safety gate error: {e}")
            state["safety_status"] = "unsafe"
            state["errors"].append(f"Safety check error: {str(e)}")
            
        return state
    
    async def _memory_fetch(self, state: OrchestrationState) -> OrchestrationState:
        """Memory and context fetching"""
        logger.info("Memory fetch processing")

        try:
            errors = state.setdefault("errors", [])
            warnings = state.setdefault("warnings", [])
            messages = state.get("messages", [])
            conversation_history = [
                self._message_to_history_entry(message) for message in messages
            ]

            state["conversation_history"] = conversation_history

            if not messages:
                state["memory_context"] = {
                    "conversation_history": [],
                    "context_summary": "No prior context",
                    "memories": [],
                }
                return state

            context_manager = await self._ensure_context_manager()

            user_profile = state.get("user_profile") or {}
            user_settings = user_profile.get("preferences", {})
            prompt = conversation_history[-1]["content"]

            context = await context_manager.build_context(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                prompt=prompt,
                conversation_history=conversation_history,
                user_settings=user_settings,
                memories=None,
            )

            state["memory_context"] = context
            if isinstance(context, dict) and context.get("memories"):
                state.setdefault("warnings", []).append(
                    f"Loaded {len(context['memories'])} contextual memories"
                )

        except Exception as e:
            logger.error(f"Memory fetch error: {e}")
            errors = state.setdefault("errors", [])
            errors.append(f"Memory fetch error: {str(e)}")

        return state
    
    async def _intent_detect(self, state: OrchestrationState) -> OrchestrationState:
        """Intent detection and classification"""
        logger.info("Intent detection processing")

        try:
            messages = state.get("messages", [])
            if not messages:
                state["detected_intent"] = "unknown"
                state["intent_confidence"] = 0.0
                state["intent_analysis"] = {"reason": "no_messages"}
                return state

            prompt = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
            context = state.get("memory_context") or {}

            analysis = await self._decision_engine.analyze_intent(prompt, context)
            state["intent_analysis"] = analysis
            state["detected_intent"] = analysis.get("primary_intent", analysis.get("intent", "unknown"))
            state["intent_confidence"] = analysis.get("confidence", 0.0)
            reasoning_metadata = analysis.get("metadata", {}) if isinstance(analysis, dict) else {}
            if reasoning_metadata:
                state.setdefault("warnings", []).extend(
                    [
                        warning
                        for warning in [
                            f"Reasoning identified knowledge gaps: {', '.join(reasoning_metadata.get('knowledge_gaps', [])[:3])}"
                            if reasoning_metadata.get("knowledge_gaps")
                            else None
                        ]
                        if warning
                    ]
                )

            suggested_tools = analysis.get("suggested_tools", []) or []
            entities = analysis.get("entities", []) or []
            tool_calls: List[Dict[str, Any]] = []

            for tool_name in suggested_tools:
                parameters: Dict[str, Any] = {}
                for entity in entities:
                    entity_type = (entity.get("type") or "").lower()
                    value = entity.get("value")
                    if not value:
                        continue
                    if entity_type == "location":
                        parameters.setdefault("location", value)
                    elif entity_type == "book":
                        parameters.setdefault("book_title", value)
                    elif entity_type == "time":
                        parameters.setdefault("time_reference", value)

                tool_calls.append({"tool": tool_name, "parameters": parameters})

            state["tool_calls"] = tool_calls or None

            if analysis.get("requires_clarification"):
                state.setdefault("warnings", []).append(
                    "Intent engine suggests clarifying the user request"
                )

        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            state["errors"].append(f"Intent detection error: {str(e)}")

        return state

    def _compose_execution_plan(
        self,
        intent: str,
        analysis: Optional[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        safety_status: str,
    ) -> Dict[str, Any]:
        """Create a structured execution plan used by the planner and dry-run analysis."""

        analysis = analysis or {}
        execution_plan: Dict[str, Any] = {
            "intent": intent,
            "steps": [],
            "tools_required": [call["tool"] for call in tool_calls],
            "estimated_time_seconds": 2,
            "complexity": "low",
            "metadata": {
                "confidence": analysis.get("confidence", 0.0),
                "requires_clarification": analysis.get("requires_clarification", False),
                "safety_status": safety_status,
            },
        }

        if intent in {"code_generation", "email_compose"}:
            execution_plan["steps"] = [
                "understand_requirements",
                "draft_solution",
                "review_and_refine",
            ]
            execution_plan["complexity"] = "medium"
            execution_plan["estimated_time_seconds"] = 6
        elif intent in {"weather_query", "time_query", "information_retrieval", "book_query"}:
            execution_plan["steps"] = [
                "gather_context",
                "invoke_tools" if tool_calls else "search_internal_memory",
                "synthesize_answer",
            ]
            execution_plan["complexity"] = "low"
            execution_plan["estimated_time_seconds"] = 4
        else:
            execution_plan["steps"] = ["analyze_prompt", "compose_response"]

        if safety_status == "review_required":
            execution_plan["requires_human_review"] = True

        return execution_plan

    async def _planner(self, state: OrchestrationState) -> OrchestrationState:
        """Execution planning based on intent"""
        logger.info("Planning processing")

        try:
            intent = state.get("detected_intent", "general_chat") or "general_chat"
            analysis = state.get("intent_analysis") or {}
            tool_calls = state.get("tool_calls") or []
            safety_status = state.get("safety_status", "safe")

            execution_plan = self._compose_execution_plan(
                intent,
                analysis,
                tool_calls,
                safety_status,
            )
            state["execution_plan"] = execution_plan

        except Exception as e:
            logger.error(f"Planning error: {e}")
            state["errors"].append(f"Planning error: {str(e)}")

        return state
    
    async def _router_select(self, state: OrchestrationState) -> OrchestrationState:
        """LLM provider and model selection"""
        logger.info("Router selection processing")

        try:
            messages = state.get("messages", [])
            if not messages:
                state["selected_provider"] = "fallback"
                state["selected_model"] = "kari-fallback-v1"
                state["routing_reason"] = "No conversation context available"
                return state

            conversation_history = state.get("conversation_history") or [
                self._message_to_history_entry(message) for message in messages
            ]
            memory_context = state.get("memory_context") or {}
            plan = state.get("execution_plan", {})
            tool_calls = state.get("tool_calls") or []

            profile = self._profile_manager.get_active_profile()
            provider_preferences = (
                asdict(profile.provider_preferences)
                if profile and getattr(profile, "provider_preferences", None)
                else {}
            )
            request_config = state.get("request_config") or {}
            if isinstance(request_config, dict):
                preferred_provider = request_config.get("preferred_llm_provider")
                preferred_model = request_config.get("preferred_model")
                if preferred_provider and not provider_preferences.get("preferred_llm_provider"):
                    provider_preferences["preferred_llm_provider"] = preferred_provider
                if preferred_model and not provider_preferences.get("preferred_model"):
                    provider_preferences["preferred_model"] = preferred_model
            explicit_preferred_provider = (
                request_config.get("preferred_llm_provider")
                if isinstance(request_config, dict)
                else None
            )
            explicit_preferred_model = (
                request_config.get("preferred_model")
                if isinstance(request_config, dict)
                else None
            )
            preferred_model_name: Optional[str] = None
            if explicit_preferred_model:
                preferred_model_name = str(explicit_preferred_model)
            elif not explicit_preferred_provider:
                profile_chat_preference = provider_preferences.get("chat")
                if profile_chat_preference:
                    preferred_model_name = str(profile_chat_preference)

            request = ChatRequest(
                message=conversation_history[-1]["content"],
                context={
                    "conversation": conversation_history,
                    "plan": plan,
                    "safety": state.get("safety_evaluation"),
                },
                tools=[call["tool"] for call in tool_calls],
                memory_context=memory_context.get("context_summary"),
                user_preferences=provider_preferences,
                preferred_model=preferred_model_name,
                conversation_id=state.get("session_id"),
                stream=bool(state.get("streaming_enabled")),
            )

            provider_selection = await self._llm_router.select_provider(
                request,
                user_preferences=provider_preferences,
            )

            if provider_selection:
                provider_name, model_name = provider_selection
                state["selected_provider"] = provider_name
                state["selected_model"] = model_name
                state["routing_reason"] = (
                    "Selected via LLM router policy"
                )
            else:
                state["selected_provider"] = "fallback"
                state["selected_model"] = "kari-fallback-v1"
                state["routing_reason"] = "Router returned no provider; using fallback"

        except Exception as e:
            logger.error(f"Router selection error: {e}")
            state["errors"].append(f"Router selection error: {str(e)}")

        return state
    
    async def _tool_exec(self, state: OrchestrationState) -> OrchestrationState:
        """Tool execution based on plan"""
        logger.info("Tool execution processing")

        try:
            tool_calls = state.get("tool_calls") or []
            plan = state.get("execution_plan", {})

            if not tool_calls:
                state["tool_results"] = []
                state["tool_execution_metadata"] = {"executed": 0}
                return state

            tool_service = await self._ensure_tool_service()
            tool_results: List[Dict[str, Any]] = []
            execution_metadata = {"executed": 0, "failed": 0}

            for call in tool_calls:
                tool_name = call.get("tool")
                parameters = call.get("parameters", {})

                if not tool_name:
                    continue

                tool_input = ToolInput(
                    tool_name=tool_name,
                    parameters=parameters,
                    user_context={
                        "intent": state.get("detected_intent"),
                        "plan": plan,
                    },
                    user_id=state.get("user_id"),
                    session_id=state.get("session_id"),
                )

                execution_metadata["executed"] += 1

                try:
                    output: ToolOutput = await tool_service.execute_tool(tool_input)
                    tool_results.append(output.model_dump())
                    if not output.success:
                        execution_metadata["failed"] += 1
                except Exception as exc:
                    execution_metadata["failed"] += 1
                    tool_results.append(
                        {
                            "tool": tool_name,
                            "success": False,
                            "error": str(exc),
                            "parameters": parameters,
                        }
                    )
                    state.setdefault("warnings", []).append(
                        f"Tool '{tool_name}' failed: {exc}"
                    )

            state["tool_results"] = tool_results
            state["tool_execution_metadata"] = execution_metadata

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            state["errors"].append(f"Tool execution error: {str(e)}")

        return state
    
    async def _response_synth(self, state: OrchestrationState) -> OrchestrationState:
        """Response synthesis and generation"""
        logger.info("Response synthesis processing")
        
        try:
            messages = state.get("messages", [])
            if not messages:
                state["response"] = "I'm ready whenever you are."
                state.setdefault("warnings", []).append(
                    "No user message available for response synthesis"
                )
                return state

            conversation_history = state.get("conversation_history") or [
                self._message_to_history_entry(message) for message in messages
            ]
            memory_context = state.get("memory_context") or {}
            tool_results = state.get("tool_results", [])
            provider_preferences = {}
            profile = self._profile_manager.get_active_profile()
            if profile and getattr(profile, "provider_preferences", None):
                provider_preferences = asdict(profile.provider_preferences)

            request = ChatRequest(
                message=conversation_history[-1]["content"],
                context={
                    "conversation": conversation_history,
                    "plan": state.get("execution_plan"),
                    "tool_results": tool_results,
                },
                tools=[result.get("tool") for result in tool_results if isinstance(result, dict)],
                memory_context=memory_context.get("context_summary"),
                user_preferences=provider_preferences,
                preferred_model=state.get("selected_model"),
                conversation_id=state.get("session_id"),
                stream=bool(state.get("streaming_enabled")),
            )

            chunks: List[str] = []
            async for chunk in self._llm_router.process_chat_request(
                request,
                user_preferences=provider_preferences,
            ):
                if chunk is None:
                    continue
                normalized_chunk = str(chunk).strip()
                if normalized_chunk:
                    chunks.append(normalized_chunk)

            if not chunks:
                chunks.append(
                    "I'm here and ready to assist, but I didn't receive any content to respond to."
                )

            response_text = "".join(chunks).strip()

            state["response"] = response_text
            state["response_metadata"] = {
                "provider": state.get("selected_provider", "fallback"),
                "model": state.get("selected_model", "unknown"),
                "tool_results": len(tool_results),
                "chunks": len(chunks),
                "reasoning": (
                    state.get("intent_analysis", {}).get("metadata", {})
                    if isinstance(state.get("intent_analysis"), dict)
                    else {}
                ),
            }

            if state.get("streaming_enabled"):
                state["stream_chunks"] = chunks

            state.setdefault("messages", []).append(AIMessage(content=response_text))
            
        except Exception as e:
            logger.error(f"Response synthesis error: {e}")
            state["errors"].append(f"Response synthesis error: {str(e)}")
            
        return state
    
    async def _approval_gate(self, state: OrchestrationState) -> OrchestrationState:
        """Human approval gate for sensitive operations"""
        logger.info("Approval gate processing")

        try:
            requires_approval = bool(state.get("requires_approval"))
            safety_status = state.get("safety_status")
            plan = state.get("execution_plan") or {}

            if safety_status == "review_required":
                requires_approval = True

            if plan.get("requires_human_review"):
                requires_approval = True

            state["requires_approval"] = requires_approval

            if requires_approval:
                state["approval_status"] = "pending"
                state["approval_reason"] = plan.get(
                    "review_reason",
                    "Flagged by safety or planning policies",
                )
            else:
                state["approval_status"] = "approved"
                state["approval_reason"] = "Policy auto-approval"

        except Exception as e:
            logger.error(f"Approval gate error: {e}")
            state["errors"].append(f"Approval gate error: {str(e)}")

        return state
    
    async def _memory_write(self, state: OrchestrationState) -> OrchestrationState:
        """Memory writing and conversation storage"""
        logger.info("Memory write processing")
        
        try:
            memory_write_timeout = float(
                os.getenv("LANGGRAPH_MEMORY_WRITE_TIMEOUT_SECONDS", "2.0")
            )
            memory_service = await asyncio.wait_for(
                self._resolve_memory_service(),
                timeout=memory_write_timeout,
            )
            if not memory_service or not hasattr(memory_service, "store_web_ui_memory"):
                state.setdefault("warnings", []).append(
                    "Memory service unavailable; skipping persistence"
                )
                return state

            response = state.get("response")
            if not response:
                return state

            tenant_id = state.get("tenant_id") or "default"
            user_id = state.get("user_id") or "anonymous"
            session_id = state.get("session_id")

            metadata = {
                "provider": state.get("selected_provider"),
                "model": state.get("selected_model"),
                "intent": state.get("detected_intent"),
                "tool_execution": state.get("tool_execution_metadata"),
                "safety": state.get("safety_evaluation"),
            }

            await asyncio.wait_for(
                memory_service.store_web_ui_memory(
                    tenant_id=tenant_id,
                    content=response,
                    user_id=user_id,
                    ui_source=UISource.API,
                    session_id=session_id,
                    conversation_id=session_id,
                    memory_type=MemoryType.CONVERSATION,
                    tags=["conversation", state.get("detected_intent", "general_chat")],
                    importance_score=5,
                    ai_generated=True,
                    metadata=metadata,
                ),
                timeout=memory_write_timeout,
            )

        except asyncio.TimeoutError:
            logger.warning("Memory write timed out; skipping persistence")
            state.setdefault("warnings", []).append(
                "Memory write timed out; skipping persistence"
            )
        except Exception as e:
            logger.error(f"Memory write error: {e}")
            state["errors"].append(f"Memory write error: {str(e)}")

        return state
    
    # Conditional edge functions
    def _should_continue_after_auth(self, state: OrchestrationState) -> str:
        """Determine if processing should continue after auth gate"""
        auth_status = state.get("auth_status")
        return "continue" if auth_status == "authenticated" else "reject"
    
    def _should_continue_after_safety(self, state: OrchestrationState) -> str:
        """Determine if processing should continue after safety gate"""
        safety_status = state.get("safety_status")
        if safety_status == "safe":
            return "continue"
        elif safety_status == "review_required":
            return "review"
        else:
            return "reject"
    
    def _should_require_approval(self, state: OrchestrationState) -> str:
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
    
    def _check_approval_status(self, state: OrchestrationState) -> str:
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

        user = user or {}
        context = context or {}

        session_identifier = session_id or context.get("session_id") or f"dryrun-{uuid.uuid4()}"
        user_id = user.get("id") or user.get("user_id") or "anonymous"
        tenant_id = (
            user.get("tenant_id")
            or user.get("organization_id")
            or context.get("tenant_id")
            or "default"
        )

        conversation_history = context.get("conversation_history")
        if not isinstance(conversation_history, list):
            conversation_history = []

        sanitized_history: List[Dict[str, Any]] = []
        for entry in conversation_history:
            if isinstance(entry, dict) and "content" in entry:
                sanitized_history.append(entry)

        user_settings = context.get("user_settings")
        if not isinstance(user_settings, dict):
            user_settings = {}

        memories = context.get("memories")
        if not isinstance(memories, list):
            memories = None

        context_manager = await self._ensure_context_manager()
        built_context = await context_manager.build_context(
            user_id=user_id,
            session_id=session_identifier,
            prompt=message,
            conversation_history=sanitized_history,
            user_settings=user_settings,
            memories=memories,
        )

        intent_analysis = await self._decision_engine.analyze_intent(message, built_context)

        suggested_tools = intent_analysis.get("suggested_tools", []) or []
        entities = intent_analysis.get("entities", []) or []
        tool_calls: List[Dict[str, Any]] = []

        for tool_name in suggested_tools:
            parameters: Dict[str, Any] = {}
            for entity in entities:
                entity_type = (entity.get("type") or "").lower()
                value = entity.get("value")
                if not value:
                    continue
                if entity_type == "location":
                    parameters.setdefault("location", value)
                elif entity_type == "book":
                    parameters.setdefault("book_title", value)
                elif entity_type == "time":
                    parameters.setdefault("time_reference", value)

            tool_calls.append({"tool": tool_name, "parameters": parameters})

        safety_service = self._ensure_safety_service()
        safety_result: SafetyResult = await safety_service.filter_safety(message)
        if not safety_result.is_safe and safety_result.flagged_categories:
            safety_status = "review_required"
        elif safety_result.is_safe:
            safety_status = "safe"
        else:
            safety_status = "unsafe"

        execution_plan = self._compose_execution_plan(
            intent_analysis.get("primary_intent", "conversation"),
            intent_analysis,
            tool_calls,
            safety_status,
        )

        provider_preferences = {}
        for candidate in (
            context.get("llm_preferences"),
            context.get("user_preferences"),
            user.get("llm_preferences"),
            user_settings.get("llm_preferences") if isinstance(user_settings, dict) else None,
        ):
            if isinstance(candidate, dict):
                provider_preferences.update(candidate)

        llm_request = ChatRequest(
            message=message,
            context={
                "conversation": sanitized_history,
                "plan": execution_plan,
                "safety": {
                    "status": safety_status,
                    "score": safety_result.safety_score,
                    "flags": safety_result.flagged_categories,
                },
                "tenant_id": tenant_id,
            },
            tools=[call["tool"] for call in tool_calls] or None,
            memory_context=built_context.get("context_summary") if isinstance(built_context, dict) else None,
            user_preferences=provider_preferences or None,
            preferred_model=provider_preferences.get("chat") if isinstance(provider_preferences, dict) else None,
            conversation_id=session_identifier,
            stream=False,
        )

        provider_selection = await self._llm_router.select_provider(
            llm_request,
            user_preferences=provider_preferences,
        )

        if provider_selection:
            predicted_provider, predicted_model = provider_selection
            routing_reason = f"Selected via {self._llm_router.routing_policy.value} policy"
            routing_confidence = 0.9
        else:
            predicted_provider, predicted_model = "fallback", "kari-fallback-v1"
            routing_reason = "Router returned no healthy provider; using fallback"
            routing_confidence = 0.2

        approval_required = bool(
            execution_plan.get("requires_human_review")
            or not safety_result.is_safe
            or execution_plan.get("complexity") == "high"
        )

        memories_considered = 0
        if isinstance(built_context, dict):
            memories_data = built_context.get("memories")
            if isinstance(memories_data, list):
                memories_considered = len(memories_data)

        analysis_timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "session_id": session_identifier,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "message": message,
            "predicted_intent": intent_analysis.get("primary_intent", "conversation"),
            "intent_confidence": intent_analysis.get("confidence", 0.0),
            "routing_reason": routing_reason,
            "routing_confidence": routing_confidence,
            "predicted_provider": predicted_provider,
            "predicted_model": predicted_model,
            "estimated_processing_time": execution_plan.get("estimated_time_seconds", 0.0),
            "required_tools": [call["tool"] for call in tool_calls],
            "tool_parameters": tool_calls,
            "execution_plan": execution_plan,
            "safety_assessment": {
                "status": safety_status,
                "score": safety_result.safety_score,
                "flagged_categories": safety_result.flagged_categories,
                "used_fallback": safety_result.used_fallback,
            },
            "approval_required": approval_required,
            "context_summary": (
                built_context.get("context_summary")
                if isinstance(built_context, dict)
                else None
            ),
            "memories_considered": memories_considered,
            "timestamp": analysis_timestamp,
            "user_preferences": provider_preferences,
        }

    async def process(self,
                     messages: List[BaseMessage],
                     user_id: str,
                     session_id: str = None,
                     config: Dict[str, Any] = None) -> Dict[str, Any]:
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

        initial_state: OrchestrationState = {
            "messages": messages,
            "user_id": user_id,
            "session_id": session_id,
            "tenant_id": None,
            "auth_status": None,
            "user_permissions": None,
            "auth_context": cast(Dict[str, Any], runtime_config.get("auth_context") or {}),
            "user_profile": None,
            "safety_status": None,
            "safety_flags": None,
            "safety_evaluation": None,
            "memory_context": None,
            "conversation_history": None,
            "detected_intent": None,
            "intent_confidence": None,
            "execution_plan": None,
            "intent_analysis": None,
            "selected_provider": None,
            "selected_model": None,
            "routing_reason": None,
            "tool_calls": None,
            "tool_results": None,
            "tool_execution_metadata": None,
            "response": None,
            "response_metadata": None,
            "requires_approval": None,
            "approval_status": None,
            "approval_reason": None,
            "errors": [],
            "warnings": [],
            "streaming_enabled": bool(runtime_config.get("streaming_enabled", self.config.streaming_enabled)),
            "stream_chunks": None,
            "request_config": runtime_config,
        }
        
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
    
    async def stream_process(self, 
                           messages: List[BaseMessage], 
                           user_id: str, 
                           session_id: str = None,
                           config: Dict[str, Any] = None):
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

        initial_state: OrchestrationState = {
            "messages": messages,
            "user_id": user_id,
            "session_id": session_id,
            "tenant_id": None,
            "auth_status": None,
            "user_permissions": None,
            "auth_context": cast(Dict[str, Any], runtime_config.get("auth_context") or {}),
            "user_profile": None,
            "safety_status": None,
            "safety_flags": None,
            "safety_evaluation": None,
            "memory_context": None,
            "conversation_history": None,
            "detected_intent": None,
            "intent_confidence": None,
            "execution_plan": None,
            "intent_analysis": None,
            "selected_provider": None,
            "selected_model": None,
            "routing_reason": None,
            "tool_calls": None,
            "tool_results": None,
            "tool_execution_metadata": None,
            "response": None,
            "response_metadata": None,
            "requires_approval": None,
            "approval_status": None,
            "approval_reason": None,
            "errors": [],
            "warnings": [],
            "streaming_enabled": bool(runtime_config.get("streaming_enabled", True)),
            "stream_chunks": [],
            "request_config": runtime_config,
        }
        
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

    async def update_configuration(self, updates: Dict[str, Any]) -> OrchestrationConfig:
        """Update orchestrator configuration and rebuild the graph."""

        if not updates:
            return self.config

        allowed_fields = set(OrchestrationConfig.__annotations__.keys())
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
            sum(latency_samples) / len(latency_samples)
            if latency_samples
            else 0.0
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
        index = max(0, min(len(ordered) - 1, int(round(percentile * (len(ordered) - 1)))))
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
def create_orchestrator(config: OrchestrationConfig = None) -> LangGraphOrchestrator:
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
