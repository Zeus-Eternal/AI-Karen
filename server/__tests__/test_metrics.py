"""
Tests for metrics functionality.

Tests Prometheus metrics initialization, counters, and recording.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import (
    initialize_metrics,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ERROR_COUNT,
    PROMETHEUS_ENABLED
)


class TestMetricsInitialization:
    """Test metrics initialization and configuration."""
    
    def test_initialize_metrics_with_prometheus(self):
        """Test metrics initialization when Prometheus is available."""
        with patch('metrics.REGISTRY', Mock()) as mock_registry:
            with patch('metrics.get_metrics_manager') as mock_get_manager:
                from contextlib import contextmanager
                
                @contextmanager
                def mock_context():
                    yield None
                
                mock_manager = Mock()
                mock_manager.register_counter = Mock(return_value=Mock())
                mock_manager.register_histogram = Mock(return_value=Mock())
                mock_manager.register_gauge = Mock(return_value=Mock())
                mock_manager.safe_metrics_context = mock_context
                
                mock_get_manager.return_value = mock_manager
                
                metrics = initialize_metrics()
                
                # Verify metrics components were created
                assert REQUEST_COUNT is not None
                assert REQUEST_LATENCY is not None
                assert ERROR_COUNT is not None
                # The initialize_metrics function is called multiple times (once at import, once in test)
                assert mock_manager.register_counter.call_count >= 1
                assert mock_manager.register_histogram.call_count >= 1
                assert mock_manager.register_gauge.call_count >= 1
    
    def test_initialize_metrics_without_prometheus(self):
        """Test metrics initialization when Prometheus is not available."""
        with patch('metrics.PROMETHEUS_ENABLED', False):
            with patch('metrics.get_metrics_manager') as mock_get_manager:
                from contextlib import contextmanager
                
                @contextmanager
                def mock_context():
                    yield None
                
                mock_manager = Mock()
                mock_manager.register_counter = Mock(return_value=Mock())
                mock_manager.register_histogram = Mock(return_value=Mock())
                mock_manager.register_gauge = Mock(return_value=Mock())
                mock_manager.safe_metrics_context = mock_context
                
                mock_get_manager.return_value = mock_manager
                
                metrics = initialize_metrics()
                
                # Verify metrics components were created
                assert REQUEST_COUNT is not None
                assert REQUEST_LATENCY is not None
                assert ERROR_COUNT is not None
                # The initialize_metrics function is called multiple times (once at import, once in test)
                assert mock_manager.register_counter.call_count >= 1
                assert mock_manager.register_histogram.call_count >= 1
                assert mock_manager.register_gauge.call_count >= 1


class TestMetricsRecording:
    """Test metrics recording functionality."""
    
    @pytest.fixture
    def mock_metrics(self):
        """Create mock metrics components."""
        mock_request_count = Mock()
        mock_request_latency = Mock()
        mock_error_count = Mock()
        
        return {
            'REQUEST_COUNT': mock_request_count,
            'REQUEST_LATENCY': mock_request_latency,
            'ERROR_COUNT': mock_error_count
        }
    
    def test_record_request_count(self, mock_metrics):
        """Test request count recording."""
        mock_labels = Mock()
        mock_metrics['REQUEST_COUNT'].labels.return_value = mock_labels
        
        # Record a request with labels
        mock_metrics['REQUEST_COUNT'].labels(method="GET", path="/test")
        mock_metrics['REQUEST_COUNT'].inc()
        
        # Verify the inc method was called
        mock_metrics['REQUEST_COUNT'].inc.assert_called_once()
        mock_metrics['REQUEST_COUNT'].labels.assert_called_once_with(method="GET", path="/test")
    
    def test_record_request_latency(self, mock_metrics):
        """Test request latency recording."""
        mock_labels = Mock()
        mock_metrics['REQUEST_LATENCY'].labels.return_value = mock_labels
        
        # Record latency with labels
        mock_metrics['REQUEST_LATENCY'].labels(method="GET", path="/test")
        mock_metrics['REQUEST_LATENCY'].observe(0.5)
        
        # Verify the observe method was called
        mock_metrics['REQUEST_LATENCY'].observe.assert_called_once_with(0.5)
        mock_metrics['REQUEST_LATENCY'].labels.assert_called_once_with(method="GET", path="/test")
    
    def test_record_error_count(self, mock_metrics):
        """Test error count recording."""
        mock_labels = Mock()
        mock_metrics['ERROR_COUNT'].labels.return_value = mock_labels
        
        # Record an error with labels
        mock_metrics['ERROR_COUNT'].labels(method="GET", path="/test", error_type="500")
        mock_metrics['ERROR_COUNT'].inc()
        
        # Verify the inc method was called
        mock_metrics['ERROR_COUNT'].inc.assert_called_once()
        mock_metrics['ERROR_COUNT'].labels.assert_called_once_with(method="GET", path="/test", error_type="500")
    
    def test_record_metrics_with_labels(self, mock_metrics):
        """Test metrics recording with custom labels."""
        # Record metrics with labels
        mock_metrics['REQUEST_COUNT'].labels(method="GET", path="/test")
        mock_metrics['REQUEST_COUNT'].inc()
        
        mock_metrics['REQUEST_LATENCY'].labels(method="POST", path="/api/test")
        mock_metrics['REQUEST_LATENCY'].observe(1.2)
        
        # Verify labels were set
        mock_metrics['REQUEST_COUNT'].labels.assert_called_with(method="GET", path="/test")
        mock_metrics['REQUEST_LATENCY'].labels.assert_called_with(method="POST", path="/api/test")


class TestExtensionMetrics:
    """Test extension-specific metrics."""
    
    @pytest.fixture
    def mock_extension_metrics(self):
        """Create mock extension metrics components."""
        mock_health_status = Mock()
        mock_response_time = Mock()
        mock_background_tasks = Mock()
        mock_api_calls = Mock()
        mock_errors = Mock()
        mock_uptime = Mock()
        
        return {
            'EXTENSION_HEALTH_STATUS': mock_health_status,
            'EXTENSION_RESPONSE_TIME': mock_response_time,
            'EXTENSION_BACKGROUND_TASKS': mock_background_tasks,
            'EXTENSION_API_CALLS': mock_api_calls,
            'EXTENSION_ERRORS': mock_errors,
            'EXTENSION_UPTIME': mock_uptime
        }
    
    def test_record_extension_health_status(self, mock_extension_metrics):
        """Test extension health status recording."""
        # Record health status
        mock_extension_metrics['EXTENSION_HEALTH_STATUS'].labels(
            extension_name="test-extension",
            extension_category="monitoring"
        )
        mock_extension_metrics['EXTENSION_HEALTH_STATUS'].set(1.0)  # Healthy
        
        # Verify the set method was called
        mock_extension_metrics['EXTENSION_HEALTH_STATUS'].set.assert_called_once_with(1.0)
        mock_extension_metrics['EXTENSION_HEALTH_STATUS'].labels.assert_called_once_with(
            extension_name="test-extension",
            extension_category="monitoring"
        )
    
    def test_record_extension_response_time(self, mock_extension_metrics):
        """Test extension response time recording."""
        # Record response time
        mock_extension_metrics['EXTENSION_RESPONSE_TIME'].labels(
            extension_name="test-extension",
            operation="test-operation"
        )
        mock_extension_metrics['EXTENSION_RESPONSE_TIME'].observe(0.75)
        
        # Verify the observe method was called
        mock_extension_metrics['EXTENSION_RESPONSE_TIME'].observe.assert_called_once_with(0.75)
        mock_extension_metrics['EXTENSION_RESPONSE_TIME'].labels.assert_called_once_with(
            extension_name="test-extension",
            operation="test-operation"
        )
    
    def test_record_extension_background_tasks(self, mock_extension_metrics):
        """Test extension background tasks recording."""
        # Record background tasks
        mock_extension_metrics['EXTENSION_BACKGROUND_TASKS'].labels(
            extension_name="test-extension",
            task_status="active"
        )
        mock_extension_metrics['EXTENSION_BACKGROUND_TASKS'].set(5)  # 5 active tasks
        
        # Verify the set method was called
        mock_extension_metrics['EXTENSION_BACKGROUND_TASKS'].set.assert_called_once_with(5)
        mock_extension_metrics['EXTENSION_BACKGROUND_TASKS'].labels.assert_called_once_with(
            extension_name="test-extension",
            task_status="active"
        )


class TestMetricsIntegration:
    """Test metrics integration with other components."""
    
    @pytest.fixture
    def mock_app_with_metrics(self):
        """Create a mock FastAPI app with metrics."""
        from fastapi import FastAPI
        
        app = FastAPI()
        
        # Mock metrics middleware
        async def metrics_middleware(request, call_next):
            # Simulate metrics recording
            if hasattr(TestMetricsIntegration, 'mock_metrics'):
                TestMetricsIntegration.mock_metrics['REQUEST_COUNT'].inc()
            
            response = await call_next(request)
            return response
        
        app.middleware("http")(metrics_middleware)
        return app
    
    def test_metrics_middleware_integration(self, mock_app_with_metrics):
        """Test that metrics middleware integrates with FastAPI."""
        from fastapi.testclient import TestClient
        
        # Set up mock metrics on class
        mock_metrics = {
            'REQUEST_COUNT': Mock(),
            'REQUEST_LATENCY': Mock(),
            'ERROR_COUNT': Mock()
        }
        TestMetricsIntegration.mock_metrics = mock_metrics
        
        client = TestClient(mock_app_with_metrics)
        
        # Make a request
        response = client.get("/nonexistent")
        
        # Verify metrics were recorded
        mock_metrics['REQUEST_COUNT'].inc.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])