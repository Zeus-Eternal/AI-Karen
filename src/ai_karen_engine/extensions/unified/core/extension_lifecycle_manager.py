"""
Unified Extension Lifecycle Manager

Consolidates the best features from both platform/core and runtime lifecycle management systems.
Provides comprehensive lifecycle management with state transitions, event handling, and dependency resolution.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from ..database_models import ExtensionModel, ExtensionState


logger = logging.getLogger(__name__)


class ExtensionLifecycleState(str, Enum):
    """Extension lifecycle states."""

    UNINSTALLED = "uninstalled"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPGRADING = "upgrading"
    RELOADING = "reloading"


@dataclass
class ExtensionLifecycleEvent:
    """Extension lifecycle event."""

    id: str
    extension_id: str
    event_type: str
    from_state: ExtensionLifecycleState
    to_state: ExtensionLifecycleState
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    triggered_by: Optional[str] = None


class ExtensionLifecycleManager:
    """Unified extension lifecycle management system."""

    def __init__(self, registry=None):
        self.registry = registry
        self._lifecycle_state: Dict[str, ExtensionLifecycleState] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._transition_handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

        # Lifecycle state machine
        self._state_transitions = self._setup_state_transitions()

        # Event history
        self._event_history: List[ExtensionLifecycleEvent] = []
        self._max_events = 1000

        # Dependency tracking
        self._dependency_graph: Dict[str, set] = {}

    async def initialize(self) -> None:
        """Initialize the lifecycle manager."""
        # Load existing lifecycle state
        await self._load_lifecycle_state()

        # Setup default transition handlers
        self._setup_default_transition_handlers()

        logger.info("Extension lifecycle manager initialized")

    async def transition_state(
        self,
        extension_id: str,
        new_state: ExtensionLifecycleState,
        data: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None,
    ) -> bool:
        """Transition an extension to a new state."""
        async with self._lock:
            # Get current state
            current_state = self._lifecycle_state.get(
                extension_id, ExtensionLifecycleState.UNINSTALLED
            )

            # Validate transition
            if not self._is_valid_transition(current_state, new_state):
                logger.error(
                    f"Invalid state transition: {current_state} -> {new_state}"
                )
                return False

            # Call transition handler
            handler_result = await self._call_transition_handler(
                extension_id, current_state, new_state, data
            )

            if not handler_result:
                logger.error(f"Transition handler failed for {extension_id}")
                return False

            # Create event
            event = ExtensionLifecycleEvent(
                id=str(uuid.uuid4()),
                extension_id=extension_id,
                event_type="state_transition",
                from_state=current_state,
                to_state=new_state,
                timestamp=datetime.now(timezone.utc).timestamp(),
                data=data or {},
                triggered_by=triggered_by,
            )

            # Update state
            self._lifecycle_state[extension_id] = new_state

            # Store event
            self._store_event(event)

            # Notify event handlers
            await self._notify_event_handlers(event)

            logger.info(
                f"State transition: {extension_id} {current_state} -> {new_state}"
            )
            return True

    async def get_extension_state(self, extension_id: str) -> ExtensionLifecycleState:
        """Get current state of an extension."""
        return self._lifecycle_state.get(
            extension_id, ExtensionLifecycleState.UNINSTALLED
        )

    async def get_all_extension_states(self) -> Dict[str, ExtensionLifecycleState]:
        """Get states of all extensions."""
        return self._lifecycle_state.copy()

    async def get_extension_event_history(
        self, extension_id: str, limit: int = 100
    ) -> List[ExtensionLifecycleEvent]:
        """Get event history for an extension."""
        events = [
            event for event in self._event_history if event.extension_id == extension_id
        ]
        return events[-limit:]

    async def get_all_event_history(
        self, limit: int = 100
    ) -> List[ExtensionLifecycleEvent]:
        """Get all event history."""
        return self._event_history[-limit:]

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for: {event_type}")

    def register_transition_handler(
        self, transition_key: str, handler: Callable
    ) -> None:
        """Register a state transition handler."""
        self._transition_handlers[transition_key] = handler
        logger.info(f"Registered transition handler for: {transition_key}")

    async def install_extension(
        self, extension_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Install an extension."""
        return await self.transition_state(
            extension_id, ExtensionLifecycleState.INSTALLED, data, "install"
        )

    async def enable_extension(
        self, extension_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Enable an extension."""
        return await self.transition_state(
            extension_id, ExtensionLifecycleState.ENABLED, data, "enable"
        )

    async def disable_extension(
        self, extension_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Disable an extension."""
        return await self.transition_state(
            extension_id, ExtensionLifecycleState.DISABLED, data, "disable"
        )

    async def uninstall_extension(
        self, extension_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Uninstall an extension."""
        return await self.transition_state(
            extension_id, ExtensionLifecycleState.UNINSTALLED, data, "uninstall"
        )

    async def upgrade_extension(
        self, extension_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Upgrade an extension."""
        return await self.transition_state(
            extension_id, ExtensionLifecycleState.UPGRADING, data, "upgrade"
        )

    async def reload_extension(
        self, extension_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Reload an extension."""
        return await self.transition_state(
            extension_id, ExtensionLifecycleState.RELOADING, data, "reload"
        )

    def _is_valid_transition(
        self, from_state: ExtensionLifecycleState, to_state: ExtensionLifecycleState
    ) -> bool:
        """Check if a state transition is valid."""
        return to_state in self._state_transitions.get(from_state, set())

    def _setup_state_transitions(self) -> Dict[ExtensionLifecycleState, set]:
        """Setup valid state transitions."""
        transitions = {
            ExtensionLifecycleState.UNINSTALLED: {ExtensionLifecycleState.INSTALLED},
            ExtensionLifecycleState.INSTALLED: {
                ExtensionLifecycleState.ENABLED,
                ExtensionLifecycleState.UNINSTALLED,
            },
            ExtensionLifecycleState.ENABLED: {
                ExtensionLifecycleState.DISABLED,
                ExtensionLifecycleState.UPGRADING,
                ExtensionLifecycleState.UNINSTALLED,
            },
            ExtensionLifecycleState.DISABLED: {
                ExtensionLifecycleState.ENABLED,
                ExtensionLifecycleState.UNINSTALLED,
            },
            ExtensionLifecycleState.ERROR: {
                ExtensionLifecycleState.INSTALLED,
                ExtensionLifecycleState.UNINSTALLED,
            },
            ExtensionLifecycleState.UPGRADING: {
                ExtensionLifecycleState.ENABLED,
                ExtensionLifecycleState.INSTALLED,
                ExtensionLifecycleState.UNINSTALLED,
            },
            ExtensionLifecycleState.RELOADING: {
                ExtensionLifecycleState.ENABLED,
                ExtensionLifecycleState.INSTALLED,
                ExtensionLifecycleState.UNINSTALLED,
            },
        }

        return transitions

    def _setup_default_transition_handlers(self) -> None:
        """Setup default transition handlers."""

        # Install handler
        async def handle_install(
            extension_id: str,
            from_state: ExtensionLifecycleState,
            to_state: ExtensionLifecycleState,
            data: Dict[str, Any],
        ) -> bool:
            if self.registry:
                extension = await self.registry.get_extension(extension_id)
                if extension:
                    # Update extension state in registry
                    await self.registry.update_extension(
                        extension_id, {"state": to_state.value}
                    )
                    return True
            return False

        self.register_transition_handler("uninstalled->installed", handle_install)

        # Enable handler
        async def handle_enable(
            extension_id: str,
            from_state: ExtensionLifecycleState,
            to_state: ExtensionLifecycleState,
            data: Dict[str, Any],
        ) -> bool:
            # Check dependencies
            if await self._check_dependencies(extension_id):
                logger.info(f"Dependencies satisfied for {extension_id}")
                return True
            else:
                logger.warning(f"Dependencies not satisfied for {extension_id}")
                return False

        self.register_transition_handler("installed->enabled", handle_enable)

        # Disable handler
        async def handle_disable(
            extension_id: str,
            from_state: ExtensionLifecycleState,
            to_state: ExtensionLifecycleState,
            data: Dict[str, Any],
        ) -> bool:
            # Check if any extensions depend on this one
            if await self._has_dependents(extension_id):
                logger.warning(f"Cannot disable {extension_id}: has dependents")
                return False
            return True

        self.register_transition_handler("enabled->disabled", handle_disable)

        # Uninstall handler
        async def handle_uninstall(
            extension_id: str,
            from_state: ExtensionLifecycleState,
            to_state: ExtensionLifecycleState,
            data: Dict[str, Any],
        ) -> bool:
            # Check if any extensions depend on this one
            if await self._has_dependents(extension_id):
                logger.warning(f"Cannot uninstall {extension_id}: has dependents")
                return False
            return True

        self.register_transition_handler("enabled->uninstalled", handle_uninstall)
        self.register_transition_handler("disabled->uninstalled", handle_uninstall)

    async def _call_transition_handler(
        self,
        extension_id: str,
        from_state: ExtensionLifecycleState,
        to_state: ExtensionLifecycleState,
        data: Dict[str, Any],
    ) -> bool:
        """Call a transition handler."""
        transition_key = f"{from_state.value}->{to_state.value}"

        if transition_key in self._transition_handlers:
            handler = self._transition_handlers[transition_key]
            try:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(extension_id, from_state, to_state, data)
                else:
                    return handler(extension_id, from_state, to_state, data)
            except Exception as e:
                logger.error(f"Error in transition handler {transition_key}: {e}")
                return False

        return True

    async def _notify_event_handlers(self, event: ExtensionLifecycleEvent) -> None:
        """Notify all registered event handlers."""
        if event.event_type in self._event_handlers:
            for handler in self._event_handlers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

    def _store_event(self, event: ExtensionLifecycleEvent) -> None:
        """Store a lifecycle event."""
        self._event_history.append(event)

        # Limit event history size
        if len(self._event_history) > self._max_events:
            self._event_history = self._event_history[-self._max_events :]

    async def _load_lifecycle_state(self) -> None:
        """Load existing lifecycle state."""
        if self.registry:
            extensions = await self.registry.list_extensions()
            for extension in extensions:
                self._lifecycle_state[extension.id] = ExtensionLifecycleState(
                    extension.state
                )

        logger.info("Loaded lifecycle state from registry")

    async def _check_dependencies(self, extension_id: str) -> bool:
        """Check if extension dependencies are satisfied."""
        if not self.registry:
            return True

        extension = await self.registry.get_extension(extension_id)
        if not extension:
            return False

        manifest = extension.manifest
        dependencies = manifest.get("dependencies", {})

        for dep_name, dep_version in dependencies.items():
            dep_extension = await self.registry.get_extension_by_name(dep_name)
            if not dep_extension:
                return False

            dep_state = ExtensionLifecycleState(dep_extension.state)
            if dep_state != ExtensionLifecycleState.ENABLED:
                return False

        return True

    async def _has_dependents(self, extension_id: str) -> bool:
        """Check if any extensions depend on this one."""
        if not self.registry:
            return False

        extensions = await self.registry.list_extensions()
        for extension in extensions:
            if extension.id == extension_id:
                continue

            manifest = extension.manifest
            dependencies = manifest.get("dependencies", {})

            if extension_id in dependencies:
                return True

        return False
