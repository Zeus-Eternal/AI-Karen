"""
Frontend Integration Service - Bridges authority chain with frontend plugin host.

This service ensures that the frontend plugin host respects the authority chain
and lifecycle rules established by the backend services.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from extensions.core.authority_chain import (
    AuthorityChainService,
    AuthorityLevel,
    LifecycleStage,
    AuthorityRecord,
    AuthorityViolation,
    get_authority_chain_service,
)
from extensions.core.lifecycle_validation import (
    LifecycleValidationService,
    get_lifecycle_validation_service,
)
from extensions.core.category_validation import (
    CategoryValidationService,
    CategoryType,
    get_category_validation_service,
)

logger = logging.getLogger("kari.frontend_integration")


class FrontendPermission(str, Enum):
    """Frontend-specific permissions."""

    VIEW_PLUGIN = "view_plugin"
    INTERACT_WITH_PLUGIN = "interact_with_plugin"
    CONFIGURE_PLUGIN_UI = "configure_plugin_ui"
    MOUNT_PLUGIN_COMPONENT = "mount_plugin_component"
    UNMOUNT_PLUGIN_COMPONENT = "unmount_plugin_component"
    REFRESH_PLUGIN_CATALOG = "refresh_plugin_catalog"


@dataclass
class FrontendPluginRecord:
    """Frontend representation of a plugin with authority information."""

    plugin_id: str
    display_name: str
    description: str
    category: str
    authority_level: AuthorityLevel
    lifecycle_stage: LifecycleStage
    is_visible: bool = True
    is_mountable: bool = False
    is_configurable: bool = False
    required_permissions: Set[FrontendPermission] = field(default_factory=set)
    ui_components: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FrontendValidationResult:
    """Result of frontend validation."""

    is_valid: bool
    plugin_id: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    frontend_record: Optional[FrontendPluginRecord] = None


class FrontendIntegrationService:
    """
    Service that bridges backend authority chain with frontend plugin host.

    Responsibilities:
    - Filter plugins based on user authority and frontend permissions
    - Enforce lifecycle rules in frontend operations
    - Validate frontend plugin requests against backend authority
    - Provide canonical plugin catalog to frontend
    - Handle frontend plugin mounting/unmounting with authority checks
    """

    def __init__(self, authority_chain_service: AuthorityChainService):
        """Initialize frontend integration service."""
        self.authority_chain = authority_chain_service
        self.lifecycle_validation = get_lifecycle_validation_service(
            authority_chain_service
        )
        self.category_validation = get_category_validation_service()

        # Frontend plugin registry
        self.frontend_registry: Dict[str, FrontendPluginRecord] = {}

        # User permissions mapping (would come from authentication system)
        self.user_permissions: Dict[str, Set[FrontendPermission]] = {}

        logger.info("FrontendIntegrationService initialized")

    def register_user_permissions(
        self, user_id: str, permissions: Set[FrontendPermission]
    ):
        """Register frontend permissions for a user."""
        self.user_permissions[user_id] = permissions
        logger.debug(f"Registered permissions for user {user_id}")

    def sync_frontend_registry(self) -> Dict[str, FrontendPluginRecord]:
        """
        Synchronize frontend registry with backend authority chain.

        Returns:
            Dictionary of frontend plugin records
        """
        logger.info("Synchronizing frontend registry with backend authority chain")

        # Clear existing registry
        self.frontend_registry.clear()

        # Get all plugins from authority chain
        for (
            plugin_name,
            authority_record,
        ) in self.authority_chain.authority_records.items():
            frontend_record = self._create_frontend_record(authority_record)
            if frontend_record:
                self.frontend_registry[plugin_name] = frontend_record

        logger.info(
            f"Synchronized {len(self.frontend_registry)} plugins to frontend registry"
        )
        return self.frontend_registry

    def _create_frontend_record(
        self, authority_record: AuthorityRecord
    ) -> Optional[FrontendPluginRecord]:
        """Create a frontend plugin record from authority record."""
        try:
            # Get category information from authority record
            if not authority_record.category:
                logger.warning(
                    f"No category info for plugin: {authority_record.plugin_name}"
                )
                return None

            category_info = self.category_validation.get_category_info(
                authority_record.category
            )
            if not category_info:
                logger.warning(
                    f"No category info for plugin: {authority_record.plugin_name}"
                )
                return None

            # Determine frontend visibility based on authority level
            is_visible = self._is_frontend_visible(authority_record.authority_level)

            # Determine mountability based on lifecycle stage
            is_mountable = authority_record.lifecycle_stage in [
                LifecycleStage.MOUNTED,
                LifecycleStage.ENABLED,
                LifecycleStage.DISABLED,
            ]

            # Determine configurability
            is_configurable = authority_record.lifecycle_stage in [
                LifecycleStage.ENABLED,
                LifecycleStage.DISABLED,
            ]

            # Calculate required frontend permissions
            required_permissions = self._calculate_required_permissions(
                authority_record.authority_level,
                authority_record.lifecycle_stage,
                category_info["name"],
            )

            return FrontendPluginRecord(
                plugin_id=authority_record.plugin_name,
                display_name=category_info.get(
                    "display_name", authority_record.plugin_name
                ),
                description=category_info.get("description", ""),
                category=category_info["name"],
                authority_level=authority_record.authority_level,
                lifecycle_stage=authority_record.lifecycle_stage,
                is_visible=is_visible,
                is_mountable=is_mountable,
                is_configurable=is_configurable,
                required_permissions=required_permissions,
                ui_components=self._get_ui_components(authority_record.plugin_name),
                last_updated=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(
                f"Failed to create frontend record for {authority_record.plugin_name}: {str(e)}"
            )
            return None

    def _is_frontend_visible(self, authority_level: AuthorityLevel) -> bool:
        """Determine if a plugin should be visible in frontend based on authority level."""
        # Higher authority levels are visible to lower levels
        authority_hierarchy = {
            AuthorityLevel.GUEST: 0,
            AuthorityLevel.USER: 1,
            AuthorityLevel.FRONTEND: 2,
            AuthorityLevel.PLUGIN: 3,
            AuthorityLevel.ADMIN: 4,
            AuthorityLevel.SYSTEM: 5,
        }

        # Plugins with authority level >= current user level are visible
        # For now, assume current user is at USER level
        user_level = AuthorityLevel.USER
        return authority_level.value <= user_level.value

    def _calculate_required_permissions(
        self,
        authority_level: AuthorityLevel,
        lifecycle_stage: LifecycleStage,
        category: str,
    ) -> Set[FrontendPermission]:
        """Calculate required frontend permissions for a plugin."""
        permissions = set()

        # All visible plugins require view permission
        permissions.add(FrontendPermission.VIEW_PLUGIN)

        # Mountable plugins require mount permission
        if lifecycle_stage in [LifecycleStage.MOUNTED, LifecycleStage.ENABLED]:
            permissions.add(FrontendPermission.MOUNT_PLUGIN_COMPONENT)

        # Configurable plugins require configure permission
        if lifecycle_stage in [LifecycleStage.ENABLED, LifecycleStage.DISABLED]:
            permissions.add(FrontendPermission.CONFIGURE_PLUGIN_UI)

        # Plugins with UI components require interaction permission
        if category == CategoryType.PLUGINS.value:
            permissions.add(FrontendPermission.INTERACT_WITH_PLUGIN)

        return permissions

    def _get_ui_components(self, plugin_name: str) -> List[str]:
        """Get UI components for a plugin (placeholder implementation)."""
        # This would read from the plugin's manifest.json or UI configuration
        return ["main_component", "settings_component"]

    def get_frontend_catalog(
        self, user_id: str, include_hidden: bool = False
    ) -> Dict[str, FrontendPluginRecord]:
        """
        Get frontend plugin catalog filtered by user permissions.

        Args:
            user_id: User ID to filter permissions for
            include_hidden: Whether to include plugins not normally visible

        Returns:
            Filtered catalog of plugins the user can access
        """
        user_permissions = self.user_permissions.get(user_id, set())
        catalog = {}

        for plugin_id, record in self.frontend_registry.items():
            # Check visibility
            if not record.is_visible and not include_hidden:
                continue

            # Check user permissions
            if not user_permissions.issuperset(record.required_permissions):
                continue

            catalog[plugin_id] = record

        logger.debug(
            f"Frontend catalog generated for user {user_id}: {len(catalog)} plugins"
        )
        return catalog

    def validate_frontend_request(
        self,
        user_id: str,
        plugin_id: str,
        requested_action: str,
        action_params: Optional[Dict[str, Any]] = None,
    ) -> FrontendValidationResult:
        """
        Validate a frontend request against authority rules.

        Args:
            user_id: User making the request
            plugin_id: Plugin ID being accessed
            requested_action: Action being requested
            action_params: Additional parameters for the action

        Returns:
            FrontendValidationResult with validation results
        """
        result = FrontendValidationResult(is_valid=True, plugin_id=plugin_id)

        try:
            # Check if plugin exists in frontend registry
            plugin_record = self.frontend_registry.get(plugin_id)
            if not plugin_record:
                result.is_valid = False
                result.errors.append(f"Plugin not found: {plugin_id}")
                return result

            # Check user permissions
            user_permissions = self.user_permissions.get(user_id, set())

            # Map requested action to frontend permission
            required_permission = self._map_action_to_permission(requested_action)
            if required_permission and required_permission not in user_permissions:
                result.is_valid = False
                result.errors.append(
                    f"User {user_id} lacks permission: {required_permission.value}"
                )
                return result

            # Check authority boundary
            try:
                self.authority_chain.verify_authority_boundary(
                    plugin_id,
                    requested_action,
                    AuthorityLevel.FRONTEND,  # Frontend is making the request
                )
            except AuthorityViolation as e:
                result.is_valid = False
                result.errors.append(f"Authority violation: {str(e)}")
                return result

            # Check lifecycle stage compatibility
            lifecycle_error = self._validate_lifecycle_action(
                plugin_record.lifecycle_stage, requested_action
            )
            if lifecycle_error:
                result.is_valid = False
                result.errors.append(lifecycle_error)
                return result

            # Check category-specific rules
            category_error = self._validate_category_action(
                plugin_record.category, requested_action, action_params
            )
            if category_error:
                result.is_valid = False
                result.errors.append(category_error)
                return result

            # If all checks pass, set the frontend record
            result.frontend_record = plugin_record

        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Unexpected error: {str(e)}")

        return result

    def _map_action_to_permission(self, action: str) -> Optional[FrontendPermission]:
        """Map a requested action to frontend permission."""
        action_mapping = {
            "view": FrontendPermission.VIEW_PLUGIN,
            "interact": FrontendPermission.INTERACT_WITH_PLUGIN,
            "configure": FrontendPermission.CONFIGURE_PLUGIN_UI,
            "mount": FrontendPermission.MOUNT_PLUGIN_COMPONENT,
            "unmount": FrontendPermission.UNMOUNT_PLUGIN_COMPONENT,
            "refresh": FrontendPermission.REFRESH_PLUGIN_CATALOG,
        }
        return action_mapping.get(action)

    def _validate_lifecycle_action(
        self, lifecycle_stage: LifecycleStage, requested_action: str
    ) -> Optional[str]:
        """Validate that an action is compatible with the current lifecycle stage."""

        if requested_action in ["mount", "interact", "configure"]:
            if lifecycle_stage in [
                LifecycleStage.DISCOVERED,
                LifecycleStage.DOWNLOADED,
                LifecycleStage.VALIDATED,
            ]:
                return (
                    f"Cannot {requested_action} plugin in {lifecycle_stage.value} stage"
                )

        if requested_action == "unmount":
            if lifecycle_stage not in [
                LifecycleStage.MOUNTED,
                LifecycleStage.ENABLED,
                LifecycleStage.DISABLED,
            ]:
                return f"Cannot unmount plugin in {lifecycle_stage.value} stage"

        return None

    def _validate_category_action(
        self,
        category: str,
        requested_action: str,
        action_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Validate category-specific action rules."""

        if category == CategoryType.SYS_EXTENSIONS.value:
            if requested_action in ["configure", "unmount"]:
                return f"Cannot {requested_action} system extensions"

        if category == CategoryType.CHANNELS.value:
            if requested_action == "configure" and action_params:
                # Channels might require special configuration validation
                if "protocol" not in action_params:
                    return "Channel configuration requires protocol specification"

        return None

    def request_plugin_mount(
        self,
        user_id: str,
        plugin_id: str,
        component_id: str,
        mount_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Request to mount a plugin component.

        Args:
            user_id: User making the request
            plugin_id: Plugin ID to mount
            component_id: Component ID to mount
            mount_params: Additional mount parameters

        Returns:
            Tuple of (success, error_messages)
        """
        errors = []

        # Validate the request
        validation_result = self.validate_frontend_request(
            user_id,
            plugin_id,
            "mount",
            {"component_id": component_id, **(mount_params or {})},
        )

        if not validation_result.is_valid:
            return False, validation_result.errors

        # Check if plugin is already mounted
        plugin_record = validation_result.frontend_record
        if plugin_record.lifecycle_stage == LifecycleStage.ENABLED:
            errors.append(f"Plugin {plugin_id} is already mounted and enabled")

        # Try to transition to mounted stage
        try:
            # This would call the authority chain to transition the lifecycle
            # For now, we'll simulate it
            if plugin_record.lifecycle_stage == LifecycleStage.REGISTERED:
                # Would call: self.authority_chain.transition_lifecycle_stage(
                #     plugin_id, LifecycleStage.MOUNTED
                # )
                logger.info(f"Would mount plugin {plugin_id} component {component_id}")
                return True, errors
            elif plugin_record.lifecycle_stage == LifecycleStage.DISABLED:
                # Would call: self.authority_chain.transition_lifecycle_stage(
                #     plugin_id, LifecycleStage.ENABLED
                # )
                logger.info(f"Would enable plugin {plugin_id} component {component_id}")
                return True, errors
            else:
                errors.append(
                    f"Plugin {plugin_id} cannot be mounted from {plugin_record.lifecycle_stage.value} stage"
                )

        except Exception as e:
            errors.append(f"Failed to mount plugin: {str(e)}")

        return False, errors

    def request_plugin_unmount(
        self, user_id: str, plugin_id: str, component_id: str
    ) -> Tuple[bool, List[str]]:
        """
        Request to unmount a plugin component.

        Args:
            user_id: User making the request
            plugin_id: Plugin ID to unmount
            component_id: Component ID to unmount

        Returns:
            Tuple of (success, error_messages)
        """
        errors = []

        # Validate the request
        validation_result = self.validate_frontend_request(
            user_id, plugin_id, "unmount", {"component_id": component_id}
        )

        if not validation_result.is_valid:
            return False, validation_result.errors

        # Check if plugin is mounted
        plugin_record = validation_result.frontend_record
        if plugin_record.lifecycle_stage not in [
            LifecycleStage.MOUNTED,
            LifecycleStage.ENABLED,
        ]:
            errors.append(
                f"Plugin {plugin_id} is not mounted (current stage: {plugin_record.lifecycle_stage.value})"
            )

        # Try to transition to disabled stage
        try:
            # This would call the authority chain to transition the lifecycle
            # For now, we'll simulate it
            if plugin_record.lifecycle_stage == LifecycleStage.ENABLED:
                # Would call: self.authority_chain.transition_lifecycle_stage(
                #     plugin_id, LifecycleStage.DISABLED
                # )
                logger.info(
                    f"Would disable plugin {plugin_id} component {component_id}"
                )
                return True, errors
            elif plugin_record.lifecycle_stage == LifecycleStage.MOUNTED:
                # Would call: self.authority_chain.transition_lifecycle_stage(
                #     plugin_id, LifecycleStage.UNINSTALLED
                # )
                logger.info(
                    f"Would unmount plugin {plugin_id} component {component_id}"
                )
                return True, errors
            else:
                errors.append(
                    f"Plugin {plugin_id} cannot be unmounted from {plugin_record.lifecycle_stage.value} stage"
                )

        except Exception as e:
            errors.append(f"Failed to unmount plugin: {str(e)}")

        return False, errors

    def get_authority_boundary_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get authority boundary status for a user.

        Args:
            user_id: User ID to check

        Returns:
            Dictionary with authority boundary status
        """
        user_permissions = self.user_permissions.get(user_id, set())

        # Count plugins by category and authority level
        category_counts = {}
        authority_counts = {}

        for record in self.frontend_registry.values():
            if record.is_visible:
                # Category counts
                category = record.category
                category_counts[category] = category_counts.get(category, 0) + 1

                # Authority level counts
                auth_level = record.authority_level.value
                authority_counts[auth_level] = authority_counts.get(auth_level, 0) + 1

        return {
            "user_id": user_id,
            "user_permissions": [p.value for p in user_permissions],
            "total_visible_plugins": len(
                [r for r in self.frontend_registry.values() if r.is_visible]
            ),
            "category_distribution": category_counts,
            "authority_distribution": authority_counts,
            "boundary_health": "healthy"
            if len(user_permissions) > 0
            else "no_permissions",
        }


# Global singleton instance
_frontend_integration_service: Optional[FrontendIntegrationService] = None


def get_frontend_integration_service(
    authority_chain_service: AuthorityChainService,
) -> FrontendIntegrationService:
    """Get the global frontend integration service instance."""
    global _frontend_integration_service
    if _frontend_integration_service is None:
        _frontend_integration_service = FrontendIntegrationService(
            authority_chain_service
        )
    return _frontend_integration_service


__all__ = [
    "FrontendIntegrationService",
    "FrontendPermission",
    "FrontendPluginRecord",
    "FrontendValidationResult",
    "get_frontend_integration_service",
]
