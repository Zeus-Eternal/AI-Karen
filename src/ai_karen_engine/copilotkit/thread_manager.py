"""
Thread Manager for Copilot integration.

This module manages the mapping between Copilot UI sessions and LangGraph
threads for runtime state management and persistence.
"""

from __future__ import annotations

import copy
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ThreadManager:
    """
    Manages mapping between Copilot sessions and LangGraph threads.

    Each Copilot chat session maps to a LangGraph thread used for runtime
    state continuity and persistence.

    This class is a bridge/registry, not the runtime itself.
    """

    def __init__(self) -> None:
        """Initialize thread manager with empty mappings."""
        self.copilot_to_langgraph: Dict[str, str] = {}
        self.langgraph_to_copilot: Dict[str, str] = {}
        self.thread_metadata: Dict[str, Dict[str, Any]] = {}
        self.thread_checkpoints: Dict[str, Dict[str, Any]] = {}

        logger.info("Thread Manager initialized")

    async def create_thread(self, copilot_session_id: str) -> str:
        """
        Create a new LangGraph thread for a Copilot session.

        Args:
            copilot_session_id: Copilot session ID

        Returns:
            LangGraph thread ID
        """
        session_id = self._validate_session_id(copilot_session_id)

        existing_thread_id = await self.get_langgraph_thread(session_id)
        if existing_thread_id:
            logger.info(
                "Thread already exists for session %s: %s",
                session_id,
                existing_thread_id,
            )
            return existing_thread_id

        langgraph_thread_id = self._generate_thread_id(session_id)

        self.copilot_to_langgraph[session_id] = langgraph_thread_id
        self.langgraph_to_copilot[langgraph_thread_id] = session_id

        now = datetime.utcnow()
        self.thread_metadata[langgraph_thread_id] = {
            "copilot_session_id": session_id,
            "created_at": now,
            "last_accessed": now,
            "message_count": 0,
            "status": "active",
        }

        logger.info(
            "Created thread %s for session %s",
            langgraph_thread_id,
            session_id,
        )
        return langgraph_thread_id

    async def get_langgraph_thread(self, copilot_session_id: str) -> Optional[str]:
        """
        Get LangGraph thread ID for Copilot session.

        Args:
            copilot_session_id: Copilot session ID

        Returns:
            LangGraph thread ID or None if not found
        """
        session_id = self._validate_session_id(copilot_session_id)
        thread_id = self.copilot_to_langgraph.get(session_id)

        if thread_id and thread_id in self.thread_metadata:
            self.thread_metadata[thread_id]["last_accessed"] = datetime.utcnow()

        return thread_id

    async def get_copilot_session(self, langgraph_thread_id: str) -> Optional[str]:
        """
        Get Copilot session ID for LangGraph thread.

        Args:
            langgraph_thread_id: LangGraph thread ID

        Returns:
            Copilot session ID or None if not found
        """
        thread_id = self._validate_thread_id(langgraph_thread_id)
        return self.langgraph_to_copilot.get(thread_id)

    async def delete_thread(self, thread_id: str) -> bool:
        """
        Delete a thread and its mappings.

        Args:
            thread_id: LangGraph thread ID to delete

        Returns:
            True if thread was deleted, False otherwise
        """
        normalized_thread_id = self._validate_thread_id(thread_id)
        session_id = self.langgraph_to_copilot.get(normalized_thread_id)

        if not session_id and normalized_thread_id not in self.thread_metadata:
            logger.warning("Thread %s not found for deletion", normalized_thread_id)
            return False

        if session_id:
            self.copilot_to_langgraph.pop(session_id, None)

        self.langgraph_to_copilot.pop(normalized_thread_id, None)
        self.thread_metadata.pop(normalized_thread_id, None)
        self.thread_checkpoints.pop(normalized_thread_id, None)

        logger.info(
            "Deleted thread %s (session: %s)",
            normalized_thread_id,
            session_id,
        )
        return True

    async def update_thread_metadata(self, thread_id: str, **metadata: Any) -> bool:
        """
        Update metadata for a thread.

        Args:
            thread_id: LangGraph thread ID
            **metadata: Metadata fields to update

        Returns:
            True if updated, False if thread not found
        """
        normalized_thread_id = self._validate_thread_id(thread_id)

        if normalized_thread_id not in self.thread_metadata:
            logger.warning(
                "Thread %s not found for metadata update",
                normalized_thread_id,
            )
            return False

        self.thread_metadata[normalized_thread_id].update(copy.deepcopy(metadata))
        self.thread_metadata[normalized_thread_id]["last_accessed"] = datetime.utcnow()

        logger.debug("Updated metadata for thread %s", normalized_thread_id)
        return True

    async def get_thread_metadata(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a thread.

        Args:
            thread_id: LangGraph thread ID

        Returns:
            Thread metadata or None if not found
        """
        normalized_thread_id = self._validate_thread_id(thread_id)
        metadata = self.thread_metadata.get(normalized_thread_id)
        return copy.deepcopy(metadata) if metadata else None

    async def increment_message_count(self, thread_id: str) -> bool:
        """
        Increment message count for a thread.

        Args:
            thread_id: LangGraph thread ID

        Returns:
            True if incremented, False if thread not found
        """
        normalized_thread_id = self._validate_thread_id(thread_id)

        if normalized_thread_id not in self.thread_metadata:
            logger.warning(
                "Thread %s not found for message count increment",
                normalized_thread_id,
            )
            return False

        self.thread_metadata[normalized_thread_id]["message_count"] = (
            int(self.thread_metadata[normalized_thread_id].get("message_count", 0)) + 1
        )
        self.thread_metadata[normalized_thread_id]["last_accessed"] = datetime.utcnow()

        logger.debug("Incremented message count for thread %s", normalized_thread_id)
        return True

    async def get_active_threads(
        self,
        session_id: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get active threads.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            Dictionary of thread_id -> metadata
        """
        normalized_session_id = (
            self._validate_session_id(session_id) if session_id is not None else None
        )

        active_threads: Dict[str, Dict[str, Any]] = {}
        for thread_id, metadata in self.thread_metadata.items():
            if normalized_session_id is None or metadata.get("copilot_session_id") == normalized_session_id:
                active_threads[thread_id] = copy.deepcopy(metadata)

        return active_threads

    async def cleanup_old_threads(self, max_age_days: int = 30) -> int:
        """
        Clean up threads older than specified age.

        Args:
            max_age_days: Maximum age in days before cleanup

        Returns:
            Number of threads cleaned up
        """
        if max_age_days < 1:
            raise ValueError("max_age_days must be >= 1")

        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0

        old_threads = []
        for thread_id, metadata in self.thread_metadata.items():
            created_at = metadata.get("created_at")
            if isinstance(created_at, datetime) and created_at < cutoff_time:
                old_threads.append(thread_id)

        for thread_id in old_threads:
            if await self.delete_thread(thread_id):
                cleaned_count += 1

        logger.info(
            "Cleaned up %s old threads (older than %s days)",
            cleaned_count,
            max_age_days,
        )
        return cleaned_count

    def get_thread_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about managed threads.

        Returns:
            Dictionary with thread statistics
        """
        total_threads = len(self.thread_metadata)
        total_messages = sum(
            int(meta.get("message_count", 0))
            for meta in self.thread_metadata.values()
        )

        now = datetime.utcnow()
        ages = []
        for metadata in self.thread_metadata.values():
            created_at = metadata.get("created_at")
            if isinstance(created_at, datetime):
                age_days = (now - created_at).days
                ages.append(age_days)

        avg_age = sum(ages) / len(ages) if ages else 0.0
        max_age = max(ages) if ages else 0
        min_age = min(ages) if ages else 0

        unique_sessions = {
            meta.get("copilot_session_id")
            for meta in self.thread_metadata.values()
            if meta.get("copilot_session_id")
        }

        return {
            "total_threads": total_threads,
            "total_messages": total_messages,
            "average_age_days": avg_age,
            "oldest_thread_days": max_age,
            "newest_thread_days": min_age,
            "threads_per_session": len(unique_sessions),
            "checkpoint_count": len(self.thread_checkpoints),
        }

    async def migrate_thread(
        self,
        old_session_id: str,
        new_session_id: str,
        rebind_existing_thread: bool = True,
    ) -> Optional[str]:
        """
        Migrate or rebind a thread from one session to another.

        Args:
            old_session_id: Original session ID
            new_session_id: New session ID
            rebind_existing_thread: If True, rebind the existing thread to the new
                session. If False, create a new thread and copy metadata.

        Returns:
            Thread ID if migrated, None if original session is not found
        """
        normalized_old_session_id = self._validate_session_id(old_session_id)
        normalized_new_session_id = self._validate_session_id(new_session_id)

        old_thread_id = await self.get_langgraph_thread(normalized_old_session_id)
        if not old_thread_id:
            logger.warning(
                "No thread found for session %s to migrate",
                normalized_old_session_id,
            )
            return None

        if rebind_existing_thread:
            self.copilot_to_langgraph.pop(normalized_old_session_id, None)
            self.copilot_to_langgraph[normalized_new_session_id] = old_thread_id
            self.langgraph_to_copilot[old_thread_id] = normalized_new_session_id

            if old_thread_id in self.thread_metadata:
                self.thread_metadata[old_thread_id]["copilot_session_id"] = normalized_new_session_id
                self.thread_metadata[old_thread_id]["migrated_from"] = normalized_old_session_id
                self.thread_metadata[old_thread_id]["last_accessed"] = datetime.utcnow()

            logger.info(
                "Rebound thread %s from session %s to %s",
                old_thread_id,
                normalized_old_session_id,
                normalized_new_session_id,
            )
            return old_thread_id

        new_thread_id = await self.create_thread(normalized_new_session_id)

        if old_thread_id in self.thread_metadata:
            old_metadata = copy.deepcopy(self.thread_metadata[old_thread_id])
            await self.update_thread_metadata(
                new_thread_id,
                migrated_from=normalized_old_session_id,
                original_created_at=old_metadata.get("created_at"),
                message_count=old_metadata.get("message_count", 0),
            )

        if old_thread_id in self.thread_checkpoints:
            self.thread_checkpoints[new_thread_id] = copy.deepcopy(
                self.thread_checkpoints[old_thread_id]
            )

        logger.info(
            "Migrated thread from session %s to %s using new thread %s",
            normalized_old_session_id,
            normalized_new_session_id,
            new_thread_id,
        )
        return new_thread_id

    async def save_checkpoint_state(
        self,
        thread_id: str,
        state: Dict[str, Any],
    ) -> None:
        """
        Save checkpoint state for a thread.

        This provides a concrete boundary for SessionStateManager integration.
        """
        normalized_thread_id = self._validate_thread_id(thread_id)
        if normalized_thread_id not in self.thread_metadata:
            raise ValueError(f"Thread {normalized_thread_id} not found")

        self.thread_checkpoints[normalized_thread_id] = copy.deepcopy(state)
        self.thread_metadata[normalized_thread_id]["last_accessed"] = datetime.utcnow()

        logger.debug("Saved checkpoint state for thread %s", normalized_thread_id)

    async def load_checkpoint_state(
        self,
        thread_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint state for a thread.
        """
        normalized_thread_id = self._validate_thread_id(thread_id)
        checkpoint = self.thread_checkpoints.get(normalized_thread_id)
        if normalized_thread_id in self.thread_metadata:
            self.thread_metadata[normalized_thread_id]["last_accessed"] = datetime.utcnow()
        return copy.deepcopy(checkpoint) if checkpoint is not None else None

    async def delete_checkpoint_state(self, thread_id: str) -> None:
        """
        Delete checkpoint state for a thread.
        """
        normalized_thread_id = self._validate_thread_id(thread_id)
        self.thread_checkpoints.pop(normalized_thread_id, None)

        if normalized_thread_id in self.thread_metadata:
            self.thread_metadata[normalized_thread_id]["last_accessed"] = datetime.utcnow()

        logger.debug("Deleted checkpoint state for thread %s", normalized_thread_id)

    def _generate_thread_id(self, session_id: str) -> str:
        """Generate a unique LangGraph thread ID."""
        return f"langgraph_{session_id}_{uuid.uuid4().hex}"

    def _validate_session_id(self, session_id: str) -> str:
        """Validate and normalize session ID."""
        if not isinstance(session_id, str):
            raise ValueError("session_id must be a string")

        normalized = session_id.strip()
        if not normalized:
            raise ValueError("session_id cannot be empty")

        return normalized

    def _validate_thread_id(self, thread_id: str) -> str:
        """Validate and normalize thread ID."""
        if not isinstance(thread_id, str):
            raise ValueError("thread_id must be a string")

        normalized = thread_id.strip()
        if not normalized:
            raise ValueError("thread_id cannot be empty")

        return normalized