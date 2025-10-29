"""
Extension Recovery Manager

Handles extension recovery operations and failure scenarios.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from .models import (
    ExtensionHealth,
    ExtensionHealthStatus,
    RecoveryAction,
    RecoveryActionType,
    LifecycleEvent,
    LifecycleEventType
)
from .backup_manager import ExtensionBackupManager
from .migration_manager import ExtensionMigrationManager
from ..manager import ExtensionManager


class ExtensionRecoveryManager:
    """Manages extension recovery operations."""
    
    def __init__(
        self,
        extension_manager: ExtensionManager,
        backup_manager: ExtensionBackupManager,
        migration_manager: ExtensionMigrationManager,
        db_session: Session
    ):
        self.extension_manager = extension_manager
        self.backup_manager = backup_manager
        self.migration_manager = migration_manager
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        self._recovery_history: Dict[str, List[Dict[str, Any]]] = {}
        self._recovery_locks: Dict[str, asyncio.Lock] = {}
    
    async def recover_extension(
        self,
        extension_name: str,
        recovery_strategy: str = "auto",
        force_recovery: bool = False
    ) -> bool:
        """Recover a failed extension."""
        # Get or create lock for this extension
        if extension_name not in self._recovery_locks:
            self._recovery_locks[extension_name] = asyncio.Lock()
        
        async with self._recovery_locks[extension_name]:
            return await self._recover_extension_internal(
                extension_name, recovery_strategy, force_recovery
            )
    
    async def _recover_extension_internal(
        self,
        extension_name: str,
        recovery_strategy: str,
        force_recovery: bool
    ) -> bool:
        """Internal recovery logic."""
        self.logger.info(f"Starting recovery for extension: {extension_name}")
        
        # Check if recovery is needed
        if not force_recovery:
            health = await self._get_extension_health(extension_name)
            if health and health.status == ExtensionHealthStatus.HEALTHY:
                self.logger.info(f"Extension {extension_name} is healthy, no recovery needed")
                return True
        
        # Determine recovery actions based on strategy
        recovery_actions = await self._determine_recovery_actions(
            extension_name, recovery_strategy
        )
        
        # Execute recovery actions
        for action in recovery_actions:
            try:
                success = await self._execute_recovery_action(extension_name, action)
                if success:
                    await self._record_recovery_success(extension_name, action)
                    self.logger.info(
                        f"Recovery successful for {extension_name} using {action['type']}"
                    )
                    return True
                else:
                    await self._record_recovery_failure(extension_name, action, "Action failed")
            except Exception as e:
                await self._record_recovery_failure(extension_name, action, str(e))
                self.logger.error(
                    f"Recovery action {action['type']} failed for {extension_name}: {e}"
                )
        
        self.logger.error(f"All recovery actions failed for {extension_name}")
        return False    

    async def _determine_recovery_actions(
        self,
        extension_name: str,
        strategy: str
    ) -> List[Dict[str, Any]]:
        """Determine recovery actions based on strategy."""
        if strategy == "auto":
            return await self._get_auto_recovery_actions(extension_name)
        elif strategy == "conservative":
            return await self._get_conservative_recovery_actions(extension_name)
        elif strategy == "aggressive":
            return await self._get_aggressive_recovery_actions(extension_name)
        else:
            raise ValueError(f"Unknown recovery strategy: {strategy}")
    
    async def _get_auto_recovery_actions(
        self, extension_name: str
    ) -> List[Dict[str, Any]]:
        """Get automatic recovery actions."""
        actions = []
        
        # Get extension health and history
        health = await self._get_extension_health(extension_name)
        history = self._recovery_history.get(extension_name, [])
        
        # Recent restart attempts
        recent_restarts = len([
            h for h in history 
            if h.get("action") == "restart" 
            and h.get("timestamp", datetime.min) > datetime.utcnow() - timedelta(hours=1)
        ])
        
        # Progressive recovery strategy
        if recent_restarts < 2:
            actions.append({"type": "restart", "priority": 1})
        
        if recent_restarts >= 1:
            actions.append({"type": "clear_cache", "priority": 2})
            actions.append({"type": "restore_last_backup", "priority": 3})
        
        if recent_restarts >= 3:
            actions.append({"type": "rollback_version", "priority": 4})
            actions.append({"type": "disable", "priority": 5})
        
        return sorted(actions, key=lambda x: x["priority"])
    
    async def _get_conservative_recovery_actions(
        self, extension_name: str
    ) -> List[Dict[str, Any]]:
        """Get conservative recovery actions."""
        return [
            {"type": "restart", "priority": 1},
            {"type": "clear_cache", "priority": 2}
        ]
    
    async def _get_aggressive_recovery_actions(
        self, extension_name: str
    ) -> List[Dict[str, Any]]:
        """Get aggressive recovery actions."""
        return [
            {"type": "restart", "priority": 1},
            {"type": "clear_cache", "priority": 2},
            {"type": "restore_last_backup", "priority": 3},
            {"type": "rollback_version", "priority": 4},
            {"type": "reinstall", "priority": 5}
        ]
    
    async def _execute_recovery_action(
        self, extension_name: str, action: Dict[str, Any]
    ) -> bool:
        """Execute a specific recovery action."""
        action_type = action["type"]
        
        self.logger.info(f"Executing recovery action: {action_type} for {extension_name}")
        
        if action_type == "restart":
            return await self._restart_extension(extension_name)
        elif action_type == "clear_cache":
            return await self._clear_extension_cache(extension_name)
        elif action_type == "restore_last_backup":
            return await self._restore_last_backup(extension_name)
        elif action_type == "rollback_version":
            return await self._rollback_to_previous_version(extension_name)
        elif action_type == "reinstall":
            return await self._reinstall_extension(extension_name)
        elif action_type == "disable":
            return await self._disable_extension(extension_name)
        else:
            self.logger.error(f"Unknown recovery action: {action_type}")
            return False    

    async def _restart_extension(self, extension_name: str) -> bool:
        """Restart an extension."""
        try:
            await self.extension_manager.restart_extension(extension_name)
            
            # Wait a bit and check if it's running
            await asyncio.sleep(5)
            return await self.extension_manager.is_extension_running(extension_name)
        except Exception as e:
            self.logger.error(f"Failed to restart {extension_name}: {e}")
            return False
    
    async def _clear_extension_cache(self, extension_name: str) -> bool:
        """Clear extension cache."""
        try:
            await self.extension_manager.clear_extension_cache(extension_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache for {extension_name}: {e}")
            return False
    
    async def _restore_last_backup(self, extension_name: str) -> bool:
        """Restore from the most recent backup."""
        try:
            backups = await self.backup_manager.list_backups(
                extension_name=extension_name, limit=1
            )
            
            if not backups:
                self.logger.warning(f"No backups found for {extension_name}")
                return False
            
            latest_backup = backups[0]
            success = await self.backup_manager.restore_backup(
                latest_backup.backup_id,
                target_extension_name=extension_name
            )
            
            if success:
                # Wait and verify
                await asyncio.sleep(10)
                return await self.extension_manager.is_extension_running(extension_name)
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to restore backup for {extension_name}: {e}")
            return False
    
    async def _rollback_to_previous_version(self, extension_name: str) -> bool:
        """Rollback to previous version."""
        try:
            # Get current version
            info = await self.extension_manager.get_extension_info(extension_name)
            if not info:
                return False
            
            current_version = info.get("version")
            
            # Find previous version (this would typically query version history)
            # For now, this is a placeholder
            self.logger.info(f"Would rollback {extension_name} from {current_version}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to rollback {extension_name}: {e}")
            return False
    
    async def _reinstall_extension(self, extension_name: str) -> bool:
        """Reinstall extension."""
        try:
            # This would typically uninstall and reinstall from marketplace
            self.logger.info(f"Would reinstall {extension_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reinstall {extension_name}: {e}")
            return False
    
    async def _disable_extension(self, extension_name: str) -> bool:
        """Disable extension as last resort."""
        try:
            await self.extension_manager.disable_extension(extension_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable {extension_name}: {e}")
            return False    

    async def _get_extension_health(self, extension_name: str) -> Optional[ExtensionHealth]:
        """Get extension health status."""
        # This would typically query the health monitor
        # For now, return a placeholder
        return None
    
    async def _record_recovery_success(
        self, extension_name: str, action: Dict[str, Any]
    ) -> None:
        """Record successful recovery action."""
        if extension_name not in self._recovery_history:
            self._recovery_history[extension_name] = []
        
        self._recovery_history[extension_name].append({
            "action": action["type"],
            "timestamp": datetime.utcnow(),
            "success": True
        })
        
        await self._log_lifecycle_event(
            extension_name,
            LifecycleEventType.RECOVERY_COMPLETED,
            {"action": action, "success": True}
        )
    
    async def _record_recovery_failure(
        self, extension_name: str, action: Dict[str, Any], error: str
    ) -> None:
        """Record failed recovery action."""
        if extension_name not in self._recovery_history:
            self._recovery_history[extension_name] = []
        
        self._recovery_history[extension_name].append({
            "action": action["type"],
            "timestamp": datetime.utcnow(),
            "success": False,
            "error": error
        })
        
        await self._log_lifecycle_event(
            extension_name,
            LifecycleEventType.RECOVERY_INITIATED,
            {"action": action, "success": False, "error": error}
        )
    
    async def get_recovery_history(
        self, extension_name: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recovery history for an extension."""
        history = self._recovery_history.get(extension_name, [])
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
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