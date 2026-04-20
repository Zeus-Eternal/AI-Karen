"""
Extension Database Models

Unified database models for extension system, consolidating models from both
platform/core and runtime systems.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json


class ExtensionState(str, Enum):
    """Extension state enumeration."""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNINSTALLED = "uninstalled"
    ERROR = "error"


@dataclass
class ExtensionModel:
    """Unified extension model combining features from both systems."""

    id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    extension_path: Optional[str] = None
    manifest: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: ExtensionState = ExtensionState.INSTALLED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "extension_path": self.extension_path,
            "manifest": self.manifest,
            "metadata": self.metadata,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtensionModel":
        """Create model from dictionary."""
        state = data.get("state")
        if isinstance(state, str):
            state = ExtensionState(state)

        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data.get("description"),
            author=data.get("author"),
            extension_path=data.get("extension_path"),
            manifest=data.get("manifest", {}),
            metadata=data.get("metadata", {}),
            state=state,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class ExtensionHealth:
    """Extension health model combining health monitoring features."""

    extension_id: str
    status: str = "healthy"
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "extension_id": self.extension_id,
            "status": self.status,
            "last_check": self.last_check.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "metrics": self.metrics,
        }


@dataclass
class ExtensionPermission:
    """Extension permission model combining permission features."""

    id: str
    extension_id: str
    permission_type: str
    resource: str
    action: str
    granted: bool = True
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "extension_id": self.extension_id,
            "permission_type": self.permission_type,
            "resource": self.resource,
            "action": self.action,
            "granted": self.granted,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "conditions": self.conditions,
        }


@dataclass
class ExtensionConfig:
    """Extension configuration model."""

    id: str
    extension_id: str
    key: str
    value: Any
    config_type: str = "string"
    description: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "extension_id": self.extension_id,
            "key": self.key,
            "value": self.value,
            "config_type": self.config_type,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
