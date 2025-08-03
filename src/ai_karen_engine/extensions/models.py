"""
Extension data models and schemas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, ConfigDict, Field, validator

    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback for environments without pydantic
    PYDANTIC_AVAILABLE = False
    BaseModel = object

    def Field(**kwargs):
        """Return a no-op field placeholder when pydantic is unavailable."""
        return None

    def validator(*args, **kwargs):
        """Return a decorator that leaves the function unchanged."""

        def decorator(func):
            return func

        return decorator


class ExtensionStatus(Enum):
    """Extension status enumeration."""

    INACTIVE = "inactive"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADING = "unloading"


@dataclass
class ExtensionCapabilities:
    """Extension capability declarations."""

    provides_ui: bool = False
    provides_api: bool = False
    provides_background_tasks: bool = False
    provides_webhooks: bool = False


@dataclass
class ExtensionDependencies:
    """Extension dependency declarations."""

    plugins: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    system_services: List[str] = field(default_factory=list)


@dataclass
class ExtensionPermissions:
    """Extension permission declarations."""

    data_access: List[str] = field(default_factory=list)
    plugin_access: List[str] = field(default_factory=list)
    system_access: List[str] = field(default_factory=list)
    network_access: List[str] = field(default_factory=list)


@dataclass
class ExtensionResources:
    """Extension resource limits."""

    max_memory_mb: int = 256
    max_cpu_percent: int = 10
    max_disk_mb: int = 100
    enforcement_action: str = "default"


@dataclass
class ExtensionUIConfig:
    """Extension UI configuration."""

    control_room_pages: List[Dict[str, Any]] = field(default_factory=list)
    streamlit_pages: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtensionAPIConfig:
    """Extension API configuration."""

    endpoints: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtensionBackgroundTask:
    """Extension background task configuration."""

    name: str
    schedule: str
    function: str


@dataclass
class ExtensionMarketplaceInfo:
    """Extension marketplace metadata."""

    price: str = "free"
    support_url: Optional[str] = None
    documentation_url: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)


@dataclass
class ExtensionManifest:
    """Extension manifest containing all metadata and configuration."""

    # Basic metadata
    name: str
    version: str
    display_name: str
    description: str
    author: str
    license: str
    category: str
    tags: List[str] = field(default_factory=list)

    # API compatibility
    api_version: str = "1.0"
    kari_min_version: str = "0.4.0"

    # Capabilities and configuration
    capabilities: ExtensionCapabilities = field(default_factory=ExtensionCapabilities)
    dependencies: ExtensionDependencies = field(default_factory=ExtensionDependencies)
    permissions: ExtensionPermissions = field(default_factory=ExtensionPermissions)
    resources: ExtensionResources = field(default_factory=ExtensionResources)

    # UI and API configuration
    ui: ExtensionUIConfig = field(default_factory=ExtensionUIConfig)
    api: ExtensionAPIConfig = field(default_factory=ExtensionAPIConfig)
    background_tasks: List[ExtensionBackgroundTask] = field(default_factory=list)

    # Marketplace metadata
    marketplace: ExtensionMarketplaceInfo = field(
        default_factory=ExtensionMarketplaceInfo
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExtensionManifest:
        """Create manifest from dictionary."""
        # Handle nested objects
        if "capabilities" in data:
            data["capabilities"] = ExtensionCapabilities(**data["capabilities"])
        if "dependencies" in data:
            data["dependencies"] = ExtensionDependencies(**data["dependencies"])
        if "permissions" in data:
            data["permissions"] = ExtensionPermissions(**data["permissions"])
        if "resources" in data:
            data["resources"] = ExtensionResources(**data["resources"])
        if "ui" in data:
            data["ui"] = ExtensionUIConfig(**data["ui"])
        if "api" in data:
            data["api"] = ExtensionAPIConfig(**data["api"])
        if "background_tasks" in data:
            data["background_tasks"] = [
                ExtensionBackgroundTask(**task) for task in data["background_tasks"]
            ]
        if "marketplace" in data:
            data["marketplace"] = ExtensionMarketplaceInfo(**data["marketplace"])

        return cls(**data)

    @classmethod
    def from_file(cls, manifest_path: Path) -> ExtensionManifest:
        """Load manifest from JSON file."""
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if hasattr(value, "__dict__"):
                result[key] = value.__dict__
            elif isinstance(value, list) and value and hasattr(value[0], "__dict__"):
                result[key] = [item.__dict__ for item in value]
            else:
                result[key] = value
        return result


@dataclass
class ExtensionContext:
    """Context provided to extensions during initialization."""

    plugin_router: Any  # PluginRouter instance
    db_session: Any  # Database session
    app_instance: Any  # FastAPI app instance
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ExtensionRecord:
    """Runtime record of a loaded extension."""

    manifest: ExtensionManifest
    instance: Any  # BaseExtension instance
    status: ExtensionStatus
    directory: Path
    loaded_at: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "status": self.status.value,
            "directory": str(self.directory),
            "loaded_at": self.loaded_at,
            "error_message": self.error_message,
            "manifest": self.manifest.to_dict(),
        }


# Pydantic models for API serialization (if available)
if PYDANTIC_AVAILABLE:

    class ExtensionManifestAPI(BaseModel):
        """Pydantic model for API serialization of extension manifest."""

        name: str
        version: str
        display_name: str
        description: str
        author: str
        license: str
        category: str
        tags: List[str] = []
        api_version: str = "1.0"
        kari_min_version: str = "0.4.0"

        model_config = ConfigDict(extra="allow")

    class ExtensionStatusAPI(BaseModel):
        """Pydantic model for API serialization of extension status."""

        name: str
        version: str
        status: str
        loaded_at: Optional[float] = None
        error_message: Optional[str] = None

else:
    # Fallback classes when pydantic is not available
    class ExtensionManifestAPI:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class ExtensionStatusAPI:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)


__all__ = [
    "ExtensionStatus",
    "ExtensionCapabilities",
    "ExtensionDependencies",
    "ExtensionPermissions",
    "ExtensionResources",
    "ExtensionUIConfig",
    "ExtensionAPIConfig",
    "ExtensionBackgroundTask",
    "ExtensionMarketplaceInfo",
    "ExtensionManifest",
    "ExtensionContext",
    "ExtensionRecord",
    "ExtensionManifestAPI",
    "ExtensionStatusAPI",
]
