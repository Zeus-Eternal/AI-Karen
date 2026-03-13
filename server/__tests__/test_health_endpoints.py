"""
Tests for health endpoints functionality.

Tests health check endpoints, status reporting, and system health monitoring.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthEndpoints:
    """Test health endpoints functionality."""
    
    @pytest.mark.asyncio
    async def test_ping_endpoint_success(self):
        """Test successful ping endpoint."""
        # Import the ping function
        from health_endpoints import api_ping
        
        # Call the ping function
        result = api_ping()
        
        # Verify response structure
        assert "status" in result
        assert result["status"] == "ok"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_root_ping_endpoint_success(self):
        """Test successful root ping endpoint."""
        # Import the root ping function
        from health_endpoints import root_ping
        
        # Call the root ping function
        result = root_ping()
        
        # Verify response structure
        assert "status" in result
        assert result["status"] == "ok"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_root_health_endpoint_success(self):
        """Test successful root health endpoint."""
        # Import the root health function
        from health_endpoints import root_health
        
        # Call the root health function
        result = root_health()
        
        # Verify response structure
        assert "status" in result
        assert result["status"] == "ok"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_endpoint_success(self):
        """Test successful comprehensive health endpoint."""
        # Import the comprehensive health function
        from health_endpoints import comprehensive_health
        
        # Mock request object
        mock_request = Mock()
        mock_request.client.host = "localhost"
        
        # Mock all status functions
        with patch('health_endpoints._check_database_health') as mock_db_status, \
             patch('health_endpoints._check_redis_health') as mock_redis_status, \
             patch('health_endpoints._check_ai_providers_health') as mock_ai_providers_status, \
             patch('health_endpoints._check_system_resources') as mock_system_resources, \
             patch('health_endpoints._check_extension_system_health') as mock_extension_status:
            
            mock_db_status.return_value = {
                "status": "healthy",
                "connected": True,
                "response_time_ms": 12.5
            }
            
            mock_redis_status.return_value = {
                "status": "healthy",
                "connected": True,
                "response_time_ms": 8.2
            }
            
            mock_ai_providers_status.return_value = {
                "status": "healthy",
                "total_providers": 5,
                "available_providers": 4
            }
            
            mock_system_resources.return_value = {
                "status": "healthy",
                "cpu_percent": 25.5,
                "memory_percent": 60.2
            }
            
            mock_extension_status.return_value = {
                "status": "healthy",
                "total_extensions": 8,
                "healthy_extensions": 6
            }
            
            # Call comprehensive health function
            result = await comprehensive_health(mock_request)
            
            # Verify response structure
            assert "status" in result
            assert result["status"] == "healthy"
            assert "timestamp" in result
            assert "response_time_ms" in result
            assert "services" in result
            assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_database_health_function(self):
        """Test database health check function."""
        # Import the database health function
        from health_endpoints import _check_database_health
        
        # Mock database manager
        with patch('health_endpoints.get_database_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.test_connection.return_value = True
            mock_manager.is_degraded.return_value = False
            mock_get_manager.return_value = mock_manager
            
            # Call database health function
            result = await _check_database_health()
            
            # Verify response structure
            assert "status" in result
            assert result["status"] == "healthy"
            assert result["connected"] is True
            assert result["degraded"] is False
    
    @pytest.mark.asyncio
    async def test_database_health_function_with_degraded_status(self):
        """Test database health check function with degraded status."""
        # Import the database health function
        from health_endpoints import _check_database_health
        
        # Mock database manager
        with patch('health_endpoints.get_database_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.test_connection.return_value = True
            mock_manager.is_degraded.return_value = True
            mock_get_manager.return_value = mock_manager
            
            # Call database health function
            result = await _check_database_health()
            
            # Verify response structure
            assert "status" in result
            assert result["status"] == "degraded"
            assert result["connected"] is True
            assert result["degraded"] is True
    
    @pytest.mark.asyncio
    async def test_database_health_function_with_exception(self):
        """Test database health check function with exception."""
        # Import the database health function
        from health_endpoints import _check_database_health
        
        # Mock database manager with exception
        with patch('health_endpoints.get_database_manager') as mock_get_manager:
            mock_get_manager.side_effect = Exception("Connection failed")
            
            # Call database health function
            result = await _check_database_health()
            
            # Verify error handling
            assert "status" in result
            assert result["status"] == "unhealthy"
            assert result["connected"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_redis_health_function(self):
        """Test Redis health check function."""
        # Import the Redis health function
        from health_endpoints import _check_redis_health
        
        # Mock Redis manager
        with patch('health_endpoints.get_redis_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.test_connection.return_value = True
            mock_manager.is_degraded.return_value = False
            mock_get_manager.return_value = mock_manager
            
            # Call Redis health function
            result = await _check_redis_health()
            
            # Verify response structure
            assert "status" in result
            assert result["status"] == "healthy"
            assert result["connected"] is True
            assert result["degraded"] is False
    
    @pytest.mark.asyncio
    async def test_system_resources_function(self):
        """Test system resources check function."""
        # Import the system resources function
        from health_endpoints import _check_system_resources
        
        # Mock psutil
        with patch('health_endpoints.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 25.5
            mock_psutil.virtual_memory.return_value = Mock(percent=60.2)
            mock_psutil.disk_usage.return_value = Mock(percent=45.8)
            
            # Call system resources function
            result = await _check_system_resources()
            
            # Verify response structure
            assert "status" in result
            assert result["status"] == "healthy"
            assert result["cpu_percent"] == 25.5
            assert result["memory_percent"] == 60.2
            assert result["disk_percent"] == 45.8
    
    @pytest.mark.asyncio
    async def test_system_resources_function_with_high_usage(self):
        """Test system resources check function with high usage."""
        # Import the system resources function
        from health_endpoints import _check_system_resources
        
        # Mock psutil with high usage
        with patch('health_endpoints.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 92.0
            mock_psutil.virtual_memory.return_value = Mock(percent=93.5)
            mock_psutil.disk_usage.return_value = Mock(percent=96.2)
            
            # Call system resources function
            result = await _check_system_resources()
            
            # Verify response structure
            assert "status" in result
            assert result["status"] == "unhealthy"
            assert result["cpu_percent"] == 92.0
            assert result["memory_percent"] == 93.5
            assert result["disk_percent"] == 96.2
    
    @pytest.mark.asyncio
    async def test_ai_providers_health_function(self):
        """Test AI providers health check function."""
        # Import the AI providers health function
        from health_endpoints import _check_ai_providers_health
        
        # Mock provider registry
        with patch('health_endpoints.get_provider_registry_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_system_status.return_value = {
                "total_providers": 5,
                "available_providers": 4,
                "failed_providers": [],
                "provider_details": {}
            }
            mock_get_service.return_value = mock_service
            
            # Mock Path for models directory
            with patch('health_endpoints.Path') as mock_path:
                mock_path.return_value.exists.return_value = False
                mock_path.return_value.glob.return_value = []
                
                # Call AI providers health function
                result = await _check_ai_providers_health()
                
                # Verify response structure
                assert "status" in result
                assert result["status"] == "healthy"
                assert result["total_providers"] == 5
                assert result["available_providers"] == 4
                assert result["local_models"] == 0
    
    @pytest.mark.asyncio
    async def test_extension_system_health_function(self):
        """Test extension system health check function."""
        # Import the extension system health function
        from health_endpoints import _check_extension_system_health
        
        # Mock extension health monitor
        with patch('health_endpoints.get_extension_health_monitor') as mock_get_monitor:
            mock_monitor = Mock()
            mock_monitor.get_extension_health_for_api.return_value = {
                "status": "healthy",
                "extensions": {
                    "total": 8,
                    "healthy": 6,
                    "degraded": 2,
                    "unhealthy": 0,
                    "details": {}
                },
                "uptime_seconds": 3600,
                "supporting_services": ["database", "redis"]
            }
            mock_get_monitor.return_value = mock_monitor
            
            # Call extension system health function
            result = await _check_extension_system_health()
            
            # Verify response structure
            assert "status" in result
            assert result["status"] == "healthy"
            assert result["total_extensions"] == 8
            assert result["healthy_extensions"] == 6
            assert result["degraded_extensions"] == 2
            assert result["unhealthy_extensions"] == 0


class TestHealthEndpointIntegration:
    """Test health endpoint integration with other components."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_with_exception_handling(self):
        """Test health endpoint with exception handling."""
        # Import the comprehensive health function
        from health_endpoints import comprehensive_health
        
        # Mock request object
        mock_request = Mock()
        mock_request.client.host = "localhost"
        
        # Mock exception in database status
        with patch('health_endpoints._check_database_health') as mock_db_status:
            mock_db_status.side_effect = Exception("Database connection failed")
            
            # Call comprehensive health function
            result = await comprehensive_health(mock_request)
            
            # Verify error is handled gracefully
            assert result["status"] == "unhealthy"
            assert "services" in result
            assert "database" in result["services"]
    
    @pytest.mark.asyncio
    async def test_health_endpoint_response_time_format(self):
        """Test health endpoint response time format."""
        # Import the comprehensive health function
        from health_endpoints import comprehensive_health
        
        # Mock request object
        mock_request = Mock()
        mock_request.client.host = "localhost"
        
        # Mock all status functions
        with patch('health_endpoints._check_database_health') as mock_db_status, \
             patch('health_endpoints._check_redis_health') as mock_redis_status, \
             patch('health_endpoints._check_ai_providers_health') as mock_ai_providers_status, \
             patch('health_endpoints._check_system_resources') as mock_system_resources, \
             patch('health_endpoints._check_extension_system_health') as mock_extension_status:
            
            mock_db_status.return_value = {"status": "healthy", "connected": True}
            mock_redis_status.return_value = {"status": "healthy", "connected": True}
            mock_ai_providers_status.return_value = {"status": "healthy", "total_providers": 5}
            mock_system_resources.return_value = {"status": "healthy", "cpu_percent": 25.5}
            mock_extension_status.return_value = {"status": "healthy", "total_extensions": 8}
            
            # Call comprehensive health function
            result = await comprehensive_health(mock_request)
            
            # Verify timestamp format
            import re
            timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z'
            assert re.match(timestamp_pattern, result["timestamp"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])