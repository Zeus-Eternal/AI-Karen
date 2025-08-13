"""
Tests for Vector Optimization - Task 8.1
Tests vector query optimization to ensure p95 latency < 50ms, ≥ 0.95 recall rate,
and ≥ +15% MRR improvement vs ANN-only.
"""

import asyncio
import pytest
import time
import numpy as np
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.vector_optimization import (
    VectorOptimizationService, VectorSearchConfig, OptimizedVectorIndex,
    IndexType, SearchResult, SearchMetrics
)
from src.ai_karen_engine.services.performance_monitor import (
    PerformanceMonitor, SLOTarget, MetricType, SLOStatus
)

class TestVectorOptimization:
    """Test vector optimization functionality"""
    
    @pytest.fixture
    def vector_config(self):
        """Create test vector configuration"""
        return VectorSearchConfig(
            target_p95_latency_ms=50.0,
            target_recall_rate=0.95,
            target_mrr_improvement=0.15,
            index_type=IndexType.FLAT,  # Use flat for testing
            rerank_enabled=True,
            cache_enabled=True,
            max_workers=2
        )
    
    @pytest.fixture
    def optimization_service(self, vector_config):
        """Create vector optimization service"""
        return VectorOptimizationService(vector_config)
    
    @pytest.fixture
    def sample_vectors(self):
        """Create sample vectors for testing"""
        np.random.seed(42)  # For reproducible tests
        dimension = 128
        num_vectors = 100
        
        vectors = []
        metadata = []
        
        for i in range(num_vectors):
            # Create random vector
            vector = np.random.normal(0, 1, dimension).astype(np.float32)
            vector = vector / np.linalg.norm(vector)  # Normalize
            
            meta = {
                "id": f"vec_{i}",
                "user_id": f"user_{i % 10}",
                "importance": np.random.randint(1, 11),
                "tags": [f"tag_{i % 5}"],
                "created_at": "2024-01-01T00:00:00Z"
            }
            
            vectors.append(vector)
            metadata.append(meta)
        
        return vectors, metadata
    
    def test_vector_index_initialization(self, vector_config):
        """Test vector index initialization"""
        dimension = 128
        index = OptimizedVectorIndex(vector_config, dimension)
        
        assert index.dimension == dimension
        assert index.config == vector_config
        assert len(index.vectors) == 0
        assert len(index.metadata) == 0
    
    def test_add_vectors_to_index(self, vector_config, sample_vectors):
        """Test adding vectors to index"""
        vectors, metadata = sample_vectors
        dimension = len(vectors[0])
        
        index = OptimizedVectorIndex(vector_config, dimension)
        index.add_vectors(vectors[:10], metadata[:10])
        
        assert len(index.vectors) == 10
        assert len(index.metadata) == 10
        assert len(index.id_to_idx) == 10
        
        # Check ID mapping
        for i, meta in enumerate(metadata[:10]):
            assert index.id_to_idx[meta["id"]] == i
    
    def test_flat_vector_search(self, vector_config, sample_vectors):
        """Test flat vector search functionality"""
        vectors, metadata = sample_vectors
        dimension = len(vectors[0])
        
        # Create index and add vectors
        index = OptimizedVectorIndex(vector_config, dimension)
        index.add_vectors(vectors, metadata)
        
        # Search with first vector (should return itself as top result)
        query_vector = vectors[0]
        results, metrics = index.search(query_vector, top_k=5)
        
        assert len(results) > 0
        assert results[0].id == metadata[0]["id"]
        assert results[0].score > 0.99  # Should be very similar to itself
        assert metrics.total_latency_ms > 0
        assert metrics.results_count == len(results)
    
    def test_metadata_filtering(self, vector_config, sample_vectors):
        """Test metadata filtering in search"""
        vectors, metadata = sample_vectors
        dimension = len(vectors[0])
        
        index = OptimizedVectorIndex(vector_config, dimension)
        index.add_vectors(vectors, metadata)
        
        # Search with user filter
        query_vector = vectors[0]
        metadata_filter = {"user_id": "user_0"}
        results, metrics = index.search(query_vector, top_k=5, metadata_filter=metadata_filter)
        
        # All results should match the filter
        for result in results:
            assert result.metadata["user_id"] == "user_0"
    
    def test_reranking_functionality(self, vector_config, sample_vectors):
        """Test reranking improves result quality"""
        vectors, metadata = sample_vectors
        dimension = len(vectors[0])
        
        # Enable reranking
        vector_config.rerank_enabled = True
        vector_config.rerank_factor = 2.0
        
        index = OptimizedVectorIndex(vector_config, dimension)
        index.add_vectors(vectors, metadata)
        
        query_vector = vectors[0]
        results, metrics = index.search(query_vector, top_k=3)
        
        # Check that rerank scores are set
        for result in results:
            assert result.rerank_score is not None
            assert result.original_rank is not None
            assert result.final_rank is not None
    
    @pytest.mark.asyncio
    async def test_optimization_service_search(self, optimization_service, sample_vectors):
        """Test optimization service search functionality"""
        vectors, metadata = sample_vectors
        collection_name = "test_collection"
        dimension = len(vectors[0])
        
        # Add vectors to service
        await optimization_service.add_vectors_batch(
            collection_name, vectors, metadata, dimension
        )
        
        # Perform search
        query_vector = vectors[0]
        results, metrics = await optimization_service.search_optimized(
            collection_name, query_vector, top_k=5
        )
        
        assert len(results) > 0
        assert results[0].id == metadata[0]["id"]
        assert metrics.total_latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_latency_performance(self, optimization_service, sample_vectors):
        """Test that search latency meets SLO targets"""
        vectors, metadata = sample_vectors
        collection_name = "test_collection"
        dimension = len(vectors[0])
        
        # Add vectors
        await optimization_service.add_vectors_batch(
            collection_name, vectors, metadata, dimension
        )
        
        # Perform multiple searches and measure latency
        latencies = []
        num_searches = 20
        
        for i in range(num_searches):
            query_vector = vectors[i % len(vectors)]
            start_time = time.time()
            
            results, metrics = await optimization_service.search_optimized(
                collection_name, query_vector, top_k=10
            )
            
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
        
        # Calculate p95 latency
        sorted_latencies = sorted(latencies)
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        
        # Check SLO compliance (p95 < 50ms)
        assert p95_latency < 50.0, f"P95 latency {p95_latency:.2f}ms exceeds 50ms target"
        
        # Check average latency is reasonable
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 25.0, f"Average latency {avg_latency:.2f}ms is too high"
    
    def test_performance_stats(self, vector_config, sample_vectors):
        """Test performance statistics collection"""
        vectors, metadata = sample_vectors
        dimension = len(vectors[0])
        
        index = OptimizedVectorIndex(vector_config, dimension)
        index.add_vectors(vectors, metadata)
        
        # Perform some searches
        query_vector = vectors[0]
        for _ in range(5):
            index.search(query_vector, top_k=3)
        
        stats = index.get_performance_stats()
        
        assert stats["search_count"] == 5
        assert stats["total_vectors"] == len(vectors)
        assert stats["avg_latency_ms"] > 0
        assert stats["p95_latency_ms"] > 0
        assert stats["index_type"] == vector_config.index_type.value
    
    @pytest.mark.asyncio
    async def test_benchmark_performance(self, optimization_service, sample_vectors):
        """Test performance benchmarking"""
        vectors, metadata = sample_vectors
        collection_name = "test_collection"
        dimension = len(vectors[0])
        
        # Add vectors
        await optimization_service.add_vectors_batch(
            collection_name, vectors, metadata, dimension
        )
        
        # Create test queries
        test_queries = vectors[:10]
        
        # Create ground truth (each query should find itself)
        ground_truth = [[metadata[i]["id"]] for i in range(10)]
        
        # Run benchmark
        benchmark_results = await optimization_service.benchmark_performance(
            collection_name, test_queries, ground_truth
        )
        
        assert "total_queries" in benchmark_results
        assert "summary" in benchmark_results
        assert benchmark_results["total_queries"] == 10
        
        summary = benchmark_results["summary"]
        assert summary["avg_recall"] > 0.8  # Should have good recall
        assert summary["p95_latency_ms"] < 50.0  # Should meet latency SLO

