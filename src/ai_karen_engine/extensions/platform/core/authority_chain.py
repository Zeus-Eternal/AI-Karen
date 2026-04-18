"""
Authority Chain Service - Manages authority boundaries and verification between backend and frontend.

This service establishes clear authority boundaries and ensures that lifecycle rules
are enforced throughout the plugin system.
"""

from __future__ import annotations

import logging
import hashlib
import json
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import asyncio
from datetime import datetime

from extensions.core.manifest import ExtensionManifest, ExtensionStatus
from extensions.core.registry.database_service import get_database_service

logger = logging.getLogger("kari.authority_chain")


class AuthorityLevel(str, Enum):
    """Authority levels for different system components."""

    SYSTEM = "system"  # Highest authority - core system functions
    ADMIN = "admin"  # Administrative functions
    PLUGIN = "plugin"  # Plugin runtime authority
    FRONTEND = "frontend"  # Frontend UI authority
    USER = "user"  # User-level authority
    GUEST = "guest"  # Lowest authority - read-only access


class LifecycleStage(str, Enum):
    """Plugin lifecycle stages with strict separation."""

    DISCOVERED = "discovered"  # Found but not processed
    DOWNLOADED = "downloaded"  # Package downloaded
    VALIDATED = "validated"  # Manifest validated
    INSTALLED = "installed"  # Files installed on disk
    REGISTERED = "registered"  # Registered with system
    MOUNTED = "mounted"  # Mounted in runtime
    ENABLED = "enabled"  # Active and running
    DISABLED = "disabled"  # Installed but inactive
    UNINSTALLED = "uninstalled"  # Removed from system


class TransitionEvent(Enum):
    """Events that trigger state transitions."""

    DOWNLOAD_START = "download_start"
    DOWNLOAD_COMPLETE = "download_complete"
    DOWNLOAD_FAILED = "download_failed"

    EXTRACT_START = "extract_start"
    EXTRACT_COMPLETE = "extract_complete"
    EXTRACT_FAILED = "extract_failed"

    VALIDATE_START = "validate_start"
    VALIDATE_COMPLETE = "validate_complete"
    VALIDATE_FAILED = "validate_failed"

    INSTALL_START = "install_start"
    INSTALL_COMPLETE = "install_complete"
    INSTALL_FAILED = "install_failed"

    UNINSTALL_START = "uninstall_start"
    UNINSTALL_COMPLETE = "uninstall_complete"
    UNINSTALL_FAILED = "uninstall_failed"

    UPDATE_START = "update_start"
    UPDATE_COMPLETE = "update_complete"
    UPDATE_FAILED = "update_failed"

    RESTORE_START = "restore_start"
    RESTORE_COMPLETE = "restore_complete"
    RESTORE_FAILED = "restore_failed"

    ENABLE_START = "enable_start"
    ENABLE_COMPLETE = "enable_complete"
    ENABLE_FAILED = "enable_failed"

    DISABLE_START = "disable_start"
    DISABLE_COMPLETE = "disable_complete"
    DISABLE_FAILED = "disable_failed"

    ERROR_OCCURRED = "error_occurred"
    RESET = "reset"


@dataclass
class StateTransition:
    """Record of a state transition."""

    plugin_name: str
    from_state: ExtensionState
    to_state: ExtensionState
    event: TransitionEvent
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CanonicalSource:
    """Represents the canonical source of a plugin/extension."""

    source_type: str  # "file", "url", "registry", "marketplace"
    source_path: str
    checksum: str
    verified: bool = False
    verified_at: Optional[datetime] = None
    authority_level: AuthorityLevel = AuthorityLevel.USER

    def verify_checksum(self, content: bytes) -> bool:
        """Verify the content matches the expected checksum."""
        content_hash = hashlib.sha256(content).hexdigest()
        if content_hash == self.checksum:
            self.verified = True
            self.verified_at = datetime.utcnow()
            return True
        return False


