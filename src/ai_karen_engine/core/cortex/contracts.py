from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class ReasoningDepth(str, Enum):
    NONE = "none"
    LIGHT = "light"
    STANDARD = "standard"
    DEEP = "deep"


class RouteFamily(str, Enum):
    CHAT = "chat"
    SEARCH = "search"
    MEMORY = "memory"
    TOOL = "tool"
    AGENT = "agent"
    REASONING = "reasoning"
    ADMIN = "admin"
    DEGRADED = "degraded"


class ExecutionMode(str, Enum):
    DIRECT = "direct"
    LANGGRAPH = "langgraph"
    DEGRADED = "degraded"


@dataclass(slots=True)
class IntentSignal:
    primary_intent: str
    secondary_intents: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    confidence: float = 0.0
    category: str = "general"
    requested_modality: str = "text"


@dataclass(slots=True)
class PredictorSignal:
    ambiguity_score: float = 0.0
    complexity_score: float = 0.0
    tool_likelihood: float = 0.0
    memory_relevance: float = 0.0
    multi_step_likelihood: float = 0.0
    degraded_risk: float = 0.0


@dataclass(slots=True)
class KireSignal:
    requires_reasoning: bool
    reasoning_depth: ReasoningDepth
    reasoning_modes: List[str] = field(default_factory=list)
    strategy_hint: Optional[str] = None
    should_use_memory: bool = True
    should_use_tools: bool = False
    should_use_retrieval_reasoning: bool = False
    should_use_causal_reasoning: bool = False
    should_use_graph_reasoning: bool = False
    should_self_refine: bool = False
    should_verify: bool = False


@dataclass(slots=True)
class RoutingDecision:
    route_family: RouteFamily
    execution_mode: ExecutionMode
    target_graph: str = "default_chat_graph"
    target_service: Optional[str] = None
    target_plugin: Optional[str] = None
    target_agent: Optional[str] = None
    allow_reasoning: bool = False
    allow_tools: bool = False
    allow_memory_read: bool = True
    allow_memory_write: bool = True
    require_approval_gate: bool = False


@dataclass(slots=True)
class UserContext:
    user_id: str
    tenant_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    thread_id: Optional[str] = None


@dataclass(slots=True)
class RuntimeRequest:
    message: str
    user: UserContext
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CortexOutput:
    intent: IntentSignal
    predictors: PredictorSignal
    kire: KireSignal
    routing: RoutingDecision
    correlation_id: str
    audit_tags: List[str] = field(default_factory=list)


@dataclass(slots=True)
class OrchestrationInput:
    message: str
    user: UserContext
    metadata: Dict[str, Any]
    cortex: CortexOutput


@dataclass(slots=True)
class ReasoningRequest:
    message: str
    user: UserContext
    memory_context: Dict[str, Any]
    tool_context: Dict[str, Any]
    intent: IntentSignal
    predictors: PredictorSignal
    kire: KireSignal
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReasoningResult:
    summary: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    confidence: float = 0.0
    verification_notes: List[str] = field(default_factory=list)
    refined_answer: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OrchestrationResult:
    final_text: str
    reasoning_result: Optional[ReasoningResult] = None
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    memory_reads: List[Dict[str, Any]] = field(default_factory=list)
    memory_writes: List[Dict[str, Any]] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class IntentEngine(Protocol):
    def detect(self, request: RuntimeRequest) -> IntentSignal:
        ...


class PredictorEngine(Protocol):
    def predict(self, request: RuntimeRequest, intent: IntentSignal) -> PredictorSignal:
        ...


class KireEngine(Protocol):
    def enrich(
        self,
        request: RuntimeRequest,
        intent: IntentSignal,
        predictors: PredictorSignal,
    ) -> KireSignal:
        ...


class RbacValidator(Protocol):
    def validate(
        self,
        user: UserContext,
        intent: IntentSignal,
        routing: RoutingDecision,
    ) -> None:
        ...


class RoutingEngine(Protocol):
    def decide(
        self,
        request: RuntimeRequest,
        intent: IntentSignal,
        predictors: PredictorSignal,
        kire: KireSignal,
    ) -> RoutingDecision:
        ...


class KROOrchestrator(Protocol):
    def run(self, request: ReasoningRequest) -> ReasoningResult:
        ...


class LangGraphRuntime(Protocol):
    def run(self, orchestration_input: OrchestrationInput) -> OrchestrationResult:
        ...


class CorrelationIdFactory:
    def create(self, request: RuntimeRequest) -> str:
        base = request.user.user_id or "anonymous"
        thread = request.user.thread_id or "no-thread"
        return f"cx-{base}-{thread}"
