from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class ProviderRouteDecision:
    """Canonical contract for an LLM provider/model routing decision."""
    requested_provider: Optional[str]
    requested_model: Optional[str]

    selected_provider: Optional[str]
    selected_model: Optional[str]

    provider_category: Optional[str] = None
    compatibility_profile: Optional[str] = None
    runtime_engine: Optional[str] = None
    transport: Optional[str] = None

    selection_source: str = "unknown" # e.g., "preferred", "policy", "fallback"
    fallback_level: int = 0

    degraded_mode: bool = False
    degradation_type: Optional[str] = None
    degradation_reason: Optional[str] = None

    provider_healthy: bool = True
    model_available: bool = True
    allowed_for_current_user: bool = True

    provider_catalog_version: Optional[str] = None
    runtime_config_hash: Optional[str] = None
    correlation_id: str = ""

    routing_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderExecutionResult:
    """Canonical contract for the result of an LLM provider execution."""
    text: str

    requested_provider: Optional[str]
    requested_model: Optional[str]

    selected_provider: Optional[str]
    selected_model: Optional[str]

    actual_provider: Optional[str]
    actual_model: Optional[str]

    provider_category: Optional[str] = None
    compatibility_profile: Optional[str] = None
    runtime_engine: Optional[str] = None
    transport: Optional[str] = None

    response_source: str = "unknown" # e.g., "provider_runtime", "fallback_provider_runtime", "emergency_static"
    fallback_level: int = 0

    degraded_mode: bool = False
    degradation_type: Optional[str] = None
    degradation_reason: Optional[str] = None

    latency_ms: float = 0.0
    correlation_id: str = ""

    provider_attempts: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    finish_reason: Optional[str] = None
