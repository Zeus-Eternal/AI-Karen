"""
Basic tests for health endpoints functionality.

Tests health check endpoints, status reporting, and system health monitoring.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthEndpointsBasic:
    """Test basic health endpoints functionality."""
    
    def test_health_endpoints_module_imports(self):
        """Test that health endpoints module can be imported."""
        # Import the module
        import health_endpoints
        
        # Verify module has expected functions
        assert hasattr(health_endpoints, 'register_health_endpoints')
        assert hasattr(health_endpoints, '_check_database_health')
        assert hasattr(health_endpoints, '_check_redis_health')
        assert hasattr(health_endpoints, '_check_ai_providers_health')
        assert hasattr(health_endpoints, '_check_system_resources')
        assert hasattr(health_endpoints, '_check_extension_system_health')
    
    def test_register_health_endpoints_function_exists(self):
        """Test that register_health_endpoints function exists and is callable."""
        # Import the function
        from health_endpoints import register_health_endpoints
        
        # Verify function exists and is callable
        assert callable(register_health_endpoints)
    
    def test_database_health_function_exists(self):
        """Test that database health function exists and has correct signature."""
        # Import the function
        from health_endpoints import _check_database_health
        
        # Verify function exists
        assert callable(_check_database_health)
        
        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(_check_database_health)
    
    def test_redis_health_function_exists(self):
        """Test that Redis health function exists and has correct signature."""
        # Import the function
        from health_endpoints import _check_redis_health
        
        # Verify function exists
        assert callable(_check_redis_health)
        
        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(_check_redis_health)
    
    def test_system_resources_function_exists(self):
        """Test that system resources function exists and has correct signature."""
        # Import the function
        from health_endpoints import _check_system_resources
        
        # Verify function exists
        assert callable(_check_system_resources)
        
        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(_check_system_resources)
    
    def test_ai_providers_health_function_exists(self):
        """Test that AI providers health function exists and has correct signature."""
        # Import the function
        from health_endpoints import _check_ai_providers_health
        
        # Verify function exists
        assert callable(_check_ai_providers_health)
        
        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(_check_ai_providers_health)
    
    def test_extension_system_health_function_exists(self):
        """Test that extension system health function exists and has correct signature."""
        # Import the function
        from health_endpoints import _check_extension_system_health
        
        # Verify function exists
        assert callable(_check_extension_system_health)
        
        # Verify function is async
        import inspect
        assert inspect.iscoroutinefunction(_check_extension_system_health)
    
    def test_register_health_endpoints_with_mock_app(self):
        """Test register_health_endpoints with a mock FastAPI app."""
        # Import the function
        from health_endpoints import register_health_endpoints
        
        # Create a mock FastAPI app
        mock_app = Mock()
        
        # Register endpoints
        register_health_endpoints(mock_app)
        
        # Verify that app has the expected methods called
        # We can't easily test the exact routes without more complex mocking,
        # but we can verify the function executed without error
        assert True  # If we get here, the function executed without error
    
    def test_database_health_function_returns_dict(self):
        """Test that database health function returns a dictionary."""
        # Import the function
        from health_endpoints import _check_database_health
        
        # Mock all the dependencies
        with patch('health_endpoints.logger') as mock_logger:
            # Call the function
            import asyncio
            result = asyncio.run(_check_database_health())
            
            # Verify result is a dictionary
            assert isinstance(result, dict)
            
            # Verify result has expected keys
            assert "status" in result
            assert "connected" in result
            assert "error" in result or "response_time_ms" in result
    
    def test_redis_health_function_returns_dict(self):
        """Test that Redis health function returns a dictionary."""
        # Import the function
        from health_endpoints import _check_redis_health
        
        # Mock all the dependencies
        with patch('health_endpoints.logger') as mock_logger:
            # Call the function
            import asyncio
            result = asyncio.run(_check_redis_health())
            
            # Verify result is a dictionary
            assert isinstance(result, dict)
            
            # Verify result has expected keys
            assert "status" in result
            assert "connected" in result
            assert "error" in result or "response_time_ms" in result
    
    def test_ai_providers_health_function_returns_dict(self):
        """Test that AI providers health function returns a dictionary."""
        # Import the function
        from health_endpoints import _check_ai_providers_health
        
        # Mock all the dependencies
        with patch('health_endpoints.logger') as mock_logger:
            # Call the function
            import asyncio
            result = asyncio.run(_check_ai_providers_health())
            
            # Verify result is a dictionary
            assert isinstance(result, dict)
            
            # Verify result has expected keys
            assert "status" in result
            assert "total_providers" in result
            assert "available_providers" in result
            assert "local_models" in result
    
    def test_extension_system_health_function_returns_dict(self):
        """Test that extension system health function returns a dictionary."""
        # Import the function
        from health_endpoints import _check_extension_system_health
        
        # Mock all the dependencies
        with patch('health_endpoints.logger') as mock_logger:
            # Call the function
            import asyncio
            result = asyncio.run(_check_extension_system_health())
            
            # Verify result is a dictionary
            assert isinstance(result, dict)
            
            # Verify result has expected keys
            assert "status" in result
            assert "total_extensions" in result
            assert "healthy_extensions" in result
            assert "degraded_extensions" in result
            assert "unhealthy_extensions" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])