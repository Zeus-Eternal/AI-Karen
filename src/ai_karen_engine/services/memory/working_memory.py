"""
Working Memory Service - Facade Module

This module provides the public interface for working memory functionality,
which handles short-term memory and conversation context.
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class WorkingMemory:
    """
    Facade for working memory functionality.
    
    This service provides a clean interface for managing working memory,
    which handles short-term memory and conversation context.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the working memory service.
        
        Args:
            config: Configuration dictionary for working memory
        """
        self.config = config or {}
        self._memory_store = None
        self._is_initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the working memory store.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Import internal implementation
            from .internal.backends import WorkingMemoryStore
            
            self._memory_store = WorkingMemoryStore(self.config)
            self._is_initialized = await self._memory_store.connect()
            
            if self._is_initialized:
                logger.info("Working memory service initialized successfully")
            else:
                logger.warning("Failed to initialize working memory service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing working memory: {e}")
            return False
    
    async def add_item(
        self, 
        content: str, 
        item_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Add an item to working memory.
        
        Args:
            content: Content of the memory item
            item_type: Type of the memory item (text, image, etc.)
            metadata: Optional metadata dictionary
            session_id: Session identifier for context
            
        Returns:
            str: ID of the added item if successful, None otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot add item: Working memory service not initialized")
            return None
            
        try:
            return await self._memory_store.add_item(content, item_type, metadata, session_id)
        except Exception as e:
            logger.error(f"Error adding item to working memory: {e}")
            return None
    
    async def get_items(
        self, 
        session_id: Optional[str] = None,
        limit: int = 10,
        item_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get items from working memory.
        
        Args:
            session_id: Session identifier for context
            limit: Maximum number of items to return
            item_type: Filter by item type if specified
            
        Returns:
            List of memory item dictionaries
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot get items: Working memory service not initialized")
            return []
            
        try:
            return await self._memory_store.get_items(session_id, limit, item_type)
        except Exception as e:
            logger.error(f"Error getting items from working memory: {e}")
            return []
    
    async def update_item(
        self, 
        item_id: str, 
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an item in working memory.
        
        Args:
            item_id: ID of the item to update
            content: New content for the item
            metadata: New metadata for the item
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot update item: Working memory service not initialized")
            return False
            
        try:
            return await self._memory_store.update_item(item_id, content, metadata)
        except Exception as e:
            logger.error(f"Error updating item in working memory: {e}")
            return False
    
    async def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from working memory.
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            bool: True if removal was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot remove item: Working memory service not initialized")
            return False
            
        try:
            return await self._memory_store.remove_item(item_id)
        except Exception as e:
            logger.error(f"Error removing item from working memory: {e}")
            return False
    
    async def clear_session(self, session_id: str) -> bool:
        """
        Clear all items for a session.
        
        Args:
            session_id: Session identifier to clear
            
        Returns:
            bool: True if clearing was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot clear session: Working memory service not initialized")
            return False
            
        try:
            return await self._memory_store.clear_session(session_id)
        except Exception as e:
            logger.error(f"Error clearing session in working memory: {e}")
            return False
    
    async def get_context_summary(
        self, 
        session_id: Optional[str] = None,
        max_items: int = 5
    ) -> Dict[str, Any]:
        """
        Get a summary of the current working memory context.
        
        Args:
            session_id: Session identifier for context
            max_items: Maximum number of items to include in summary
            
        Returns:
            Dictionary with context summary information
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot get context summary: Working memory service not initialized")
            return {"status": "error", "message": "Service not initialized"}
            
        try:
            return await self._memory_store.get_context_summary(session_id, max_items)
        except Exception as e:
            logger.error(f"Error getting context summary from working memory: {e}")
            return {"status": "error", "message": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the working memory service.
        
        Returns:
            Dictionary with health status information
        """
        if not self._is_initialized:
            return {"status": "not_initialized", "message": "Service not initialized"}
            
        try:
            return await self._memory_store.health_check()
        except Exception as e:
            logger.error(f"Error checking working memory health: {e}")
            return {"status": "error", "message": str(e)}