"""
Tests for core infrastructure components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from ai_karen_engine.core.services import (
    BaseService, ServiceConfig, ServiceStatus, ServiceContainer, get_container
)
from ai_karen_engine.core.errors import (
    KarenError, ValidationError, ErrorHandler, ErrorCode
)
from ai_karen_engine.core.logging import get_logger, LogLevel
from ai_karen_engine.core.gateway import create_app


class TestService(BaseService):
    """Test service implementation."""
    
    async def initialize(self):
        """Initialize test service."""
        pass
    
    async def start(self):
        """Start test service."""
        pass
    
    async def stop(self):
        """Stop test service."""
        pass
    
    async def health_check(self):
        """Health check for test service."""
        return True


class TestServiceInfrastructure:
    """Test service infrastructure components."""
    
    def test_service_config_creation(self):
        """Test service configuration creation."""
        config = ServiceConfig(
            name="test_service",
            enabled=True,
            dependencies=["dep1", "dep2"],
            config={"key": "value"}
        )
        
        assert config.name == "test_service"
        assert config.enabled is True
        assert config.dependencies == ["dep1", "dep2"]
        assert config.config == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_base_service_lifecycle(self):
        """Test base service lifecycle."""
        config = ServiceConfig(name="test_service")
        service = TestService(config)
        
        assert service.name == "test_service"
        assert service.status == ServiceStatus.INITIALIZING
        
        # Test startup
        await service.startup()
        assert service.status == ServiceStatus.RUNNING
        
        # Test shutdown
        await service.shutdown()
        assert service.status == ServiceStatus.STOPPED
    
    def test_service_container_registration(self):
        """Test service container registration."""
        container = ServiceContainer()
        config = ServiceConfig(name="test_service")
        
        container.register_service("test_service", TestService, config)
        
        # Get service instance
        service = container.get_service("test_service")
        assert isinstance(service, TestService)
        assert service.name == "test_service"
    
    def test_service_container_dependency_resolution(self):
        """Test dependency resolution."""
        container = ServiceContainer()
        
        # Register services with dependencies
        config1 = ServiceConfig(name="service1", dependencies=[])
        config2 = ServiceConfig(name="service2", dependencies=["service1"])
        
        container.register_service("service1", TestService, config1)
        container.register_service("service2", TestService, config2)
        
        # Get startup order
        startup_order = container.get_startup_order()
        assert startup_order.index("service1") < startup_order.index("service2")
    
    @pytest.mark.asyncio
    async def test_service_container_startup_shutdown(self):
        """Test service container startup and shutdown."""
        container = ServiceContainer()
        config = ServiceConfig(name="test_service")
        
        container.register_service("test_service", TestService, config)
        
        # Test startup
        await container.start_all_services()
        service = container.get_service("test_service")
        assert service.status == ServiceStatus.RUNNING
        
        # Test shutdown
        await container.stop_all_services()
        assert service.status == ServiceStatus.STOPPED


class TestErrorHandling:
    """Test error handling components."""
    
    def test_karen_error_creation(self):
        """Test KarenError creation."""
        error = KarenError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError(
            message="Invalid field",
            field="test_field",
            value="invalid_value"
        )
        
        assert error.message == "Invalid field"
        assert error.field == "test_field"
        assert error.value == "invalid_value"
        assert error.error_code == "VALIDATION_ERROR"
    
    def test_error_handler_karen_error(self):
        """Test error handler with KarenError."""
        handler = ErrorHandler()
        error = ValidationError("Test validation error")
        
        response = handler.handle_exception(error)
        
        assert response.error_code == ErrorCode.VALIDATION_ERROR
        assert response.message == "Test validation error"
        assert response.request_id is not None
        assert response.timestamp is not None
    
    def test_error_handler_unknown_error(self):
        """Test error handler with unknown error."""
        handler = ErrorHandler()
        error = ValueError("Test value error")
        
        response = handler.handle_exception(error)
        
        assert response.error_code == ErrorCode.VALIDATION_ERROR
        assert response.message == "Test value error"
    
    def test_error_handler_http_status_codes(self):
        """Test HTTP status code mapping."""
        handler = ErrorHandler()
        
        assert handler.get_http_status_code(ErrorCode.VALIDATION_ERROR) == 400
        assert handler.get_http_status_code(ErrorCode.AUTHENTICATION_ERROR) == 401
        assert handler.get_http_status_code(ErrorCode.AUTHORIZATION_ERROR) == 403
        assert handler.get_http_status_code(ErrorCode.NOT_FOUND) == 404
        assert handler.get_http_status_code(ErrorCode.INTERNAL_ERROR) == 500


class TestLogging:
    """Test logging components."""
    
    def test_logger_creation(self):
        """Test logger creation."""
        logger = get_logger("test_logger", LogLevel.DEBUG)
        
        assert logger.name == "test_logger"
        assert logger.logger.level == 10  # DEBUG level
    
    def test_logger_context(self):
        """Test logger context management."""
        logger = get_logger("test_logger")
        
        # Set context
        logger.set_context(user_id="123", session_id="abc")
        assert logger._context == {"user_id": "123", "session_id": "abc"}
        
        # Remove context
        logger.remove_context("user_id")
        assert logger._context == {"session_id": "abc"}
        
        # Clear context
        logger.clear_context()
        assert logger._context == {}


class TestGateway:
    """Test FastAPI gateway components."""
    
    def test_app_creation(self):
        """Test FastAPI app creation."""
        app = create_app(
            title="Test App",
            description="Test Description",
            version="1.0.0",
            debug=True
        )
        
        # Basic checks - the app should be created without errors
        assert app is not None
        
        # Check if app has basic attributes
        assert hasattr(app, 'routes')
        assert hasattr(app, 'get')
        assert hasattr(app, 'post')


# Integration test
class TestIntegration:
    """Integration tests for core infrastructure."""
    
    @pytest.mark.asyncio
    async def test_full_integration(self):
        """Test full integration of core components."""
        # Create service container
        container = ServiceContainer()
        
        # Register test service
        config = ServiceConfig(name="integration_test_service")
        container.register_service("integration_test_service", TestService, config)
        
        # Start services
        await container.start_all_services()
        
        # Verify service is running
        service = container.get_service("integration_test_service")
        assert service.status == ServiceStatus.RUNNING
        
        # Test error handling
        handler = ErrorHandler()
        error = ValidationError("Integration test error")
        response = handler.handle_exception(error)
        assert response.error_code == ErrorCode.VALIDATION_ERROR
        
        # Test logging
        logger = get_logger("integration_test")
        logger.info("Integration test log message")
        
        # Stop services
        await container.stop_all_services()
        assert service.status == ServiceStatus.STOPPED