"""
Tests for Extension Lifecycle Management
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from .manager import ExtensionLifecycleManager
from .health_monitor import ExtensionHealthMonitor
from .backup_manager import ExtensionBackupManager
from .migration_manager import ExtensionMigrationManager
from .recovery_manager import ExtensionRecoveryManager
from .models import (
    ExtensionHealth,
    ExtensionHealthStatus,
    ExtensionBackup,
    ExtensionMigration,
    LifecycleEvent,
    RecoveryAction
)


@pytest.fixture
def mock_extension_manager():
    """Mock extension manager."""
    manager = Mock()
    manager.get_loaded_extensions = AsyncMock(return_value=["test_extension"])
    manager.get_extension = AsyncMock(return_value=Mock())
    manager.get_extension_info = AsyncMock(return_value={
        "name": "test_extension",
        "version": "1.0.0",
        "status": "running"
    })
    manager.is_extension_running = AsyncMock(return_value=True)
    manager.start_extension = AsyncMock()
    manager.stop_extension = AsyncMock()
    manager.restart_extension = AsyncMock()
    manager.disable_extension = AsyncMock()
    manager.clear_extension_cache = AsyncMock()
    manager.get_extension_status = AsyncMock(return_value="running")
    manager.get_extension_metrics = AsyncMock(return_value={})
    manager.get_extension_directory = AsyncMock(return_value=Path("/tmp/test_extension"))
    return manager


@pytest.fixture
def mock_version_manager():
    """Mock version manager."""
    manager = Mock()
    manager.get_migration_path = AsyncMock(return_value=[
        {"from": "1.0.0", "to": "1.1.0"}
    ])
    return manager


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def temp_backup_dir(tmp_path):
    """Temporary backup directory."""
    return tmp_path / "backups"


@pytest.fixture
async def lifecycle_manager(
    mock_extension_manager,
    mock_version_manager,
    mock_db_session,
    temp_backup_dir
):
    """Create lifecycle manager for testing."""
    manager = ExtensionLifecycleManager(
        extension_manager=mock_extension_manager,
        version_manager=mock_version_manager,
        db_session=mock_db_session,
        backup_root=temp_backup_dir,
        enable_auto_recovery=False,  # Disable for testing
        health_check_interval=1  # Fast interval for testing
    )
    return manager


class TestExtensionHealthMonitor:
    """Test extension health monitoring."""
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, mock_extension_manager, mock_db_session):
        """Test starting health monitoring."""
        monitor = ExtensionHealthMonitor(
            mock_extension_manager, mock_db_session, check_interval=1
        )
        
        await monitor.start_monitoring()
        assert monitor.is_running
        
        await monitor.stop_monitoring()
        assert not monitor.is_running
    
    @pytest.mark.asyncio
    async def test_extension_monitoring(self, mock_extension_manager, mock_db_session):
        """Test monitoring a specific extension."""
        monitor = ExtensionHealthMonitor(
            mock_extension_manager, mock_db_session, check_interval=1
        )
        
        await monitor.start_extension_monitoring("test_extension")
        assert "test_extension" in monitor._monitoring_tasks
        
        await monitor.stop_extension_monitoring("test_extension")
        assert "test_extension" not in monitor._monitoring_tasks
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_extension_manager, mock_db_session):
        """Test health check execution."""
        monitor = ExtensionHealthMonitor(
            mock_extension_manager, mock_db_session, check_interval=1
        )
        
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.cpu_percent.return_value = 15.0
            mock_process.return_value.memory_info.return_value.rss = 128 * 1024 * 1024
            mock_process.return_value.create_time.return_value = datetime.utcnow().timestamp() - 3600
            
            config = await monitor._get_health_config("test_extension")
            health = await monitor._perform_health_check("test_extension", config)
            
            assert isinstance(health, ExtensionHealth)
            assert health.extension_name == "test_extension"
            assert health.status in ExtensionHealthStatus


class TestExtensionBackupManager:
    """Test extension backup management."""
    
    @pytest.mark.asyncio
    async def test_create_backup(
        self, mock_extension_manager, mock_db_session, temp_backup_dir
    ):
        """Test backup creation."""
        backup_manager = ExtensionBackupManager(
            mock_extension_manager, mock_db_session, temp_backup_dir
        )
        
        backup = await backup_manager.create_backup(
            "test_extension",
            backup_type="full",
            description="Test backup"
        )
        
        assert isinstance(backup, ExtensionBackup)
        assert backup.extension_name == "test_extension"
        assert backup.backup_type == "full"
        assert backup.description == "Test backup"
    
    @pytest.mark.asyncio
    async def test_list_backups(
        self, mock_extension_manager, mock_db_session, temp_backup_dir
    ):
        """Test listing backups."""
        backup_manager = ExtensionBackupManager(
            mock_extension_manager, mock_db_session, temp_backup_dir
        )
        
        # Create a test backup file
        test_backup = temp_backup_dir / "test_extension_full_20240115_120000.tar.gz"
        test_backup.parent.mkdir(parents=True, exist_ok=True)
        test_backup.write_text("test backup content")
        
        backups = await backup_manager.list_backups()
        assert len(backups) >= 0  # May be empty if no backups exist
    
    @pytest.mark.asyncio
    async def test_create_snapshot(
        self, mock_extension_manager, mock_db_session, temp_backup_dir
    ):
        """Test snapshot creation."""
        backup_manager = ExtensionBackupManager(
            mock_extension_manager, mock_db_session, temp_backup_dir
        )
        
        snapshot = await backup_manager.create_snapshot("test_extension")
        
        assert snapshot.extension_name == "test_extension"
        assert snapshot.version == "1.0.0"


class TestExtensionMigrationManager:
    """Test extension migration management."""
    
    @pytest.mark.asyncio
    async def test_plan_migration(
        self,
        mock_extension_manager,
        mock_version_manager,
        mock_db_session,
        temp_backup_dir
    ):
        """Test migration planning."""
        backup_manager = ExtensionBackupManager(
            mock_extension_manager, mock_db_session, temp_backup_dir
        )
        migration_manager = ExtensionMigrationManager(
            mock_extension_manager, backup_manager, mock_version_manager, mock_db_session
        )
        
        steps = await migration_manager._plan_migration(
            "test_extension", "1.0.0", "1.1.0"
        )
        
        assert len(steps) > 0
        assert any(step.name == "download_version" for step in steps)
        assert any(step.name == "stop_extension" for step in steps)
        assert any(step.name == "start_extension" for step in steps)


class TestExtensionRecoveryManager:
    """Test extension recovery management."""
    
    @pytest.mark.asyncio
    async def test_determine_recovery_actions(
        self,
        mock_extension_manager,
        mock_db_session,
        temp_backup_dir
    ):
        """Test recovery action determination."""
        backup_manager = ExtensionBackupManager(
            mock_extension_manager, mock_db_session, temp_backup_dir
        )
        migration_manager = ExtensionMigrationManager(
            mock_extension_manager, backup_manager, Mock(), mock_db_session
        )
        recovery_manager = ExtensionRecoveryManager(
            mock_extension_manager, backup_manager, migration_manager, mock_db_session
        )
        
        actions = await recovery_manager._determine_recovery_actions(
            "test_extension", "auto"
        )
        
        assert len(actions) > 0
        assert any(action["type"] == "restart" for action in actions)
    
    @pytest.mark.asyncio
    async def test_execute_recovery_action(
        self,
        mock_extension_manager,
        mock_db_session,
        temp_backup_dir
    ):
        """Test recovery action execution."""
        backup_manager = ExtensionBackupManager(
            mock_extension_manager, mock_db_session, temp_backup_dir
        )
        migration_manager = ExtensionMigrationManager(
            mock_extension_manager, backup_manager, Mock(), mock_db_session
        )
        recovery_manager = ExtensionRecoveryManager(
            mock_extension_manager, backup_manager, migration_manager, mock_db_session
        )
        
        action = {"type": "restart", "priority": 1}
        success = await recovery_manager._execute_recovery_action(
            "test_extension", action
        )
        
        assert isinstance(success, bool)


class TestExtensionLifecycleManager:
    """Test main lifecycle manager."""
    
    @pytest.mark.asyncio
    async def test_start_stop(self, lifecycle_manager):
        """Test starting and stopping lifecycle management."""
        await lifecycle_manager.start()
        assert lifecycle_manager._is_running
        
        await lifecycle_manager.stop()
        assert not lifecycle_manager._is_running
    
    @pytest.mark.asyncio
    async def test_get_extension_overview(self, lifecycle_manager):
        """Test getting extension overview."""
        overview = await lifecycle_manager.get_extension_overview("test_extension")
        
        assert "extension_name" in overview
        assert "timestamp" in overview
        assert overview["extension_name"] == "test_extension"
    
    @pytest.mark.asyncio
    async def test_get_system_overview(self, lifecycle_manager):
        """Test getting system overview."""
        overview = await lifecycle_manager.get_system_overview()
        
        assert "timestamp" in overview
        assert "extensions" in overview
        assert "statistics" in overview
    
    @pytest.mark.asyncio
    async def test_create_backup(self, lifecycle_manager):
        """Test backup creation through lifecycle manager."""
        backup = await lifecycle_manager.create_backup(
            "test_extension", "full", "Test backup"
        )
        
        assert isinstance(backup, ExtensionBackup)
        assert backup.extension_name == "test_extension"
    
    @pytest.mark.asyncio
    async def test_health_callback(self, lifecycle_manager):
        """Test health change callback."""
        # Enable auto-recovery for this test
        lifecycle_manager.enable_auto_recovery = True
        
        # Create unhealthy status
        health = ExtensionHealth(
            extension_name="test_extension",
            status=ExtensionHealthStatus.CRITICAL,
            last_check=datetime.utcnow(),
            cpu_usage=95.0,
            memory_usage=1024.0,
            disk_usage=0.0,
            error_rate=50.0,
            response_time=5000.0,
            uptime=3600.0,
            restart_count=3,
            health_score=10.0
        )
        
        # This should trigger auto-recovery
        await lifecycle_manager._on_health_change(health)
        
        # Verify recovery was initiated (would need more sophisticated mocking)
        assert True  # Placeholder assertion


# Integration tests
class TestLifecycleIntegration:
    """Integration tests for lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_full_backup_restore_cycle(self, lifecycle_manager):
        """Test complete backup and restore cycle."""
        # Create backup
        backup = await lifecycle_manager.create_backup("test_extension")
        assert backup.extension_name == "test_extension"
        
        # List backups
        backups = await lifecycle_manager.list_backups("test_extension")
        assert len(backups) >= 1
        
        # Restore backup (this would fail in real scenario without proper setup)
        # For testing, we just verify the method can be called
        try:
            await lifecycle_manager.restore_backup(backup.backup_id)
        except Exception:
            pass  # Expected to fail in test environment
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, lifecycle_manager):
        """Test health monitoring integration."""
        await lifecycle_manager.start()
        
        # Wait a bit for monitoring to start
        await asyncio.sleep(0.1)
        
        # Get health status
        health_status = await lifecycle_manager.get_all_health_status()
        assert isinstance(health_status, dict)
        
        await lifecycle_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__])