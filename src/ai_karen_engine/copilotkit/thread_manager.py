"""
Thread Manager for CoPilot integration.

This module manages the mapping between CoPilot sessions and LangGraph threads
for state management and persistence.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ThreadManager:
    """
    Manages mapping between CoPilot sessions and LangGraph threads.
    
    Each CoPilot chat session maps directly to a LangGraph thread
    for state management and persistence.
    """
    
    def __init__(self):
        """Initialize thread manager with empty mappings."""
        # Maps CoPilot session IDs to LangGraph thread IDs
        self.copilot_to_langgraph: Dict[str, str] = {}
        
        # Maps LangGraph thread IDs to CoPilot session IDs
        self.langgraph_to_copilot: Dict[str, str] = {}
        
        # Thread metadata
        self.thread_metadata: Dict[str, Dict] = {}
        
        logger.info("Thread Manager initialized")
    
    async def create_thread(self, copilot_session_id: str) -> str:
        """
        Create a new LangGraph thread for a CoPilot session.
        
        Args:
            copilot_session_id: CoPilot session ID
            
        Returns:
            LangGraph thread ID
        """
        # Check if thread already exists
        existing_thread_id = await self.get_langgraph_thread(copilot_session_id)
        if existing_thread_id:
            logger.info(f"Thread already exists for session {copilot_session_id}: {existing_thread_id}")
            return existing_thread_id
        
        # Create new thread ID
        langgraph_thread_id = f"langgraph_{copilot_session_id}_{int(datetime.utcnow().timestamp())}"
        
        # Store bidirectional mapping
        self.copilot_to_langgraph[copilot_session_id] = langgraph_thread_id
        self.langgraph_to_copilot[langgraph_thread_id] = copilot_session_id
        
        # Store thread metadata
        self.thread_metadata[langgraph_thread_id] = {
            "copilot_session_id": copilot_session_id,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "message_count": 0
        }
        
        logger.info(f"Created thread {langgraph_thread_id} for session {copilot_session_id}")
        return langgraph_thread_id
    
    async def get_langgraph_thread(self, copilot_session_id: str) -> Optional[str]:
        """
        Get LangGraph thread ID for CoPilot session.
        
        Args:
            copilot_session_id: CoPilot session ID
            
        Returns:
            LangGraph thread ID or None if not found
        """
        thread_id = self.copilot_to_langgraph.get(copilot_session_id)
        
        if thread_id:
            # Update last accessed time
            if thread_id in self.thread_metadata:
                self.thread_metadata[thread_id]["last_accessed"] = datetime.utcnow()
        
        return thread_id
    
    async def get_copilot_session(self, langgraph_thread_id: str) -> Optional[str]:
        """
        Get CoPilot session ID for LangGraph thread.
        
        Args:
            langgraph_thread_id: LangGraph thread ID
            
        Returns:
            CoPilot session ID or None if not found
        """
        return self.langgraph_to_copilot.get(langgraph_thread_id)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """
        Delete a thread and its mappings.
        
        Args:
            thread_id: LangGraph thread ID to delete
            
        Returns:
            True if thread was deleted, False if not found
        """
        # Get associated session ID
        session_id = self.langgraph_to_copilot.get(thread_id)
        
        if not session_id and thread_id not in self.copilot_to_langgraph.values():
            logger.warning(f"Thread {thread_id} not found for deletion")
            return False
        
        # Remove from mappings
        if session_id:
            del self.copilot_to_langgraph[session_id]
        
        if thread_id in self.langgraph_to_copilot:
            del self.langgraph_to_copilot[thread_id]
        
        # Remove metadata
        if thread_id in self.thread_metadata:
            del self.thread_metadata[thread_id]
        
        logger.info(f"Deleted thread {thread_id} (session: {session_id})")
        return True
    
    async def update_thread_metadata(self, thread_id: str, **metadata) -> bool:
        """
        Update metadata for a thread.
        
        Args:
            thread_id: LangGraph thread ID
            **metadata: Metadata fields to update
            
        Returns:
            True if updated, False if thread not found
        """
        if thread_id not in self.thread_metadata:
            logger.warning(f"Thread {thread_id} not found for metadata update")
            return False
        
        # Update metadata
        self.thread_metadata[thread_id].update(metadata)
        self.thread_metadata[thread_id]["last_accessed"] = datetime.utcnow()
        
        logger.debug(f"Updated metadata for thread {thread_id}")
        return True
    
    async def get_thread_metadata(self, thread_id: str) -> Optional[Dict]:
        """
        Get metadata for a thread.
        
        Args:
            thread_id: LangGraph thread ID
            
        Returns:
            Thread metadata or None if not found
        """
        return self.thread_metadata.get(thread_id)
    
    async def increment_message_count(self, thread_id: str) -> bool:
        """
        Increment message count for a thread.
        
        Args:
            thread_id: LangGraph thread ID
            
        Returns:
            True if incremented, False if thread not found
        """
        if thread_id not in self.thread_metadata:
            logger.warning(f"Thread {thread_id} not found for message count increment")
            return False
        
        # Increment count and update last accessed
        self.thread_metadata[thread_id]["message_count"] += 1
        self.thread_metadata[thread_id]["last_accessed"] = datetime.utcnow()
        
        logger.debug(f"Incremented message count for thread {thread_id}")
        return True
    
    async def get_active_threads(self, session_id: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get active threads.
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            Dictionary of thread_id -> metadata
        """
        active_threads = {}
        
        for thread_id, metadata in self.thread_metadata.items():
            if session_id is None or metadata.get("copilot_session_id") == session_id:
                active_threads[thread_id] = metadata.copy()
        
        return active_threads
    
    async def cleanup_old_threads(self, max_age_days: int = 30) -> int:
        """
        Clean up threads older than specified age.
        
        Args:
            max_age_days: Maximum age in days before cleanup
            
        Returns:
            Number of threads cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0
        
        # Find old threads
        old_threads = []
        for thread_id, metadata in self.thread_metadata.items():
            if metadata["created_at"] < cutoff_time:
                old_threads.append(thread_id)
        
        # Clean up old threads
        for thread_id in old_threads:
            if await self.delete_thread(thread_id):
                cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old threads (older than {max_age_days} days)")
        return cleaned_count
    
    def get_thread_statistics(self) -> Dict:
        """
        Get statistics about managed threads.
        
        Returns:
            Dictionary with thread statistics
        """
        total_threads = len(self.thread_metadata)
        total_messages = sum(meta.get("message_count", 0) for meta in self.thread_metadata.values())
        
        # Calculate thread age statistics
        now = datetime.utcnow()
        ages = []
        for metadata in self.thread_metadata.values():
            age_days = (now - metadata["created_at"]).days
            ages.append(age_days)
        
        avg_age = sum(ages) / len(ages) if ages else 0
        max_age = max(ages) if ages else 0
        min_age = min(ages) if ages else 0
        
        return {
            "total_threads": total_threads,
            "total_messages": total_messages,
            "average_age_days": avg_age,
            "oldest_thread_days": max_age,
            "newest_thread_days": min_age,
            "threads_per_session": len(set(meta.get("copilot_session_id") for meta in self.thread_metadata.values()))
        }
    
    async def migrate_thread(self, old_session_id: str, new_session_id: str) -> Optional[str]:
        """
        Migrate a thread from one session to another.
        
        Args:
            old_session_id: Original session ID
            new_session_id: New session ID
            
        Returns:
            New thread ID if migrated, None if not found
        """
        # Get existing thread
        old_thread_id = await self.get_langgraph_thread(old_session_id)
        if not old_thread_id:
            logger.warning(f"No thread found for session {old_session_id} to migrate")
            return None
        
        # Create new thread for new session
        new_thread_id = await self.create_thread(new_session_id)
        
        # Copy metadata from old thread
        if old_thread_id in self.thread_metadata:
            old_metadata = self.thread_metadata[old_thread_id]
            await self.update_thread_metadata(new_thread_id, **{
                "migrated_from": old_session_id,
                "original_created_at": old_metadata.get("created_at"),
                "message_count": old_metadata.get("message_count", 0)
            })
        
        logger.info(f"Migrated thread from session {old_session_id} to {new_session_id}")
        return new_thread_id