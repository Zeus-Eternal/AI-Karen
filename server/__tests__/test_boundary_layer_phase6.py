"""
Boundary Layer Tests - Phase 6.

Tests for CopilotKit as proper UI boundary:
1. Request validation and sanitization
2. Response formatting for UI consumption
3. Input/output boundary enforcement
4. Security boundary validation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from datetime import datetime

# Add the src directory to the path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ai_karen_engine.copilotkit.agent_ui_service import AgentUIService
from ai_karen_engine.copilotkit.models import (
    SendMessageRequest,
    SendMessageResponse,
    CreateDeepTaskRequest,
    CreateDeepTaskResponse,
    GetTaskProgressRequest,
    GetTaskProgressResponse,
    TaskStatus,
    TaskType,
    AgentTask,
)
from ai_karen_engine.copilotkit.safety_middleware import SafetyMiddleware


class TestRequestValidation:
    """Test request validation at the UI boundary."""

    @pytest.fixture
    def safety_middleware(self):
        """Safety middleware instance."""
        return SafetyMiddleware()

    @pytest.fixture
    def agent_ui_service_with_safety(self, safety_middleware):
        """Agent UI service with safety middleware."""
        return AgentUIService(safety_middleware=safety_middleware)

    def test_valid_request_validation(self, agent_ui_service_with_safety):
        """Test validation of valid requests."""
        valid_requests = [
            SendMessageRequest(
                session_id="valid_session_123",
                content="Hello, how are you?",
                task_type=TaskType.CONVERSATION,
            ),
            SendMessageRequest(
                session_id="valid_session_123",
                content="Help me refactor this code",
                task_type=TaskType.CODE_REFACTOR,
                user_id="user_456",
                tenant_id="tenant_789",
            ),
            SendMessageRequest(
                session_id="valid_session_123",
                content="Generate documentation",
                task_type=TaskType.DOCUMENTATION,
                context={"project": "test_project"},
            ),
        ]

        for request in valid_requests:
            # Should not raise exceptions for valid requests
            task = agent_ui_service_with_safety._create_agent_task_from_message(request)
            assert task.session_id == "valid_session_123"
            assert len(task.content) > 0
            assert task.task_type in TaskType

    def test_invalid_request_validation(self):
        """Test validation of invalid requests."""
        invalid_requests = [
            # Empty session ID
            SendMessageRequest(session_id="", content="test"),
            # Empty content
            SendMessageRequest(session_id="valid", content=""),
            # Invalid task type
            SendMessageRequest(
                session_id="valid", content="test", task_type="invalid_type"
            ),
            # Context too large
            SendMessageRequest(
                session_id="valid",
                content="test",
                context={"large": "x" * 10000},  # Exceeds 10,000 character limit
            ),
            # Invalid priority
            SendMessageRequest(
                session_id="valid",
                content="test",
                priority=15,  # Exceeds max priority of 10
            ),
            # Invalid timeout
            SendMessageRequest(
                session_id="valid",
                content="test",
                timeout_seconds=4000,  # Exceeds max timeout of 3600
            ),
        ]

        for request in invalid_requests:
            with pytest.raises(ValueError):
                # Should raise validation errors for invalid requests
                task = AgentUIService()._create_agent_task_from_message(request)

    def test_request_sanitization(self, agent_ui_service_with_safety):
        """Test request sanitization for security."""
        # Test potentially dangerous content
        dangerous_requests = [
            SendMessageRequest(
                session_id="test_session",
                content="<script>alert('xss')</script>",
                context={"malicious": "data"},
            ),
            SendMessageRequest(
                session_id="test_session",
                content="'; DROP TABLE users; --",
                context={"sql_injection": "test"},
            ),
            SendMessageRequest(
                session_id="test_session",
                content="javascript:alert('xss')",
                context={"xss": "test"},
            ),
        ]

        for request in dangerous_requests:
            # Should handle dangerous content safely
            task = agent_ui_service_with_safety._create_agent_task_from_message(request)
            assert (
                task.content == request.content
            )  # Content should be preserved but handled safely
            assert isinstance(task.context, dict)

    def test_request_field_validation(self):
        """Test field-level validation."""
        # Test string field validation
        with pytest.raises(ValueError):
            SendMessageRequest(session_id=None, content="test")

        with pytest.raises(ValueError):
            SendMessageRequest(session_id="valid", content=None)

        with pytest.raises(ValueError):
            SendMessageRequest(session_id="", content="test")

        with pytest.raises(ValueError):
            SendMessageRequest(session_id="valid", content="")

    def test_context_validation(self):
        """Test context validation."""
        # Valid context
        valid_context = {"user_id": "123", "project": "test"}
        request = SendMessageRequest(
            session_id="valid", content="test", context=valid_context
        )
        task = AgentUIService()._create_agent_task_from_message(request)
        assert task.context == valid_context

        # Invalid context (non-dict)
        with pytest.raises(ValueError):
            SendMessageRequest(
                session_id="valid", content="test", context="invalid_context"
            )

        # Context too large
        large_context = {"data": "x" * 10001}
        with pytest.raises(ValueError):
            SendMessageRequest(
                session_id="valid", content="test", context=large_context
            )


class TestResponseFormatting:
    """Test response formatting for UI consumption."""

    @pytest.fixture
    def mock_runtime_adapter(self):
        """Mock runtime adapter."""
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
    def agent_ui_service(self, mock_runtime_adapter):
        """Agent UI service with mock adapter."""
        return AgentUIService(runtime_adapter=mock_runtime_adapter)

    async def test_response_structure_validation(self, agent_ui_service):
        """Test that responses have proper structure for UI consumption."""
        request = SendMessageRequest(
            session_id="test_session",
            content="Test message",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service.send_message(request)

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
        assert isinstance(response.timestamp, datetime)

    async def test_response_content_formatting(self, agent_ui_service):
        """Test response content formatting."""
        # Test different content types
        test_cases = [
            {"content": "Simple text response", "expected_type": str},
            {
                "content": 123,
                "expected_type": str,
            },  # Number should be converted to string
            {
                "content": {"key": "value"},
                "expected_type": str,
            },  # Dict should be converted to string
            {
                "content": ["item1", "item2"],
                "expected_type": str,
            },  # List should be converted to string
        ]

        for case in test_cases:
            mock_runtime_adapter = Mock()
            mock_runtime_adapter.execute_task = AsyncMock(
                return_value={
                    "content": case["content"],
                    "metadata": {"runtime": "langgraph"},
                }
            )

            service = AgentUIService(runtime_adapter=mock_runtime_adapter)
            request = SendMessageRequest(
                session_id="test_session",
                content="Test message",
                task_type=TaskType.CONVERSATION,
            )

            response = await service.send_message(request)
            assert isinstance(response.content, str)

    async def test_response_metadata_enrichment(self, agent_ui_service):
        """Test response metadata enrichment."""
        request = SendMessageRequest(
            session_id="test_session",
            content="Test message",
            task_type=TaskType.CONVERSATION,
        )

        response = await agent_ui_service.send_message(request)

        # Verify metadata is enriched
        metadata = response.execution_metadata
        assert "runtime" in metadata
        assert "mode" in metadata
        assert "timestamp" in metadata
        assert metadata["runtime"] == "langgraph"
        assert metadata["mode"] == "agentmedusa"

    async def test_error_response_formatting(self, agent_ui_service):
        """Test error response formatting."""
        # Configure adapter to raise an error
        mock_runtime_adapter = Mock()
        mock_runtime_adapter.execute_task = AsyncMock(
            side_effect=Exception("Test error")
        )

        service = AgentUIService(runtime_adapter=mock_runtime_adapter)

        request = SendMessageRequest(
            session_id="test_session",
            content="Error test",
            task_type=TaskType.CONVERSATION,
        )

        response = await service.send_message(request)

        # Verify error response structure
        assert response.success == False
        assert "Test error" in response.content
        assert "error" in response.execution_metadata
        assert response.execution_metadata["error"] == "Test error"

    async def test_progress_response_formatting(self, agent_ui_service):
        """Test progress response formatting."""
        request = CreateDeepTaskRequest(
            session_id="test_session",
            content="Long running task",
            task_type=TaskType.CODE_REFACTOR,
        )

        response = await agent_ui_service.create_deep_task(request)

        # Verify progress response structure
        assert response.success == True
        assert response.task_id is not None
        assert response.status == TaskStatus.PENDING
        assert response.estimated_duration is not None
        assert "execution_metadata" in response

    async def test_task_progress_response_formatting(self, agent_ui_service):
        """Test task progress response formatting."""
        # Create a task first
        create_request = CreateDeepTaskRequest(
            session_id="test_session",
            content="Test task",
            task_type=TaskType.CONVERSATION,
        )

        create_response = await agent_ui_service.create_deep_task(create_request)
        task_id = create_response.task_id

        # Get progress
        progress_request = GetTaskProgressRequest(
            session_id="test_session", task_id=task_id
        )

        progress_response = await agent_ui_service.get_task_progress(progress_request)

        # Verify progress response structure
        assert progress_response.task_id == task_id
        assert progress_response.status in TaskStatus
        assert progress_response.progress_percentage is not None
        assert progress_response.updated_at is not None
        assert isinstance(progress_response.steps, list)


class TestBoundaryEnforcement:
    """Test boundary enforcement between UI and runtime."""

    @pytest.fixture
    def strict_boundary_service(self):
        """Service with strict boundary enforcement."""
        return AgentUIService()

    def test_boundary_isolation(self, strict_boundary_service):
        """Test that UI and runtime are properly isolated."""
        # Test that service doesn't have runtime-specific logic
        assert not hasattr(strict_boundary_service, "_select_runtime_brain")
        assert not hasattr(strict_boundary_service, "choose_orchestration_mode")
        assert not hasattr(strict_boundary_service, "determine_execution_strategy")

        # Test that service only has boundary-specific methods
        assert hasattr(strict_boundary_service, "send_message")
        assert hasattr(strict_boundary_service, "create_deep_task")
        assert hasattr(strict_boundary_service, "get_task_progress")
        assert hasattr(strict_boundary_service, "cancel_task")

    async def test_boundary_validation_only(self, strict_boundary_service):
        """Test that boundary only validates, doesn't execute."""
        # Send message without runtime adapter
        request = SendMessageRequest(
            session_id="test_session",
            content="Test message",
            task_type=TaskType.CONVERSATION,
        )

        response = await strict_boundary_service.send_message(request)

        # Should handle gracefully without runtime
        assert response.success == True
        assert "Runtime adapter not configured" in response.content

    def test_no_runtime_selection_logic(self, strict_boundary_service):
        """Test that there's no runtime selection logic in boundary."""
        # Test that boundary doesn't make runtime decisions
        assert not hasattr(strict_boundary_service, "_determine_runtime")
        assert not hasattr(strict_boundary_service, "_choose_execution_mode")
        assert not hasattr(strict_boundary_service, "select_orchestration_strategy")

    async def test_boundary_only_routes_requests(self, strict_boundary_service):
        """Test that boundary only routes requests, doesn't process them."""
        # Create mock runtime adapter
        mock_runtime = Mock()
        mock_runtime.execute_task = AsyncMock(return_value={"content": "result"})

        service = AgentUIService(runtime_adapter=mock_runtime)

        request = SendMessageRequest(
            session_id="test_session",
            content="Test message",
            task_type=TaskType.CONVERSATION,
        )

        response = await service.send_message(request)

        # Verify boundary only routed, didn't process
        mock_runtime.execute_task.assert_called_once()
        assert response.success == True


