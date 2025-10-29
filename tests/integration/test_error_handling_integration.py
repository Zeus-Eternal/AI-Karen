"""
Integration tests for Error Handling and Graceful Degradation System

Tests the complete error handling system integration including all components
working together for comprehensive error recovery and graceful degradation.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.graceful_degradation_coordinator import (
    GracefulDegradationCoordinator,
    DegradationContext,
    SystemHealthStatus,
    DegradationLevel
)
from src.ai_karen_engine.services.error_recovery_system import (
    ErrorRecoverySystem,
    ErrorType
)
from src.ai_karen_engine.services.model_availability_handler import (
    ModelAvailabilityHandler,
    ModelAvailabilityStatus
)
from src.ai_karen_engine.services.timeout_performance_handler import (
    TimeoutPerformanceHandler,
    PerformanceIssueType
)
from src.ai_karen_engine.services.memory_exhaustion_handler import (
    MemoryExhaustionHandler,
    MemoryPressureLevel
)
from src.ai_karen_engine.services.streaming_interruption_handler import (
    StreamingInterruptionHandler,
    InterruptionType
)

from src.ai_karen_engine.core.types.shared_types import (
    Modality, ModalityType
)


class TestErrorHandlingIntegration:
    """Integration tests for the complete error handling system."""
    
    @pytest.fixture
    def coordinator(self):
        """Create GracefulDegradationCoordinator for testing."""
        return GracefulDegradationCoordinator()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample degradation context."""
        return DegradationContext(
            query="Test query for integration testing",
            requested_model="test-model",
            required_modalities=[
                Modality(
                    type=ModalityType.TEXT,
                    input_supported=True,
                    output_supported=True
                )
            ],
            user_priority=1,
            timeout_tolerance=30.0,
            quality_tolerance=0.8,
            allow_fallback=True,
            allow_degradation=True
        )
    
    @pytest.mark.asyncio
    async def test_system_health_assessment(self, coordinator):
        """Test comprehensive system health assessment."""
        health_report = await coordinator.assess_system_health()
        
        assert health_report is not None
        assert isinstance(health_report.overall_status, SystemHealthStatus)
        assert isinstance(health_report.degradation_level, DegradationLevel)
        assert isinstance(health_report.available_models, list)
        assert isinstance(health_report.unavailable_models, list)
        assert isinstance(health_report.memory_pressure, MemoryPressureLevel)
        assert isinstance(health_report.performance_issues, list)
        assert isinstance(health_report.active_recoveries, int)
        assert isinstance(health_report.recommendations, list)
        assert health_report.timestamp > 0
    
    @pytest.mark.asyncio
    async def test_graceful_execution_context_success(self, coordinator, sample_context):
        """Test graceful execution context with successful execution."""
        async with coordinator.graceful_execution(sample_context) as context:
            assert context is not None
            # Simulate successful execution
            await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_graceful_execution_context_with_error(self, coordinator, sample_context):
        """Test graceful execution context with error recovery."""
        try:
            async with coordinator.graceful_execution(sample_context) as context:
                # Simulate error that should be recovered
                raise Exception("Simulated error for testing")
        except Exception:
            # Error should be handled by graceful execution
            pass
    
    @pytest.mark.asyncio
    async def test_coordinated_recovery_model_unavailable(self, coordinator):
        """Test coordinated recovery for model unavailable error."""
        error = Exception("Model test-model is not available")
        
        response = await coordinator.handle_coordinated_recovery(
            query="Test query",
            error=error,
            model_id="test-model"
        )
        
        assert response is not None
        assert response.content is not None
        assert isinstance(response.degradation_level, DegradationLevel)
        assert response.response_time > 0
        assert isinstance(response.optimizations_applied, list)
        assert isinstance(response.warnings, list)
    
    @pytest.mark.asyncio
    async def test_coordinated_recovery_memory_exhaustion(self, coordinator):
        """Test coordinated recovery for memory exhaustion error."""
        error = MemoryError("Out of memory")
        
        response = await coordinator.handle_coordinated_recovery(
            query="Large query that causes memory issues",
            error=error,
            model_id="large-model"
        )
        
        assert response is not None
        assert response.content is not None
        assert response.degradation_level.value >= DegradationLevel.MODERATE.value
        assert "memory" in str(response.optimizations_applied).lower() or len(response.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_coordinated_recovery_timeout(self, coordinator):
        """Test coordinated recovery for timeout error."""
        error = asyncio.TimeoutError("Request timeout")
        
        response = await coordinator.handle_coordinated_recovery(
            query="Query that times out",
            error=error,
            model_id="slow-model"
        )
        
        assert response is not None
        assert response.content is not None
        assert response.degradation_level.value >= DegradationLevel.MINIMAL.value
    
    @pytest.mark.asyncio
    async def test_coordinated_recovery_streaming_interruption(self, coordinator):
        """Test coordinated recovery for streaming interruption."""
        error = Exception("Stream interrupted")
        
        response = await coordinator.handle_coordinated_recovery(
            query="Query with streaming response",
            error=error,
            model_id="streaming-model"
        )
        
        assert response is not None
        assert response.content is not None
        assert response.degradation_level.value >= DegradationLevel.MINIMAL.value
    
    @pytest.mark.asyncio
    async def test_multiple_error_types_handling(self, coordinator):
        """Test handling multiple error types in sequence."""
        errors = [
            Exception("Model unavailable"),
            MemoryError("Out of memory"),
            asyncio.TimeoutError("Timeout"),
            ConnectionError("Connection failed")
        ]
        
        responses = []
        for i, error in enumerate(errors):
            response = await coordinator.handle_coordinated_recovery(
                query=f"Test query {i}",
                error=error,
                model_id=f"test-model-{i}"
            )
            responses.append(response)
        
        # All responses should be successful
        assert len(responses) == len(errors)
        for response in responses:
            assert response is not None
            assert response.content is not None
            assert response.response_time > 0
    
    @pytest.mark.asyncio
    async def test_system_degradation_under_load(self, coordinator):
        """Test system behavior under high error load."""
        # Simulate multiple concurrent errors
        error_tasks = []
        for i in range(10):
            task = coordinator.handle_coordinated_recovery(
                query=f"Concurrent query {i}",
                error=Exception(f"Concurrent error {i}"),
                model_id=f"model-{i}"
            )
            error_tasks.append(task)
        
        # Wait for all recoveries to complete
        responses = await asyncio.gather(*error_tasks, return_exceptions=True)
        
        # Check that most recoveries succeeded
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= len(responses) * 0.8  # At least 80% success rate
    
    @pytest.mark.asyncio
    async def test_component_integration(self, coordinator):
        """Test that all error handling components work together."""
        # Test that all components are properly initialized
        assert coordinator.error_recovery is not None
        assert coordinator.model_availability is not None
        assert coordinator.timeout_performance is not None
        assert coordinator.memory_exhaustion is not None
        assert coordinator.streaming_interruption is not None
        
        # Test component interactions
        health_report = await coordinator.assess_system_health()
        assert health_report is not None
        
        # Test coordinated recovery uses appropriate components
        memory_error = MemoryError("Test memory error")
        response = await coordinator.handle_coordinated_recovery(
            query="Test query",
            error=memory_error
        )
        
        assert response is not None
        assert response.degradation_level.value > DegradationLevel.NONE.value
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, coordinator):
        """Test integration with performance monitoring."""
        # Simulate performance monitoring during error recovery
        start_time = time.time()
        
        response = await coordinator.handle_coordinated_recovery(
            query="Performance test query",
            error=Exception("Performance test error")
        )
        
        end_time = time.time()
        
        assert response is not None
        assert response.response_time > 0
        assert response.response_time <= (end_time - start_time) + 1.0  # Allow some margin
    
    @pytest.mark.asyncio
    async def test_fallback_chain_integration(self, coordinator):
        """Test that fallback chains work across components."""
        # Test model fallback -> memory optimization -> emergency response chain
        with patch.object(coordinator.model_availability, 'handle_routing_error', 
                         return_value=(None, "No fallback available")):
            with patch.object(coordinator.memory_exhaustion, 'handle_memory_exhaustion',
                             return_value=Mock(success=False)):
                
                response = await coordinator.handle_coordinated_recovery(
                    query="Fallback chain test",
                    error=Exception("Multiple failure test")
                )
                
                assert response is not None
                assert response.content is not None
                assert response.degradation_level == DegradationLevel.EMERGENCY
    
    @pytest.mark.asyncio
    async def test_system_status_reporting(self, coordinator):
        """Test comprehensive system status reporting."""
        status = await coordinator.get_system_status()
        
        assert isinstance(status, dict)
        assert "health_report" in status
        assert "degradation_stats" in status
        assert "component_status" in status
        
        health_report = status["health_report"]
        assert "overall_status" in health_report
        assert "degradation_level" in health_report
        assert "available_models" in health_report
        assert "unavailable_models" in health_report
        assert "memory_pressure" in health_report
        
        degradation_stats = status["degradation_stats"]
        assert "total_requests" in degradation_stats
        assert "degraded_requests" in degradation_stats
        assert "fallback_requests" in degradation_stats
        assert "emergency_responses" in degradation_stats
    
    @pytest.mark.asyncio
    async def test_error_classification_accuracy(self, coordinator):
        """Test that errors are classified correctly for appropriate handling."""
        test_cases = [
            (Exception("Model not found"), ErrorType.MODEL_UNAVAILABLE),
            (asyncio.TimeoutError("Timeout"), ErrorType.MODEL_TIMEOUT),
            (MemoryError("OOM"), ErrorType.MEMORY_EXHAUSTION),
            (ConnectionError("Connection lost"), ErrorType.CONNECTION_FAILURE),
            (Exception("Stream interrupted"), ErrorType.STREAMING_INTERRUPTION)
        ]
        
        for error, expected_type in test_cases:
            classified_type = coordinator._classify_error_type(error)
            assert classified_type == expected_type
    
    @pytest.mark.asyncio
    async def test_degradation_policy_application(self, coordinator, sample_context):
        """Test that degradation policies are applied correctly."""
        # Test different degradation levels
        degradation_levels = [
            DegradationLevel.MINIMAL,
            DegradationLevel.MODERATE,
            DegradationLevel.SIGNIFICANT,
            DegradationLevel.SEVERE,
            DegradationLevel.EMERGENCY
        ]
        
        for level in degradation_levels:
            # Simulate system health that would trigger this degradation level
            with patch.object(coordinator, 'current_degradation_level', level):
                # Test that appropriate policies are available
                policies = coordinator.degradation_policies.get(level, {})
                assert isinstance(policies, dict)
                
                if level.value > DegradationLevel.NONE.value:
                    assert "allow_model_fallback" in policies
    
    @pytest.mark.asyncio
    async def test_recovery_statistics_tracking(self, coordinator):
        """Test that recovery statistics are properly tracked."""
        initial_stats = coordinator.degradation_stats.copy()
        
        # Perform several recovery operations
        for i in range(5):
            await coordinator.handle_coordinated_recovery(
                query=f"Stats test query {i}",
                error=Exception(f"Stats test error {i}")
            )
        
        final_stats = coordinator.degradation_stats
        
        # Check that statistics were updated
        assert final_stats["total_requests"] > initial_stats["total_requests"]
        assert final_stats["degraded_requests"] >= initial_stats["degraded_requests"]
    
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, coordinator):
        """Test handling multiple concurrent errors without interference."""
        # Create multiple concurrent error scenarios
        concurrent_tasks = []
        
        for i in range(20):
            error_type = [
                Exception("Model error"),
                MemoryError("Memory error"),
                asyncio.TimeoutError("Timeout error"),
                ConnectionError("Connection error")
            ][i % 4]
            
            task = coordinator.handle_coordinated_recovery(
                query=f"Concurrent test {i}",
                error=error_type,
                model_id=f"concurrent-model-{i}"
            )
            concurrent_tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # Verify results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= len(results) * 0.9  # At least 90% success rate
        
        # Verify no interference between concurrent operations
        for result in successful_results:
            assert result.content is not None
            assert result.response_time > 0


