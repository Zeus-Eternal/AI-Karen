"""
Tests for TinyLlama service implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.ai_karen_engine.services.tinyllama_service import (
    TinyLlamaService,
    TinyLlamaConfig,
    ScaffoldResult,
    OutlineResult,
    SummaryResult,
    get_tinyllama_service
)


class TestTinyLlamaConfig:
    """Test TinyLlama configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TinyLlamaConfig()
        assert config.model_name == "tinyllama-1.1b-chat"
        assert config.max_tokens == 150
        assert config.temperature == 0.7
        assert config.enable_fallback is True
        assert config.cache_size == 1000
        assert config.cache_ttl == 1800
        assert config.scaffold_max_tokens == 100
        assert config.outline_max_tokens == 80
        assert config.summary_max_tokens == 120
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TinyLlamaConfig(
            model_name="custom-model",
            max_tokens=200,
            temperature=0.5,
            enable_fallback=False
        )
        assert config.model_name == "custom-model"
        assert config.max_tokens == 200
        assert config.temperature == 0.5
        assert config.enable_fallback is False


class TestTinyLlamaService:
    """Test TinyLlama service functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock LlamaCpp client."""
        client = Mock()
        client.health_check.return_value = {"status": "healthy"}
        client.chat.return_value = "Generated response"
        return client
    
    @pytest.fixture
    def service_with_mock(self, mock_client):
        """TinyLlama service with mocked client."""
        with patch('src.ai_karen_engine.services.tinyllama_service.llamacpp_inprocess_client', mock_client):
            with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', True):
                service = TinyLlamaService()
                service.client = mock_client
                return service
    
    @pytest.fixture
    def fallback_service(self):
        """TinyLlama service in fallback mode."""
        with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', False):
            return TinyLlamaService()
    
    def test_initialization_with_client(self, service_with_mock):
        """Test service initialization with working client."""
        assert service_with_mock.client is not None
        assert service_with_mock.fallback_mode is False
    
    def test_initialization_fallback_mode(self, fallback_service):
        """Test service initialization in fallback mode."""
        assert fallback_service.client is None
        assert fallback_service.fallback_mode is True
    
    @pytest.mark.asyncio
    async def test_generate_scaffold_with_client(self, service_with_mock):
        """Test scaffold generation with working client."""
        result = await service_with_mock.generate_scaffold("Test input", "reasoning")
        
        assert isinstance(result, ScaffoldResult)
        assert result.content == "Generated response"
        assert result.used_fallback is False
        assert result.input_length == len("Test input")
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_generate_scaffold_fallback(self, fallback_service):
        """Test scaffold generation in fallback mode."""
        result = await fallback_service.generate_scaffold("Test input for reasoning", "reasoning")
        
        assert isinstance(result, ScaffoldResult)
        assert result.used_fallback is True
        assert "Analyze" in result.content
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_generate_outline_with_client(self, service_with_mock):
        """Test outline generation with working client."""
        service_with_mock.client.chat.return_value = "- Point 1\n- Point 2\n- Point 3"
        
        result = await service_with_mock.generate_outline("Test input", "bullet", 3)
        
        assert isinstance(result, OutlineResult)
        assert len(result.outline) == 3
        assert result.used_fallback is False
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_generate_outline_fallback(self, fallback_service):
        """Test outline generation in fallback mode."""
        result = await fallback_service.generate_outline("First sentence. Second sentence. Third sentence.", "bullet", 3)
        
        assert isinstance(result, OutlineResult)
        assert len(result.outline) >= 1
        assert result.used_fallback is True
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_generate_short_fill(self, service_with_mock):
        """Test short generative fill."""
        result = await service_with_mock.generate_short_fill("Context", "Complete this")
        
        assert isinstance(result, ScaffoldResult)
        assert result.content == "Generated response"
        assert result.used_fallback is False
    
    @pytest.mark.asyncio
    async def test_summarize_context_with_client(self, service_with_mock):
        """Test context summarization with working client."""
        result = await service_with_mock.summarize_context("Long text to summarize", "concise")
        
        assert isinstance(result, SummaryResult)
        assert result.summary == "Generated response"
        assert result.used_fallback is False
        assert result.compression_ratio > 0
    
    @pytest.mark.asyncio
    async def test_summarize_context_fallback(self, fallback_service):
        """Test context summarization in fallback mode."""
        text = "First sentence. Second sentence. Third sentence."
        result = await fallback_service.summarize_context(text, "concise")
        
        assert isinstance(result, SummaryResult)
        assert result.used_fallback is True
        assert len(result.summary) > 0
        assert result.compression_ratio > 0
    
    @pytest.mark.asyncio
    async def test_empty_input_handling(self, service_with_mock):
        """Test handling of empty inputs."""
        scaffold_result = await service_with_mock.generate_scaffold("", "reasoning")
        assert scaffold_result.content == ""
        assert scaffold_result.used_fallback is True
        
        outline_result = await service_with_mock.generate_outline("", "bullet")
        assert outline_result.outline == []
        assert outline_result.used_fallback is True
        
        summary_result = await service_with_mock.summarize_context("", "concise")
        assert summary_result.summary == ""
        assert summary_result.used_fallback is True
    
    def test_cache_functionality(self, service_with_mock):
        """Test caching functionality."""
        # Clear cache first
        service_with_mock.clear_cache()
        
        # Check cache is empty
        assert len(service_with_mock.cache) == 0
        
        # Generate cache key
        cache_key = service_with_mock._get_cache_key("test")
        assert cache_key.startswith("tinyllama:")
    
    def test_health_status(self, service_with_mock):
        """Test health status reporting."""
        health = service_with_mock.get_health_status()
        
        assert health.is_healthy is True
        assert health.model_loaded is True
        assert health.fallback_mode is False
        assert health.cache_size >= 0
        assert health.error_count >= 0
    
    def test_health_status_fallback(self, fallback_service):
        """Test health status in fallback mode."""
        health = fallback_service.get_health_status()
        
        assert health.is_healthy is True  # Still healthy due to fallback
        assert health.model_loaded is False
        assert health.fallback_mode is True
    
    def test_reset_metrics(self, service_with_mock):
        """Test metrics reset functionality."""
        # Add some metrics
        service_with_mock._cache_hits = 10
        service_with_mock._cache_misses = 5
        service_with_mock._error_count = 2
        
        # Reset metrics
        service_with_mock.reset_metrics()
        
        # Check metrics are reset
        assert service_with_mock._cache_hits == 0
        assert service_with_mock._cache_misses == 0
        assert service_with_mock._error_count == 0
    
    @pytest.mark.asyncio
    async def test_error_handling_with_fallback(self, service_with_mock):
        """Test error handling with fallback enabled."""
        # Make client raise an exception
        service_with_mock.client.chat.side_effect = Exception("Test error")
        
        result = await service_with_mock.generate_scaffold("Test input", "reasoning")
        
        # Should fallback to rule-based generation
        assert result.used_fallback is True
        assert result.content != ""
        assert service_with_mock._error_count > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_without_fallback(self):
        """Test error handling with fallback disabled."""
        config = TinyLlamaConfig(enable_fallback=False)
        
        with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', True):
            mock_client = Mock()
            mock_client.health_check.return_value = {"status": "healthy"}
            mock_client.chat.side_effect = Exception("Test error")
            
            with patch('src.ai_karen_engine.services.tinyllama_service.llamacpp_inprocess_client', mock_client):
                service = TinyLlamaService(config)
                service.client = mock_client
                
                with pytest.raises(Exception):
                    await service.generate_scaffold("Test input", "reasoning")


