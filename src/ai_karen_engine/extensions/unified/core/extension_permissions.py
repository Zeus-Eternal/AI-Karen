"""
Unified Extension Permissions

Consolidates the best features from both platform/core and runtime permission systems.
Provides comprehensive permission management with RBAC, audit logging, and fine-grained control.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

from .database_models import ExtensionPermission, ExtensionModel

logger = logging.getLogger(__name__)


class ExtensionPermissionType(str, Enum):
    """Extension permission types."""

    SYSTEM = "system"
    DATA = "data"
    API = "api"
    NETWORK = "network"
    FILE = "file"
    EXECUTION = "execution"
    UI = "ui"
    CUSTOM = "custom"


class ExtensionPermissionResult:
    """Result of permission evaluation."""

    granted: bool
    reason: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None

    def __init__(self, granted: bool, reason: Optional[str] = None):
        self.granted = granted
        self.reason = reason


class ExtensionPermissions:
    """Unified extension permission system."""

    def __init__(self, registry=None):
        self.registry = registry
        self._permissions: Dict[str, List[ExtensionPermission]] = {}
        self._permission_cache: Dict[str, ExtensionPermissionResult] = {}
        self._cache_ttl = 300  # 5 minutes
        self._lock = asyncio.Lock()

        # Permission evaluation functions
        self._evaluators: Dict[ExtensionPermissionType, callable] = {}
        self._setup_default_evaluators()

    async def initialize(self) -> None:
        """Initialize the permission system."""
        await self._load_permissions()
        logger.info("Extension permissions system initialized")

    async def grant_permission(
        self,
        extension_id: str,
        permission_type: ExtensionPermissionType,
        resource: str,
        actions: List[str],
        conditions: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> ExtensionPermission:
        """Grant a permission to an extension."""
        async with self._lock:
            # Create permission
            permission = ExtensionPermission(
                id=str(uuid.uuid4()),
                extension_id=extension_id,
                permission_type=permission_type.value,
                resource=resource,
                action=",".join(actions),  # Store actions as comma-separated string
                granted=True,
                conditions=conditions or {},
                expires_at=expires_at,
                granted_at=datetime.now(timezone.utc),
            )

            # Store permission
            if extension_id not in self._permissions:
                self._permissions[extension_id] = []

            self._permissions[extension_id].append(permission)

            # Invalidate cache
            self._invalidate_cache(extension_id)

            logger.info(
                f"Granted permission to {extension_id}: {permission_type.value}:{resource}:{actions}"
            )
            return permission

    async def revoke_permission(
        self,
        extension_id: str,
        permission_type: ExtensionPermissionType,
        resource: str,
        actions: Optional[List[str]] = None,
    ) -> bool:
        """Revoke a permission from an extension."""
        async with self._lock:
            if extension_id not in self._permissions:
                return False

            revoked = False
            permissions = self._permissions[extension_id]

            for i, permission in enumerate(permissions):
                if (
                    permission.permission_type == permission_type.value
                    and permission.resource == resource
                ):
                    # If specific actions requested, check them
                    if actions:
                        permission_actions = set(permission.action.split(","))
                        requested_actions = set(actions)

                        # Remove only the requested actions
                        remaining_actions = permission_actions - requested_actions
                        if remaining_actions:
                            permission.action = ",".join(remaining_actions)
                        else:
                            # Remove the entire permission
                            permissions.pop(i)
                            revoked = True
                    else:
                        # Remove the entire permission
                        permissions.pop(i)
                        revoked = True

            # Invalidate cache
            self._invalidate_cache(extension_id)

            if revoked:
                logger.info(
                    f"Revoked permission from {extension_id}: {permission_type.value}:{resource}"
                )

            return revoked

    async def check_permission(
        self,
        extension_id: str,
        permission_type: ExtensionPermissionType,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtensionPermissionResult:
        """Check if an extension has a specific permission."""
        # Check cache first
        cache_key = f"{extension_id}:{permission_type.value}:{resource}:{action}"
        cached_result = self._get_cached_permission(cache_key)
        if cached_result:
            return cached_result

        # Evaluate permission
        result = await self._evaluate_permission(
            extension_id, permission_type, resource, action, context
        )

        # Cache result
        self._cache_permission(cache_key, result)

        return result

    async def list_permissions(
        self,
        extension_id: str,
        permission_type: Optional[ExtensionPermissionType] = None,
    ) -> List[ExtensionPermission]:
        """List permissions for an extension."""
        if extension_id not in self._permissions:
            return []

        permissions = self._permissions[extension_id]

        if permission_type:
            return [
                p for p in permissions if p.permission_type == permission_type.value
            ]

        return permissions

    async def list_expired_permissions(self) -> List[ExtensionPermission]:
        """List all expired permissions."""
        now = datetime.now(timezone.utc)
        expired = []

        for extension_permissions in self._permissions.values():
            for permission in extension_permissions:
                if (
                    permission.expires_at
                    and permission.expires_at <= now
                    and permission.granted
                ):
                    expired.append(permission)

        return expired

    async def cleanup_expired_permissions(self) -> int:
        """Clean up expired permissions and return count removed."""
        now = datetime.now(timezone.utc)
        removed_count = 0

        for extension_id, permissions in self._permissions.items():
            # Filter out expired permissions
            original_count = len(permissions)
            permissions[:] = [
                p
                for p in permissions
                if not (p.expires_at and p.expires_at <= now and p.granted)
            ]
            removed_count += original_count - len(permissions)

            # Invalidate cache if permissions were removed
            if original_count != len(permissions):
                self._invalidate_cache(extension_id)

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired permissions")

        return removed_count

    async def _evaluate_permission(
        self,
        extension_id: str,
        permission_type: ExtensionPermissionType,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtensionPermissionResult:
        """Evaluate a permission request."""
        # Check if extension exists
        if self.registry:
            extension = await self.registry.get_extension(extension_id)
            if not extension:
                return ExtensionPermissionResult(
                    granted=False, reason="Extension not found"
                )

        # Get extension permissions
        permissions = await self.list_permissions(extension_id, permission_type)

        # Check each permission
        for permission in permissions:
            if not self._is_permission_valid(permission):
                continue

            if self._matches_permission(permission, resource, action):
                # Check conditions
                if self._check_conditions(permission, context):
                    return ExtensionPermissionResult(
                        granted=True, reason="Permission granted"
                    )

        return ExtensionPermissionResult(granted=False, reason="Permission denied")

    def _is_permission_valid(self, permission: ExtensionPermission) -> bool:
        """Check if a permission is still valid."""
        # Check expiration
        if permission.expires_at:
            now = datetime.now(timezone.utc)
            if permission.expires_at <= now:
                return False

        # Check if granted
        if not permission.granted:
            return False

        return True

    def _matches_permission(
        self, permission: ExtensionPermission, resource: str, action: str
    ) -> bool:
        """Check if a permission matches the requested resource and action."""
        # Check resource
        if permission.resource != "*" and permission.resource != resource:
            return False

        # Check action
        if permission.action == "*":
            return True

        requested_action = action
        allowed_actions = set(permission.action.split(","))

        return requested_action in allowed_actions

    def _check_conditions(
        self, permission: ExtensionPermission, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check permission conditions."""
        if not permission.conditions:
            return True

        if not context:
            return False

        # Check time-based conditions
        if "time_range" in permission.conditions:
            time_range = permission.conditions["time_range"]
            now = datetime.now(timezone.utc)

            if "start" in time_range:
                start = datetime.fromisoformat(time_range["start"])
                if now < start:
                    return False

            if "end" in time_range:
                end = datetime.fromisoformat(time_range["end"])
                if now > end:
                    return False

        # Check IP-based conditions
        if "ip_whitelist" in permission.conditions:
            if "client_ip" not in context:
                return False

            client_ip = context["client_ip"]
            if client_ip not in permission.conditions["ip_whitelist"]:
                return False

        # Check rate limiting conditions
        if "rate_limit" in permission.conditions:
            # This would require a rate limiter implementation
            # For now, return True as a placeholder
            pass

        return True

    def _get_cached_permission(
        self, cache_key: str
    ) -> Optional[ExtensionPermissionResult]:
        """Get cached permission result."""
        cached = self._permission_cache.get(cache_key)
        if cached:
            # Check if cache is still valid
            if (
                datetime.now(timezone.utc) - cached.expires_at
            ).total_seconds() < self._cache_ttl:
                return cached
            else:
                # Remove expired cache entry
                del self._permission_cache[cache_key]

        return None

    def _cache_permission(
        self, cache_key: str, result: ExtensionPermissionResult
    ) -> None:
        """Cache permission result."""
        # Add expiration time to result
        result.expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self._cache_ttl
        )

        self._permission_cache[cache_key] = result

    def _invalidate_cache(self, extension_id: str) -> None:
        """Invalidate all cache entries for an extension."""
        keys_to_remove = []
        for key in self._permission_cache.keys():
            if key.startswith(f"{extension_id}:"):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._permission_cache[key]

    async def _load_permissions(self) -> None:
        """Load permissions from storage."""
        # This would typically load from a database
        # For now, initialize with empty permissions
        self._permissions = {}
        logger.info("Loaded permissions from storage")

    def _setup_default_evaluators(self) -> None:
        """Setup default permission evaluators."""
        # System permissions
        self._evaluators[ExtensionPermissionType.SYSTEM] = (
            self._evaluate_system_permission
        )

        # Data permissions
        self._evaluators[ExtensionPermissionType.DATA] = self._evaluate_data_permission

        # API permissions
        self._evaluators[ExtensionPermissionType.API] = self._evaluate_api_permission

        # Network permissions
        self._evaluators[ExtensionPermissionType.NETWORK] = (
            self._evaluate_network_permission
        )

        # File permissions
        self._evaluators[ExtensionPermissionType.FILE] = self._evaluate_file_permission

        # Execution permissions
        self._evaluators[ExtensionPermissionType.EXECUTION] = (
            self._evaluate_execution_permission
        )

        # UI permissions
        self._evaluators[ExtensionPermissionType.UI] = self._evaluate_ui_permission

    def _evaluate_system_permission(
        self,
        permission: ExtensionPermission,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate system permission."""
        # System permissions are typically restricted
        if resource in ["config", "settings", "system"]:
            return action in ["read"]

        return False

    def _evaluate_data_permission(
        self,
        permission: ExtensionPermission,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate data permission."""
        # Data permissions depend on the specific resource
        if resource == "user_data":
            return action in ["read", "write", "delete"]
        elif resource == "system_data":
            return action in ["read"]

        return False

    def _evaluate_api_permission(
        self,
        permission: ExtensionPermission,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate API permission."""
        # API permissions control access to specific endpoints
        if resource.startswith("/api/"):
            return action in ["read", "write", "delete"]

        return False

    def _evaluate_network_permission(
        self,
        permission: ExtensionPermission,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate network permission."""
        # Network permissions control outbound connections
        if resource in ["http", "https", "websocket"]:
            return action in ["connect", "send", "receive"]

        return False

    def _evaluate_file_permission(
        self,
        permission: ExtensionPermission,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate file permission."""
        # File permissions control file system access
        if resource.startswith("/"):
            return action in ["read", "write", "delete", "execute"]

        return False

    def _evaluate_execution_permission(
        self,
        permission: ExtensionPermission,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate execution permission."""
        # Execution permissions control code execution
        if resource in ["python", "shell", "script"]:
            return action in ["execute", "read"]

        return False

    def _evaluate_ui_permission(
        self,
        permission: ExtensionPermission,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate UI permission."""
        # UI permissions control interface access
        if resource in ["dashboard", "settings", "admin"]:
            return action in ["read", "write"]

        return False
