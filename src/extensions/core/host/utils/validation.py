"""Compatibility validation helpers for the unified extension host."""

from __future__ import annotations

from typing import Any, Dict

from extensions.core.host.errors import ExtensionValidationError
from extensions.core.registry.validator import ExtensionValidator


def validate_manifest(manifest_data: Dict[str, Any]) -> None:
    """Validate a manifest payload and raise on invalid input."""
    validator = ExtensionValidator()
    is_valid, errors, _warnings = validator.validate_manifest(manifest_data)
    if not is_valid:
        raise ExtensionValidationError(
            "Manifest validation failed",
            validation_errors=errors,
        )

