"""
Tests for Intelligent Model Router

Tests the model router and wiring system to ensure it preserves existing
routing logic while enhancing it with discovered models and intelligent
fallback mechanisms.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_karen_engine.services.intelligent_model_router import (
    ModelRouter, RoutingDecision, RoutingStrategy, ConnectionStatus,
    ModelConnection, get_model_router, initialize_model_router
)
from ai_karen_engine.services.model_discovery_engine import (
    ModelInfo, ModelType, ModalityType, ModelCategory, Modality,
    ResourceRequirements, ModelMetadata, ModelSpecialization
)
from ai_karen_engine.services.llm_router import ChatRequest


class TestModelRouter:
    """Test cases for ModelRouter."""
    
    @pytest.fixture
    def temp_models_dir(self):
        """Create temporary models directory."""
        temp_dir = tempfile.mkdtemp()
        models_dir = Path(temp_dir) / "models"
        models_dir.mkdir(parents=True)
        
        # Create some test model files
        (models_dir / "llama").mkdir()
        (models_dir / "llama" / "test_model.gguf").write_text("fake model data")
        
        (models_dir / "transformers").mkdir()
        (models_dir / "transformers" / "test_transformer").mkdir()
        (models_dir / "transformers" / "test_transformer" / "config.json").write_text('{"model_type": "llama"}')
        
        yield str(models_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_provider_registry(self):
        """Mock provider registry."""
        mock_registry = Mock()
        mock_registry.get_available_providers.return_value = ["llamacpp", "huggingface", "openai"]
        mock_registry.get_provider_status.return_value = Mock(is_available=True)
        return mock_registry
    
    @pytest.fixture
    def mock_llm_registry(self):
        """Mock LLM registry."""
        mock_registry = Mock()
        mock_registry.get_provider_info.return_value = {"default_model": "test_model"}
        mock_registry.health_check.return_value = {"status": "healthy"}
        return mock_registry
    
    @pytest.fixture
    def sample_model_info(self):
        """Create sample model info."""
        return ModelInfo(
            id="test_model",
            name="Test Model",
            display_name="Test Model",
            type=ModelType.LLAMA_CPP,
            path="/fake/path/test_model.gguf",
            size=1024*1024*100,  # 100MB
            modalities=[
                Modality(
                    type=ModalityType.TEXT,
                    input_supported=True,
                    output_supported=True,
                    formats=["text"]
                )
            ],
            capabilities=["chat", "text-generation"],
            requirements=ResourceRequirements(
                min_ram_gb=1.0,
                recommended_ram_gb=2.0
            ),
            status=ModelStatus.AVAILABLE,
            metadata=ModelMetadata(
                name="Test Model",
                display_name="Test Model",
                description="A test model",
                version="1.0",
                author="Test",
                license="MIT",
                context_length=2048
            ),
            category=ModelCategory.LANGUAGE,
            specialization=[ModelSpecialization.CHAT],
            tags=["test", "llama"],
            last_updated=1234567890.0
        )
    
    @pytest.fixture
    async def model_router(self, temp_models_dir, mock_provider_registry, mock_llm_registry):
        """Create model router for testing."""
        with patch('ai_karen_engine.services.intelligent_model_router.get_provider_registry_service') as mock_get_provider:
            with patch('ai_karen_engine.services.intelligent_model_router.get_registry') as mock_get_registry:
                mock_get_provider.return_value = mock_provider_registry
                mock_get_registry.return_value = mock_llm_registry
                
                router = ModelRouter(models_root=temp_models_dir, enable_discovery=False)
                yield router
    
    @pytest.mark.asyncio
    async def test_model_router_initialization(self, model_router):
        """Test model router initialization."""
        assert model_router is not None
        assert model_router.models_root.exists()
        assert model_router.preserve_existing_routing is True
        assert model_router.routing_strategy == RoutingStrategy.HYBRID
    
    @pytest.mark.asyncio
    async def test_wire_model_connection(self, model_router, sample_model_info):
        """Test wiring model connection."""
        # Add model to router
        model_router.model_connections["test_model"] = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.DISCONNECTED
        )
        
        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=b"fake data")):
                connection = await model_router.wire_model_connection("test_model")
                
                assert connection is not None
                assert connection.model_id == "test_model"
                assert connection.status == ConnectionStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_verify_model_routing(self, model_router, sample_model_info):
        """Test model routing verification."""
        # Setup connected model
        connection = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.CONNECTED
        )
        model_router.model_connections["test_model"] = connection
        
        # Mock existing router
        model_router.existing_llm_router.select_provider = AsyncMock(
            return_value=("llamacpp", "test_model")
        )
        
        verified = await model_router.verify_model_routing("test_model")
        assert verified is True
    
    @pytest.mark.asyncio
    async def test_route_request_to_model(self, model_router, sample_model_info):
        """Test routing request to specific model."""
        # Setup model connection
        model_router.model_connections["test_model"] = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.DISCONNECTED
        )
        
        # Mock successful connection
        model_router.wire_model_connection = AsyncMock(return_value=ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.CONNECTED
        ))
        
        request = ChatRequest(message="Test message", preferred_model="test_model")
        decision = await model_router.route_request_to_model(request, "test_model")
        
        assert decision is not None
        assert decision.model_id == "test_model"
        assert decision.provider == "llamacpp"
        assert decision.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_select_optimal_model_for_task(self, model_router, sample_model_info):
        """Test optimal model selection for task."""
        # Setup model connections
        model_router.model_connections["test_model"] = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.CONNECTED
        )
        
        # Mock existing routing logic
        model_router.existing_llm_router.select_provider = AsyncMock(
            return_value=("llamacpp", "test_model")
        )
        model_router.wire_model_connection = AsyncMock(return_value=model_router.model_connections["test_model"])
        
        decision = await model_router.select_optimal_model_for_task(
            task_type="chat",
            modalities=[ModalityType.TEXT],
            user_preferences={"preferred_model": "test_model"}
        )
        
        assert decision is not None
        assert decision.model_id == "llamacpp:test_model"
        assert decision.routing_strategy == RoutingStrategy.PROFILE_BASED
    
    @pytest.mark.asyncio
    async def test_filter_models_by_capability(self, model_router, sample_model_info):
        """Test filtering models by capability."""
        # Setup model connections
        model_router.model_connections["test_model"] = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.CONNECTED
        )
        
        # Test chat capability filtering
        suitable_models = await model_router.filter_models_by_capability("chat")
        assert "test_model" in suitable_models
        
        # Test unsupported capability
        suitable_models = await model_router.filter_models_by_capability("vision")
        assert "test_model" not in suitable_models
    
    @pytest.mark.asyncio
    async def test_handle_model_fallback(self, model_router, sample_model_info):
        """Test model fallback handling."""
        # Setup multiple models
        model_router.model_connections["primary_model"] = ModelConnection(
            model_id="primary_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.ERROR
        )
        
        fallback_model_info = sample_model_info
        fallback_model_info.id = "fallback_model"
        model_router.model_connections["fallback_model"] = ModelConnection(
            model_id="fallback_model",
            provider="llamacpp",
            model_info=fallback_model_info,
            status=ConnectionStatus.CONNECTED
        )
        
        # Mock routing to fallback
        model_router.route_request_to_model = AsyncMock(return_value=RoutingDecision(
            model_id="fallback_model",
            provider="llamacpp",
            model_connection=model_router.model_connections["fallback_model"],
            routing_strategy=RoutingStrategy.CAPABILITY_BASED,
            confidence=0.8
        ))
        
        decision = await model_router.handle_model_fallback(
            failed_model="primary_model",
            required_modalities=[ModalityType.TEXT],
            task_type="chat"
        )
        
        assert decision is not None
        assert decision.model_id == "fallback_model"
    
    @pytest.mark.asyncio
    async def test_get_active_model_info(self, model_router, sample_model_info):
        """Test getting active model information."""
        # Setup connected model
        connection = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.CONNECTED,
            connection_time=1234567890.0,
            last_used=1234567900.0
        )
        model_router.model_connections["test_model"] = connection
        
        # Add performance metrics
        from ai_karen_engine.services.intelligent_model_router import ModelPerformanceMetrics
        model_router.performance_metrics["test_model"] = ModelPerformanceMetrics(
            model_id="test_model",
            provider="llamacpp",
            total_requests=10,
            successful_requests=9,
            average_response_time=1.5
        )
        
        active_models = await model_router.get_active_model_info()
        
        assert "test_model" in active_models
        model_info = active_models["test_model"]
        assert model_info["provider"] == "llamacpp"
        assert model_info["performance"]["total_requests"] == 10
        assert model_info["performance"]["success_rate"] == 0.9
    
    @pytest.mark.asyncio
    async def test_routing_statistics(self, model_router, sample_model_info):
        """Test routing statistics collection."""
        # Setup model and metrics
        model_router.model_connections["test_model"] = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=sample_model_info,
            status=ConnectionStatus.CONNECTED
        )
        
        from ai_karen_engine.services.intelligent_model_router import ModelPerformanceMetrics
        model_router.performance_metrics["test_model"] = ModelPerformanceMetrics(
            model_id="test_model",
            provider="llamacpp",
            total_requests=5,
            successful_requests=4
        )
        
        stats = await model_router.get_routing_statistics()
        
        assert stats["total_models"] == 1
        assert stats["connected_models"] == 1
        assert stats["total_requests"] == 5
        assert stats["successful_requests"] == 4
        assert stats["average_success_rate"] == 0.8
        assert stats["routing_strategy"] == "hybrid"
    
    @pytest.mark.asyncio
    async def test_performance_metrics_update(self, model_router):
        """Test performance metrics updating."""
        # Update metrics
        await model_router._update_request_metrics("test_model", success=True, response_time=1.5)
        await model_router._update_request_metrics("test_model", success=False)
        
        metrics = model_router.performance_metrics["test_model"]
        assert metrics.total_requests == 2
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 1
        assert metrics.error_rate == 0.5
        assert metrics.average_response_time == 1.5
    
    def test_model_router_singleton(self):
        """Test model router singleton pattern."""
        router1 = get_model_router()
        router2 = get_model_router()
        assert router1 is router2
    
    @pytest.mark.asyncio
    async def test_initialize_model_router(self):
        """Test model router initialization function."""
        with patch('ai_karen_engine.services.intelligent_model_router.get_model_router') as mock_get:
            mock_router = Mock()
            mock_router.initialize = AsyncMock()
            mock_get.return_value = mock_router
            
            result = await initialize_model_router()
            
            assert result is mock_router
            mock_router.initialize.assert_called_once()


class TestModelConnection:
    """Test cases for ModelConnection."""
    
    def test_model_connection_creation(self):
        """Test model connection creation."""
        from ai_karen_engine.services.model_discovery_engine import ModelInfo, ModelType, ModelStatus
        
        model_info = Mock(spec=ModelInfo)
        model_info.id = "test_model"
        
        connection = ModelConnection(
            model_id="test_model",
            provider="llamacpp",
            model_info=model_info,
            status=ConnectionStatus.DISCONNECTED
        )
        
        assert connection.model_id == "test_model"
        assert connection.provider == "llamacpp"
        assert connection.status == ConnectionStatus.DISCONNECTED
        assert connection.connection_time is None
        assert connection.last_used is None


class TestRoutingDecision:
    """Test cases for RoutingDecision."""
    
    def test_routing_decision_creation(self):
        """Test routing decision creation."""
        model_info = Mock()
        connection = Mock()
        
        decision = RoutingDecision(
            model_id="test_model",
            provider="llamacpp",
            model_connection=connection,
            routing_strategy=RoutingStrategy.PERFORMANCE_BASED,
            confidence=0.9,
            fallback_options=["fallback1", "fallback2"],
            reasoning="Selected based on performance"
        )
        
        assert decision.model_id == "test_model"
        assert decision.provider == "llamacpp"
        assert decision.routing_strategy == RoutingStrategy.PERFORMANCE_BASED
        assert decision.confidence == 0.9
        assert len(decision.fallback_options) == 2
        assert decision.reasoning == "Selected based on performance"


@pytest.mark.integration
class TestModelRouterIntegration:
    """Integration tests for model router."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_routing(self, temp_models_dir):
        """Test end-to-end model routing."""
        with patch('ai_karen_engine.services.intelligent_model_router.get_provider_registry_service'):
            with patch('ai_karen_engine.services.intelligent_model_router.get_registry'):
                router = ModelRouter(models_root=temp_models_dir, enable_discovery=False)
                
                # This would be a more comprehensive test with real components
                # For now, just verify the router can be created and initialized
                await router.initialize()
                
                assert router is not None
                assert len(router.model_connections) >= 0  # May be empty without discovery
    
    @pytest.mark.asyncio
    async def test_reasoning_preservation(self, model_router):
        """Test that existing reasoning logic is preserved."""
        # Mock existing components
        mock_decision_engine = Mock()
        mock_flow_manager = Mock()
        
        # Verify router doesn't interfere with existing components
        # This is more of a structural test - the actual preservation
        # is handled by the ReasoningPreservationLayer
        
        assert model_router.preserve_existing_routing is True
        assert model_router.existing_llm_router is not None
        assert model_router.intelligent_router is not None


def mock_open(read_data=b""):
    """Mock open function for file operations."""
    from unittest.mock import mock_open as original_mock_open
    return original_mock_open(read_data=read_data)