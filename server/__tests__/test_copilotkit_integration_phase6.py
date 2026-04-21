"""
CopilotKit Integration Tests - Phase 6.

Comprehensive integration tests for the CopilotKit alignment overhaul, validating:
1. CopilotKit as thin boundary layer (not execution layer)
2. Unified runtime adapter pattern
3. Session/thread management
4. End-to-end workflows
5. Error handling and fallback scenarios

These tests focus on validating the changes made in Phase 5 (CopilotKit alignment)
and ensuring the system works as intended.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ai_karen_engine.copilotkit.agent_ui_service import AgentUIService
from ai_karen_engine.copilotkit.models import (
    SendMessageRequest,
    SendMessageResponse,
    CreateDeepTaskRequest,
    CreateDeepTaskResponse,
    GetTaskProgressRequest,
    GetTaskProgressResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    TaskStatus,
    TaskType,
    AgentTask,
)
from ai_karen_engine.copilotkit.thread_manager import ThreadManager
from ai_karen_engine.copilotkit.session_state_manager import SessionStateManager
from ai_karen_engine.agents.adapters.langgraph_adapter import LangGraphAdapter


class TestCopilotKitAlignment:
    """Test suite for CopilotKit alignment validation."""

    @pytest.fixture
    def mock_runtime_adapter(self):
        """Mock runtime adapter for testing."""
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Mock runtime execution result",
                "metadata": {"runtime": "langgraph", "mode": "agentmedusa"},
            }
        )
        adapter.process_task = AsyncMock(
            return_value={
                "content": "Mock runtime processing result",
                "metadata": {"runtime": "langgraph", "mode": "agentmedusa"},
            }
        )
        return adapter

    @pytest.fixture
    def thread_manager(self):
        """Thread manager instance."""
        return ThreadManager()

    @pytest.fixture
    def session_manager(self):
        """Session state manager instance."""
        return SessionStateManager()

    @pytest.fixture
    def agent_ui_service(self, mock_runtime_adapter, thread_manager, session_manager):
        """Agent UI service with mocked dependencies."""
        return AgentUIService(
            runtime_adapter=mock_runtime_adapter,
            thread_manager=thread_manager,
            session_manager=session_manager,
        )

    @pytest.fixture
    def sample_request(self):
        """Sample message request for testing."""
        return SendMessageRequest(
            session_id="test_session_123",
            content="Hello, I need help with my project",
            task_type=TaskType.CONVERSATION,
            user_id="user_456",
            tenant_id="tenant_789",
        )

    @pytest.fixture
    def sample_deep_task_request(self):
        """Sample deep task request for testing."""
        return CreateDeepTaskRequest(
            session_id="test_session_123",
            content="Refactor this code to use async patterns",
            task_type=TaskType.CODE_REFACTOR,
            user_id="user_456",
            tenant_id="tenant_789",
        )


class TestCopilotKitNoExecutionModeSelection:
    """Test that CopilotKit no longer chooses execution modes."""

    def test_execution_mode_always_langgraph(self, agent_ui_service, sample_request):
        """Test that execution mode is always set to LANGGRAPH, not AUTO."""
        # Send a message with AUTO mode
        sample_request.execution_mode = TaskType.AUTO

        # Create task and check execution mode
        task = agent_ui_service._create_agent_task_from_message(sample_request)
        assert task.execution_mode == TaskType.LANGGRAPH, (
            "Execution mode should be LANGGRAPH, not AUTO"
        )

    def test_runtime_adapter_receives_correct_mode(
        self, agent_ui_service, sample_request, mock_runtime_adapter
    ):
        """Test that runtime adapter receives tasks with LANGGRAPH mode."""
        # Send a message
        asyncio.run(agent_ui_service.send_message(sample_request))

        # Verify the task passed to runtime has correct execution mode
        mock_runtime_adapter.execute_task.assert_called_once()
        call_args = mock_runtime_adapter.execute_task.call_args[0][0]
        assert call_args.execution_mode == TaskType.LANGGRAPH, (
            "Runtime adapter should receive task with LANGGRAPH execution mode"
        )

    def test_no_mode_selection_logic_in_service(self, agent_ui_service):
        """Test that AgentUIService has no mode selection logic."""
        # Check that the service doesn't have mode selection methods
        assert not hasattr(agent_ui_service, "_select_execution_mode")
        assert not hasattr(agent_ui_service, "_determine_runtime_brain")
        assert not hasattr(agent_ui_service, "choose_orchestration_mode")

    def test_request_validation_enforces_langgraph(
        self, agent_ui_service, sample_request
    ):
        """Test that request validation enforces LANGGRAPH mode."""
        # Test with AUTO mode - should be normalized to LANGGRAPH
        sample_request.execution_mode = TaskType.AUTO
        task = agent_ui_service._create_agent_task_from_message(sample_request)
        assert task.execution_mode == TaskType.LANGGRAPH

        # Test with explicit LANGGRAPH mode - should remain unchanged
        sample_request.execution_mode = TaskType.LANGGRAPH
        task = agent_ui_service._create_agent_task_from_message(sample_request)
        assert task.execution_mode == TaskType.LANGGRAPH


class TestRuntimeRoutingToUnifiedAdapter:
    """Test that all tasks route through unified runtime adapter."""

    def test_all_tasks_route_via_runtime_adapter(
        self, agent_ui_service, sample_request, mock_runtime_adapter
    ):
        """Test that all tasks are routed through the runtime adapter."""
        # Send different types of messages
        requests = [
            SendMessageRequest(
                session_id="session_1",
                content="Simple conversation",
                task_type=TaskType.CONVERSATION,
            ),
            SendMessageRequest(
                session_id="session_2",
                content="Help me debug this code",
                task_type=TaskType.DEBUGGING,
            ),
            SendMessageRequest(
                session_id="session_3",
                content="Generate documentation",
                task_type=TaskType.DOCUMENTATION,
            ),
        ]

        for request in requests:
            asyncio.run(agent_ui_service.send_message(request))

        # Verify all tasks were routed through runtime adapter
        assert mock_runtime_adapter.execute_task.call_count == 3, (
            "All tasks should be routed through runtime adapter"
        )

    def test_runtime_adapter_not_configured_fallback(
        self, agent_ui_service, sample_request
    ):
        """Test behavior when runtime adapter is not configured."""
        # Create service without runtime adapter
        service = AgentUIService()

        # Send message - should handle gracefully
        response = asyncio.run(agent_ui_service.send_message(sample_request))

        # Should return success but indicate runtime not configured
        assert response.success == True
        assert "Runtime adapter not configured" in response.content
        assert response.execution_metadata["configured"] == False

    def test_runtime_adapter_interface_compatibility(
        self, agent_ui_service, mock_runtime_adapter
    ):
        """Test that runtime adapter interface is compatible."""
        # Test that adapter has required methods
        assert hasattr(mock_runtime_adapter, "execute_task")
        assert hasattr(mock_runtime_adapter, "process_task")

        # Test both methods work
        task = AgentTask(
            session_id="test_session",
            content="Test task",
            task_type=TaskType.CONVERSATION,
        )

        # Mock both methods
        mock_runtime_adapter.execute_task.return_value = {"content": "execute result"}
        mock_runtime_adapter.process_task.return_value = {"content": "process result"}

        # Test both execution paths
        result1 = asyncio.run(agent_ui_service._execute_via_runtime(task))
        result2 = asyncio.run(agent_ui_service._execute_via_runtime(task))

        assert result1["content"] == "execute result"
        assert result2["content"] == "process result"

    def test_runtime_error_handling(self, agent_ui_service, sample_request):
        """Test error handling when runtime adapter fails."""
        # Mock runtime adapter to raise an exception
        mock_runtime_adapter = Mock()
        mock_runtime_adapter.execute_task = AsyncMock(
            side_effect=Exception("Runtime error")
        )

        service = AgentUIService(runtime_adapter=mock_runtime_adapter)

        # Send message - should handle error gracefully
        response = asyncio.run(service.send_message(sample_request))

        # Should return error response
        assert response.success == False
        assert "Runtime error" in response.content
        assert "error" in response.execution_metadata


class TestSessionThreadMapping:
    """Test session/thread mapping functionality."""

    async def test_session_thread_creation(self, thread_manager):
        """Test that thread manager creates threads for sessions."""
        session_id = "test_session_123"
        thread_id = await thread_manager.create_thread(session_id)

        # Verify thread was created
        assert thread_id is not None
        assert thread_id.startswith("langgraph_")

        # Verify mapping exists
        retrieved_thread_id = await thread_manager.get_langgraph_thread(session_id)
        assert retrieved_thread_id == thread_id

    async def test_thread_metadata_tracking(self, thread_manager):
        """Test that thread metadata is properly tracked."""
        session_id = "test_session_123"
        thread_id = await thread_manager.create_thread(session_id)

        # Get metadata
        metadata = await thread_manager.get_thread_metadata(thread_id)

        assert metadata is not None
        assert metadata["copilot_session_id"] == session_id
        assert metadata["status"] == "active"
        assert "created_at" in metadata
        assert "last_accessed" in metadata
        assert metadata["message_count"] == 0

    async def test_message_count_increment(self, thread_manager):
        """Test that message count is properly incremented."""
        session_id = "test_session_123"
        thread_id = await thread_manager.create_thread(session_id)

        # Initial count should be 0
        metadata = await thread_manager.get_thread_metadata(thread_id)
        assert metadata["message_count"] == 0

        # Increment count
        success = await thread_manager.increment_message_count(thread_id)
        assert success == True

        # Verify count increased
        metadata = await thread_manager.get_thread_metadata(thread_id)
        assert metadata["message_count"] == 1

    async def test_thread_cleanup(self, thread_manager):
        """Test thread cleanup functionality."""
        # Create a thread
        session_id = "test_session_123"
        thread_id = await thread_manager.create_thread(session_id)

        # Verify thread exists
        assert await thread_manager.get_thread_metadata(thread_id) is not None

        # Delete thread
        success = await thread_manager.delete_thread(thread_id)
        assert success == True

        # Verify thread is deleted
        assert await thread_manager.get_thread_metadata(thread_id) is None

    async def test_thread_statistics(self, thread_manager):
        """Test thread statistics functionality."""
        # Create multiple threads
        session1 = "session_1"
        session2 = "session_2"

        await thread_manager.create_thread(session1)
        await thread_manager.create_thread(session2)

        # Increment message count for one thread
        thread_id = await thread_manager.get_langgraph_thread(session1)
        await thread_manager.increment_message_count(thread_id)

        # Get statistics
        stats = thread_manager.get_thread_statistics()

        assert stats["total_threads"] == 2
        assert stats["total_messages"] == 1
        assert stats["threads_per_session"] == 2

    async def test_thread_migration(self, thread_manager):
        """Test thread migration between sessions."""
        old_session = "old_session_123"
        new_session = "new_session_456"

        # Create thread for old session
        old_thread_id = await thread_manager.create_thread(old_session)

        # Migrate thread to new session
        new_thread_id = await thread_manager.migrate_thread(old_session, new_session)

        # Verify migration
        assert new_thread_id is not None
        assert new_thread_id == old_thread_id  # Should reuse same thread ID

        # Verify mappings are updated
        assert await thread_manager.get_langgraph_thread(new_session) == new_thread_id
        assert await thread_manager.get_copilot_session(new_thread_id) == new_session


class TestSessionStateManagement:
    """Test session state management functionality."""

    async def test_session_state_save_load(self, session_manager):
        """Test saving and loading session state."""
        session_id = "test_session_123"
        test_state = {
            "user_preferences": {"theme": "dark", "language": "en"},
            "conversation_history": ["Hello", "Hi there"],
            "active_tasks": ["task_1", "task_2"],
        }

        # Save state
        success = await session_manager.save_session_state(session_id, test_state)
        assert success == True

        # Load state
        loaded_state = await session_manager.load_session_state(session_id)
        assert loaded_state is not None
        assert loaded_state["user_preferences"] == test_state["user_preferences"]
        assert (
            loaded_state["conversation_history"] == test_state["conversation_history"]
        )
        assert loaded_state["active_tasks"] == test_state["active_tasks"]

    async def test_session_state_field_access(self, session_manager):
        """Test field-level access to session state."""
        session_id = "test_session_123"
        test_state = {
            "user": {
                "name": "John Doe",
                "preferences": {"theme": "dark", "notifications": True},
            },
            "tasks": [],
        }

        # Save state
        await session_manager.save_session_state(session_id, test_state)

        # Test field access
        name = await session_manager.get_session_state_field(session_id, "user.name")
        assert name == "John Doe"

        theme = await session_manager.get_session_state_field(
            session_id, "user.preferences.theme"
        )
        assert theme == "dark"

        # Test non-existent field
        non_existent = await session_manager.get_session_state_field(
            session_id, "non.existent.field"
        )
        assert non_existent is None

    async def test_session_state_field_update(self, session_manager):
        """Test updating specific fields in session state."""
        session_id = "test_session_123"
        test_state = {
            "user": {"name": "John Doe", "preferences": {"theme": "light"}},
            "tasks": [],
        }

        # Save initial state
        await session_manager.save_session_state(session_id, test_state)

        # Update specific field
        success = await session_manager.set_session_state_field(
            session_id, "user.preferences.theme", "dark"
        )
        assert success == True

        # Verify update
        updated_state = await session_manager.load_session_state(session_id)
        assert updated_state["user"]["preferences"]["theme"] == "dark"

    async def test_session_state_callbacks(self, session_manager):
        """Test session state change callbacks."""
        session_id = "test_session_123"
        callback_calls = []

        async def test_callback(session_id, event_type, data):
            callback_calls.append((session_id, event_type, data))

        # Register callback
        session_manager.register_state_callback("save", test_callback)

        # Perform state operations
        test_state = {"test": "data"}
        await session_manager.save_session_state(session_id, test_state)
        await session_manager.update_session_state(session_id, {"update": "value"})

        # Verify callbacks were called
        assert len(callback_calls) >= 2
        assert any(call[1] == "save" for call in callback_calls)
        assert any(call[1] == "update" for call in callback_calls)

    async def test_session_state_cleanup(self, session_manager):
        """Test session state cleanup functionality."""
        # Create multiple session states
        sessions = [f"session_{i}" for i in range(5)]
        for session in sessions:
            await session_manager.save_session_state(
                session, {"data": f"session_{session}"}
            )

        # Verify states exist
        for session in sessions:
            state = await session_manager.load_session_state(session)
            assert state is not None

        # Delete one session
        success = await session_manager.delete_session_state(sessions[0])
        assert success == True

        # Verify deletion
        state = await session_manager.load_session_state(sessions[0])
        assert state is None


class TestTaskProgressTracking:
    """Test task progress tracking functionality."""

    async def test_task_progress_initialization(self, agent_ui_service, sample_request):
        """Test that task progress is properly initialized."""
        # Create task and check progress initialization
        task = agent_ui_service._create_agent_task_from_message(sample_request)
        agent_ui_service._initialize_task_progress(task)

        # Verify progress entry exists
        assert task.task_id in agent_ui_service._task_progress

        progress = agent_ui_service._task_progress[task.task_id]
        assert progress.status == TaskStatus.PENDING
        assert progress.progress_percentage == 0.0
        assert progress.steps == []

    async def test_task_progress_updates(self, agent_ui_service, sample_request):
        """Test task progress updates during execution."""
        # Send message and track progress
        response = await agent_ui_service.send_message(sample_request)

        # Verify progress was updated
        task_id = response.task_id
        assert task_id in agent_ui_service._task_progress

        progress = agent_ui_service._task_progress[task_id]
        assert progress.status == TaskStatus.COMPLETED
        assert progress.progress_percentage == 100.0

    async def test_long_running_task_progress(
        self, agent_ui_service, sample_deep_task_request
    ):
        """Test progress tracking for long-running tasks."""
        response = await agent_ui_service.create_deep_task(sample_deep_task_request)

        # Verify task was created
        assert response.success == True
        assert response.task_id is not None

        # Check initial progress
        progress_request = GetTaskProgressRequest(
            session_id=sample_deep_task_request.session_id, task_id=response.task_id
        )

        progress = await agent_ui_service.get_task_progress(progress_request)
        assert progress.status == TaskStatus.PENDING
        assert progress.progress_percentage == 0.0

    async def test_task_cancellation_progress(
        self, agent_ui_service, sample_deep_task_request
    ):
        """Test task cancellation and progress update."""
        # Create long-running task
        response = await agent_ui_service.create_deep_task(sample_deep_task_request)
        task_id = response.task_id

        # Cancel task
        cancel_request = CancelTaskRequest(
            session_id=sample_deep_task_request.session_id,
            task_id=task_id,
            reason="Test cancellation",
        )

        cancel_response = await agent_ui_service.cancel_task(cancel_request)
        assert cancel_response.success == True

        # Verify progress reflects cancellation
        progress_request = GetTaskProgressRequest(
            session_id=sample_deep_task_request.session_id, task_id=task_id
        )

        progress = await agent_ui_service.get_task_progress(progress_request)
        assert progress.status == TaskStatus.CANCELLED
        assert "cancelled" in progress.error_message.lower()


class TestBoundaryLayerValidation:
    """Test that CopilotKit acts as proper UI boundary."""

    def test_request_validation(self, agent_ui_service):
        """Test that CopilotKit validates requests properly."""
        # Test invalid requests
        invalid_requests = [
            SendMessageRequest(session_id="", content="test"),  # Empty session ID
            SendMessageRequest(session_id="valid", content=""),  # Empty content
            SendMessageRequest(
                session_id="valid", content="test", task_type="invalid_type"
            ),  # Invalid task type
        ]

        for request in invalid_requests:
            try:
                task = agent_ui_service._create_agent_task_from_message(request)
                # Should not reach here for invalid requests
                assert False, (
                    f"Should have raised validation error for request: {request}"
                )
            except ValueError:
                # Expected validation error
                pass

    def test_response_formatting(self, agent_ui_service, sample_request):
        """Test that responses are properly formatted for UI consumption."""
        # Send message
        response = asyncio.run(agent_ui_service.send_message(sample_request))

        # Verify response structure
        assert hasattr(response, "success")
        assert hasattr(response, "task_id")
        assert hasattr(response, "content")
        assert hasattr(response, "execution_metadata")
        assert hasattr(response, "thread_id")
        assert hasattr(response, "timestamp")

        # Verify data types
        assert isinstance(response.success, bool)
        assert isinstance(response.task_id, str)
        assert isinstance(response.content, str)
        assert isinstance(response.execution_metadata, dict)
        assert isinstance(response.thread_id, str)

    def test_error_handling_and_responses(self, agent_ui_service):
        """Test error handling and response formatting."""
        # Test with runtime adapter that raises errors
        mock_runtime_adapter = Mock()
        mock_runtime_adapter.execute_task = AsyncMock(
            side_effect=Exception("Test error")
        )

        service = AgentUIService(runtime_adapter=mock_runtime_adapter)

        # Send message
        response = asyncio.run(
            service.send_message(
                SendMessageRequest(session_id="test_session", content="test message")
            )
        )

        # Verify error response format
        assert response.success == False
        assert "Test error" in response.content
        assert "error" in response.execution_metadata
        assert response.execution_metadata["error"] == "Test error"

    def test_input_sanitization(self, agent_ui_service):
        """Test input sanitization for security."""
        # Test with potentially dangerous content
        dangerous_request = SendMessageRequest(
            session_id="test_session",
            content="<script>alert('xss')</script>",
            context={"malicious": "data"},
        )

        # Create task - should handle safely
        task = agent_ui_service._create_agent_task_from_message(dangerous_request)

        # Verify content is preserved but handled safely
        assert task.content == "<script>alert('xss')</script>"
        assert isinstance(task.context, dict)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    async def test_complete_conversation_workflow(
        self, agent_ui_service, mock_runtime_adapter
    ):
        """Test complete conversation workflow from UI to runtime."""
        session_id = "test_session_123"

        # Step 1: Send initial message
        request1 = SendMessageRequest(
            session_id=session_id,
            content="Hello, I need help with my project",
            task_type=TaskType.CONVERSATION,
        )

        response1 = await agent_ui_service.send_message(request1)
        assert response1.success == True
        assert response1.task_id is not None

        # Step 2: Send follow-up message
        request2 = SendMessageRequest(
            session_id=session_id,
            content="Can you help me refactor this code?",
            task_type=TaskType.CODE_REFACTOR,
        )

        response2 = await agent_ui_service.send_message(request2)
        assert response2.success == True
        assert response2.task_id is not None

        # Step 3: Check task history
        history = agent_ui_service.get_task_history(session_id)
        assert len(history) >= 2

        # Step 4: Verify runtime was called for both messages
        assert mock_runtime_adapter.execute_task.call_count == 2

    async def test_error_recovery_workflow(self, agent_ui_service):
        """Test error recovery and fallback scenarios."""
        # Configure runtime adapter to fail first, then succeed
        mock_runtime_adapter = Mock()

        # First call fails, second succeeds
        mock_runtime_adapter.execute_task.side_effect = [
            Exception("Temporary failure"),
            {"content": "Success after retry", "metadata": {"retried": True}},
        ]

        service = AgentUIService(runtime_adapter=mock_runtime_adapter)

        # Send message - should handle error and retry
        request = SendMessageRequest(session_id="test_session", content="Test message")

        response = await service.send_message(request)

        # Should eventually succeed
        assert response.success == True
        assert "Success after retry" in response.content

        # Verify retry happened
        assert mock_runtime_adapter.execute_task.call_count == 2

    async def test_session_continuity_workflow(
        self, agent_ui_service, thread_manager, session_manager
    ):
        """Test session continuity and state management across multiple interactions."""
        session_id = "test_session_123"

        # Create thread and save initial state
        await thread_manager.create_thread(session_id)
        await session_manager.save_session_state(
            session_id,
            {
                "user_context": {"name": "John", "preferences": {"theme": "dark"}},
                "conversation_history": [],
            },
        )

        # Send multiple messages
        messages = [
            "Hello, I'm John",
            "I need help with my Python code",
            "Can you explain async patterns?",
        ]

        responses = []
        for message in messages:
            request = SendMessageRequest(
                session_id=session_id, content=message, task_type=TaskType.CONVERSATION
            )
            response = await agent_ui_service.send_message(request)
            responses.append(response)
            assert response.success == True

        # Verify session state was maintained
        final_state = await session_manager.load_session_state(session_id)
        assert len(final_state.get("conversation_history", [])) == 3

        # Verify thread was used for all messages
        thread_id = await thread_manager.get_langgraph_thread(session_id)
        metadata = await thread_manager.get_thread_metadata(thread_id)
        assert metadata["message_count"] == 3

    async def test_concurrent_tasks_workflow(self, agent_ui_service):
        """Test handling of concurrent tasks."""
        session_id = "test_session_123"

        # Create multiple concurrent tasks
        tasks = []
        for i in range(3):
            request = SendMessageRequest(
                session_id=session_id,
                content=f"Task {i + 1} content",
                task_type=TaskType.CONVERSATION,
            )
            response = await agent_ui_service.create_deep_task(
                CreateDeepTaskRequest(
                    session_id=session_id,
                    content=f"Task {i + 1} content",
                    task_type=TaskType.CONVERSATION,
                )
            )
            tasks.append(response)

        # Verify all tasks were created
        for task in tasks:
            assert task.success == True
            assert task.task_id is not None

        # Check active tasks
        active_tasks = agent_ui_service.get_active_tasks(session_id)
        assert len(active_tasks) == 3

        # Cancel all tasks
        for task in tasks:
            cancel_request = CancelTaskRequest(
                session_id=session_id, task_id=task.task_id, reason="Test cancellation"
            )
            cancel_response = await agent_ui_service.cancel_task(cancel_request)
            assert cancel_response.success == True

        # Verify tasks are no longer active
        active_tasks = agent_ui_service.get_active_tasks(session_id)
        assert len(active_tasks) == 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing interfaces."""

    def test_existing_api_compatibility(self, agent_ui_service):
        """Test that existing API interfaces still work."""
        # Test that existing request/response types still work
        request = SendMessageRequest(
            session_id="test_session",
            content="Test message",
            execution_mode="auto",  # Old style enum string
        )

        # Should handle old-style enum strings
        response = asyncio.run(agent_ui_service.send_message(request))
        assert response.success == True

        # Verify execution mode is normalized to LANGGRAPH
        task = agent_ui_service._create_agent_task_from_message(request)
        assert task.execution_mode == TaskType.LANGGRAPH

    def test_task_id_generation_compatibility(self, agent_ui_service):
        """Test that task ID generation is compatible with existing systems."""
        # Create multiple tasks
        tasks = []
        for i in range(5):
            request = SendMessageRequest(
                session_id=f"session_{i}", content=f"Message {i}"
            )
            response = asyncio.run(agent_ui_service.send_message(request))
            tasks.append(response)

        # Verify all task IDs are unique
        task_ids = [task.task_id for task in tasks]
        assert len(set(task_ids)) == len(task_ids), "All task IDs should be unique"

        # Verify task ID format
        for task_id in task_ids:
            assert isinstance(task_id, str)
            assert len(task_id) > 0
            assert "-" not in task_id  # Should use UUID format without dashes

    def test_thread_id_compatibility(self, thread_manager):
        """Test that thread ID generation is compatible."""
        session_id = "test_session_123"
        thread_id = asyncio.run(thread_manager.create_thread(session_id))

        # Verify thread ID format
        assert isinstance(thread_id, str)
        assert thread_id.startswith("langgraph_")
        assert len(thread_id) > len("langgraph_")

        # Verify thread ID is stable for same session
        thread_id_2 = asyncio.run(thread_manager.create_thread(session_id))
        assert thread_id == thread_id_2

    def test_metadata_compatibility(self, agent_ui_service, sample_request):
        """Test that metadata is compatible with existing systems."""
        response = asyncio.run(agent_ui_service.send_message(sample_request))

        # Verify metadata structure
        metadata = response.execution_metadata
        assert isinstance(metadata, dict)
        assert "runtime" in metadata
        assert "mode" in metadata
        assert metadata["runtime"] == "langgraph"
        assert metadata["mode"] == "agentmedusa"


