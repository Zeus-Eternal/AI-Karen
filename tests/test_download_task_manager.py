"""
Tests for Download Task Manager

Tests the comprehensive download task management functionality including:
- Task creation and lifecycle management
- Progress tracking and callbacks
- Disk space validation
- Task persistence and recovery
"""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.ai_karen_engine.services.download_task_manager import (
    DownloadTaskManager, DownloadTask, TaskStatus, TaskPriority
)

class TestDownloadTask(unittest.TestCase):
    """Test DownloadTask class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.task = DownloadTask(
            task_id="test-task-1",
            model_id="test-model",
            url="https://example.com/model.bin",
            filename="model.bin",
            destination_path="/tmp/model.bin"
        )
    
    def test_task_creation(self):
        """Test basic task creation."""
        self.assertEqual(self.task.task_id, "test-task-1")
        self.assertEqual(self.task.model_id, "test-model")
        self.assertEqual(self.task.status, TaskStatus.PENDING)
        self.assertEqual(self.task.priority, TaskPriority.NORMAL)
        self.assertEqual(self.task.progress, 0.0)
        self.assertEqual(self.task.retry_count, 0)
    
    def test_progress_update(self):
        """Test progress update functionality."""
        self.task.update_progress(500, 1000)
        
        self.assertEqual(self.task.downloaded_size, 500)
        self.assertEqual(self.task.total_size, 1000)
        self.assertEqual(self.task.progress, 50.0)
    
    def test_status_update(self):
        """Test status update functionality."""
        self.task.set_status(TaskStatus.DOWNLOADING)
        self.assertEqual(self.task.status, TaskStatus.DOWNLOADING)
        self.assertIsNotNone(self.task.started_at)
        
        self.task.set_status(TaskStatus.COMPLETED)
        self.assertEqual(self.task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(self.task.completed_at)
    
    def test_callbacks(self):
        """Test callback functionality."""
        progress_callback = Mock()
        completion_callback = Mock()
        
        self.task.add_progress_callback(progress_callback)
        self.task.add_completion_callback(completion_callback)
        
        self.task.notify_progress()
        progress_callback.assert_called_once_with(self.task)
        
        self.task.notify_completion()
        completion_callback.assert_called_once_with(self.task)
    
    def test_serialization(self):
        """Test task serialization and deserialization."""
        # Update some fields
        self.task.update_progress(250, 1000)
        self.task.set_status(TaskStatus.DOWNLOADING)
        
        # Serialize
        data = self.task.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['task_id'], "test-task-1")
        self.assertEqual(data['status'], TaskStatus.DOWNLOADING.value)
        
        # Deserialize
        restored_task = DownloadTask.from_dict(data)
        self.assertEqual(restored_task.task_id, self.task.task_id)
        self.assertEqual(restored_task.status, self.task.status)
        self.assertEqual(restored_task.progress, self.task.progress)
    
    def test_eta_formatting(self):
        """Test ETA formatting."""
        self.task.estimated_time_remaining = 30
        self.assertEqual(self.task.get_eta_formatted(), "30s")
        
        self.task.estimated_time_remaining = 90
        self.assertEqual(self.task.get_eta_formatted(), "1m 30s")
        
        self.task.estimated_time_remaining = 3661
        self.assertEqual(self.task.get_eta_formatted(), "1h 1m")
    
    def test_speed_formatting(self):
        """Test speed formatting."""
        self.task.download_speed = 500
        self.assertEqual(self.task.get_speed_formatted(), "500.0 B/s")
        
        self.task.download_speed = 1536
        self.assertEqual(self.task.get_speed_formatted(), "1.5 KB/s")
        
        self.task.download_speed = 2097152
        self.assertEqual(self.task.get_speed_formatted(), "2.0 MB/s")

class TestDownloadTaskManager(unittest.TestCase):
    """Test DownloadTaskManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DownloadTaskManager(
            storage_dir=self.temp_dir,
            persistence_file="test_tasks.json"
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.head')
    def test_task_creation(self, mock_head):
        """Test task creation."""
        # Mock successful HEAD request
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1000'}
        mock_head.return_value = mock_response
        
        task = self.manager.create_task(
            model_id="test-model",
            url="https://example.com/model.bin",
            filename="model.bin"
        )
        
        self.assertIsNotNone(task.task_id)
        self.assertEqual(task.model_id, "test-model")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIn(task.task_id, self.manager.tasks)
        self.assertIn(task.task_id, self.manager.task_queue)
    
    def test_task_retrieval(self):
        """Test task retrieval methods."""
        # Create test tasks
        task1 = DownloadTask(
            task_id="task-1",
            model_id="model-1",
            url="https://example.com/model1.bin",
            filename="model1.bin",
            destination_path="/tmp/model1.bin"
        )
        task1.set_status(TaskStatus.DOWNLOADING)
        
        task2 = DownloadTask(
            task_id="task-2",
            model_id="model-1",
            url="https://example.com/model2.bin",
            filename="model2.bin",
            destination_path="/tmp/model2.bin"
        )
        task2.set_status(TaskStatus.COMPLETED)
        
        self.manager.tasks["task-1"] = task1
        self.manager.tasks["task-2"] = task2
        
        # Test get_task
        retrieved_task = self.manager.get_task("task-1")
        self.assertEqual(retrieved_task.task_id, "task-1")
        
        # Test get_tasks_by_model
        model_tasks = self.manager.get_tasks_by_model("model-1")
        self.assertEqual(len(model_tasks), 2)
        
        # Test get_tasks_by_status
        downloading_tasks = self.manager.get_tasks_by_status(TaskStatus.DOWNLOADING)
        self.assertEqual(len(downloading_tasks), 1)
        self.assertEqual(downloading_tasks[0].task_id, "task-1")
        
        completed_tasks = self.manager.get_tasks_by_status(TaskStatus.COMPLETED)
        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(completed_tasks[0].task_id, "task-2")
    
    def test_task_status_updates(self):
        """Test task status update functionality."""
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.bin",
            filename="model.bin",
            destination_path="/tmp/model.bin"
        )
        
        self.manager.tasks["test-task"] = task
        self.manager.task_queue.append("test-task")
        
        # Update status
        self.manager.update_task_status("test-task", TaskStatus.DOWNLOADING)
        self.assertEqual(task.status, TaskStatus.DOWNLOADING)
        
        # Complete task
        self.manager.update_task_status("test-task", TaskStatus.COMPLETED)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertNotIn("test-task", self.manager.task_queue)
    
    def test_task_progress_updates(self):
        """Test task progress update functionality."""
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.bin",
            filename="model.bin",
            destination_path="/tmp/model.bin"
        )
        
        progress_callback = Mock()
        task.add_progress_callback(progress_callback)
        
        self.manager.tasks["test-task"] = task
        
        # Update progress
        self.manager.update_task_progress("test-task", 500, 1000)
        
        self.assertEqual(task.downloaded_size, 500)
        self.assertEqual(task.total_size, 1000)
        self.assertEqual(task.progress, 50.0)
        progress_callback.assert_called_once_with(task)
    
    def test_task_cancellation(self):
        """Test task cancellation."""
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.bin",
            filename="model.bin",
            destination_path="/tmp/model.bin"
        )
        task.set_status(TaskStatus.DOWNLOADING)
        
        self.manager.tasks["test-task"] = task
        self.manager.task_queue.append("test-task")
        
        # Cancel task
        result = self.manager.cancel_task("test-task")
        
        self.assertTrue(result)
        self.assertEqual(task.status, TaskStatus.CANCELLED)
        self.assertNotIn("test-task", self.manager.task_queue)
    
    def test_task_retry(self):
        """Test task retry functionality."""
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.bin",
            filename="model.bin",
            destination_path="/tmp/model.bin"
        )
        task.set_status(TaskStatus.FAILED)
        task.error_message = "Network error"
        
        self.manager.tasks["test-task"] = task
        
        # Retry task
        result = self.manager.retry_task("test-task")
        
        self.assertTrue(result)
        self.assertEqual(task.status, TaskStatus.QUEUED)
        self.assertEqual(task.retry_count, 1)
        self.assertIsNone(task.error_message)
        self.assertIn("test-task", self.manager.task_queue)
    
    @patch('shutil.disk_usage')
    def test_disk_space_validation(self, mock_disk_usage):
        """Test disk space validation."""
        # Mock disk usage - 1GB free
        mock_disk_usage.return_value = Mock(free=1024*1024*1024)
        
        # Test sufficient space
        result = self.manager.validate_disk_space(500*1024*1024)  # 500MB
        self.assertTrue(result)
        
        # Test insufficient space
        result = self.manager.validate_disk_space(2*1024*1024*1024)  # 2GB
        self.assertFalse(result)
    
    def test_queue_management(self):
        """Test task queue management with priorities."""
        # Create tasks with different priorities
        low_task = DownloadTask(
            task_id="low-task",
            model_id="model-1",
            url="https://example.com/model1.bin",
            filename="model1.bin",
            destination_path="/tmp/model1.bin",
            priority=TaskPriority.LOW
        )
        
        high_task = DownloadTask(
            task_id="high-task",
            model_id="model-2",
            url="https://example.com/model2.bin",
            filename="model2.bin",
            destination_path="/tmp/model2.bin",
            priority=TaskPriority.HIGH
        )
        
        normal_task = DownloadTask(
            task_id="normal-task",
            model_id="model-3",
            url="https://example.com/model3.bin",
            filename="model3.bin",
            destination_path="/tmp/model3.bin",
            priority=TaskPriority.NORMAL
        )
        
        # Add to manager
        self.manager.tasks["low-task"] = low_task
        self.manager.tasks["high-task"] = high_task
        self.manager.tasks["normal-task"] = normal_task
        
        # Add to queue (should be ordered by priority)
        self.manager._add_to_queue("low-task", TaskPriority.LOW)
        self.manager._add_to_queue("high-task", TaskPriority.HIGH)
        self.manager._add_to_queue("normal-task", TaskPriority.NORMAL)
        
        # High priority should be first
        next_task = self.manager.get_next_queued_task()
        self.assertEqual(next_task.task_id, "high-task")
    
    def test_statistics(self):
        """Test statistics generation."""
        # Create tasks with different statuses
        tasks_data = [
            ("task-1", TaskStatus.PENDING),
            ("task-2", TaskStatus.DOWNLOADING),
            ("task-3", TaskStatus.COMPLETED),
            ("task-4", TaskStatus.FAILED),
            ("task-5", TaskStatus.CANCELLED)
        ]
        
        for task_id, status in tasks_data:
            task = DownloadTask(
                task_id=task_id,
                model_id=f"model-{task_id}",
                url=f"https://example.com/{task_id}.bin",
                filename=f"{task_id}.bin",
                destination_path=f"/tmp/{task_id}.bin"
            )
            task.set_status(status)
            task.downloaded_size = 100
            self.manager.tasks[task_id] = task
        
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['total_tasks'], 5)
        self.assertEqual(stats['pending_tasks'], 1)
        self.assertEqual(stats['downloading_tasks'], 1)
        self.assertEqual(stats['completed_tasks'], 1)
        self.assertEqual(stats['failed_tasks'], 1)
        self.assertEqual(stats['cancelled_tasks'], 1)
        self.assertEqual(stats['total_bytes_downloaded'], 500)
    
    def test_persistence(self):
        """Test task persistence and loading."""
        # Create a task
        task = DownloadTask(
            task_id="persist-task",
            model_id="persist-model",
            url="https://example.com/model.bin",
            filename="model.bin",
            destination_path="/tmp/model.bin"
        )
        task.update_progress(500, 1000)
        
        self.manager.tasks["persist-task"] = task
        self.manager.task_queue.append("persist-task")
        
        # Persist tasks
        self.manager._persist_tasks()
        
        # Create new manager and load tasks
        new_manager = DownloadTaskManager(
            storage_dir=self.temp_dir,
            persistence_file="test_tasks.json"
        )
        
        # Verify task was loaded
        self.assertIn("persist-task", new_manager.tasks)
        loaded_task = new_manager.tasks["persist-task"]
        self.assertEqual(loaded_task.model_id, "persist-model")
        self.assertEqual(loaded_task.progress, 50.0)
        self.assertIn("persist-task", new_manager.task_queue)

if __name__ == '__main__':
    unittest.main()