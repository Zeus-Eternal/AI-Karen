"""
Working Memory Service

This service provides working memory functionality for chat and reasoning flows.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from collections import deque
import asyncio
import time


@dataclass
class WorkingMemoryEntry:
    """An entry in working memory."""
    content: Any
    timestamp: float = field(default_factory=time.time)
    importance: float = 1.0
    context: Dict[str, Any] = field(default_factory=dict)


class WorkingMemory:
    """
    Working Memory provides short-term memory for active conversations
    and reasoning processes.
    
    This service maintains a limited capacity working memory with
    importance-based eviction and context management.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Working Memory.
        
        Args:
            config: Configuration for working memory
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_entries = config.get("max_entries", 100)
        self.max_age = config.get("max_age", 3600)  # 1 hour
        self.eviction_threshold = config.get("eviction_threshold", 0.8)
        
        # Working memory storage
        self.entries: deque[WorkingMemoryEntry] = deque(maxlen=self.max_entries)
        self.context: Dict[str, Any] = {}
        
        # Background cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await self._cleanup_expired()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired(self):
        """Clean up expired entries."""
        current_time = time.time()
        cutoff_time = current_time - self.max_age
        
        # Remove expired entries
        while self.entries and self.entries[0].timestamp < cutoff_time:
            self.entries.popleft()
        
        # If we're still over threshold, remove by importance
        if len(self.entries) > self.max_entries * self.eviction_threshold:
            await self._evict_by_importance()
    
    async def _evict_by_importance(self):
        """Evict entries with lowest importance."""
        if not self.entries:
            return
        
        # Sort by importance and timestamp
        sorted_entries = sorted(
            self.entries, 
            key=lambda x: (x.importance, x.timestamp)
        )
        
        # Remove least important entries
        to_remove = int(len(self.entries) * 0.2)  # Remove 20%
        for i in range(to_remove):
            if sorted_entries[i] in self.entries:
                self.entries.remove(sorted_entries[i])
    
    async def add(
        self, 
        content: Any, 
        importance: float = 1.0,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an entry to working memory.
        
        Args:
            content: The content to add
            importance: Importance score (higher = more important)
            context: Optional context information
            
        Returns:
            The ID of the added entry
        """
        entry = WorkingMemoryEntry(
            content=content,
            importance=importance,
            context=context or {}
        )
        
        self.entries.append(entry)
        
        # Check if we need to evict
        if len(self.entries) >= self.max_entries * self.eviction_threshold:
            await self._evict_by_importance()
        
        return str(id(entry))
    
    async def get(self, entry_id: str) -> Optional[WorkingMemoryEntry]:
        """
        Get an entry from working memory.
        
        Args:
            entry_id: The ID of the entry to get
            
        Returns:
            The entry if found, None otherwise
        """
        for entry in self.entries:
            if str(id(entry)) == entry_id:
                return entry
        return None
    
    async def get_recent(self, limit: int = 10) -> List[WorkingMemoryEntry]:
        """
        Get the most recent entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent entries
        """
        return list(self.entries)[-limit:]
    
    async def get_by_importance(self, limit: int = 10) -> List[WorkingMemoryEntry]:
        """
        Get entries sorted by importance.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of entries sorted by importance
        """
        sorted_entries = sorted(
            self.entries, 
            key=lambda x: x.importance, 
            reverse=True
        )
        return sorted_entries[:limit]
    
    async def update_context(self, key: str, value: Any):
        """
        Update the working memory context.
        
        Args:
            key: The context key
            value: The context value
        """
        self.context[key] = value
    
    async def get_context(self, key: str) -> Any:
        """
        Get a value from the working memory context.
        
        Args:
            key: The context key
            
        Returns:
            The context value
        """
        return self.context.get(key)
    
    async def clear(self):
        """Clear all entries from working memory."""
        self.entries.clear()
        self.context.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get working memory statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "total_entries": len(self.entries),
            "max_entries": self.max_entries,
            "utilization": len(self.entries) / self.max_entries,
            "context_size": len(self.context)
        }
    
    async def close(self):
        """Close the working memory service."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