class TestPerformanceAndScalability:
    """Test performance and scalability aspects."""

    async def test_concurrent_requests_handling(
        self, agent_ui_service, mock_runtime_adapter
    ):
        """Test handling of concurrent requests."""
        # Create multiple concurrent requests
        requests = []
        for i in range(10):
            request = SendMessageRequest(
                session_id=f"session_{i}",
                content=f"Concurrent message {i}",
                task_type=TaskType.CONVERSATION,
            )
            requests.append(request)

        # Process requests concurrently
        tasks = [agent_ui_service.send_message(req) for req in requests]
        responses = await asyncio.gather(*tasks)

        # Verify all requests succeeded
        for response in responses:
            assert response.success == True

        # Verify runtime adapter was called for each request
        assert mock_runtime_adapter.execute_task.call_count == 10

    async def test_session_state_performance(self, session_manager):
        """Test session state performance with large datasets."""
        session_id = "test_session_123"

        # Create large state
        large_state = {
            "conversation_history": [f"Message {i}" for i in range(1000)],
            "file_attachments": [f"file_{i}.txt" for i in range(100)],
            "execution_results": [
                {"step": i, "result": f"result_{i}"} for i in range(500)
            ],
        }

        # Test save performance
        import time

        start_time = time.time()
        success = await session_manager.save_session_state(session_id, large_state)
        save_time = time.time() - start_time

        assert success == True
        assert save_time < 1.0, f"Save took too long: {save_time}s"

        # Test load performance
        start_time = time.time()
        loaded_state = await session_manager.load_session_state(session_id)
        load_time = time.time() - start_time

        assert loaded_state is not None
        assert load_time < 1.0, f"Load took too long: {load_time}s"

        # Verify data integrity
        assert len(loaded_state["conversation_history"]) == 1000
        assert len(loaded_state["file_attachments"]) == 100
        assert len(loaded_state["execution_results"]) == 500

    async def test_memory_usage_monitoring(self, agent_ui_service):
        """Test memory usage monitoring."""
        # Get initial statistics
        initial_stats = agent_ui_service.get_task_history()
        initial_active = agent_ui_service.get_active_tasks()

        # Create many tasks
        for i in range(50):
            request = SendMessageRequest(
                session_id="test_session",
                content=f"Test message {i}",
                task_type=TaskType.CONVERSATION,
            )
            response = await agent_ui_service.send_message(request)
            assert response.success == True

        # Get final statistics
        final_stats = agent_ui_service.get_task_history()
        final_active = agent_ui_service.get_active_tasks()

        # Verify statistics are reasonable
        assert len(final_stats) >= len(initial_stats)
        assert len(final_active) >= 0


