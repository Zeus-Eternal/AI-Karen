from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ModelValidationResult:
    valid: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    security_flags: tuple[str, ...] = field(default_factory=tuple)


def validate_model_record(
    record: Mapping[str, Any],
    discovery_config: Mapping[str, Any] | None = None,
) -> ModelValidationResult:
    security_policy = (discovery_config or {}).get("security_policy", {}) or {}
    allowed_formats = {
        "transformers",
        "gguf",
        "onnx",
        "unknown",
    }

    errors: list[str] = []
    warnings: list[str] = []
    security_flags = set(record.get("security_flags") or [])

    model_format = str(record.get("model_format") or "unknown").lower()
    if model_format not in allowed_formats:
        warnings.append(f"Unrecognized model format: {model_format}")

    if model_format == "transformers":
        if security_policy.get("require_tokenizer_for_transformers") and not record.get("tokenizer_present", True):
            errors.append("Transformers model missing tokenizer metadata")
            security_flags.add("missing_tokenizer")
        if security_policy.get("require_weights_for_transformers") and not record.get("weights_present", True):
            errors.append("Transformers model missing weights")
            security_flags.add("missing_weights")

    if record.get("adapter_only") and not record.get("base_model_ref"):
        warnings.append("Adapter-only model requires a base model reference")
        security_flags.add("adapter_only_without_base")

    valid = not errors
    return ModelValidationResult(
        valid=valid,
        warnings=tuple(warnings),
        errors=tuple(errors),
        security_flags=tuple(sorted(security_flags)),
    )