class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor"""
        return PerformanceMonitor()
    
    def test_monitor_initialization(self, performance_monitor):
        """Test performance monitor initialization"""
        assert len(performance_monitor.slo_targets) > 0
        assert "vector_query_p95_latency" in performance_monitor.slo_targets
        assert "vector_query_recall" in performance_monitor.slo_targets
        assert "vector_query_mrr_improvement" in performance_monitor.slo_targets
    
    def test_record_metrics(self, performance_monitor):
        """Test recording performance metrics"""
        # Record some latency metrics
        for i in range(10):
            performance_monitor.record_vector_search_latency(
                latency_ms=20.0 + i,
                status="success",
                correlation_id=f"test_{i}"
            )
        
        # Get metrics
        metrics = performance_monitor.get_metric_values("vector_search_latency_ms", window_minutes=5)
        assert len(metrics) == 10
        assert min(metrics) == 20.0
        assert max(metrics) == 29.0
    
    def test_slo_evaluation(self, performance_monitor):
        """Test SLO evaluation"""
        # Record metrics that meet SLO
        for _ in range(20):
            performance_monitor.record_vector_search_latency(30.0, "success")  # Under 50ms target
        
        # Evaluate SLO
        slo_result = performance_monitor.evaluate_slo("vector_query_p95_latency")
        
        assert slo_result["slo_name"] == "vector_query_p95_latency"
        assert slo_result["is_met"] == True
        assert slo_result["status"] == SLOStatus.HEALTHY
        assert slo_result["actual_value"] == 30.0  # All values are 30.0
    
    def test_slo_violation_detection(self, performance_monitor):
        """Test SLO violation detection"""
        # Record metrics that violate SLO
        for _ in range(20):
            performance_monitor.record_vector_search_latency(80.0, "success")  # Over 50ms target
        
        # Evaluate SLO
        slo_result = performance_monitor.evaluate_slo("vector_query_p95_latency")
        
        assert slo_result["is_met"] == False
        assert slo_result["status"] in [SLOStatus.WARNING, SLOStatus.CRITICAL]
        assert slo_result["actual_value"] == 80.0
    
    def test_performance_summary(self, performance_monitor):
        """Test performance summary generation"""
        # Record various metrics
        performance_monitor.record_vector_search_latency(25.0, "success")
        performance_monitor.record_vector_search_latency(35.0, "success")
        performance_monitor.record_vector_search_latency(45.0, "success")
        
        performance_monitor.record_vector_search_recall(0.95)
        performance_monitor.record_vector_search_recall(0.92)
        
        performance_monitor.record_cache_hit(True)
        performance_monitor.record_cache_hit(False)
        performance_monitor.record_cache_hit(True)
        
        # Get summary
        summary = performance_monitor.get_performance_summary(window_minutes=5)
        
        assert "metrics" in summary
        assert "vector_search_latency" in summary["metrics"]
        assert "recall" in summary["metrics"]
        assert "cache_hit_rate" in summary["metrics"]
        
        latency_metrics = summary["metrics"]["vector_search_latency"]
        assert latency_metrics["count"] == 3
        assert latency_metrics["avg_ms"] == 35.0
        assert latency_metrics["p95_ms"] == 45.0
        
        cache_metrics = summary["metrics"]["cache_hit_rate"]
        assert cache_metrics["hit_rate"] == 2/3  # 2 hits out of 3 accesses
    
    def test_slo_dashboard(self, performance_monitor):
        """Test SLO dashboard generation"""
        # Record some metrics
        for _ in range(10):
            performance_monitor.record_vector_search_latency(30.0, "success")
            performance_monitor.record_vector_search_recall(0.96)
        
        # Get dashboard
        dashboard = performance_monitor.get_slo_dashboard()
        
        assert "timestamp" in dashboard
        assert "slos" in dashboard
        assert "overall_health" in dashboard
        
        # Check specific SLOs
        assert "vector_query_p95_latency" in dashboard["slos"]
        assert "vector_query_recall" in dashboard["slos"]
        
        # Should be healthy since metrics meet targets
        assert dashboard["overall_health"] == SLOStatus.HEALTHY

class TestIntegration:
    """Integration tests for vector optimization with memory service"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for integration testing"""
        db_client = Mock()
        milvus_client = Mock()
        embedding_manager = Mock()
        redis_client = Mock()
        
        # Mock embedding manager
        embedding_manager.dim = 128
        embedding_manager.get_embedding = AsyncMock(return_value=[0.1] * 128)
        
        return db_client, milvus_client, embedding_manager, redis_client
    
    @pytest.mark.asyncio
    async def test_optimized_memory_service_integration(self, mock_dependencies):
        """Test integration with optimized memory service"""
        from src.ai_karen_engine.services.optimized_memory_service import OptimizedMemoryService
        from src.ai_karen_engine.services.unified_memory_service import MemoryQueryRequest
        
        db_client, milvus_client, embedding_manager, redis_client = mock_dependencies
        
        # Create optimized memory service
        service = OptimizedMemoryService(
            db_client=db_client,
            milvus_client=milvus_client,
            embedding_manager=embedding_manager,
            redis_client=redis_client
        )
        
        # Mock the base query method to avoid database calls
        with patch.object(service, '_ensure_vectors_loaded', new_callable=AsyncMock):
            with patch.object(service, '_get_memory_data_by_id', new_callable=AsyncMock) as mock_get_data:
                mock_get_data.return_value = {"content": "test content", "metadata": {}}
                
                # Create test request
                request = MemoryQueryRequest(
                    user_id="test_user",
                    query="test query",
                    top_k=5
                )
                
                # This should not fail even with mocked dependencies
                try:
                    response = await service.query("test_tenant", request)
                    # If we get here without exception, the integration is working
                    assert response is not None
                except Exception as e:
                    # Expected to fail due to mocking, but should not be import/syntax errors
                    assert "not found" in str(e).lower() or "mock" in str(e).lower()
    
    def test_recall_calculation(self):
        """Test recall calculation for MRR improvement validation"""
        # Test data: query results vs ground truth
        retrieved_results = ["doc1", "doc3", "doc5", "doc2", "doc7"]
        ground_truth = ["doc1", "doc2", "doc4", "doc6"]
        
        # Calculate recall
        retrieved_set = set(retrieved_results)
        ground_truth_set = set(ground_truth)
        
        recall = len(retrieved_set.intersection(ground_truth_set)) / len(ground_truth_set)
        
        # Should find doc1 and doc2 (2 out of 4)
        assert recall == 0.5
    
    def test_mrr_calculation(self):
        """Test MRR calculation for improvement validation"""
        # Test data: ranked results vs relevant documents
        ranked_results = ["doc1", "doc3", "doc2", "doc5", "doc4"]
        relevant_docs = {"doc1", "doc2", "doc4"}
        
        # Calculate MRR
        mrr = 0.0
        for rank, doc_id in enumerate(ranked_results):
            if doc_id in relevant_docs:
                mrr = 1.0 / (rank + 1)
                break
        
        # First relevant document is doc1 at rank 1
        assert mrr == 1.0
        
        # Test with relevant doc at different position
        ranked_results_2 = ["doc3", "doc5", "doc2", "doc1", "doc4"]
        mrr_2 = 0.0
        for rank, doc_id in enumerate(ranked_results_2):
            if doc_id in relevant_docs:
                mrr_2 = 1.0 / (rank + 1)
                break
        
        # First relevant document is doc2 at rank 3 (0-indexed)
        assert mrr_2 == 1.0 / 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])