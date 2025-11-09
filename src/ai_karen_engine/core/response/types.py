"""
Unified Response Types for AI-Karen

This module provides unified types for the response generation system,
integrating with memory and reasoning modules.

Aligns with:
- Memory module (MemoryEntry, MemoryQuery)
- Reasoning module (CognitiveOrchestrator, SoftReasoningEngine)
- Response orchestrator pipeline

Author: AI-Karen Core Team
Version: 1.0.0 (Unified Architecture)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# ===================================
# ENUMS AND CLASSIFICATIONS
# ===================================

class IntentType(str, Enum):
    """
    User intent classification.

    Based on common patterns in conversational AI.
    """
    GENERAL_ASSIST = "general_assist"
    OPTIMIZE_CODE = "optimize_code"
    DEBUG_ERROR = "debug_error"
    EXPLAIN_CONCEPT = "explain_concept"
    GENERATE_CODE = "generate_code"
    REFACTOR_CODE = "refactor_code"
    TEST_CODE = "test_code"
    DOCUMENT_CODE = "document_code"
    REVIEW_CODE = "review_code"
    CHAT = "chat"
    QUESTION = "question"
    COMMAND = "command"
    FEEDBACK = "feedback"
    UNKNOWN = "unknown"


class SentimentType(str, Enum):
    """
    Sentiment classification for user input.
    """
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFUSED = "confused"
    SATISFIED = "satisfied"


class PersonaType(str, Enum):
    """
    Persona/personality modes for responses.
    """
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    CONCISE = "concise"
    DETAILED = "detailed"
    EDUCATIONAL = "educational"
    DEFAULT = "default"


class ResponseStatus(str, Enum):
    """Response generation status."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    RECALLING = "recalling"
    REASONING = "reasoning"
    GENERATING = "generating"
    FORMATTING = "formatting"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ModelType(str, Enum):
    """LLM model types."""
    LOCAL_SMALL = "local_small"      # Fast local models (< 3B params)
    LOCAL_MEDIUM = "local_medium"    # Medium local models (3-7B params)
    LOCAL_LARGE = "local_large"      # Large local models (> 7B params)
    CLOUD_FAST = "cloud_fast"        # Cloud APIs optimized for speed
    CLOUD_SMART = "cloud_smart"      # Cloud APIs optimized for quality
    HYBRID = "hybrid"                # Combination of local + cloud


class RoutingDecision(str, Enum):
    """Model routing decisions."""
    LOCAL_ONLY = "local_only"        # Use only local models
    CLOUD_PREFERRED = "cloud_preferred"  # Prefer cloud if available
    CLOUD_REQUIRED = "cloud_required"    # Require cloud model
    HYBRID_PARALLEL = "hybrid_parallel"  # Run local + cloud in parallel
    FALLBACK_TO_CLOUD = "fallback_to_cloud"  # Try local first, fallback to cloud
    FALLBACK_TO_LOCAL = "fallback_to_local"  # Try cloud first, fallback to local


# ===================================
# TYPE ALIASES
# ===================================

# Message format for LLM APIs
Message = Dict[str, str]  # {"role": "user|assistant|system", "content": "..."}
Messages = List[Message]

# Entity extracted from text
Entity = Dict[str, Any]  # {"text": "...", "type": "...", "confidence": 0.9}

# Context from memory recall
Context = Dict[str, Any]  # {"text": "...", "score": 0.9, "metadata": {...}}


# ===================================
# CORE DATA STRUCTURES
# ===================================

@dataclass
class AnalysisResult:
    """
    Result of text analysis phase.

    Combines NLP analysis (intent, sentiment, entities) with
    metadata for response generation.
    """
    # === Core Analysis ===
    intent: IntentType = IntentType.UNKNOWN
    sentiment: SentimentType = SentimentType.NEUTRAL
    entities: List[Entity] = field(default_factory=list)

    # === Metadata ===
    confidence: float = 0.0  # 0-1 confidence in analysis
    language: str = "en"
    complexity: float = 0.5  # 0-1 estimated complexity

    # === Timing ===
    analysis_time_ms: float = 0.0

    # === Additional Context ===
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intent": self.intent.value,
            "sentiment": self.sentiment.value,
            "entities": self.entities,
            "confidence": self.confidence,
            "language": self.language,
            "complexity": self.complexity,
            "analysis_time_ms": self.analysis_time_ms,
            "keywords": self.keywords,
            "topics": self.topics,
        }


