"""
Comprehensive tests for Model Availability Cache implementation.

Tests cover:
1. Basic functionality (add/retrieve models, check status)
2. LRU eviction with usage-based priorities 
3. Error handling and recovery mechanisms
4. Environment variable configuration
5. Integration with capability-aware selector
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from pathlib import Path

# Import the classes we need to test
from .model_availability_cache import (
    AvailabilityStatus,
    PreloadPriority,
    ModelMetadata,
    UsagePattern,
    CacheEntry,
    PreloadConfig,
    ModelAvailabilityCache,
    get_model_availability_cache,
    initialize_model_availability_cache
)
from ..monitoring.network_connectivity import NetworkStatus
from .intelligent_provider_registry import (
    IntelligentProviderRegistration,
    ProviderRegistration,
    ProviderType,
    ProviderPriority,
    ModelInfo
)
from .capability_aware_selector import (
    CapabilityAwareSelector,
    get_capability_selector
)


class TestModelAvailabilityCache(unittest.TestCase):
    """Test suite for ModelAvailabilityCache class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test configuration
        self.test_config = PreloadConfig(
            max_cache_size_bytes=1024 * 1024,  # 1MB
            max_concurrent_downloads=2,
            preload_threshold=0.5,
            critical_models={"provider1:critical_model"},
            network_aware_preloading=True,
            offline_preload_only=False,
            preload_on_startup=False,  # Disable for tests
            cleanup_interval=3600.0,
            cache_directory=self.temp_dir,
            enable_compression=False,
            verify_integrity=False,
            lru_eviction_threshold=0.8,
            usage_based_priority_weight=0.7
        )
        
        # Mock the dependencies
        self.network_monitor = MagicMock()
        self.network_monitor.get_current_status.return_value = NetworkStatus.ONLINE
        
        self.provider_registry = MagicMock()
        self.capability_selector = MagicMock()
        
        # Create test models
        self.test_model1 = ModelInfo(
            name="test_model1",
            capabilities=["text", "chat"]
        )
        
        self.test_model2 = ModelInfo(
            name="test_model2",
            capabilities=["code", "generation"]
        )
        
        self.test_critical_model = ModelInfo(
            name="critical_model",
            capabilities=["text", "critical"]
        )
        
        # Create provider registration
        self.provider_registration = ProviderRegistration(
            name="provider1",
            provider_class=MagicMock,
            description="Test provider",
            models=[self.test_model1, self.test_model2, self.test_critical_model],
            requires_api_key=False,
            default_model="test_model1"
        )
        
        self.intelligent_registration = IntelligentProviderRegistration(
            base_registration=self.provider_registration,
            provider_type=ProviderType.CLOUD,
            priority=ProviderPriority.STANDARD
        )
        
        self.provider_registry.get_provider_info.return_value = self.intelligent_registration
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_cache_initialization(self, mock_selector, mock_registry, mock_network):
        """Test cache initialization with default and custom configuration."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        # Test with custom configuration
        cache = ModelAvailabilityCache(self.test_config)
        
        # Verify initialization
        self.assertEqual(cache.config.max_cache_size_bytes, 1024 * 1024)
        self.assertEqual(cache.config.max_concurrent_downloads, 2)
        self.assertEqual(len(cache._cache), 0)
        self.assertEqual(len(cache._usage_patterns), 0)
        self.assertTrue(os.path.exists(self.temp_dir))
        
        # Verify cache directory was created
        self.assertTrue(Path(self.temp_dir).exists())
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_basic_functionality(self, mock_selector, mock_registry, mock_network):
        """Test basic functionality: add/retrieve models, check status."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Test initial status - model not in cache
        status = cache.get_model_status("provider1", "test_model1")
        self.assertEqual(status, AvailabilityStatus.UNAVAILABLE)
        
        # Test is_model_cached for non-existent model
        self.assertFalse(cache.is_model_cached("provider1", "test_model1"))
        
        # Test get_model_metadata for non-existent model
        self.assertIsNone(cache.get_model_metadata("provider1", "test_model1"))
        
        # Add a model to cache manually
        metadata = ModelMetadata(
            name="test_model1",
            provider="provider1",
            model_type="llm",
            capabilities={"text", "chat"},
            size_bytes=100 * 1024
        )
        
        cache_key = cache._get_cache_key("provider1", "test_model1")
        cache._cache[cache_key] = CacheEntry(
            metadata=metadata,
            status=AvailabilityStatus.AVAILABLE,
            created_at=time.time(),
            last_accessed=time.time()
        )
        
        # Now test retrieval
        status = cache.get_model_status("provider1", "test_model1")
        self.assertEqual(status, AvailabilityStatus.AVAILABLE)
        
        # Test is_model_cached
        self.assertTrue(cache.is_model_cached("provider1", "test_model1"))
        
        # Test get_model_metadata
        retrieved_metadata = cache.get_model_metadata("provider1", "test_model1")
        self.assertIsNotNone(retrieved_metadata)
        if retrieved_metadata:  # Add null check for type checker
            self.assertEqual(retrieved_metadata.name, "test_model1")
            self.assertEqual(retrieved_metadata.provider, "provider1")
            self.assertEqual(retrieved_metadata.capabilities, {"text", "chat"})
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_usage_pattern_tracking(self, mock_selector, mock_registry, mock_network):
        """Test usage pattern tracking functionality."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Record usage for a model
        cache.record_model_usage(
            provider="provider1",
            model_name="test_model1",
            context="chat",
            success=True,
            response_time=1.5
        )
        
        # Check usage pattern was created
        model_key = "provider1:test_model1"
        self.assertIn(model_key, cache._usage_patterns)
        
        pattern = cache._usage_patterns[model_key]
        self.assertEqual(pattern.request_count, 1)
        self.assertEqual(pattern.contexts, {"chat"})
        self.assertEqual(pattern.success_rate, 1.0)
        self.assertEqual(pattern.average_response_time, 1.5)
        
        # Record more usage
        cache.record_model_usage(
            provider="provider1",
            model_name="test_model1",
            context="code",
            success=True,
            response_time=2.0
        )
        
        # Check pattern was updated
        self.assertEqual(pattern.request_count, 2)
        self.assertEqual(pattern.contexts, {"chat", "code"})
        self.assertGreater(pattern.last_used, pattern.last_used - 1.0)  # Should be recent
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_lru_eviction_with_usage_priorities(self, mock_selector, mock_registry, mock_network):
        """Test LRU eviction with usage-based priorities."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        # Create a small cache for testing eviction
        small_config = PreloadConfig(
            max_cache_size_bytes=300 * 1024,  # 300KB - smaller than our models
            cache_directory=self.temp_dir,
            lru_eviction_threshold=0.8,
            usage_based_priority_weight=0.7
        )
        
        cache = ModelAvailabilityCache(small_config)
        
        # Add models that exceed cache size
        models_data = [
            ("provider1", "test_model1", 100 * 1024, AvailabilityStatus.AVAILABLE),
            ("provider1", "test_model2", 200 * 1024, AvailabilityStatus.AVAILABLE),
        ]
        
        for provider, name, size, status in models_data:
            metadata = ModelMetadata(
                name=name,
                provider=provider,
                model_type="llm",
                capabilities={"text"},
                size_bytes=size
            )
            
            cache_key = cache._get_cache_key(provider, name)
            cache._cache[cache_key] = CacheEntry(
                metadata=metadata,
                status=status,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size
            )
        
        # Add usage patterns to influence eviction
        # Make test_model1 more frequently used
        for i in range(10):
            cache.record_model_usage("provider1", "test_model1", success=True, response_time=1.0)
        
        # Make test_model2 less frequently used
        for i in range(2):
            cache.record_model_usage("provider1", "test_model2", success=True, response_time=2.0)
        
        # Try to add a new model that requires eviction
        new_metadata = ModelMetadata(
            name="new_model",
            provider="provider1",
            model_type="llm",
            capabilities={"text"},
            size_bytes=150 * 1024
        )
        
        # This should trigger eviction
        cache._ensure_space_available(150 * 1024)
        
        # Verify that test_model2 (less used) was evicted, not test_model1
        model1_key = cache._get_cache_key("provider1", "test_model1")
        model2_key = cache._get_cache_key("provider1", "test_model2")
        
        self.assertIn(model1_key, cache._cache)  # Should still be in cache
        # test_model2 should be evicted because it's less used despite being larger
        self.assertNotIn(model2_key, cache._cache)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_error_handling_and_recovery(self, mock_selector, mock_registry, mock_network):
        """Test error handling and recovery mechanisms."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Test download failure and retry logic
        with patch.object(cache, '_fetch_model_metadata') as mock_fetch:
            with patch.object(cache, '_perform_model_download') as mock_download:
                # First call fails
                mock_fetch.return_value = ModelMetadata(
                    name="test_model1",
                    provider="provider1",
                    model_type="llm",
                    capabilities={"text"},
                    size_bytes=100 * 1024
                )
                mock_download.return_value = None  # Simulate download failure
                
                # Start preloading to trigger download
                asyncio.run(cache.start_preloading())
                
                # Queue a model for preloading
                result = asyncio.run(cache.preload_model("provider1", "test_model1"))
                self.assertTrue(result)  # Should be queued successfully
                
                # Give some time for processing
                asyncio.run(asyncio.sleep(0.1))
                
                # Check error recovery state
                cache_key = cache._get_cache_key("provider1", "test_model1")
                self.assertIn(cache_key, cache._error_recovery_state)
                
                recovery_state = cache._error_recovery_state[cache_key]
                self.assertGreater(recovery_state['retry_count'], 0)
                self.assertIsNotNone(recovery_state['last_error'])
                
                # Stop preloading
                asyncio.run(cache.stop_preloading())
        
        # Test corruption detection and cleanup
        cache_key = cache._get_cache_key("provider1", "test_model1")
        
        # Add a model marked as corrupted
        metadata = ModelMetadata(
            name="test_model1",
            provider="provider1",
            model_type="llm",
            capabilities={"text"},
            size_bytes=100 * 1024,
            local_path=os.path.join(self.temp_dir, "corrupted_file")
        )
        
        # Create a fake corrupted file
        if metadata.local_path:  # Add null check
            with open(metadata.local_path, 'w') as f:
                f.write("corrupted data")
        
        cache._cache[cache_key] = CacheEntry(
            metadata=metadata,
            status=AvailabilityStatus.CORRUPTED,
            created_at=time.time(),
            last_accessed=time.time()
        )
        
        # Mark as corrupted in the cache
        cache._corruption_detected.add(cache_key)
        
        # Test cleanup
        cache._cleanup_corrupted_model(cache_key)
        
        # Verify file was removed
        if metadata.local_path:  # Add null check
            self.assertFalse(os.path.exists(metadata.local_path))
        
        # Verify status was updated
        self.assertEqual(cache._cache[cache_key].status, AvailabilityStatus.UNAVAILABLE)
        self.assertEqual(cache._cache[cache_key].error_message, "Model was corrupted and cleaned up")
    
    @patch.dict(os.environ, {
        'KAREN_MAX_CACHE_SIZE_BYTES': '2097152',  # 2MB
        'KAREN_MAX_CONCURRENT_DOWNLOADS': '5',
        'KAREN_PRELOAD_THRESHOLD': '0.8',
        'KAREN_CRITICAL_MODELS': 'provider1:critical_model,provider2:backup_model',
        'KAREN_NETWORK_AWARE_PRELOADING': 'false',
        'KAREN_OFFLINE_PRELOAD_ONLY': 'true',
        'KAREN_PRELOAD_ON_STARTUP': 'false',
        'KAREN_CLEANUP_INTERVAL': '7200.0',
        'KAREN_USAGE_HISTORY_SIZE': '2000',
        'KAREN_PRELOAD_RETRY_ATTEMPTS': '5',
        'KAREN_PRELOAD_RETRY_DELAY': '600.0',
        'KAREN_CACHE_DIRECTORY': '/tmp/test_cache',
        'KAREN_ENABLE_COMPRESSION': 'false',
        'KAREN_VERIFY_INTEGRITY': 'false',
        'KAREN_LRU_EVICTION_THRESHOLD': '0.9',
        'KAREN_USAGE_PRIORITY_WEIGHT': '0.8'
    })
    def test_environment_variable_configuration(self):
        """Test configuration through environment variables."""
        # Create config without explicit values (should use env vars)
        config = PreloadConfig()
        
        # Verify environment variables were used
        self.assertEqual(config.max_cache_size_bytes, 2097152)  # 2MB
        self.assertEqual(config.max_concurrent_downloads, 5)
        self.assertEqual(config.preload_threshold, 0.8)
        self.assertEqual(config.critical_models, {"provider1:critical_model", "provider2:backup_model"})
        self.assertFalse(config.network_aware_preloading)
        self.assertTrue(config.offline_preload_only)
        self.assertFalse(config.preload_on_startup)
        self.assertEqual(config.cleanup_interval, 7200.0)
        self.assertEqual(config.usage_history_size, 2000)
        self.assertEqual(config.preload_retry_attempts, 5)
        self.assertEqual(config.preload_retry_delay, 600.0)
        self.assertEqual(config.cache_directory, "/tmp/test_cache")
        self.assertFalse(config.enable_compression)
        self.assertFalse(config.verify_integrity)
        self.assertEqual(config.lru_eviction_threshold, 0.9)
        self.assertEqual(config.usage_based_priority_weight, 0.8)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_capability_aware_selector_integration(self, mock_selector, mock_registry, mock_network):
        """Test integration with capability-aware selector."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        # Add update_model_availability method to mock selector
        self.capability_selector.update_model_availability = MagicMock()
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Add a model to cache
        metadata = ModelMetadata(
            name="test_model1",
            provider="provider1",
            model_type="llm",
            capabilities={"text", "chat"},
            size_bytes=100 * 1024
        )
        
        cache_key = cache._get_cache_key("provider1", "test_model1")
        cache._cache[cache_key] = CacheEntry(
            metadata=metadata,
            status=AvailabilityStatus.AVAILABLE,
            created_at=time.time(),
            last_accessed=time.time()
        )
        
        # Record usage to trigger capability selector update
        cache.record_model_usage(
            provider="provider1",
            model_name="test_model1",
            context="chat",
            success=True,
            response_time=1.0
        )
        
        # Verify capability selector was updated
        self.capability_selector.update_model_availability.assert_called_once()
        
        # Check the arguments passed to update_model_availability
        call_args = self.capability_selector.update_model_availability.call_args[0][0]
        self.assertEqual(call_args['provider'], "provider1")
        self.assertEqual(call_args['model'], "test_model1")
        self.assertEqual(call_args['status'], AvailabilityStatus.AVAILABLE.value)
        self.assertEqual(call_args['capabilities'], ["text", "chat"])
        self.assertEqual(call_args['model_type'], "llm")
        self.assertEqual(call_args['size_bytes'], 100 * 1024)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_cache_statistics(self, mock_selector, mock_registry, mock_network):
        """Test cache statistics functionality."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Add some models to cache
        models_data = [
            ("provider1", "test_model1", 100 * 1024, AvailabilityStatus.AVAILABLE),
            ("provider1", "test_model2", 200 * 1024, AvailabilityStatus.CACHED),
            ("provider2", "test_model3", 150 * 1024, AvailabilityStatus.DOWNLOADING),
        ]
        
        for provider, name, size, status in models_data:
            metadata = ModelMetadata(
                name=name,
                provider=provider,
                model_type="llm",
                capabilities={"text"},
                size_bytes=size
            )
            
            cache_key = cache._get_cache_key(provider, name)
            cache._cache[cache_key] = CacheEntry(
                metadata=metadata,
                status=status,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size
            )
        
        # Add some usage patterns
        cache.record_model_usage("provider1", "test_model1", success=True)
        cache.record_model_usage("provider1", "test_model2", success=True)
        cache.record_model_usage("provider1", "test_model1", success=False)
        
        # Get statistics
        stats = cache.get_cache_statistics()
        
        # Verify statistics
        self.assertEqual(stats['total_entries'], 3)
        self.assertEqual(stats['total_size_bytes'], 450 * 1024)  # Sum of all sizes
        self.assertEqual(stats['usage_patterns_tracked'], 2)  # Two unique models
        self.assertEqual(stats['status_distribution']['available'], 1)
        self.assertEqual(stats['status_distribution']['cached'], 1)
        self.assertEqual(stats['status_distribution']['downloading'], 1)
        self.assertGreater(stats['cache_hit_rate'], 0)
        self.assertEqual(stats['network_status'], NetworkStatus.ONLINE.value)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_cache_clear_functionality(self, mock_selector, mock_registry, mock_network):
        """Test cache clearing functionality."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Add models from different providers
        models_data = [
            ("provider1", "test_model1", 100 * 1024, AvailabilityStatus.AVAILABLE),
            ("provider1", "test_model2", 200 * 1024, AvailabilityStatus.CACHED),
            ("provider2", "test_model3", 150 * 1024, AvailabilityStatus.DOWNLOADING),
        ]
        
        for provider, name, size, status in models_data:
            metadata = ModelMetadata(
                name=name,
                provider=provider,
                model_type="llm",
                capabilities={"text"},
                size_bytes=size
            )
            
            cache_key = cache._get_cache_key(provider, name)
            cache._cache[cache_key] = CacheEntry(
                metadata=metadata,
                status=status,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size
            )
        
        # Test clearing all cache
        cleared_count = cache.clear_cache()
        self.assertEqual(cleared_count, 3)
        self.assertEqual(len(cache._cache), 0)
        
        # Add models again
        for provider, name, size, status in models_data:
            metadata = ModelMetadata(
                name=name,
                provider=provider,
                model_type="llm",
                capabilities={"text"},
                size_bytes=size
            )
            
            cache_key = cache._get_cache_key(provider, name)
            cache._cache[cache_key] = CacheEntry(
                metadata=metadata,
                status=status,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size
            )
        
        # Test clearing by provider
        cleared_count = cache.clear_cache(provider="provider1")
        self.assertEqual(cleared_count, 2)
        self.assertEqual(len(cache._cache), 1)
        
        # Verify only provider2 model remains
        remaining_key = cache._get_cache_key("provider2", "test_model3")
        self.assertIn(remaining_key, cache._cache)
        
        # Test clearing by model
        cleared_count = cache.clear_cache(provider="provider2", model_name="test_model3")
        self.assertEqual(cleared_count, 1)
        self.assertEqual(len(cache._cache), 0)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_preloading_candidates(self, mock_selector, mock_registry, mock_network):
        """Test preloading candidates selection."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Add usage patterns for different models
        # High usage model
        for i in range(20):
            cache.record_model_usage("provider1", "high_usage_model", success=True, response_time=1.0)
        
        # Medium usage model
        for i in range(10):
            cache.record_model_usage("provider1", "medium_usage_model", success=True, response_time=1.5)
        
        # Low usage model
        for i in range(3):
            cache.record_model_usage("provider1", "low_usage_model", success=True, response_time=2.0)
        
        # Get preloading candidates
        candidates = cache.get_preloading_candidates(limit=5)
        
        # Verify candidates are ordered by priority score
        self.assertGreater(len(candidates), 0)
        
        # Check that high usage model has higher priority
        high_usage_score = None
        low_usage_score = None
        
        for model_key, score in candidates:
            if "high_usage_model" in model_key:
                high_usage_score = score
            elif "low_usage_model" in model_key:
                low_usage_score = score
        
        self.assertIsNotNone(high_usage_score)
        self.assertIsNotNone(low_usage_score)
        if high_usage_score is not None and low_usage_score is not None:
            self.assertGreater(high_usage_score, low_usage_score)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_cache_metadata_persistence(self, mock_selector, mock_registry, mock_network):
        """Test cache metadata persistence to disk."""
        # Setup mocks
        mock_network.return_value = self.network_monitor
        mock_registry.return_value = self.provider_registry
        mock_selector.return_value = self.capability_selector
        
        cache = ModelAvailabilityCache(self.test_config)
        
        # Add a model to cache
        metadata = ModelMetadata(
            name="test_model1",
            provider="provider1",
            model_type="llm",
            capabilities={"text", "chat"},
            size_bytes=100 * 1024,
            version="1.0",
            checksum="abc123"
        )
        
        cache_key = cache._get_cache_key("provider1", "test_model1")
        cache._cache[cache_key] = CacheEntry(
            metadata=metadata,
            status=AvailabilityStatus.AVAILABLE,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=5,
            ttl=3600.0,
            size_bytes=100 * 1024,
            preload_priority=PreloadPriority.HIGH
        )
        
        # Save metadata
        cache._save_cache_metadata()
        
        # Verify metadata file was created
        metadata_file = os.path.join(self.temp_dir, "cache_metadata.json")
        self.assertTrue(os.path.exists(metadata_file))
        
        # Load and verify metadata content
        with open(metadata_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['version'], '1.0')
        self.assertEqual(len(data['entries']), 1)
        
        entry = data['entries'][0]
        self.assertEqual(entry['metadata']['name'], 'test_model1')
        self.assertEqual(entry['metadata']['provider'], 'provider1')
        self.assertEqual(entry['metadata']['capabilities'], ['text', 'chat'])
        self.assertEqual(entry['status'], 'available')
        self.assertEqual(entry['access_count'], 5)
        self.assertEqual(entry['ttl'], 3600.0)
        self.assertEqual(entry['preload_priority'], 1)  # HIGH = 1
        
        # Test loading metadata
        new_cache = ModelAvailabilityCache(self.test_config)
        self.assertEqual(len(new_cache._cache), 1)
        
        loaded_entry = new_cache._cache[cache_key]
        self.assertEqual(loaded_entry.metadata.name, 'test_model1')
        self.assertEqual(loaded_entry.metadata.provider, 'provider1')
        self.assertEqual(loaded_entry.status, AvailabilityStatus.AVAILABLE)
        self.assertEqual(loaded_entry.access_count, 5)
        self.assertEqual(loaded_entry.preload_priority, PreloadPriority.HIGH)


class TestGlobalFunctions(unittest.TestCase):
    """Test global functions and singleton behavior."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Reset global instances
        from ai_karen_engine.integrations.model_availability_cache import _model_availability_cache
        globals()['_model_availability_cache'] = None
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    def test_get_model_availability_cache_singleton(self, mock_selector, mock_registry, mock_network):
        """Test that get_model_availability_cache returns singleton instance."""
        # Setup mocks
        mock_network.return_value = MagicMock()
        mock_registry.return_value = MagicMock()
        mock_selector.return_value = MagicMock()
        
        # Get cache instance twice
        cache1 = get_model_availability_cache()
        cache2 = get_model_availability_cache()
        
        # Verify they are the same instance
        self.assertIs(cache1, cache2)
        
        # Verify with custom config
        custom_config = PreloadConfig(max_cache_size_bytes=2048)
        cache3 = get_model_availability_cache(custom_config)
        
        # Should still be the same instance (config ignored after first call)
        self.assertIs(cache1, cache3)
    
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_network_monitor')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_intelligent_provider_registry')
    @patch('src.ai_karen_engine.integrations.model_availability_cache.get_capability_selector')
    async def test_initialize_model_availability_cache(self, mock_selector, mock_registry, mock_network):
        """Test initialize_model_availability_cache function."""
        # Setup mocks
        mock_network.return_value = MagicMock()
        mock_registry.return_value = MagicMock()
        mock_selector.return_value = MagicMock()
        
        # Initialize cache
        cache = await initialize_model_availability_cache()
        
        # Verify cache was initialized and preloading started
        self.assertIsNotNone(cache)
        self.assertTrue(cache._preloading_active)
        
        # Clean up
        await cache.stop_preloading()


if __name__ == '__main__':
    unittest.main()
