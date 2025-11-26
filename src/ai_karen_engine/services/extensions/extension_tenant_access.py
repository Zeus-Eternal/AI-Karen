"""
extension_tenant_access Service - Facade Module

This module provides a public interface for extension_tenant_access functionality.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExtensionTenantAccess:
    """
    Facade for extension_tenant_access functionality.
    
    This service provides a clean interface for extension_tenant_access operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the extension_tenant_access service.
        
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
            from .internal.backends import ExtensionTenantAccessImpl
            
            self._service_impl = ExtensionTenantAccessImpl(self.config)
            self._is_initialized = await self._service_impl.connect()
            
            if self._is_initialized:
                logger.info("extension_tenant_access service initialized successfully")
            else:
                logger.warning("Failed to initialize extension_tenant_access service")
                
            return self._is_initialized
            
        except Exception as e:
            logger.error(f"Error initializing extension_tenant_access service: {e}")
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
            logger.error(f"Error checking extension_tenant_access service health: {e}")
            return {"status": "error", "message": str(e)}
