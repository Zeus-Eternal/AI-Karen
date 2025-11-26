"""
Internal schemas for the extensions domain.

This module defines the data structures and schemas used internally by extension services.
These are not part of the public API and should not be imported from outside the extensions domain.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator


class ExtensionType(str, Enum):
    """Enumeration of extension types."""
    SYSTEM = "system"
    USER = "user"
    MARKETPLACE = "marketplace"
    INTEGRATION = "integration"
    PLUGIN = "plugin"


class ExtensionStatus(str, Enum):
    """Enumeration of extension statuses."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    TERMINATED = "terminated"
    DISABLED = "disabled"


class ExecutionStatus(str, Enum):
    """Enumeration of execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class PermissionType(str, Enum):
    """Enumeration of permission types."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class ExtensionCapability(BaseModel):
    """Schema for extension capability."""
    name: str
    description: str
    version: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ExtensionSchema(BaseModel):
    """Base schema for extension data."""
    id: UUID
    name: str
    type: ExtensionType
    version: str
    description: str
    status: ExtensionStatus
    capabilities: List[ExtensionCapability] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('capabilities')
    def validate_capabilities(cls, v):
        """Validate extension capabilities."""
        capability_names = [cap.name for cap in v]
        if len(capability_names) != len(set(capability_names)):
            raise ValueError("Duplicate capability names found")
        return v


class ExtensionManifestSchema(BaseModel):
    """Schema for extension manifest."""
    name: str
    type: ExtensionType
    version: str
    description: str
    entry_point: str
    requirements: List[str] = Field(default_factory=list)
    capabilities: List[ExtensionCapability] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    resources: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        if not v:
            raise ValueError("Version cannot be empty")
        return v
    
    @validator('entry_point')
    def validate_entry_point(cls, v):
        """Validate entry point format."""
        if not v.endswith('.py'):
            raise ValueError("Entry point must be a Python file")
        return v


class ExtensionExecutionSchema(BaseModel):
    """Schema for extension execution."""
    extension_id: UUID
    execution_id: UUID
    status: ExecutionStatus
    request: Dict[str, Any] = Field(default_factory=dict)
    response: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    auth: Dict[str, Any] = Field(default_factory=dict)
    flags: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtensionConfigSchema(BaseModel):
    """Schema for extension configuration."""
    extension_id: UUID
    config_key: str
    config_value: Any
    config_type: str
    description: Optional[str] = None
    is_sensitive: bool = False
    is_required: bool = False
    default_value: Optional[Any] = None
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('config_type')
    def validate_config_type(cls, v):
        """Validate config type."""
        allowed_types = ['string', 'integer', 'float', 'boolean', 'list', 'dict', 'json']
        if v not in allowed_types:
            raise ValueError(f"Invalid config type: {v}")
        return v


class ExtensionAuthSchema(BaseModel):
    """Schema for extension authentication."""
    extension_id: UUID
    auth_type: str
    auth_data: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('auth_type')
    def validate_auth_type(cls, v):
        """Validate auth type."""
        allowed_types = ['token', 'api_key', 'oauth', 'jwt', 'basic', 'certificate']
        if v not in allowed_types:
            raise ValueError(f"Invalid auth type: {v}")
        return v


class ExtensionPermissionSchema(BaseModel):
    """Schema for extension permissions."""
    extension_id: UUID
    resource: str
    permission_type: PermissionType
    conditions: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtensionResultSchema(BaseModel):
    """Schema for extension execution result."""
    extension_id: UUID
    execution_id: UUID
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtensionHealthSchema(BaseModel):
    """Schema for extension health."""
    extension_id: UUID
    is_healthy: bool
    health_check_time: datetime
    response_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    error_count: int = 0
    warning_count: int = 0
    last_error: Optional[str] = None
    last_warning: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtensionDependencySchema(BaseModel):
    """Schema for extension dependencies."""
    extension_id: UUID
    dependency_id: UUID
    dependency_name: str
    dependency_version: str
    is_optional: bool = False
    is_resolved: bool = False
    resolved_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtensionMarketplaceSchema(BaseModel):
    """Schema for extension marketplace."""
    id: UUID
    name: str
    display_name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str] = Field(default_factory=list)
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    is_featured: bool = False
    is_verified: bool = False
    is_compatible: bool = True
    price: Optional[float] = None
    license_type: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('rating')
    def validate_rating(cls, v):
        """Validate rating."""
        if v < 0 or v > 5:
            raise ValueError("Rating must be between 0 and 5")
        return v