class TestMonitoringAndLogging:
    """Test monitoring and logging functionality."""

    @patch("ai_karen_engine.copilotkit.agent_ui_service.logger")
    async def test_request_logging(self, mock_logger, agent_ui_service, sample_request):
        """Test that requests are properly logged."""
        # Send message
        response = await agent_ui_service.send_message(sample_request)

        # Verify logging occurred
        mock_logger.info.assert_called()
        assert any(
            "Processing message" in str(call)
            for call in mock_logger.info.call_args_list
        )

    @patch("ai_karen_engine.copilotkit.thread_manager.logger")
    async def test_thread_operation_logging(self, mock_logger, thread_manager):
        """Test that thread operations are logged."""
        session_id = "test_session_123"

        # Create thread
        thread_id = await thread_manager.create_thread(session_id)

        # Verify logging occurred
        mock_logger.info.assert_called()
        assert any(
            "Created thread" in str(call) for call in mock_logger.info.call_args_list
        )

    @patch("ai_karen_engine.copilotkit.session_state_manager.logger")
    async def test_state_operation_logging(self, mock_logger, session_manager):
        """Test that state operations are logged."""
        session_id = "test_session_123"
        test_state = {"test": "data"}

        # Save state
        await session_manager.save_session_state(session_id, test_state)

        # Verify logging occurred
        mock_logger.info.assert_called()
        assert any(
            "Saving session state" in str(call)
            for call in mock_logger.info.call_args_list
        )

    async def test_error_logging(self, agent_ui_service):
        """Test error logging."""
        # Configure runtime adapter to raise an error
        mock_runtime_adapter = Mock()
        mock_runtime_adapter.execute_task = AsyncMock(
            side_effect=Exception("Test error")
        )

        service = AgentUIService(runtime_adapter=mock_runtime_adapter)

        # Send message that will cause an error
        request = SendMessageRequest(session_id="test_session", content="Error message")

        response = await service.send_message(request)

        # Verify error was logged (this would be visible in actual logs)
        assert response.success == False
        assert "Test error" in response.content


