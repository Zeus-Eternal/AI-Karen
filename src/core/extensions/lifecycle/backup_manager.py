"""
Extension Backup Manager

Handles backup and restore operations for extensions.
"""

import asyncio
import hashlib
import json
import logging
import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from .models import (
    ExtensionBackup,
    ExtensionSnapshot,
    LifecycleEvent,
    LifecycleEventType
)
from ..manager import ExtensionManager


class ExtensionBackupManager:
    """Manages extension backups and restore operations."""
    
    def __init__(
        self,
        extension_manager: ExtensionManager,
        db_session: Session,
        backup_root: Path
    ):
        self.extension_manager = extension_manager
        self.db_session = db_session
        self.backup_root = Path(backup_root)
        self.logger = logging.getLogger(__name__)
        
        # Ensure backup directory exists
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        self._backup_locks: Dict[str, asyncio.Lock] = {}
    
    async def create_backup(
        self,
        extension_name: str,
        backup_type: str = "full",
        description: Optional[str] = None,
        include_data: bool = True,
        include_config: bool = True,
        include_code: bool = True
    ) -> ExtensionBackup:
        """Create a backup of an extension."""
        # Get or create lock for this extension
        if extension_name not in self._backup_locks:
            self._backup_locks[extension_name] = asyncio.Lock()
        
        async with self._backup_locks[extension_name]:
            return await self._create_backup_internal(
                extension_name,
                backup_type,
                description,
                include_data,
                include_config,
                include_code
            )
    
    async def _create_backup_internal(
        self,
        extension_name: str,
        backup_type: str,
        description: Optional[str],
        include_data: bool,
        include_config: bool,
        include_code: bool
    ) -> ExtensionBackup:
        """Internal backup creation logic."""
        self.logger.info(f"Creating {backup_type} backup for extension: {extension_name}")
        
        # Generate backup ID
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{extension_name}_{backup_type}_{timestamp}"
        
        # Get extension info
        extension_info = await self.extension_manager.get_extension_info(extension_name)
        if not extension_info:
            raise ValueError(f"Extension not found: {extension_name}")
        
        version = extension_info.get("version", "unknown")
        
        # Create backup directory
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "extension_name": extension_name,
                "version": version,
                "backup_type": backup_type,
                "created_at": datetime.utcnow().isoformat(),
                "description": description,
                "includes": {
                    "data": include_data,
                    "config": include_config,
                    "code": include_code
                }
            }
            
            backup_size = 0
            
            # Backup extension code
            if include_code:
                code_size = await self._backup_extension_code(
                    extension_name, backup_dir / "code"
                )
                backup_size += code_size
                manifest["code_backup"] = True
            
            # Backup extension configuration
            if include_config:
                config_size = await self._backup_extension_config(
                    extension_name, backup_dir / "config"
                )
                backup_size += config_size
                manifest["config_backup"] = True
            
            # Backup extension data
            if include_data:
                data_size = await self._backup_extension_data(
                    extension_name, backup_dir / "data"
                )
                backup_size += data_size
                manifest["data_backup"] = True
            
            # Save manifest
            manifest_path = backup_dir / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create compressed archive
            archive_path = self.backup_root / f"{backup_id}.tar.gz"
            await self._create_archive(backup_dir, archive_path)
            
            # Calculate checksum
            checksum = await self._calculate_checksum(archive_path)
            
            # Clean up temporary directory
            shutil.rmtree(backup_dir)
            
            # Create backup record
            backup = ExtensionBackup(
                backup_id=backup_id,
                extension_name=extension_name,
                version=version,
                created_at=datetime.utcnow(),
                backup_type=backup_type,
                size_bytes=archive_path.stat().st_size,
                file_path=str(archive_path),
                metadata=manifest,
                checksum=checksum,
                description=description
            )
            
            # Log lifecycle event
            await self._log_lifecycle_event(
                extension_name,
                LifecycleEventType.BACKUP_CREATED,
                {"backup": backup.dict()}
            )
            
            self.logger.info(
                f"Backup created successfully: {backup_id} "
                f"({backup.size_bytes} bytes)"
            )
            
            return backup
            
        except Exception as e:
            # Clean up on error
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            archive_path = self.backup_root / f"{backup_id}.tar.gz"
            if archive_path.exists():
                archive_path.unlink()
            
            self.logger.error(f"Backup creation failed for {extension_name}: {e}")
            raise
    
    async def restore_backup(
        self,
        backup_id: str,
        target_extension_name: Optional[str] = None,
        restore_data: bool = True,
        restore_config: bool = True,
        restore_code: bool = False,
        create_snapshot: bool = True
    ) -> bool:
        """Restore an extension from backup."""
        self.logger.info(f"Restoring backup: {backup_id}")
        
        # Find backup
        backup = await self.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Backup not found: {backup_id}")
        
        extension_name = target_extension_name or backup.extension_name
        
        # Create snapshot before restore if requested
        snapshot = None
        if create_snapshot:
            try:
                snapshot = await self.create_snapshot(extension_name)
            except Exception as e:
                self.logger.warning(f"Failed to create pre-restore snapshot: {e}")
        
        # Get or create lock for this extension
        if extension_name not in self._backup_locks:
            self._backup_locks[extension_name] = asyncio.Lock()
        
        async with self._backup_locks[extension_name]:
            try:
                success = await self._restore_backup_internal(
                    backup,
                    extension_name,
                    restore_data,
                    restore_config,
                    restore_code
                )
                
                if success:
                    await self._log_lifecycle_event(
                        extension_name,
                        LifecycleEventType.BACKUP_RESTORED,
                        {
                            "backup_id": backup_id,
                            "restored_components": {
                                "data": restore_data,
                                "config": restore_config,
                                "code": restore_code
                            }
                        }
                    )
                
                return success
                
            except Exception as e:
                # Attempt to restore from snapshot if available
                if snapshot:
                    try:
                        await self.restore_snapshot(snapshot.snapshot_id)
                        self.logger.info(
                            f"Restored from snapshot after failed backup restore"
                        )
                    except Exception as snapshot_error:
                        self.logger.error(
                            f"Failed to restore from snapshot: {snapshot_error}"
                        )
                
                raise e
    
    async def _restore_backup_internal(
        self,
        backup: ExtensionBackup,
        extension_name: str,
        restore_data: bool,
        restore_config: bool,
        restore_code: bool
    ) -> bool:
        """Internal backup restore logic."""
        # Verify backup integrity
        if not await self._verify_backup_integrity(backup):
            raise ValueError(f"Backup integrity check failed: {backup.backup_id}")
        
        # Extract backup
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract archive
            await self._extract_archive(Path(backup.file_path), temp_path)
            
            backup_dir = temp_path / backup.backup_id
            if not backup_dir.exists():
                # Archive might be extracted directly
                backup_dir = temp_path
            
            # Load manifest
            manifest_path = backup_dir / "manifest.json"
            if not manifest_path.exists():
                raise ValueError("Backup manifest not found")
            
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Stop extension if running
            was_running = await self.extension_manager.is_extension_running(extension_name)
            if was_running:
                await self.extension_manager.stop_extension(extension_name)
            
            try:
                # Restore components
                if restore_code and manifest.get("code_backup"):
                    await self._restore_extension_code(
                        extension_name, backup_dir / "code"
                    )
                
                if restore_config and manifest.get("config_backup"):
                    await self._restore_extension_config(
                        extension_name, backup_dir / "config"
                    )
                
                if restore_data and manifest.get("data_backup"):
                    await self._restore_extension_data(
                        extension_name, backup_dir / "data"
                    )
                
                # Restart extension if it was running
                if was_running:
                    await self.extension_manager.start_extension(extension_name)
                
                return True
                
            except Exception as e:
                # Try to restart extension even if restore failed
                if was_running:
                    try:
                        await self.extension_manager.start_extension(extension_name)
                    except Exception:
                        pass
                raise e
    
    async def create_snapshot(self, extension_name: str) -> ExtensionSnapshot:
        """Create a lightweight snapshot of extension state."""
        self.logger.info(f"Creating snapshot for extension: {extension_name}")
        
        # Generate snapshot ID
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_id = f"{extension_name}_snapshot_{timestamp}"
        
        # Get extension info
        extension_info = await self.extension_manager.get_extension_info(extension_name)
        if not extension_info:
            raise ValueError(f"Extension not found: {extension_name}")
        
        # Collect current state
        state = {
            "status": await self.extension_manager.get_extension_status(extension_name),
            "metrics": await self.extension_manager.get_extension_metrics(extension_name),
            "runtime_info": extension_info
        }
        
        # Collect configuration
        config = await self._get_extension_configuration(extension_name)
        
        # Calculate data checksum
        data_checksum = await self._calculate_data_checksum(extension_name)
        
        snapshot = ExtensionSnapshot(
            snapshot_id=snapshot_id,
            extension_name=extension_name,
            version=extension_info.get("version", "unknown"),
            created_at=datetime.utcnow(),
            state=state,
            configuration=config,
            data_checksum=data_checksum
        )
        
        # Save snapshot (this would typically go to database)
        self.logger.info(f"Snapshot created: {snapshot_id}")
        
        return snapshot
    
    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore extension from a snapshot."""
        # This would typically load from database
        # For now, this is a placeholder
        self.logger.info(f"Restoring from snapshot: {snapshot_id}")
        return True
    
    async def list_backups(
        self,
        extension_name: Optional[str] = None,
        backup_type: Optional[str] = None,
        limit: int = 50
    ) -> List[ExtensionBackup]:
        """List available backups."""
        # This would typically query database
        # For now, scan backup directory
        backups = []
        
        for backup_file in self.backup_root.glob("*.tar.gz"):
            try:
                # Extract backup info from filename
                parts = backup_file.stem.split("_")
                if len(parts) >= 3:
                    ext_name = parts[0]
                    b_type = parts[1]
                    
                    if extension_name and ext_name != extension_name:
                        continue
                    
                    if backup_type and b_type != backup_type:
                        continue
                    
                    # Create basic backup info
                    backup = ExtensionBackup(
                        backup_id=backup_file.stem,
                        extension_name=ext_name,
                        version="unknown",
                        created_at=datetime.fromtimestamp(backup_file.stat().st_mtime),
                        backup_type=b_type,
                        size_bytes=backup_file.stat().st_size,
                        file_path=str(backup_file),
                        checksum="",
                        metadata={}
                    )
                    backups.append(backup)
            except Exception as e:
                self.logger.warning(f"Error processing backup file {backup_file}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        
        return backups[:limit]
    
    async def get_backup(self, backup_id: str) -> Optional[ExtensionBackup]:
        """Get backup by ID."""
        backups = await self.list_backups()
        for backup in backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        backup = await self.get_backup(backup_id)
        if not backup:
            return False
        
        try:
            Path(backup.file_path).unlink()
            self.logger.info(f"Deleted backup: {backup_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    async def _backup_extension_code(
        self, 
        extension_name: str, 
        backup_path: Path
    ) -> int:
        """Backup extension code files."""
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Get extension directory
        extension_dir = await self.extension_manager.get_extension_directory(extension_name)
        if not extension_dir or not extension_dir.exists():
            return 0
        
        # Copy extension files
        shutil.copytree(extension_dir, backup_path / "extension", dirs_exist_ok=True)
        
        # Calculate size
        return sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
    
    async def _backup_extension_config(
        self, 
        extension_name: str, 
        backup_path: Path
    ) -> int:
        """Backup extension configuration."""
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Get extension configuration
        config = await self._get_extension_configuration(extension_name)
        
        # Save configuration
        config_file = backup_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_file.stat().st_size
    
    async def _backup_extension_data(
        self, 
        extension_name: str, 
        backup_path: Path
    ) -> int:
        """Backup extension data."""
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # This would typically export database tables
        # For now, create a placeholder
        data_file = backup_path / "data.json"
        with open(data_file, 'w') as f:
            json.dump({"placeholder": "data backup"}, f)
        
        return data_file.stat().st_size
    
    async def _restore_extension_code(
        self, 
        extension_name: str, 
        backup_path: Path
    ) -> None:
        """Restore extension code from backup."""
        if not backup_path.exists():
            return
        
        extension_dir = await self.extension_manager.get_extension_directory(extension_name)
        if extension_dir:
            # Remove existing code
            if extension_dir.exists():
                shutil.rmtree(extension_dir)
            
            # Restore from backup
            shutil.copytree(backup_path / "extension", extension_dir)
    
    async def _restore_extension_config(
        self, 
        extension_name: str, 
        backup_path: Path
    ) -> None:
        """Restore extension configuration from backup."""
        config_file = backup_path / "config.json"
        if not config_file.exists():
            return
        
        with open(config_file) as f:
            config = json.load(f)
        
        # This would typically update database configuration
        # For now, this is a placeholder
        self.logger.info(f"Restored configuration for {extension_name}")
    
    async def _restore_extension_data(
        self, 
        extension_name: str, 
        backup_path: Path
    ) -> None:
        """Restore extension data from backup."""
        data_file = backup_path / "data.json"
        if not data_file.exists():
            return
        
        # This would typically restore database tables
        # For now, this is a placeholder
        self.logger.info(f"Restored data for {extension_name}")
    
    async def _create_archive(self, source_dir: Path, archive_path: Path) -> None:
        """Create compressed archive."""
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)
    
    async def _extract_archive(self, archive_path: Path, extract_dir: Path) -> None:
        """Extract compressed archive."""
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(extract_dir)
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    async def _verify_backup_integrity(self, backup: ExtensionBackup) -> bool:
        """Verify backup file integrity."""
        if not Path(backup.file_path).exists():
            return False
        
        # Verify checksum if available
        if backup.checksum:
            current_checksum = await self._calculate_checksum(Path(backup.file_path))
            return current_checksum == backup.checksum
        
        return True
    
    async def _get_extension_configuration(self, extension_name: str) -> Dict[str, Any]:
        """Get extension configuration."""
        # This would typically query database
        # For now, return placeholder
        return {"extension_name": extension_name, "config": {}}
    
    async def _calculate_data_checksum(self, extension_name: str) -> str:
        """Calculate checksum of extension data."""
        # This would typically hash database tables
        # For now, return placeholder
        return hashlib.sha256(extension_name.encode()).hexdigest()
    
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