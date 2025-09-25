"""
Tests for async contract compliance in AI-Karen modular architecture.

This module validates that all async interfaces are properly implemented
according to the modular design principles outlined in AGENTS.md.
"""

import pytest
import asyncio
import numpy as np
from typing import List, Dict, Any

from ai_karen_engine.core.embedding_manager import EmbeddingManager
from ai_karen_engine.core.milvus_client import MilvusClient


class TestEmbeddingManagerAsyncContract:
    """Test EmbeddingManager async contract compliance."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.embedding_manager = EmbeddingManager(dim=8)
    
    def test_sync_embed_method_exists(self):
        """Test that sync embed method exists and works."""
        text = "test embedding"
        result = self.embedding_manager.embed(text)
        
        assert isinstance(result, list)
        assert len(result) == 8
        assert all(isinstance(x, float) for x in result)
        assert all(0.0 <= x <= 1.0 for x in result)
    
    @pytest.mark.asyncio
    async def test_async_get_embedding_method_exists(self):
        """Test that async get_embedding method exists and works."""
        text = "test embedding"
        result = await self.embedding_manager.get_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) == 8
        assert all(isinstance(x, float) for x in result)
        assert all(0.0 <= x <= 1.0 for x in result)
    
    @pytest.mark.asyncio
    async def test_sync_async_consistency(self):
        """Test that sync and async methods return identical results."""
        text = "consistency test"
        
        sync_result = self.embedding_manager.embed(text)
        async_result = await self.embedding_manager.get_embedding(text)
        
        assert sync_result == async_result
    
    @pytest.mark.asyncio
    async def test_async_embedding_deterministic(self):
        """Test that async embeddings are deterministic."""
        text = "deterministic test"
        
        result1 = await self.embedding_manager.get_embedding(text)
        result2 = await self.embedding_manager.get_embedding(text)
        
        assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_async_embedding_different_inputs(self):
        """Test that different inputs produce different embeddings."""
        text1 = "first text"
        text2 = "second text"
        
        result1 = await self.embedding_manager.get_embedding(text1)
        result2 = await self.embedding_manager.get_embedding(text2)
        
        assert result1 != result2


class TestMilvusClientAsyncContract:
    """Test MilvusClient async contract compliance."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.milvus_client = MilvusClient(dim=8)
    
    def test_sync_methods_exist(self):
        """Test that sync methods exist and work."""
        vector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        payload = {"user_id": "test_user", "content": "test content"}
        
        # Test upsert
        record_id = self.milvus_client.upsert(vector, payload)
        assert isinstance(record_id, int)
        assert record_id > 0
        
        # Test search_sync
        results = self.milvus_client.search_sync(vector, top_k=5)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert all("id" in result and "score" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_async_insert_method_exists(self):
        """Test that async insert method exists and works."""
        vectors = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]]
        metadata = [{"user_id": "test_user", "content": "test content"}]
        
        result = await self.milvus_client.insert(
            collection_name="test_collection",
            vectors=vectors,
            metadata=metadata
        )
        
        assert result is not None
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_async_search_method_exists(self):
        """Test that async search method exists and works."""
        # First insert some data
        vectors = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]]
        metadata = [{"user_id": "test_user", "content": "test content"}]
        
        await self.milvus_client.insert(
            collection_name="test_collection",
            vectors=vectors,
            metadata=metadata
        )
        
        # Then search
        query_vectors = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]]
        results = await self.milvus_client.search(
            collection_name="test_collection",
            query_vectors=query_vectors,
            top_k=5
        )
        
        assert isinstance(results, list)
        assert len(results) == 1  # One query result set
        assert isinstance(results[0], list)  # List of results for first query
    
    @pytest.mark.asyncio
    async def test_async_search_with_metadata_filter(self):
        """Test async search with metadata filtering."""
        # Insert test data
        vectors = [
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        ]
        metadata = [
            {"user_id": "user1", "category": "test"},
            {"user_id": "user2", "category": "other"}
        ]
        
        for vector, meta in zip(vectors, metadata):
            await self.milvus_client.insert(
                collection_name="test_collection",
                vectors=[vector],
                metadata=[meta]
            )
        
        # Search with metadata filter
        query_vectors = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]]
        results = await self.milvus_client.search(
            collection_name="test_collection",
            query_vectors=query_vectors,
            top_k=5,
            metadata_filter={"user_id": "user1"}
        )
        
        assert isinstance(results, list)
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_async_search_empty_query(self):
        """Test async search with empty query vectors."""
        results = await self.milvus_client.search(
            collection_name="test_collection",
            query_vectors=[],
            top_k=5
        )
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0] == []
    
    def test_sync_search_metadata_filter_format(self):
        """Test that sync search properly handles metadata filter format."""
        vector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        payload = {"user_id": "test_user", "category": "test"}
        
        # Insert data
        self.milvus_client.upsert(vector, payload)
        
        # Test with dictionary metadata filter (correct format)
        results = self.milvus_client.search_sync(
            vector, 
            top_k=5, 
            metadata_filter={"user_id": "test_user"}
        )
        assert isinstance(results, list)
        
        # Test with None metadata filter
        results = self.milvus_client.search_sync(vector, top_k=5, metadata_filter=None)
        assert isinstance(results, list)


