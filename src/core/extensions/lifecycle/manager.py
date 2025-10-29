"""
Extension Lifecycle Manager

Main orchestrator for extension lifecycle management.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from .models import (
    ExtensionHealth,
    ExtensionBackup,
    ExtensionMigration,
    LifecycleEvent,
    RecoveryAction
)
from .health_monitor import ExtensionHealthMonitor
from .backup_manager import ExtensionBackupManager
from .migration_manager import ExtensionMigrationManager
from .recovery_manager import ExtensionRecoveryManager
from ..manager import ExtensionManager
from ..marketplace.version_manager import ExtensionVersionManager


class ExtensionLifecycleManager:
    """Main extension lifecycle management orchestrator."""
    
    def __init__(
        self,
        extension_manager: ExtensionManager,
        version_manager: ExtensionVersionManager,
        db_session: Session,
        backup_root: Path,
        enable_auto_recovery: bool = True,
        health_check_interval: int = 60
    ):
        self.extension_manager = extension_manager
        self.version_manager = version_manager
        self.db_session = db_session
        self.backup_root = backup_root
        self.enable_auto_recovery = enable_auto_recovery
        self.logger = logging.getLogger(__name__)
        
        # Initialize component managers
        self.backup_manager = ExtensionBackupManager(
            extension_manager, db_session, backup_root
        )
        
        self.migration_manager = ExtensionMigrationManager(
            extension_manager, self.backup_manager, version_manager, db_session
        )
        
        self.recovery_manager = ExtensionRecoveryManager(
            extension_manager, self.backup_manager, self.migration_manager, db_session
        )
        
        self.health_monitor = ExtensionHealthMonitor(
            extension_manager, db_session, health_check_interval
        )
        
        # Setup health monitoring callbacks
        if enable_auto_recovery:
            self.health_monitor.add_health_callback(self._on_health_change)
        
        self._is_running = False
    
    async def start(self) -> None:
        """Start lifecycle management services."""
        if self._is_running:
            return
        
        self.logger.info("Starting extension lifecycle management")
        
        # Start health monitoring
        await self.health_monitor.start_monitoring()
        
        self._is_running = True
        self.logger.info("Extension lifecycle management started")
    
    async def stop(self) -> None:
        """Stop lifecycle management services."""
        if not self._is_running:
            return
        
        self.logger.info("Stopping extension lifecycle management")
        
        # Stop health monitoring
        await self.health_monitor.stop_monitoring()
        
        self._is_running = False
        self.logger.info("Extension lifecycle management stopped")
    
    # Health Management
    async def get_extension_health(self, extension_name: str) -> Optional[ExtensionHealth]:
        """Get health status of an extension."""
        return await self.health_monitor.get_extension_health(extension_name)
    
    async def get_all_health_status(self) -> Dict[str, ExtensionHealth]:
        """Get health status of all extensions."""
        return await self.health_monitor.get_all_health_status()
    
    async def configure_health_monitoring(
        self, extension_name: str, config: Dict[str, Any]
    ) -> None:
        """Configure health monitoring for an extension."""
        # This would update health check configuration
        self.logger.info(f"Configured health monitoring for {extension_name}")
    
    # Backup Management
    async def create_backup(
        self,
        extension_name: str,
        backup_type: str = "full",
        description: Optional[str] = None
    ) -> ExtensionBackup:
        """Create a backup of an extension."""
        return await self.backup_manager.create_backup(
            extension_name, backup_type, description
        )
    
    async def restore_backup(
        self,
        backup_id: str,
        target_extension_name: Optional[str] = None
    ) -> bool:
        """Restore an extension from backup."""
        return await self.backup_manager.restore_backup(
            backup_id, target_extension_name
        )
    
    async def list_backups(
        self, extension_name: Optional[str] = None
    ) -> List[ExtensionBackup]:
        """List available backups."""
        return await self.backup_manager.list_backups(extension_name)
    
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        return await self.backup_manager.delete_backup(backup_id)  
  
    # Migration Management
    async def migrate_extension(
        self,
        extension_name: str,
        target_version: str,
        create_backup: bool = True
    ) -> ExtensionMigration:
        """Migrate an extension to a target version."""
        return await self.migration_manager.migrate_extension(
            extension_name, target_version, create_backup
        )
    
    async def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a migration."""
        return await self.migration_manager.rollback_migration(migration_id)
    
    async def get_migration_status(
        self, extension_name: str
    ) -> Optional[ExtensionMigration]:
        """Get migration status for an extension."""
        return await self.migration_manager.get_migration_status(extension_name)
    
    async def list_migrations(
        self, extension_name: Optional[str] = None
    ) -> List[ExtensionMigration]:
        """List migrations."""
        return await self.migration_manager.list_migrations(extension_name)
    
    # Recovery Management
    async def recover_extension(
        self,
        extension_name: str,
        strategy: str = "auto"
    ) -> bool:
        """Recover a failed extension."""
        return await self.recovery_manager.recover_extension(extension_name, strategy)
    
    async def get_recovery_history(
        self, extension_name: str
    ) -> List[Dict[str, Any]]:
        """Get recovery history for an extension."""
        return await self.recovery_manager.get_recovery_history(extension_name)
    
    # Lifecycle Events
    async def get_lifecycle_events(
        self,
        extension_name: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[LifecycleEvent]:
        """Get lifecycle events."""
        # This would typically query database
        # For now, return empty list
        return []
    
    # Auto-recovery callback
    async def _on_health_change(self, health: ExtensionHealth) -> None:
        """Handle health status changes."""
        if not self.enable_auto_recovery:
            return
        
        # Trigger recovery for unhealthy extensions
        if health.status in ["unhealthy", "critical"]:
            self.logger.warning(
                f"Extension {health.extension_name} is {health.status}, "
                f"triggering auto-recovery"
            )
            
            # Run recovery in background
            asyncio.create_task(
                self.recovery_manager.recover_extension(
                    health.extension_name, "auto"
                )
            )
    
    # Utility methods
    async def get_extension_overview(self, extension_name: str) -> Dict[str, Any]:
        """Get comprehensive overview of an extension's lifecycle status."""
        overview = {
            "extension_name": extension_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Health status
        health = await self.get_extension_health(extension_name)
        overview["health"] = health.dict() if health else None
        
        # Recent backups
        backups = await self.list_backups(extension_name)
        overview["recent_backups"] = [b.dict() for b in backups[:5]]
        
        # Migration status
        migration = await self.get_migration_status(extension_name)
        overview["current_migration"] = migration.dict() if migration else None
        
        # Recovery history
        recovery_history = await self.get_recovery_history(extension_name)
        overview["recent_recovery"] = recovery_history[:5]
        
        return overview
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide lifecycle overview."""
        overview = {
            "timestamp": datetime.utcnow().isoformat(),
            "extensions": {}
        }
        
        # Get all extension health
        all_health = await self.get_all_health_status()
        
        for extension_name, health in all_health.items():
            ext_overview = await self.get_extension_overview(extension_name)
            overview["extensions"][extension_name] = ext_overview
        
        # System-wide statistics
        total_extensions = len(all_health)
        healthy_count = sum(
            1 for h in all_health.values() 
            if h.status == "healthy"
        )
        
        overview["statistics"] = {
            "total_extensions": total_extensions,
            "healthy_extensions": healthy_count,
            "unhealthy_extensions": total_extensions - healthy_count,
            "health_percentage": (healthy_count / total_extensions * 100) if total_extensions > 0 else 0
        }
        
        return overview