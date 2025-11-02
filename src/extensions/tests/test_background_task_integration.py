"""
Integration test for background task system.

This test verifies that the background task system integrates properly
with the extension manager and can execute tasks.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.extensions.core.background_tasks import (
    BackgroundTaskManager,
    TaskDefinition,
    TaskStatus,
    TaskTriggerType
)
from src.extensions.core.models import (
    ExtensionManifest,
    ExtensionRecord,
    ExtensionCapabilities,
    ExtensionBackgroundTask,
    ExtensionContext
)
from src.extensions.core.base import BaseExtension


class TestExtension(BaseExtension):
    """Test extension for integration testing."""
    
    async def _initialize(self):
        pass
    
    async def _shutdown(self):
        pass
    
    async def test_task(self, execution_id: str, task_name: str, extension_name: str, **kwargs):
        """Test task function."""
        return {
            "message": "Task executed successfully",
            "execution_id": execution_id,
            "task_name": task_name,
            "extension_name": extension_name
        }


async def test_background_task_integration():
    """Test the background task system integration."""
    print("Starting background task integration test...")
    
    try:
        # Create test extension
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
                    schedule="0 * * * *",
                    function="test_task",
                    description="Test task",
                    enabled=True
                )
            ]
        )
        
        context = ExtensionContext(extension_name="test-extension")
        extension = TestExtension(manifest, context)
        
        # Create extension record
        record = ExtensionRecord(
            manifest=manifest,
            instance=extension
        )
        
        # Initialize background task manager
        task_manager = BackgroundTaskManager()
        await task_manager.initialize()
        
        print("✓ Background task manager initialized")
        
        # Register extension tasks
        task_manager.register_extension_tasks(record)
        
        print("✓ Extension tasks registered")
        
        # Check that tasks were registered
        tasks = task_manager.get_task_definitions()
        assert len(tasks) > 0, "No tasks were registered"
        
        print(f"✓ Found {len(tasks)} registered tasks")
        
        # Get specific task
        task_def = task_manager.get_task_definition("test-extension", "test_task")
        assert task_def is not None, "Test task not found"
        assert task_def.name == "test_task"
        assert task_def.extension_name == "test-extension"
        
        print("✓ Task definition retrieved successfully")
        
        # Test manual task execution (mock extension manager)
        class MockExtensionManager:
            def get_extension_by_name(self, name):
                if name == "test-extension":
                    return record
                return None
        
        task_manager.extension_manager = MockExtensionManager()
        
        # Execute task manually
        execution = await task_manager.execute_task_manually("test-extension", "test_task")
        
        assert execution.status == TaskStatus.COMPLETED, f"Task failed: {execution.error}"
        assert execution.task_name == "test_task"
        assert execution.extension_name == "test-extension"
        assert execution.result is not None
        
        print("✓ Task executed successfully")
        print(f"  - Execution ID: {execution.id}")
        print(f"  - Status: {execution.status.value}")
        print(f"  - Result: {execution.result}")
        
        # Check execution history
        history = task_manager.get_execution_history()
        assert len(history) == 1, "Execution not found in history"
        assert history[0].id == execution.id
        
        print("✓ Execution history recorded")
        
        # Test event emission
        triggered_tasks = await task_manager.emit_event("test_event", {"data": "test"})
        print(f"✓ Event emitted, triggered {len(triggered_tasks)} tasks")
        
        # Test manager stats
        stats = task_manager.get_manager_stats()
        assert stats["registered_tasks"] > 0
        assert stats["total_executions"] > 0
        
        print("✓ Manager stats retrieved")
        print(f"  - Registered tasks: {stats['registered_tasks']}")
        print(f"  - Total executions: {stats['total_executions']}")
        
        # Test health check
        health = await task_manager.health_check()
        assert health["status"] == "healthy"
        
        print("✓ Health check passed")
        
        # Cleanup
        task_manager.unregister_extension_tasks("test-extension")
        await task_manager.shutdown()
        
        print("✓ Background task manager shut down")
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the integration test
    result = asyncio.run(test_background_task_integration())
    sys.exit(0 if result else 1)