"""
Tests for LLM Optimization - Task 8.2
Tests LLM generation optimization to ensure p95 first-token latency < 1.2 seconds
with model preloading, warming strategies, and local-first routing.
"""

import asyncio
import pytest
import time
from typing import List, Dict, Any, AsyncIterator
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.llm_optimization import (
    OptimizedLLMService, ModelConfig, ModelType, WarmupStrategy,
    ModelPreloader, ResponseCache, GenerationMetrics, ModelState
)

class MockProvider:
    """Mock LLM provider for testing"""
    
    def __init__(self, name: str, latency_ms: float = 100.0):
        self.name = name
        self.latency_ms = latency_ms
        self.call_count = 0
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Mock response generation"""
        self.call_count += 1
        
        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        return f"Response from {self.name} for: {prompt[:50]}..."
    
    async def stream_response(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Mock streaming response"""
        self.call_count += 1
        
        # Simulate first token latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        # Stream response in chunks
        response = f"Streaming response from {self.name} for: {prompt[:30]}..."
        words = response.split()
        
        for word in words:
            yield word + " "
            await asyncio.sleep(0.01)  # Small delay between tokens

class TestModelPreloader:
    """Test model preloading functionality"""
    
    @pytest.fixture
    def preloader(self):
        """Create model preloader"""
        return ModelPreloader(max_workers=2)
    
    @pytest.fixture
    def test_config(self):
        """Create test model configuration"""
        return ModelConfig(
            name="test_model",
            provider="test_provider",
            model_type=ModelType.LOCAL,
            warmup_strategy=WarmupStrategy.EAGER,
            preload_enabled=True,
            warmup_prompts=["Hello", "Test prompt"]
        )
    
    @pytest.mark.asyncio
    async def test_preload_local_model(self, preloader, test_config):
        """Test preloading local model"""
        result = await preloader.preload_model(test_config)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_preload_remote_model(self, preloader):
        """Test preloading remote API model"""
        config = ModelConfig(
            name="remote_model",
            provider="openai",
            model_type=ModelType.REMOTE_API,
            warmup_strategy=WarmupStrategy.LAZY
        )
        
        result = await preloader.preload_model(config)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_warm_model(self, preloader, test_config):
        """Test model warming"""
        mock_provider = MockProvider("test_provider", latency_ms=50.0)
        
        warmup_time = await preloader.warm_model(test_config, mock_provider)
        
        assert warmup_time > 0
        assert mock_provider.call_count == len(test_config.warmup_prompts)

class TestResponseCache:
    """Test response caching functionality"""
    
    @pytest.fixture
    def cache(self):
        """Create response cache"""
        return ResponseCache(max_size=10, ttl_seconds=60)
    
    def test_cache_put_and_get(self, cache):
        """Test basic cache operations"""
        prompt = "Test prompt"
        model_name = "test_model"
        response = "Test response"
        
        # Cache should be empty initially
        assert cache.get(prompt, model_name) is None
        
        # Put response in cache
        cache.put(prompt, model_name, response)
        
        # Should retrieve cached response
        cached_response = cache.get(prompt, model_name)
        assert cached_response == response
    
    def test_cache_expiry(self, cache):
        """Test cache expiry"""
        # Set very short TTL
        cache.ttl_seconds = 0.1
        
        prompt = "Test prompt"
        model_name = "test_model"
        response = "Test response"
        
        cache.put(prompt, model_name, response)
        
        # Should get response immediately
        assert cache.get(prompt, model_name) == response
        
        # Wait for expiry
        time.sleep(0.2)
        
        # Should be expired
        assert cache.get(prompt, model_name) is None
    
    def test_cache_eviction(self, cache):
        """Test cache eviction when full"""
        # Fill cache to capacity
        for i in range(cache.max_size):
            cache.put(f"prompt_{i}", "test_model", f"response_{i}")
        
        assert len(cache.cache) == cache.max_size
        
        # Add one more item (should evict oldest)
        cache.put("new_prompt", "test_model", "new_response")
        
        # Cache should still be at max size
        assert len(cache.cache) == cache.max_size
        
        # New item should be in cache
        assert cache.get("new_prompt", "test_model") == "new_response"
    
    def test_cache_key_generation(self, cache):
        """Test cache key generation with different parameters"""
        prompt = "Test prompt"
        model_name = "test_model"
        
        # Same parameters should generate same key
        key1 = cache._generate_cache_key(prompt, model_name, max_tokens=100, temperature=0.7)
        key2 = cache._generate_cache_key(prompt, model_name, max_tokens=100, temperature=0.7)
        assert key1 == key2
        
        # Different parameters should generate different keys
        key3 = cache._generate_cache_key(prompt, model_name, max_tokens=200, temperature=0.7)
        assert key1 != key3

