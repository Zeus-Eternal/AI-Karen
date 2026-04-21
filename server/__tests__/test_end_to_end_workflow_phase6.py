"""
End-to-End Workflow Tests - Phase 6.

Comprehensive end-to-end tests for complete workflows:
1. Complete workflow from UI request to runtime execution
2. Error handling and fallback scenarios
3. Session continuity and state management
4. Multi-step workflows and task chaining
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ai_karen_engine.copilotkit.agent_ui_service import AgentUIService
from ai_karen_engine.copilotkit.thread_manager import ThreadManager
from ai_karen_engine.copilotkit.session_state_manager import SessionStateManager
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


class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    @pytest.fixture
    def mock_runtime_adapter(self):
        """Mock runtime adapter for testing."""
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Runtime execution result",
                "metadata": {
                    "runtime": "langgraph",
                    "mode": "agentmedusa",
                    "execution_time": 1.5,
                    "tokens_used": 100,
                },
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
    def complete_service(self, mock_runtime_adapter, thread_manager, session_manager):
        """Complete service with all dependencies."""
        return AgentUIService(
            runtime_adapter=mock_runtime_adapter,
            thread_manager=thread_manager,
            session_manager=session_manager,
        )

    async def test_complete_conversation_workflow(self, complete_service):
        """Test complete conversation workflow from UI to runtime."""
        session_id = "test_session_123"

        # Step 1: Initialize session
        await complete_service.thread_manager.create_thread(session_id)
        await complete_service.session_manager.save_session_state(
            session_id,
            {
                "user_context": {"name": "John", "preferences": {"theme": "dark"}},
                "conversation_history": [],
            },
        )

        # Step 2: Send initial message
        request1 = SendMessageRequest(
            session_id=session_id,
            content="Hello, I'm John and I need help with my project",
            task_type=TaskType.CONVERSATION,
            user_id="user_456",
            tenant_id="tenant_789",
        )

        response1 = await complete_service.send_message(request1)
        assert response1.success == True
        assert response1.task_id is not None

        # Step 3: Send follow-up message
        request2 = SendMessageRequest(
            session_id=session_id,
            content="Can you help me refactor this Python code?",
            task_type=TaskType.CODE_REFACTOR,
            context={"project": "my_python_app"},
        )

        response2 = await complete_service.send_message(request2)
        assert response2.success == True
        assert response2.task_id is not None

        # Step 4: Send another message
        request3 = SendMessageRequest(
            session_id=session_id,
            content="What about documentation?",
            task_type=TaskType.DOCUMENTATION,
        )

        response3 = await complete_service.send_message(request3)
        assert response3.success == True
        assert response3.task_id is not None

        # Step 5: Verify workflow completion
        # Check thread usage
        thread_id = await complete_service.thread_manager.get_langgraph_thread(
            session_id
        )
        metadata = await complete_service.thread_manager.get_thread_metadata(thread_id)
        assert metadata["message_count"] == 3

        # Check session state
        session_state = await complete_service.session_manager.load_session_state(
            session_id
        )
        assert len(session_state.get("conversation_history", [])) == 3

        # Check task history
        task_history = complete_service.get_task_history(session_id)
        assert len(task_history) == 3

        # Verify runtime adapter was called for each message
        assert complete_service.runtime_adapter.execute_task.call_count == 3

    async def test_multi_step_task_workflow(self, complete_service):
        """Test multi-step task workflow."""
        session_id = "test_session_123"

        # Step 1: Create long-running task
        create_request = CreateDeepTaskRequest(
            session_id=session_id,
            content="Refactor the entire application",
            task_type=TaskType.CODE_REFACTOR,
            priority=8,
            timeout_seconds=300,
        )

        create_response = await complete_service.create_deep_task(create_request)
        assert create_response.success == True
        assert create_response.task_id is not None

        # Step 2: Check task progress
        progress_request = GetTaskProgressRequest(
            session_id=session_id, task_id=create_response.task_id
        )

        progress_response = await complete_service.get_task_progress(progress_request)
        assert progress_response.status == TaskStatus.PENDING
        assert progress_response.progress_percentage == 0.0

        # Step 3: Wait for task completion (simulate)
        # In real scenario, this would be handled by background task
        await asyncio.sleep(0.1)  # Simulate some processing time

        # Step 4: Check progress again
        progress_response = await complete_service.get_task_progress(progress_request)
        assert progress_response.status == TaskStatus.RUNNING
        assert progress_response.progress_percentage > 0.0

        # Step 5: Cancel task (simulate user cancellation)
        cancel_request = CancelTaskRequest(
            session_id=session_id,
            task_id=create_response.task_id,
            reason="User cancelled",
        )

        cancel_response = await complete_service.cancel_task(cancel_request)
        assert cancel_response.success == True

        # Step 6: Verify cancellation
        progress_response = await complete_service.get_task_progress(progress_request)
        assert progress_response.status == TaskStatus.CANCELLED

    async def test_session_continuity_workflow(self, complete_service):
        """Test session continuity across multiple interactions."""
        session_id = "test_session_123"

        # Step 1: Initialize session with state
        await complete_service.thread_manager.create_thread(session_id)
        initial_state = {
            "user_context": {"name": "Alice", "preferences": {"theme": "light"}},
            "conversation_history": [],
            "active_tasks": [],
        }
        await complete_service.session_manager.save_session_state(
            session_id, initial_state
        )

        # Step 2: Send multiple messages
        messages = [
            "Hello, I'm Alice",
            "I need help with my Python project",
            "Can you help me optimize the database queries?",
            "What about adding tests?",
        ]

        responses = []
        for i, message in enumerate(messages):
            request = SendMessageRequest(
                session_id=session_id,
                content=message,
                task_type=TaskType.CONVERSATION if i < 2 else TaskType.ANALYSIS,
                context={"project": "my_python_app"},
            )

            response = await complete_service.send_message(request)
            responses.append(response)
            assert response.success == True

        # Step 3: Verify session continuity
        # Check thread usage
        thread_id = await complete_service.thread_manager.get_langgraph_thread(
            session_id
        )
        metadata = await complete_service.thread_manager.get_thread_metadata(thread_id)
        assert metadata["message_count"] == 4

        # Check session state evolution
        current_state = await complete_service.session_manager.load_session_state(
            session_id
        )
        assert len(current_state.get("conversation_history", [])) == 4
        assert len(current_state.get("active_tasks", [])) == 0

        # Check task history
        task_history = complete_service.get_task_history(session_id)
        assert len(task_history) == 4

        # Verify all tasks have consistent session ID
        for task in task_history:
            assert task["session_id"] == session_id

    async def test_concurrent_task_workflow(self, complete_service):
        """Test handling of concurrent tasks."""
        session_id = "test_session_123"

        # Step 1: Create multiple concurrent tasks
        task_requests = []
        for i in range(5):
            request = CreateDeepTaskRequest(
                session_id=session_id,
                content=f"Concurrent task {i + 1}: {['refactor', 'debug', 'test', 'document', 'optimize'][i]}",
                task_type=[
                    TaskType.CODE_REFACTOR,
                    TaskType.DEBUGGING,
                    TaskType.CODE_GENERATION,
                    TaskType.DOCUMENTATION,
                    TaskType.ANALYSIS,
                ][i],
                priority=[5, 8, 6, 4, 7][i],
            )
            task_requests.append(request)

        # Create all tasks concurrently
        create_tasks = [complete_service.create_deep_task(req) for req in task_requests]
        create_responses = await asyncio.gather(*create_tasks)

        # Verify all tasks were created
        task_ids = []
        for response in create_responses:
            assert response.success == True
            assert response.task_id is not None
            task_ids.append(response.task_id)

        # Step 2: Check active tasks
        active_tasks = complete_service.get_active_tasks(session_id)
        assert len(active_tasks) == 5

        # Step 3: Monitor progress for all tasks
        progress_tasks = []
        for task_id in task_ids:
            progress_request = GetTaskProgressRequest(
                session_id=session_id, task_id=task_id
            )
            progress_tasks.append(complete_service.get_task_progress(progress_request))

        progress_responses = await asyncio.gather(*progress_tasks)

        # Verify all tasks have progress tracking
        for progress in progress_responses:
            assert progress.task_id in task_ids
            assert progress.status in TaskStatus

        # Step 4: Cancel some tasks
        cancel_tasks = []
        for i, task_id in enumerate(task_ids[:3]):  # Cancel first 3 tasks
            cancel_request = CancelTaskRequest(
                session_id=session_id, task_id=task_id, reason=f"Cancelled task {i + 1}"
            )
            cancel_tasks.append(complete_service.cancel_task(cancel_request))

        cancel_responses = await asyncio.gather(*cancel_tasks)

        # Verify cancellations
        for response in cancel_responses:
            assert response.success == True

        # Step 5: Verify final state
        active_tasks = complete_service.get_active_tasks(session_id)
        assert len(active_tasks) == 2  # 2 tasks should remain active

        # Check thread statistics
        thread_stats = complete_service.thread_manager.get_thread_statistics()
        assert thread_stats["total_threads"] == 1
        assert thread_stats["total_messages"] == 0  # No direct messages, only tasks


class TestErrorHandlingWorkflows:
    """Test error handling and fallback scenarios."""

    @pytest.fixture
    def error_runtime_adapter(self):
        """Runtime adapter that simulates errors."""
        adapter = Mock()

        # First call fails, subsequent calls succeed
        call_count = 0

        def execute_task_with_retry(task):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Retry {call_count}: Temporary failure")
            return {
                "content": f"Success after {call_count} attempts",
                "metadata": {"retries": call_count - 1},
            }

        adapter.execute_task = AsyncMock(side_effect=execute_task_with_retry)
        return adapter

    @pytest.fixture
    def error_service(self, error_runtime_adapter, thread_manager, session_manager):
        """Service with error handling."""
        return AgentUIService(
            runtime_adapter=error_runtime_adapter,
            thread_manager=thread_manager,
            session_manager=session_manager,
        )

    async def test_error_recovery_workflow(self, error_service):
        """Test error recovery workflow."""
        session_id = "test_session_123"

        # Step 1: Send message that will fail initially
        request = SendMessageRequest(
            session_id=session_id,
            content="Error recovery test",
            task_type=TaskType.CONVERSATION,
        )

        # First attempt should fail
        response1 = await error_service.send_message(request)
        assert response1.success == False
        assert "Temporary failure" in response1.content

        # Second attempt should also fail
        response2 = await error_service.send_message(request)
        assert response2.success == False
        assert "Temporary failure" in response2.content

        # Third attempt should succeed
        response3 = await error_service.send_message(request)
        assert response3.success == True
        assert "Success after 3 attempts" in response3.content

        # Verify runtime was called 3 times
        assert error_service.runtime_adapter.execute_task.call_count == 3

    async def test_graceful_degradation_workflow(self, error_service):
        """Test graceful degradation when runtime fails."""
        session_id = "test_session_123"

        # Configure adapter to always fail
        error_service.runtime_adapter.execute_task = AsyncMock(
            side_effect=Exception("Persistent failure")
        )

        request = SendMessageRequest(
            session_id=session_id,
            content="Degradation test",
            task_type=TaskType.CONVERSATION,
        )

        response = await error_service.send_message(request)

        # Should handle gracefully
        assert response.success == True
        assert "Runtime adapter not configured" in response.content
        assert response.execution_metadata["configured"] == False

    async def test_session_error_handling(self, error_service):
        """Test session error handling."""
        session_id = "test_session_123"

        # Step 1: Create session state
        await error_service.session_manager.save_session_state(
            session_id, {"test": "data"}
        )

        # Step 2: Simulate session state corruption
        with patch.object(error_service.session_manager, "_session_state", {}):
            # Try to load state - should handle gracefully
            state = await error_service.session_manager.load_session_state(session_id)
            assert state is None

            # Try to send message - should still work
            request = SendMessageRequest(
                session_id=session_id,
                content="Error handling test",
                task_type=TaskType.CONVERSATION,
            )

            response = await error_service.send_message(request)
            assert response.success == True

    async def test_concurrent_error_handling(self, error_service):
        """Test error handling with concurrent requests."""
        session_id = "test_session_123"

        # Configure adapter to fail for first few calls
        call_count = 0

        def execute_task_with_concurrent_error(task):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception(f"Concurrent error {call_count}")
            return {
                "content": f"Concurrent success {call_count}",
                "metadata": {"concurrent_call": call_count},
            }

        error_service.runtime_adapter.execute_task.side_effect = (
            execute_task_with_concurrent_error
        )

        # Create multiple concurrent requests
        requests = [
            SendMessageRequest(
                session_id=session_id,
                content=f"Concurrent message {i}",
                task_type=TaskType.CONVERSATION,
            )
            for i in range(5)
        ]

        # Process concurrently
        responses = await asyncio.gather(
            *[error_service.send_message(req) for req in requests]
        )

        # Verify results
        success_count = sum(1 for r in responses if r.success)
        failure_count = sum(1 for r in responses if not r.success)

        # Should have some failures and some successes
        assert failure_count > 0
        assert success_count > 0
        assert success_count + failure_count == 5


class TestStateManagementWorkflows:
    """Test state management workflows."""

    @pytest.fixture
    def state_service(self, mock_runtime_adapter, thread_manager, session_manager):
        """Service with state management."""
        return AgentUIService(
            runtime_adapter=mock_runtime_adapter,
            thread_manager=thread_manager,
            session_manager=session_manager,
        )

    async def test_state_persistence_workflow(self, state_service):
        """Test state persistence workflow."""
        session_id = "test_session_123"

        # Step 1: Initialize session
        await state_service.thread_manager.create_thread(session_id)

        # Step 2: Save initial state
        initial_state = {
            "user_context": {"name": "Bob", "preferences": {"theme": "dark"}},
            "conversation_history": [],
            "active_tasks": [],
            "project_context": {"name": "my_app", "version": "1.0"},
        }

        success = await state_service.session_manager.save_session_state(
            session_id, initial_state
        )
        assert success == True

        # Step 3: Send messages to update state
        messages = [
            "Hello, I'm Bob",
            "I'm working on my_app",
            "Can you help me add authentication?",
        ]

        for message in messages:
            request = SendMessageRequest(
                session_id=session_id, content=message, task_type=TaskType.CONVERSATION
            )
            response = await state_service.send_message(request)
            assert response.success == True

        # Step 4: Verify state evolution
        current_state = await state_service.session_manager.load_session_state(
            session_id
        )
        assert len(current_state.get("conversation_history", [])) == 3
        assert current_state["user_context"]["name"] == "Bob"
        assert current_state["project_context"]["name"] == "my_app"

        # Step 5: Update specific state fields
        success = await state_service.session_manager.set_session_state_field(
            session_id, "user_context.preferences.theme", "light"
        )
        assert success == True

        # Step 6: Verify field update
        updated_state = await state_service.session_manager.load_session_state(
            session_id
        )
        assert updated_state["user_context"]["preferences"]["theme"] == "light"

    async def test_state_migration_workflow(self, state_service):
        """Test state migration workflow."""
        old_session = "old_session_123"
        new_session = "new_session_456"

        # Step 1: Create session with state
        await state_service.thread_manager.create_thread(old_session)
        await state_service.session_manager.save_session_state(
            old_session,
            {
                "user_context": {"name": "Alice"},
                "conversation_history": ["Hello", "Hi there"],
                "active_tasks": ["task_1"],
            },
        )

        # Step 2: Send a message to create more state
        request = SendMessageRequest(
            session_id=old_session,
            content="One more message",
            task_type=TaskType.CONVERSATION,
        )
        response = await state_service.send_message(request)
        assert response.success == True

        # Step 3: Migrate session
        new_thread_id = await state_service.thread_manager.migrate_thread(
            old_session, new_session
        )
        assert new_thread_id is not None

        # Step 4: Verify migration
        # Check thread mapping
        assert (
            await state_service.thread_manager.get_langgraph_thread(new_session)
            == new_thread_id
        )

        # Check state migration
        migrated_state = await state_service.session_manager.load_session_state(
            new_session
        )
        assert migrated_state["user_context"]["name"] == "Alice"
        assert len(migrated_state.get("conversation_history", [])) == 3

        # Step 5: Continue with new session
        new_request = SendMessageRequest(
            session_id=new_session,
            content="Continued conversation",
            task_type=TaskType.CONVERSATION,
        )
        new_response = await state_service.send_message(new_request)
        assert new_response.success == True

        # Step 6: Verify final state
        final_state = await state_service.session_manager.load_session_state(
            new_session
        )
        assert len(final_state.get("conversation_history", [])) == 4

    async def test_state_cleanup_workflow(self, state_service):
        """Test state cleanup workflow."""
        # Step 1: Create multiple sessions
        sessions = [f"session_{i}" for i in range(5)]
        for session in sessions:
            await state_service.thread_manager.create_thread(session)
            await state_service.session_manager.save_session_state(
                session, {"test": f"data_{session}"}
            )

        # Step 2: Verify sessions exist
        for session in sessions:
            state = await state_service.session_manager.load_session_state(session)
            assert state is not None

        # Step 3: Clean up old sessions
        cleaned_count = await state_service.session_manager.cleanup_old_states(
            max_age_days=0
        )
        assert cleaned_count == 5

        # Step 4: Verify cleanup
        for session in sessions:
            state = await state_service.session_manager.load_session_state(session)
            assert state is None


class TestMultiStepWorkflow:
    """Test multi-step workflows and task chaining."""

    @pytest.fixture
    def multi_step_service(self, mock_runtime_adapter, thread_manager, session_manager):
        """Service for multi-step workflows."""
        return AgentUIService(
            runtime_adapter=mock_runtime_adapter,
            thread_manager=thread_manager,
            session_manager=session_manager,
        )

    async def test_task_chaining_workflow(self, multi_step_service):
        """Test task chaining workflow."""
        session_id = "test_session_123"

        # Step 1: Initialize session
        await multi_step_service.thread_manager.create_thread(session_id)
        await multi_step_service.session_manager.save_session_state(
            session_id, {"workflow_state": {"step": 0, "results": []}}
        )

        # Step 2: Define chained tasks
        chain_steps = [
            {
                "task": "Analyze requirements",
                "type": TaskType.ANALYSIS,
                "input": "User wants to refactor authentication system",
            },
            {
                "task": "Design new architecture",
                "type": TaskType.CODE_REFACTOR,
                "input": "Based on analysis results",
            },
            {
                "task": "Generate implementation",
                "type": TaskType.CODE_GENERATION,
                "input": "Based on design",
            },
            {
                "task": "Create documentation",
                "type": TaskType.DOCUMENTATION,
                "input": "Based on implementation",
            },
        ]

        # Step 3: Execute chained tasks
        workflow_state = await multi_step_service.session_manager.load_session_state(
            session_id
        )
        workflow_state["workflow_state"]["step"] = 0

        for i, step in enumerate(chain_steps):
            # Update workflow state
            workflow_state["workflow_state"]["step"] = i
            workflow_state["workflow_state"]["current_step"] = step["task"]
            await multi_step_service.session_manager.save_session_state(
                session_id, workflow_state
            )

            # Execute task
            request = SendMessageRequest(
                session_id=session_id,
                content=step["input"],
                task_type=step["type"],
                context={"workflow_step": i, "total_steps": len(chain_steps)},
            )

            response = await multi_step_service.send_message(request)
            assert response.success == True

            # Store result
            workflow_state["workflow_state"]["results"].append(
                {
                    "step": i,
                    "task": step["task"],
                    "task_id": response.task_id,
                    "status": TaskStatus.COMPLETED,
                }
            )
            await multi_step_service.session_manager.save_session_state(
                session_id, workflow_state
            )

        # Step 4: Verify workflow completion
        final_state = await multi_step_service.session_manager.load_session_state(
            session_id
        )
        assert final_state["workflow_state"]["step"] == len(chain_steps) - 1
        assert len(final_state["workflow_state"]["results"]) == len(chain_steps)

        # Step 5: Check thread usage
        thread_id = await multi_step_service.thread_manager.get_langgraph_thread(
            session_id
        )
        metadata = await multi_step_service.thread_manager.get_thread_metadata(
            thread_id
        )
        assert metadata["message_count"] == len(chain_steps)

    async def test_conditional_workflow(self, multi_step_service):
        """Test conditional workflow with branching."""
        session_id = "test_session_123"

        # Step 1: Initialize session
        await multi_step_service.thread_manager.create_thread(session_id)
        await multi_step_service.session_manager.save_session_state(
            session_id, {"workflow_state": {"branch": None, "completed_steps": []}}
        )

        # Step 2: Send conditional message
        request = SendMessageRequest(
            session_id=session_id,
            content="I need help with my code, but I'm not sure what type of help",
            task_type=TaskType.CONVERSATION,
            context={"workflow_type": "conditional"},
        )

        response = await multi_step_service.send_message(request)
        assert response.success == True

        # Step 3: Simulate conditional branching
        current_state = await multi_step_service.session_manager.load_session_state(
            session_id
        )

        # Simulate user choice - refactoring path
        if "refactor" in response.content.lower():
            current_state["workflow_state"]["branch"] = "refactoring"

            # Execute refactoring workflow
            refactoring_steps = [
                "Analyze current code structure",
                "Identify refactoring opportunities",
                "Implement refactoring",
                "Test refactored code",
            ]

            for step in refactoring_steps:
                step_request = SendMessageRequest(
                    session_id=session_id,
                    content=f"Refactoring step: {step}",
                    task_type=TaskType.CODE_REFACTOR,
                )
                step_response = await multi_step_service.send_message(step_request)
                assert step_response.success == True

                current_state["workflow_state"]["completed_steps"].append(step)
                await multi_step_service.session_manager.save_session_state(
                    session_id, current_state
                )

        # Step 4: Verify conditional workflow
        final_state = await multi_step_service.session_manager.load_session_state(
            session_id
        )
        assert final_state["workflow_state"]["branch"] == "refactoring"
        assert len(final_state["workflow_state"]["completed_steps"]) == 4

    async def test_iterative_workflow(self, multi_step_service):
        """Test iterative workflow with feedback loops."""
        session_id = "test_session_123"

        # Step 1: Initialize session
        await multi_step_service.thread_manager.create_thread(session_id)
        await multi_step_service.session_manager.save_session_state(
            session_id,
            {
                "iterative_state": {
                    "iteration": 0,
                    "max_iterations": 3,
                    "feedback": [],
                    "improvements": [],
                }
            },
        )

        # Step 2: Execute iterative process
        current_state = await multi_step_service.session_manager.load_session_state(
            session_id
        )

        for iteration in range(current_state["iterative_state"]["max_iterations"]):
            # Update iteration state
            current_state["iterative_state"]["iteration"] = iteration
            await multi_step_service.session_manager.save_session_state(
                session_id, current_state
            )

            # Execute iteration task
            request = SendMessageRequest(
                session_id=session_id,
                content=f"Iteration {iteration + 1}: Improve the code quality",
                task_type=TaskType.CODE_AUDIT,
                context={
                    "iteration": iteration + 1,
                    "max_iterations": current_state["iterative_state"][
                        "max_iterations"
                    ],
                },
            )

            response = await multi_step_service.send_message(request)
            assert response.success == True

            # Collect feedback
            feedback = f"Feedback from iteration {iteration + 1}: {response.content}"
            current_state["iterative_state"]["feedback"].append(feedback)

            # Apply improvements
            improvement = (
                f"Improvement from iteration {iteration + 1}: Enhanced code structure"
            )
            current_state["iterative_state"]["improvements"].append(improvement)

            await multi_step_service.session_manager.save_session_state(
                session_id, current_state
            )

        # Step 3: Verify iterative workflow
        final_state = await multi_step_service.session_manager.load_session_state(
            session_id
        )
        assert final_state["iterative_state"]["iteration"] == 2
        assert len(final_state["iterative_state"]["feedback"]) == 3
        assert len(final_state["iterative_state"]["improvements"]) == 3

        # Step 4: Generate final summary
        summary_request = SendMessageRequest(
            session_id=session_id,
            content="Generate final summary of all improvements",
            task_type=TaskType.DOCUMENTATION,
        )

        summary_response = await multi_step_service.send_message(summary_request)
        assert summary_response.success == True


class TestPerformanceWorkflows:
    """Test performance-related workflows."""

    @pytest.fixture
    def performance_service(
        self, mock_runtime_adapter, thread_manager, session_manager
    ):
        """Service for performance testing."""
        return AgentUIService(
            runtime_adapter=mock_runtime_adapter,
            thread_manager=thread_manager,
            session_manager=session_manager,
        )

    async def test_high_volume_workflow(self, performance_service):
        """Test high volume workflow."""
        session_id = "test_session_123"

        # Step 1: Initialize session
        await performance_service.thread_manager.create_thread(session_id)

        # Step 2: Process high volume of messages
        message_count = 100
        requests = [
            SendMessageRequest(
                session_id=session_id,
                content=f"High volume message {i}",
                task_type=TaskType.CONVERSATION,
            )
            for i in range(message_count)
        ]

        # Process requests in batches to avoid overwhelming
        batch_size = 10
        responses = []

        for i in range(0, len(requests), batch_size):
            batch = requests[i : i + batch_size]
            batch_responses = await asyncio.gather(
                *[performance_service.send_message(req) for req in batch]
            )
            responses.extend(batch_responses)

        # Step 3: Verify high volume processing
        assert len(responses) == message_count
        success_count = sum(1 for r in responses if r.success)
        assert success_count == message_count

        # Step 4: Verify system state
        thread_id = await performance_service.thread_manager.get_langgraph_thread(
            session_id
        )
        metadata = await performance_service.thread_manager.get_thread_metadata(
            thread_id
        )
        assert metadata["message_count"] == message_count

        task_history = performance_service.get_task_history(session_id)
        assert len(task_history) == message_count

    async def test_memory_efficient_workflow(self, performance_service):
        """Test memory efficient workflow."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        session_id = "test_session_123"

        # Step 1: Initialize session
        await performance_service.thread_manager.create_thread(session_id)

        # Step 2: Process messages with memory monitoring
        message_count = 50
        for i in range(message_count):
            request = SendMessageRequest(
                session_id=session_id,
                content=f"Memory efficient message {i}",
                task_type=TaskType.CONVERSATION,
            )

            response = await performance_service.send_message(request)
            assert response.success == True

            # Check memory usage periodically
            if i % 10 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                assert memory_increase < 50 * 1024 * 1024  # Less than 50MB increase

        # Step 3: Verify memory efficiency
        final_memory = process.memory_info().rss
        total_memory_increase = final_memory - initial_memory
        assert (
            total_memory_increase < 100 * 1024 * 1024
        )  # Less than 100MB total increase


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
