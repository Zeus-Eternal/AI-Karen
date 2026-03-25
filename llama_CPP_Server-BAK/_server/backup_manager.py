#!/usr/bin/env python3
"""
Automatic backup and recovery system for llama.cpp server

This module provides functionality to automatically backup and restore
server configurations, models, and other important data.
"""

import os
import sys
import json
import shutil
import tarfile
import zipfile
import hashlib
import tempfile
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass

# Local imports
try:
    from .config_manager import ConfigManager  # type: ignore
    from .error_handler import ErrorCategory, ErrorLevel, handle_error  # type: ignore
except ImportError:
    # Fallback for standalone usage
    class ConfigManager:
        def __init__(self, config_path=None):
            self.config = {}
        
        def get(self, key, default=None):
            return default
        
        def set(self, key, value):
            pass
        
        def save_config(self):
            return True
    
    class ErrorCategory:
        SYSTEM = 0
        BACKUP = 1
    
    class ErrorLevel:
        ERROR = 0
        WARNING = 1
    
    def handle_error(category, code, details=None, level=ErrorLevel.ERROR):
        pass


@dataclass
class BackupInfo:
    """Backup information"""
    id: str
    timestamp: datetime
    size_bytes: int
    checksum: str
    description: str
    includes_config: bool
    includes_models: bool
    includes_logs: bool
    file_path: str
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "description": self.description,
            "includes_config": self.includes_config,
            "includes_models": self.includes_models,
            "includes_logs": self.includes_logs,
            "file_path": self.file_path
        }


class BackupManager:
    """Backup manager for automatic backup and recovery"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize backup manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.config_manager = ConfigManager(config_path)
        
        # Get backup directory from config or use default
        backup_dir = self.config_manager.get("backup.directory", "backups") or "backups"
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Get backup settings from config or use defaults
        self.enabled = self.config_manager.get("backup.enabled", True)
        self.interval_hours = self.config_manager.get("backup.interval_hours", 24)
        self.max_backups = self.config_manager.get("backup.max_backups", 10)
        self.include_config = self.config_manager.get("backup.include_config", True)
        self.include_models = self.config_manager.get("backup.include_models", False)
        self.include_logs = self.config_manager.get("backup.include_logs", True)
        self.compression = self.config_manager.get("backup.compression", "gzip")
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create file handler
        log_file = log_dir / "backup_manager.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Load backup index
        self.backup_index_file = self.backup_dir / "index.json"
        self.backup_index = self._load_backup_index()
    
    def _load_backup_index(self) -> Dict[str, Dict]:
        """Load backup index from file
        
        Returns:
            Dict[str, Dict]: Backup index
        """
        if not self.backup_index_file.exists():
            return {}
        
        try:
            with open(self.backup_index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.BACKUP,
                    "001",
                    f"Failed to load backup index: {e}",
                    ErrorLevel.ERROR
                )
            return {}
    
    def _save_backup_index(self):
        """Save backup index to file"""
        try:
            with open(self.backup_index_file, 'w') as f:
                json.dump(self.backup_index, f, indent=2)
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.BACKUP,
                    "002",
                    f"Failed to save backup index: {e}",
                    ErrorLevel.ERROR
                )
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate checksum for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            str: Checksum as hex string
        """
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _get_backup_id(self) -> str:
        """Generate a unique backup ID
        
        Returns:
            str: Backup ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"{timestamp}_{random_suffix}"
    
    def _cleanup_old_backups(self):
        """Clean up old backups if we exceed the maximum number"""
        # Sort backups by timestamp (newest first)
        sorted_backups = sorted(
            self.backup_index.values(),
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        # Keep only the newest backups
        backups_to_keep = sorted_backups[:self.max_backups]
        backup_ids_to_keep = {backup["id"] for backup in backups_to_keep}
        
        # Delete old backups
        for backup_id, backup_info in list(self.backup_index.items()):
            if backup_id not in backup_ids_to_keep:
                try:
                    backup_file = Path(backup_info["file_path"])
                    if backup_file.exists():
                        backup_file.unlink()
                    
                    # Remove from index
                    del self.backup_index[backup_id]
                    
                    self.logger.info(f"Deleted old backup: {backup_id}")
                except Exception as e:
                    if ErrorCategory and ErrorLevel:
                        handle_error(
                            ErrorCategory.BACKUP,
                            "003",
                            f"Failed to delete old backup {backup_id}: {e}",
                            ErrorLevel.WARNING
                        )
    
    def create_backup(self, description: str = "", include_config: Optional[bool] = None,
                   include_models: Optional[bool] = None, include_logs: Optional[bool] = None) -> Optional[BackupInfo]:
        """Create a backup
        
        Args:
            description: Backup description
            include_config: Whether to include configuration files
            include_models: Whether to include model files
            include_logs: Whether to include log files
            
        Returns:
            Optional[BackupInfo]: Backup information if successful, None otherwise
        """
        if not self.enabled:
            self.logger.info("Backup is disabled")
            return None
        
        # Use provided values or fall back to defaults
        include_config = include_config if include_config is not None else self.include_config
        include_models = include_models if include_models is not None else self.include_models
        include_logs = include_logs if include_logs is not None else self.include_logs
        
        # Generate backup ID
        backup_id = self._get_backup_id()
        
        # Create backup file path
        if self.compression == "zip":
            backup_file = self.backup_dir / f"{backup_id}.zip"
        else:
            backup_file = self.backup_dir / f"{backup_id}.tar.gz"
        
        try:
            # Create backup
            if self.compression == "zip":
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if include_config:
                        self._backup_config(zipf)
                    
                    if include_models:
                        self._backup_models(zipf)
                    
                    if include_logs:
                        self._backup_logs(zipf)
            else:
                with tarfile.open(backup_file, 'w:gz') as tarf:
                    if include_config:
                        self._backup_config(tarf)
                    
                    if include_models:
                        self._backup_models(tarf)
                    
                    if include_logs:
                        self._backup_logs(tarf)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_file)
            
            # Get file size
            size_bytes = backup_file.stat().st_size
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id,
                datetime.now(),
                size_bytes,
                checksum,
                description or f"Backup created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                bool(include_config),
                bool(include_models),
                bool(include_logs),
                str(backup_file)
            )
            
            # Add to index
            self.backup_index[backup_id] = backup_info.to_dict()
            
            # Save index
            self._save_backup_index()
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            self.logger.info(f"Created backup: {backup_id}")
            return backup_info
        
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.BACKUP,
                    "004",
                    f"Failed to create backup {backup_id}: {e}",
                    ErrorLevel.ERROR
                )
            
            # Clean up partial backup file
            if backup_file.exists():
                backup_file.unlink()
            
            return None
    
    def _backup_config(self, archive: Union[zipfile.ZipFile, tarfile.TarFile]) -> None:
        """Backup configuration files
        
        Args:
            archive: Archive object (ZipFile or TarFile)
        """
        # Backup main config file
        if self.config_path and self.config_path.exists():
            if isinstance(archive, zipfile.ZipFile):
                archive.write(self.config_path, arcname="config/config.json")
            else:  # tarfile.TarFile
                archive.add(self.config_path, arcname="config/config.json")
        
        # Backup additional config files
        config_dir = Path("config")
        if config_dir.exists():
            for file_path in config_dir.glob("*.json"):
                if isinstance(archive, zipfile.ZipFile):
                    archive.write(file_path, arcname=f"config/{file_path.name}")
                else:  # tarfile.TarFile
                    archive.add(file_path, arcname=f"config/{file_path.name}")
    
    def _backup_models(self, archive: Union[zipfile.ZipFile, tarfile.TarFile]) -> None:
        """Backup model files
        
        Args:
            archive: Archive object (ZipFile or TarFile)
        """
        models_dir = Path("models")
        if models_dir.exists():
            # Only backup GGUF model files (skip large files if models directory is too big)
            for model_file in models_dir.glob("*.gguf"):
                # Skip files larger than 5GB
                if model_file.stat().st_size > 5 * 1024 * 1024 * 1024:
                    self.logger.warning(f"Skipping large model file: {model_file}")
                    continue
                
                if isinstance(archive, zipfile.ZipFile):
                    archive.write(model_file, arcname=f"models/{model_file.name}")
                else:  # tarfile.TarFile
                    archive.add(model_file, arcname=f"models/{model_file.name}")
    
    def _backup_logs(self, archive: Union[zipfile.ZipFile, tarfile.TarFile]) -> None:
        """Backup log files
        
        Args:
            archive: Archive object (ZipFile or TarFile)
        """
        logs_dir = Path("logs")
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                if isinstance(archive, zipfile.ZipFile):
                    archive.write(log_file, arcname=f"logs/{log_file.name}")
                else:  # tarfile.TarFile
                    archive.add(log_file, arcname=f"logs/{log_file.name}")
    
    def restore_backup(self, backup_id: str, restore_config: Optional[bool] = None,
                      restore_models: Optional[bool] = None, restore_logs: Optional[bool] = None) -> bool:
        """Restore a backup
        
        Args:
            backup_id: Backup ID to restore
            restore_config: Whether to restore configuration files
            restore_models: Whether to restore model files
            restore_logs: Whether to restore log files
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if backup exists
        if backup_id not in self.backup_index:
            self.logger.error(f"Backup not found: {backup_id}")
            return False
        
        # Get backup info
        backup_info = self.backup_index[backup_id]
        
        # Use provided values or fall back to what was backed up
        restore_config = restore_config if restore_config is not None else backup_info.get("includes_config", False)
        restore_models = restore_models if restore_models is not None else backup_info.get("includes_models", False)
        restore_logs = restore_logs if restore_logs is not None else backup_info.get("includes_logs", False)
        
        # Get backup file path
        backup_file = Path(backup_info.get("file_path", ""))
        
        if not backup_file.exists():
            self.logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            # Create temp directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup
                if backup_file.suffix == ".zip":
                    with zipfile.ZipFile(backup_file, 'r') as zipf:
                        zipf.extractall(temp_dir)
                        
                        # Restore files
                        if restore_config:
                            self._restore_config(zipf, temp_dir)
                        
                        if restore_models:
                            self._restore_models(zipf, temp_dir)
                        
                        if restore_logs:
                            self._restore_logs(zipf, temp_dir)
                else:
                    with tarfile.open(backup_file, 'r:gz') as tarf:
                        tarf.extractall(temp_dir)
                        
                        # Restore files
                        if restore_config:
                            self._restore_config(tarf, temp_dir)
                        
                        if restore_models:
                            self._restore_models(tarf, temp_dir)
                        
                        if restore_logs:
                            self._restore_logs(tarf, temp_dir)
            
            self.logger.info(f"Successfully restored backup: {backup_id}")
            return True
        
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.BACKUP,
                    "006",
                    f"Failed to restore backup {backup_id}: {e}",
                    ErrorLevel.ERROR
                )
            
            return False
    
    def restore_backup_from_path(self, backup_path: Union[str, Path], restore_configs: bool = True,
                               restore_models: bool = True, restore_logs: bool = True) -> bool:
        """Restore a backup from a specific path
        
        Args:
            backup_path: Path to the backup file
            restore_configs: Whether to restore configuration files
            restore_models: Whether to restore model files
            restore_logs: Whether to restore log files
            
        Returns:
            bool: True if successful, False otherwise
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Create temp directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup
                if backup_path.suffix == ".zip":
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        zipf.extractall(temp_dir)
                        
                        # Restore files
                        if restore_configs:
                            self._restore_config(zipf, temp_dir)
                        
                        if restore_models:
                            self._restore_models(zipf, temp_dir)
                        
                        if restore_logs:
                            self._restore_logs(zipf, temp_dir)
                else:
                    with tarfile.open(backup_path, 'r:gz') as tarf:
                        tarf.extractall(temp_dir)
                        
                        # Restore files
                        if restore_configs:
                            self._restore_config(tarf, temp_dir)
                        
                        if restore_models:
                            self._restore_models(tarf, temp_dir)
                        
                        if restore_logs:
                            self._restore_logs(tarf, temp_dir)
            
            self.logger.info(f"Successfully restored backup from: {backup_path}")
            return True
        
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.BACKUP,
                    "008",
                    f"Failed to restore backup from {backup_path}: {e}",
                    ErrorLevel.ERROR
                )
            
            return False
    
    def _restore_config(self, archive: Union[zipfile.ZipFile, tarfile.TarFile], temp_dir: str) -> None:
        """Restore configuration files
        
        Args:
            archive: Archive object (ZipFile or TarFile)
            temp_dir: Temporary directory where files were extracted
        """
        # Create config directory if it doesn't exist
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Extract config files
        temp_config_dir = Path(temp_dir) / "config"
        if temp_config_dir.exists():
            for file_path in temp_config_dir.glob("*"):
                if file_path.is_file():
                    shutil.copy2(file_path, config_dir / file_path.name)
    
    def _restore_models(self, archive: Union[zipfile.ZipFile, tarfile.TarFile], temp_dir: str) -> None:
        """Restore model files
        
        Args:
            archive: Archive object (ZipFile or TarFile)
            temp_dir: Temporary directory where files were extracted
        """
        # Create models directory if it doesn't exist
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Extract model files
        temp_models_dir = Path(temp_dir) / "models"
        if temp_models_dir.exists():
            for file_path in temp_models_dir.glob("*"):
                if file_path.is_file():
                    shutil.copy2(file_path, models_dir / file_path.name)
    
    def _restore_logs(self, archive: Union[zipfile.ZipFile, tarfile.TarFile], temp_dir: str) -> None:
        """Restore log files
        
        Args:
            archive: Archive object (ZipFile or TarFile)
            temp_dir: Temporary directory where files were extracted
        """
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Extract log files
        temp_logs_dir = Path(temp_dir) / "logs"
        if temp_logs_dir.exists():
            for file_path in temp_logs_dir.glob("*"):
                if file_path.is_file():
                    shutil.copy2(file_path, logs_dir / file_path.name)
    
    def list_backups(self) -> List[BackupInfo]:
        """List all backups
        
        Returns:
            List[BackupInfo]: List of backup information
        """
        backups = []
        
        for backup_id, backup_data in self.backup_index.items():
            backup_info = BackupInfo(
                backup_data["id"],
                datetime.fromisoformat(backup_data["timestamp"]),
                backup_data["size_bytes"],
                backup_data["checksum"],
                backup_data["description"],
                bool(backup_data["includes_config"]),
                bool(backup_data["includes_models"]),
                bool(backup_data["includes_logs"]),
                backup_data["file_path"]
            )
            backups.append(backup_info)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup
        
        Args:
            backup_id: Backup ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if backup_id not in self.backup_index:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.BACKUP,
                    "009",
                    f"Backup not found: {backup_id}",
                    ErrorLevel.ERROR
                )
            return False
        
        backup_info = self.backup_index[backup_id]
        backup_file = Path(backup_info["file_path"])
        
        try:
            # Delete backup file
            if backup_file.exists():
                backup_file.unlink()
            
            # Remove from index
            del self.backup_index[backup_id]
            
            # Save index
            self._save_backup_index()
            
            self.logger.info(f"Deleted backup: {backup_id}")
            return True
        
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.BACKUP,
                    "010",
                    f"Failed to delete backup {backup_id}: {e}",
                    ErrorLevel.ERROR
                )
            return False
    
    def should_create_backup(self) -> bool:
        """Check if a backup should be created based on the interval
        
        Returns:
            bool: True if a backup should be created, False otherwise
        """
        if not self.enabled:
            return False
        
        # If no backups exist, create one
        if not self.backup_index:
            return True
        
        # Get the most recent backup
        most_recent_backup = max(
            self.backup_index.values(),
            key=lambda x: x["timestamp"]
        )
        
        # Parse timestamp
        last_backup_time = datetime.fromisoformat(most_recent_backup["timestamp"])
        
        # Check if enough time has passed
        interval_hours = self.interval_hours or 24
        next_backup_time = last_backup_time + timedelta(hours=interval_hours)
        
        return datetime.now() >= next_backup_time
    
    def auto_backup(self) -> Optional[BackupInfo]:
        """Create an automatic backup if needed
        
        Returns:
            Optional[BackupInfo]: Backup information if backup was created, None otherwise
        """
        if self.should_create_backup():
            description = f"Automatic backup created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return self.create_backup(description)
        
        return None
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics
        
        Returns:
            Dict[str, Any]: Backup statistics
        """
        total_backups = len(self.backup_index)
        total_size_bytes = sum(info["size_bytes"] for info in self.backup_index.values())
        
        # Get oldest and newest backup
        if total_backups > 0:
            timestamps = [datetime.fromisoformat(info["timestamp"]) for info in self.backup_index.values()]
            oldest_backup = min(timestamps)
            newest_backup = max(timestamps)
        else:
            oldest_backup = None
            newest_backup = None
        
        return {
            "total_backups": total_backups,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "oldest_backup": oldest_backup.isoformat() if oldest_backup else None,
            "newest_backup": newest_backup.isoformat() if newest_backup else None,
            "backup_directory": str(self.backup_dir),
            "enabled": self.enabled,
            "interval_hours": self.interval_hours,
            "max_backups": self.max_backups
        }


def get_backup_manager(config_path: Optional[Union[str, Path]] = None) -> BackupManager:
    """Get backup manager instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        BackupManager: Backup manager instance
    """
    return BackupManager(config_path)


if __name__ == "__main__":
    # Test backup manager
    backup_manager = get_backup_manager()
    
    print("Creating backup...")
    backup_info = backup_manager.create_backup("Test backup")
    
    if backup_info:
        print(f"Backup created: {backup_info.id}")
        print(f"Backup size: {backup_info.size_bytes} bytes")
        print(f"Backup checksum: {backup_info.checksum}")
        
        print("\nListing backups...")
        backups = backup_manager.list_backups()
        for backup in backups:
            print(f"- {backup.id}: {backup.description} ({backup.timestamp})")
        
        print("\nBackup stats:")
        stats = backup_manager.get_backup_stats()
        print(json.dumps(stats, indent=2))
        
        print("\nDeleting backup...")
        success = backup_manager.delete_backup(backup_info.id)
        print(f"Backup deleted: {success}")
    else:
        print("Failed to create backup")