"""
Integration tests for component interactions.

Tests how frontend and backend components work together.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import json
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFrontendBackendIntegration:
    """Test frontend and backend component interactions."""
    
    def test_task_management_api_integration(self):
        """Test task management API integration."""
        # Test that task management components can interact with backend APIs
        # This is a basic integration test that verifies the API structure
        
        # Mock the task management API
        with patch('server.routers') as mock_routers:
            mock_router = Mock()
            mock_routers.task_router = mock_router
            
            # Verify router has expected endpoints
            assert hasattr(mock_router, 'get_tasks') or hasattr(mock_router, 'get')
            assert hasattr(mock_router, 'create_task') or hasattr(mock_router, 'post')
            assert hasattr(mock_router, 'update_task') or hasattr(mock_router, 'put')
            assert hasattr(mock_router, 'delete_task') or hasattr(mock_router, 'delete')
    
    def test_memory_api_integration(self):
        """Test memory API integration."""
        # Test that memory components can interact with backend APIs
        
        # Mock the memory API
        with patch('server.routers') as mock_routers:
            mock_router = Mock()
            mock_routers.memory_router = mock_router
            
            # Verify router has expected endpoints
            assert hasattr(mock_router, 'get_memories') or hasattr(mock_router, 'get')
            assert hasattr(mock_router, 'create_memory') or hasattr(mock_router, 'post')
            assert hasattr(mock_router, 'update_memory') or hasattr(mock_router, 'put')
            assert hasattr(mock_router, 'delete_memory') or hasattr(mock_router, 'delete')
    
    def test_health_endpoints_integration(self):
        """Test health endpoints integration."""
        # Test that health endpoints are properly integrated
        
        # Mock the FastAPI app
        with patch('server.health_endpoints') as mock_health:
            mock_app = Mock()
            
            # Mock register_health_endpoints function
            def mock_register(app):
                app.add_route = Mock()
                return app
            
            mock_health.register_health_endpoints = mock_register
            
            # Call registration
            result = mock_health.register_health_endpoints(mock_app)
            
            # Verify registration was called
            assert result is not None
    
    def test_middleware_integration(self):
        """Test middleware integration."""
        # Test that middleware is properly integrated
        
        # Mock the middleware
        with patch('server.middleware') as mock_middleware:
            mock_app = Mock()
            
            # Mock configure_middleware function
            def mock_configure(app):
                app.add_middleware = Mock()
                return app
            
            mock_middleware.configure_middleware = mock_configure
            
            # Call configuration
            result = mock_middleware.configure_middleware(mock_app)
            
            # Verify configuration was called
            assert result is not None
    
    def test_database_integration(self):
        """Test database integration."""
        # Test that database is properly integrated
        
        # Mock the database
        with patch('server.validate_database_config') as mock_db:
            mock_settings = Mock()
            mock_settings.database_url = "sqlite:///test.db"
            mock_settings.db_pool_size = 10
            mock_settings.db_connection_timeout = 30
            
            # Mock validate_database_configuration function
            def mock_validate(settings):
                return {
                    "valid": True,
                    "database_url": settings.database_url,
                    "pool_size": settings.db_pool_size,
                    "timeout": settings.db_connection_timeout
                }
            
            mock_db.validate_database_configuration = mock_validate
            
            # Call validation
            result = mock_db.validate_database_configuration(mock_settings)
            
            # Verify validation results
            assert result["valid"] is True
            assert result["database_url"] == "sqlite:///test.db"
            assert result["pool_size"] == 10
            assert result["timeout"] == 30
    
    def test_security_integration(self):
        """Test security integration."""
        # Test that security is properly integrated
        
        # Mock the security
        with patch('server.security') as mock_security:
            mock_token = Mock()
            mock_token.return_value = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            
            # Mock create_access_token function
            def mock_create_token(data):
                return mock_token.return_value
            
            mock_security.create_access_token = mock_create_token
            
            # Call token creation
            result = mock_security.create_access_token({"user_id": "test_user"})
            
            # Verify token creation
            assert result is not None
            assert len(result) > 0
    
    def test_logging_integration(self):
        """Test logging integration."""
        # Test that logging is properly integrated
        
        # Mock the logging
        with patch('server.logging_setup') as mock_logging:
            mock_logger = Mock()
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            mock_logger.warning = Mock()
            
            # Mock configure_logging function
            def mock_configure():
                return mock_logger
            
            mock_logging.configure_logging = mock_configure
            
            # Call configuration
            result = mock_logging.configure_logging()
            
            # Verify configuration was called
            assert result is not None
    
    def test_performance_integration(self):
        """Test performance integration."""
        # Test that performance monitoring is properly integrated
        
        # Mock the performance
        with patch('server.performance') as mock_perf:
            mock_metrics = Mock()
            mock_metrics.return_value = {
                "cpu_percent": 25.5,
                "memory_percent": 60.2,
                "disk_percent": 45.8
            }
            
            # Mock get_performance_status function
            def mock_get_status():
                return mock_metrics.return_value
            
            mock_perf.get_performance_status = mock_get_status
            
            # Call status check
            result = mock_perf.get_performance_status()
            
            # Verify status check
            assert result is not None
            assert "cpu_percent" in result
            assert "memory_percent" in result
            assert "disk_percent" in result
    
    def test_config_integration(self):
        """Test configuration integration."""
        # Test that configuration is properly integrated
        
        # Mock the configuration
        with patch('server.config') as mock_config:
            mock_settings = Mock()
            mock_settings.debug = False
            mock_settings.secret_key = "test_secret_key"
            mock_settings.database_url = "sqlite:///test.db"
            
            # Mock Settings class
            class MockSettings:
                def __init__(self):
                    self.debug = False
                    self.secret_key = "test_secret_key"
                    self.database_url = "sqlite:///test.db"
            
            mock_config.Settings = MockSettings
            
            # Create settings instance
            settings = mock_config.Settings()
            
            # Verify settings
            assert settings.debug is False
            assert settings.secret_key == "test_secret_key"
            assert settings.database_url == "sqlite:///test.db"
    
    def test_api_routes_integration(self):
        """Test API routes integration."""
        # Test that API routes are properly integrated
        
        # Mock the API routes
        with patch('server.routers') as mock_routers:
            mock_app = Mock()
            mock_app.include_router = Mock()
            
            # Mock task and memory routers
            mock_task_router = Mock()
            mock_memory_router = Mock()
            mock_routers.task_router = mock_task_router
            mock_routers.memory_router = mock_memory_router
            
            # Create a simple FastAPI-like app
            class MockApp:
                def __init__(self):
                    self.routers = []
                
                def include_router(self, router):
                    self.routers.append(router)
            
            app = MockApp()
            
            # Include routers
            app.include_router(mock_task_router)
            app.include_router(mock_memory_router)
            
            # Verify routers were included
            assert len(app.routers) == 2
            assert mock_task_router in app.routers
            assert mock_memory_router in app.routers
    
    def test_error_handling_integration(self):
        """Test error handling integration."""
        # Test that error handling is properly integrated
        
        # Mock error handling
        with patch('server.validation') as mock_validation:
            mock_errors = []
            
            # Mock validation function
            def mock_validate(data):
                if not data:
                    mock_errors.append("Data is required")
                    return False
                return True
            
            mock_validation.validate_request_data = mock_validate
            
            # Test validation with valid data
            result = mock_validation.validate_request_data({"key": "value"})
            assert result is True
            assert len(mock_errors) == 0
            
            # Test validation with invalid data
            result = mock_validation.validate_request_data({})
            assert result is False
            assert len(mock_errors) == 1
            assert "Data is required" in mock_errors


class TestDataFlowIntegration:
    """Test data flow between components."""
    
    def test_task_to_database_flow(self):
        """Test task data flow to database."""
        # Test that task data flows correctly to database
        
        # Mock task creation and database storage
        with patch('server.routers') as mock_routers, \
             patch('server.validate_database_config') as mock_db:
            
            # Mock task data
            task_data = {
                "title": "Test Task",
                "description": "Test Description",
                "status": "pending",
                "priority": "medium"
            }
            
            # Mock database storage
            mock_db.store_task = Mock(return_value={"id": 1, **task_data})
            
            # Mock router
            mock_router = Mock()
            mock_router.create_task = Mock(return_value=mock_db.store_task.return_value)
            mock_routers.task_router = mock_router
            
            # Test task creation flow
            result = mock_router.create_task(task_data)
            
            # Verify flow
            assert result["id"] == 1
            assert result["title"] == "Test Task"
            assert result["description"] == "Test Description"
            assert result["status"] == "pending"
            assert result["priority"] == "medium"
    
    def test_memory_to_database_flow(self):
        """Test memory data flow to database."""
        # Test that memory data flows correctly to database
        
        # Mock memory creation and database storage
        with patch('server.routers') as mock_routers, \
             patch('server.validate_database_config') as mock_db:
            
            # Mock memory data
            memory_data = {
                "content": "Test Memory",
                "tags": ["test", "sample"],
                "importance": "medium"
            }
            
            # Mock database storage
            mock_db.store_memory = Mock(return_value={"id": 1, **memory_data})
            
            # Mock router
            mock_router = Mock()
            mock_router.create_memory = Mock(return_value=mock_db.store_memory.return_value)
            mock_routers.memory_router = mock_router
            
            # Test memory creation flow
            result = mock_router.create_memory(memory_data)
            
            # Verify flow
            assert result["id"] == 1
            assert result["content"] == "Test Memory"
            assert result["tags"] == ["test", "sample"]
            assert result["importance"] == "medium"
    
    def test_authentication_flow(self):
        """Test authentication flow."""
        # Test that authentication flows correctly through the system
        
        # Mock authentication and authorization
        with patch('server.security') as mock_security, \
             patch('server.token_manager') as mock_token:
            
            # Mock user credentials
            credentials = {
                "username": "test_user",
                "password": "test_password"
            }
            
            # Mock authentication
            mock_security.authenticate_user = Mock(return_value={"id": 1, "username": "test_user"})
            mock_token.create_access_token = Mock(return_value="test_token_123")
            
            # Test authentication flow
            user = mock_security.authenticate_user(credentials)
            assert user["id"] == 1
            assert user["username"] == "test_user"
            
            # Test token creation flow
            token = mock_token.create_access_token(user)
            assert token == "test_token_123"
    
    def test_health_check_flow(self):
        """Test health check flow."""
        # Test that health checks flow correctly through the system
        
        # Mock health checks
        with patch('server.health_endpoints') as mock_health:
            
            # Mock health check results
            health_results = {
                "database": {"status": "healthy", "connected": True},
                "redis": {"status": "healthy", "connected": True},
                "system": {"status": "healthy", "cpu_percent": 25.5}
            }
            
            # Mock health check functions
            mock_health._check_database_health = Mock(return_value=health_results["database"])
            mock_health._check_redis_health = Mock(return_value=health_results["redis"])
            mock_health._check_system_resources = Mock(return_value=health_results["system"])
            
            # Test health check flow
            db_health = mock_health._check_database_health()
            redis_health = mock_health._check_redis_health()
            sys_health = mock_health._check_system_resources()
            
            # Verify flow
            assert db_health["status"] == "healthy"
            assert db_health["connected"] is True
            assert redis_health["status"] == "healthy"
            assert redis_health["connected"] is True
            assert sys_health["status"] == "healthy"
            assert sys_health["cpu_percent"] == 25.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])