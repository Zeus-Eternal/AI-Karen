from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class ProviderRouteDecision:
    """Canonical contract for an LLM provider/model routing decision."""
    requested_provider: Optional[str]
    requested_model: Optional[str]
    selected_provider: str
    selected_model: str
    runtime_engine: str
    selection_source: str  # e.g., "preferred", "policy", "fallback"
    fallback_level: int
    degraded_mode: bool
    degradation_reason: Optional[str]
    provider_healthy: bool
    model_available: bool
    routing_reason: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass(frozen=True)
class ProviderExecutionResult:
    """Canonical contract for the result of an LLM provider execution."""
    text: str
    requested_provider: Optional[str]
    requested_model: Optional[str]
    selected_provider: str
    selected_model: str
    actual_provider: str
    actual_model: str
    runtime_engine: str
    response_source: str  # e.g., "provider_runtime", "fallback_provider_runtime", "static_fallback"
    fallback_level: int
    degraded_mode: bool
    degradation_reason: Optional[str]
    latency_ms: float
    correlation_id: str
    usage: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    finish_reason: Optional[str] = None
