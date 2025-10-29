"""
Tests for the background task system.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from ..background_tasks import (
    BackgroundTaskManager,
    TaskExecutor,
    TaskScheduler,
    EventManager,
    TaskResourceMonitor,
    TaskDefinition,
    TaskExecution,
    TaskStatus,
    TaskTriggerType,
    EventTrigger
)
from ..models import ExtensionManifest, ExtensionRecord, ExtensionCapabilities, ExtensionBackgroundTask
from ..base import BaseExtension


class MockExtension(BaseExtension):
    """Mock extension for testing."""
    
    async def _initialize(self):
        pass
    
    async def _shutdown(self):
        pass
    
    async def test_task(self, execution_id: str, task_name: str, extension_name: str, **kwargs):
        """Test task function."""
        return {"message": "Task executed successfully", "execution_id": execution_id}
    
    async def failing_task(self, execution_id: str, task_name: str, extension_name: str, **kwargs):
        """Task that always fails."""
        raise Exception("Task failed intentionally")
    
    def sync_task(self, execution_id: str, task_name: str, extension_name: str, **kwargs):
        """Synchronous test task."""
        return {"message": "Sync task executed", "execution_id": execution_id}


@pytest.fixture
def mock_extension():
    """Create a mock extension for testing."""
    manifest = ExtensionManifest(
        name="test-extension",
        version="1.0.0",
        display_name="Test Extension",
        description="Test extension for background tasks",
        author="Test Author",
        license="MIT",
        category="test",
        capabilities=ExtensionCapabilities(provides_background_tasks=True),
        background_tasks=[
            ExtensionBackgroundTask(
                name="test_task",
                schedule="0 * * * *",  # Every hour
                function="test_task",
                description="Test task",
                enabled=True
            )
        ]
    )
    
    from ..models import ExtensionContext
    context = ExtensionContext(extension_name="test-extension")
    
    return MockExtension(manifest, context)


@pytest.fixture
def task_resource_monitor():
    """Create a task resource monitor."""
    return TaskResourceMonitor()


@pytest.fixture
def task_executor(task_resource_monitor):
    """Create a task executor."""
    return TaskExecutor(task_resource_monitor)


@pytest.fixture
def task_scheduler(task_executor):
    """Create a task scheduler."""
    return TaskScheduler(task_executor)


@pytest.fixture
def event_manager(task_executor):
    """Create an event manager."""
    return EventManager(task_executor)


@pytest.fixture
def background_task_manager():
    """Create a background task manager."""
    return BackgroundTaskManager()


class TestTaskResourceMonitor:
    """Test the task resource monitor."""
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, task_resource_monitor):
        """Test starting and stopping resource monitoring."""
        execution_id = "test-execution-1"
        task_name = "test-task"
        
        # Start monitoring
        await task_resource_monitor.start_monitoring(execution_id, task_name)
        assert execution_id in task_resource_monitor.active_tasks
        
        # Stop monitoring
        usage = await task_resource_monitor.stop_monitoring(execution_id)
        assert execution_id not in task_resource_monitor.active_tasks
        assert "duration_seconds" in usage
        assert "memory_usage_mb" in usage


class TestTaskExecutor:
    """Test the task executor."""
    
    @pytest.mark.asyncio
    async def test_execute_successful_task(self, task_executor, mock_extension):
        """Test executing a successful task."""
        task_def = TaskDefinition(
            name="test_task",
            extension_name="test-extension",
            function_path="test_task",
            timeout_seconds=30
        )
        
        execution = await task_executor.execute_task(
            task_def, mock_extension, TaskTriggerType.MANUAL
        )
        
        assert execution.status == TaskStatus.COMPLETED
        assert execution.task_name == "test_task"
        assert execution.extension_name == "test-extension"
        assert execution.result is not None
        assert execution.error is None
        assert execution.started_at is not None
        assert execution.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_execute_failing_task(self, task_executor, mock_extension):
        """Test executing a task that fails."""
        task_def = TaskDefinition(
            name="failing_task",
            extension_name="test-extension",
            function_path="failing_task",
            timeout_seconds=30
        )
        
        execution = await task_executor.execute_task(
            task_def, mock_extension, TaskTriggerType.MANUAL
        )
        
        assert execution.status == TaskStatus.FAILED
        assert execution.error is not None
        assert "Task failed intentionally" in execution.error
        assert execution.traceback is not None
    
    @pytest.mark.asyncio
    async def test_execute_sync_task(self, task_executor, mock_extension):
        """Test executing a synchronous task."""
        task_def = TaskDefinition(
            name="sync_task",
            extension_name="test-extension",
            function_path="sync_task",
            timeout_seconds=30
        )
        
        execution = await task_executor.execute_task(
            task_def, mock_extension, TaskTriggerType.MANUAL
        )
        
        assert execution.status == TaskStatus.COMPLETED
        assert execution.result is not None
        assert "Sync task executed" in execution.result["message"]
    
    @pytest.mark.asyncio
    async def test_task_timeout(self, task_executor, mock_extension):
        """Test task timeout handling."""
        # Mock a long-running task
        async def long_task(execution_id: str, task_name: str, extension_name: str, **kwargs):
            await asyncio.sleep(10)  # Sleep longer than timeout
            return "Should not reach here"
        
        mock_extension.long_task = long_task
        
        task_def = TaskDefinition(
            name="long_task",
            extension_name="test-extension",
            function_path="long_task",
            timeout_seconds=1  # Very short timeout
        )
        
        execution = await task_executor.execute_task(
            task_def, mock_extension, TaskTriggerType.MANUAL
        )
        
        assert execution.status == TaskStatus.FAILED
        assert "timed out" in execution.error.lower()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_executor):
        """Test cancelling a running task."""
        execution_id = "test-execution"
        
        # Mock a running task
        mock_task = AsyncMock()
        task_executor.active_executions[execution_id] = mock_task
        
        success = await task_executor.cancel_task(execution_id)
        
        assert success
        assert execution_id not in task_executor.active_executions
        mock_task.cancel.assert_called_once()


class TestTaskScheduler:
    """Test the task scheduler."""
    
    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self, task_scheduler):
        """Test starting and stopping the scheduler."""
        assert not task_scheduler.running
        
        await task_scheduler.start()
        assert task_scheduler.running
        assert task_scheduler.scheduler_task is not None
        
        await task_scheduler.stop()
        assert not task_scheduler.running
        assert task_scheduler.scheduler_task is None
    
    def test_add_remove_scheduled_task(self, task_scheduler):
        """Test adding and removing scheduled tasks."""
        task_def = TaskDefinition(
            name="test_task",
            extension_name="test-extension",
            function_path="test_task",
            schedule="0 * * * *",
            trigger_type=TaskTriggerType.CRON
        )
        
        # Add task
        task_scheduler.add_scheduled_task(task_def)
        assert len(task_scheduler.scheduled_tasks) == 1
        
        # Remove task
        task_scheduler.remove_scheduled_task("test-extension", "test_task")
        assert len(task_scheduler.scheduled_tasks) == 0
    
    def test_should_run_cron_task(self, task_scheduler):
        """Test cron schedule evaluation."""
        task_def = TaskDefinition(
            name="test_task",
            extension_name="test-extension",
            function_path="test_task",
            schedule="* * * * *",  # Every minute
            trigger_type=TaskTriggerType.CRON
        )
        
        current_time = datetime.now(timezone.utc)
        
        # This is a simplified test - in practice, cron evaluation is complex
        should_run = task_scheduler._should_run_cron_task(task_def, current_time)
        assert isinstance(should_run, bool)


class TestEventManager:
    """Test the event manager."""
    
    def test_register_unregister_event_trigger(self, event_manager):
        """Test registering and unregistering event triggers."""
        trigger = EventTrigger(
            event_type="test_event",
            task_name="test_task",
            extension_name="test-extension"
        )
        
        # Register trigger
        event_manager.register_event_trigger(trigger)
        assert "test_event" in event_manager.event_triggers
        assert len(event_manager.event_triggers["test_event"]) == 1
        
        # Unregister trigger
        event_manager.unregister_event_trigger("test_event", "test_task", "test-extension")
        assert len(event_manager.event_triggers["test_event"]) == 0
    
    @pytest.mark.asyncio
    async def test_emit_event(self, event_manager):
        """Test emitting events."""
        trigger = EventTrigger(
            event_type="test_event",
            task_name="test_task",
            extension_name="test-extension",
            enabled=True
        )
        
        event_manager.register_event_trigger(trigger)
        
        # Emit event
        triggered_tasks = await event_manager.emit_event(
            "test_event", 
            {"data": "test"}
        )
        
        assert len(triggered_tasks) == 1
        assert "test-extension.test_task" in triggered_tasks
    
    def test_matches_filter(self, event_manager):
        """Test event filter matching."""
        # No filter - should match
        assert event_manager._matches_filter({"key": "value"}, {})
        
        # Matching filter
        assert event_manager._matches_filter(
            {"key": "value", "other": "data"}, 
            {"key": "value"}
        )
        
        # Non-matching filter
        assert not event_manager._matches_filter(
            {"key": "different"}, 
            {"key": "value"}
        )
        
        # Missing key
        assert not event_manager._matches_filter(
            {"other": "data"}, 
            {"key": "value"}
        )


class TestBackgroundTaskManager:
    """Test the background task manager."""
    
    @pytest.mark.asyncio
    async def test_initialize_shutdown(self, background_task_manager):
        """Test initializing and shutting down the manager."""
        await background_task_manager.initialize()
        assert background_task_manager.running
        assert background_task_manager.task_scheduler.running
        
        await background_task_manager.shutdown()
        assert not background_task_manager.running
        assert not background_task_manager.task_scheduler.running
    
    def test_register_extension_tasks(self, background_task_manager, mock_extension):
        """Test registering extension tasks."""
        # Create extension record
        record = ExtensionRecord(
            manifest=mock_extension.manifest,
            instance=mock_extension
        )
        
        # Register tasks
        background_task_manager.register_extension_tasks(record)
        
        # Check that tasks were registered
        tasks = background_task_manager.get_task_definitions()
        assert len(tasks) > 0
        
        # Check specific task
        task_def = background_task_manager.get_task_definition("test-extension", "test_task")
        assert task_def is not None
        assert task_def.name == "test_task"
        assert task_def.extension_name == "test-extension"
    
    def test_unregister_extension_tasks(self, background_task_manager, mock_extension):
        """Test unregistering extension tasks."""
        # Create and register extension
        record = ExtensionRecord(
            manifest=mock_extension.manifest,
            instance=mock_extension
        )
        background_task_manager.register_extension_tasks(record)
        
        # Verify tasks are registered
        assert len(background_task_manager.get_task_definitions()) > 0
        
        # Unregister tasks
        background_task_manager.unregister_extension_tasks("test-extension")
        
        # Verify tasks are removed
        remaining_tasks = [
            task for task in background_task_manager.get_task_definitions()
            if task.extension_name == "test-extension"
        ]
        assert len(remaining_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_execute_task_manually(self, background_task_manager, mock_extension):
        """Test manual task execution."""
        # Initialize manager
        await background_task_manager.initialize()
        
        # Mock extension manager
        mock_extension_manager = Mock()
        mock_extension_record = ExtensionRecord(
            manifest=mock_extension.manifest,
            instance=mock_extension
        )
        mock_extension_manager.get_extension_by_name.return_value = mock_extension_record
        background_task_manager.extension_manager = mock_extension_manager
        
        # Register extension tasks
        background_task_manager.register_extension_tasks(mock_extension_record)
        
        # Execute task manually
        execution = await background_task_manager.execute_task_manually(
            "test-extension", "test_task"
        )
        
        assert execution.status == TaskStatus.COMPLETED
        assert execution.task_name == "test_task"
        assert execution.extension_name == "test-extension"
        
        # Check execution history
        history = background_task_manager.get_execution_history()
        assert len(history) == 1
        assert history[0].id == execution.id
        
        await background_task_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_emit_event(self, background_task_manager):
        """Test event emission."""
        await background_task_manager.initialize()
        
        # Register event trigger
        background_task_manager.register_event_trigger(
            "test_event", "test-extension", "test_task"
        )
        
        # Emit event
        triggered_tasks = await background_task_manager.emit_event(
            "test_event", {"data": "test"}
        )
        
        assert len(triggered_tasks) == 1
        assert "test-extension.test_task" in triggered_tasks
        
        await background_task_manager.shutdown()
    
    def test_get_manager_stats(self, background_task_manager, mock_extension):
        """Test getting manager statistics."""
        # Register extension tasks
        record = ExtensionRecord(
            manifest=mock_extension.manifest,
            instance=mock_extension
        )
        background_task_manager.register_extension_tasks(record)
        
        # Get stats
        stats = background_task_manager.get_manager_stats()
        
        assert "running" in stats
        assert "registered_tasks" in stats
        assert "scheduled_tasks" in stats
        assert "active_executions" in stats
        assert "total_executions" in stats
        assert "event_triggers" in stats
        
        assert stats["registered_tasks"] > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, background_task_manager):
        """Test health check."""
        await background_task_manager.initialize()
        
        health = await background_task_manager.health_check()
        
        assert "status" in health
        assert health["status"] == "healthy"
        assert "registered_tasks" in health
        assert "scheduler_running" in health
        assert health["scheduler_running"] is True
        
        await background_task_manager.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])