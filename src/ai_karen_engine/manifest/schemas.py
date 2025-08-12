"""Pydantic schemas for extension and plugin manifests."""
from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


SEMVER_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


class BaseManifest(BaseModel):
    """Fields common to both plugin and extension manifests."""

    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    category: str = "general"
    tags: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not NAME_PATTERN.match(v):
            raise ValueError("name must be lowercase kebab-case")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not SEMVER_PATTERN.match(v):
            raise ValueError("version must follow semantic versioning")
        return v


class ExtensionCapabilities(BaseModel):
    provides_ui: bool = False
    provides_api: bool = False
    provides_background_tasks: bool = False
    provides_webhooks: bool = False


class ExtensionDependencies(BaseModel):
    plugins: List[str] = Field(default_factory=list)
    extensions: List[str] = Field(default_factory=list)
    system_services: List[str] = Field(default_factory=list)


class ExtensionPermissions(BaseModel):
    data_access: List[str] = Field(default_factory=list)
    plugin_access: List[str] = Field(default_factory=list)
    system_access: List[str] = Field(default_factory=list)
    network_access: List[str] = Field(default_factory=list)


class ExtensionResources(BaseModel):
    max_memory_mb: int = 256
    max_cpu_percent: int = 10
    max_disk_mb: int = 100
    enforcement_action: str = "default"


class ExtensionUIConfig(BaseModel):
    control_room_pages: List[Dict[str, Any]] = Field(default_factory=list)
    streamlit_pages: List[Dict[str, Any]] = Field(default_factory=list)


class APIEndpoint(BaseModel):
    path: str
    methods: List[str]


class ExtensionAPIConfig(BaseModel):
    endpoints: List[APIEndpoint] = Field(default_factory=list)


class ExtensionBackgroundTask(BaseModel):
    name: str
    schedule: str
    function: str


class ExtensionMarketplaceInfo(BaseModel):
    price: str = "free"
    support_url: Optional[str] = None
    documentation_url: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)


class ExtensionManifestSchema(BaseManifest):
    """Schema for extension manifests."""

    display_name: str
    api_version: str = "1.0"
    kari_min_version: str = "0.4.0"
    capabilities: ExtensionCapabilities = Field(default_factory=ExtensionCapabilities)
    dependencies: ExtensionDependencies = Field(default_factory=ExtensionDependencies)
    permissions: ExtensionPermissions = Field(default_factory=ExtensionPermissions)
    resources: ExtensionResources = Field(default_factory=ExtensionResources)
    ui: ExtensionUIConfig = Field(default_factory=ExtensionUIConfig)
    api: ExtensionAPIConfig = Field(default_factory=ExtensionAPIConfig)
    background_tasks: List[ExtensionBackgroundTask] = Field(default_factory=list)
    marketplace: ExtensionMarketplaceInfo = Field(default_factory=ExtensionMarketplaceInfo)

    @field_validator("kari_min_version")
    @classmethod
    def validate_kari_version(cls, v: str) -> str:
        if not SEMVER_PATTERN.match(v):
            raise ValueError("kari_min_version must follow semantic versioning")
        return v


class PluginType(str, Enum):
    CORE = "core"
    AUTOMATION = "automation"
    AI = "ai"
    INTEGRATION = "integration"
    EXAMPLE = "example"
    CUSTOM = "custom"


class PluginManifestSchema(BaseManifest):
    """Schema for plugin manifests."""

    plugin_api_version: str = "1.0"
    plugin_type: PluginType = PluginType.CUSTOM
    module: str
    entry_point: str = "run"
    required_roles: List[str] = Field(default_factory=lambda: ["user"])
    trusted_ui: bool = False
    enable_external_workflow: bool = False
    sandbox_required: bool = True
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    compatibility: Dict[str, Any] = Field(default_factory=dict)
    intent: Optional[str] = None

    @field_validator("plugin_api_version")
    @classmethod
    def validate_api_version(cls, v: str) -> str:
        if v not in {"1.0", "1.1"}:
            raise ValueError("unsupported plugin API version")
        return v


__all__ = [
    "BaseManifest",
    "ExtensionCapabilities",
    "ExtensionDependencies",
    "ExtensionPermissions",
    "ExtensionResources",
    "ExtensionUIConfig",
    "ExtensionAPIConfig",
    "ExtensionBackgroundTask",
    "ExtensionMarketplaceInfo",
    "ExtensionManifestSchema",
    "PluginType",
    "PluginManifestSchema",
]
