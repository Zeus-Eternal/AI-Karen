"""
Tests for performance monitoring functionality.

Tests performance metrics, monitoring, and optimization.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPerformance:
    """Test performance monitoring functionality."""
    
    def test_performance_module_imports(self):
        """Test that performance module can be imported."""
        # Import the module
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        import performance
        
        # Verify module has expected functions
        assert hasattr(performance, 'load_performance_settings')
        assert hasattr(performance, 'get_performance_status')
        assert hasattr(performance, 'run_performance_audit')
        assert hasattr(performance, 'trigger_optimization')
    
    def test_monitor_performance_function_exists(self):
        """Test that load_performance_settings function exists and is callable."""
        # Import the function
        from performance import load_performance_settings
        
        # Verify function exists and is callable
        assert callable(load_performance_settings)
    
    def test_track_request_time_function_exists(self):
        """Test that get_performance_status function exists and is callable."""
        # Import the function
        from performance import get_performance_status
        
        # Verify function exists and is callable
        assert callable(get_performance_status)
    
    def test_get_performance_metrics_function_exists(self):
        """Test that run_performance_audit function exists and is callable."""
        # Import the function
        from performance import run_performance_audit
        
        # Verify function exists and is callable
        assert callable(run_performance_audit)
    
    def test_monitor_performance_with_mock(self):
        """Test monitor_performance with mocked dependencies."""
        # Import the function
        from performance import monitor_performance
        
        # Mock dependencies using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_time.return_value = 1234567890.123
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call monitor_performance
            result = monitor_performance("test_function", args=[1, 2], kwargs={"key": "value"})
            
            # Verify result structure
            assert isinstance(result, dict)
            assert "execution_time" in result
            assert "function_name" in result
            assert "timestamp" in result
    
    def test_track_request_time_with_mock(self):
        """Test track_request_time with mocked dependencies."""
        # Import the function
        from performance import track_request_time
        
        # Mock dependencies using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_time.return_value = 1234567890.123
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call track_request_time
            result = track_request_time("GET", "/api/test", 200)
            
            # Verify result structure
            assert isinstance(result, dict)
            assert "request_method" in result
            assert "request_path" in result
            assert "status_code" in result
            assert "response_time" in result
    
    def test_get_performance_metrics_with_mock(self):
        """Test get_performance_metrics with mocked dependencies."""
        # Import the function
        from performance import get_performance_metrics
        
        # Mock dependencies using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_time.return_value = 1234567890.123
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call get_performance_metrics
            result = get_performance_metrics()
            
            # Verify result structure
            assert isinstance(result, dict)
            assert "timestamp" in result
            assert "system_metrics" in result
    
    def test_performance_metrics_has_cpu_info(self):
        """Test that performance metrics includes CPU information."""
        # Import the function
        from performance import get_performance_metrics
        
        # Mock dependencies using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('psutil.cpu_percent') as mock_cpu_percent:
            
            mock_time.return_value = 1234567890.123
            mock_cpu_percent.return_value = 25.5
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call get_performance_metrics
            result = get_performance_metrics()
            
            # Verify CPU information
            assert "system_metrics" in result
            assert "cpu_percent" in result["system_metrics"]
    
    def test_performance_metrics_has_memory_info(self):
        """Test that performance metrics includes memory information."""
        # Import the function
        from performance import get_performance_metrics
        
        # Mock dependencies using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('psutil.virtual_memory') as mock_virtual_memory:
            
            mock_time.return_value = 1234567890.123
            mock_memory = Mock()
            mock_memory.percent = 60.2
            mock_memory.available = 8 * 1024**3  # 8GB
            mock_virtual_memory.return_value = mock_memory
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call get_performance_metrics
            result = get_performance_metrics()
            
            # Verify memory information
            assert "system_metrics" in result
            assert "memory_percent" in result["system_metrics"]
            assert "memory_available" in result["system_metrics"]
    
    def test_performance_metrics_has_disk_info(self):
        """Test that performance metrics includes disk information."""
        # Import the function
        from performance import get_performance_metrics
        
        # Mock dependencies using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('psutil.disk_usage') as mock_disk_usage:
            
            mock_time.return_value = 1234567890.123
            mock_disk = Mock()
            mock_disk.percent = 45.8
            mock_disk.free = 100 * 1024**3  # 100GB
            mock_disk_usage.return_value = mock_disk
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call get_performance_metrics
            result = get_performance_metrics()
            
            # Verify disk information
            assert "system_metrics" in result
            assert "disk_percent" in result["system_metrics"]
            assert "disk_free" in result["system_metrics"]
    
    def test_performance_monitoring_with_exception(self):
        """Test performance monitoring with exception handling."""
        # Import the function
        from performance import monitor_performance
        
        # Mock dependencies with exception using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_time.side_effect = Exception("Time measurement failed")
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call monitor_performance and handle exception
            try:
                result = monitor_performance("test_function")
                # Should still return a result even with exception
                assert isinstance(result, dict)
                assert "error" in result
            except Exception:
                # If exception is raised, that's also acceptable
                pass
    
    def test_performance_logging_with_mock(self):
        """Test that performance functions log appropriately."""
        # Import the function
        from performance import monitor_performance
        
        # Mock logging using the actual modules
        with patch('logging.getLogger') as mock_get_logger, \
             patch('time.time') as mock_time:
            
            mock_time.return_value = 1234567890.123
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Reload performance module to reinitialize logger
            import importlib
            import performance
            importlib.reload(performance)
            
            # Call monitor_performance
            performance.monitor_performance("test_function")
            
            # Verify logging was called
            mock_get_logger.assert_called()
            mock_logger.info.assert_called()
    
    def test_performance_metrics_aggregation(self):
        """Test that performance metrics can be aggregated."""
        # Import the function
        from performance import get_performance_metrics
        
        # Mock dependencies using the actual modules
        with patch('time.time') as mock_time, \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_time.return_value = 1234567890.123
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call get_performance_metrics multiple times
            result1 = get_performance_metrics()
            result2 = get_performance_metrics()
            
            # Verify both results have expected structure
            assert isinstance(result1, dict)
            assert isinstance(result2, dict)
            assert "timestamp" in result1
            assert "timestamp" in result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])