class TestFactoryFunction:
    """Test factory function."""
    
    def test_get_tinyllama_service(self):
        """Test factory function returns service instance."""
        with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', False):
            service = get_tinyllama_service()
            assert isinstance(service, TinyLlamaService)
    
    def test_get_tinyllama_service_with_config(self):
        """Test factory function with custom config."""
        config = TinyLlamaConfig(model_name="custom-model")
        
        with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', False):
            service = get_tinyllama_service(config)
            assert isinstance(service, TinyLlamaService)
            assert service.config.model_name == "custom-model"


class TestScaffoldTypes:
    """Test different scaffold types."""
    
    @pytest.fixture
    def fallback_service(self):
        """Service in fallback mode for testing rule-based generation."""
        with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', False):
            return TinyLlamaService()
    
    @pytest.mark.asyncio
    async def test_reasoning_scaffold_fallback(self, fallback_service):
        """Test reasoning scaffold in fallback mode."""
        result = await fallback_service.generate_scaffold("Complex problem to solve", "reasoning")
        assert "Analyze" in result.content
        assert "Consider" in result.content
        assert "Conclude" in result.content
    
    @pytest.mark.asyncio
    async def test_structure_scaffold_fallback(self, fallback_service):
        """Test structure scaffold in fallback mode."""
        result = await fallback_service.generate_scaffold("Long text with multiple concepts and ideas", "structure")
        assert "Introduction" in result.content or "Main content" in result.content
    
    @pytest.mark.asyncio
    async def test_fill_scaffold_fallback(self, fallback_service):
        """Test fill scaffold in fallback mode."""
        result = await fallback_service.generate_scaffold("The weather today is", "fill")
        assert "continuing" in result.content.lower()