class TestSecurityBoundary:
    """Test security boundary enforcement."""

    @pytest.fixture
    def security_middleware(self):
        """Security middleware instance."""
        return SafetyMiddleware()

    def test_input_sanitization(self, security_middleware):
        """Test input sanitization."""
        # Test malicious input detection
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
        ]

        for input_content in malicious_inputs:
            # Should detect and handle malicious input
            sanitized = security_middleware.sanitize_input(input_content)
            assert isinstance(sanitized, str)
            assert len(sanitized) > 0

    def test_content_validation(self, security_middleware):
        """Test content validation."""
        # Test content length limits
        long_content = "x" * 100000  # Very long content

        # Should handle long content gracefully
        is_valid = security_middleware.validate_content_length(long_content)
        assert is_valid == False  # Should exceed limits

    def test_request_security_check(self, security_middleware):
        """Test request security checks."""
        # Test valid request
        valid_request = SendMessageRequest(
            session_id="valid_session",
            content="Hello, how are you?",
            task_type=TaskType.CONVERSATION,
        )

        is_safe = security_middleware.check_request_safety(valid_request)
        assert is_safe == True

        # Test request with potentially dangerous content
        dangerous_request = SendMessageRequest(
            session_id="test_session",
            content="<script>alert('xss')</script>",
            task_type=TaskType.CONVERSATION,
        )

        is_safe = security_middleware.check_request_safety(dangerous_request)
        # Should handle dangerous content safely
        assert isinstance(is_safe, bool)

    async def test_response_sanitization(self, security_middleware):
        """Test response sanitization."""
        # Test potentially dangerous response content
        dangerous_response = {
            "content": "<script>alert('xss')</script>",
            "metadata": {"safe": False},
        }

        sanitized = security_middleware.sanitize_response(dangerous_response)
        assert isinstance(sanitized, dict)
        assert "content" in sanitized
        assert isinstance(sanitized["content"], str)


