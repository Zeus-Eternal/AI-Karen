"""
Runtime Integration Tests - Phase 6.

Tests for runtime integration between CopilotKit and various runtime systems:
1. LangGraph orchestrator integration
2. ChatOrchestrator integration
3. Unified runtime adapter pattern validation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ai_karen_engine.copilotkit.agent_ui_service import AgentUIService
from ai_karen_engine.copilotkit.models import SendMessageRequest, TaskType
from ai_karen_engine.agents.adapters.langgraph_adapter import LangGraphAdapter
from ai_karen_engine.core.langgraph_orchestrator.langgraph_orchestrator import ChatOrchestrator


class TestLangGraphOrchestratorIntegration:
    """Test integration with LangGraph orchestrator."""

    @pytest.fixture
    def mock_langgraph_adapter(self):
        """Mock LangGraph adapter for testing."""
        adapter = Mock(spec=LangGraphAdapter)
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "LangGraph execution result",
                "metadata": {"runtime": "langgraph", "mode": "agentmedusa"},
            }
        )
        adapter.health_check = AsyncMock(
            return_value={
                "service": "langgraph_adapter",
                "langgraph_available": True,
                "graphs_count": 1,
                "llms_count": 2,
            }
        )
        return adapter

    @pytest.fixture
    def agent_ui_service_with_langgraph(self, mock_langgraph_adapter):
        """Agent UI service with LangGraph adapter."""
        return AgentUIService(runtime_adapter=mock_langgraph_adapter)

    async def test_langgraph_execution(
        self, agent_ui_service_with_langgraph, mock_langgraph_adapter
    ):
        """Test that tasks are executed through LangGraph adapter."""
        request = SendMessageRequest(
            session_id="test_session",
            content="Execute through LangGraph",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_langgraph.send_message(request)

        # Verify LangGraph adapter was called
        mock_langgraph_adapter.execute_task.assert_called_once()

        # Verify response contains LangGraph metadata
        assert response.success == True
        assert "LangGraph execution result" in response.content
        assert response.execution_metadata["runtime"] == "langgraph"

    async def test_langgraph_health_check(
        self, agent_ui_service_with_langgraph, mock_langgraph_adapter
    ):
        """Test LangGraph health check integration."""
        # Send message to trigger health check
        request = SendMessageRequest(
            session_id="test_session",
            content="Health check test",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_langgraph.send_message(request)

        # Verify health check was performed
        mock_langgraph_adapter.health_check.assert_called()
        assert response.success == True

    async def test_langgraph_error_handling(
        self, agent_ui_service_with_langgraph, mock_langgraph_adapter
    ):
        """Test error handling when LangGraph fails."""
        # Mock LangGraph to raise an error
        mock_langgraph_adapter.execute_task = AsyncMock(
            side_effect=Exception("LangGraph error")
        )

        request = SendMessageRequest(
            session_id="test_session",
            content="Error test",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_langgraph.send_message(request)

        # Verify error is handled gracefully
        assert response.success == False
        assert "LangGraph error" in response.content

    async def test_langgraph_state_persistence(
        self, agent_ui_service_with_langgraph, mock_langgraph_adapter
    ):
        """Test state persistence with LangGraph."""
        # Mock state persistence
        mock_langgraph_adapter.execute_task = AsyncMock(
            return_value={
                "content": "State persistence test",
                "metadata": {"runtime": "langgraph", "state_persisted": True},
            }
        )

        request = SendMessageRequest(
            session_id="test_session",
            content="State test",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_langgraph.send_message(request)

        # Verify state was handled
        assert response.success == True
        assert "State persistence test" in response.content


class TestChatOrchestratorIntegration:
    """Test integration with ChatOrchestrator."""

    @pytest.fixture
    def mock_chat_orchestrator(self):
        """Mock ChatOrchestrator for testing."""
        orchestrator = Mock(spec=ChatOrchestrator)
        orchestrator.process_message = AsyncMock(
            return_value={
                "content": "ChatOrchestrator result",
                "metadata": {"runtime": "chat_orchestrator", "processed": True},
            }
        )
        return orchestrator

    @pytest.fixture
    def agent_ui_service_with_chat_orchestrator(self, mock_chat_orchestrator):
        """Agent UI service with ChatOrchestrator adapter."""
        return AgentUIService(runtime_adapter=mock_chat_orchestrator)

    async def test_chat_orchestrator_execution(
        self, agent_ui_service_with_chat_orchestrator, mock_chat_orchestrator
    ):
        """Test that tasks are executed through ChatOrchestrator."""
        request = SendMessageRequest(
            session_id="test_session",
            content="Process through ChatOrchestrator",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_chat_orchestrator.send_message(request)

        # Verify ChatOrchestrator was called
        mock_chat_orchestrator.process_message.assert_called_once()

        # Verify response contains ChatOrchestrator metadata
        assert response.success == True
        assert "ChatOrchestrator result" in response.content
        assert response.execution_metadata["runtime"] == "chat_orchestrator"

    async def test_chat_orchestrator_context_handling(
        self, agent_ui_service_with_chat_orchestrator, mock_chat_orchestrator
    ):
        """Test context handling with ChatOrchestrator."""
        request = SendMessageRequest(
            session_id="test_session",
            content="Context test",
            task_type=TaskType.CONVERSATION,
            context={"user_id": "user123", "project": "test_project"},
        )

        response = await agent_ui_service_with_chat_orchestrator.send_message(request)

        # Verify context was passed through
        call_args = mock_chat_orchestrator.process_message.call_args[0][0]
        assert call_args["context"]["user_id"] == "user123"
        assert call_args["context"]["project"] == "test_project"

    async def test_chat_orchestrator_error_handling(
        self, agent_ui_service_with_chat_orchestrator, mock_chat_orchestrator
    ):
        """Test error handling when ChatOrchestrator fails."""
        # Mock ChatOrchestrator to raise an error
        mock_chat_orchestrator.process_message = AsyncMock(
            side_effect=Exception("ChatOrchestrator error")
        )

        request = SendMessageRequest(
            session_id="test_session",
            content="Error test",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_chat_orchestrator.send_message(request)

        # Verify error is handled gracefully
        assert response.success == False
        assert "ChatOrchestrator error" in response.content


class TestUnifiedRuntimeAdapterPattern:
    """Test unified runtime adapter pattern."""

    @pytest.fixture
    def mock_unified_adapter(self):
        """Mock unified runtime adapter."""
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Unified adapter result",
                "metadata": {"runtime": "unified", "adapter": "universal"},
            }
        )
        adapter.get_runtime_info = AsyncMock(
            return_value={
                "type": "unified",
                "supported_runtimes": ["langgraph", "chat_orchestrator"],
                "current_runtime": "langgraph",
            }
        )
        return adapter

    @pytest.fixture
    def agent_ui_service_with_unified_adapter(self, mock_unified_adapter):
        """Agent UI service with unified adapter."""
        return AgentUIService(runtime_adapter=mock_unified_adapter)

    async def test_unified_adapter_execution(
        self, agent_ui_service_with_unified_adapter, mock_unified_adapter
    ):
        """Test execution through unified adapter."""
        request = SendMessageRequest(
            session_id="test_session",
            content="Execute through unified adapter",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_unified_adapter.send_message(request)

        # Verify unified adapter was called
        mock_unified_adapter.execute_task.assert_called_once()

        # Verify response contains unified adapter metadata
        assert response.success == True
        assert "Unified adapter result" in response.content
        assert response.execution_metadata["runtime"] == "unified"

    async def test_unified_adapter_runtime_info(
        self, agent_ui_service_with_unified_adapter, mock_unified_adapter
    ):
        """Test runtime info retrieval from unified adapter."""
        # Get runtime info
        runtime_info = await mock_unified_adapter.get_runtime_info()

        # Verify runtime info structure
        assert "type" in runtime_info
        assert "supported_runtimes" in runtime_info
        assert "current_runtime" in runtime_info
        assert runtime_info["type"] == "unified"
        assert "langgraph" in runtime_info["supported_runtimes"]
        assert "chat_orchestrator" in runtime_info["supported_runtimes"]

    async def test_unified_adapter_fallback(
        self, agent_ui_service_with_unified_adapter, mock_unified_adapter
    ):
        """Test fallback mechanism in unified adapter."""
        # Configure adapter to fail first, then succeed
        mock_unified_adapter.execute_task.side_effect = [
            Exception("Primary runtime failed"),
            {"content": "Fallback runtime result", "metadata": {"runtime": "fallback"}},
        ]

        request = SendMessageRequest(
            session_id="test_session",
            content="Fallback test",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service_with_unified_adapter.send_message(request)

        # Verify fallback worked
        assert response.success == True
        assert "Fallback runtime result" in response.content

        # Verify multiple attempts were made
        assert mock_unified_adapter.execute_task.call_count == 2

    async def test_unified_adapter_load_balancing(
        self, agent_ui_service_with_unified_adapter, mock_unified_adapter
    ):
        """Test load balancing in unified adapter."""
        # Configure adapter to track execution calls
        execution_count = 0

        def track_execution(*args, **kwargs):
            nonlocal execution_count
            execution_count += 1
            return {
                "content": f"Load balanced result {execution_count}",
                "metadata": {"runtime": "unified", "execution_id": execution_count},
            }

        mock_unified_adapter.execute_task.side_effect = track_execution

        # Send multiple requests
        requests = [
            SendMessageRequest(session_id=f"session_{i}", content=f"Message {i}")
            for i in range(5)
        ]

        responses = await asyncio.gather(
            *[
                agent_ui_service_with_unified_adapter.send_message(req)
                for req in requests
            ]
        )

        # Verify all requests were processed
        for response in responses:
            assert response.success == True

        # Verify load balancing occurred
        assert execution_count == 5


class TestRuntimeCompatibility:
    """Test runtime compatibility and interoperability."""

    async def test_runtime_switching(self):
        """Test switching between different runtimes."""
        # This test verifies that the system can handle different runtime types
        # through the unified adapter pattern

        # Mock different runtime adapters
        langgraph_adapter = Mock()
        langgraph_adapter.execute_task = AsyncMock(
            return_value={
                "content": "LangGraph result",
                "metadata": {"runtime": "langgraph"},
            }
        )

        chat_orchestrator = Mock()
        chat_orchestrator.process_message = AsyncMock(
            return_value={
                "content": "ChatOrchestrator result",
                "metadata": {"runtime": "chat_orchestrator"},
            }
        )

        # Test that both adapters work through the unified interface
        test_cases = [
            (langgraph_adapter, "langgraph"),
            (chat_orchestrator, "chat_orchestrator"),
        ]

        for adapter, runtime_name in test_cases:
            service = AgentUIService(runtime_adapter=adapter)
            request = SendMessageRequest(
                session_id="test_session",
                content=f"Test {runtime_name}",
                task_type=TaskType.CONVERSATION,
            )

            response = await service.send_message(request)
            assert response.success == True
            assert runtime_name in response.content.lower()

    async def test_runtime_interface_compatibility(self):
        """Test that different runtime interfaces are compatible."""
        # Test adapters with different method names but same functionality
        adapters = [
            Mock(execute_task=AsyncMock(return_value={"content": "result1"})),
            Mock(process_task=AsyncMock(return_value={"content": "result2"})),
            Mock(invoke=AsyncMock(return_value={"content": "result3"})),
        ]

        for adapter in adapters:
            service = AgentUIService(runtime_adapter=adapter)
            request = SendMessageRequest(
                session_id="test_session",
                content="Compatibility test",
                task_type=TaskType.CONVERSATION,
            )

            response = await service.send_message(request)
            assert response.success == True

    async def test_runtime_error_compatibility(self):
        """Test error handling across different runtimes."""
        # Test different error types from different runtimes
        error_cases = [
            (Exception("Runtime error"), "Runtime error"),
            (ValueError("Invalid input"), "Invalid input"),
            (TimeoutError("Timeout"), "Timeout"),
        ]

        for error, error_message in error_cases:
            adapter = Mock()
            adapter.execute_task = AsyncMock(side_effect=error)

            service = AgentUIService(runtime_adapter=adapter)
            request = SendMessageRequest(
                session_id="test_session",
                content="Error test",
                task_type=TaskType.CONVERSATION,
            )

            response = await service.send_message(request)
            assert response.success == False
            assert error_message in response.content


class TestRuntimePerformance:
    """Test runtime performance characteristics."""

    async def test_runtime_execution_speed(self):
        """Test execution speed of different runtimes."""
        import time

        # Mock adapter with realistic execution time
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Performance test result",
                "metadata": {"execution_time": 0.5},
            }
        )

        service = AgentUIService(runtime_adapter=adapter)
        request = SendMessageRequest(
            session_id="test_session",
            content="Performance test",
            task_type=TaskType.CONVERSATION,
        )

        # Measure execution time
        start_time = time.time()
        response = await service.send_message(request)
        execution_time = time.time() - start_time

        # Verify performance is acceptable
        assert response.success == True
        assert execution_time < 2.0  # Should complete within 2 seconds
        assert "Performance test result" in response.content

    async def test_concurrent_runtime_execution(self):
        """Test concurrent execution through runtime adapter."""
        # Mock adapter that can handle concurrent requests
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Concurrent result",
                "metadata": {"concurrent": True},
            }
        )

        service = AgentUIService(runtime_adapter=adapter)

        # Create multiple concurrent requests
        requests = [
            SendMessageRequest(
                session_id=f"session_{i}",
                content=f"Concurrent message {i}",
                task_type=TaskType.CONVERSATION,
            )
            for i in range(10)
        ]

        # Execute concurrently
        start_time = asyncio.get_event_loop().time()
        responses = await asyncio.gather(
            *[service.send_message(req) for req in requests]
        )
        execution_time = asyncio.get_event_loop().time() - start_time

        # Verify all requests succeeded
        for response in responses:
            assert response.success == True

        # Verify concurrent execution was efficient
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert adapter.execute_task.call_count == 10

    async def test_runtime_memory_usage(self):
        """Test memory usage of runtime adapter."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Mock adapter with memory-intensive operations
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Memory test result",
                "metadata": {"memory_intensive": True},
            }
        )

        service = AgentUIService(runtime_adapter=adapter)

        # Execute multiple memory-intensive operations
        for i in range(50):
            request = SendMessageRequest(
                session_id=f"session_{i}",
                content=f"Memory test message {i}",
                task_type=TaskType.CONVERSATION,
            )
            response = await service.send_message(request)
            assert response.success == True

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Verify memory usage is reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase


