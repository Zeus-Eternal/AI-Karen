"""
model_availability_handler Service - Facade Module

This module provides a public interface for model_availability_handler functionality.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelAvailabilityHandler:
    """
    Facade for model_availability_handler functionality.
    
    This service provides a clean interface for model_availability_handler operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the model_availability_handler service.
        
        Args:
            config: Configuration dictionary for the service
        """
        self.config = config or {}
        self._service_impl = None
        self._is_initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the service implementation.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Import internal implementation
            from .internal.backends import ModelAvailabilityHandlerImpl
            
            self._service_impl = ModelAvailabilityHandlerImpl(self.config)
            self._is_initialized = await self._service_impl.connect()
            
            if self._is_initialized:
                logger.info("model_availability_handler service initialized successfully")
            else:
                logger.warning("Failed to initialize model_availability_handler service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing model_availability_handler service: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the service.
        
        Returns:
            Dictionary with health status information
        """
        if not self._is_initialized:
            return {"status": "not_initialized", "message": "Service not initialized"}
            
        try:
            return await self._service_impl.health_check()
        except Exception as e:
            logger.error(f"Error checking model_availability_handler service health: {e}")
            return {"status": "error", "message": str(e)}