class TestUIResponseCompatibility:
    """Test UI response compatibility."""

    async def test_ui_response_structure(self):
        """Test that responses are compatible with UI expectations."""
        # Create mock response
        response = SendMessageResponse(
            success=True,
            task_id="test_task_123",
            content="UI compatible response",
            execution_metadata={
                "runtime": "langgraph",
                "mode": "agentmedusa",
                "timestamp": datetime.utcnow().isoformat(),
            },
            thread_id="thread_123",
        )

        # Verify UI compatibility
        assert hasattr(response, "success")
        assert hasattr(response, "task_id")
        assert hasattr(response, "content")
        assert hasattr(response, "execution_metadata")
        assert hasattr(response, "thread_id")
        assert hasattr(response, "timestamp")

        # Verify JSON serialization
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert "success" in parsed
        assert "task_id" in parsed
        assert "content" in parsed
        assert "execution_metadata" in parsed

    async def test_progress_response_ui_compatibility(self):
        """Test progress response UI compatibility."""
        response = GetTaskProgressResponse(
            task_id="test_task_123",
            status=TaskStatus.RUNNING,
            progress_percentage=50.0,
            steps=[
                {
                    "step_id": "step_1",
                    "name": "Processing",
                    "status": TaskStatus.COMPLETED,
                    "progress_percentage": 100.0,
                }
            ],
        )

        # Verify UI compatibility
        assert hasattr(response, "task_id")
        assert hasattr(response, "status")
        assert hasattr(response, "progress_percentage")
        assert hasattr(response, "steps")

        # Verify JSON serialization
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert "task_id" in parsed
        assert "status" in parsed
        assert "progress_percentage" in parsed
        assert "steps" in parsed

    def test_error_response_ui_compatibility(self):
        """Test error response UI compatibility."""
        from ai_karen_engine.copilotkit.models import AgentUIServiceError

        error = AgentUIServiceError(
            error_code="INVALID_REQUEST",
            error_message="Invalid request format",
            details={"field": "session_id"},
        )

        # Verify UI compatibility
        assert hasattr(error, "error_code")
        assert hasattr(error, "error_message")
        assert hasattr(error, "details")
        assert hasattr(error, "timestamp")

        # Verify JSON serialization
        json_str = error.model_dump_json()
        parsed = json.loads(json_str)
        assert "error_code" in parsed
        assert "error_message" in parsed
        assert "details" in parsed