class TestMemoryManagerIntegration:
    """Test memory manager integration with async contracts."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.embedding_manager = EmbeddingManager(dim=8)
        self.milvus_client = MilvusClient(dim=8)
    
    @pytest.mark.asyncio
    async def test_embedding_numpy_compatibility(self):
        """Test that embeddings work with numpy array operations."""
        text = "numpy compatibility test"
        
        # Get embedding
        embedding_list = await self.embedding_manager.get_embedding(text)
        
        # Convert to numpy array (as memory manager does)
        embedding_array = np.array(embedding_list)
        
        # Test .tolist() method (as memory manager calls)
        # Handle different numpy array types
        if hasattr(embedding_array, 'tolist'):
            converted_back = embedding_array.tolist()
        else:
            converted_back = list(embedding_array)
        
        assert isinstance(converted_back, list)
        assert converted_back == embedding_list
    
    @pytest.mark.asyncio
    async def test_milvus_client_memory_manager_compatibility(self):
        """Test MilvusClient compatibility with memory manager usage patterns."""
        # Simulate memory manager usage
        query_text = "test query"
        
        # Get embedding (as memory manager does)
        embedding_raw = await self.embedding_manager.get_embedding(query_text)
        embedding_array = np.array(embedding_raw)
        
        # Insert data (as memory manager does)
        # Handle different numpy array types
        if hasattr(embedding_array, 'tolist'):
            vector_list = embedding_array.tolist()
        else:
            vector_list = list(embedding_array)
            
        vectors = [vector_list]
        metadata = [{"memory_id": "test_memory", "user_id": "test_user"}]
        
        result = await self.milvus_client.insert(
            collection_name="test_memories",
            vectors=vectors,
            metadata=metadata
        )
        
        assert result is not None
        
        # Search data (as memory manager does)
        query_vectors = [vector_list]
        search_results = await self.milvus_client.search(
            collection_name="test_memories",
            query_vectors=query_vectors,
            top_k=10,
            metadata_filter={"user_id": "test_user"}
        )
        
        assert isinstance(search_results, list)
        assert len(search_results) == 1  # One query result set


class TestAbsoluteImportsCompliance:
    """Test that modules use absolute imports as required by AGENTS.md."""
    
    def test_memory_manager_imports(self):
        """Test that memory_manager uses absolute imports."""
        import ai_karen_engine.database.memory_manager as mm
        
        # Check that the module can be imported with absolute path
        assert hasattr(mm, 'MemoryManager')
        assert hasattr(mm, 'MemoryEntry')
        assert hasattr(mm, 'MemoryQuery')
    
    def test_memory_service_imports(self):
        """Test that memory_service uses absolute imports."""
        import ai_karen_engine.services.memory_service as ms
        
        # Check that the module can be imported with absolute path
        assert hasattr(ms, 'WebUIMemoryService')
        assert hasattr(ms, 'MemoryType')
        assert hasattr(ms, 'UISource')
    
    def test_web_api_compatibility_imports(self):
        """Test that web_api_compatibility uses absolute imports."""
        import ai_karen_engine.services.web_api_compatibility as wuc
        
        # Check that the module can be imported with absolute path
        assert hasattr(wuc, 'WebUITransformationService')
    
    def test_embedding_manager_imports(self):
        """Test that embedding_manager can be imported with absolute path."""
        import ai_karen_engine.core.embedding_manager as em
        
        # Check that the module can be imported with absolute path
        assert hasattr(em, 'EmbeddingManager')
    
    def test_milvus_client_imports(self):
        """Test that milvus_client can be imported with absolute path."""
        import ai_karen_engine.core.milvus_client as mc
        
        # Check that the module can be imported with absolute path
        assert hasattr(mc, 'MilvusClient')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])