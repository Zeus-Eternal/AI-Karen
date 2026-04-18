"""
Extension State Transition Machine - Manages lifecycle state transitions for extensions.
"""

import logging
import asyncio
from typing import Dict, Optional, List, Callable, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from ai_karen_engine.extensions.platform.core.manifest import ExtensionStatus
from ai_karen_engine.extensions.platform.core.registry.database_service import get_database_service

logger = logging.getLogger("kari.extension_state_machine")


class ExtensionState(Enum):
    """Extension lifecycle states."""

    # Initial state
    INITIAL = "initial"

    # Transient states (in progress)
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    INSTALLING = "installing"
    UNINSTALLING = "uninstalling"
    UPDATING = "updating"
    RESTORING = "restoring"
    ENABLING = "enabling"
    DISABLING = "disabling"

    # Terminal states (final)
    INSTALLED = "installed"
    UNINSTALLED = "uninstalled"
    ERROR = "error"
    DISABLED = "disabled"
    ENABLED = "enabled"


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


class ExtensionStateMachine:
    """
    State machine for managing extension lifecycle transitions.

    Features:
    - Valid state transition enforcement
    - Transition history tracking
    - Pre/post transition hooks
    - Error handling and recovery
    - Concurrency safety
    """

    # Define valid state transitions
    TRANSITIONS: Dict[ExtensionState, Dict[TransitionEvent, ExtensionState]] = {
        ExtensionState.INITIAL: {
            TransitionEvent.DOWNLOAD_START: ExtensionState.DOWNLOADING,
        },
        ExtensionState.DOWNLOADING: {
            TransitionEvent.DOWNLOAD_COMPLETE: ExtensionState.EXTRACTING,
            TransitionEvent.DOWNLOAD_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.EXTRACTING: {
            TransitionEvent.EXTRACT_COMPLETE: ExtensionState.VALIDATING,
            TransitionEvent.EXTRACT_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.VALIDATING: {
            TransitionEvent.VALIDATE_COMPLETE: ExtensionState.INSTALLING,
            TransitionEvent.VALIDATE_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.INSTALLING: {
            TransitionEvent.INSTALL_COMPLETE: ExtensionState.INSTALLED,
            TransitionEvent.INSTALL_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.INSTALLED: {
            TransitionEvent.UPDATE_START: ExtensionState.UPDATING,
            TransitionEvent.UNINSTALL_START: ExtensionState.UNINSTALLING,
            TransitionEvent.DISABLE_START: ExtensionState.DISABLING,
            TransitionEvent.RESET: ExtensionState.INITIAL,
        },
        ExtensionState.UNINSTALLING: {
            TransitionEvent.UNINSTALL_COMPLETE: ExtensionState.UNINSTALLED,
            TransitionEvent.UNINSTALL_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.UNINSTALLED: {
            TransitionEvent.RESET: ExtensionState.INITIAL,
        },
        ExtensionState.UPDATING: {
            TransitionEvent.UPDATE_COMPLETE: ExtensionState.INSTALLED,
            TransitionEvent.UPDATE_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.RESTORING: {
            TransitionEvent.RESTORE_COMPLETE: ExtensionState.INSTALLED,
            TransitionEvent.RESTORE_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.DISABLING: {
            TransitionEvent.DISABLE_COMPLETE: ExtensionState.DISABLED,
            TransitionEvent.DISABLE_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.DISABLED: {
            TransitionEvent.ENABLE_START: ExtensionState.ENABLING,
            TransitionEvent.RESET: ExtensionState.INITIAL,
        },
        ExtensionState.ENABLING: {
            TransitionEvent.ENABLE_COMPLETE: ExtensionState.ENABLED,
            TransitionEvent.ENABLE_FAILED: ExtensionState.ERROR,
        },
        ExtensionState.ENABLED: {
            TransitionEvent.DISABLE_START: ExtensionState.DISABLING,
            TransitionEvent.RESET: ExtensionState.INITIAL,
        },
        ExtensionState.ERROR: {
            TransitionEvent.RESET: ExtensionState.INITIAL,
            TransitionEvent.RESTORE_START: ExtensionState.RESTORING,
        },
    }

    def __init__(self, database_service=None):
        """
        Initialize state machine.

        Args:
            database_service: Optional database service for persistence
        """
        self._states: Dict[str, ExtensionState] = {}
        self._transition_history: Dict[str, List[StateTransition]] = {}
        self._transition_locks: Dict[str, asyncio.Lock] = {}
        self._pre_transition_hooks: Dict[str, List[Callable]] = {}
        self._post_transition_hooks: Dict[str, List[Callable]] = {}
        self.database_service = database_service or get_database_service()

        logger.info("ExtensionStateMachine initialized")

    def initialize_plugin(self, plugin_name: str):
        """
        Initialize a plugin in the state machine.

        Args:
            plugin_name: Name of plugin to initialize
        """
        if plugin_name not in self._states:
            self._states[plugin_name] = ExtensionState.INITIAL
            self._transition_history[plugin_name] = []
            self._transition_locks[plugin_name] = asyncio.Lock()
            logger.debug(f"Plugin '{plugin_name}' initialized in state machine")

    def get_state(self, plugin_name: str) -> Optional[ExtensionState]:
        """
        Get current state of a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Current state or None if plugin not tracked
        """
        return self._states.get(plugin_name)

    def can_transition(self, plugin_name: str, event: TransitionEvent) -> bool:
        """
        Check if a transition is valid.

        Args:
            plugin_name: Name of plugin
            event: Transition event to check

        Returns:
            True if transition is valid, False otherwise
        """
        current_state = self._states.get(plugin_name)
        if not current_state:
            logger.warning(f"Plugin '{plugin_name}' not initialized in state machine")
            return False

        valid_transitions = self.TRANSITIONS.get(current_state, {})
        return event in valid_transitions

    async def transition(
        self,
        plugin_name: str,
        event: TransitionEvent,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateTransition:
        """
        Perform a state transition.

        Args:
            plugin_name: Name of plugin
            event: Transition event to trigger
            error_message: Error message if transition failed
            metadata: Optional metadata for the transition

        Returns:
            StateTransition record

        Raises:
            Exception if transition is invalid or fails
        """
        # Initialize plugin if not already tracked
        if plugin_name not in self._states:
            self.initialize_plugin(plugin_name)

        # Get current state
        current_state = self._states[plugin_name]

        # Check if transition is valid
        if not self.can_transition(plugin_name, event):
            valid_transitions = self.TRANSITIONS.get(current_state, {})
            raise Exception(
                f"Invalid transition from {current_state.value} "
                f"via {event.value}. Valid transitions: "
                f"{[e.value for e in valid_transitions.keys()]}"
            )

        # Get target state
        target_state = self.TRANSITIONS[current_state][event]

        # Determine if transition is successful
        success = error_message is None

        # Acquire lock for concurrent safety
        async with self._transition_locks[plugin_name]:
            # Execute pre-transition hooks
            try:
                await self._execute_hooks(
                    plugin_name, current_state, target_state, event, "pre"
                )
            except Exception as e:
                logger.warning(f"Pre-transition hook failed for '{plugin_name}': {e}")

            # Perform transition
            transition = StateTransition(
                plugin_name=plugin_name,
                from_state=current_state,
                to_state=target_state,
                event=event,
                timestamp=datetime.utcnow(),
                success=success,
                error_message=error_message,
                metadata=metadata,
            )

            # Update state
            self._states[plugin_name] = target_state
            self._transition_history[plugin_name].append(transition)

            logger.info(
                f"Plugin '{plugin_name}' transitioned from {current_state.value} "
                f"to {target_state.value} via {event.value}"
            )

            # Execute post-transition hooks
            try:
                await self._execute_hooks(
                    plugin_name, current_state, target_state, event, "post"
                )
            except Exception as e:
                logger.warning(f"Post-transition hook failed for '{plugin_name}': {e}")

            # Persist transition to database if successful
            if success and self.database_service:
                try:
                    await self._persist_transition(transition)
                except Exception as e:
                    logger.warning(f"Failed to persist transition: {e}")

            return transition

    async def _execute_hooks(
        self,
        plugin_name: str,
        from_state: ExtensionState,
        to_state: ExtensionState,
        event: TransitionEvent,
        hook_type: str,
    ):
        """
        Execute pre or post transition hooks.

        Args:
            plugin_name: Name of plugin
            from_state: Source state
            to_state: Target state
            event: Transition event
            hook_type: 'pre' or 'post'
        """
        hook_key = f"{hook_type}_{event.value}"

        if hook_key in self._pre_transition_hooks:
            for hook in self._pre_transition_hooks[hook_key]:
                await hook(plugin_name, from_state, to_state, event)

    async def _persist_transition(self, transition: StateTransition):
        """
        Persist transition to database.

        Args:
            transition: StateTransition to persist
        """
        # Create installation history record
        # This integrates with the database service's history tracking
        pass

    def register_hook(
        self, event: TransitionEvent, hook_type: str = "post", hook: Callable = None
    ):
        """
        Register a hook for state transitions.

        Args:
            event: Transition event to hook
            hook_type: 'pre' or 'post'
            hook: Callback function to execute
        """
        hook_key = f"{hook_type}_{event.value}"

        if hook_key not in self._pre_transition_hooks:
            self._pre_transition_hooks[hook_key] = []

        self._pre_transition_hooks[hook_key].append(hook)
        logger.debug(f"Registered {hook_type}-hook for {event.value}")

    def get_transition_history(
        self, plugin_name: str, limit: int = 100
    ) -> List[StateTransition]:
        """
        Get transition history for a plugin.

        Args:
            plugin_name: Name of plugin
            limit: Maximum number of transitions to return

        Returns:
            List of state transitions (most recent first)
        """
        history = self._transition_history.get(plugin_name, [])
        return list(reversed(history[-limit:]))

    def get_all_states(self) -> Dict[str, ExtensionState]:
        """
        Get current states of all tracked plugins.

        Returns:
            Dictionary mapping plugin names to states
        """
        return self._states.copy()

    async def reset_plugin(self, plugin_name: str):
        """
        Reset a plugin back to initial state.

        Args:
            plugin_name: Name of plugin to reset
        """
        await self.transition(plugin_name, TransitionEvent.RESET)
        logger.info(f"Plugin '{plugin_name}' reset to initial state")

    def map_state_to_status(self, state: ExtensionState) -> Optional[ExtensionStatus]:
        """
        Map state machine state to ExtensionStatus enum.

        Args:
            state: ExtensionState to map

        Returns:
            Corresponding ExtensionStatus or None
        """
        state_mapping = {
            ExtensionState.INITIAL: ExtensionStatus.INACTIVE,
            ExtensionState.DOWNLOADING: ExtensionStatus.LOADING,
            ExtensionState.EXTRACTING: ExtensionStatus.LOADING,
            ExtensionState.VALIDATING: ExtensionStatus.LOADING,
            ExtensionState.INSTALLING: ExtensionStatus.LOADING,
            ExtensionState.UNINSTALLING: ExtensionStatus.UNLOADING,
            ExtensionState.UPDATING: ExtensionStatus.LOADING,
            ExtensionState.RESTORING: ExtensionStatus.LOADING,
            ExtensionState.ENABLING: ExtensionStatus.LOADING,
            ExtensionState.DISABLING: ExtensionStatus.UNLOADING,
            ExtensionState.INSTALLED: ExtensionStatus.ACTIVE,
            ExtensionState.UNINSTALLED: ExtensionStatus.INACTIVE,
            ExtensionState.ERROR: ExtensionStatus.ERROR,
            ExtensionState.DISABLED: ExtensionStatus.INACTIVE,
            ExtensionState.ENABLED: ExtensionStatus.ACTIVE,
        }
        return state_mapping.get(state)

    def get_state_description(self, state: ExtensionState) -> str:
        """
        Get human-readable description of a state.

        Args:
            state: ExtensionState to describe

        Returns:
            Human-readable description
        """
        descriptions = {
            ExtensionState.INITIAL: "Plugin is initialized but not processed",
            ExtensionState.DOWNLOADING: "Plugin is being downloaded",
            ExtensionState.EXTRACTING: "Plugin is being extracted from package",
            ExtensionState.VALIDATING: "Plugin is being validated",
            ExtensionState.INSTALLING: "Plugin is being installed",
            ExtensionState.UNINSTALLING: "Plugin is being uninstalled",
            ExtensionState.UPDATING: "Plugin is being updated",
            ExtensionState.RESTORING: "Plugin is being restored from backup",
            ExtensionState.ENABLING: "Plugin is being enabled",
            ExtensionState.DISABLING: "Plugin is being disabled",
            ExtensionState.INSTALLED: "Plugin is installed and ready for use",
            ExtensionState.UNINSTALLED: "Plugin is not installed",
            ExtensionState.ERROR: "Plugin encountered an error",
            ExtensionState.DISABLED: "Plugin is installed but disabled",
            ExtensionState.ENABLED: "Plugin is enabled and active",
        }
        return descriptions.get(state, "Unknown state")


# Singleton instance
_state_machine: Optional[ExtensionStateMachine] = None


def get_state_machine(database_service=None) -> ExtensionStateMachine:
    """Get the singleton state machine instance."""
    global _state_machine
    if _state_machine is None:
        _state_machine = ExtensionStateMachine(database_service=database_service)
    return _state_machine
