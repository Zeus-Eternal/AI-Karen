"""
Model Registry Service - Facade Module

This module provides the public interface for the model registry,
which manages known models, capabilities, metadata, and tags.
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Facade for the model registry functionality.
    
    This service provides a clean interface for managing known models,
    their capabilities, metadata, and tags.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the model registry service.
        
        Args:
            config: Configuration dictionary for the model registry
        """
        self.config = config or {}
        self._registry = None
        self._is_initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the model registry.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Import internal implementation
            from .internal.metadata_store import ModelMetadataStore
            
            self._registry = ModelMetadataStore(self.config)
            self._is_initialized = await self._registry.connect()
            
            if self._is_initialized:
                logger.info("Model registry service initialized successfully")
            else:
                logger.warning("Failed to initialize model registry service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing model registry: {e}")
            return False
    
    async def register_model(
        self, 
        model_id: str,
        name: str,
        version: str,
        provider: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a new model in the registry.
        
        Args:
            model_id: Unique identifier for the model
            name: Human-readable name of the model
            version: Version of the model
            provider: Provider of the model
            capabilities: List of capabilities of the model
            metadata: Additional metadata about the model
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot register model: Model registry service not initialized")
            return False
            
        try:
            return await self._registry.register_model(
                model_id, name, version, provider, capabilities, metadata
            )
        except Exception as e:
            logger.error(f"Error registering model in registry: {e}")
            return False
    
    async def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model.
        
        Args:
            model_id: ID of the model to retrieve
            
        Returns:
            Dictionary containing model information if found, None otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot get model: Model registry service not initialized")
            return None
            
        try:
            return await self._registry.get_model(model_id)
        except Exception as e:
            logger.error(f"Error getting model from registry: {e}")
            return None
    
    async def list_models(
        self, 
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List models in the registry with optional filtering.
        
        Args:
            provider: Filter by provider if specified
            capability: Filter by capability if specified
            limit: Maximum number of models to return
            
        Returns:
            List of model information dictionaries
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot list models: Model registry service not initialized")
            return []
            
        try:
            return await self._registry.list_models(provider, capability, limit)
        except Exception as e:
            logger.error(f"Error listing models from registry: {e}")
            return []
    
    async def update_model(
        self, 
        model_id: str,
        name: Optional[str] = None,
        version: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update information about a model in the registry.
        
        Args:
            model_id: ID of the model to update
            name: New name for the model
            version: New version for the model
            capabilities: New capabilities list for the model
            metadata: New metadata for the model
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot update model: Model registry service not initialized")
            return False
            
        try:
            return await self._registry.update_model(
                model_id, name, version, capabilities, metadata
            )
        except Exception as e:
            logger.error(f"Error updating model in registry: {e}")
            return False
    
    async def deregister_model(self, model_id: str) -> bool:
        """
        Remove a model from the registry.
        
        Args:
            model_id: ID of the model to remove
            
        Returns:
            bool: True if removal was successful, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot deregister model: Model registry service not initialized")
            return False
            
        try:
            return await self._registry.deregister_model(model_id)
        except Exception as e:
            logger.error(f"Error deregistering model from registry: {e}")
            return False
    
    async def search_models(
        self, 
        query: str,
        fields: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for models in the registry.
        
        Args:
            query: Search query string
            fields: List of fields to search in (if None, searches all fields)
            limit: Maximum number of results to return
            
        Returns:
            List of matching model information dictionaries
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot search models: Model registry service not initialized")
            return []
            
        try:
            return await self._registry.search_models(query, fields, limit)
        except Exception as e:
            logger.error(f"Error searching models in registry: {e}")
            return []
    
    async def get_model_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the models in the registry.
        
        Returns:
            Dictionary with statistics information
        """
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            logger.error("Cannot get model statistics: Model registry service not initialized")
            return {"status": "error", "message": "Service not initialized"}
            
        try:
            return await self._registry.get_statistics()
        except Exception as e:
            logger.error(f"Error getting model statistics from registry: {e}")
            return {"status": "error", "message": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the model registry service.
        
        Returns:
            Dictionary with health status information
        """
        if not self._is_initialized:
            return {"status": "not_initialized", "message": "Service not initialized"}
            
        try:
            return await self._registry.health_check()
        except Exception as e:
            logger.error(f"Error checking model registry health: {e}")
            return {"status": "error", "message": str(e)}