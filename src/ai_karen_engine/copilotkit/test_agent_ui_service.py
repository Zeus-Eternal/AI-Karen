"""
Unit tests for Agent UI Service.

This module provides comprehensive tests for the Agent UI Service
that bridges CoPilot UI with the agent architecture.
"""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from .agent_ui_service import AgentUIService
from .models import (
    AgentTask,
    SendMessageRequest,
    SendMessageResponse,
    CreateDeepTaskRequest,
    CreateDeepTaskResponse,
    GetTaskProgressRequest,
    GetTaskProgressResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    ExecutionMode,
    TaskType,
    TaskStatus,
    TaskStep
)
from .thread_manager import ThreadManager
from .session_state_manager import SessionStateManager
from .safety_middleware import CopilotSafetyMiddleware


class TestAgentUIService(unittest.TestCase):
    """Test cases for AgentUIService."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock dependencies
        self.mock_agent_orchestrator = AsyncMock()
        self.mock_thread_manager = AsyncMock(spec=ThreadManager)
        self.mock_session_manager = AsyncMock(spec=SessionStateManager)
        
        # Create service instance
        self.agent_ui_service = AgentUIService(
            agent_orchestrator=self.mock_agent_orchestrator,
            thread_manager=self.mock_thread_manager,
            session_manager=self.mock_session_manager
        )
        
        # Set up mock return values
        self.mock_thread_manager.create_thread.return_value = "test_thread_123"
        self.mock_session_manager.load_session_state.return_value = None
        self.mock_session_manager.save_session_state.return_value = True
    
    async def test_send_message_success(self):
        """Test successful message sending."""
        # Create request
        request = SendMessageRequest(
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="Hello, agent!",
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.send_message(request)
        
        # Verify response
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Native execution completed for: Hello, agent!...")
        self.assertEqual(response.execution_mode, ExecutionMode.NATIVE)
        self.assertIsNotNone(response.task_id)
        
        # Verify task creation
        self.mock_thread_manager.get_langgraph_thread.assert_called_once_with("test_session")
    
    async def test_send_message_with_explicit_execution_mode(self):
        """Test message sending with explicit execution mode."""
        # Create request with explicit mode
        request = SendMessageRequest(
            session_id="test_session",
            task_type=TaskType.CODE_GENERATION,
            content="Generate a function",
            execution_mode=ExecutionMode.LANGGRAPH,
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.send_message(request)
        
        # Verify response
        self.assertTrue(response.success)
        self.assertEqual(response.execution_mode, ExecutionMode.LANGGRAPH)
        self.assertIn("workflow_steps", response.execution_metadata)
    
    async def test_send_message_validation_error(self):
        """Test message sending with validation error."""
        # Create invalid request
        request = SendMessageRequest(
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="",  # Empty content should fail validation
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.send_message(request)
        
        # Verify error response
        self.assertFalse(response.success)
        self.assertIn("Error processing message", response.content)
    
    async def test_create_deep_task_success(self):
        """Test successful deep task creation."""
        # Create request
        request = CreateDeepTaskRequest(
            session_id="test_session",
            task_type=TaskType.CODE_AUDIT,
            content="Audit this code repository",
            priority=3,
            timeout_seconds=300,
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.create_deep_task(request)
        
        # Verify response
        self.assertTrue(response.success)
        self.assertEqual(response.status, TaskStatus.PENDING)
        self.assertIsNotNone(response.task_id)
        self.assertEqual(response.execution_metadata["mode"], "deepagent")
        self.assertIsNotNone(response.estimated_duration)
        
        # Verify thread creation
        self.mock_thread_manager.create_thread.assert_called_once_with("test_session")
    
    async def test_create_deep_task_validation_error(self):
        """Test deep task creation with validation error."""
        # Create invalid request
        request = CreateDeepTaskRequest(
            session_id="test_session",
            task_type=TaskType.CODE_AUDIT,
            content="",  # Empty content should fail validation
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.create_deep_task(request)
        
        # Verify error response
        self.assertFalse(response.success)
        self.assertEqual(response.status, TaskStatus.FAILED)
    
    async def test_get_task_progress_success(self):
        """Test successful task progress retrieval."""
        # Set up mock task
        task_id = "test_task_123"
        expected_progress = GetTaskProgressResponse(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            progress_percentage=50.0,
            steps=[
                TaskStep(
                    step_id="step_1",
                    name="Analysis",
                    status=TaskStatus.COMPLETED
                )
            ]
        )
        
        # Mock the task progress
        self.agent_ui_service._task_progress[task_id] = expected_progress
        
        # Create request
        request = GetTaskProgressRequest(
            session_id="test_session",
            task_id=task_id,
            include_steps=True,
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.get_task_progress(request)
        
        # Verify response
        self.assertEqual(response.task_id, task_id)
        self.assertEqual(response.status, TaskStatus.RUNNING)
        self.assertEqual(response.progress_percentage, 50.0)
        self.assertIsNotNone(response.steps)
        self.assertEqual(len(response.steps), 1)
    
    async def test_get_task_progress_not_found(self):
        """Test task progress retrieval for non-existent task."""
        # Create request for non-existent task
        request = GetTaskProgressRequest(
            session_id="test_session",
            task_id="non_existent_task",
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.get_task_progress(request)
        
        # Verify error response
        self.assertEqual(response.task_id, "non_existent_task")
        self.assertEqual(response.status, TaskStatus.FAILED)
        self.assertIsNotNone(response.error_message)
    
    async def test_cancel_task_success(self):
        """Test successful task cancellation."""
        # Set up running task
        task_id = "test_task_123"
        self.agent_ui_service._running_tasks[task_id] = asyncio.create_task(asyncio.sleep(1))
        
        # Create request
        request = CancelTaskRequest(
            session_id="test_session",
            task_id=task_id,
            reason="User requested cancellation",
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.cancel_task(request)
        
        # Verify response
        self.assertTrue(response.success)
        self.assertEqual(response.task_id, task_id)
        self.assertEqual(response.status, TaskStatus.CANCELLED)
        self.assertIn("cancelled successfully", response.message)
        
        # Verify task is no longer running
        self.assertNotIn(task_id, self.agent_ui_service._running_tasks)
    
    async def test_cancel_task_not_found(self):
        """Test task cancellation for non-existent task."""
        # Create request for non-existent task
        request = CancelTaskRequest(
            session_id="test_session",
            task_id="non_existent_task",
            user_id="test_user"
        )
        
        # Call service
        response = await self.agent_ui_service.cancel_task(request)
        
        # Verify error response
        self.assertFalse(response.success)
        self.assertEqual(response.task_id, "non_existent_task")
        self.assertIn("not found", response.message)
    
    async def test_execution_mode_determination(self):
        """Test automatic execution mode determination."""
        # Test conversation task
        conv_task = AgentTask(
            task_id="conv_task",
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="Simple conversation",
            execution_mode=ExecutionMode.AUTO
        )
        
        mode = await self.agent_ui_service._determine_execution_mode(conv_task)
        self.assertEqual(mode, ExecutionMode.NATIVE)
        
        # Test code generation task
        code_task = AgentTask(
            task_id="code_task",
            session_id="test_session",
            task_type=TaskType.CODE_GENERATION,
            content="Generate simple function",
            execution_mode=ExecutionMode.AUTO
        )
        
        mode = await self.agent_ui_service._determine_execution_mode(code_task)
        self.assertEqual(mode, ExecutionMode.NATIVE)
        
        # Test complex code task
        complex_task = AgentTask(
            task_id="complex_task",
            session_id="test_session",
            task_type=TaskType.CODE_GENERATION,
            content="Generate complex system with multiple modules and dependencies",
            context={"files": ["file1.py", "file2.py"], "requirements": ["req1", "req2"]},
            execution_mode=ExecutionMode.AUTO
        )
        
        mode = await self.agent_ui_service._determine_execution_mode(complex_task)
        self.assertEqual(mode, ExecutionMode.LANGGRAPH)
        
        # Test code refactor task
        refactor_task = AgentTask(
            task_id="refactor_task",
            session_id="test_session",
            task_type=TaskType.CODE_REFACTOR,
            content="Refactor authentication system",
            execution_mode=ExecutionMode.AUTO
        )
        
        mode = await self.agent_ui_service._determine_execution_mode(refactor_task)
        self.assertEqual(mode, ExecutionMode.DEEPAGENT)
    
    async def test_task_duration_estimation(self):
        """Test task duration estimation."""
        # Test simple task
        simple_task = AgentTask(
            task_id="simple_task",
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="Hello",
            execution_mode=ExecutionMode.AUTO
        )
        
        duration = self.agent_ui_service._estimate_task_duration(simple_task)
        self.assertGreater(duration, 0)
        self.assertLessEqual(duration, 120)  # Should be less than 2 minutes
        
        # Test complex task
        complex_task = AgentTask(
            task_id="complex_task",
            session_id="test_session",
            task_type=TaskType.CODE_REFACTOR,
            content="Refactor entire system",
            context={"files": 100},  # Large context
            execution_mode=ExecutionMode.AUTO
        )
        
        duration = self.agent_ui_service._estimate_task_duration(complex_task)
        self.assertGreater(duration, 60)  # Should be more than 1 minute
        self.assertLessEqual(duration, 600)  # Should be less than 10 minutes
    
    async def test_get_active_tasks(self):
        """Test retrieval of active tasks."""
        # Set up tasks
        active_task = AgentTask(
            task_id="active_task",
            session_id="test_session",
            task_type=TaskType.CODE_GENERATION,
            content="Active task",
            execution_mode=ExecutionMode.AUTO
        )
        active_task.status = TaskStatus.RUNNING
        
        completed_task = AgentTask(
            task_id="completed_task",
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="Completed task",
            execution_mode=ExecutionMode.AUTO
        )
        completed_task.status = TaskStatus.COMPLETED
        
        self.agent_ui_service._tasks["active_task"] = active_task
        self.agent_ui_service._tasks["completed_task"] = completed_task
        
        # Get active tasks
        active_tasks = self.agent_ui_service.get_active_tasks()
        
        # Verify results
        self.assertEqual(len(active_tasks), 1)
        self.assertEqual(active_tasks[0]["task_id"], "active_task")
        self.assertEqual(active_tasks[0]["status"], TaskStatus.RUNNING)
    
    async def test_get_task_history(self):
        """Test retrieval of task history."""
        # Set up tasks
        task1 = AgentTask(
            task_id="task1",
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="First task",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        task2 = AgentTask(
            task_id="task2",
            session_id="test_session",
            task_type=TaskType.CODE_GENERATION,
            content="Second task",
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        self.agent_ui_service._tasks["task1"] = task1
        self.agent_ui_service._tasks["task2"] = task2
        
        # Get history
        history = self.agent_ui_service.get_task_history(limit=10)
        
        # Verify results
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["task_id"], "task2")  # Newest first
        self.assertEqual(history[1]["task_id"], "task1")
        self.assertEqual(history[0]["task_type"], TaskType.CODE_GENERATION)
        self.assertEqual(history[1]["task_type"], TaskType.CONVERSATION)


class TestThreadManager(unittest.IsolatedAsyncTestCase):
    """Test cases for ThreadManager."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        self.thread_manager = ThreadManager()
    
    async def test_create_thread(self):
        """Test thread creation."""
        # Create thread
        session_id = "test_session"
        thread_id = await self.thread_manager.create_thread(session_id)
        
        # Verify thread ID format
        self.assertTrue(thread_id.startswith("langgraph_test_session_"))
        
        # Verify bidirectional mapping
        retrieved_session = await self.thread_manager.get_copilot_session(thread_id)
        self.assertEqual(retrieved_session, session_id)
        
        retrieved_thread = await self.thread_manager.get_langgraph_thread(session_id)
        self.assertEqual(retrieved_thread, thread_id)
    
    async def test_thread_metadata(self):
        """Test thread metadata operations."""
        session_id = "test_session"
        thread_id = await self.thread_manager.create_thread(session_id)
        
        # Get initial metadata
        metadata = await self.thread_manager.get_thread_metadata(thread_id)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["copilot_session_id"], session_id)
        self.assertIn("created_at", metadata)
        self.assertIn("message_count", metadata)
        self.assertEqual(metadata["message_count"], 0)
        
        # Update metadata
        update_success = await self.thread_manager.update_thread_metadata(
            thread_id,
            custom_field="test_value"
        )
        self.assertTrue(update_success)
        
        # Verify update
        updated_metadata = await self.thread_manager.get_thread_metadata(thread_id)
        self.assertEqual(updated_metadata["custom_field"], "test_value")
    
    async def test_increment_message_count(self):
        """Test message count increment."""
        session_id = "test_session"
        thread_id = await self.thread_manager.create_thread(session_id)
        
        # Increment count
        increment_success = await self.thread_manager.increment_message_count(thread_id)
        self.assertTrue(increment_success)
        
        # Verify increment
        metadata = await self.thread_manager.get_thread_metadata(thread_id)
        self.assertEqual(metadata["message_count"], 1)
    
    async def test_delete_thread(self):
        """Test thread deletion."""
        session_id = "test_session"
        thread_id = await self.thread_manager.create_thread(session_id)
        
        # Delete thread
        delete_success = await self.thread_manager.delete_thread(thread_id)
        self.assertTrue(delete_success)
        
        # Verify deletion
        retrieved_session = await self.thread_manager.get_langgraph_thread(session_id)
        self.assertIsNone(retrieved_session)
        
        retrieved_thread = await self.thread_manager.get_copilot_session(thread_id)
        self.assertIsNone(retrieved_thread)