@dataclass
class MemoryContext:
    """
    Context recalled from memory for response generation.

    Integrates with memory.MemoryEntry but provides
    response-specific fields.
    """
    # === Retrieved Context ===
    contexts: List[Context] = field(default_factory=list)

    # === Memory Stats ===
    total_recalled: int = 0
    avg_relevance: float = 0.0
    recall_time_ms: float = 0.0

    # === Source Information ===
    memory_types: List[str] = field(default_factory=list)  # episodic, semantic, etc.
    namespaces: List[str] = field(default_factory=list)  # short_term, long_term, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contexts": self.contexts,
            "total_recalled": self.total_recalled,
            "avg_relevance": self.avg_relevance,
            "recall_time_ms": self.recall_time_ms,
            "memory_types": self.memory_types,
            "namespaces": self.namespaces,
        }


@dataclass
class ReasoningTrace:
    """
    Trace of reasoning process.

    Integrates with reasoning.CognitiveOrchestrator to track
    reasoning steps used in response generation.
    """
    # === Reasoning Steps ===
    steps: List[Dict[str, Any]] = field(default_factory=list)

    # === Strategy Used ===
    strategy: Optional[str] = None  # analytical, intuitive, etc.
    cognitive_mode: Optional[str] = None  # fast, deliberate, etc.

    # === Metrics ===
    reasoning_time_ms: float = 0.0
    confidence: float = 0.0

    # === Integration Points ===
    used_soft_reasoning: bool = False
    used_causal_reasoning: bool = False
    used_self_refine: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "steps": self.steps,
            "strategy": self.strategy,
            "cognitive_mode": self.cognitive_mode,
            "reasoning_time_ms": self.reasoning_time_ms,
            "confidence": self.confidence,
            "used_soft_reasoning": self.used_soft_reasoning,
            "used_causal_reasoning": self.used_causal_reasoning,
            "used_self_refine": self.used_self_refine,
        }


@dataclass
class ModelSelection:
    """
    Model selection decision.

    Tracks which model(s) were selected and why.
    """
    # === Selected Model ===
    model_id: str
    model_type: ModelType
    routing_decision: RoutingDecision

    # === Selection Criteria ===
    intent: IntentType
    context_size: int  # tokens
    complexity: float

    # === Fallback Configuration ===
    fallback_model: Optional[str] = None
    timeout_ms: int = 30000

    # === Metadata ===
    selection_time_ms: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type.value,
            "routing_decision": self.routing_decision.value,
            "intent": self.intent.value,
            "context_size": self.context_size,
            "complexity": self.complexity,
            "fallback_model": self.fallback_model,
            "timeout_ms": self.timeout_ms,
            "selection_time_ms": self.selection_time_ms,
            "confidence": self.confidence,
        }


@dataclass
class GenerationMetrics:
    """
    Metrics for LLM generation.
    """
    # === Tokens ===
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # === Timing ===
    generation_time_ms: float = 0.0
    first_token_ms: Optional[float] = None

    # === Model Info ===
    model_used: str = ""
    model_type: ModelType = ModelType.LOCAL_SMALL

    # === Quality ===
    temperature: float = 0.7
    top_p: float = 1.0
    finish_reason: str = "stop"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "generation_time_ms": self.generation_time_ms,
            "first_token_ms": self.first_token_ms,
            "model_used": self.model_used,
            "model_type": self.model_type.value,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "finish_reason": self.finish_reason,
        }


@dataclass
class ResponseRequest:
    """
    Unified request for response generation.

    This is the input to the response pipeline.
    """
    # === Core Input ===
    request_id: str
    user_text: str

    # === User Context ===
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None

    # === Preferences ===
    persona: PersonaType = PersonaType.DEFAULT
    model_preference: Optional[ModelType] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

    # === UI Capabilities ===
    ui_caps: Dict[str, Any] = field(default_factory=dict)
    streaming_enabled: bool = False

    # === Metadata ===
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormattedResponse:
    """
    Final formatted response.

    This is the output of the response pipeline.
    """
    # === Core Response ===
    response_id: str
    request_id: str
    text: str  # Main response text

    # === Classification ===
    intent: IntentType
    sentiment: SentimentType
    persona: PersonaType

    # === Pipeline Trace ===
    analysis: Optional[AnalysisResult] = None
    memory_context: Optional[MemoryContext] = None
    reasoning_trace: Optional[ReasoningTrace] = None
    model_selection: Optional[ModelSelection] = None
    generation_metrics: Optional[GenerationMetrics] = None

    # === Status ===
    status: ResponseStatus = ResponseStatus.COMPLETE
    error: Optional[str] = None

    # === Timing ===
    total_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # === Optional Fields ===
    suggestions: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "text": self.text,
            "intent": self.intent.value,
            "sentiment": self.sentiment.value,
            "persona": self.persona.value,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "memory_context": self.memory_context.to_dict() if self.memory_context else None,
            "reasoning_trace": self.reasoning_trace.to_dict() if self.reasoning_trace else None,
            "model_selection": self.model_selection.to_dict() if self.model_selection else None,
            "generation_metrics": self.generation_metrics.to_dict() if self.generation_metrics else None,
            "status": self.status.value,
            "error": self.error,
            "total_time_ms": self.total_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "suggestions": self.suggestions,
            "actions": self.actions,
            "metadata": self.metadata,
        }


