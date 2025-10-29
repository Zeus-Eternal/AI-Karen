"""
Extension Migration Manager

Handles extension updates and migrations with rollback capabilities.
"""

import asyncio
import json
import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from sqlalchemy.orm import Session

from .models import (
    ExtensionMigration,
    LifecycleEvent,
    LifecycleEventType
)
from .backup_manager import ExtensionBackupManager
from ..manager import ExtensionManager
from ..marketplace.version_manager import ExtensionVersionManager


class MigrationStep:
    """Represents a single migration step."""
    
    def __init__(
        self,
        name: str,
        description: str,
        execute_func: Callable,
        rollback_func: Optional[Callable] = None,
        required: bool = True
    ):
        self.name = name
        self.description = description
        self.execute_func = execute_func
        self.rollback_func = rollback_func
        self.required = required
        self.executed = False
        self.execution_time: Optional[datetime] = None
        self.error: Optional[str] = None


class ExtensionMigrationManager:
    """Manages extension migrations and updates."""
    
    def __init__(
        self,
        extension_manager: ExtensionManager,
        backup_manager: ExtensionBackupManager,
        version_manager: ExtensionVersionManager,
        db_session: Session
    ):
        self.extension_manager = extension_manager
        self.backup_manager = backup_manager
        self.version_manager = version_manager
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        self._migration_locks: Dict[str, asyncio.Lock] = {}
        self._active_migrations: Dict[str, ExtensionMigration] = {}
    
    async def migrate_extension(
        self,
        extension_name: str,
        target_version: str,
        create_backup: bool = True,
        auto_rollback_on_failure: bool = True,
        migration_timeout: int = 3600  # 1 hour
    ) -> ExtensionMigration:
        """Migrate an extension to a target version."""
        # Get or create lock for this extension
        if extension_name not in self._migration_locks:
            self._migration_locks[extension_name] = asyncio.Lock()
        
        async with self._migration_locks[extension_name]:
            return await self._migrate_extension_internal(
                extension_name,
                target_version,
                create_backup,
                auto_rollback_on_failure,
                migration_timeout
            )
    
    async def _migrate_extension_internal(
        self,
        extension_name: str,
        target_version: str,
        create_backup: bool,
        auto_rollback_on_failure: bool,
        migration_timeout: int
    ) -> ExtensionMigration:
        """Internal migration logic."""
        self.logger.info(
            f"Starting migration of {extension_name} to version {target_version}"
        )
        
        # Get current extension info
        current_info = await self.extension_manager.get_extension_info(extension_name)
        if not current_info:
            raise ValueError(f"Extension not found: {extension_name}")
        
        current_version = current_info.get("version", "unknown")
        
        # Create migration record
        migration_id = f"{extension_name}_{current_version}_to_{target_version}_{int(datetime.utcnow().timestamp())}"
        migration = ExtensionMigration(
            migration_id=migration_id,
            extension_name=extension_name,
            from_version=current_version,
            to_version=target_version,
            started_at=datetime.utcnow(),
            status="pending"
        )
        
        self._active_migrations[extension_name] = migration
        
        try:
            # Log migration start
            await self._log_lifecycle_event(
                extension_name,
                LifecycleEventType.MIGRATION_STARTED,
                {"migration": migration.dict()}
            )
            
            # Create backup if requested
            backup_id = None
            if create_backup:
                backup = await self.backup_manager.create_backup(
                    extension_name,
                    backup_type="pre_migration",
                    description=f"Pre-migration backup for {current_version} -> {target_version}"
                )
                backup_id = backup.backup_id
                migration.backup_id = backup_id
            
            # Plan migration steps
            migration_steps = await self._plan_migration(
                extension_name, current_version, target_version
            )
            migration.migration_steps = [step.__dict__ for step in migration_steps]
            
            # Create rollback plan
            rollback_plan = await self._create_rollback_plan(
                extension_name, current_version, target_version, backup_id
            )
            migration.rollback_plan = rollback_plan
            
            # Execute migration with timeout
            migration.status = "running"
            
            try:
                await asyncio.wait_for(
                    self._execute_migration_steps(migration, migration_steps),
                    timeout=migration_timeout
                )
                
                # Migration completed successfully
                migration.status = "completed"
                migration.completed_at = datetime.utcnow()
                
                await self._log_lifecycle_event(
                    extension_name,
                    LifecycleEventType.MIGRATION_COMPLETED,
                    {"migration": migration.dict()}
                )
                
                self.logger.info(
                    f"Migration completed successfully: {extension_name} "
                    f"{current_version} -> {target_version}"
                )
                
            except asyncio.TimeoutError:
                migration.status = "failed"
                migration.error_message = "Migration timed out"
                
                if auto_rollback_on_failure:
                    await self._execute_rollback(migration)
                
                raise TimeoutError(f"Migration timed out after {migration_timeout} seconds")
            
            except Exception as e:
                migration.status = "failed"
                migration.error_message = str(e)
                
                if auto_rollback_on_failure:
                    await self._execute_rollback(migration)
                
                raise e
            
            return migration
            
        except Exception as e:
            await self._log_lifecycle_event(
                extension_name,
                LifecycleEventType.MIGRATION_FAILED,
                {
                    "migration": migration.dict(),
                    "error": str(e)
                }
            )
            raise e
        
        finally:
            # Clean up
            if extension_name in self._active_migrations:
                del self._active_migrations[extension_name]
    
    async def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a migration."""
        # Find migration (this would typically query database)
        migration = None
        for active_migration in self._active_migrations.values():
            if active_migration.migration_id == migration_id:
                migration = active_migration
                break
        
        if not migration:
            raise ValueError(f"Migration not found: {migration_id}")
        
        return await self._execute_rollback(migration)
    
    async def _execute_rollback(self, migration: ExtensionMigration) -> bool:
        """Execute rollback for a migration."""
        self.logger.info(f"Rolling back migration: {migration.migration_id}")
        
        try:
            extension_name = migration.extension_name
            
            # Stop extension if running
            was_running = await self.extension_manager.is_extension_running(extension_name)
            if was_running:
                await self.extension_manager.stop_extension(extension_name)
            
            # Execute rollback plan
            for step in reversed(migration.rollback_plan):
                step_name = step.get("name", "unknown")
                step_type = step.get("type", "unknown")
                
                self.logger.info(f"Executing rollback step: {step_name}")
                
                if step_type == "restore_backup":
                    if migration.backup_id:
                        await self.backup_manager.restore_backup(
                            migration.backup_id,
                            target_extension_name=extension_name
                        )
                
                elif step_type == "restore_version":
                    target_version = step.get("version", migration.from_version)
                    await self._restore_extension_version(extension_name, target_version)
                
                elif step_type == "restore_config":
                    config = step.get("config", {})
                    await self._restore_extension_config(extension_name, config)
                
                elif step_type == "restore_data":
                    await self._restore_extension_data(extension_name, step.get("data", {}))
                
                elif step_type == "custom":
                    # Execute custom rollback function
                    func_name = step.get("function")
                    if func_name:
                        await self._execute_custom_rollback_step(extension_name, func_name, step)
            
            # Restart extension if it was running
            if was_running:
                await self.extension_manager.start_extension(extension_name)
            
            # Update migration status
            migration.status = "rolled_back"
            
            self.logger.info(f"Migration rollback completed: {migration.migration_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for migration {migration.migration_id}: {e}")
            return False
    
    async def _plan_migration(
        self,
        extension_name: str,
        from_version: str,
        to_version: str
    ) -> List[MigrationStep]:
        """Plan migration steps."""
        steps = []
        
        # Get migration path
        migration_path = await self.version_manager.get_migration_path(
            extension_name, from_version, to_version
        )
        
        for version_step in migration_path:
            current_ver = version_step["from"]
            target_ver = version_step["to"]
            
            # Add version-specific migration steps
            version_steps = await self._get_version_migration_steps(
                extension_name, current_ver, target_ver
            )
            steps.extend(version_steps)
        
        return steps
    
    async def _get_version_migration_steps(
        self,
        extension_name: str,
        from_version: str,
        to_version: str
    ) -> List[MigrationStep]:
        """Get migration steps for a specific version transition."""
        steps = []
        
        # Download new version
        steps.append(MigrationStep(
            name="download_version",
            description=f"Download extension version {to_version}",
            execute_func=lambda: self._download_extension_version(extension_name, to_version)
        ))
        
        # Stop extension
        steps.append(MigrationStep(
            name="stop_extension",
            description="Stop extension",
            execute_func=lambda: self.extension_manager.stop_extension(extension_name),
            rollback_func=lambda: self.extension_manager.start_extension(extension_name)
        ))
        
        # Update extension files
        steps.append(MigrationStep(
            name="update_files",
            description="Update extension files",
            execute_func=lambda: self._update_extension_files(extension_name, to_version),
            rollback_func=lambda: self._restore_extension_files(extension_name, from_version)
        ))
        
        # Run data migrations
        steps.append(MigrationStep(
            name="migrate_data",
            description="Migrate extension data",
            execute_func=lambda: self._migrate_extension_data(extension_name, from_version, to_version),
            rollback_func=lambda: self._rollback_data_migration(extension_name, from_version, to_version)
        ))
        
        # Update configuration
        steps.append(MigrationStep(
            name="update_config",
            description="Update extension configuration",
            execute_func=lambda: self._update_extension_config(extension_name, to_version),
            rollback_func=lambda: self._restore_extension_config(extension_name, {})
        ))
        
        # Start extension
        steps.append(MigrationStep(
            name="start_extension",
            description="Start extension",
            execute_func=lambda: self.extension_manager.start_extension(extension_name),
            rollback_func=lambda: self.extension_manager.stop_extension(extension_name)
        ))
        
        # Verify migration
        steps.append(MigrationStep(
            name="verify_migration",
            description="Verify migration success",
            execute_func=lambda: self._verify_migration(extension_name, to_version),
            required=False
        ))
        
        return steps
    
    async def _create_rollback_plan(
        self,
        extension_name: str,
        from_version: str,
        to_version: str,
        backup_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Create rollback plan."""
        plan = []
        
        if backup_id:
            # Primary rollback: restore from backup
            plan.append({
                "name": "restore_from_backup",
                "type": "restore_backup",
                "backup_id": backup_id,
                "description": "Restore extension from pre-migration backup"
            })
        else:
            # Alternative rollback: restore previous version
            plan.append({
                "name": "restore_previous_version",
                "type": "restore_version",
                "version": from_version,
                "description": f"Restore extension to version {from_version}"
            })
        
        return plan
    
    async def _execute_migration_steps(
        self,
        migration: ExtensionMigration,
        steps: List[MigrationStep]
    ) -> None:
        """Execute migration steps."""
        for i, step in enumerate(steps):
            self.logger.info(f"Executing migration step {i+1}/{len(steps)}: {step.name}")
            
            try:
                step.execution_time = datetime.utcnow()
                await step.execute_func()
                step.executed = True
                
                # Update migration record
                migration.migration_steps[i]["executed"] = True
                migration.migration_steps[i]["execution_time"] = step.execution_time.isoformat()
                
            except Exception as e:
                step.error = str(e)
                migration.migration_steps[i]["error"] = str(e)
                
                if step.required:
                    # Required step failed, rollback executed steps
                    await self._rollback_executed_steps(steps[:i])
                    raise e
                else:
                    # Optional step failed, continue
                    self.logger.warning(f"Optional migration step failed: {step.name}: {e}")
    
    async def _rollback_executed_steps(self, steps: List[MigrationStep]) -> None:
        """Rollback executed migration steps."""
        for step in reversed(steps):
            if step.executed and step.rollback_func:
                try:
                    self.logger.info(f"Rolling back step: {step.name}")
                    await step.rollback_func()
                except Exception as e:
                    self.logger.error(f"Rollback failed for step {step.name}: {e}")
    
    async def _download_extension_version(
        self, 
        extension_name: str, 
        version: str
    ) -> None:
        """Download a specific version of an extension."""
        # This would typically download from marketplace
        self.logger.info(f"Downloading {extension_name} version {version}")
        # Placeholder implementation
        pass
    
    async def _update_extension_files(
        self, 
        extension_name: str, 
        version: str
    ) -> None:
        """Update extension files to new version."""
        # This would typically replace extension files
        self.logger.info(f"Updating files for {extension_name} to version {version}")
        # Placeholder implementation
        pass
    
    async def _restore_extension_files(
        self, 
        extension_name: str, 
        version: str
    ) -> None:
        """Restore extension files to previous version."""
        self.logger.info(f"Restoring files for {extension_name} to version {version}")
        # Placeholder implementation
        pass
    
    async def _migrate_extension_data(
        self,
        extension_name: str,
        from_version: str,
        to_version: str
    ) -> None:
        """Migrate extension data between versions."""
        self.logger.info(
            f"Migrating data for {extension_name} from {from_version} to {to_version}"
        )
        # This would typically run database migrations
        # Placeholder implementation
        pass
    
    async def _rollback_data_migration(
        self,
        extension_name: str,
        from_version: str,
        to_version: str
    ) -> None:
        """Rollback data migration."""
        self.logger.info(
            f"Rolling back data migration for {extension_name} from {to_version} to {from_version}"
        )
        # Placeholder implementation
        pass
    
    async def _update_extension_config(
        self, 
        extension_name: str, 
        version: str
    ) -> None:
        """Update extension configuration for new version."""
        self.logger.info(f"Updating configuration for {extension_name} version {version}")
        # Placeholder implementation
        pass
    
    async def _restore_extension_config(
        self, 
        extension_name: str, 
        config: Dict[str, Any]
    ) -> None:
        """Restore extension configuration."""
        self.logger.info(f"Restoring configuration for {extension_name}")
        # Placeholder implementation
        pass
    
    async def _restore_extension_data(
        self, 
        extension_name: str, 
        data: Dict[str, Any]
    ) -> None:
        """Restore extension data."""
        self.logger.info(f"Restoring data for {extension_name}")
        # Placeholder implementation
        pass
    
    async def _restore_extension_version(
        self, 
        extension_name: str, 
        version: str
    ) -> None:
        """Restore extension to a specific version."""
        self.logger.info(f"Restoring {extension_name} to version {version}")
        # This would typically download and install the specific version
        # Placeholder implementation
        pass
    
    async def _verify_migration(
        self, 
        extension_name: str, 
        version: str
    ) -> None:
        """Verify migration was successful."""
        # Check if extension is running
        if not await self.extension_manager.is_extension_running(extension_name):
            raise Exception("Extension is not running after migration")
        
        # Check version
        info = await self.extension_manager.get_extension_info(extension_name)
        if info.get("version") != version:
            raise Exception(f"Version mismatch after migration: expected {version}, got {info.get('version')}")
        
        # Perform health check
        # This would typically use the health monitor
        self.logger.info(f"Migration verification passed for {extension_name}")
    
    async def _execute_custom_rollback_step(
        self,
        extension_name: str,
        function_name: str,
        step_config: Dict[str, Any]
    ) -> None:
        """Execute custom rollback step."""
        self.logger.info(f"Executing custom rollback step: {function_name}")
        # This would typically load and execute a custom function
        # Placeholder implementation
        pass
    
    async def get_migration_status(self, extension_name: str) -> Optional[ExtensionMigration]:
        """Get current migration status for an extension."""
        return self._active_migrations.get(extension_name)
    
    async def list_migrations(
        self,
        extension_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[ExtensionMigration]:
        """List migrations."""
        # This would typically query database
        # For now, return active migrations
        migrations = list(self._active_migrations.values())
        
        if extension_name:
            migrations = [m for m in migrations if m.extension_name == extension_name]
        
        if status:
            migrations = [m for m in migrations if m.status == status]
        
        return migrations[:limit]
    
    async def _log_lifecycle_event(
        self, 
        extension_name: str, 
        event_type: LifecycleEventType,
        details: Dict[str, Any]
    ) -> None:
        """Log a lifecycle event."""
        event = LifecycleEvent(
            event_id=f"{extension_name}_{event_type}_{int(datetime.utcnow().timestamp())}",
            extension_name=extension_name,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            details=details
        )
        
        # This would typically save to database
        self.logger.info(f"Lifecycle event: {event.dict()}")