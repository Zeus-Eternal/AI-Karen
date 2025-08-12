"""Plugin manifest validation utilities."""
from __future__ import annotations

from typing import Any, List, Tuple

from pydantic import ValidationError as PydanticValidationError

from ai_karen_engine.manifest import PluginManifestSchema


class PluginValidationError(Exception):
    """Plugin validation error."""
    pass


class PluginManifestValidator:
    """Validates plugin manifests using the shared schema."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_manifest(self, manifest: dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        self.errors = []
        self.warnings = []
        try:
            PluginManifestSchema(**manifest)
        except PydanticValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(part) for part in err["loc"])
                self.errors.append(f"{loc}: {err['msg']}")
        return len(self.errors) == 0, self.errors.copy(), self.warnings.copy()


def validate_plugin_manifest(manifest: dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """Convenience function for plugin manifest validation."""
    return PluginManifestValidator().validate_manifest(manifest)


__all__ = [
    "PluginManifestValidator",
    "PluginValidationError",
    "validate_plugin_manifest",
]
