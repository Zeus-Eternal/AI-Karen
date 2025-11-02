"""
Extension data models and schemas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Use dataclasses instead of pydantic for compatibility
try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator
except ImportError:
    # Fallback using dataclasses
    from dataclasses import dataclass
    
    class BaseModel:
        pass
    
    def Field(**kwargs):
        return None
    
    def field_validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class ConfigDict:
        pass

SEMVER_PATTERN = (
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
NAME_PATTERN = r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$"


class ExtensionStatus(Enum):
    """Extension status enumeration."""

    INACTIVE = "inactive"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADING = "unloading"


class ExtensionCapabilities(BaseModel):
    """Extension capability declarations."""

    provides_ui: bool = False
    provides_api: bool = False
    provides_background_tasks: bool = False
    provides_webhooks: bool = False


class ExtensionDependencies(BaseModel):
    """Extension dependency declarations."""

    plugins: List[str] = Field(default_factory=list)
    extensions: List[str] = Field(default_factory=list)
    system_services: List[str] = Field(default_factory=list)


class ExtensionPermissions(BaseModel):
    """Extension permission declarations."""

    data_access: List[str] = Field(default_factory=list)
    plugin_access: List[str] = Field(default_factory=list)
    system_access: List[str] = Field(default_factory=list)
    network_access: List[str] = Field(default_factory=list)


class ExtensionResources(BaseModel):
    """Extension resource limits."""

    max_memory_mb: int = 256
    max_cpu_percent: int = 10
    max_disk_mb: int = 100
    enforcement_action: str = "default"


class ExtensionUIConfig(BaseModel):
    """Extension UI configuration."""

    control_room_pages: List[Dict[str, Any]] = Field(default_factory=list)
    streamlit_pages: List[Dict[str, Any]] = Field(default_factory=list)


class ExtensionAPIConfig(BaseModel):
    """Extension API configuration."""

    endpoints: List[Dict[str, Any]] = Field(default_factory=list)


class ExtensionBackgroundTask(BaseModel):
    """Extension background task configuration."""

    name: str
    schedule: str
    function: str


class ExtensionMarketplaceInfo(BaseModel):
    """Extension marketplace metadata."""

    price: str = "free"
    support_url: Optional[str] = None
    documentation_url: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)


class ExtensionManifest(BaseModel):
    """Extension manifest containing all metadata and configuration."""

    model_config = ConfigDict(extra="allow")

    # Basic metadata
    name: str = Field(pattern=NAME_PATTERN, min_length=1, max_length=50)
    version: str = Field(pattern=SEMVER_PATTERN)
    display_name: str
    description: str
    author: str
    license: str
    category: str
    tags: List[str] = Field(default_factory=list)

    # API compatibility
    api_version: str = "1.0"
    kari_min_version: str = Field(default="0.4.0", pattern=SEMVER_PATTERN)

    # Capabilities and configuration
    capabilities: ExtensionCapabilities = Field(default_factory=ExtensionCapabilities)
    dependencies: ExtensionDependencies = Field(default_factory=ExtensionDependencies)
    permissions: ExtensionPermissions = Field(default_factory=ExtensionPermissions)
    resources: ExtensionResources = Field(default_factory=ExtensionResources)

    # UI and API configuration
    ui: ExtensionUIConfig = Field(default_factory=ExtensionUIConfig)
    api: ExtensionAPIConfig = Field(default_factory=ExtensionAPIConfig)
    background_tasks: List[ExtensionBackgroundTask] = Field(default_factory=list)

    # Marketplace metadata
    marketplace: ExtensionMarketplaceInfo = Field(
        default_factory=ExtensionMarketplaceInfo
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtensionManifest":
        """Create manifest from dictionary."""
        return cls(**data)

    @classmethod
    def from_file(cls, manifest_path: Path) -> "ExtensionManifest":
        """Load manifest from JSON file."""
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return self.model_dump()


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
    loaded_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "status": self.status.value,
            "directory": str(self.directory),
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "error_message": self.error_message,
            "manifest": self.manifest.to_dict(),
        }


# Pydantic models for API serialization

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
