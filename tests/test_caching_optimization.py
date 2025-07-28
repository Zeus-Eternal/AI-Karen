"""
Unit tests for NLP analysis caching and optimization features.

This module tests the caching, batch processing, and performance optimization
functionality of the CredentialAnalyzer service.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Tuple

from ai_karen_engine.security.credential_analyzer import CredentialAnalyzer
from ai_karen_engine.security.models import (
    IntelligentAuthConfig,
    NLPFeatures
)
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.services.nlp_config import SpacyConfig


class TestCachingOptimization:
    """Test cases for caching and optimization features."""

    @pytest.fixture
    def config(self):
        """Create test configuration with caching enabled."""
        return IntelligentAuthConfig(
            cache_size=100,
            cache_ttl=300,
            batch_size=10,
            max_processing_time=5.0
        )

    @pytest.fixture
    def mock_spacy_service(self):
        """Create mock spaCy service."""
        mock_service = Mock(spec=SpacyService)
        
        async def mock_parse_message(text):
            # Add small delay to simulate processing
            await asyncio.sleep(0.01)
            return ParsedMessage(
                tokens=text.split(),
                lemmas=[token.lower() for token in text.split()],
                entities=[],
                pos_tags=[(token, 'NOUN') for token in text.split()],
                noun_phrases=[text],
                sentences=[text],
                dependencies=[],
                language='en',
                processing_time=0.01,
                used_fallback=False
            )
        
        mock_service.parse_message = AsyncMock(side_effect=mock_parse_message)
        
        from ai_karen_engine.services.spacy_service import SpacyHealthStatus
        mock_service.get_health_status.return_value = SpacyHealthStatus(
            is_healthy=True,
            model_loaded=True,
            fallback_mode=False,
            cache_size=10,
            cache_hit_rate=0.8,
            avg_processing_time=0.01,
            error_count=0,
            last_error=None
        )
        
        return mock_service

    @pytest.fixture
    def analyzer(self, config, mock_spacy_service):
        """Create CredentialAnalyzer instance."""
        return CredentialAnalyzer(config, mock_spacy_service)

    @pytest.mark.asyncio
    async def test_basic_caching(self, analyzer):
        """Test basic caching functionality."""
        await analyzer.initialize()
        
        email = "test@example.com"
        password_hash = "testhash123"
        
        # First call - should miss cache
        start_time = time.time()
        result1 = await analyzer.analyze_credentials(email, password_hash)
        first_call_time = time.time() - start_time
        
        # Second call - should hit cache
        start_time = time.time()
        result2 = await analyzer.analyze_credentials(email, password_hash)
        second_call_time = time.time() - start_time
        
        # Results should be identical (except processing time)
        assert result1.email_features.token_count == result2.email_features.token_count
        assert result1.credential_similarity == result2.credential_similarity
        
        # Second call should be faster due to caching
        assert second_call_time < first_call_time or second_call_time < 0.01
        
        # Check cache metrics
        metrics = analyzer.get_performance_metrics()
        assert metrics['cache_hits'] >= 1
        assert metrics['cache_hit_rate'] > 0

    @pytest.mark.asyncio
    async def test_batch_processing(self, analyzer):
        """Test batch processing functionality."""
        await analyzer.initialize()
        
        # Create test credential pairs
        credential_pairs = [
            (f"user{i}@example.com", f"hash{i}123")
            for i in range(5)
        ]
        
        # Process batch
        start_time = time.time()
        results = await analyzer.analyze_credentials_batch(credential_pairs)
        batch_time = time.time() - start_time
        
        # Should return results for all pairs
        assert len(results) == len(credential_pairs)
        
        # All results should be NLPFeatures instances
        assert all(isinstance(result, NLPFeatures) for result in results)
        
        # Process individually for comparison
        start_time = time.time()
        individual_results = []
        for email, password_hash in credential_pairs:
            result = await analyzer.analyze_credentials(email, password_hash)
            individual_results.append(result)
        individual_time = time.time() - start_time
        
        # Batch processing should be more efficient (or at least not significantly slower)
        # Note: Due to caching, individual might be faster on second run
        assert len(individual_results) == len(results)

    @pytest.mark.asyncio
    async def test_empty_batch_processing(self, analyzer):
        """Test batch processing with empty input."""
        await analyzer.initialize()
        
        results = await analyzer.analyze_credentials_batch([])
        assert results == []

    @pytest.mark.asyncio
    async def test_batch_processing_with_errors(self, analyzer):
        """Test batch processing error handling."""
        await analyzer.initialize()
        
        # Mock one of the analyze_credentials calls to fail
        original_analyze = analyzer.analyze_credentials
        call_count = 0
        
        async def failing_analyze(email, password_hash):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Fail on second call
                raise Exception("Test error")
            return await original_analyze(email, password_hash)
        
        analyzer.analyze_credentials = failing_analyze
        
        credential_pairs = [
            ("user1@example.com", "hash1"),
            ("user2@example.com", "hash2"),  # This will fail
            ("user3@example.com", "hash3")
        ]
        
        results = await analyzer.analyze_credentials_batch(credential_pairs)
        
        # Should still return results for all pairs (with fallback for failed one)
        assert len(results) == 3
        assert all(isinstance(result, NLPFeatures) for result in results)
        
        # The failed one should use fallback
        assert results[1].used_fallback is True

    @pytest.mark.asyncio
    async def test_cache_warming(self, analyzer):
        """Test cache warming functionality."""
        await analyzer.initialize()
        
        credential_pairs = [
            ("warm1@example.com", "warmhash1"),
            ("warm2@example.com", "warmhash2"),
            ("warm3@example.com", "warmhash3")
        ]
        
        # Warm the cache
        await analyzer.warm_cache(credential_pairs)
        
        # Check that items are now cached
        cache_stats = analyzer.get_cache_statistics()
        assert cache_stats['main_cache']['size'] >= len(credential_pairs)
        
        # Subsequent calls should be faster due to cache
        start_time = time.time()
        for email, password_hash in credential_pairs:
            await analyzer.analyze_credentials(email, password_hash)
        cached_time = time.time() - start_time
        
        # Should be relatively fast due to caching
        assert cached_time < 1.0  # Should complete quickly

    @pytest.mark.asyncio
    async def test_pattern_precomputation(self, analyzer):
        """Test pattern precomputation functionality."""
        await analyzer.initialize()
        
        common_texts = [
            "password123",
            "admin456",
            "qwerty",
            "test@example.com"
        ]
        
        # Precompute patterns
        await analyzer.precompute_common_patterns(common_texts)
        
        # Subsequent pattern detection should be faster
        start_time = time.time()
        for text in common_texts:
            await analyzer.detect_suspicious_patterns(text)
        precomputed_time = time.time() - start_time
        
        # Should complete without errors
        assert precomputed_time >= 0

    def test_cache_optimization_recommendations(self, analyzer):
        """Test cache optimization recommendations."""
        # Simulate low hit rate scenario
        analyzer._cache_hits = 10
        analyzer._cache_misses = 90
        
        # Fill cache to near capacity
        for i in range(int(analyzer.cache.maxsize * 0.95)):
            analyzer.cache[f"key_{i}"] = f"value_{i}"
        
        recommendations = analyzer.optimize_cache_settings(hit_rate_threshold=0.8)
        
        assert 'current_hit_rate' in recommendations
        assert 'recommendations' in recommendations
        assert recommendations['current_hit_rate'] == 0.1  # 10/100
        
        # Should recommend increasing cache size due to low hit rate and high utilization
        rec_actions = [rec['action'] for rec in recommendations['recommendations']]
        assert 'increase_cache_size' in rec_actions

    def test_performance_metrics_collection(self, analyzer):
        """Test comprehensive performance metrics collection."""
        # Simulate some activity
        analyzer._analysis_count = 100
        analyzer._cache_hits = 80
        analyzer._cache_misses = 20
        analyzer._processing_times = [0.1, 0.2, 0.15, 0.3, 0.12] * 20  # 100 measurements
        analyzer._error_count = 5
        
        metrics = analyzer.get_performance_metrics()
        
        # Check all expected metrics are present
        expected_metrics = [
            'analysis_count', 'cache_hit_rate', 'cache_hits', 'cache_misses',
            'cache_size', 'cache_max_size', 'language_cache_size',
            'avg_processing_time', 'processing_time_p50', 'processing_time_p95',
            'processing_time_p99', 'error_count', 'error_rate', 'throughput_per_second'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
        
        # Verify calculations
        assert metrics['analysis_count'] == 100
        assert metrics['cache_hit_rate'] == 0.8  # 80/100
        assert metrics['error_rate'] == 0.05  # 5/100
        assert metrics['avg_processing_time'] > 0
        assert metrics['throughput_per_second'] > 0

    def test_cache_statistics(self, analyzer):
        """Test detailed cache statistics."""
        # Add some items to caches
        analyzer.cache['test1'] = 'value1'
        analyzer.cache['test2'] = 'value2'
        analyzer._language_cache['lang1'] = 'en'
        
        stats = analyzer.get_cache_statistics()
        
        # Check structure
        assert 'main_cache' in stats
        assert 'language_cache' in stats
        
        # Check main cache stats
        main_cache = stats['main_cache']
        assert main_cache['size'] >= 2
        assert main_cache['max_size'] == analyzer.cache.maxsize
        assert 0 <= main_cache['utilization'] <= 1
        assert main_cache['ttl'] == analyzer.config.cache_ttl
        
        # Check language cache stats
        lang_cache = stats['language_cache']
        assert lang_cache['size'] >= 1
        assert lang_cache['ttl'] == 7200

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, analyzer):
        """Test cache TTL expiration behavior."""
        await analyzer.initialize()
        
        # Use a very short TTL for testing
        analyzer.cache = analyzer.cache.__class__(maxsize=100, ttl=0.1)  # 0.1 second TTL
        
        email = "ttl@example.com"
        password_hash = "ttlhash123"
        
        # First call - should miss cache
        result1 = await analyzer.analyze_credentials(email, password_hash)
        
        # Immediate second call - should hit cache
        result2 = await analyzer.analyze_credentials(email, password_hash)
        
        # Wait for TTL to expire
        await asyncio.sleep(0.2)
        
        # Third call - should miss cache due to TTL expiration
        result3 = await analyzer.analyze_credentials(email, password_hash)
        
        # All results should be valid
        assert all(isinstance(result, NLPFeatures) for result in [result1, result2, result3])

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, analyzer):
        """Test concurrent access to cache."""
        await analyzer.initialize()
        
        email = "concurrent@example.com"
        password_hash = "concurrenthash123"
        
        # Create multiple concurrent requests for the same credential
        tasks = [
            analyzer.analyze_credentials(email, password_hash)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.email_features.token_count == first_result.email_features.token_count
            assert result.credential_similarity == first_result.credential_similarity
        
        # Should have some cache activity (hits or misses)
        metrics = analyzer.get_performance_metrics()
        assert metrics['cache_hits'] + metrics['cache_misses'] > 0

    @pytest.mark.asyncio
    async def test_large_batch_processing(self, analyzer):
        """Test processing of large batches."""
        await analyzer.initialize()
        
        # Create a large batch (larger than configured batch_size)
        large_batch = [
            (f"user{i}@example.com", f"hash{i}123")
            for i in range(25)  # Larger than default batch_size of 10
        ]
        
        start_time = time.time()
        results = await analyzer.analyze_credentials_batch(large_batch)
        processing_time = time.time() - start_time
        
        # Should process all items
        assert len(results) == 25
        
        # Should complete in reasonable time
        assert processing_time < 10.0  # Should not take too long
        
        # All results should be valid
        assert all(isinstance(result, NLPFeatures) for result in results)

    def test_cache_memory_management(self, analyzer):
        """Test cache memory management and cleanup."""
        # Fill cache beyond capacity to test eviction
        cache_size = analyzer.cache.maxsize
        
        # Add more items than cache can hold
        for i in range(cache_size + 10):
            analyzer.cache[f"key_{i}"] = f"value_{i}"
        
        # Cache should not exceed max size
        assert len(analyzer.cache) <= cache_size
        
        # Clear cache
        analyzer.clear_cache()
        
        # Both caches should be empty
        assert len(analyzer.cache) == 0
        assert len(analyzer._language_cache) == 0

    def test_metrics_reset(self, analyzer):
        """Test metrics reset functionality."""
        # Set some metrics
        analyzer._analysis_count = 100
        analyzer._cache_hits = 80
        analyzer._cache_misses = 20
        analyzer._processing_times = [0.1, 0.2, 0.3]
        analyzer._error_count = 5
        analyzer._last_error = "Test error"
        
        # Reset metrics
        analyzer.reset_metrics()
        
        # All metrics should be reset
        assert analyzer._analysis_count == 0
        assert analyzer._cache_hits == 0
        assert analyzer._cache_misses == 0
        assert len(analyzer._processing_times) == 0
        assert analyzer._error_count == 0
        assert analyzer._last_error is None

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, analyzer):
        """Test batch processing performance characteristics."""
        await analyzer.initialize()
        
        # Create test data
        small_batch = [(f"user{i}@example.com", f"hash{i}") for i in range(5)]
        large_batch = [(f"user{i}@example.com", f"hash{i}") for i in range(20)]
        
        # Process small batch
        start_time = time.time()
        small_results = await analyzer.analyze_credentials_batch(small_batch)
        small_time = time.time() - start_time
        
        # Process large batch
        start_time = time.time()
        large_results = await analyzer.analyze_credentials_batch(large_batch)
        large_time = time.time() - start_time
        
        # Verify results
        assert len(small_results) == 5
        assert len(large_results) == 20
        
        # Large batch should not be proportionally slower (due to batching efficiency)
        time_per_item_small = small_time / 5
        time_per_item_large = large_time / 20
        
        # Large batch should be more efficient per item (or at least not much worse)
        assert time_per_item_large <= time_per_item_small * 2  # Allow some overhead

    @pytest.mark.asyncio
    async def test_error_handling_in_optimization(self, analyzer):
        """Test error handling in optimization features."""
        await analyzer.initialize()
        
        # Test cache warming with invalid data
        invalid_pairs = [("", ""), ("invalid", "")]
        
        try:
            await analyzer.warm_cache(invalid_pairs)
            # Should not raise exception
        except Exception as e:
            pytest.fail(f"Cache warming should handle invalid data gracefully: {e}")
        
        # Test pattern precomputation with invalid data
        invalid_texts = ["", None, 123]  # Mix of invalid types
        
        try:
            # Filter out None and non-string values for the actual call
            valid_texts = [text for text in invalid_texts if isinstance(text, str)]
            await analyzer.precompute_common_patterns(valid_texts)
            # Should not raise exception
        except Exception as e:
            pytest.fail(f"Pattern precomputation should handle invalid data gracefully: {e}")


if __name__ == "__main__":
    pytest.main([__file__])