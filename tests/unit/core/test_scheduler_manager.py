"""
Tests for the autonomous training scheduler manager.

This module tests the cron-based scheduling system for autonomous learning cycles,
including schedule management, safety controls, notifications, and error handling.
"""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_karen_engine.core.response.scheduler_manager import (
    SchedulerManager, AutonomousConfig, NotificationConfig, SafetyControls,
    ScheduleInfo, ScheduleStatus, NotificationType, SafetyLevel,
    NotificationManager, ResourceMonitor
)
from ai_karen_engine.core.response.autonomous_learner import (
    AutonomousLearner, LearningCycleResult, TrainingStatus
)


@pytest.fixture
def mock_autonomous_learner():
    """Create a mock autonomous learner."""
    learner = Mock(spec=AutonomousLearner)
    
    # Mock successful learning cycle
    result = LearningCycleResult(
        cycle_id="test-cycle-123",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        status=TrainingStatus.COMPLETED,
        data_collected=150,
        examples_created=120,
        training_time=45.5,
        model_improved=True
    )
    
    learner.trigger_learning_cycle = AsyncMock(return_value=result)
    return learner


@pytest.fixture
def mock_memory_service():
    """Create a mock memory service."""
    service = Mock()
    service.store_web_ui_memory = AsyncMock()
    service.query_memories = AsyncMock(return_value=[])
    return service


