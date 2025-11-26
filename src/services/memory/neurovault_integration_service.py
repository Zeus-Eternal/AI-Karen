"""
NeuroVault Integration Service

Integrates NeuroVault tri-partite memory with:
- PostgreSQL for memory metadata persistence
- Milvus for vector storage and retrieval
- Redis for caching recent memories
- Existing chat orchestrator
- Existing memory services

This service provides a unified interface for all memory operations.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ai_karen_engine.core.neuro_vault import (
    NeuroVault,
    MemoryType,
    MemoryEntry,
    RetrievalRequest,
    RetrievalResult,
    create_memory_entry,
    get_neurovault,
)

logger = logging.getLogger(__name__)


class NeuroVaultIntegrationService:
    """
    Production integration service for NeuroVault memory system.

    Features:
    - Automatic memory storage from chat interactions
    - Periodic consolidation (reflection) jobs
    - Memory decay processing
    - Integration with existing memory services
    - Backward compatibility with legacy memory APIs
    """

    def __init__(
        self,
        neurovault: Optional[NeuroVault] = None,
        enable_auto_storage: bool = True,
        enable_consolidation: bool = True,
    ):
        """Initialize integration service."""
        self.neurovault = neurovault or get_neurovault()
        self.enable_auto_storage = enable_auto_storage
        self.enable_consolidation = enable_consolidation

        # Background task handles
        self._consolidation_task = None
        self._decay_task = None

        logger.info("NeuroVault Integration Service initialized")

    async def start_background_tasks(self):
        """Start background maintenance tasks."""
        if self.enable_consolidation:
            self._consolidation_task = asyncio.create_task(
                self._consolidation_loop()
            )
            logger.info("Started consolidation task")

        self._decay_task = asyncio.create_task(self._decay_loop())
        logger.info("Started decay task")

    async def stop_background_tasks(self):
        """Stop background tasks."""
        if self._consolidation_task:
            self._consolidation_task.cancel()
        if self._decay_task:
            self._decay_task.cancel()

        logger.info("Stopped background tasks")

    async def _consolidation_loop(self):
        """Background task for memory consolidation."""
        while True:
            try:
                # Run consolidation every 6 hours
                await asyncio.sleep(6 * 3600)

                logger.info("Running memory consolidation...")
                count = await self.neurovault.consolidate_memories()
                logger.info(f"Consolidated {count} memories")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consolidation error: {e}", exc_info=True)

    async def _decay_loop(self):
        """Background task for memory decay processing."""
        while True:
            try:
                # Run decay every 12 hours
                await asyncio.sleep(12 * 3600)

                logger.info("Applying memory decay...")
                archived = await self.neurovault.apply_decay()
                logger.info(f"Archived {archived} decayed memories")

                # Purge expired
                purged = await self.neurovault.purge_expired()
                logger.info(f"Purged {purged} expired memories")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Decay error: {e}", exc_info=True)

    async def store_conversation_memory(
        self,
        user_message: str,
        ai_response: str,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        importance_score: float = 5.0,
        emotional_valence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MemoryEntry]:
        """
        Store conversation as episodic memory.

        This is called automatically from chat orchestrator.
        """
        content = f"User: {user_message}\nAI: {ai_response}"

        return await self.neurovault.store_memory(
            content=content,
            memory_type=MemoryType.EPISODIC,
            tenant_id=tenant_id,
            user_id=user_id,
            importance_score=importance_score,
            conversation_id=conversation_id,
            emotional_valence=emotional_valence,
            event_type="conversation",
            metadata=metadata or {},
        )

    async def store_tool_usage(
        self,
        tool_name: str,
        success: bool,
        tenant_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MemoryEntry]:
        """Store tool usage pattern as procedural memory."""
        content = f"Tool: {tool_name}, Success: {success}"

        # Update success rate if memory exists
        existing = self.neurovault.index.search(
            memory_types=[MemoryType.PROCEDURAL],
            tenant_id=tenant_id,
            user_id=user_id,
        )

        tool_memory = next(
            (m for m in existing if m.tool_name == tool_name), None
        )

        if tool_memory:
            # Update existing
            tool_memory.usage_count += 1
            if success:
                tool_memory.success_rate = (
                    (tool_memory.success_rate or 0) * (tool_memory.usage_count - 1)
                    + 1.0
                ) / tool_memory.usage_count
            else:
                tool_memory.success_rate = (
                    (tool_memory.success_rate or 0) * (tool_memory.usage_count - 1)
                ) / tool_memory.usage_count

            return tool_memory
        else:
            # Create new
            return await self.neurovault.store_memory(
                content=content,
                memory_type=MemoryType.PROCEDURAL,
                tenant_id=tenant_id,
                user_id=user_id,
                importance_score=7.0,  # Tool patterns are important
                tool_name=tool_name,
                success_rate=1.0 if success else 0.0,
                usage_count=1,
                metadata=metadata or {},
            )

    async def retrieve_relevant_memories(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        top_k: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
    ) -> RetrievalResult:
        """Retrieve relevant memories for current context."""
        request = RetrievalRequest(
            query=query,
            tenant_id=tenant_id,
            user_id=user_id,
            memory_types=memory_types,
            top_k=top_k,
            min_relevance=0.3,
        )

        return await self.neurovault.retrieve_memories(request)

    async def get_conversation_context(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        max_turns: int = 10,
    ) -> List[MemoryEntry]:
        """Get recent conversation memories for context."""
        # Search for episodic memories in this conversation
        candidates = self.neurovault.index.search(
            memory_types=[MemoryType.EPISODIC],
            tenant_id=tenant_id,
            user_id=user_id,
            temporal_window_hours=24,  # Last 24 hours
        )

        # Filter by conversation_id
        conversation_memories = [
            m for m in candidates
            if m.metadata and m.metadata.conversation_id == conversation_id
        ]

        # Sort by timestamp descending
        conversation_memories.sort(key=lambda m: m.timestamp, reverse=True)

        return conversation_memories[:max_turns]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return self.neurovault.get_stats()


# ===================================
# FACTORY FUNCTION
# ===================================

_integration_service = None

def get_neurovault_integration() -> NeuroVaultIntegrationService:
    """Get singleton integration service."""
    global _integration_service
    if _integration_service is None:
        _integration_service = NeuroVaultIntegrationService()
    return _integration_service


async def initialize_neurovault_service():
    """Initialize and start NeuroVault service."""
    service = get_neurovault_integration()
    await service.start_background_tasks()
    logger.info("NeuroVault service fully initialized")
    return service