# ===================================
# HELPER FUNCTIONS
# ===================================

def make_request_id(prefix: str = "req") -> str:
    """Generate unique request ID."""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def make_response_id(prefix: str = "resp") -> str:
    """Generate unique response ID."""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def create_request(
    user_text: str,
    *,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    persona: PersonaType = PersonaType.DEFAULT,
    **kwargs
) -> ResponseRequest:
    """
    Factory function to create a response request.

    Args:
        user_text: User input text (required)
        user_id: Optional user ID
        tenant_id: Optional tenant ID
        persona: Response persona
        **kwargs: Additional ResponseRequest fields

    Returns:
        ResponseRequest instance
    """
    return ResponseRequest(
        request_id=make_request_id(),
        user_text=user_text,
        user_id=user_id,
        tenant_id=tenant_id,
        persona=persona,
        **kwargs
    )


def create_error_response(
    request_id: str,
    error_message: str,
    **kwargs
) -> FormattedResponse:
    """
    Create an error response.

    Args:
        request_id: Request ID that failed
        error_message: Error message
        **kwargs: Additional fields

    Returns:
        FormattedResponse with error status
    """
    return FormattedResponse(
        response_id=make_response_id(),
        request_id=request_id,
        text=f"I encountered an error: {error_message}",
        intent=IntentType.UNKNOWN,
        sentiment=SentimentType.NEUTRAL,
        persona=PersonaType.DEFAULT,
        status=ResponseStatus.FAILED,
        error=error_message,
        **kwargs
    )


# ===================================
# CONSTANTS
# ===================================

# Default timeouts (milliseconds)
DEFAULT_ANALYSIS_TIMEOUT_MS = 5000
DEFAULT_RECALL_TIMEOUT_MS = 3000
DEFAULT_REASONING_TIMEOUT_MS = 10000
DEFAULT_GENERATION_TIMEOUT_MS = 30000
DEFAULT_TOTAL_TIMEOUT_MS = 60000

# Token limits
DEFAULT_MAX_PROMPT_TOKENS = 4000
DEFAULT_MAX_COMPLETION_TOKENS = 2000
DEFAULT_MAX_TOTAL_TOKENS = 6000

# Model selection thresholds
COMPLEXITY_THRESHOLD_SMALL = 0.3  # < 0.3 = small model sufficient
COMPLEXITY_THRESHOLD_MEDIUM = 0.7  # < 0.7 = medium model sufficient
# > 0.7 = large model recommended


__all__ = [
    # Enums
    "IntentType",
    "SentimentType",
    "PersonaType",
    "ResponseStatus",
    "ModelType",
    "RoutingDecision",
    # Type aliases
    "Message",
    "Messages",
    "Entity",
    "Context",
    # Data structures
    "AnalysisResult",
    "MemoryContext",
    "ReasoningTrace",
    "ModelSelection",
    "GenerationMetrics",
    "ResponseRequest",
    "FormattedResponse",
    # Helper functions
    "make_request_id",
    "make_response_id",
    "create_request",
    "create_error_response",
    # Constants
    "DEFAULT_ANALYSIS_TIMEOUT_MS",
    "DEFAULT_RECALL_TIMEOUT_MS",
    "DEFAULT_REASONING_TIMEOUT_MS",
    "DEFAULT_GENERATION_TIMEOUT_MS",
    "DEFAULT_TOTAL_TIMEOUT_MS",
    "DEFAULT_MAX_PROMPT_TOKENS",
    "DEFAULT_MAX_COMPLETION_TOKENS",
    "DEFAULT_MAX_TOTAL_TOKENS",
    "COMPLEXITY_THRESHOLD_SMALL",
    "COMPLEXITY_THRESHOLD_MEDIUM",
]
