"""
auth_utils Service - Facade Module

This module provides a public interface for auth_utils functionality.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuthUtils:
    """
    Facade for auth_utils functionality.
    
    This service provides a clean interface for auth_utils operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the auth_utils service.
        
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
            from .internal.backends import AuthUtilsImpl
            
            self._service_impl = AuthUtilsImpl(self.config)
            self._is_initialized = await self._service_impl.connect()
            
            if self._is_initialized:
                logger.info("auth_utils service initialized successfully")
            else:
                logger.warning("Failed to initialize auth_utils service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing auth_utils service: {e}")
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
            logger.error(f"Error checking auth_utils service health: {e}")
            return {"status": "error", "message": str(e)}
