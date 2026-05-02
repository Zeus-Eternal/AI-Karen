from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EngineConfig:
    enabled: bool = True
    type: str = "builtin_provider_engine"
    fallback_eligible: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExpressionPolicyConfig:
    allow_third_party_engines: bool = True
    allow_external_engines: bool = False
    require_admin_for_external: bool = True
    default_timeout_ms: int = 30000


@dataclass(slots=True)
class ExpressionSettings:
    active_engine: str = "builtin"
    engines: dict[str, EngineConfig] = field(
        default_factory=lambda: {
            "builtin": EngineConfig(enabled=True, type="builtin_provider_engine"),
            "openai_compatible_local": EngineConfig(enabled=False, type="openai_compatible"),
            "llama_cpp_server": EngineConfig(enabled=False, type="openai_compatible"),
            "glm": EngineConfig(enabled=False, type="openai_compatible", fallback_eligible=True),
        }
    )
    policies: ExpressionPolicyConfig = field(default_factory=ExpressionPolicyConfig)
    engine_fallback_order: list[str] = field(default_factory=lambda: ["builtin", "openai_compatible_local", "llama_cpp_server", "glm", "enterprise"])
    local_first_mode: bool = True
    provider_fallback_policy: str = "ordered"
    third_party_endpoint_url: str | None = None