class TestErrorHandlingAPIIntegration:
    """Integration tests for error handling API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from src.ai_karen_engine.api_routes.error_recovery_routes import router
        
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_get_system_health_endpoint(self, client):
        """Test system health endpoint."""
        response = client.get("/api/error-recovery/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_status" in data
        assert "degradation_level" in data
        assert "available_models" in data
        assert "unavailable_models" in data
        assert "memory_pressure" in data
        assert "active_recoveries" in data
        assert "recommendations" in data
        assert "timestamp" in data
    
    def test_recover_from_error_endpoint(self, client):
        """Test error recovery endpoint."""
        request_data = {
            "query": "Test query for API",
            "error_message": "Test error message",
            "model_id": "test-model",
            "modalities": ["text"]
        }
        
        response = client.post("/api/error-recovery/recover", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "recovered_content" in data
        assert "degradation_level" in data
        assert "recovery_time" in data
        assert "warnings" in data
    
    def test_check_model_availability_endpoint(self, client):
        """Test model availability check endpoint."""
        response = client.get("/api/error-recovery/models/test-model/availability")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_id" in data
        assert "status" in data
        assert "response_time" in data
        assert "load_percentage" in data
    
    def test_get_memory_status_endpoint(self, client):
        """Test memory status endpoint."""
        response = client.get("/api/error-recovery/memory/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "usage_percentage" in data
        assert "pressure_level" in data
        assert "available_gb" in data
        assert "used_gb" in data
        assert "total_gb" in data
    
    def test_get_recovery_statistics_endpoint(self, client):
        """Test recovery statistics endpoint."""
        response = client.get("/api/error-recovery/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "error_recovery" in data
        assert "model_availability" in data
        assert "memory_exhaustion" in data
        assert "streaming_interruption" in data
        assert "overall_stats" in data
    
    def test_simulate_error_endpoint(self, client):
        """Test error simulation endpoint."""
        request_data = {
            "error_type": "timeout",
            "query": "Test query",
            "model_id": "test-model"
        }
        
        response = client.post("/api/error-recovery/test/simulate-error", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "simulated_error_type" in data
        assert "recovery_successful" in data
        assert data["simulated_error_type"] == "timeout"
    
    def test_get_configuration_endpoint(self, client):
        """Test configuration retrieval endpoint."""
        response = client.get("/api/error-recovery/configuration")
        assert response.status_code == 200
        
        data = response.json()
        assert "timeouts" in data
        assert "memory_thresholds" in data
        assert "performance_thresholds" in data
        assert "optimization_settings" in data


if __name__ == "__main__":
    pytest.main([__file__])