class TestOptimizedLLMService:
    """Test optimized LLM service functionality"""
    
    @pytest.fixture
    def test_configs(self):
        """Create test model configurations"""
        return [
            ModelConfig(
                name="local_model",
                provider="ollama",
                model_type=ModelType.LOCAL,
                warmup_strategy=WarmupStrategy.EAGER,
                preload_enabled=True,
                cache_responses=True
            ),
            ModelConfig(
                name="remote_model",
                provider="openai",
                model_type=ModelType.REMOTE_API,
                warmup_strategy=WarmupStrategy.LAZY,
                preload_enabled=False,
                cache_responses=True
            )
        ]
    
    @pytest.fixture
    def llm_service(self, test_configs):
        """Create optimized LLM service"""
        return OptimizedLLMService(test_configs)
    
    def test_service_initialization(self, llm_service, test_configs):
        """Test service initialization"""
        assert len(llm_service.configs) == len(test_configs)
        assert len(llm_service.model_states) == len(test_configs)
        
        # Check model states are initialized
        for config in test_configs:
            assert config.name in llm_service.model_states
            state = llm_service.model_states[config.name]
            assert isinstance(state, ModelState)
            assert state.name == config.name
    
    def test_get_model_config(self, llm_service):
        """Test getting model configuration"""
        config = llm_service._get_model_config("local_model")
        assert config is not None
        assert config.name == "local_model"
        
        # Non-existent model should return None
        config = llm_service._get_model_config("non_existent")
        assert config is None
    
    @pytest.mark.asyncio
    async def test_select_optimal_model(self, llm_service):
        """Test optimal model selection"""
        # Mark local model as warmed
        llm_service.model_states["local_model"].is_warmed = True
        llm_service.model_states["local_model"].avg_first_token_latency = 100.0
        
        selected_model = await llm_service._select_optimal_model("test prompt")
        
        # Should prefer local model
        assert selected_model == "local_model"
    
    @pytest.mark.asyncio
    async def test_generate_optimized_with_mock(self, llm_service):
        """Test optimized generation with mocked provider"""
        mock_provider = MockProvider("test_provider", latency_ms=50.0)
        
        with patch.object(llm_service, '_get_provider_instance', new_callable=AsyncMock) as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            # Test non-streaming generation
            response_parts = []
            async for chunk in llm_service.generate_optimized(
                "Test prompt",
                model_name="local_model",
                stream=False
            ):
                response_parts.append(chunk)
            
            assert len(response_parts) == 1
            assert "Response from test_provider" in response_parts[0]
            assert mock_provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_generate_optimized_streaming(self, llm_service):
        """Test optimized streaming generation"""
        mock_provider = MockProvider("test_provider", latency_ms=30.0)
        
        with patch.object(llm_service, '_get_provider_instance', new_callable=AsyncMock) as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            # Test streaming generation
            response_parts = []
            start_time = time.time()
            first_chunk_time = None
            
            async for chunk in llm_service.generate_optimized(
                "Test prompt for streaming",
                model_name="local_model",
                stream=True
            ):
                if first_chunk_time is None:
                    first_chunk_time = time.time()
                response_parts.append(chunk)
            
            total_time = time.time() - start_time
            first_token_latency = (first_chunk_time - start_time) * 1000 if first_chunk_time else 0
            
            assert len(response_parts) > 1  # Should have multiple chunks
            assert first_token_latency < 1200  # Should meet first-token SLO
            assert mock_provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, llm_service):
        """Test response caching"""
        mock_provider = MockProvider("test_provider", latency_ms=100.0)
        
        with patch.object(llm_service, '_get_provider_instance', new_callable=AsyncMock) as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            prompt = "Test caching prompt"
            
            # First request (should hit provider)
            response_parts_1 = []
            async for chunk in llm_service.generate_optimized(
                prompt,
                model_name="local_model",
                stream=False
            ):
                response_parts_1.append(chunk)
            
            assert mock_provider.call_count == 1
            
            # Second request with same prompt (should hit cache)
            response_parts_2 = []
            async for chunk in llm_service.generate_optimized(
                prompt,
                model_name="local_model",
                stream=False
            ):
                response_parts_2.append(chunk)
            
            # Provider should not be called again
            assert mock_provider.call_count == 1
            
            # Responses should be the same
            assert response_parts_1 == response_parts_2
    
    def test_metrics_recording(self, llm_service):
        """Test metrics recording"""
        metrics = GenerationMetrics(
            model_name="test_model",
            provider="test_provider",
            first_token_latency_ms=50.0,
            total_latency_ms=200.0,
            tokens_generated=10,
            tokens_per_second=50.0,
            cache_hit=False
        )
        
        initial_count = len(llm_service.metrics_history)
        llm_service._record_metrics(metrics)
        
        assert len(llm_service.metrics_history) == initial_count + 1
        assert llm_service.metrics_history[-1] == metrics
    
    def test_performance_report(self, llm_service):
        """Test performance report generation"""
        # Add some test metrics
        for i in range(10):
            metrics = GenerationMetrics(
                model_name="test_model",
                provider="test_provider",
                first_token_latency_ms=50.0 + i * 10,
                total_latency_ms=200.0 + i * 20,
                tokens_generated=10 + i,
                tokens_per_second=50.0 - i,
                cache_hit=i % 3 == 0  # Every third request is cache hit
            )
            llm_service._record_metrics(metrics)
        
        report = llm_service.get_performance_report()
        
        assert "summary" in report
        assert "latency_metrics" in report
        assert "model_states" in report
        assert "slo_compliance" in report
        
        # Check summary statistics
        summary = report["summary"]
        assert summary["total_requests"] == 10
        assert 0 <= summary["cache_hit_rate"] <= 1
        assert summary["error_rate"] == 0  # No errors in test data
        
        # Check latency metrics
        if "first_token" in report["latency_metrics"]:
            ft_metrics = report["latency_metrics"]["first_token"]
            assert "avg_ms" in ft_metrics
            assert "p95_ms" in ft_metrics
            assert ft_metrics["p95_ms"] > ft_metrics["avg_ms"]
    
    @pytest.mark.asyncio
    async def test_benchmark_performance(self, llm_service):
        """Test performance benchmarking"""
        mock_provider = MockProvider("test_provider", latency_ms=80.0)
        
        with patch.object(llm_service, '_get_provider_instance', new_callable=AsyncMock) as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            test_prompts = [
                "Test prompt 1",
                "Test prompt 2",
                "Test prompt 3"
            ]
            
            results = await llm_service.benchmark_performance(test_prompts)
            
            assert "test_prompts" in results
            assert "results" in results
            assert "summary" in results
            
            assert results["test_prompts"] == len(test_prompts)
            assert len(results["results"]) == len(test_prompts)
            
            # Check that all requests succeeded
            successful_results = [r for r in results["results"] if r["success"]]
            assert len(successful_results) == len(test_prompts)
            
            # Check summary statistics
            summary = results["summary"]
            assert summary["success_rate"] == 1.0
            assert summary["avg_latency_ms"] > 0
            assert summary["p95_latency_ms"] >= summary["avg_latency_ms"]