@pytest.fixture
def temp_storage_path():
    """Create a temporary storage path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def scheduler_manager(mock_autonomous_learner, mock_memory_service, temp_storage_path):
    """Create a scheduler manager for testing."""
    return SchedulerManager(
        autonomous_learner=mock_autonomous_learner,
        memory_service=mock_memory_service,
        storage_path=temp_storage_path
    )


@pytest.fixture
def sample_config():
    """Create a sample autonomous configuration."""
    return AutonomousConfig(
        enabled=True,
        training_schedule="0 2 * * *",
        timezone="UTC",
        min_data_threshold=50,
        quality_threshold=0.7,
        validation_threshold=0.85,
        safety_controls=SafetyControls(
            level=SafetyLevel.MODERATE,
            min_data_threshold=50,
            max_data_threshold=5000,
            quality_threshold=0.7,
            max_training_time_minutes=30,
            validation_threshold=0.85,
            rollback_on_degradation=True,
            max_memory_usage_mb=1024,
            max_cpu_usage_percent=70.0,
            max_consecutive_failures=2,
            failure_cooldown_hours=12
        ),
        notifications=NotificationConfig(
            enabled=True,
            types=[NotificationType.LOG, NotificationType.MEMORY],
            memory_tenant_id="test-tenant",
            memory_importance_score=8
        ),
        max_training_time=1800,
        backup_models=True,
        auto_rollback=True
    )


class TestSchedulerManager:
    """Test the SchedulerManager class."""
    
    def test_init(self, scheduler_manager):
        """Test scheduler manager initialization."""
        assert scheduler_manager.schedules == {}
        assert scheduler_manager.running_tasks == {}
        assert not scheduler_manager.running
        assert scheduler_manager.storage_path.exists()
    
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    def test_create_training_schedule(self, mock_croniter, scheduler_manager, sample_config):
        """Test creating a training schedule."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=sample_config,
            description="Test description"
        )
        
        assert schedule_id in scheduler_manager.schedules
        schedule = scheduler_manager.schedules[schedule_id]
        assert schedule.name == "Test Schedule"
        assert schedule.tenant_id == "test-tenant"
        assert schedule.cron_expression == "0 2 * * *"
        assert schedule.status == ScheduleStatus.ACTIVE
        assert schedule.next_run is not None
    
    def test_create_schedule_invalid_cron(self, scheduler_manager, sample_config):
        """Test creating a schedule with invalid cron expression."""
        with patch('ai_karen_engine.core.response.scheduler_manager.croniter') as mock_croniter:
            mock_croniter.is_valid.return_value = False
            
            with pytest.raises(ValueError, match="Invalid cron expression"):
                scheduler_manager.create_training_schedule(
                    tenant_id="test-tenant",
                    name="Test Schedule",
                    cron_expression="invalid cron",
                    config=sample_config
                )
    
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    def test_update_schedule(self, mock_croniter, scheduler_manager, sample_config):
        """Test updating a schedule."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedule
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Original Name",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        # Update schedule
        success = scheduler_manager.update_schedule(
            schedule_id,
            name="Updated Name",
            description="Updated description"
        )
        
        assert success
        schedule = scheduler_manager.schedules[schedule_id]
        assert schedule.name == "Updated Name"
        assert schedule.description == "Updated description"
    
    def test_update_nonexistent_schedule(self, scheduler_manager):
        """Test updating a non-existent schedule."""
        with pytest.raises(ValueError, match="Schedule not found"):
            scheduler_manager.update_schedule("nonexistent-id", name="New Name")
    
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    def test_pause_resume_schedule(self, mock_croniter, scheduler_manager, sample_config):
        """Test pausing and resuming a schedule."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedule
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        # Pause schedule
        success = scheduler_manager.pause_schedule(schedule_id)
        assert success
        assert scheduler_manager.schedules[schedule_id].status == ScheduleStatus.PAUSED
        
        # Resume schedule
        success = scheduler_manager.resume_schedule(schedule_id)
        assert success
        assert scheduler_manager.schedules[schedule_id].status == ScheduleStatus.ACTIVE
    
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    def test_delete_schedule(self, mock_croniter, scheduler_manager, sample_config):
        """Test deleting a schedule."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedule
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        assert schedule_id in scheduler_manager.schedules
        
        # Delete schedule
        success = scheduler_manager.delete_schedule(schedule_id)
        assert success
        assert schedule_id not in scheduler_manager.schedules
    
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    def test_get_schedule_status(self, mock_croniter, scheduler_manager, sample_config):
        """Test getting schedule status."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        next_run = datetime.utcnow() + timedelta(hours=1)
        mock_cron_instance.get_next.return_value = next_run
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedule
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        # Get status
        status = scheduler_manager.get_schedule_status(schedule_id)
        
        assert status is not None
        assert status["schedule_id"] == schedule_id
        assert status["name"] == "Test Schedule"
        assert status["status"] == ScheduleStatus.ACTIVE.value
        assert status["cron_expression"] == "0 2 * * *"
        assert status["total_runs"] == 0
        assert status["successful_runs"] == 0
        assert status["failed_runs"] == 0
        assert not status["is_running"]
    
    def test_get_nonexistent_schedule_status(self, scheduler_manager):
        """Test getting status of non-existent schedule."""
        status = scheduler_manager.get_schedule_status("nonexistent-id")
        assert status is None
    
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    def test_list_schedules(self, mock_croniter, scheduler_manager, sample_config):
        """Test listing schedules."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedules for different tenants
        schedule_id1 = scheduler_manager.create_training_schedule(
            tenant_id="tenant-1",
            name="Schedule 1",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        schedule_id2 = scheduler_manager.create_training_schedule(
            tenant_id="tenant-2",
            name="Schedule 2",
            cron_expression="0 3 * * *",
            config=sample_config
        )
        
        # List all schedules
        all_schedules = scheduler_manager.list_schedules()
        assert len(all_schedules) == 2
        
        # List schedules for specific tenant
        tenant1_schedules = scheduler_manager.list_schedules("tenant-1")
        assert len(tenant1_schedules) == 1
        assert tenant1_schedules[0]["schedule_id"] == schedule_id1
    
    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self, scheduler_manager):
        """Test starting and stopping the scheduler."""
        # Start scheduler
        await scheduler_manager.start_scheduler()
        assert scheduler_manager.running
        assert scheduler_manager.scheduler_task is not None
        
        # Stop scheduler
        await scheduler_manager.stop_scheduler()
        assert not scheduler_manager.running
        assert len(scheduler_manager.running_tasks) == 0
    
    def test_save_load_schedules(self, scheduler_manager, sample_config, temp_storage_path):
        """Test saving and loading schedules."""
        with patch('ai_karen_engine.core.response.scheduler_manager.croniter') as mock_croniter:
            mock_croniter.is_valid.return_value = True
            mock_cron_instance = Mock()
            mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
            mock_croniter.return_value = mock_cron_instance
            
            # Create schedule
            schedule_id = scheduler_manager.create_training_schedule(
                tenant_id="test-tenant",
                name="Test Schedule",
                cron_expression="0 2 * * *",
                config=sample_config
            )
            
            # Create new scheduler manager with same storage path
            new_scheduler = SchedulerManager(
                autonomous_learner=Mock(),
                storage_path=temp_storage_path
            )
            
            # Check that schedule was loaded
            assert schedule_id in new_scheduler.schedules
            loaded_schedule = new_scheduler.schedules[schedule_id]
            assert loaded_schedule.name == "Test Schedule"
            assert loaded_schedule.tenant_id == "test-tenant"


class TestNotificationManager:
    """Test the NotificationManager class."""
    
    @pytest.fixture
    def notification_manager(self, mock_memory_service):
        """Create a notification manager for testing."""
        return NotificationManager(mock_memory_service)
    
    @pytest.mark.asyncio
    async def test_send_log_notification(self, notification_manager):
        """Test sending log notifications."""
        config = NotificationConfig(
            enabled=True,
            types=[NotificationType.LOG]
        )
        
        with patch('ai_karen_engine.core.response.scheduler_manager.logger') as mock_logger:
            await notification_manager.send_notification(
                config,
                "training_completed",
                "Training Completed",
                "Training was successful",
                {"model_improved": True}
            )
            
            mock_logger.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_memory_notification(self, notification_manager, mock_memory_service):
        """Test sending memory notifications."""
        config = NotificationConfig(
            enabled=True,
            types=[NotificationType.MEMORY],
            memory_tenant_id="test-tenant",
            memory_importance_score=8
        )
        
        await notification_manager.send_notification(
            config,
            "training_completed",
            "Training Completed",
            "Training was successful",
            {"model_improved": True}
        )
        
        mock_memory_service.store_web_ui_memory.assert_called_once()
        call_args = mock_memory_service.store_web_ui_memory.call_args
        assert call_args[1]["tenant_id"] == "test-tenant"
        assert call_args[1]["importance_score"] == 8
        assert "autonomous_training" in call_args[1]["tags"]
    
    @pytest.mark.asyncio
    async def test_send_email_notification(self, notification_manager):
        """Test sending email notifications."""
        config = NotificationConfig(
            enabled=True,
            types=[NotificationType.EMAIL],
            email_smtp_host="smtp.example.com",
            email_smtp_port=587,
            email_username="test@example.com",
            email_password="password",
            email_recipients=["admin@example.com"],
            email_use_tls=True
        )
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            await notification_manager.send_notification(
                config,
                "training_completed",
                "Training Completed",
                "Training was successful"
            )
            
            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test@example.com", "password")
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_webhook_notification(self, notification_manager):
        """Test sending webhook notifications."""
        config = NotificationConfig(
            enabled=True,
            types=[NotificationType.WEBHOOK],
            webhook_url="https://example.com/webhook",
            webhook_headers={"Authorization": "Bearer token"},
            webhook_timeout=30
        )
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post
            
            await notification_manager.send_notification(
                config,
                "training_completed",
                "Training Completed",
                "Training was successful"
            )
            
            # Verify webhook was called
            mock_session.assert_called_once()


class TestResourceMonitor:
    """Test the ResourceMonitor class."""
    
    @pytest.fixture
    def resource_monitor(self):
        """Create a resource monitor for testing."""
        return ResourceMonitor()
    
    @pytest.mark.asyncio
    async def test_get_current_usage_with_psutil(self, resource_monitor):
        """Test getting resource usage with psutil available."""
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            # Mock memory info
            mock_memory_info = Mock()
            mock_memory_info.used = 2 * 1024 * 1024 * 1024  # 2GB
            mock_memory_info.percent = 75.0
            mock_memory.return_value = mock_memory_info
            
            # Mock CPU usage
            mock_cpu.return_value = 45.5
            
            usage = await resource_monitor.get_current_usage()
            
            assert usage["memory_mb"] == 2048.0
            assert usage["memory_percent"] == 75.0
            assert usage["cpu_percent"] == 45.5
    
    @pytest.mark.asyncio
    async def test_get_current_usage_without_psutil(self, resource_monitor):
        """Test getting resource usage without psutil available."""
        with patch('ai_karen_engine.core.response.scheduler_manager.psutil', None):
            usage = await resource_monitor.get_current_usage()
            
            # Should return fallback values
            assert "memory_mb" in usage
            assert "memory_percent" in usage
            assert "cpu_percent" in usage
    
    @pytest.mark.asyncio
    async def test_usage_caching(self, resource_monitor):
        """Test that resource usage is cached."""
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            mock_memory_info = Mock()
            mock_memory_info.used = 1024 * 1024 * 1024  # 1GB
            mock_memory_info.percent = 50.0
            mock_memory.return_value = mock_memory_info
            mock_cpu.return_value = 25.0
            
            # First call
            usage1 = await resource_monitor.get_current_usage()
            
            # Second call (should use cache)
            usage2 = await resource_monitor.get_current_usage()
            
            assert usage1 == usage2
            # psutil should only be called once due to caching
            assert mock_memory.call_count == 1
            assert mock_cpu.call_count == 1


class TestSafetyControls:
    """Test safety control functionality."""
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    async def test_safety_controls_memory_limit(self, mock_croniter, scheduler_manager, sample_config):
        """Test safety controls for memory usage."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedule with strict memory limits
        config = sample_config
        config.safety_controls.max_memory_usage_mb = 512  # Low limit
        
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=config
        )
        
        schedule = scheduler_manager.schedules[schedule_id]
        
        # Mock high memory usage
        with patch.object(scheduler_manager.resource_monitor, 'get_current_usage') as mock_usage:
            mock_usage.return_value = {
                "memory_mb": 1024,  # Higher than limit
                "memory_percent": 80.0,
                "cpu_percent": 25.0
            }
            
            # Safety check should fail
            result = await scheduler_manager._check_safety_controls(schedule)
            assert not result
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    async def test_safety_controls_consecutive_failures(self, mock_croniter, scheduler_manager, sample_config):
        """Test safety controls for consecutive failures."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedule
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        schedule = scheduler_manager.schedules[schedule_id]
        
        # Set consecutive failures above threshold
        schedule.consecutive_failures = 5  # Above the limit of 2
        
        # Mock normal resource usage
        with patch.object(scheduler_manager.resource_monitor, 'get_current_usage') as mock_usage:
            mock_usage.return_value = {
                "memory_mb": 512,
                "memory_percent": 50.0,
                "cpu_percent": 25.0
            }
            
            # Safety check should fail due to consecutive failures
            result = await scheduler_manager._check_safety_controls(schedule)
            assert not result


class TestScheduleExecution:
    """Test schedule execution functionality."""
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    async def test_execute_training_success(self, mock_croniter, scheduler_manager, sample_config, mock_autonomous_learner):
        """Test successful training execution."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Create schedule
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        schedule = scheduler_manager.schedules[schedule_id]
        
        # Execute training
        await scheduler_manager._execute_training(schedule_id, schedule)
        
        # Verify autonomous learner was called
        mock_autonomous_learner.trigger_learning_cycle.assert_called_once_with(
            tenant_id="test-tenant",
            force_training=False
        )
        
        # Verify schedule statistics were updated
        assert schedule.total_runs == 1
        assert schedule.successful_runs == 1
        assert schedule.failed_runs == 0
        assert schedule.consecutive_failures == 0
        assert schedule.last_result is not None
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.core.response.scheduler_manager.croniter')
    async def test_execute_training_failure(self, mock_croniter, scheduler_manager, sample_config, mock_autonomous_learner):
        """Test training execution failure."""
        # Mock croniter
        mock_croniter.is_valid.return_value = True
        mock_cron_instance = Mock()
        mock_cron_instance.get_next.return_value = datetime.utcnow() + timedelta(hours=1)
        mock_croniter.return_value = mock_cron_instance
        
        # Mock learning cycle failure
        mock_autonomous_learner.trigger_learning_cycle.side_effect = Exception("Training failed")
        
        # Create schedule
        schedule_id = scheduler_manager.create_training_schedule(
            tenant_id="test-tenant",
            name="Test Schedule",
            cron_expression="0 2 * * *",
            config=sample_config
        )
        
        schedule = scheduler_manager.schedules[schedule_id]
        
        # Execute training
        await scheduler_manager._execute_training(schedule_id, schedule)
        
        # Verify schedule statistics were updated for failure
        assert schedule.total_runs == 1
        assert schedule.successful_runs == 0
        assert schedule.failed_runs == 1
        assert schedule.consecutive_failures == 1
        
        # Verify error was recorded
        result = json.loads(schedule.last_result)
        assert "error" in result
        assert result["status"] == "failed"


if __name__ == "__main__":
    pytest.main([__file__])