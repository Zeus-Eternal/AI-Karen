"""
Extension Manifest

Unified manifest system for extensions, consolidating manifest handling from
both platform/core and runtime systems.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExtensionManifest:
    """Unified extension manifest combining features from both systems."""

    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)

    # Extension metadata
    extension_type: str = "plugin"  # plugin, theme, integration, system
    api_version: str = "1.0.0"
    min_platform_version: str = "1.0.0"
    max_platform_version: str = "999.0.0"

    # Dependencies and requirements
    dependencies: Dict[str, str] = field(default_factory=dict)  # name -> version
    system_requirements: Dict[str, Any] = field(default_factory=dict)
    python_requirements: List[str] = field(default_factory=list)

    # Configuration
    config_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)

    # Permissions
    permissions: List[Dict[str, Any]] = field(default_factory=list)

    # Lifecycle hooks
    hooks: Dict[str, List[str]] = field(default_factory=dict)

    # UI components
    ui_components: Dict[str, Any] = field(default_factory=dict)

    # Marketplace
    marketplace: Dict[str, Any] = field(default_factory=dict)

    # Additional metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        data = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "keywords": self.keywords,
            "categories": self.categories,
            "extension_type": self.extension_type,
            "api_version": self.api_version,
            "min_platform_version": self.min_platform_version,
            "max_platform_version": self.max_platform_version,
            "dependencies": self.dependencies,
            "system_requirements": self.system_requirements,
            "python_requirements": self.python_requirements,
            "config_schema": self.config_schema,
            "default_config": self.default_config,
            "permissions": self.permissions,
            "hooks": self.hooks,
            "ui_components": self.ui_components,
            "marketplace": self.marketplace,
        }

        # Add timestamps if available
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtensionManifest":
        """Create manifest from dictionary."""
        manifest = cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description"),
            author=data.get("author"),
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            license=data.get("license"),
            keywords=data.get("keywords", []),
            categories=data.get("categories", []),
            extension_type=data.get("extension_type", "plugin"),
            api_version=data.get("api_version", "1.0.0"),
            min_platform_version=data.get("min_platform_version", "1.0.0"),
            max_platform_version=data.get("max_platform_version", "999.0.0"),
            dependencies=data.get("dependencies", {}),
            system_requirements=data.get("system_requirements", {}),
            python_requirements=data.get("python_requirements", []),
            config_schema=data.get("config_schema", {}),
            default_config=data.get("default_config", {}),
            permissions=data.get("permissions", []),
            hooks=data.get("hooks", {}),
            ui_components=data.get("ui_components", {}),
            marketplace=data.get("marketplace", {}),
        )

        # Parse timestamps
        if "created_at" in data:
            manifest.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            manifest.updated_at = datetime.fromisoformat(data["updated_at"])

        return manifest

    def to_json(self, indent: int = 2) -> str:
        """Convert manifest to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_yaml(self) -> str:
        """Convert manifest to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_json(cls, json_str: str) -> "ExtensionManifest":
        """Create manifest from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ExtensionManifest":
        """Create manifest from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, file_path: Path) -> "ExtensionManifest":
        """Create manifest from file (JSON or YAML)."""
        if file_path.suffix.lower() == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return cls.from_json(f.read())
        elif file_path.suffix.lower() in [".yaml", ".yml"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return cls.from_yaml(f.read())
        else:
            raise ValueError(f"Unsupported manifest format: {file_path.suffix}")

    def validate(self) -> List[str]:
        """Validate manifest and return list of errors."""
        errors = []

        # Required fields
        if not self.name:
            errors.append("Name is required")
        if not self.version:
            errors.append("Version is required")

        # Version format validation
        if not self._is_valid_version(self.version):
            errors.append(f"Invalid version format: {self.version}")

        # Dependencies validation
        for dep_name, dep_version in self.dependencies.items():
            if not dep_name:
                errors.append("Dependency name cannot be empty")
            if not self._is_valid_version(dep_version):
                errors.append(
                    f"Invalid dependency version for {dep_name}: {dep_version}"
                )

        # API version validation
        if not self._is_valid_version(self.api_version):
            errors.append(f"Invalid API version format: {self.api_version}")

        # Platform version validation
        if not self._is_valid_version(self.min_platform_version):
            errors.append(
                f"Invalid min platform version format: {self.min_platform_version}"
            )
        if not self._is_valid_version(self.max_platform_version):
            errors.append(
                f"Invalid max platform version format: {self.max_platform_version}"
            )

        # Permissions validation
        for perm in self.permissions:
            if not isinstance(perm, dict):
                errors.append("Permissions must be objects")
                break
            if "resource" not in perm:
                errors.append("Permission must have 'resource' field")
            if "actions" not in perm:
                errors.append("Permission must have 'actions' field")

        return errors

    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid (semantic versioning)."""
        if not version:
            return False

        try:
            parts = version.split(".")
            if len(parts) != 3:
                return False

            for part in parts:
                if not part.isdigit():
                    return False

            return True
        except:
            return False

    def satisfies_platform_version(self, platform_version: str) -> bool:
        """Check if manifest satisfies platform version requirements."""
        if not platform_version:
            return True

        try:
            platform_parts = [int(x) for x in platform_version.split(".")]
            min_parts = [int(x) for x in self.min_platform_version.split(".")]
            max_parts = [int(x) for x in self.max_platform_version.split(".")]

            # Check minimum version
            if platform_parts < min_parts:
                return False

            # Check maximum version
            if platform_parts > max_parts:
                return False

            return True
        except:
            return False

    def get_required_permissions(self) -> List[Dict[str, Any]]:
        """Get list of required permissions."""
        return self.permissions

    def get_hook_points(self) -> List[str]:
        """Get list of available hook points."""
        return list(self.hooks.keys())

    def get_hook_handlers(self, hook_point: str) -> List[str]:
        """Get list of handlers for a specific hook point."""
        return self.hooks.get(hook_point, [])
