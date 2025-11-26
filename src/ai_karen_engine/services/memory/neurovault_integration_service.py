"""
NeuroVault Integration Service - Facade Module

This module provides the public interface for integrating with NeuroVault/EchoCore
memory platforms, providing embeddings and retrieval pipelines.
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class NeuroVaultIntegrationService:
    """
    Facade for NeuroVault integration functionality.
    
    This service provides a clean interface for integrating with advanced memory
    platforms like NeuroVault/EchoCore, handling embeddings and retrieval.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NeuroVault integration service.
        
        Args:
            config: Configuration dictionary for NeuroVault integration
        """
        self.config = config or {}
        self._client = None
        self._is_initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the NeuroVault client connection.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Import internal implementation
            from .internal.backends import NeuroVaultClient
            
            self._client = NeuroVaultClient(self.config)
            self._is_initialized = await self._client.connect()
            
            if self._is_initialized:
                logger.info("NeuroVault integration service initialized successfully")
            else:
                logger.warning("Failed to initialize NeuroVault integration service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing NeuroVault integration: {e}")
            return False
    
    async def store_embedding(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store content embedding in NeuroVault.
        
        Args:
            content: Text content to embed and store
            metadata: Optional metadata dictionary
            tenant_id: Tenant identifier for isolation
            
        Returns:
            str: ID of the stored embedding if successful, None otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot store embedding: NeuroVault service not initialized")
            return None
            
        try:
            return await self._client.store_embedding(content, metadata, tenant_id)
        except Exception as e:
            logger.error(f"Error storing embedding in NeuroVault: {e}")
            return None
    
    async def search_embeddings(
        self, 
        query: str, 
        top_k: int = 10,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in NeuroVault.
        
        Args:
            query: Query text to search for
            top_k: Number of results to return
            tenant_id: Tenant identifier for isolation
            filters: Optional filters to apply to search
            
        Returns:
            List of search result dictionaries
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot search embeddings: NeuroVault service not initialized")
            return []
            
        try:
            return await self._client.search_embeddings(query, top_k, tenant_id, filters)
        except Exception as e:
            logger.error(f"Error searching embeddings in NeuroVault: {e}")
            return []
    
    async def get_embedding(self, content_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific embedding by ID.
        
        Args:
            content_id: ID of the embedding to retrieve
            tenant_id: Tenant identifier for isolation
            
        Returns:
            Dictionary containing embedding data if found, None otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot get embedding: NeuroVault service not initialized")
            return None
            
        try:
            return await self._client.get_embedding(content_id, tenant_id)
        except Exception as e:
            logger.error(f"Error retrieving embedding from NeuroVault: {e}")
            return None
    
    async def delete_embedding(self, content_id: str, tenant_id: Optional[str] = None) -> bool:
        """
        Delete a specific embedding by ID.
        
        Args:
            content_id: ID of the embedding to delete
            tenant_id: Tenant identifier for isolation
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot delete embedding: NeuroVault service not initialized")
            return False
            
        try:
            return await self._client.delete_embedding(content_id, tenant_id)
        except Exception as e:
            logger.error(f"Error deleting embedding from NeuroVault: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the NeuroVault service.
        
        Returns:
            Dictionary with health status information
        """
        if not self._is_initialized:
            return {"status": "not_initialized", "message": "Service not initialized"}
            
        try:
            return await self._client.health_check()
        except Exception as e:
            logger.error(f"Error checking NeuroVault health: {e}")
            return {"status": "error", "message": str(e)}