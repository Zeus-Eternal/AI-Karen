"""
Extension system data models and types.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


class ExtensionStatus(str, Enum):
    """Extension status enumeration."""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"
    UNLOADING = "unloading"


class ExtensionCapabilities(BaseModel):
    """Extension capabilities declaration."""
    provides_ui: bool = False
    provides_api: bool = False
    provides_background_tasks: bool = False
    provides_webhooks: bool = False


class ExtensionDependencies(BaseModel):
    """Extension dependencies declaration."""
    plugins: List[str] = Field(default_factory=list)
    extensions: List[str] = Field(default_factory=list)
    system_services: List[str] = Field(default_factory=list)


class ExtensionPermissions(BaseModel):
    """Extension permissions declaration."""
    data_access: List[str] = Field(default_factory=list)  # read, write, admin
    plugin_access: List[str] = Field(default_factory=list)  # execute, manage
    system_access: List[str] = Field(default_factory=list)  # files, network, scheduler, logs
    network_access: List[str] = Field(default_factory=list)  # external, internal


class ExtensionResources(BaseModel):
    """Extension resource limits."""
    max_memory_mb: int = 256
    max_cpu_percent: int = 10
    max_disk_mb: int = 512


class ExtensionUIPage(BaseModel):
    """Extension UI page definition."""
    name: str
    path: str
    icon: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class ExtensionUI(BaseModel):
    """Extension UI configuration."""
    control_room_pages: List[ExtensionUIPage] = Field(default_factory=list)


class ExtensionAPIEndpoint(BaseModel):
    """Extension API endpoint definition."""
    path: str
    methods: List[str] = Field(default_factory=lambda: ["GET"])
    permissions: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ExtensionAPI(BaseModel):
    """Extension API configuration."""
    endpoints: List[ExtensionAPIEndpoint] = Field(default_factory=list)
    prefix: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ExtensionBackgroundTask(BaseModel):
    """Extension background task definition."""
    name: str
    schedule: str  # Cron expression
    function: str  # Module.function path
    description: Optional[str] = None
    enabled: bool = True


class ExtensionMarketplace(BaseModel):
    """Extension marketplace metadata."""
    price: str = "free"
    support_url: Optional[str] = None
    documentation_url: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class ExtensionManifest(BaseModel):
    """Extension manifest model."""
    # Required fields
    name: str = Field(..., pattern=r"^[a-z0-9-]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    display_name: str
    description: str
    author: str
    license: str
    category: str
    
    # Optional metadata
    tags: List[str] = Field(default_factory=list)
    homepage: Optional[str] = None
    repository: Optional[str] = None
    
    # Version compatibility
    api_version: str = "1.0"
    kari_min_version: str = "0.4.0"
    
    # Extension configuration
    capabilities: ExtensionCapabilities = Field(default_factory=ExtensionCapabilities)
    dependencies: ExtensionDependencies = Field(default_factory=ExtensionDependencies)
    permissions: ExtensionPermissions = Field(default_factory=ExtensionPermissions)
    resources: ExtensionResources = Field(default_factory=ExtensionResources)
    
    # Integration configuration
    ui: ExtensionUI = Field(default_factory=ExtensionUI)
    api: ExtensionAPI = Field(default_factory=ExtensionAPI)
    background_tasks: List[ExtensionBackgroundTask] = Field(default_factory=list)
    
    # Marketplace metadata
    marketplace: ExtensionMarketplace = Field(default_factory=ExtensionMarketplace)
    
    @validator('name')
    def validate_name(cls, v):
        """Validate extension name format."""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Extension name must be lowercase alphanumeric with hyphens')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Extension name must be between 3 and 50 characters')
        return v
    
    @validator('version')
    def validate_version(cls, v):
        """Validate semantic version format."""
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Version must follow semantic versioning (x.y.z)')
        return v


class ExtensionRecord(BaseModel):
    """Extension runtime record."""
    manifest: ExtensionManifest
    status: ExtensionStatus = ExtensionStatus.NOT_LOADED
    instance: Optional[Any] = None  # The actual extension instance
    error: Optional[str] = None
    loaded_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class ExtensionContext(BaseModel):
    """Extension execution context."""
    extension_name: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    resource_limits: ExtensionResources = Field(default_factory=ExtensionResources)
    
    class Config:
        arbitrary_types_allowed = True


class ExtensionAPIRoute(BaseModel):
    """Extension API route information."""
    extension_name: str
    path: str
    methods: List[str]
    handler: Any
    permissions: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class ExtensionHealthStatus(BaseModel):
    """Extension health status."""
    extension_name: str
    status: ExtensionStatus
    is_healthy: bool
    last_check: datetime
    error_count: int = 0
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    uptime_seconds: float = 0.0
    
    
class ExtensionRegistryEntry(BaseModel):
    """Extension registry database entry."""
    id: Optional[int] = None
    name: str
    version: str
    manifest: Dict[str, Any]  # JSON serialized manifest
    status: str
    installed_at: datetime
    updated_at: datetime
    tenant_id: Optional[str] = None
    installed_by: Optional[str] = None
    error_message: Optional[str] = None