class TestOutlineStyles:
    """Test different outline styles."""
    
    @pytest.fixture
    def fallback_service(self):
        """Service in fallback mode for testing rule-based generation."""
        with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', False):
            return TinyLlamaService()
    
    @pytest.mark.asyncio
    async def test_bullet_outline_fallback(self, fallback_service):
        """Test bullet outline in fallback mode."""
        text = "First point. Second point. Third point."
        result = await fallback_service.generate_outline(text, "bullet", 3)
        assert len(result.outline) >= 1
        assert all(len(point) > 0 for point in result.outline)
    
    @pytest.mark.asyncio
    async def test_numbered_outline_fallback(self, fallback_service):
        """Test numbered outline in fallback mode."""
        text = "First concept. Second concept. Third concept."
        result = await fallback_service.generate_outline(text, "numbered", 3)
        assert len(result.outline) >= 1
    
    @pytest.mark.asyncio
    async def test_structured_outline_fallback(self, fallback_service):
        """Test structured outline in fallback mode."""
        text = "Main idea with supporting details and examples."
        result = await fallback_service.generate_outline(text, "structured", 3)
        assert len(result.outline) >= 1


class TestSummaryTypes:
    """Test different summary types."""
    
    @pytest.fixture
    def fallback_service(self):
        """Service in fallback mode for testing rule-based generation."""
        with patch('src.ai_karen_engine.services.tinyllama_service.LLAMACPP_AVAILABLE', False):
            return TinyLlamaService()
    
    @pytest.mark.asyncio
    async def test_concise_summary_fallback(self, fallback_service):
        """Test concise summary in fallback mode."""
        text = "First sentence with important information. Second sentence with more details."
        result = await fallback_service.summarize_context(text, "concise")
        assert len(result.summary) > 0
        assert len(result.summary) <= len(text)
    
    @pytest.mark.asyncio
    async def test_detailed_summary_fallback(self, fallback_service):
        """Test detailed summary in fallback mode."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        result = await fallback_service.summarize_context(text, "detailed")
        assert len(result.summary) > 0
    
    @pytest.mark.asyncio
    async def test_key_points_summary_fallback(self, fallback_service):
        """Test key points summary in fallback mode."""
        text = "Important point one. Important point two. Important point three."
        result = await fallback_service.summarize_context(text, "key_points")
        assert "Key points:" in result.summary