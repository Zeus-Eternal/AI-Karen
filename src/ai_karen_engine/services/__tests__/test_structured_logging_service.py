"""
Tests for Structured Logging Service

Requirements: 1.2, 8.5
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from ai_karen_engine.services.structured_logging_service import (
    StructuredLogger,
    StructuredLogEntry,
    LogLevel,
    LogCategory,
    set_correlation_id,
    get_correlation_id,
    generate_correlation_id,
    set_user_context,
    clear_context,
    get_structured_logger,
)


class TestStructuredLogEntry:
    """Test StructuredLogEntry class"""

    def test_to_json_basic(self):
        """Test basic JSON serialization"""
        entry = StructuredLogEntry(
            timestamp="2023-01-01T00:00:00Z",
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            message="Test message"
        )
        
        json_str = entry.to_json()
        data = json.loads(json_str)
        
        assert data["timestamp"] == "2023-01-01T00:00:00Z"
        assert data["level"] == "info"
        assert data["category"] == "system"
        assert data["message"] == "Test message"

    def test_to_json_with_metadata(self):
        """Test JSON serialization with metadata"""
        entry = StructuredLogEntry(
            timestamp="2023-01-01T00:00:00Z",
            level=LogLevel.ERROR,
            category=LogCategory.API,
            message="Test error",
            correlation_id="test-123",
            user_id="user-456",
            metadata={"key": "value", "number": 42}
        )
        
        json_str = entry.to_json()
        data = json.loads(json_str)
        
        assert data["correlation_id"] == "test-123"
        assert data["user_id"] == "user-456"
        assert data["metadata"]["key"] == "value"
        assert data["metadata"]["number"] == 42

    def test_to_json_excludes_none_values(self):
        """Test that None values are excluded from JSON"""
        entry = StructuredLogEntry(
            timestamp="2023-01-01T00:00:00Z",
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            message="Test message",
            correlation_id=None,
            user_id=None
        )
        
        json_str = entry.to_json()
        data = json.loads(json_str)
        
        assert "correlation_id" not in data
        assert "user_id" not in data


class TestStructuredLogger:
    """Test StructuredLogger class"""

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        with patch('ai_karen_engine.services.structured_logging_service.get_logger') as mock:
            mock_logger_instance = Mock()
            mock.return_value = mock_logger_instance
            mock_logger_instance.handlers = []
            yield mock_logger_instance

    def test_logger_initialization(self, mock_logger):
        """Test logger initialization"""
        logger = StructuredLogger("test-service", "test-component")
        
        assert logger.service_name == "test-service"
        assert logger.component_name == "test-component"

    def test_info_logging(self, mock_logger):
        """Test info level logging"""
        logger = StructuredLogger("test-service")
        
        logger.info("Test message", category=LogCategory.API, operation="test_op")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["level"] == "info"
        assert log_data["category"] == "api"
        assert log_data["message"] == "Test message"
        assert log_data["operation"] == "test_op"

    def test_error_logging_with_exception(self, mock_logger):
        """Test error logging with exception"""
        logger = StructuredLogger("test-service")
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            logger.error("Error occurred", error=e, operation="test_op")
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["level"] == "error"
        assert log_data["message"] == "Error occurred"
        assert log_data["error_type"] == "ValueError"
        assert log_data["error_details"]["message"] == "Test error"
        assert "stack_trace" in log_data

    def test_user_action_logging(self, mock_logger):
        """Test user action logging"""
        logger = StructuredLogger("test-service")
        
        logger.log_user_action("login", resource="dashboard", result="success")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["category"] == "user_action"
        assert log_data["operation"] == "user_action"
        assert log_data["metadata"]["action"] == "login"
        assert log_data["metadata"]["resource"] == "dashboard"
        assert log_data["metadata"]["result"] == "success"

    def test_api_request_logging(self, mock_logger):
        """Test API request logging"""
        logger = StructuredLogger("test-service")
        
        logger.log_api_request(
            method="GET",
            endpoint="/api/test",
            status_code=200,
            duration_ms=150.5,
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["category"] == "api"
        assert log_data["operation"] == "api_request"
        assert log_data["status_code"] == 200
        assert log_data["duration_ms"] == 150.5
        assert log_data["metadata"]["method"] == "GET"
        assert log_data["metadata"]["endpoint"] == "/api/test"

    def test_database_operation_logging(self, mock_logger):
        """Test database operation logging"""
        logger = StructuredLogger("test-service")
        
        logger.log_database_operation(
            operation="SELECT",
            table="users",
            duration_ms=25.0,
            affected_rows=5
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["category"] == "database"
        assert log_data["operation"] == "SELECT"
        assert log_data["duration_ms"] == 25.0
        assert log_data["metadata"]["table"] == "users"
        assert log_data["metadata"]["affected_rows"] == 5

    def test_llm_request_logging(self, mock_logger):
        """Test LLM request logging"""
        logger = StructuredLogger("test-service")
        
        logger.log_llm_request(
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            duration_ms=2000.0
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["category"] == "llm"
        assert log_data["operation"] == "llm_request"
        assert log_data["duration_ms"] == 2000.0
        assert log_data["metadata"]["provider"] == "openai"
        assert log_data["metadata"]["model"] == "gpt-4"
        assert log_data["metadata"]["prompt_tokens"] == 100

    def test_security_event_logging(self, mock_logger):
        """Test security event logging"""
        logger = StructuredLogger("test-service")
        
        logger.log_security_event(
            event_type="brute_force",
            severity="critical",
            details={"attempts": 5, "blocked": True},
            ip_address="192.168.1.100"
        )
        
        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["level"] == "critical"
        assert log_data["category"] == "security"
        assert log_data["operation"] == "security_event"
        assert log_data["metadata"]["event_type"] == "brute_force"
        assert log_data["metadata"]["severity"] == "critical"
        assert log_data["metadata"]["attempts"] == 5


class TestContextManagement:
    """Test context management functions"""

    def test_correlation_id_context(self):
        """Test correlation ID context management"""
        # Initially no correlation ID
        assert get_correlation_id() is None
        
        # Set correlation ID
        test_id = "test-correlation-123"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id
        
        # Clear context
        clear_context()
        assert get_correlation_id() is None

    def test_generate_correlation_id(self):
        """Test correlation ID generation"""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()
        
        assert id1 != id2
        assert len(id1) > 0
        assert len(id2) > 0

    def test_user_context(self):
        """Test user context management"""
        from ai_karen_engine.services.structured_logging_service import user_id_var, session_id_var
        
        # Initially no user context
        assert user_id_var.get() is None
        assert session_id_var.get() is None
        
        # Set user context
        set_user_context("user-123", "session-456")
        assert user_id_var.get() == "user-123"
        assert session_id_var.get() == "session-456"
        
        # Clear context
        clear_context()
        assert user_id_var.get() is None
        assert session_id_var.get() is None


class TestFactoryFunction:
    """Test factory function"""

    def test_get_structured_logger(self):
        """Test structured logger factory function"""
        logger = get_structured_logger("test-service", "test-component")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.service_name == "test-service"
        assert logger.component_name == "test-component"

    def test_get_structured_logger_without_component(self):
        """Test structured logger factory function without component"""
        logger = get_structured_logger("test-service")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.service_name == "test-service"
        assert logger.component_name is None