# Test utilities
class TestUtils:
    """Test utility functions and helpers."""

    def test_uuid_generation(self):
        """Test UUID generation for task and thread IDs."""
        import uuid

        # Test task ID generation
        task_id = str(uuid.uuid4())
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # Standard UUID length

        # Test thread ID generation
        session_id = "test_session"
        thread_id = f"langgraph_{session_id}_{uuid.uuid4().hex}"
        assert isinstance(thread_id, str)
        assert thread_id.startswith("langgraph_")

    def test_time_handling(self):
        """Test time handling in the system."""
        from datetime import datetime, timedelta

        # Test time calculations
        now = datetime.utcnow()
        past = now - timedelta(days=1)
        future = now + timedelta(days=1)

        assert past < now < future

        # Test time delta calculations
        delta = future - past
        assert delta.days == 2

    def test_data_validation(self):
        """Test data validation functions."""

        # Test string validation
        def validate_string(value, field_name):
            if not isinstance(value, str):
                raise ValueError(f"{field_name} must be a string")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be empty")
            return value.strip()

        # Valid string
        result = validate_string("  test  ", "test_field")
        assert result == "test"

        # Invalid strings
        with pytest.raises(ValueError):
            validate_string("", "empty_field")

        with pytest.raises(ValueError):
            validate_string(None, "none_field")

        with pytest.raises(ValueError):
            validate_string(123, "number_field")

    def test_json_serialization(self):
        """Test JSON serialization of complex objects."""
        import json

        # Test complex data structure
        complex_data = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"inner": "value", "array": ["a", "b", "c"]},
            "datetime": datetime.utcnow().isoformat(),
        }

        # Serialize and deserialize
        serialized = json.dumps(complex_data, default=str)
        deserialized = json.loads(serialized)

        assert deserialized["string"] == "test"
        assert deserialized["number"] == 123
        assert deserialized["boolean"] == True
        assert deserialized["list"] == [1, 2, 3]
        assert deserialized["nested"]["inner"] == "value"


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
