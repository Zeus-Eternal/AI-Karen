"""
Unit tests for Model Metadata Service

Tests the model metadata service functionality including:
- Caching mechanism for remote metadata
- Predefined model configurations with TinyLlama examples
- Technical specifications and capabilities management
- Performance metrics and compatibility information
"""

import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ai_karen_engine.services.model_metadata_service import (
    ModelMetadataService,
    CachedMetadata,
    ModelCapabilities,
    PerformanceMetrics
)
from src.ai_karen_engine.services.model_registry import ModelMetadata


class TestModelMetadataService:
    """Test cases for ModelMetadataService."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def metadata_service(self, temp_cache_dir):
        """Create metadata service instance with temporary cache."""
        return ModelMetadataService(cache_dir=temp_cache_dir, cache_ttl=3600)
    
    def test_service_initialization(self, metadata_service):
        """Test service initialization."""
        assert len(metadata_service.predefined_models) >= 3  # TinyLlama + Phi-2
        assert metadata_service.cache_ttl == 3600
        assert metadata_service.cache_dir.exists()
        
        # Check predefined models
        assert "tinyllama-1.1b-chat-q4" in metadata_service.predefined_models
        assert "tinyllama-1.1b-instruct-q4" in metadata_service.predefined_models
        assert "phi-2-q4" in metadata_service.predefined_models
    
    def test_get_predefined_model_metadata(self, metadata_service):
        """Test getting metadata for predefined models."""
        # Test TinyLlama Chat model
        metadata = metadata_service.get_model_metadata("tinyllama-1.1b-chat-q4")
        assert metadata is not None
        assert metadata.parameters == "1.1B"
        assert metadata.quantization == "Q4_K_M"
        assert metadata.context_length == 2048
        assert "chat" in metadata.tags
        assert metadata.architecture == "Llama"
        
        # Test TinyLlama Instruct model
        metadata = metadata_service.get_model_metadata("tinyllama-1.1b-instruct-q4")
        assert metadata is not None
        assert metadata.parameters == "1.1B"
        assert "instruct" in metadata.tags
        assert "instruction_following" in metadata.performance_metrics
        
        # Test Phi-2 model
        metadata = metadata_service.get_model_metadata("phi-2-q4")
        assert metadata is not None
        assert metadata.parameters == "2.7B"
        assert metadata.architecture == "Phi"
        assert "reasoning" in metadata.tags
    
    def test_get_model_capabilities(self, metadata_service):
        """Test getting detailed model capabilities."""
        # Test TinyLlama Chat capabilities
        capabilities = metadata_service.get_model_capabilities("tinyllama-1.1b-chat-q4")
        assert capabilities is not None
        assert "conversational-ai" in capabilities.primary_tasks
        assert "gguf" in capabilities.supported_formats
        assert "en" in capabilities.languages
        assert capabilities.performance_tier == "medium"
        assert capabilities.hardware_requirements["min_ram_gb"] == 1
        assert capabilities.hardware_requirements["gpu_required"] is False
        
        # Test Phi-2 capabilities
        capabilities = metadata_service.get_model_capabilities("phi-2-q4")
        assert capabilities is not None
        assert "code-generation" in capabilities.primary_tasks
        assert "reasoning" in capabilities.primary_tasks
        assert capabilities.performance_tier == "high"
        assert capabilities.hardware_requirements["min_ram_gb"] == 2
    
    def test_get_performance_metrics(self, metadata_service):
        """Test getting model performance metrics."""
        # Test TinyLlama Chat performance
        performance = metadata_service.get_performance_metrics("tinyllama-1.1b-chat-q4")
        assert performance is not None
        assert performance.inference_speed == "fast"
        assert performance.memory_efficiency == "high"
        assert performance.quality_score == 0.75
        assert performance.tokens_per_second == 25.0
        assert performance.memory_usage_mb == 1024
        assert "hellaswag" in performance.benchmark_scores
        
        # Test Phi-2 performance
        performance = metadata_service.get_performance_metrics("phi-2-q4")
        assert performance is not None
        assert performance.inference_speed == "medium"
        assert performance.quality_score == 0.82
        assert "humaneval" in performance.benchmark_scores
        assert "gsm8k" in performance.benchmark_scores
    
    def test_metadata_caching(self, metadata_service):
        """Test metadata caching functionality."""
        model_id = "tinyllama-1.1b-chat-q4"
        
        # First call should cache the metadata
        metadata1 = metadata_service.get_model_metadata(model_id)
        assert metadata1 is not None
        assert model_id in metadata_service.metadata_cache
        
        cached = metadata_service.metadata_cache[model_id]
        assert cached.source == "predefined"
        assert cached.expires_at > time.time()
        
        # Second call should return cached version
        metadata2 = metadata_service.get_model_metadata(model_id)
        assert metadata2 is not None
        assert metadata1.parameters == metadata2.parameters
    
    def test_force_refresh_metadata(self, metadata_service):
        """Test force refreshing metadata."""
        model_id = "tinyllama-1.1b-chat-q4"
        
        # Get metadata and cache it
        metadata1 = metadata_service.get_model_metadata(model_id)
        assert metadata1 is not None
        
        original_cached_at = metadata_service.metadata_cache[model_id].cached_at
        
        # Wait a bit and force refresh
        time.sleep(0.1)
        metadata2 = metadata_service.get_model_metadata(model_id, force_refresh=True)
        assert metadata2 is not None
        
        # Cache should be updated
        new_cached_at = metadata_service.metadata_cache[model_id].cached_at
        assert new_cached_at > original_cached_at
    
    def test_update_metadata_cache(self, metadata_service):
        """Test updating metadata cache manually."""
        model_id = "custom-model"
        
        custom_metadata = ModelMetadata(
            parameters="7B",
            quantization="Q8_0",
            memory_requirement="8GB",
            context_length=4096,
            license="Custom License",
            tags=["custom", "test"],
            architecture="Custom",
            training_data="Custom training data"
        )
        
        # Update cache
        metadata_service.update_metadata_cache(model_id, custom_metadata, "manual")
        
        # Verify it's cached
        assert model_id in metadata_service.metadata_cache
        cached = metadata_service.metadata_cache[model_id]
        assert cached.source == "manual"
        assert cached.metadata.parameters == "7B"
        
        # Verify we can retrieve it
        retrieved = metadata_service.get_model_metadata(model_id)
        assert retrieved is not None
        assert retrieved.parameters == "7B"
        assert retrieved.architecture == "Custom"
    
    def test_search_models_by_capability(self, metadata_service):
        """Test searching models by capability."""
        # Search for chat models
        chat_models = metadata_service.search_models_by_capability("chat")
        assert "tinyllama-1.1b-chat-q4" in chat_models
        
        # Search for instruction following models
        instruct_models = metadata_service.search_models_by_capability("instruction-following")
        assert "tinyllama-1.1b-instruct-q4" in instruct_models
        
        # Search for code generation models
        code_models = metadata_service.search_models_by_capability("code-generation")
        assert "phi-2-q4" in code_models
        
        # Search for non-existent capability
        none_models = metadata_service.search_models_by_capability("non-existent")
        assert len(none_models) == 0
    
    def test_get_models_by_performance_tier(self, metadata_service):
        """Test getting models by performance tier."""
        # Get medium tier models
        medium_models = metadata_service.get_models_by_performance_tier("medium")
        assert "tinyllama-1.1b-chat-q4" in medium_models
        assert "tinyllama-1.1b-instruct-q4" in medium_models
        
        # Get high tier models
        high_models = metadata_service.get_models_by_performance_tier("high")
        assert "phi-2-q4" in high_models
        
        # Get non-existent tier
        none_models = metadata_service.get_models_by_performance_tier("enterprise")
        assert len(none_models) == 0
    
    def test_get_models_by_size_range(self, metadata_service):
        """Test getting models by size range."""
        # Get small models (under 1GB)
        small_models = metadata_service.get_models_by_size_range(0, 1000000000)
        assert "tinyllama-1.1b-chat-q4" in small_models
        assert "tinyllama-1.1b-instruct-q4" in small_models
        
        # Get medium models (1-2GB)
        medium_models = metadata_service.get_models_by_size_range(1000000000, 2000000000)
        assert "phi-2-q4" in medium_models
        
        # Get very large models (over 10GB)
        large_models = metadata_service.get_models_by_size_range(10000000000, float('inf'))
        assert len(large_models) == 0
    
    def test_get_compatible_models(self, metadata_service):
        """Test getting models compatible with hardware constraints."""
        # Test with minimal hardware
        minimal_hw = {
            "ram_gb": 1,
            "has_gpu": False,
            "cpu_cores": 2
        }
        compatible = metadata_service.get_compatible_models(minimal_hw)
        assert "tinyllama-1.1b-chat-q4" in compatible
        assert "tinyllama-1.1b-instruct-q4" in compatible
        # Phi-2 requires 2GB RAM, so it shouldn't be compatible
        assert "phi-2-q4" not in compatible
        
        # Test with better hardware
        better_hw = {
            "ram_gb": 4,
            "has_gpu": False,
            "cpu_cores": 4
        }
        compatible = metadata_service.get_compatible_models(better_hw)
        assert "tinyllama-1.1b-chat-q4" in compatible
        assert "tinyllama-1.1b-instruct-q4" in compatible
        assert "phi-2-q4" in compatible
        
        # Test with insufficient hardware
        insufficient_hw = {
            "ram_gb": 0.5,
            "has_gpu": False,
            "cpu_cores": 1
        }
        compatible = metadata_service.get_compatible_models(insufficient_hw)
        assert len(compatible) == 0
    
    def test_get_model_comparison(self, metadata_service):
        """Test getting comparison data for multiple models."""
        model_ids = ["tinyllama-1.1b-chat-q4", "phi-2-q4"]
        comparison = metadata_service.get_model_comparison(model_ids)
        
        assert len(comparison) == 2
        
        # Check TinyLlama data
        tinyllama_data = comparison["tinyllama-1.1b-chat-q4"]
        assert "metadata" in tinyllama_data
        assert "capabilities" in tinyllama_data
        assert "performance" in tinyllama_data
        assert tinyllama_data["name"] == "TinyLlama 1.1B Chat Q4_K_M"
        assert tinyllama_data["size"] == 669000000
        
        # Check Phi-2 data
        phi2_data = comparison["phi-2-q4"]
        assert "metadata" in phi2_data
        assert "capabilities" in phi2_data
        assert "performance" in phi2_data
        assert phi2_data["name"] == "Microsoft Phi-2 Q4_K_M"
        assert phi2_data["size"] == 1600000000
    
    def test_cache_persistence(self, temp_cache_dir):
        """Test that cache persists across service instances."""
        # Create first service instance and cache some data
        service1 = ModelMetadataService(cache_dir=temp_cache_dir, cache_ttl=3600)
        
        custom_metadata = ModelMetadata(
            parameters="3B",
            quantization="Q4_K_M",
            memory_requirement="3GB",
            context_length=2048,
            license="Test License",
            tags=["test"],
            architecture="Test"
        )
        
        service1.update_metadata_cache("test-model", custom_metadata, "test")
        service1._save_cache()
        
        # Create second service instance
        service2 = ModelMetadataService(cache_dir=temp_cache_dir, cache_ttl=3600)
        
        # Should load cached data
        retrieved = service2.get_model_metadata("test-model")
        assert retrieved is not None
        assert retrieved.parameters == "3B"
        assert retrieved.architecture == "Test"
    
    def test_cache_expiration(self, metadata_service):
        """Test cache expiration functionality."""
        model_id = "test-expiration"
        
        # Create metadata with very short TTL
        metadata_service.cache_ttl = 1  # 1 second
        
        custom_metadata = ModelMetadata(
            parameters="1B",
            quantization="Q4_K_M",
            memory_requirement="1GB",
            context_length=1024,
            license="Test",
            tags=["test"],
            architecture="Test"
        )
        
        # Cache the metadata
        metadata_service.update_metadata_cache(model_id, custom_metadata, "test")
        
        # Should be available immediately
        retrieved1 = metadata_service.get_model_metadata(model_id)
        assert retrieved1 is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired and return None (since it's not predefined)
        retrieved2 = metadata_service.get_model_metadata(model_id)
        assert retrieved2 is None
        assert model_id not in metadata_service.metadata_cache
    
    def test_refresh_all_cache(self, metadata_service):
        """Test refreshing all cached metadata."""
        # Add some test data with short TTL
        metadata_service.cache_ttl = 1
        
        custom_metadata = ModelMetadata(
            parameters="1B",
            quantization="Q4_K_M",
            memory_requirement="1GB",
            context_length=1024,
            license="Test",
            tags=["test"],
            architecture="Test"
        )
        
        metadata_service.update_metadata_cache("expired-model", custom_metadata, "test")
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Refresh cache
        metadata_service.refresh_all_cache()
        
        # Expired entry should be removed
        assert "expired-model" not in metadata_service.metadata_cache
    
    def test_get_cache_statistics(self, metadata_service):
        """Test getting cache statistics."""
        # Get some metadata to populate cache
        metadata_service.get_model_metadata("tinyllama-1.1b-chat-q4")
        metadata_service.get_model_metadata("phi-2-q4")
        
        stats = metadata_service.get_cache_statistics()
        
        assert "total_entries" in stats
        assert "expired_entries" in stats
        assert "valid_entries" in stats
        assert "sources" in stats
        assert "predefined_models" in stats
        assert "cache_ttl_hours" in stats
        
        assert stats["total_entries"] >= 2
        assert stats["predefined_models"] >= 3
        assert stats["cache_ttl_hours"] == 1.0  # 3600 seconds = 1 hour
        assert "predefined" in stats["sources"]
    
    def test_unknown_model_metadata(self, metadata_service):
        """Test getting metadata for unknown models."""
        metadata = metadata_service.get_model_metadata("unknown-model")
        assert metadata is None
        
        capabilities = metadata_service.get_model_capabilities("unknown-model")
        assert capabilities is None
        
        performance = metadata_service.get_performance_metrics("unknown-model")
        assert performance is None


class TestCachedMetadata:
    """Test cases for CachedMetadata dataclass."""
    
    def test_cached_metadata_creation(self):
        """Test creating CachedMetadata."""
        metadata = ModelMetadata(
            parameters="1B",
            quantization="Q4_K_M",
            memory_requirement="1GB",
            context_length=2048,
            license="Apache 2.0",
            tags=["test"]
        )
        
        current_time = time.time()
        cached = CachedMetadata(
            metadata=metadata,
            cached_at=current_time,
            expires_at=current_time + 3600,
            source="test"
        )
        
        assert cached.metadata.parameters == "1B"
        assert cached.cached_at == current_time
        assert cached.expires_at == current_time + 3600
        assert cached.source == "test"


class TestModelCapabilities:
    """Test cases for ModelCapabilities dataclass."""
    
    def test_model_capabilities_creation(self):
        """Test creating ModelCapabilities."""
        capabilities = ModelCapabilities(
            primary_tasks=["text-generation", "chat"],
            supported_formats=["gguf"],
            languages=["en", "es"],
            domains=["general", "chat"],
            performance_tier="medium",
            hardware_requirements={
                "min_ram_gb": 2,
                "recommended_ram_gb": 4,
                "gpu_required": False,
                "cpu_cores": 2
            }
        )
        
        assert "text-generation" in capabilities.primary_tasks
        assert "gguf" in capabilities.supported_formats
        assert "en" in capabilities.languages
        assert capabilities.performance_tier == "medium"
        assert capabilities.hardware_requirements["min_ram_gb"] == 2
        assert capabilities.hardware_requirements["gpu_required"] is False


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics dataclass."""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics."""
        performance = PerformanceMetrics(
            inference_speed="fast",
            memory_efficiency="high",
            quality_score=0.85,
            benchmark_scores={
                "hellaswag": 0.75,
                "arc_challenge": 0.60
            },
            tokens_per_second=30.0,
            memory_usage_mb=2048
        )
        
        assert performance.inference_speed == "fast"
        assert performance.memory_efficiency == "high"
        assert performance.quality_score == 0.85
        assert performance.benchmark_scores["hellaswag"] == 0.75
        assert performance.tokens_per_second == 30.0
        assert performance.memory_usage_mb == 2048
    
    def test_performance_metrics_minimal(self):
        """Test creating PerformanceMetrics with minimal fields."""
        performance = PerformanceMetrics(
            inference_speed="medium",
            memory_efficiency="medium"
        )
        
        assert performance.inference_speed == "medium"
        assert performance.memory_efficiency == "medium"
        assert performance.quality_score is None
        assert performance.benchmark_scores is None
        assert performance.tokens_per_second is None
        assert performance.memory_usage_mb is None