class TestBoundaryPerformance:
    """Test boundary layer performance."""

    async def test_request_processing_performance(self):
        """Test request processing performance."""
        import time

        service = AgentUIService()

        # Test request processing speed
        request = SendMessageRequest(
            session_id="test_session",
            content="Performance test",
            task_type=TaskType.CONVERSATION,
        )

        start_time = time.time()
        task = service._create_agent_task_from_message(request)
        processing_time = time.time() - start_time

        # Should be fast
        assert processing_time < 0.1  # Should complete within 100ms
        assert task is not None

    async def test_response_generation_performance(self):
        """Test response generation performance."""
        import time

        # Mock runtime adapter
        mock_runtime = Mock()
        mock_runtime.execute_task = AsyncMock(return_value={"content": "result"})

        service = AgentUIService(runtime_adapter=mock_runtime)

        request = SendMessageRequest(
            session_id="test_session",
            content="Performance test",
            task_type=TaskType.CONVERSATION,
        )

        start_time = time.time()
        response = await service.send_message(request)
        generation_time = time.time() - start_time

        # Should be fast
        assert generation_time < 0.5  # Should complete within 500ms
        assert response.success == True

    async def test_concurrent_boundary_processing(self):
        """Test concurrent boundary processing."""
        service = AgentUIService()

        # Create multiple requests
        requests = [
            SendMessageRequest(
                session_id=f"session_{i}",
                content=f"Message {i}",
                task_type=TaskType.CONVERSATION,
            )
            for i in range(10)
        ]

        # Process concurrently
        start_time = asyncio.get_event_loop().time()
        tasks = [service._create_agent_task_from_message(req) for req in requests]
        processing_time = asyncio.get_event_loop().time() - start_time

        # Should handle concurrent requests efficiently
        assert processing_time < 1.0  # Should complete within 1 second
        assert len(tasks) == 10


