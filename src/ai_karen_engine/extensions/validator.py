from __future__ import annotations

from typing import Any, List, Tuple

from pydantic import ValidationError as PydanticValidationError

from ai_karen_engine.extensions.models import ExtensionManifest
from ai_karen_engine.manifest import ExtensionManifestSchema


class ValidationError(Exception):
    """Extension validation error."""
    pass


class ExtensionValidator:
    """Validates extension manifests using the shared schema."""

    VALID_CATEGORIES = {
        "analytics", "automation", "communication", "data", "development",
        "finance", "integration", "iot", "marketing", "productivity",
        "security", "social", "utilities", "example", "test"
    }

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_manifest(self, manifest: ExtensionManifest | dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate an extension manifest."""
        self.errors = []
        self.warnings = []

        data = manifest.to_dict() if hasattr(manifest, "to_dict") else manifest

        try:
            validated = ExtensionManifestSchema(**data)
        except PydanticValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(part) for part in err["loc"])
                self.errors.append(f"{loc}: {err['msg']}")
            return False, self.errors.copy(), self.warnings.copy()

        if validated.category not in self.VALID_CATEGORIES:
            self.warnings.append(
                "Category '" + validated.category + "' is not in recommended categories: "
                + ", ".join(sorted(self.VALID_CATEGORIES))
            )

        resources = validated.resources
        if resources.max_memory_mb > 4096:
            self.warnings.append(f"Memory limit {resources.max_memory_mb}MB is very high")
        if resources.max_cpu_percent > 50:
            self.warnings.append(f"CPU limit {resources.max_cpu_percent}% is very high")
        if resources.max_disk_mb > 10240:
            self.warnings.append(f"Disk limit {resources.max_disk_mb}MB is very high")

        return True, self.errors.copy(), self.warnings.copy()


def validate_extension_manifest(manifest: ExtensionManifest | dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """Convenience function for validating extension manifests."""
    return ExtensionValidator().validate_manifest(manifest)


__all__ = ["ExtensionValidator", "ValidationError", "validate_extension_manifest"]
