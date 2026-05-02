from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .response_sanitizer import sanitize_response_text
from .response_validator import validate_response_text


REQUIRED_RUNTIME_METADATA_KEYS = [
    "preferred_engine",
    "active_engine",
    "requested_provider",
    "requested_model",
    "actual_provider",
    "actual_model",
    "runtime_engine",
    "response_source",
    "failed_engines",
    "failed_providers",
    "skipped_providers",
    "policy_rejections",
    "fallback_level",
    "degraded",
    "degradation_reason",
    "correlation_id",
]


@dataclass(slots=True)
class ProcessedResponse:
    text: str
    valid: bool
    metadata: dict[str, Any] = field(default_factory=dict)


def ensure_runtime_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    base = dict(metadata or {})
    for key in REQUIRED_RUNTIME_METADATA_KEYS:
        base.setdefault(key, None)
    base.setdefault("failed_engines", [])
    base.setdefault("failed_providers", [])
    base.setdefault("skipped_providers", [])
    base.setdefault("policy_rejections", [])
    base.setdefault("degraded", False)
    return base


def process_response(text: str, *, metadata: dict[str, Any] | None = None, allow_tool_json: bool = False) -> ProcessedResponse:
    clean = sanitize_response_text(text)
    valid = validate_response_text(clean, allow_tool_json=allow_tool_json)
    final_text = clean if valid else "Response unavailable."
    return ProcessedResponse(text=final_text, valid=valid, metadata=ensure_runtime_metadata(metadata))
