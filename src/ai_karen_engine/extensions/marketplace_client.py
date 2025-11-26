"""
Marketplace client for the legacy extension system.

This module provides backward compatibility with the old marketplace client
while migrating to the new two-tier architecture.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


class MarketplaceClient:
    """
    Client for the extension marketplace in the legacy system.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("extension.marketplace_client")
    
    async def download_extension(
        self, 
        extension_id: str, 
        version: str, 
        target_dir: Path
    ) -> bool:
        """
        Download an extension from the marketplace.
        
        Args:
            extension_id: Extension ID
            version: Extension version
            target_dir: Target directory for the extension
            
        Returns:
            True if download was successful, False otherwise
        """
        # For now, just log the request and return True
        # This can be enhanced later to actually download extensions
        self.logger.info(
            "Marketplace download request for extension %s version %s to %s",
            extension_id, version, target_dir
        )
        return True
    
    async def search_extensions(
        self, 
        query: str, 
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for extensions in the marketplace.
        
        Args:
            query: Search query
            category: Optional category filter
            
        Returns:
            List of extension information
        """
        # For now, return an empty list
        # This can be enhanced later to actually search extensions
        self.logger.info(
            "Marketplace search request for query %s in category %s",
            query, category
        )
        return []
    
    async def get_extension_info(
        self, 
        extension_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about an extension from the marketplace.
        
        Args:
            extension_id: Extension ID
            
        Returns:
            Extension information or None if not found
        """
        # For now, return None
        # This can be enhanced later to actually get extension info
        self.logger.info(
            "Marketplace info request for extension %s",
            extension_id
        )
        return None
    
    async def get_extension_versions(
        self, 
        extension_id: str
    ) -> List[str]:
        """
        Get available versions for an extension from the marketplace.
        
        Args:
            extension_id: Extension ID
            
        Returns:
            List of available versions
        """
        # For now, return an empty list
        # This can be enhanced later to actually get extension versions
        self.logger.info(
            "Marketplace versions request for extension %s",
            extension_id
        )
        return []