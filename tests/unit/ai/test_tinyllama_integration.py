"""
Integration tests for TinyLlama service with orchestration agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from ai_karen_engine.services.orchestration_agent import OrchestrationAgent, OrchestrationInput
from ai_karen_engine.services.tinyllama_service import TinyLlamaService


class TestTinyLlamaIntegration:
    """Test TinyLlama integration with orchestration agent."""
    
    @pytest.mark.asyncio
    async def test_scaffolding_task_routing(self):
        """Test that scaffolding tasks are routed to TinyLlama service."""
        # Create orchestration agent
        agent = OrchestrationAgent()
        
        # Test scaffolding task detection
        input_data = OrchestrationInput(message="Create an outline for my presentation")
        task_type = await agent._infer_task_type(input_data)
        assert task_type == "scaffolding"
        
        # Test full orchestration response
        result = await agent.orchestrate_response(input_data)
        
        # Verify response structure
        assert "final" in result
        assert "meta" in result
        assert "suggestions" in result
        
        # Verify routing metadata
        meta = result["meta"]
        assert "Helper: TinyLlama" in meta.get("annotations", [])
        assert meta.get("provider") == "Helper"
        
        # Verify routing information
        routing = meta.get("routing", {})
        assert routing.get("task") == "scaffolding"
        assert "TinyLlama" in routing.get("rationale", "")
    
    @pytest.mark.asyncio
    async def test_helper_prefix_building(self):
        """Test that TinyLlama is used for building helper prefixes."""
        agent = OrchestrationAgent()
        
        input_data = OrchestrationInput(message="Explain machine learning concepts")
        
        # Test helper prefix building
        prefix = await agent._build_helper_prefix(input_data)
        
        # Should contain scaffolding information
        assert len(prefix) > 0
        # In fallback mode, should contain either scaffold or outline
        assert "scaffold" in prefix.lower() or "outline" in prefix.lower()
    
    @pytest.mark.asyncio
    async def test_available_helpers_tracking(self):
        """Test that TinyLlama is tracked in available helpers."""
        agent = OrchestrationAgent()
        
        helpers = agent._get_available_helpers()
        
        # TinyLlama should be available (even in fallback mode)
        assert "TinyLlama" in helpers
        
        # Other helpers should also be available
        assert "DistilBERT" in helpers
        assert "spaCy" in helpers
    
    @pytest.mark.asyncio
    async def test_different_scaffold_types(self):
        """Test different types of scaffolding requests."""
        agent = OrchestrationAgent()
        
        # Test outline request
        outline_input = OrchestrationInput(message="Create an outline for project management")
        outline_result = await agent.orchestrate_response(outline_input)
        assert "outline" in outline_result["final"].lower()
        
        # Test structure request
        structure_input = OrchestrationInput(message="Structure this information about AI")
        structure_result = await agent.orchestrate_response(structure_input)
        assert "structure" in structure_result["final"].lower() or "scaffold" in structure_result["final"].lower()
        
        # Test summarize request
        summary_input = OrchestrationInput(message="Summarize the key points of this discussion")
        summary_result = await agent.orchestrate_response(summary_input)
        assert "summary" in summary_result["final"].lower() or "key points" in summary_result["final"].lower()
    
    @pytest.mark.asyncio
    async def test_tinyllama_service_health_integration(self):
        """Test that TinyLlama service health is properly integrated."""
        agent = OrchestrationAgent()
        
        # Check TinyLlama service health
        if agent.tinyllama_service:
            health = agent.tinyllama_service.get_health_status()
            
            # Should be healthy (even in fallback mode)
            assert health.is_healthy is True
            
            # Should have proper fallback mode setting
            assert isinstance(health.fallback_mode, bool)
            
            # Should have monitoring metrics
            assert health.cache_size >= 0
            assert health.error_count >= 0
    
    @pytest.mark.asyncio
    async def test_fallback_mode_functionality(self):
        """Test that TinyLlama works correctly in fallback mode."""
        # Create service in fallback mode
        service = TinyLlamaService()
        
        # Should be in fallback mode due to missing model
        assert service.fallback_mode is True
        
        # Test scaffold generation
        scaffold_result = await service.generate_scaffold("Test reasoning task", "reasoning")
        assert scaffold_result.used_fallback is True
        assert len(scaffold_result.content) > 0
        assert "Analyze" in scaffold_result.content
        
        # Test outline generation
        outline_result = await service.generate_outline("Point one. Point two. Point three.", "bullet", 3)
        assert outline_result.used_fallback is True
        assert len(outline_result.outline) > 0
        
        # Test summarization
        summary_result = await service.summarize_context("Long text with multiple sentences and ideas.", "concise")
        assert summary_result.used_fallback is True
        assert len(summary_result.summary) > 0
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self):
        """Test that TinyLlama service caching works correctly."""
        service = TinyLlamaService()
        
        # Clear cache
        service.clear_cache()
        initial_cache_size = len(service.cache)
        
        # Generate scaffold (should cache result)
        await service.generate_scaffold("Test input for caching", "reasoning")
        
        # Cache should have increased
        assert len(service.cache) > initial_cache_size
        
        # Generate same scaffold again (should hit cache)
        initial_hits = service._cache_hits
        await service.generate_scaffold("Test input for caching", "reasoning")
        
        # Cache hits should have increased
        assert service._cache_hits > initial_hits
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and graceful degradation."""
        service = TinyLlamaService()
        
        # Test with empty input
        empty_result = await service.generate_scaffold("", "reasoning")
        assert empty_result.content == ""
        assert empty_result.used_fallback is True
        
        # Test with very long input (should handle gracefully)
        long_input = "Very long text. " * 1000
        long_result = await service.generate_scaffold(long_input, "reasoning")
        assert len(long_result.content) > 0
        assert long_result.used_fallback is True  # Should use fallback due to no real model
    
    def test_configuration_integration(self):
        """Test that TinyLlama configuration is properly integrated."""
        from ai_karen_engine.services.nlp_config import TinyLlamaConfig, NLPConfig
        
        # Test TinyLlama config
        config = TinyLlamaConfig()
        assert config.model_name == "tinyllama-1.1b-chat"
        assert config.scaffold_max_tokens == 100
        assert config.outline_max_tokens == 80
        assert config.summary_max_tokens == 120
        
        # Test NLP config integration
        nlp_config = NLPConfig()
        assert nlp_config.tinyllama is not None
        assert isinstance(nlp_config.tinyllama, TinyLlamaConfig)
    
    @pytest.mark.asyncio
    async def test_requirements_compliance(self):
        """Test compliance with task requirements."""
        service = TinyLlamaService()
        
        # Requirement 3.1: Fast reasoning scaffolding and outline generation
        reasoning_result = await service.generate_scaffold("Complex problem", "reasoning")
        assert reasoning_result.processing_time < 5.0  # Should be fast
        assert len(reasoning_result.content) > 0
        
        outline_result = await service.generate_outline("Topic with multiple aspects", "bullet", 5)
        assert outline_result.processing_time < 5.0  # Should be fast
        assert len(outline_result.outline) > 0
        
        # Requirement 3.2: Conversation outlines and quick scaffolding interface
        quick_scaffold = await service.generate_scaffold("Quick task", "structure", max_tokens=50)
        assert quick_scaffold.output_tokens <= 50  # Should respect token limits
        assert len(quick_scaffold.content) > 0
        
        # Requirement 3.3: Short generative fills and context summarization
        short_fill = await service.generate_short_fill("Context", "Complete this", max_tokens=30)
        assert short_fill.output_tokens <= 30  # Should be short
        assert len(short_fill.content) > 0
        
        summary = await service.summarize_context("Long context with details and more information", "concise")
        assert summary.compression_ratio <= 1.0  # Should compress or maintain content
        assert len(summary.summary) > 0


if __name__ == "__main__":
    # Run a simple test
    async def main():
        test = TestTinyLlamaIntegration()
        await test.test_scaffolding_task_routing()
        print("✓ Scaffolding task routing test passed")
        
        await test.test_helper_prefix_building()
        print("✓ Helper prefix building test passed")
        
        await test.test_available_helpers_tracking()
        print("✓ Available helpers tracking test passed")
        
        await test.test_fallback_mode_functionality()
        print("✓ Fallback mode functionality test passed")
        
        await test.test_requirements_compliance()
        print("✓ Requirements compliance test passed")
        
        print("\n🎉 All TinyLlama integration tests passed!")
    
    asyncio.run(main())