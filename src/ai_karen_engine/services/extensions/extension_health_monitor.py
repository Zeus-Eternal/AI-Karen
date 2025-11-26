"""
extension_health_monitor Service - Facade Module

This module provides a public interface for extension_health_monitor functionality.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExtensionHealthMonitor:
    """
    Facade for extension_health_monitor functionality.
    
    This service provides a clean interface for extension_health_monitor operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the extension_health_monitor service.
        
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
            from .internal.backends import ExtensionHealthMonitorImpl
            
            self._service_impl = ExtensionHealthMonitorImpl(self.config)
            self._is_initialized = await self._service_impl.connect()
            
            if self._is_initialized:
                logger.info("extension_health_monitor service initialized successfully")
            else:
                logger.warning("Failed to initialize extension_health_monitor service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing extension_health_monitor service: {e}")
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
            logger.error(f"Error checking extension_health_monitor service health: {e}")
            return {"status": "error", "message": str(e)}
