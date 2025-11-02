"""Lightweight memory helper for plugins.

Provides a simple interface over the unified memory manager
in ``ai_karen_engine.core.memory.manager`` so plugins can
store and recall information without dealing with backend
specifics.
"""

from typing import Any, Dict, Optional

from ai_karen_engine.core.memory import manager as unified_memory


class MemoryManager:
    """Helper exposing read/write operations to unified memory."""

    def __init__(self, tenant_id: Optional[str] = None) -> None:
        self.tenant_id = tenant_id

    def write(self, user_ctx: Dict[str, Any], query: str, result: Any) -> bool:
        """Write a memory entry using the unified manager."""
        user_ctx = user_ctx or {}
        return unified_memory.update_memory(user_ctx, query, result, tenant_id=self.tenant_id)

    def read(
        self, user_ctx: Dict[str, Any], query: str, limit: int = 10
    ):
        """Read memories related to a query via the unified manager."""
        user_ctx = user_ctx or {}
        return unified_memory.recall_context(
            user_ctx, query, limit=limit, tenant_id=self.tenant_id
        )