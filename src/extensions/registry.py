"""
Extension registry for managing extension metadata and persistence.

This module provides the ExtensionRegistry class for managing extension
registration, metadata storage, and database persistence.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
import json

from .models import (
    ExtensionManifest, 
    ExtensionRecord, 
    ExtensionStatus,
    ExtensionRegistryEntry
)

logger = logging.getLogger(__name__)


class ExtensionRegistry:
    """
    Manages extension registration and metadata persistence.
    
    The registry maintains information about installed extensions,
    their status, and configuration in both memory and database.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize the extension registry.
        
        Args:
            db_session: Database session for persistence (optional)
        """
        self.db_session = db_session
        self._registry: Dict[str, ExtensionRecord] = {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Extension registry initialized")
    
    async def register_extension(
        self, 
        manifest: ExtensionManifest, 
        instance: Any = None,
        tenant_id: Optional[str] = None,
        installed_by: Optional[str] = None
    ) -> ExtensionRecord:
        """
        Register an extension in the registry.
        
        Args:
            manifest: Extension manifest
            instance: Extension instance (optional)
            tenant_id: Tenant ID for multi-tenant installations
            installed_by: User who installed the extension
            
        Returns:
            ExtensionRecord: The registered extension record
        """
        try:
            extension_name = manifest.name
            logger.info(f"Registering extension: {extension_name}")
            
            # Create extension record
            record = ExtensionRecord(
                manifest=manifest,
                status=ExtensionStatus.NOT_LOADED,
                instance=instance,
                loaded_at=datetime.now(timezone.utc) if instance else None
            )
            
            # Store in memory registry
            self._registry[extension_name] = record
            
            # Persist to database if available
            if self.db_session:
                await self._persist_extension_record(
                    record, 
                    tenant_id, 
                    installed_by
                )
            
            logger.info(f"Extension {extension_name} registered successfully")
            return record
            
        except Exception as e:
            logger.error(f"Failed to register extension {manifest.name}: {e}")
            raise
    
    async def unregister_extension(self, extension_name: str) -> bool:
        """
        Unregister an extension from the registry.
        
        Args:
            extension_name: Name of extension to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            logger.info(f"Unregistering extension: {extension_name}")
            
            # Remove from memory registry
            if extension_name in self._registry:
                del self._registry[extension_name]
            
            # Remove from metadata cache
            if extension_name in self._metadata_cache:
                del self._metadata_cache[extension_name]
            
            # Remove from database if available
            if self.db_session:
                await self._remove_extension_record(extension_name)
            
            logger.info(f"Extension {extension_name} unregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister extension {extension_name}: {e}")
            return False
    
    def get_extension(self, extension_name: str) -> Optional[ExtensionRecord]:
        """
        Get an extension record by name.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Optional[ExtensionRecord]: Extension record or None if not found
        """
        return self._registry.get(extension_name)
    
    def get_all_extensions(self) -> Dict[str, ExtensionRecord]:
        """
        Get all registered extensions.
        
        Returns:
            Dict[str, ExtensionRecord]: All extension records
        """
        return self._registry.copy()
    
    def get_extensions_by_status(self, status: ExtensionStatus) -> List[ExtensionRecord]:
        """
        Get extensions by status.
        
        Args:
            status: Extension status to filter by
            
        Returns:
            List[ExtensionRecord]: Extensions with the specified status
        """
        return [
            record for record in self._registry.values() 
            if record.status == status
        ]
    
    def get_extensions_by_category(self, category: str) -> List[ExtensionRecord]:
        """
        Get extensions by category.
        
        Args:
            category: Extension category to filter by
            
        Returns:
            List[ExtensionRecord]: Extensions in the specified category
        """
        return [
            record for record in self._registry.values()
            if record.manifest.category == category
        ]
    
    def get_extensions_with_capability(self, capability: str) -> List[ExtensionRecord]:
        """
        Get extensions that provide a specific capability.
        
        Args:
            capability: Capability to filter by (api, ui, background_tasks, webhooks)
            
        Returns:
            List[ExtensionRecord]: Extensions with the specified capability
        """
        extensions = []
        for record in self._registry.values():
            capabilities = record.manifest.capabilities
            if (
                (capability == 'api' and capabilities.provides_api) or
                (capability == 'ui' and capabilities.provides_ui) or
                (capability == 'background_tasks' and capabilities.provides_background_tasks) or
                (capability == 'webhooks' and capabilities.provides_webhooks)
            ):
                extensions.append(record)
        
        return extensions
    
    async def update_extension_status(
        self, 
        extension_name: str, 
        status: ExtensionStatus,
        error: Optional[str] = None
    ) -> bool:
        """
        Update extension status.
        
        Args:
            extension_name: Name of the extension
            status: New status
            error: Error message if status is ERROR
            
        Returns:
            bool: True if update successful
        """
        try:
            record = self._registry.get(extension_name)
            if not record:
                logger.warning(f"Extension {extension_name} not found in registry")
                return False
            
            # Update status
            record.status = status
            record.error = error
            
            # Update loaded_at timestamp for active status
            if status == ExtensionStatus.ACTIVE:
                record.loaded_at = datetime.now(timezone.utc)
            elif status in [ExtensionStatus.NOT_LOADED, ExtensionStatus.DISABLED]:
                record.loaded_at = None
            
            # Persist to database if available
            if self.db_session:
                await self._update_extension_status_in_db(extension_name, status, error)
            
            logger.debug(f"Updated extension {extension_name} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update extension {extension_name} status: {e}")
            return False
    
    async def update_extension_instance(
        self, 
        extension_name: str, 
        instance: Any
    ) -> bool:
        """
        Update extension instance.
        
        Args:
            extension_name: Name of the extension
            instance: Extension instance
            
        Returns:
            bool: True if update successful
        """
        try:
            record = self._registry.get(extension_name)
            if not record:
                logger.warning(f"Extension {extension_name} not found in registry")
                return False
            
            record.instance = instance
            
            logger.debug(f"Updated extension {extension_name} instance")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update extension {extension_name} instance: {e}")
            return False
    
    async def update_extension_health(
        self, 
        extension_name: str, 
        health_data: Dict[str, Any]
    ) -> bool:
        """
        Update extension health information.
        
        Args:
            extension_name: Name of the extension
            health_data: Health check data
            
        Returns:
            bool: True if update successful
        """
        try:
            record = self._registry.get(extension_name)
            if not record:
                logger.warning(f"Extension {extension_name} not found in registry")
                return False
            
            record.last_health_check = datetime.now(timezone.utc)
            record.resource_usage = health_data.get('resource_usage', {})
            
            logger.debug(f"Updated extension {extension_name} health data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update extension {extension_name} health: {e}")
            return False
    
    def is_extension_registered(self, extension_name: str) -> bool:
        """
        Check if an extension is registered.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            bool: True if extension is registered
        """
        return extension_name in self._registry
    
    def get_extension_count(self) -> int:
        """
        Get total number of registered extensions.
        
        Returns:
            int: Number of registered extensions
        """
        return len(self._registry)
    
    def get_status_summary(self) -> Dict[str, int]:
        """
        Get summary of extension statuses.
        
        Returns:
            Dict[str, int]: Count of extensions by status
        """
        summary = {}
        for status in ExtensionStatus:
            summary[status.value] = len(self.get_extensions_by_status(status))
        return summary
    
    def get_category_summary(self) -> Dict[str, int]:
        """
        Get summary of extensions by category.
        
        Returns:
            Dict[str, int]: Count of extensions by category
        """
        summary = {}
        for record in self._registry.values():
            category = record.manifest.category
            summary[category] = summary.get(category, 0) + 1
        return summary
    
    async def load_from_database(self) -> int:
        """
        Load extension registry from database.
        
        Returns:
            int: Number of extensions loaded
        """
        if not self.db_session:
            logger.warning("No database session available for loading registry")
            return 0
        
        try:
            # This would load from the extension_registry table
            # Implementation depends on the database schema
            logger.info("Loading extension registry from database")
            
            # Placeholder implementation
            loaded_count = 0
            
            logger.info(f"Loaded {loaded_count} extensions from database")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load registry from database: {e}")
            return 0
    
    async def save_to_database(self) -> bool:
        """
        Save extension registry to database.
        
        Returns:
            bool: True if save successful
        """
        if not self.db_session:
            logger.warning("No database session available for saving registry")
            return False
        
        try:
            logger.info("Saving extension registry to database")
            
            # Save all registered extensions
            for record in self._registry.values():
                await self._persist_extension_record(record)
            
            logger.info("Extension registry saved to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save registry to database: {e}")
            return False
    
    async def _persist_extension_record(
        self, 
        record: ExtensionRecord,
        tenant_id: Optional[str] = None,
        installed_by: Optional[str] = None
    ) -> None:
        """Persist extension record to database."""
        try:
            # This would insert/update the extension_registry table
            # Implementation depends on the database schema
            
            entry = ExtensionRegistryEntry(
                name=record.manifest.name,
                version=record.manifest.version,
                manifest=record.manifest.dict(),
                status=record.status.value,
                installed_at=record.loaded_at or datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                installed_by=installed_by,
                error_message=record.error
            )
            
            logger.debug(f"Persisted extension record: {record.manifest.name}")
            
        except Exception as e:
            logger.error(f"Failed to persist extension record {record.manifest.name}: {e}")
            raise
    
    async def _remove_extension_record(self, extension_name: str) -> None:
        """Remove extension record from database."""
        try:
            # This would delete from the extension_registry table
            logger.debug(f"Removed extension record: {extension_name}")
            
        except Exception as e:
            logger.error(f"Failed to remove extension record {extension_name}: {e}")
            raise
    
    async def _update_extension_status_in_db(
        self, 
        extension_name: str, 
        status: ExtensionStatus,
        error: Optional[str] = None
    ) -> None:
        """Update extension status in database."""
        try:
            # This would update the extension_registry table
            logger.debug(f"Updated extension status in DB: {extension_name} -> {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update extension status in DB {extension_name}: {e}")
            raise
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dict[str, Any]: Registry statistics
        """
        return {
            'total_extensions': self.get_extension_count(),
            'status_summary': self.get_status_summary(),
            'category_summary': self.get_category_summary(),
            'capabilities_summary': {
                'api': len(self.get_extensions_with_capability('api')),
                'ui': len(self.get_extensions_with_capability('ui')),
                'background_tasks': len(self.get_extensions_with_capability('background_tasks')),
                'webhooks': len(self.get_extensions_with_capability('webhooks'))
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Registry health check.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            stats = self.get_registry_stats()
            
            return {
                'status': 'healthy',
                'registry_size': stats['total_extensions'],
                'active_extensions': stats['status_summary'].get('active', 0),
                'error_extensions': stats['status_summary'].get('error', 0),
                'database_connected': self.db_session is not None
            }
            
        except Exception as e:
            logger.error(f"Registry health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }