"""
Extension Lifecycle Management

This module provides comprehensive lifecycle management for extensions including:
- Rollback and recovery mechanisms
- Health monitoring and auto-restart
- Backup and restore capabilities
- Migration tools for updates
"""

from .manager import ExtensionLifecycleManager
from .health_monitor import ExtensionHealthMonitor
from .backup_manager import ExtensionBackupManager
from .migration_manager import ExtensionMigrationManager
from .recovery_manager import ExtensionRecoveryManager
from .models import (
    ExtensionHealth,
    ExtensionBackup,
    ExtensionMigration,
    LifecycleEvent,
    RecoveryAction
)

__all__ = [
    'ExtensionLifecycleManager',
    'ExtensionHealthMonitor',
    'ExtensionBackupManager',
    'ExtensionMigrationManager',
    'ExtensionRecoveryManager',
    'ExtensionHealth',
    'ExtensionBackup',
    'ExtensionMigration',
    'LifecycleEvent',
    'RecoveryAction'
]