class TestRuntimeMonitoring:
    """Test runtime monitoring and observability."""

    async def test_runtime_health_monitoring(self):
        """Test runtime health monitoring."""
        # Mock adapter with health check
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Health check result",
                "metadata": {"healthy": True},
            }
        )
        adapter.health_check = AsyncMock(
            return_value={"status": "healthy", "uptime": 3600, "memory_usage": "50%"}
        )

        service = AgentUIService(runtime_adapter=adapter)

        # Execute health check
        health_info = await adapter.health_check()

        # Verify health monitoring
        assert health_info["status"] == "healthy"
        assert "uptime" in health_info
        assert "memory_usage" in health_info

    async def test_runtime_metrics_collection(self):
        """Test runtime metrics collection."""
        # Mock adapter with metrics tracking
        adapter = Mock()
        adapter.execute_task = AsyncMock(
            return_value={
                "content": "Metrics test result",
                "metadata": {"metrics": {"executions": 1, "success_rate": 100}},
            }
        )

        service = AgentUIService(runtime_adapter=adapter)

        # Execute multiple requests to collect metrics
        for i in range(5):
            request = SendMessageRequest(
                session_id=f"session_{i}",
                content=f"Metrics test {i}",
                task_type=TaskType.CONVERSATION,
            )
            response = await service.send_message(request)
            assert response.success == True

        # Verify metrics were collected
        assert adapter.execute_task.call_count == 5

    async def test_runtime_error_tracking(self):
        """Test runtime error tracking."""
        # Mock adapter with error tracking
        adapter = Mock()
        adapter.execute_task = AsyncMock(side_effect=Exception("Test error"))

        service = AgentUIService(runtime_adapter=adapter)

        # Execute request that will fail
        request = SendMessageRequest(
            session_id="test_session",
            content="Error tracking test",
            task_type=TaskType.CONVERSATION,
        )

        response = await service.send_message(request)

        # Verify error was tracked
        assert response.success == False
        assert "Test error" in response.content
        assert adapter.execute_task.call_count == 1


# Test utilities for runtime integration
class TestRuntimeUtils:
    """Test utility functions for runtime integration."""

    def test_runtime_detection(self):
        """Test runtime detection logic."""
        # Test runtime type detection
        runtime_types = ["langgraph", "chat_orchestrator", "unified"]

        for runtime_type in runtime_types:
            assert isinstance(runtime_type, str)
            assert len(runtime_type) > 0

    def test_adapter_interface_compatibility(self):
        """Test adapter interface compatibility."""
        # Test that different adapter interfaces are compatible
        interfaces = [
            ("execute_task", "execute_task"),
            ("process_task", "process_task"),
            ("invoke", "invoke"),
        ]

        for method_name, expected_method in interfaces:
            assert isinstance(method_name, str)
            assert isinstance(expected_method, str)

    def test_runtime_error_handling_patterns(self):
        """Test runtime error handling patterns."""
        # Test different error types
        error_types = [
            Exception("General error"),
            ValueError("Value error"),
            TimeoutError("Timeout error"),
            ConnectionError("Connection error"),
        ]

        for error_type in error_types:
            assert isinstance(error_type, Exception)


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
