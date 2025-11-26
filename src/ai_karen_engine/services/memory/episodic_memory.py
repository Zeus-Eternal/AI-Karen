"""
Episodic Memory Service - Facade Module

This module provides the public interface for episodic memory functionality,
which handles long-term memory of events and experiences.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Facade for episodic memory functionality.
    
    This service provides a clean interface for managing episodic memory,
    which handles long-term memory of events and experiences.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the episodic memory service.
        
        Args:
            config: Configuration dictionary for episodic memory
        """
        self.config = config or {}
        self._memory_store = None
        self._is_initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the episodic memory store.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Import internal implementation
            from .internal.backends import EpisodicMemoryStore
            
            self._memory_store = EpisodicMemoryStore(self.config)
            self._is_initialized = await self._memory_store.connect()
            
            if self._is_initialized:
                logger.info("Episodic memory service initialized successfully")
            else:
                logger.warning("Failed to initialize episodic memory service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing episodic memory: {e}")
            return False
    
    async def store_episode(
        self, 
        title: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance: int = 5
    ) -> Optional[str]:
        """
        Store an episode in episodic memory.
        
        Args:
            title: Title of the episode
            content: Content of the episode
            timestamp: Timestamp of the episode (defaults to now)
            metadata: Optional metadata dictionary
            tags: Optional list of tags
            importance: Importance score (1-10)
            
        Returns:
            str: ID of the stored episode if successful, None otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot store episode: Episodic memory service not initialized")
            return None
            
        try:
            return await self._memory_store.store_episode(
                title, content, timestamp, metadata, tags, importance
            )
        except Exception as e:
            logger.error(f"Error storing episode in episodic memory: {e}")
            return None
    
    async def retrieve_episode(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific episode by ID.
        
        Args:
            episode_id: ID of the episode to retrieve
            
        Returns:
            Dictionary containing episode data if found, None otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot retrieve episode: Episodic memory service not initialized")
            return None
            
        try:
            return await self._memory_store.retrieve_episode(episode_id)
        except Exception as e:
            logger.error(f"Error retrieving episode from episodic memory: {e}")
            return None
    
    async def search_episodes(
        self, 
        query: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for episodes in episodic memory.
        
        Args:
            query: Search query
            start_time: Start time for search range
            end_time: End time for search range
            tags: Filter by tags if specified
            limit: Maximum number of results to return
            
        Returns:
            List of episode dictionaries
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot search episodes: Episodic memory service not initialized")
            return []
            
        try:
            return await self._memory_store.search_episodes(
                query, start_time, end_time, tags, limit
            )
        except Exception as e:
            logger.error(f"Error searching episodes in episodic memory: {e}")
            return []
    
    async def update_episode(
        self, 
        episode_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance: Optional[int] = None
    ) -> bool:
        """
        Update an episode in episodic memory.
        
        Args:
            episode_id: ID of the episode to update
            title: New title for the episode
            content: New content for the episode
            metadata: New metadata for the episode
            tags: New tags for the episode
            importance: New importance score
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot update episode: Episodic memory service not initialized")
            return False
            
        try:
            return await self._memory_store.update_episode(
                episode_id, title, content, metadata, tags, importance
            )
        except Exception as e:
            logger.error(f"Error updating episode in episodic memory: {e}")
            return False
    
    async def delete_episode(self, episode_id: str) -> bool:
        """
        Delete an episode from episodic memory.
        
        Args:
            episode_id: ID of the episode to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot delete episode: Episodic memory service not initialized")
            return False
            
        try:
            return await self._memory_store.delete_episode(episode_id)
        except Exception as e:
            logger.error(f"Error deleting episode from episodic memory: {e}")
            return False
    
    async def get_timeline(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get a timeline of episodes.
        
        Args:
            start_time: Start time for timeline
            end_time: End time for timeline
            limit: Maximum number of episodes to return
            
        Returns:
            List of episode dictionaries in chronological order
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot get timeline: Episodic memory service not initialized")
            return []
            
        try:
            return await self._memory_store.get_timeline(start_time, end_time, limit)
        except Exception as e:
            logger.error(f"Error getting timeline from episodic memory: {e}")
            return []
    
    async def get_related_episodes(
        self, 
        episode_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get episodes related to a specific episode.
        
        Args:
            episode_id: ID of the episode to find relations for
            limit: Maximum number of related episodes to return
            
        Returns:
            List of related episode dictionaries
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot get related episodes: Episodic memory service not initialized")
            return []
            
        try:
            return await self._memory_store.get_related_episodes(episode_id, limit)
        except Exception as e:
            logger.error(f"Error getting related episodes from episodic memory: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the episodic memory service.
        
        Returns:
            Dictionary with health status information
        """
        if not self._is_initialized:
            return {"status": "not_initialized", "message": "Service not initialized"}
            
        try:
            return await self._memory_store.health_check()
        except Exception as e:
            logger.error(f"Error checking episodic memory health: {e}")
            return {"status": "error", "message": str(e)}