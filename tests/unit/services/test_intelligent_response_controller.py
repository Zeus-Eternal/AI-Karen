"""
Tests for IntelligentResponseController with resource optimization.

Tests verify that the controller preserves existing reasoning logic while
adding resource monitoring and optimization capabilities.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_karen_engine.services.intelligent_response_controller import (
    IntelligentResponseController,
    ResourceMonitor,
    MemoryManager,
    ResourcePressureConfig,
    ResourceMetrics,
    ResponsePerformanceMetrics
)
from ai_karen_engine.models.shared_types import (
    DecideActionInput, DecideActionOutput, FlowInput, FlowOutput, FlowType, ToolType
)


class TestResourceMonitor:
    """Test resource monitoring functionality."""
    
    @pytest.fixture
    def config(self):
        return ResourcePressureConfig(
            cpu_threshold_percent=5.0,
            memory_threshold_mb=500.0,
            system_cpu_threshold_percent=80.0,
            system_memory_threshold_percent=85.0
        )
    
    @pytest.fixture
    def resource_monitor(self, config):
        return ResourceMonitor(config)
    
    def test_resource_monitor_initialization(self, resource_monitor, config):
        """Test resource monitor initialization."""
        assert resource_monitor.config == config
        assert not resource_monitor._monitoring
        assert resource_monitor._monitor_thread is None
        assert len(resource_monitor._metrics_history) == 0
    
    @patch('psutil.Process')
    def test_collect_metrics(self, mock_process_class, resource_monitor):
        """Test metrics collection."""
        # Mock process metrics
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 2.5
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
        mock_process_class.return_value = mock_process
        
        # Mock system memory
        with patch('psutil.virtual_memory') as mock_vm:
            mock_vm.return_value = Mock(percent=60.0)
            
            metrics = resource_monitor._collect_metrics()
            
            assert metrics.cpu_percent == 2.5
            assert metrics.memory_mb == 100.0
            assert metrics.memory_percent == 60.0
            assert isinstance(metrics.timestamp, datetime)
    
    @patch('psutil.Process')
    def test_detect_resource_pressure_normal(self, mock_process_class, resource_monitor):
        """Test resource pressure detection under normal conditions."""
        # Mock normal resource usage
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 2.0
        mock_process.memory_info.return_value = Mock(rss=50 * 1024 * 1024)
        mock_process_class.return_value = mock_process
        
        with patch('psutil.virtual_memory') as mock_vm:
            mock_vm.return_value = Mock(percent=50.0)
            
            pressure = resource_monitor.detect_resource_pressure()
            assert not pressure
    
    @patch('psutil.Process')
    def test_detect_resource_pressure_high_cpu(self, mock_process_class, resource_monitor):
        """Test resource pressure detection with high CPU."""
        # Mock high CPU usage
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 85.0  # Above threshold
        mock_process.memory_info.return_value = Mock(rss=50 * 1024 * 1024)
        mock_process_class.return_value = mock_process
        
        with patch('psutil.virtual_memory') as mock_vm:
            mock_vm.return_value = Mock(percent=50.0)
            
            pressure = resource_monitor.detect_resource_pressure()
            assert pressure
    
    @patch('psutil.Process')
    def test_detect_resource_pressure_high_memory(self, mock_process_class, resource_monitor):
        """Test resource pressure detection with high memory."""
        # Mock high memory usage
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 2.0
        mock_process.memory_info.return_value = Mock(rss=50 * 1024 * 1024)
        mock_process_class.return_value = mock_process
        
        with patch('psutil.virtual_memory') as mock_vm:
            mock_vm.return_value = Mock(percent=90.0)  # Above threshold
            
            pressure = resource_monitor.detect_resource_pressure()
            assert pressure
    
    def test_start_stop_monitoring(self, resource_monitor):
        """Test starting and stopping monitoring."""
        # Start monitoring
        resource_monitor.start_monitoring()
        assert resource_monitor._monitoring
        assert resource_monitor._monitor_thread is not None
        
        # Stop monitoring
        resource_monitor.stop_monitoring()
        assert not resource_monitor._monitoring


class TestMemoryManager:
    """Test memory management functionality."""
    
    @pytest.fixture
    def memory_manager(self):
        manager = MemoryManager()
        manager.initialize()
        return manager
    
    @patch('psutil.Process')
    def test_memory_manager_initialization(self, mock_process_class):
        """Test memory manager initialization."""
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)
        mock_process_class.return_value = mock_process
        
        manager = MemoryManager()
        manager.initialize()
        
        assert manager._baseline_memory_mb == 100.0
    
    @patch('psutil.Process')
    @patch('gc.collect')
    def test_optimize_memory_before_response(self, mock_gc, mock_process_class, memory_manager):
        """Test memory optimization before response."""
        # Mock memory usage
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=200 * 1024 * 1024)  # 200MB
        mock_process_class.return_value = mock_process
        
        # Mock garbage collection
        mock_gc.return_value = 10
        
        # Force GC by setting high memory increase
        memory_manager._baseline_memory_mb = 50.0  # Low baseline to trigger GC
        memory_manager._last_gc_time = 0  # Old timestamp to allow GC
        
        result = memory_manager.optimize_memory_before_response()
        
        assert "optimizations_applied" in result
        assert "weak_ref_cleanup" in result["optimizations_applied"]
        assert result["start_memory_mb"] == 200.0
    
    def test_optimize_memory_after_response(self, memory_manager):
        """Test memory optimization after response."""
        test_data = {"test": "data"}
        
        result = memory_manager.optimize_memory_after_response(test_data)
        
        assert result["cleanup_scheduled"] is True
        assert len(memory_manager._weak_refs) == 1


class TestIntelligentResponseController:
    """Test the main IntelligentResponseController."""
    
    @pytest.fixture
    def mock_decision_engine(self):
        """Mock DecisionEngine."""
        engine = Mock()
        engine.decide_action = AsyncMock()
        return engine
    
    @pytest.fixture
    def mock_flow_manager(self):
        """Mock FlowManager."""
        manager = Mock()
        manager.execute_flow = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_tinyllama_service(self):
        """Mock TinyLlamaService."""
        service = Mock()
        service.generate_scaffold = AsyncMock()
        return service
    
    @pytest.fixture
    def config(self):
        return ResourcePressureConfig(
            cpu_threshold_percent=5.0,
            memory_threshold_mb=500.0
        )
    
    @pytest.fixture
    def controller(self, mock_decision_engine, mock_flow_manager, mock_tinyllama_service, config):
        """Create IntelligentResponseController with mocked dependencies."""
        with patch('ai_karen_engine.services.intelligent_response_controller.ResourceMonitor'):
            with patch('ai_karen_engine.services.intelligent_response_controller.MemoryManager'):
                controller = IntelligentResponseController(
                    decision_engine=mock_decision_engine,
                    flow_manager=mock_flow_manager,
                    tinyllama_service=mock_tinyllama_service,
                    config=config
                )
                return controller
    
    def test_controller_initialization(self, controller, mock_decision_engine, mock_flow_manager):
        """Test controller initialization preserves original components."""
        assert controller._decision_engine is mock_decision_engine
        assert controller._flow_manager is mock_flow_manager
        assert controller.decision_engine is mock_decision_engine  # Property access
        assert controller.flow_manager is mock_flow_manager  # Property access
    
    @pytest.mark.asyncio
    async def test_generate_optimized_response_preserves_logic(self, controller, mock_decision_engine):
        """Test that optimized response generation preserves DecisionEngine logic."""
        # Setup mock response
        expected_response = DecideActionOutput(
            intermediate_response="Test response",
            tool_to_call=ToolType.NONE,
            tool_input=None,
            suggested_new_facts=None,
            proactive_suggestion=None
        )
        mock_decision_engine.decide_action.return_value = expected_response
        
        # Mock resource optimization methods
        controller._optimize_resources_before_response = AsyncMock()
        controller._optimize_resources_after_response = AsyncMock()
        
        # Create test input
        input_data = DecideActionInput(
            prompt="Test prompt",
            short_term_memory="",
            long_term_memory="",
            keywords=[],
            knowledge_graph_insights="",
            personal_facts=[],
            memory_depth=None,
            personality_tone=None,
            personality_verbosity=None,
            custom_persona_instructions=""
        )
        
        # Execute optimized response
        result = await controller.generate_optimized_response(input_data)
        
        # Verify DecisionEngine was called with original input
        mock_decision_engine.decide_action.assert_called_once_with(input_data)
        
        # Verify response is unchanged
        assert result == expected_response
        
        # Verify optimization methods were called
        controller._optimize_resources_before_response.assert_called_once()
        controller._optimize_resources_after_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_optimized_flow_preserves_logic(self, controller, mock_flow_manager):
        """Test that optimized flow execution preserves FlowManager logic."""
        # Setup mock response
        expected_result = FlowOutput(result="Test flow result")
        mock_flow_manager.execute_flow.return_value = expected_result
        
        # Mock resource optimization methods
        controller._optimize_resources_before_response = AsyncMock()
        controller._optimize_resources_after_response = AsyncMock()
        
        # Create test input
        flow_type = FlowType.CHAT_FLOW
        input_data = FlowInput(data={"test": "data"})
        
        # Execute optimized flow
        result = await controller.execute_optimized_flow(flow_type, input_data)
        
        # Verify FlowManager was called with original parameters
        mock_flow_manager.execute_flow.assert_called_once_with(flow_type, input_data)
        
        # Verify result is unchanged
        assert result == expected_result
        
        # Verify optimization methods were called
        controller._optimize_resources_before_response.assert_called_once()
        controller._optimize_resources_after_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_scaffolding_optimized_preserves_logic(self, controller, mock_tinyllama_service):
        """Test that optimized scaffolding preserves TinyLlamaService logic."""
        # Setup mock response
        expected_result = Mock()
        expected_result.content = "Test scaffold"
        expected_result.processing_time = 0.1
        mock_tinyllama_service.generate_scaffold.return_value = expected_result
        
        # Mock resource optimization methods
        controller._optimize_resources_before_response = AsyncMock()
        controller._optimize_resources_after_response = AsyncMock()
        
        # Execute optimized scaffolding
        result = await controller.generate_scaffolding_optimized(
            text="Test text",
            scaffold_type="reasoning",
            max_tokens=100,
            context={"test": "context"}
        )
        
        # Verify TinyLlamaService was called with original parameters
        mock_tinyllama_service.generate_scaffold.assert_called_once_with(
            "Test text", "reasoning", 100, {"test": "context"}
        )
        
        # Verify result is unchanged
        assert result == expected_result
        
        # Verify optimization methods were called
        controller._optimize_resources_before_response.assert_called_once()
        controller._optimize_resources_after_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cpu_usage_monitoring(self, controller):
        """Test CPU usage monitoring during response generation."""
        # Mock high CPU usage
        mock_metrics = ResourceMetrics(
            cpu_percent=8.0,  # Above 5% threshold
            memory_mb=100.0,
            memory_percent=50.0,
            timestamp=datetime.now()
        )
        
        controller.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)
        controller.resource_monitor.detect_resource_pressure = Mock(return_value=False)
        controller.memory_manager.optimize_memory_before_response = Mock(
            return_value={"memory_freed_mb": 0, "optimizations_applied": []}
        )
        controller.memory_manager.optimize_memory_after_response = Mock(
            return_value={"cleanup_scheduled": True}
        )
        
        # Mock decision engine
        controller._decision_engine.decide_action = AsyncMock(
            return_value=DecideActionOutput(
                intermediate_response="Test",
                tool_to_call=ToolType.NONE,
                tool_input=None,
                suggested_new_facts=None,
                proactive_suggestion=None
            )
        )
        
        input_data = DecideActionInput(
            prompt="Test",
            short_term_memory="",
            long_term_memory="",
            keywords=[],
            knowledge_graph_insights="",
            personal_facts=[],
            memory_depth=None,
            personality_tone=None,
            personality_verbosity=None,
            custom_persona_instructions=""
        )
        
        # Execute response
        await controller.generate_optimized_response(input_data, "test_response")
        
        # Check that metrics were recorded
        metrics = controller.get_performance_metrics("test_response")
        assert metrics is not None
        assert metrics.cpu_usage_percent == 8.0
        assert "cpu_threshold_exceeded" in metrics.optimization_applied
    
    @pytest.mark.asyncio
    async def test_memory_optimization_triggers(self, controller):
        """Test memory optimization triggers."""
        # Mock memory pressure
        controller.resource_monitor.detect_resource_pressure = Mock(return_value=True)
        controller.resource_monitor.get_current_metrics = Mock(
            return_value=ResourceMetrics(
                cpu_percent=2.0,
                memory_mb=600.0,  # Above 500MB threshold
                memory_percent=70.0,
                timestamp=datetime.now()
            )
        )
        
        # Mock memory optimization
        controller.memory_manager.optimize_memory_before_response = Mock(
            return_value={
                "memory_freed_mb": 50.0,
                "optimizations_applied": ["gc_collected_10", "weak_ref_cleanup"]
            }
        )
        controller.memory_manager.optimize_memory_after_response = Mock(
            return_value={"cleanup_scheduled": True}
        )
        
        # Mock decision engine
        controller._decision_engine.decide_action = AsyncMock(
            return_value=DecideActionOutput(
                intermediate_response="Test",
                tool_to_call=ToolType.NONE,
                tool_input=None,
                suggested_new_facts=None,
                proactive_suggestion=None
            )
        )
        
        input_data = DecideActionInput(
            prompt="Test",
            short_term_memory="",
            long_term_memory="",
            keywords=[],
            knowledge_graph_insights="",
            personal_facts=[],
            memory_depth=None,
            personality_tone=None,
            personality_verbosity=None,
            custom_persona_instructions=""
        )
        
        # Execute response
        await controller.generate_optimized_response(input_data, "memory_test")
        
        # Check that optimizations were applied
        metrics = controller.get_performance_metrics("memory_test")
        assert metrics is not None
        assert metrics.resource_pressure_detected
        assert "resource_pressure_detected" in metrics.optimization_applied
        assert "gc_collected_10" in metrics.optimization_applied
        assert "weak_ref_cleanup" in metrics.optimization_applied
    
    def test_performance_metrics_collection(self, controller):
        """Test performance metrics collection and retrieval."""
        # Create test metrics
        test_metrics = ResponsePerformanceMetrics(
            response_id="test_123",
            start_time=datetime.now() - timedelta(seconds=1),
            end_time=datetime.now(),
            total_duration_ms=1000.0,
            cpu_usage_percent=3.5,
            memory_usage_mb=200.0
        )
        
        # Store metrics
        controller._performance_metrics["test_123"] = test_metrics
        
        # Test retrieval
        retrieved = controller.get_performance_metrics("test_123")
        assert retrieved == test_metrics
        
        # Test non-existent metrics
        assert controller.get_performance_metrics("nonexistent") is None
    
    def test_recent_performance_summary(self, controller):
        """Test recent performance summary calculation."""
        # Create test metrics
        now = datetime.now()
        metrics1 = ResponsePerformanceMetrics(
            response_id="test_1",
            start_time=now - timedelta(minutes=5),
            end_time=now - timedelta(minutes=5) + timedelta(seconds=1),
            total_duration_ms=1000.0,
            cpu_usage_percent=2.0,
            memory_usage_mb=100.0,
            resource_pressure_detected=False
        )
        
        metrics2 = ResponsePerformanceMetrics(
            response_id="test_2",
            start_time=now - timedelta(minutes=3),
            end_time=now - timedelta(minutes=3) + timedelta(seconds=2),
            total_duration_ms=2000.0,
            cpu_usage_percent=4.0,
            memory_usage_mb=200.0,
            resource_pressure_detected=True
        )
        
        # Store metrics
        controller._performance_metrics["test_1"] = metrics1
        controller._performance_metrics["test_2"] = metrics2
        
        # Get summary
        summary = controller.get_recent_performance_summary(duration_minutes=10)
        
        assert summary["total_responses"] == 2
        assert summary["avg_duration_ms"] == 1500.0
        assert summary["max_duration_ms"] == 2000.0
        assert summary["min_duration_ms"] == 1000.0
        assert summary["avg_cpu_percent"] == 3.0
        assert summary["max_cpu_percent"] == 4.0
        assert summary["resource_pressure_count"] == 1
    
    def test_resource_status(self, controller):
        """Test resource status reporting."""
        # Mock current metrics
        mock_metrics = ResourceMetrics(
            cpu_percent=3.5,
            memory_mb=150.0,
            memory_percent=60.0,
            timestamp=datetime.now()
        )
        
        controller.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)
        controller.resource_monitor.detect_resource_pressure = Mock(return_value=False)
        controller.resource_monitor._monitoring = True
        
        status = controller.get_resource_status()
        
        assert status["current_cpu_percent"] == 3.5
        assert status["current_memory_mb"] == 150.0
        assert status["current_memory_percent"] == 60.0
        assert not status["resource_pressure_detected"]
        assert status["monitoring_active"]
        assert status["cpu_threshold_percent"] == 5.0
        assert status["memory_threshold_mb"] == 500.0
    
    @pytest.mark.asyncio
    async def test_error_handling_preserves_original_errors(self, controller, mock_decision_engine):
        """Test that error handling preserves original component errors."""
        # Make decision engine raise an error
        original_error = RuntimeError("Original DecisionEngine error")
        mock_decision_engine.decide_action.side_effect = original_error
        
        # Mock resource optimization methods
        controller._optimize_resources_before_response = AsyncMock()
        controller._optimize_resources_after_response = AsyncMock()
        
        input_data = DecideActionInput(
            prompt="Test",
            short_term_memory="",
            long_term_memory="",
            keywords=[],
            knowledge_graph_insights="",
            personal_facts=[],
            memory_depth=None,
            personality_tone=None,
            personality_verbosity=None,
            custom_persona_instructions=""
        )
        
        # Verify original error is propagated
        with pytest.raises(RuntimeError, match="Original DecisionEngine error"):
            await controller.generate_optimized_response(input_data)
        
        # Verify optimization was still attempted
        controller._optimize_resources_before_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, controller):
        """Test proper cleanup during shutdown."""
        # Add some test metrics
        controller._performance_metrics["test"] = ResponsePerformanceMetrics(
            response_id="test",
            start_time=datetime.now()
        )
        
        # Mock resource monitor
        controller.resource_monitor.stop_monitoring = Mock()
        
        await controller.shutdown()
        
        # Verify cleanup
        controller.resource_monitor.stop_monitoring.assert_called_once()
        assert len(controller._performance_metrics) == 0


class TestIntegrationWithRealComponents:
    """Integration tests with real components to verify preservation of logic."""
    
    @pytest.mark.asyncio
    async def test_integration_with_real_decision_engine(self):
        """Test integration with real DecisionEngine."""
        from ai_karen_engine.services.ai_orchestrator.decision_engine import DecisionEngine
        
        # Create real DecisionEngine
        decision_engine = DecisionEngine()
        
        # Create controller with real component
        with patch('ai_karen_engine.services.intelligent_response_controller.ResourceMonitor'):
            with patch('ai_karen_engine.services.intelligent_response_controller.MemoryManager'):
                controller = IntelligentResponseController(
                    decision_engine=decision_engine,
                    flow_manager=Mock(),
                    tinyllama_service=None
                )
                
                # Mock optimization methods to avoid actual resource operations
                controller._optimize_resources_before_response = AsyncMock()
                controller._optimize_resources_after_response = AsyncMock()
                
                # Test with real DecisionEngine
                input_data = DecideActionInput(
                    prompt="What's the weather like?",
                    short_term_memory="",
                    long_term_memory="",
                    keywords=[],
                    knowledge_graph_insights="",
                    personal_facts=[],
                    memory_depth=None,
                    personality_tone=None,
                    personality_verbosity=None,
                    custom_persona_instructions=""
                )
                
                result = await controller.generate_optimized_response(input_data)
                
                # Verify DecisionEngine logic worked
                assert isinstance(result, DecideActionOutput)
                assert result.intermediate_response is not None
                
                # Verify optimization was applied
                controller._optimize_resources_before_response.assert_called_once()
                controller._optimize_resources_after_response.assert_called_once()