class TestPerformanceTargets:
    """Test performance target compliance"""
    
    @pytest.mark.asyncio
    async def test_first_token_latency_target(self):
        """Test that first token latency meets SLO target"""
        # Create service with fast mock provider
        configs = [
            ModelConfig(
                name="fast_model",
                provider="test",
                model_type=ModelType.LOCAL,
                warmup_strategy=WarmupStrategy.LAZY,  # Use lazy to avoid warmup overhead
                preload_enabled=False  # Disable preloading for cleaner test
            )
        ]
        
        service = OptimizedLLMService(configs)
        mock_provider = MockProvider("fast_provider", latency_ms=20.0)  # Very fast provider
        
        with patch.object(service, '_get_provider_instance', new_callable=AsyncMock) as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            # Mark model as already warmed to skip warmup
            service.model_states["fast_model"].is_warmed = True
            
            # Perform multiple requests to get statistical data
            latencies = []
            
            for i in range(20):
                start_time = time.time()
                first_chunk_time = None
                
                async for chunk in service.generate_optimized(
                    f"Test prompt {i}",
                    model_name="fast_model",
                    stream=True
                ):
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                    break  # Just get first chunk for timing
                
                if first_chunk_time:
                    first_token_latency = (first_chunk_time - start_time) * 1000
                    latencies.append(first_token_latency)
            
            # Calculate p95 latency
            if latencies:
                sorted_latencies = sorted(latencies)
                p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
                
                # Should meet SLO target of < 1200ms
                assert p95_latency < 1200.0, f"P95 first-token latency {p95_latency:.2f}ms exceeds 1200ms target"
                
                # Should also be reasonable for a fast provider (more lenient for test environment)
                assert p95_latency < 500.0, f"P95 latency {p95_latency:.2f}ms is too high for fast provider"
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation"""
        service = OptimizedLLMService([])
        
        # Add metrics with some cache hits
        for i in range(10):
            metrics = GenerationMetrics(
                model_name="test_model",
                provider="test_provider",
                first_token_latency_ms=100.0,
                total_latency_ms=500.0,
                tokens_generated=20,
                tokens_per_second=40.0,
                cache_hit=(i % 4 == 0)  # 25% cache hit rate
            )
            service._record_metrics(metrics)
        
        report = service.get_performance_report()
        cache_hit_rate = report["summary"]["cache_hit_rate"]
        
        # Should be approximately 25%
        assert abs(cache_hit_rate - 0.25) < 0.1
    
    def test_model_state_tracking(self):
        """Test model state tracking"""
        configs = [
            ModelConfig(
                name="tracked_model",
                provider="test",
                model_type=ModelType.LOCAL,
                warmup_strategy=WarmupStrategy.EAGER
            )
        ]
        
        service = OptimizedLLMService(configs)
        state = service.model_states["tracked_model"]
        
        # Initial state
        assert state.request_count == 0
        assert state.error_count == 0
        assert state.avg_first_token_latency == 0.0
        
        # Simulate some requests
        state.request_count = 5
        state.error_count = 1
        state.avg_first_token_latency = 150.0
        state.avg_total_latency = 800.0
        
        report = service.get_performance_report()
        model_state = report["model_states"]["tracked_model"]
        
        assert model_state["request_count"] == 5
        assert model_state["error_count"] == 1
        assert model_state["avg_first_token_latency_ms"] == 150.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])