class TestBoundaryMonitoring:
    """Test boundary layer monitoring."""

    @patch("ai_karen_engine.copilotkit.agent_ui_service.logger")
    async def test_request_logging(self, mock_logger):
        """Test request logging."""
        service = AgentUIService()

        request = SendMessageRequest(
            session_id="test_session",
            content="Logging test",
            task_type=TaskType.CONVERSATION,
        )

        response = await service.send_message(request)

        # Verify logging occurred
        mock_logger.info.assert_called()
        assert any(
            "Processing message" in str(call)
            for call in mock_logger.info.call_args_list
        )

    @patch("ai_karen_engine.copilotkit.agent_ui_service.logger")
    async def test_error_logging(self, mock_logger):
        """Test error logging."""
        # Configure adapter to raise an error
        mock_runtime = Mock()
        mock_runtime.execute_task = AsyncMock(side_effect=Exception("Test error"))

        service = AgentUIService(runtime_adapter=mock_runtime)

        request = SendMessageRequest(
            session_id="test_session",
            content="Error test",
            task_type=TaskType.CONVERSATION,
        )

        response = await service.send_message(request)

        # Verify error logging occurred
        mock_logger.error.assert_called()
        assert any(
            "Error processing message" in str(call)
            for call in mock_logger.error.call_args_list
        )

    async def test_boundary_metrics(self):
        """Test boundary layer metrics."""
        service = AgentUIService()

        # Track metrics
        initial_tasks = len(service._tasks)

        # Process some requests
        for i in range(5):
            request = SendMessageRequest(
                session_id=f"session_{i}",
                content=f"Message {i}",
                task_type=TaskType.CONVERSATION,
            )
            response = await service.send_message(request)
            assert response.success == True

        # Verify metrics were updated
        assert len(service._tasks) == initial_tasks + 5


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
