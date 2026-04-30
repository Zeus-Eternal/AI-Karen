from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional
import uuid


@dataclass(frozen=True)
class RuntimePolicyDecision:
    """Canonical runtime policy decision produced from CORTEX output."""

    policy_token: str
    source: str
    requires_deep_reasoning: bool
    requires_medusa: bool
    correlation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cortex(
        cls,
        cortex_output: Optional[Mapping[str, Any]],
        *,
        correlation_id: Optional[str] = None,
        source: str = "cortex",
    ) -> "RuntimePolicyDecision":
        payload = dict(cortex_output or {})
        meta = dict(payload.get("metadata", {}))
        token = str(payload.get("policy_token") or uuid.uuid4())
        corr = str(correlation_id or payload.get("correlation_id") or uuid.uuid4())
        return cls(
            policy_token=token,
            source=source,
            requires_deep_reasoning=bool(payload.get("requires_deep_reasoning", False)),
            requires_medusa=bool(payload.get("requires_medusa", False)),
            correlation_id=corr,
            metadata=meta,
        )

    def to_telemetry_metadata(self) -> Dict[str, Any]:
        return {
            "policy_token": self.policy_token,
            "policy_source": self.source,
            "requires_deep_reasoning": self.requires_deep_reasoning,
            "requires_medusa": self.requires_medusa,
            "correlation_id": self.correlation_id,
            **self.metadata,
        }