class TestSessionStateManager(unittest.IsolatedAsyncTestCase):
    """Test cases for SessionStateManager."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        self.session_manager = SessionStateManager()
    
    async def test_save_and_load_session_state(self):
        """Test saving and loading session state."""
        session_id = "test_session"
        state = {
            "user_preferences": {"theme": "dark", "language": "en"},
            "active_tasks": ["task1", "task2"],
            "conversation_context": {"last_topic": "testing"}
        }
        
        # Save state
        save_success = await self.session_manager.save_session_state(session_id, state)
        self.assertTrue(save_success)
        
        # Load state
        loaded_state = await self.session_manager.load_session_state(session_id)
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state["user_preferences"]["theme"], "dark")
        self.assertEqual(loaded_state["active_tasks"], ["task1", "task2"])
    
    async def test_update_session_state(self):
        """Test updating session state."""
        session_id = "test_session"
        initial_state = {
            "user_preferences": {"theme": "light"},
            "active_tasks": []
        }
        
        # Save initial state
        await self.session_manager.save_session_state(session_id, initial_state)
        
        # Update specific field
        update_success = await self.session_manager.set_session_state_field(
            session_id,
            "user_preferences.theme",
            "dark"
        )
        self.assertTrue(update_success)
        
        # Verify update
        updated_state = await self.session_manager.load_session_state(session_id)
        self.assertEqual(updated_state["user_preferences"]["theme"], "dark")
        # Other fields should remain unchanged
        self.assertEqual(updated_state["active_tasks"], [])
    
    async def test_delete_session_state(self):
        """Test deleting session state."""
        session_id = "test_session"
        state = {"test": "data"}
        
        # Save state
        await self.session_manager.save_session_state(session_id, state)
        
        # Delete state
        delete_success = await self.session_manager.delete_session_state(session_id)
        self.assertTrue(delete_success)
        
        # Verify deletion
        loaded_state = await self.session_manager.load_session_state(session_id)
        self.assertIsNone(loaded_state)
    
    async def test_get_session_state_field(self):
        """Test getting specific field from session state."""
        session_id = "test_session"
        state = {
            "user": {"name": "test", "preferences": {"theme": "dark"}},
            "settings": {"notifications": True}
        }
        
        # Save state
        await self.session_manager.save_session_state(session_id, state)
        
        # Get nested field
        user_name = await self.session_manager.get_session_state_field(session_id, "user.name")
        self.assertEqual(user_name, "test")
        
        # Get another nested field
        notifications = await self.session_manager.get_session_state_field(session_id, "settings.notifications")
        self.assertTrue(notifications)
        
        # Get non-existent field
        non_existent = await self.session_manager.get_session_state_field(session_id, "non.existent.field")
        self.assertIsNone(non_existent)


class TestCopilotSafetyMiddleware(unittest.IsolatedAsyncTestCase):
    """Test cases for CopilotSafetyMiddleware."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        self.safety_middleware = CopilotSafetyMiddleware()
    
    async def test_content_safety_valid_content(self):
        """Test content safety check with valid content."""
        request = AgentTask(
            task_id="safe_task",
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="Hello, how are you today?",
            execution_mode=ExecutionMode.AUTO
        )
        
        # Validate request
        result = await self.safety_middleware.validate_request(request)
        
        # Verify result
        self.assertTrue(result.is_safe)
        self.assertLess(result.overall_risk_score, 3.0)
        self.assertTrue(result.can_proceed)
        self.assertFalse(result.requires_moderation)
    
    async def test_content_safety_blocked_content(self):
        """Test content safety check with blocked content."""
        request = AgentTask(
            task_id="unsafe_task",
            session_id="test_session",
            task_type=TaskType.CONVERSATION,
            content="I want to harm someone with violence",
            execution_mode=ExecutionMode.AUTO
        )
        
        # Validate request
        result = await self.safety_middleware.validate_request(request)
        
        # Verify result
        self.assertFalse(result.is_safe)
        self.assertGreaterEqual(result.overall_risk_score, 5.0)
        self.assertFalse(result.can_proceed)
        self.assertTrue(result.requires_moderation)
        self.assertIsNotNone(result.safety_check)
        self.assertGreater(len(result.safety_check.blocked_content), 0)
    
    async def test_authorization_success(self):
        """Test authorization check with sufficient permissions."""
        request = AgentTask(
            task_id="auth_task",
            session_id="test_session",
            task_type=TaskType.CODE_GENERATION,
            content="Generate code",
            execution_mode=ExecutionMode.AUTO,
            context={
                "user_permissions": ["read", "write"],
                "user_roles": ["developer"]
            }
        )
        
        # Validate request
        result = await self.safety_middleware.validate_request(request)
        
        # Verify result
        self.assertTrue(result.authorization_check.authorized)
        self.assertIn("write", result.authorization_check.granted_permissions)
        self.assertEqual(len(result.authorization_check.denied_permissions), 0)
    
    async def test_authorization_insufficient_permissions(self):
        """Test authorization check with insufficient permissions."""
        request = AgentTask(
            task_id="admin_task",
            session_id="test_session",
            task_type=TaskType.CODE_REFACTOR,
            content="Refactor system",
            execution_mode=ExecutionMode.AUTO,
            context={
                "user_permissions": ["read"],  # Missing write permission
                "user_roles": ["user"]  # Not admin or developer
            }
        )
        
        # Validate request
        result = await self.safety_middleware.validate_request(request)
        
        # Verify result
        self.assertFalse(result.authorization_check.authorized)
        self.assertNotIn("code_execute", result.authorization_check.granted_permissions)
        self.assertIn("code_execute", result.authorization_check.denied_permissions)
        self.assertIsNotNone(result.authorization_check.reason)
    
    async def test_validation_statistics(self):
        """Test validation statistics tracking."""
        # Reset statistics
        self.safety_middleware.reset_statistics()
        
        # Make several requests
        requests = [
            AgentTask(task_id=f"task_{i}", session_id="test", content="Safe content {i}")
            for i in range(5)
        ]
        
        # Process requests
        for request in requests:
            await self.safety_middleware.validate_request(request)
        
        # Make a blocked request
        blocked_request = AgentTask(
            task_id="blocked_task",
            session_id="test",
            content="Blocked content with violence"
        )
        await self.safety_middleware.validate_request(blocked_request)
        
        # Get statistics
        stats = self.safety_middleware.get_validation_statistics()
        
        # Verify statistics
        self.assertEqual(stats["total_requests"], 6)
        self.assertEqual(stats["allowed_requests"], 5)
        self.assertEqual(stats["blocked_requests"], 1)
        self.assertGreater(stats["allowed_percentage"], 80)
        self.assertLess(stats["blocked_percentage"], 20)


if __name__ == "__main__":
    unittest.main()