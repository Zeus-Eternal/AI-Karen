"""
Session State Manager for Copilot integration.

This module handles persistence and retrieval of session state across the
Copilot UI boundary and the canonical LangGraph runtime, with optional
long-term persistence to a memory service.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

StateCallback = Callable[[str, str, Any], Awaitable[None]]


class SessionStateManager:
    """
    Manages session state across the Copilot UI boundary and LangGraph runtime.

    Responsibilities:
    - maintain short-lived in-memory session state cache
    - load/save state to runtime checkpoint layer when available
    - persist important state to memory service when available
    - provide field-level access helpers for UI/session state handling
    """

    def __init__(
        self,
        thread_manager: Optional[Any] = None,
        memory_service: Optional[Any] = None,
    ) -> None:
        """Initialize session state manager with dependencies."""
        self.thread_manager = thread_manager
        self.memory_service = memory_service

        self._session_state: Dict[str, Dict[str, Any]] = {}
        self._state_callbacks: Dict[str, List[StateCallback]] = {}

        logger.info("Session State Manager initialized")

    async def save_session_state(
        self,
        copilot_session_id: str,
        state: Dict[str, Any],
    ) -> bool:
        """
        Save session state to local cache, LangGraph checkpoint, and memory service.

        Args:
            copilot_session_id: Copilot session ID
            state: Session state data

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            session_id = self._validate_session_id(copilot_session_id)
            normalized_state = self._validate_state_payload(state)

            logger.info("Saving session state for %s", session_id)

            state_copy = copy.deepcopy(normalized_state)
            self._session_state[session_id] = {
                "state": state_copy,
                "saved_at": datetime.utcnow(),
                "version": self._get_state_version(state_copy),
                "source": "memory",
            }

            langgraph_thread_id = None
            if self.thread_manager and hasattr(
                self.thread_manager,
                "get_langgraph_thread",
            ):
                langgraph_thread_id = await self.thread_manager.get_langgraph_thread(
                    session_id
                )

            if langgraph_thread_id:
                await self._save_to_langgraph_checkpoint(langgraph_thread_id, state_copy)
                self._session_state[session_id]["source"] = "langgraph"

            await self._save_to_memory_service(session_id, state_copy)
            await self._trigger_state_callbacks(session_id, "save", copy.deepcopy(state_copy))

            logger.info("Session state saved successfully for %s", session_id)
            return True

        except Exception as exc:
            logger.error(
                "Error saving session state for %s: %s",
                copilot_session_id,
                exc,
                exc_info=True,
            )
            return False

    async def load_session_state(
        self,
        copilot_session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load session state from memory cache, LangGraph, or memory service.

        Args:
            copilot_session_id: Copilot session ID

        Returns:
            Session state data or None if not found
        """
        try:
            session_id = self._validate_session_id(copilot_session_id)
            logger.info("Loading session state for %s", session_id)

            if session_id in self._session_state:
                logger.debug("Session state found in memory for %s", session_id)
                cached_state = self._session_state[session_id]["state"]
                return copy.deepcopy(cached_state)

            langgraph_thread_id = None
            if self.thread_manager and hasattr(
                self.thread_manager,
                "get_langgraph_thread",
            ):
                langgraph_thread_id = await self.thread_manager.get_langgraph_thread(
                    session_id
                )

            if langgraph_thread_id:
                state = await self._load_from_langgraph_checkpoint(langgraph_thread_id)
                if state:
                    normalized_state = self._validate_state_payload(state)
                    self._session_state[session_id] = {
                        "state": copy.deepcopy(normalized_state),
                        "loaded_at": datetime.utcnow(),
                        "version": self._get_state_version(normalized_state),
                        "source": "langgraph",
                    }
                    logger.info("Session state loaded from LangGraph for %s", session_id)
                    await self._trigger_state_callbacks(
                        session_id,
                        "load",
                        copy.deepcopy(normalized_state),
                    )
                    return copy.deepcopy(normalized_state)

            state = await self._load_from_memory_service(session_id)
            if state:
                normalized_state = self._validate_state_payload(state)
                self._session_state[session_id] = {
                    "state": copy.deepcopy(normalized_state),
                    "loaded_at": datetime.utcnow(),
                    "version": self._get_state_version(normalized_state),
                    "source": "memory",
                }
                logger.info("Session state loaded from memory service for %s", session_id)
                await self._trigger_state_callbacks(
                    session_id,
                    "load",
                    copy.deepcopy(normalized_state),
                )
                return copy.deepcopy(normalized_state)

            logger.warning("Session state not found for %s", session_id)
            return None

        except Exception as exc:
            logger.error(
                "Error loading session state for %s: %s",
                copilot_session_id,
                exc,
                exc_info=True,
            )
            return None

    async def delete_session_state(self, copilot_session_id: str) -> bool:
        """
        Delete session state from all storage locations.

        Args:
            copilot_session_id: Copilot session ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            session_id = self._validate_session_id(copilot_session_id)
            logger.info("Deleting session state for %s", session_id)

            self._session_state.pop(session_id, None)

            langgraph_thread_id = None
            if self.thread_manager and hasattr(
                self.thread_manager,
                "get_langgraph_thread",
            ):
                langgraph_thread_id = await self.thread_manager.get_langgraph_thread(
                    session_id
                )

            if langgraph_thread_id:
                await self._delete_from_langgraph_checkpoint(langgraph_thread_id)

            await self._delete_from_memory_service(session_id)
            await self._trigger_state_callbacks(session_id, "delete", None)

            logger.info("Session state deleted successfully for %s", session_id)
            return True

        except Exception as exc:
            logger.error(
                "Error deleting session state for %s: %s",
                copilot_session_id,
                exc,
                exc_info=True,
            )
            return False

    async def update_session_state(
        self,
        copilot_session_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update specific fields in session state.

        Args:
            copilot_session_id: Copilot session ID
            updates: Dictionary of field updates

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            session_id = self._validate_session_id(copilot_session_id)
            update_payload = self._validate_state_payload(updates)

            current_state = await self.load_session_state(session_id)
            if current_state is None:
                logger.warning("No current state found for %s", session_id)
                return False

            current_state.update(update_payload)
            saved = await self.save_session_state(session_id, current_state)
            if saved:
                await self._trigger_state_callbacks(
                    session_id,
                    "update",
                    copy.deepcopy(current_state),
                )
            return saved

        except Exception as exc:
            logger.error(
                "Error updating session state for %s: %s",
                copilot_session_id,
                exc,
                exc_info=True,
            )
            return False

    async def get_session_state_field(
        self,
        copilot_session_id: str,
        field_path: str,
    ) -> Any:
        """
        Get a specific field from session state using dot notation.
        """
        try:
            session_id = self._validate_session_id(copilot_session_id)
            normalized_field_path = self._validate_field_path(field_path)

            state = await self.load_session_state(session_id)
            if not state:
                return None

            keys = normalized_field_path.split(".")
            value: Any = state

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None

            return copy.deepcopy(value)

        except Exception as exc:
            logger.error(
                "Error getting session state field %s for %s: %s",
                field_path,
                copilot_session_id,
                exc,
                exc_info=True,
            )
            return None

    async def set_session_state_field(
        self,
        copilot_session_id: str,
        field_path: str,
        value: Any,
    ) -> bool:
        """
        Set a specific field in session state using dot notation.
        """
        try:
            session_id = self._validate_session_id(copilot_session_id)
            normalized_field_path = self._validate_field_path(field_path)

            state = await self.load_session_state(session_id)
            if not state:
                state = {}

            keys = normalized_field_path.split(".")
            current = state

            for key in keys[:-1]:
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]

            current[keys[-1]] = copy.deepcopy(value)
            return await self.save_session_state(session_id, state)

        except Exception as exc:
            logger.error(
                "Error setting session state field %s for %s: %s",
                field_path,
                copilot_session_id,
                exc,
                exc_info=True,
            )
            return False

    def register_state_callback(self, event_type: str, callback: StateCallback) -> None:
        """
        Register a callback for state change events.

        Args:
            event_type: Type of event ("save", "load", "delete", "update")
            callback: Async callback function
        """
        normalized_event = event_type.strip().lower()
        if not normalized_event:
            raise ValueError("event_type cannot be empty")
        if not callable(callback):
            raise ValueError("callback must be callable")

        if normalized_event not in self._state_callbacks:
            self._state_callbacks[normalized_event] = []

        if callback not in self._state_callbacks[normalized_event]:
            self._state_callbacks[normalized_event].append(callback)

        logger.debug("Registered callback for %s events", normalized_event)

    def unregister_state_callback(self, event_type: str, callback: StateCallback) -> None:
        """
        Unregister a state change callback.
        """
        normalized_event = event_type.strip().lower()
        if (
            normalized_event in self._state_callbacks
            and callback in self._state_callbacks[normalized_event]
        ):
            self._state_callbacks[normalized_event].remove(callback)
            logger.debug("Unregistered callback for %s events", normalized_event)

            if not self._state_callbacks[normalized_event]:
                del self._state_callbacks[normalized_event]

    async def _save_to_langgraph_checkpoint(
        self,
        thread_id: str,
        state: Dict[str, Any],
    ) -> None:
        """
        Save state to LangGraph checkpoint.

        Placeholder boundary. If the thread manager exposes a real checkpoint
        save method, use it. Otherwise no-op cleanly.
        """
        logger.debug("Saving state to LangGraph checkpoint %s", thread_id)

        if self.thread_manager is None:
            return

        if hasattr(self.thread_manager, "save_checkpoint_state"):
            await self.thread_manager.save_checkpoint_state(thread_id, copy.deepcopy(state))
            return

        if hasattr(self.thread_manager, "save_langgraph_checkpoint"):
            await self.thread_manager.save_langgraph_checkpoint(thread_id, copy.deepcopy(state))
            return

    async def _load_from_langgraph_checkpoint(
        self,
        thread_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load state from LangGraph checkpoint.

        Placeholder boundary. If the thread manager exposes a real checkpoint
        load method, use it. Otherwise return None cleanly.
        """
        logger.debug("Loading state from LangGraph checkpoint %s", thread_id)

        if self.thread_manager is None:
            return None

        if hasattr(self.thread_manager, "load_checkpoint_state"):
            result = await self.thread_manager.load_checkpoint_state(thread_id)
            return self._validate_state_payload(result) if result else None

        if hasattr(self.thread_manager, "load_langgraph_checkpoint"):
            result = await self.thread_manager.load_langgraph_checkpoint(thread_id)
            return self._validate_state_payload(result) if result else None

        return None

    async def _delete_from_langgraph_checkpoint(self, thread_id: str) -> None:
        """
        Delete state from LangGraph checkpoint.
        """
        logger.debug("Deleting state from LangGraph checkpoint %s", thread_id)

        if self.thread_manager is None:
            return

        if hasattr(self.thread_manager, "delete_checkpoint_state"):
            await self.thread_manager.delete_checkpoint_state(thread_id)
            return

        if hasattr(self.thread_manager, "delete_langgraph_checkpoint"):
            await self.thread_manager.delete_langgraph_checkpoint(thread_id)
            return

    async def _save_to_memory_service(
        self,
        session_id: str,
        state: Dict[str, Any],
    ) -> None:
        """Save state to memory service."""
        if not self.memory_service:
            logger.debug("No memory service available, skipping memory save")
            return

        important_state = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "version": self._get_state_version(state),
            "tasks": copy.deepcopy(state.get("tasks", [])),
            "files_accessed": copy.deepcopy(state.get("files_accessed", [])),
            "key_results": copy.deepcopy(state.get("key_results", [])),
            "user_preferences": copy.deepcopy(state.get("user_preferences", {})),
            "conversation_context": copy.deepcopy(state.get("conversation_context", {})),
            "execution_history": copy.deepcopy(state.get("execution_history", [])),
        }

        try:
            logger.debug("Saving state to memory service for session %s", session_id)

            if hasattr(self.memory_service, "save_session_state"):
                await self.memory_service.save_session_state(session_id, important_state)
                return

            if hasattr(self.memory_service, "store_session_state"):
                await self.memory_service.store_session_state(session_id, important_state)
                return

        except Exception as exc:
            logger.error("Error saving to memory service: %s", exc, exc_info=True)

    async def _load_from_memory_service(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Load state from memory service."""
        if not self.memory_service:
            logger.debug("No memory service available, skipping memory load")
            return None

        try:
            logger.debug("Loading state from memory service for session %s", session_id)

            result = None
            if hasattr(self.memory_service, "load_session_state"):
                result = await self.memory_service.load_session_state(session_id)
            elif hasattr(self.memory_service, "get_session_state"):
                result = await self.memory_service.get_session_state(session_id)

            return self._validate_state_payload(result) if result else None

        except Exception as exc:
            logger.error("Error loading from memory service: %s", exc, exc_info=True)
            return None

    async def _delete_from_memory_service(self, session_id: str) -> None:
        """Delete state from memory service."""
        if not self.memory_service:
            logger.debug("No memory service available, skipping memory delete")
            return

        try:
            logger.debug("Deleting state from memory service for session %s", session_id)

            if hasattr(self.memory_service, "delete_session_state"):
                await self.memory_service.delete_session_state(session_id)
                return

            if hasattr(self.memory_service, "remove_session_state"):
                await self.memory_service.remove_session_state(session_id)
                return

        except Exception as exc:
            logger.error("Error deleting from memory service: %s", exc, exc_info=True)

    def _get_state_version(self, state: Dict[str, Any]) -> str:
        """Generate a deterministic version hash for state."""
        try:
            normalized = json.dumps(state, sort_keys=True, default=str)
        except Exception:
            normalized = json.dumps(sorted(state.keys()), sort_keys=True, default=str)

        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return f"v1_{digest}"

    async def _trigger_state_callbacks(
        self,
        session_id: str,
        event_type: str,
        data: Any,
    ) -> None:
        """Trigger registered callbacks for state events."""
        callbacks = self._state_callbacks.get(event_type, [])
        for callback in list(callbacks):
            try:
                await callback(session_id, event_type, data)
            except Exception as exc:
                logger.error(
                    "Error in state callback for %s: %s",
                    event_type,
                    exc,
                    exc_info=True,
                )

    async def cleanup_old_states(self, max_age_days: int = 30) -> int:
        """
        Clean up old session states.

        Args:
            max_age_days: Maximum age in days before cleanup

        Returns:
            Number of states cleaned up
        """
        if max_age_days < 1:
            raise ValueError("max_age_days must be >= 1")

        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0

        old_sessions: List[str] = []
        for session_id, state_data in self._session_state.items():
            saved_at = state_data.get("saved_at") or state_data.get("loaded_at")
            if isinstance(saved_at, datetime) and saved_at < cutoff_time:
                old_sessions.append(session_id)

        for session_id in old_sessions:
            if await self.delete_session_state(session_id):
                cleaned_count += 1

        logger.info(
            "Cleaned up %s old session states (older than %s days)",
            cleaned_count,
            max_age_days,
        )
        return cleaned_count

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about managed session states.
        """
        total_sessions = len(self._session_state)

        now = datetime.utcnow()
        ages: List[int] = []
        sources: List[str] = []

        for state_data in self._session_state.values():
            reference_time = state_data.get("saved_at") or state_data.get("loaded_at")
            if isinstance(reference_time, datetime):
                age_days = (now - reference_time).days
                ages.append(age_days)

            source = state_data.get("source", "memory")
            sources.append(source)

        avg_age = sum(ages) / len(ages) if ages else 0.0
        max_age = max(ages) if ages else 0
        min_age = min(ages) if ages else 0

        source_counts: Dict[str, int] = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1

        try:
            memory_usage_mb = len(json.dumps(self._session_state, default=str)) / (1024 * 1024)
        except Exception:
            memory_usage_mb = 0.0

        return {
            "total_sessions": total_sessions,
            "average_age_days": avg_age,
            "oldest_session_days": max_age,
            "newest_session_days": min_age,
            "source_distribution": source_counts,
            "memory_usage_mb": memory_usage_mb,
            "callback_event_types": sorted(self._state_callbacks.keys()),
        }

    def _validate_session_id(self, session_id: str) -> str:
        """Validate and normalize session ID."""
        if not isinstance(session_id, str):
            raise ValueError("session_id must be a string")

        normalized = session_id.strip()
        if not normalized:
            raise ValueError("session_id cannot be empty")

        return normalized

    def _validate_state_payload(self, state: Any) -> Dict[str, Any]:
        """Validate state payload shape."""
        if state is None:
            return {}

        if not isinstance(state, dict):
            raise ValueError("state must be a dictionary")

        try:
            json.dumps(state, default=str)
        except Exception as exc:
            raise ValueError("state must be JSON serializable") from exc

        return state

    def _validate_field_path(self, field_path: str) -> str:
        """Validate dot-path access for nested state fields."""
        if not isinstance(field_path, str):
            raise ValueError("field_path must be a string")

        normalized = field_path.strip()
        if not normalized:
            raise ValueError("field_path cannot be empty")

        return normalized