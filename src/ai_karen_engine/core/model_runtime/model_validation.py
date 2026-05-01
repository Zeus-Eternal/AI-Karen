from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ModelValidationResult:
    valid: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    security_flags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ModelCapabilityProfile:
    provider: str
    model: str
    chat_capable: bool
    fallback_eligible: bool
    capabilities: set[str]
    unsuitable_for: set[str]


CODE_MODEL_PATTERNS = (
    "starcoder",
    "codellama",
    "deepseek-coder",
    "codegemma",
    "wizardcoder",
    "stable-code",
    "sqlcoder",
    "granite-code",
)


def infer_model_capabilities(model_name: str, provider: str = "") -> ModelCapabilityProfile:
    """Infer model capabilities based on naming patterns."""
    normalized = model_name.lower()

    if any(pattern in normalized for pattern in CODE_MODEL_PATTERNS):
        return ModelCapabilityProfile(
            provider=provider,
            model=model_name,
            chat_capable=False,
            fallback_eligible=False,
            capabilities={"code_generation", "code_completion", "repo_analysis"},
            unsuitable_for={"general.chat", "direct_answer", "creative.chat"},
        )

    return ModelCapabilityProfile(
        provider=provider,
        model=model_name,
        chat_capable=True,
        fallback_eligible=True,
        capabilities={"general_chat"},
        unsuitable_for=set(),
    )


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
