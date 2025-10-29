"""
Comprehensive Model Routing Tests
Validates that selected models are actually used for responses and routing works correctly.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, Optional

from src.ai_karen_engine.services.intelligent_model_router import IntelligentModelRouter
from src.ai_karen_engine.services.model_connection_manager import ModelConnectionManager
from src.ai_karen_engine.services.reasoning_preservation_layer import ReasoningPreservationLayer
from src.ai_karen_engine.core.shared_types import (
    ModelInfo, ModelType, Modality, ModelStatus, QueryAnalysis, 
    ComplexityLevel, ContentType, ResponseLength, ExpertiseLevel
)


class TestModelRoutingValidation:
    """Test suite for comprehensive model routing validation."""
    
    @pytest.fixture
    async def model_router(self):
        """Create a model router for testing."""
        router = IntelligentModelRouter()
        await router.initialize()
        return router
    
    @pytest.fixture
    async def connection_manager(self):
        """Create a connection manager for testing."""
        manager = ModelConnectionManager()
        await manager.initialize()
        return manager
    
    @pytest.fixture
    async def reasoning_layer(self):
        """Create a reasoning preservation layer for testing."""
        layer = ReasoningPreservationLayer()
        await layer.initialize()
        return layer
    
    @pytest.fixture
    def sample_models(self):
        """Create sample models for testing."""
        return [
            ModelInfo(
                id="llama-2-7b",
                name="Llama 2 7B",
                display_name="Llama 2 7B Chat",
                type=ModelType.LLAMA_CPP,
                path="/models/llama-cpp/llama-2-7b.gguf",
                size=3500000000,
                modalities=[Modality.TEXT],
                capabilities=["CHAT", "REASONING"],
                status=ModelStatus.AVAILABLE,
                metadata=Mock(),
                category=Mock(primary="LANGUAGE", secondary="CHAT")
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                display_name="GPT-3.5 Turbo",
                type=ModelType.OPENAI,
                path="gpt-3.5-turbo",
                size=0,
                modalities=[Modality.TEXT],
                capabilities=["CHAT", "CODE", "REASONING"],
                status=ModelStatus.AVAILABLE,
                metadata=Mock(),
                category=Mock(primary="LANGUAGE", secondary="CHAT")
            ),
            ModelInfo(
                id="clip-vit-base",
                name="CLIP ViT Base",
                display_name="CLIP Vision Transformer",
                type=ModelType.VISION,
                path="/models/vision/clip-vit-base",
                size=400000000,
                modalities=[Modality.TEXT, Modality.IMAGE],
                capabilities=["VISION", "MULTIMODAL"],
                status=ModelStatus.AVAILABLE,
                metadata=Mock(),
                category=Mock(primary="VISION", secondary="MULTIMODAL")
            )
        ]
    
    @pytest.mark.asyncio
    async def test_model_connection_establishment(self, model_router, connection_manager, sample_models):
        """Test that model connections are properly established."""
        # Mock the model registry
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            for model in sample_models:
                # Test connection establishment
                connection = await connection_manager.establish_connection(model.id)
                assert connection is not None, f"Failed to establish connection to {model.id}"
                
                # Verify connection is active
                is_active = await connection_manager.is_connection_active(model.id)
                assert is_active, f"Connection to {model.id} is not active"
    
    @pytest.mark.asyncio
    async def test_model_routing_verification(self, model_router, sample_models):
        """Test that requests are routed to the correct model."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Test routing to specific model
            selected_model_id = "llama-2-7b"
            
            # Mock the actual model call to verify routing
            with patch.object(model_router, '_call_model') as mock_call:
                mock_call.return_value = AsyncMock(return_value="Test response")
                
                query = "What is the capital of France?"
                response = await model_router.route_request_to_model(query, selected_model_id)
                
                # Verify the correct model was called
                mock_call.assert_called_once()
                call_args = mock_call.call_args
                assert call_args[0][1] == selected_model_id, f"Wrong model called: expected {selected_model_id}"
    
    @pytest.mark.asyncio
    async def test_model_selection_by_modality(self, model_router, sample_models):
        """Test that models are selected based on required modalities."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Test text-only query
            text_model = await model_router.select_optimal_model_for_task(
                task_type="chat",
                modalities=[Modality.TEXT]
            )
            assert text_model in ["llama-2-7b", "gpt-3.5-turbo"], "Should select text-capable model"
            
            # Test multimodal query
            multimodal_model = await model_router.select_optimal_model_for_task(
                task_type="vision",
                modalities=[Modality.TEXT, Modality.IMAGE]
            )
            assert multimodal_model == "clip-vit-base", "Should select multimodal model for vision tasks"
    
    @pytest.mark.asyncio
    async def test_model_fallback_mechanism(self, model_router, sample_models):
        """Test that fallback works when primary model fails."""
        # Make first model unavailable
        unavailable_models = sample_models.copy()
        unavailable_models[0].status = ModelStatus.ERROR
        
        with patch.object(model_router, 'get_available_models', return_value=unavailable_models):
            # Test fallback selection
            fallback_model = await model_router.handle_model_fallback(
                failed_model="llama-2-7b",
                required_modalities=[Modality.TEXT]
            )
            
            assert fallback_model != "llama-2-7b", "Should not select failed model"
            assert fallback_model in ["gpt-3.5-turbo"], "Should select available fallback model"
    
    @pytest.mark.asyncio
    async def test_active_model_tracking(self, model_router, sample_models):
        """Test that active model information is correctly tracked."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Set active model
            await model_router.set_active_model("gpt-3.5-turbo")
            
            # Verify active model info
            active_model = await model_router.get_active_model_info()
            assert active_model is not None, "Active model info should be available"
            assert active_model.id == "gpt-3.5-turbo", "Active model ID should match selected model"
    
    @pytest.mark.asyncio
    async def test_model_capability_filtering(self, model_router, sample_models):
        """Test that models are filtered by capabilities."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Filter by chat capability
            chat_models = await model_router.filter_models_by_capability("CHAT")
            chat_model_ids = [model.id for model in chat_models]
            
            assert "llama-2-7b" in chat_model_ids, "Llama model should support chat"
            assert "gpt-3.5-turbo" in chat_model_ids, "GPT model should support chat"
            assert "clip-vit-base" not in chat_model_ids, "Vision model should not be in chat results"
            
            # Filter by vision capability
            vision_models = await model_router.filter_models_by_capability("VISION")
            vision_model_ids = [model.id for model in vision_models]
            
            assert "clip-vit-base" in vision_model_ids, "CLIP model should support vision"
            assert "llama-2-7b" not in vision_model_ids, "Text model should not be in vision results"
    
    @pytest.mark.asyncio
    async def test_model_recommendation_system(self, model_router, sample_models):
        """Test that model recommendations work correctly."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Test recommendation for code query
            code_query_analysis = QueryAnalysis(
                complexity=ComplexityLevel.MODERATE,
                content_type=ContentType.CODE,
                expected_response_length=ResponseLength.MEDIUM,
                user_expertise_level=ExpertiseLevel.INTERMEDIATE,
                context_requirements=[],
                processing_priority="NORMAL"
            )
            
            recommendations = await model_router.recommend_model_for_query(code_query_analysis)
            assert len(recommendations) > 0, "Should provide model recommendations"
            
            # GPT-3.5 should be recommended for code tasks
            recommended_ids = [model.id for model in recommendations]
            assert "gpt-3.5-turbo" in recommended_ids, "GPT should be recommended for code tasks"
    
    @pytest.mark.asyncio
    async def test_reasoning_preservation_integration(self, model_router, reasoning_layer, sample_models):
        """Test that existing reasoning logic is preserved during routing."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Mock existing decision engine
            mock_decision_engine = Mock()
            mock_decision_engine.analyze_intent = AsyncMock(return_value="chat")
            mock_decision_engine.select_tools = AsyncMock(return_value=[])
            
            # Wrap with reasoning preservation
            wrapped_engine = await reasoning_layer.wrap_decision_engine(mock_decision_engine)
            
            # Test that original methods are still called
            intent = await wrapped_engine.analyze_intent("Hello, how are you?")
            assert intent == "chat", "Original intent analysis should be preserved"
            
            # Verify original method was called
            mock_decision_engine.analyze_intent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_model_switching_lifecycle(self, model_router, connection_manager, sample_models):
        """Test complete model switching lifecycle."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Start with first model
            initial_model = "llama-2-7b"
            await model_router.set_active_model(initial_model)
            
            # Verify initial connection
            initial_connection = await connection_manager.get_connection(initial_model)
            assert initial_connection is not None, "Initial connection should be established"
            
            # Switch to different model
            new_model = "gpt-3.5-turbo"
            await model_router.switch_model(new_model)
            
            # Verify new connection and old cleanup
            new_connection = await connection_manager.get_connection(new_model)
            assert new_connection is not None, "New connection should be established"
            
            # Verify active model changed
            active_model = await model_router.get_active_model_info()
            assert active_model.id == new_model, "Active model should be updated"
    
    @pytest.mark.asyncio
    async def test_concurrent_model_requests(self, model_router, sample_models):
        """Test handling of concurrent requests to different models."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Mock model calls with delays to simulate real processing
            async def mock_model_call(query, model_id):
                await asyncio.sleep(0.1)  # Simulate processing time
                return f"Response from {model_id}: {query}"
            
            with patch.object(model_router, '_call_model', side_effect=mock_model_call):
                # Create concurrent requests
                tasks = [
                    model_router.route_request_to_model("Query 1", "llama-2-7b"),
                    model_router.route_request_to_model("Query 2", "gpt-3.5-turbo"),
                    model_router.route_request_to_model("Query 3", "llama-2-7b")
                ]
                
                # Execute concurrently
                responses = await asyncio.gather(*tasks)
                
                # Verify all responses received
                assert len(responses) == 3, "Should receive all responses"
                assert "llama-2-7b" in responses[0], "First response should be from Llama"
                assert "gpt-3.5-turbo" in responses[1], "Second response should be from GPT"
                assert "llama-2-7b" in responses[2], "Third response should be from Llama"
    
    @pytest.mark.asyncio
    async def test_model_performance_tracking(self, model_router, sample_models):
        """Test that model performance is tracked during routing."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Mock performance tracking
            performance_data = {}
            
            async def mock_track_performance(model_id, response_time, success):
                if model_id not in performance_data:
                    performance_data[model_id] = []
                performance_data[model_id].append({
                    'response_time': response_time,
                    'success': success
                })
            
            with patch.object(model_router, 'track_model_performance', side_effect=mock_track_performance):
                # Make requests to track performance
                await model_router.route_request_to_model("Test query", "llama-2-7b")
                await model_router.route_request_to_model("Another query", "gpt-3.5-turbo")
                
                # Verify performance tracking
                assert "llama-2-7b" in performance_data, "Performance should be tracked for Llama"
                assert "gpt-3.5-turbo" in performance_data, "Performance should be tracked for GPT"
                
                # Verify tracking data structure
                for model_id, metrics in performance_data.items():
                    assert len(metrics) > 0, f"Should have metrics for {model_id}"
                    for metric in metrics:
                        assert 'response_time' in metric, "Should track response time"
                        assert 'success' in metric, "Should track success status"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_model(self, model_router, sample_models):
        """Test error handling when routing to invalid models."""
        with patch.object(model_router, 'get_available_models', return_value=sample_models):
            # Test routing to non-existent model
            with pytest.raises(ValueError, match="Model not found"):
                await model_router.route_request_to_model("Test query", "non-existent-model")
            
            # Test routing to unavailable model
            unavailable_model = sample_models[0]
            unavailable_model.status = ModelStatus.ERROR
            
            with pytest.raises(RuntimeError, match="Model unavailable"):
                await model_router.route_request_to_model("Test query", unavailable_model.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])