@dataclass
class AuthorityRecord:
    """Authority record tracking permissions and boundaries."""

    plugin_name: str
    authority_level: AuthorityLevel
    allowed_actions: Set[str] = field(default_factory=set)
    forbidden_actions: Set[str] = field(default_factory=set)
    lifecycle_stage: LifecycleStage = LifecycleStage.DISCOVERED
    canonical_source: Optional[CanonicalSource] = None
    category: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def can_perform(self, action: str) -> bool:
        """Check if this authority record allows a specific action."""
        return action in self.allowed_actions and action not in self.forbidden_actions

    def escalate_authority(self, new_level: AuthorityLevel) -> bool:
        """Escalate authority level if allowed."""
        authority_hierarchy = {
            AuthorityLevel.GUEST: 0,
            AuthorityLevel.USER: 1,
            AuthorityLevel.FRONTEND: 2,
            AuthorityLevel.PLUGIN: 3,
            AuthorityLevel.ADMIN: 4,
            AuthorityLevel.SYSTEM: 5,
        }

        if authority_hierarchy[new_level] > authority_hierarchy[self.authority_level]:
            self.authority_level = new_level
            self.updated_at = datetime.utcnow()
            return True
        return False


class AuthorityChainService:
    """
    Central authority service managing boundaries and lifecycle rules.

    Responsibilities:
    - Enforce authority boundaries between backend and frontend
    - Validate canonical plugin sources
    - Ensure strict lifecycle separation
    - Manage authority verification and escalation
    """

    # Valid categories for Phase 1
    VALID_CATEGORIES = {"plugins", "sys_extensions", "channels"}

    # Authority actions by level
    AUTHORITY_ACTIONS = {
        AuthorityLevel.SYSTEM: {
            "install",
            "uninstall",
            "enable",
            "disable",
            "configure",
            "manage",
        },
        AuthorityLevel.ADMIN: {
            "install",
            "uninstall",
            "enable",
            "disable",
            "configure",
            "manage",
        },
        AuthorityLevel.PLUGIN: {"execute", "access_data", "communicate", "log"},
        AuthorityLevel.FRONTEND: {"display", "interact", "configure_ui", "refresh"},
        AuthorityLevel.USER: {"view", "use", "configure", "mount"},
        AuthorityLevel.GUEST: {"view"},
    }

    # Lifecycle transitions (strict separation)
    LIFECYCLE_TRANSITIONS = {
        LifecycleStage.DISCOVERED: {LifecycleStage.DOWNLOADED},
        LifecycleStage.DOWNLOADED: {LifecycleStage.VALIDATED},
        LifecycleStage.VALIDATED: {LifecycleStage.INSTALLED},
        LifecycleStage.INSTALLED: {LifecycleStage.REGISTERED},
        LifecycleStage.REGISTERED: {LifecycleStage.MOUNTED},
        LifecycleStage.MOUNTED: {LifecycleStage.ENABLED, LifecycleStage.DISABLED},
        LifecycleStage.ENABLED: {LifecycleStage.DISABLED},
        LifecycleStage.DISABLED: {LifecycleStage.ENABLED, LifecycleStage.UNINSTALLED},
        LifecycleStage.UNINSTALLED: {LifecycleStage.DISCOVERED},
    }

    def __init__(self, database_service=None):
        """Initialize the authority chain service."""
        self.authority_records: Dict[str, AuthorityRecord] = {}
        self.canonical_sources: Dict[str, CanonicalSource] = {}
        self.database_service = database_service  # Allow None for testing

        logger.info("AuthorityChainService initialized")

    def validate_category(self, category: str) -> bool:
        """Validate that a category is allowed."""
        return category in self.VALID_CATEGORIES

    def create_canonical_source(
        self,
        source_type: str,
        source_path: str,
        content: bytes,
        authority_level: AuthorityLevel = AuthorityLevel.USER,
    ) -> CanonicalSource:
        """Create and verify a canonical source."""
        checksum = hashlib.sha256(content).hexdigest()

        canonical_source = CanonicalSource(
            source_type=source_type,
            source_path=source_path,
            checksum=checksum,
            authority_level=authority_level,
        )

        # Verify the content
        if canonical_source.verify_checksum(content):
            logger.info(f"Canonical source verified: {source_path}")
        else:
            logger.warning(f"Canonical source verification failed: {source_path}")

        return canonical_source

    def register_plugin(
        self,
        plugin_name: str,
        category: str,
        authority_level: AuthorityLevel = AuthorityLevel.USER,
        canonical_source: Optional[CanonicalSource] = None,
    ) -> AuthorityRecord:
        """Register a new plugin with the authority chain."""

        # Validate category
        if not self.validate_category(category):
            raise AuthorityViolation(
                f"Invalid category: {category}. Valid categories: {self.VALID_CATEGORIES}"
            )

        # Create authority record
        allowed_actions = self.AUTHORITY_ACTIONS.get(authority_level, set())

        authority_record = AuthorityRecord(
            plugin_name=plugin_name,
            authority_level=authority_level,
            allowed_actions=allowed_actions,
            lifecycle_stage=LifecycleStage.DISCOVERED,
            canonical_source=canonical_source,
            category=category,
        )

        self.authority_records[plugin_name] = authority_record

        if canonical_source:
            self.canonical_sources[plugin_name] = canonical_source

        logger.info(
            f"Plugin registered: {plugin_name} with authority {authority_level.value}"
        )
        return authority_record

    def validate_lifecycle_transition(
        self, plugin_name: str, from_stage: LifecycleStage, to_stage: LifecycleStage
    ) -> bool:
        """Validate that a lifecycle transition is allowed."""

        authority_record = self.authority_records.get(plugin_name)
        if not authority_record:
            raise AuthorityViolation(f"Plugin not registered: {plugin_name}")

        # Check if transition is valid
        valid_transitions = self.LIFECYCLE_TRANSITIONS.get(from_stage, set())
        if to_stage not in valid_transitions:
            raise LifecycleViolation(
                f"Invalid transition from {from_stage.value} "
                f"via {to_stage.value}. Valid transitions: "
                f"{[e.value for e in valid_transitions.keys()]}"
            )

        # Ensure strict separation rules
        if (
            from_stage == LifecycleStage.DISCOVERED
            and to_stage == LifecycleStage.INSTALLED
        ):
            raise LifecycleViolation(
                f"Cannot skip stages: DISCOVERED → INSTALLED. "
                f"Must follow: DISCOVERED → DOWNLOADED → VALIDATED → INSTALLED"
            )

        if (
            from_stage == LifecycleStage.INSTALLED
            and to_stage == LifecycleStage.MOUNTED
        ):
            raise LifecycleViolation(
                f"Cannot skip stages: INSTALLED → MOUNTED. "
                f"Must follow: INSTALLED → REGISTERED → MOUNTED"
            )

        if (
            from_stage == LifecycleStage.REGISTERED
            and to_stage == LifecycleStage.ENABLED
        ):
            raise LifecycleViolation(
                f"Cannot skip stages: REGISTERED → ENABLED. "
                f"Must follow: REGISTERED → MOUNTED → ENABLED"
            )

        logger.debug(
            f"Lifecycle transition validated: {plugin_name} {from_stage.value} → {to_stage.value}"
        )
        return True

    def transition_lifecycle_stage(
        self,
        plugin_name: str,
        to_stage: LifecycleStage,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Transition a plugin to a new lifecycle stage."""

        authority_record = self.authority_records.get(plugin_name)
        if not authority_record:
            raise AuthorityViolation(f"Plugin not registered: {plugin_name}")

        from_stage = authority_record.lifecycle_stage

        # Validate the transition
        self.validate_lifecycle_transition(plugin_name, from_stage, to_stage)

        # Perform the transition
        authority_record.lifecycle_stage = to_stage
        authority_record.updated_at = datetime.utcnow()

        logger.info(f"Plugin {plugin_name} transitioned to {to_stage.value}")

        # Persist to database if available
        if self.database_service:
            asyncio.create_task(self._persist_transition(authority_record, metadata))

        return True

    def verify_authority_boundary(
        self, plugin_name: str, requested_action: str, caller_level: AuthorityLevel
    ) -> bool:
        """Verify that an action crosses authority boundaries appropriately."""

        authority_record = self.authority_records.get(plugin_name)
        if not authority_record:
            raise AuthorityViolation(f"Plugin not registered: {plugin_name}")

        plugin_level = authority_record.authority_level

        # Check if caller has sufficient authority
        if not self._has_sufficient_authority(caller_level, plugin_level):
            raise AuthorityViolation(
                f"Caller {caller_level.value} cannot perform {requested_action} on "
                f"plugin {plugin_name} (level: {plugin_level.value})"
            )

        # Check if plugin allows the action
        if not authority_record.can_perform(requested_action):
            raise AuthorityViolation(
                f"Plugin {plugin_name} does not allow action: {requested_action}"
            )

        logger.debug(
            f"Authority boundary verified: {caller_level.value} → {plugin_name} ({requested_action})"
        )
        return True

    def _has_sufficient_authority(
        self, caller_level: AuthorityLevel, target_level: AuthorityLevel
    ) -> bool:
        """Check if caller has sufficient authority for target."""
        authority_hierarchy = {
            AuthorityLevel.GUEST: 0,
            AuthorityLevel.USER: 1,
            AuthorityLevel.FRONTEND: 2,
            AuthorityLevel.PLUGIN: 3,
            AuthorityLevel.ADMIN: 4,
            AuthorityLevel.SYSTEM: 5,
        }

        return authority_hierarchy[caller_level] >= authority_hierarchy[target_level]

    def get_plugin_authority(self, plugin_name: str) -> Optional[AuthorityRecord]:
        """Get authority record for a plugin."""
        return self.authority_records.get(plugin_name)

    def get_plugins_by_authority_level(
        self, authority_level: AuthorityLevel
    ) -> List[str]:
        """Get all plugins with a specific authority level."""
        return [
            name
            for name, record in self.authority_records.items()
            if record.authority_level == authority_level
        ]

    def get_plugins_by_lifecycle_stage(
        self, lifecycle_stage: LifecycleStage
    ) -> List[str]:
        """Get all plugins in a specific lifecycle stage."""
        return [
            name
            for name, record in self.authority_records.items()
            if record.lifecycle_stage == lifecycle_stage
        ]

    def enforce_lifecycle_rules(self) -> Dict[str, List[str]]:
        """Enforce lifecycle rules and return violations."""
        violations = {
            "discovered_not_installed": [],
            "installed_not_mounted": [],
            "mounted_not_enabled": [],
            "invalid_transitions": [],
        }

        for plugin_name, record in self.authority_records.items():
            stage = record.lifecycle_stage

            # Check discovery ≠ installation
            if stage == LifecycleStage.INSTALLED:
                violations["discovered_not_installed"].append(plugin_name)

            # Check installation ≠ registration
            if stage == LifecycleStage.REGISTERED:
                violations["installed_not_mounted"].append(plugin_name)

            # Check registration ≠ mounting
            if stage == LifecycleStage.ENABLED:
                violations["mounted_not_enabled"].append(plugin_name)

        return violations

    async def _persist_transition(
        self,
        authority_record: AuthorityRecord,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Persist authority transition to database."""
        # Implementation would integrate with database service
        pass

    def get_authority_chain_report(self) -> Dict[str, Any]:
        """Generate comprehensive authority chain report."""

        total_plugins = len(self.authority_records)
        authority_distribution = {}
        lifecycle_distribution = {}

        for record in self.authority_records.values():
            # Authority distribution
            auth_level = record.authority_level.value
            authority_distribution[auth_level] = (
                authority_distribution.get(auth_level, 0) + 1
            )

            # Lifecycle distribution
            lifecycle_stage = record.lifecycle_stage.value
            lifecycle_distribution[lifecycle_stage] = (
                lifecycle_distribution.get(lifecycle_stage, 0) + 1
            )

        # Check for violations
        violations = self.enforce_lifecycle_rules()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_plugins": total_plugins,
            "authority_distribution": authority_distribution,
            "lifecycle_distribution": lifecycle_distribution,
            "violations": violations,
            "valid_categories": list(self.VALID_CATEGORIES),
            "health_status": "healthy"
            if not any(violations.values())
            else "violations_detected",
        }


# Global singleton instance
_authority_chain_service: Optional[AuthorityChainService] = None


def get_authority_chain_service(database_service=None) -> AuthorityChainService:
    """Get the global authority chain service instance."""
    global _authority_chain_service
    if _authority_chain_service is None:
        _authority_chain_service = AuthorityChainService(
            database_service=database_service
        )
    return _authority_chain_service


class AuthorityViolation(Exception):
    """Raised when authority boundaries are violated."""

    pass


class LifecycleViolation(Exception):
    """Raised when lifecycle rules are violated."""

    pass


__all__ = [
    "AuthorityChainService",
    "AuthorityLevel",
    "LifecycleStage",
    "AuthorityViolation",
    "LifecycleViolation",
    "CanonicalSource",
    "AuthorityRecord",
    "get_authority_chain_service",
]
