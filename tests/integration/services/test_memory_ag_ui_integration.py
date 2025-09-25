"""
Tests for AG-UI Memory Integration
Tests the enhanced memory system with AG-UI components and CopilotKit integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

from ai_karen_engine.core.memory.ag_ui_manager import (
    AGUIMemoryManager, 
    MemoryGridRow, 
    MemoryNetworkNode, 
    MemoryNetworkEdge,
    MemoryAnalytics
)


class TestAGUIMemoryManager:
    """Test suite for AG-UI enhanced memory manager."""
    
    @pytest.fixture
    def ag_ui_manager(self):
        """Create AG-UI memory manager instance."""
        return AGUIMemoryManager()
    
    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "user_id": "test_user_123",
            "tenant_id": "test_tenant",
            "session_id": "test_session_456"
        }
    
    @pytest.fixture
    def sample_raw_memories(self):
        """Sample raw memory data from existing system."""
        return [
            {
                "result": "User prefers Python over JavaScript for backend development",
                "query": "programming language preference",
                "confidence": 0.9,
                "timestamp": int(datetime.now().timestamp()),
                "session_id": "test_session_456",
                "relevance_score": 0.8
            },
            {
                "result": "Meeting scheduled for 2024-01-15 at 2 PM",
                "query": "upcoming meeting",
                "confidence": 0.95,
                "timestamp": int((datetime.now() - timedelta(days=1)).timestamp()),
                "session_id": "test_session_456",
                "relevance_score": 0.7
            },
            {
                "result": "API endpoint returns 404 error when user not found",
                "query": "API error handling",
                "confidence": 0.85,
                "timestamp": int((datetime.now() - timedelta(hours=2)).timestamp()),
                "session_id": "test_session_456",
                "relevance_score": 0.9
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_memory_grid_data(self, ag_ui_manager, sample_user_context, sample_raw_memories):
        """Test getting memory data formatted for AG-UI grid display."""
        
        # Mock the recall_context function
        with patch('ai_karen_engine.core.memory.ag_ui_manager.recall_context') as mock_recall:
            mock_recall.return_value = sample_raw_memories
            
            # Get grid data
            grid_data = await ag_ui_manager.get_memory_grid_data(
                user_ctx=sample_user_context,
                filters=None,
                limit=100
            )
            
            # Verify results
            assert isinstance(grid_data, list)
            assert len(grid_data) == 3
            
            # Check first memory structure
            memory = grid_data[0]
            assert "id" in memory
            assert "content" in memory
            assert "type" in memory
            assert "confidence" in memory
            assert "last_accessed" in memory
            assert "relevance_score" in memory
            assert "semantic_cluster" in memory
            assert "relationships" in memory
            
            # Verify memory classification
            assert memory["type"] in ["fact", "preference", "context"]
            assert memory["semantic_cluster"] in ["technical", "personal", "work", "general"]
            assert 0 <= memory["confidence"] <= 1
            
            # Verify mock was called correctly
            mock_recall.assert_called_once_with(
                sample_user_context, "", limit=100, tenant_id="test_tenant"
            )
    
    @pytest.mark.asyncio
    async def test_get_memory_grid_data_with_filters(self, ag_ui_manager, sample_user_context, sample_raw_memories):
        """Test memory grid data with filters applied."""
        
        with patch('ai_karen_engine.core.memory.ag_ui_manager.recall_context') as mock_recall:
            mock_recall.return_value = sample_raw_memories
            
            # Apply filters
            filters = {
                "type": "preference",
                "confidence_min": 0.8
            }
            
            grid_data = await ag_ui_manager.get_memory_grid_data(
                user_ctx=sample_user_context,
                filters=filters,
                limit=50
            )
            
            # Verify filtering worked
            assert isinstance(grid_data, list)
            for memory in grid_data:
                if memory["type"] == "preference":
                    assert memory["confidence"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_get_memory_network_data(self, ag_ui_manager, sample_user_context):
        """Test getting memory relationship data for network visualization."""
        
        # Mock cached memory data
        cache_key = f"{sample_user_context['user_id']}_{sample_user_context['tenant_id']}"
        sample_memories = [
            MemoryGridRow(
                id="mem_1",
                content="Python programming",
                type="fact",
                confidence=0.9,
                last_accessed=datetime.now().isoformat(),
                relevance_score=0.8,
                semantic_cluster="technical",
                relationships=["mem_2"],
                timestamp=int(datetime.now().timestamp()),
                user_id="test_user_123"
            ),
            MemoryGridRow(
                id="mem_2", 
                content="Backend development",
                type="context",
                confidence=0.85,
                last_accessed=datetime.now().isoformat(),
                relevance_score=0.7,
                semantic_cluster="technical",
                relationships=["mem_1"],
                timestamp=int(datetime.now().timestamp()),
                user_id="test_user_123"
            )
        ]
        
        ag_ui_manager._memory_cache[cache_key] = sample_memories
        
        # Get network data
        network_data = await ag_ui_manager.get_memory_network_data(
            user_ctx=sample_user_context,
            max_nodes=50
        )
        
        # Verify structure
        assert "nodes" in network_data
        assert "edges" in network_data
        assert isinstance(network_data["nodes"], list)
        assert isinstance(network_data["edges"], list)
        
        # Verify nodes
        nodes = network_data["nodes"]
        assert len(nodes) == 2
        
        node = nodes[0]
        assert "id" in node
        assert "label" in node
        assert "type" in node
        assert "confidence" in node
        assert "cluster" in node
        assert "size" in node
        assert "color" in node
        
        # Verify edges
        edges = network_data["edges"]
        assert len(edges) >= 1  # Should have at least one relationship
        
        if edges:
            edge = edges[0]
            assert "source" in edge
            assert "target" in edge
            assert "weight" in edge
            assert "type" in edge
            assert "label" in edge
    
    @pytest.mark.asyncio
    async def test_get_memory_analytics(self, ag_ui_manager, sample_user_context):
        """Test getting memory analytics data for AG-UI charts."""
        
        # Mock cached memory data with varied timestamps
        cache_key = f"{sample_user_context['user_id']}_{sample_user_context['tenant_id']}"
        now = datetime.now()
        sample_memories = [
            MemoryGridRow(
                id="mem_1",
                content="Test memory 1",
                type="fact",
                confidence=0.9,
                last_accessed=now.isoformat(),
                relevance_score=0.8,
                semantic_cluster="technical",
                relationships=[],
                timestamp=int(now.timestamp()),
                user_id="test_user_123"
            ),
            MemoryGridRow(
                id="mem_2",
                content="Test memory 2", 
                type="preference",
                confidence=0.7,
                last_accessed=now.isoformat(),
                relevance_score=0.6,
                semantic_cluster="personal",
                relationships=["mem_1"],
                timestamp=int((now - timedelta(days=5)).timestamp()),
                user_id="test_user_123"
            ),
            MemoryGridRow(
                id="mem_3",
                content="Test memory 3",
                type="context",
                confidence=0.8,
                last_accessed=now.isoformat(),
                relevance_score=0.7,
                semantic_cluster="work",
                relationships=[],
                timestamp=int((now - timedelta(days=10)).timestamp()),
                user_id="test_user_123"
            )
        ]
        
        ag_ui_manager._memory_cache[cache_key] = sample_memories
        
        # Get analytics
        analytics = await ag_ui_manager.get_memory_analytics(
            user_ctx=sample_user_context,
            timeframe_days=30
        )
        
        # Verify structure
        assert "total_memories" in analytics
        assert "memories_by_type" in analytics
        assert "memories_by_cluster" in analytics
        assert "confidence_distribution" in analytics
        assert "access_patterns" in analytics
        assert "relationship_stats" in analytics
        
        # Verify data
        assert analytics["total_memories"] == 3
        assert "fact" in analytics["memories_by_type"]
        assert "preference" in analytics["memories_by_type"]
        assert "context" in analytics["memories_by_type"]
        
        assert "technical" in analytics["memories_by_cluster"]
        assert "personal" in analytics["memories_by_cluster"]
        assert "work" in analytics["memories_by_cluster"]
        
        # Verify confidence distribution
        confidence_dist = analytics["confidence_distribution"]
        assert isinstance(confidence_dist, list)
        assert all("range" in item and "count" in item for item in confidence_dist)
        
        # Verify relationship stats
        rel_stats = analytics["relationship_stats"]
        assert "total_relationships" in rel_stats
        assert "connected_memories" in rel_stats
        assert "isolated_memories" in rel_stats
        assert "avg_relationships" in rel_stats
    
    @pytest.mark.asyncio
    async def test_search_memories(self, ag_ui_manager, sample_user_context, sample_raw_memories):
        """Test enhanced semantic search with AG-UI filtering."""
        
        with patch('ai_karen_engine.core.memory.ag_ui_manager.recall_context') as mock_recall:
            mock_recall.return_value = sample_raw_memories
            
            # Perform search
            search_results = await ag_ui_manager.search_memories(
                user_ctx=sample_user_context,
                query="Python programming",
                filters={"type": "preference"},
                limit=25
            )
            
            # Verify results
            assert isinstance(search_results, list)
            
            # Verify search was performed
            mock_recall.assert_called_once_with(
                sample_user_context, "Python programming", limit=50
            )
    
    @pytest.mark.asyncio
    async def test_update_memory_with_metadata(self, ag_ui_manager, sample_user_context):
        """Test enhanced memory update with AG-UI metadata."""
        
        with patch('ai_karen_engine.core.memory.ag_ui_manager.update_memory') as mock_update:
            mock_update.return_value = True
            
            # Update memory with metadata
            metadata = {
                "confidence": 0.95,
                "source": "user_input",
                "tags": ["important", "technical"]
            }
            
            success = await ag_ui_manager.update_memory_with_metadata(
                user_ctx=sample_user_context,
                query="Test query",
                result="Test result",
                metadata=metadata
            )
            
            # Verify success
            assert success is True
            
            # Verify update was called with enhanced result
            mock_update.assert_called_once()
            call_args = mock_update.call_args
            enhanced_result = call_args[0][2]  # Third argument is the result
            
            assert "content" in enhanced_result
            assert "metadata" in enhanced_result
            assert "ag_ui_type" in enhanced_result
            assert "created_at" in enhanced_result
            assert "confidence" in enhanced_result
    
    def test_classify_memory_type(self, ag_ui_manager):
        """Test memory type classification logic."""
        
        # Test preference classification
        preference_content = "I prefer Python over JavaScript"
        assert ag_ui_manager._classify_memory_type(preference_content) == "preference"
        
        # Test fact classification
        fact_content = "The API endpoint is /api/v1/users"
        assert ag_ui_manager._classify_memory_type(fact_content) == "fact"
        
        # Test context classification (default)
        context_content = "Working on the new feature implementation"
        assert ag_ui_manager._classify_memory_type(context_content) == "context"
    
    def test_get_semantic_cluster(self, ag_ui_manager):
        """Test semantic cluster assignment logic."""
        
        # Test technical cluster
        technical_content = "Python function returns None"
        assert ag_ui_manager._get_semantic_cluster(technical_content) == "technical"
        
        # Test personal cluster
        personal_content = "User John Smith prefers morning meetings"
        assert ag_ui_manager._get_semantic_cluster(personal_content) == "personal"
        
        # Test work cluster
        work_content = "Project deadline is next Friday"
        assert ag_ui_manager._get_semantic_cluster(work_content) == "work"
        
        # Test general cluster (default)
        general_content = "Random information about something"
        assert ag_ui_manager._get_semantic_cluster(general_content) == "general"
    
    def test_passes_filters(self, ag_ui_manager):
        """Test filter application logic."""
        
        memory = MemoryGridRow(
            id="test_mem",
            content="Test content",
            type="fact",
            confidence=0.8,
            last_accessed=datetime.now().isoformat(),
            relevance_score=0.7,
            semantic_cluster="technical",
            relationships=[],
            timestamp=int(datetime.now().timestamp()),
            user_id="test_user"
        )
        
        # Test no filters (should pass)
        assert ag_ui_manager._passes_filters(memory, None) is True
        assert ag_ui_manager._passes_filters(memory, {}) is True
        
        # Test type filter (should pass)
        assert ag_ui_manager._passes_filters(memory, {"type": "fact"}) is True
        assert ag_ui_manager._passes_filters(memory, {"type": "preference"}) is False
        
        # Test confidence filters
        assert ag_ui_manager._passes_filters(memory, {"confidence_min": 0.7}) is True
        assert ag_ui_manager._passes_filters(memory, {"confidence_min": 0.9}) is False
        assert ag_ui_manager._passes_filters(memory, {"confidence_max": 0.9}) is True
        assert ag_ui_manager._passes_filters(memory, {"confidence_max": 0.7}) is False
        
        # Test cluster filter
        assert ag_ui_manager._passes_filters(memory, {"cluster": "technical"}) is True
        assert ag_ui_manager._passes_filters(memory, {"cluster": "personal"}) is False
    
    def test_get_cluster_color(self, ag_ui_manager):
        """Test cluster color assignment."""
        
        # Test color assignment
        color1 = ag_ui_manager._get_cluster_color(0)
        color2 = ag_ui_manager._get_cluster_color(1)
        color3 = ag_ui_manager._get_cluster_color(7)  # Should wrap around
        
        assert color1.startswith("#")
        assert color2.startswith("#")
        assert color3.startswith("#")
        assert color1 != color2
        assert color1 == color3  # Should wrap around to same color
    
    def test_count_by_field(self, ag_ui_manager):
        """Test field counting utility."""
        
        memories = [
            MemoryGridRow(
                id="mem_1", content="", type="fact", confidence=0.8,
                last_accessed="", relevance_score=0.7, semantic_cluster="technical",
                relationships=[], timestamp=0, user_id="test"
            ),
            MemoryGridRow(
                id="mem_2", content="", type="fact", confidence=0.9,
                last_accessed="", relevance_score=0.8, semantic_cluster="personal",
                relationships=[], timestamp=0, user_id="test"
            ),
            MemoryGridRow(
                id="mem_3", content="", type="preference", confidence=0.7,
                last_accessed="", relevance_score=0.6, semantic_cluster="technical",
                relationships=[], timestamp=0, user_id="test"
            )
        ]
        
        # Count by type
        type_counts = ag_ui_manager._count_by_field(memories, "type")
        assert type_counts["fact"] == 2
        assert type_counts["preference"] == 1
        
        # Count by cluster
        cluster_counts = ag_ui_manager._count_by_field(memories, "semantic_cluster")
        assert cluster_counts["technical"] == 2
        assert cluster_counts["personal"] == 1
    
    def test_get_confidence_distribution(self, ag_ui_manager):
        """Test confidence distribution calculation."""
        
        memories = [
            MemoryGridRow(
                id="mem_1", content="", type="fact", confidence=0.1,
                last_accessed="", relevance_score=0.7, semantic_cluster="technical",
                relationships=[], timestamp=0, user_id="test"
            ),
            MemoryGridRow(
                id="mem_2", content="", type="fact", confidence=0.5,
                last_accessed="", relevance_score=0.8, semantic_cluster="personal",
                relationships=[], timestamp=0, user_id="test"
            ),
            MemoryGridRow(
                id="mem_3", content="", type="preference", confidence=0.9,
                last_accessed="", relevance_score=0.6, semantic_cluster="technical",
                relationships=[], timestamp=0, user_id="test"
            )
        ]
        
        distribution = ag_ui_manager._get_confidence_distribution(memories)
        
        # Verify structure
        assert isinstance(distribution, list)
        assert len(distribution) == 5  # 5 bins
        
        # Verify bins
        ranges = [item["range"] for item in distribution]
        assert "0.0-0.2" in ranges
        assert "0.4-0.6" in ranges
        assert "0.8-1.0" in ranges
        
        # Verify counts
        for item in distribution:
            if item["range"] == "0.0-0.2":
                assert item["count"] == 1
            elif item["range"] == "0.4-0.6":
                assert item["count"] == 1
            elif item["range"] == "0.8-1.0":
                assert item["count"] == 1
            else:
                assert item["count"] == 0
    
    def test_rank_search_results(self, ag_ui_manager):
        """Test search result ranking logic."""
        
        results = [
            {
                "content": "Python programming language",
                "confidence": 0.8,
                "id": "mem_1"
            },
            {
                "content": "JavaScript development",
                "confidence": 0.9,
                "id": "mem_2"
            },
            {
                "content": "Python web development with Django",
                "confidence": 0.7,
                "id": "mem_3"
            }
        ]
        
        # Rank by "Python" query
        ranked = ag_ui_manager._rank_search_results(results, "Python")
        
        # Verify ranking (Python-related content should rank higher)
        assert len(ranked) == 3
        
        # First result should be Python-related with good confidence
        first_result = ranked[0]
        assert "Python" in first_result["content"]
        
        # Verify all results are present
        result_ids = [r["id"] for r in ranked]
        assert "mem_1" in result_ids
        assert "mem_2" in result_ids
        assert "mem_3" in result_ids


class TestMemoryGridRow:
    """Test MemoryGridRow data model."""
    
    def test_memory_grid_row_creation(self):
        """Test creating MemoryGridRow instance."""
        
        row = MemoryGridRow(
            id="test_mem_123",
            content="Test memory content",
            type="fact",
            confidence=0.85,
            last_accessed="2024-01-15T10:30:00",
            relevance_score=0.9,
            semantic_cluster="technical",
            relationships=["mem_456", "mem_789"],
            timestamp=1705312200,
            user_id="user_123",
            session_id="session_456",
            tenant_id="tenant_789"
        )
        
        assert row.id == "test_mem_123"
        assert row.content == "Test memory content"
        assert row.type == "fact"
        assert row.confidence == 0.85
        assert row.semantic_cluster == "technical"
        assert len(row.relationships) == 2
        assert row.user_id == "user_123"
        assert row.session_id == "session_456"
        assert row.tenant_id == "tenant_789"


class TestMemoryNetworkModels:
    """Test memory network data models."""
    
    def test_memory_network_node_creation(self):
        """Test creating MemoryNetworkNode instance."""
        
        node = MemoryNetworkNode(
            id="node_123",
            label="Test Node",
            type="fact",
            confidence=0.8,
            cluster="technical",
            size=15,
            color="#FF6B6B"
        )
        
        assert node.id == "node_123"
        assert node.label == "Test Node"
        assert node.type == "fact"
        assert node.confidence == 0.8
        assert node.cluster == "technical"
        assert node.size == 15
        assert node.color == "#FF6B6B"
    
    def test_memory_network_edge_creation(self):
        """Test creating MemoryNetworkEdge instance."""
        
        edge = MemoryNetworkEdge(
            source="node_123",
            target="node_456",
            weight=0.7,
            type="semantic",
            label="related"
        )
        
        assert edge.source == "node_123"
        assert edge.target == "node_456"
        assert edge.weight == 0.7
        assert edge.type == "semantic"
        assert edge.label == "related"


class TestMemoryAnalytics:
    """Test memory analytics data model."""
    
    def test_memory_analytics_creation(self):
        """Test creating MemoryAnalytics instance."""
        
        analytics = MemoryAnalytics(
            total_memories=100,
            memories_by_type={"fact": 40, "preference": 30, "context": 30},
            memories_by_cluster={"technical": 50, "personal": 25, "work": 25},
            confidence_distribution=[
                {"range": "0.8-1.0", "count": 60},
                {"range": "0.6-0.8", "count": 30},
                {"range": "0.4-0.6", "count": 10}
            ],
            access_patterns=[
                {"date": "2024-01-15", "count": 25},
                {"date": "2024-01-16", "count": 30}
            ],
            relationship_stats={
                "total_relationships": 150,
                "connected_memories": 80,
                "isolated_memories": 20,
                "avg_relationships": 1.5
            }
        )
        
        assert analytics.total_memories == 100
        assert analytics.memories_by_type["fact"] == 40
        assert analytics.memories_by_cluster["technical"] == 50
        assert len(analytics.confidence_distribution) == 3
        assert len(analytics.access_patterns) == 2
        assert analytics.relationship_stats["total_relationships"] == 150


# Integration test with existing memory system
class TestMemorySystemIntegration:
    """Test integration with existing Karen memory system."""
    
    @pytest.mark.asyncio
    async def test_integration_with_existing_recall_context(self):
        """Test that AG-UI manager integrates properly with existing recall_context."""
        
        ag_ui_manager = AGUIMemoryManager()
        user_ctx = {"user_id": "test_user", "tenant_id": "test_tenant"}
        
        # Mock the existing recall_context function
        with patch('ai_karen_engine.core.memory.ag_ui_manager.recall_context') as mock_recall:
            mock_recall.return_value = [
                {
                    "result": "Test memory result",
                    "query": "test query",
                    "confidence": 0.8,
                    "timestamp": int(datetime.now().timestamp()),
                    "session_id": "test_session"
                }
            ]
            
            # Call AG-UI manager method
            grid_data = await ag_ui_manager.get_memory_grid_data(user_ctx)
            
            # Verify integration
            assert len(grid_data) == 1
            assert grid_data[0]["content"] == "Test memory result"
            
            # Verify existing function was called
            mock_recall.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integration_with_existing_update_memory(self):
        """Test that AG-UI manager integrates properly with existing update_memory."""
        
        ag_ui_manager = AGUIMemoryManager()
        user_ctx = {"user_id": "test_user", "tenant_id": "test_tenant"}
        
        # Mock the existing update_memory function
        with patch('ai_karen_engine.core.memory.ag_ui_manager.update_memory') as mock_update:
            mock_update.return_value = True
            
            # Call AG-UI manager method
            success = await ag_ui_manager.update_memory_with_metadata(
                user_ctx=user_ctx,
                query="test query",
                result="test result",
                metadata={"test": "metadata"}
            )
            
            # Verify integration
            assert success is True
            
            # Verify existing function was called
            mock_update.assert_called_once()
            
            # Verify enhanced result structure
            call_args = mock_update.call_args
            enhanced_result = call_args[0][2]
            assert "content" in enhanced_result
            assert "metadata" in enhanced_result
            assert "ag_ui_type" in enhanced_result


class TestEnhancedSemanticSearch:
    """Test enhanced semantic search with DistilBERT embeddings."""
    
    @pytest.fixture
    def ag_ui_manager(self):
        """Create AG-UI memory manager instance."""
        return AGUIMemoryManager()
    
    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "user_id": "test_user_123",
            "tenant_id": "test_tenant",
            "session_id": "test_session_456"
        }
    
    @pytest.mark.asyncio
    async def test_enhanced_semantic_search_with_neuro_vault(self, ag_ui_manager, sample_user_context):
        """Test enhanced semantic search using NeuroVault vector search."""
        
        # Mock NeuroVault query
        mock_results = [
            {
                "result": "Python is a programming language",
                "query": "programming language",
                "confidence": 0.9,
                "timestamp": int(datetime.now().timestamp()),
                "semantic_score": 0.85
            },
            {
                "result": "JavaScript is used for web development",
                "query": "web development",
                "confidence": 0.8,
                "timestamp": int(datetime.now().timestamp()),
                "semantic_score": 0.75
            }
        ]
        
        with patch.object(ag_ui_manager.neuro_vault, 'query') as mock_neuro_query:
            mock_neuro_query.return_value = mock_results
            
            # Perform enhanced search
            search_results = await ag_ui_manager.search_memories(
                user_ctx=sample_user_context,
                query="Python programming",
                limit=10
            )
            
            # Verify results
            assert isinstance(search_results, list)
            assert len(search_results) == 2
            
            # Verify semantic scoring
            first_result = search_results[0]
            assert "relevance_score" in first_result
            assert first_result["relevance_score"] >= 0.7  # Should have high semantic similarity
            
            # Verify NeuroVault was called
            mock_neuro_query.assert_called_once_with("test_user_123", "Python programming", top_k=20)
    
    @pytest.mark.asyncio
    async def test_enhanced_semantic_search_fallback(self, ag_ui_manager, sample_user_context):
        """Test fallback to recall_context when NeuroVault fails."""
        
        # Mock NeuroVault to fail
        with patch.object(ag_ui_manager.neuro_vault, 'query') as mock_neuro_query:
            mock_neuro_query.side_effect = Exception("NeuroVault unavailable")
            
            # Mock recall_context fallback
            with patch('ai_karen_engine.core.memory.ag_ui_manager.recall_context') as mock_recall:
                mock_recall.return_value = [
                    {
                        "result": "Fallback memory result",
                        "query": "fallback query",
                        "confidence": 0.7,
                        "timestamp": int(datetime.now().timestamp())
                    }
                ]
                
                # Perform search
                search_results = await ag_ui_manager.search_memories(
                    user_ctx=sample_user_context,
                    query="test query",
                    limit=10
                )
                
                # Verify fallback worked
                assert len(search_results) == 1
                assert search_results[0]["content"] == "Fallback memory result"
                
                # Verify fallback was called
                mock_recall.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_semantic_similarity_calculation(self, ag_ui_manager):
        """Test semantic similarity calculation."""
        
        # Test exact match
        similarity = ag_ui_manager._calculate_semantic_similarity("Python programming", "Python programming")
        assert similarity == 1.0
        
        # Test partial match
        similarity = ag_ui_manager._calculate_semantic_similarity("Python", "Python programming language")
        assert 0.0 < similarity < 1.0
        
        # Test no match
        similarity = ag_ui_manager._calculate_semantic_similarity("Python", "JavaScript web development")
        assert similarity >= 0.0
    
    @pytest.mark.asyncio
    async def test_cosine_similarity_calculation(self, ag_ui_manager):
        """Test cosine similarity calculation for vector embeddings."""
        
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = ag_ui_manager._cosine_similarity(vec1, vec2)
        assert similarity == 1.0
        
        # Test orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = ag_ui_manager._cosine_similarity(vec1, vec2)
        assert similarity == 0.0
        
        # Test opposite vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = ag_ui_manager._cosine_similarity(vec1, vec2)
        assert similarity == 0.0  # Clamped to [0, 1]


class TestNLPEnhancedMemoryProcessing:
    """Test NLP-enhanced memory processing with spaCy integration."""
    
    @pytest.fixture
    def ag_ui_manager(self):
        """Create AG-UI memory manager instance."""
        return AGUIMemoryManager()
    
    @pytest.mark.asyncio
    async def test_nlp_enhanced_memory_classification(self, ag_ui_manager):
        """Test NLP-enhanced memory type classification."""
        
        # Mock spaCy service
        mock_doc = Mock()
        mock_doc.ents = []
        
        # Mock token with dependency parsing
        mock_token = Mock()
        mock_token.dep_ = "nsubj"
        mock_token.head.pos_ = "VERB"
        mock_doc.__iter__ = Mock(return_value=iter([mock_token]))
        
        with patch('ai_karen_engine.core.memory.ag_ui_manager.spacy_service_manager') as mock_spacy:
            mock_spacy.is_available.return_value = True
            mock_spacy.process_text = AsyncMock(return_value=mock_doc)
            
            # Test fact classification
            memory_type = await ag_ui_manager._classify_memory_type_with_nlp("The API endpoint is /api/users")
            assert memory_type == "fact"
            
            # Verify spaCy was called
            mock_spacy.process_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_nlp_enhanced_semantic_clustering(self, ag_ui_manager):
        """Test NLP-enhanced semantic clustering."""
        
        # Mock spaCy document with entities
        mock_doc = Mock()
        mock_entity = Mock()
        mock_entity.label_ = "ORG"
        mock_doc.ents = [mock_entity]
        
        with patch('ai_karen_engine.core.memory.ag_ui_manager.spacy_service_manager') as mock_spacy:
            mock_spacy.is_available.return_value = True
            mock_spacy.process_text = AsyncMock(return_value=mock_doc)
            
            # Test technical clustering
            cluster = await ag_ui_manager._get_semantic_cluster_with_nlp("The software company develops APIs")
            assert cluster == "technical"
            
            # Verify spaCy was called
            mock_spacy.process_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_nlp_enhanced_relationship_detection(self, ag_ui_manager):
        """Test NLP-enhanced relationship detection with DistilBERT."""
        
        sample_memory = {
            "result": "Python programming language",
            "user_id": "test_user"
        }
        
        sample_memories = [
            sample_memory,
            {
                "result": "JavaScript web development",
                "user_id": "test_user"
            },
            {
                "result": "Python web frameworks like Django",
                "user_id": "test_user"
            }
        ]
        
        # Mock DistilBERT embeddings
        mock_embeddings = [
            [0.8, 0.2, 0.1],  # Python programming
            [0.1, 0.8, 0.2],  # JavaScript
            [0.7, 0.3, 0.2]   # Python Django (similar to first)
        ]
        
        with patch('ai_karen_engine.core.memory.ag_ui_manager.distilbert_service_manager') as mock_distilbert:
            mock_distilbert.is_available.return_value = True
            mock_distilbert.get_embeddings = AsyncMock(side_effect=[[emb] for emb in mock_embeddings])
            
            # Test relationship detection
            relationships = await ag_ui_manager._get_semantic_relationships(sample_memory, sample_memories)
            
            # Verify relationships were found
            assert isinstance(relationships, list)
            # Should find relationship with Python Django (high similarity)
            assert len(relationships) >= 1
            
            # Verify DistilBERT was called
            assert mock_distilbert.get_embeddings.call_count >= 2


class TestCopilotKitIntegration:
    """Test CopilotKit integration for memory enhancement."""
    
    @pytest.mark.asyncio
    async def test_copilotkit_memory_enhancement_suggestions(self):
        """Test CopilotKit-powered memory enhancement suggestions."""
        
        # Mock CopilotKit provider
        mock_provider = Mock()
        mock_provider.generate_completion = AsyncMock(return_value="""
        Enhancement: Consider adding more specific details about the Python version and use cases.
        Categorization: Type: fact, Cluster: technical
        Relationships: Related to programming languages and software development
        Corrections: No corrections needed
        """)
        
        # Mock the API route function
        from ai_karen_engine.api_routes.memory_ag_ui_routes import _parse_copilot_suggestions
        
        # Test parsing CopilotKit response
        suggestions = _parse_copilot_suggestions(
            "Enhancement: Improved content here\nCategorization: Type: fact, Cluster: technical",
            "Original content"
        )
        
        # Verify suggestions structure
        assert isinstance(suggestions, list)
        if suggestions:
            suggestion = suggestions[0]
            assert hasattr(suggestion, 'type')
            assert hasattr(suggestion, 'content')
            assert hasattr(suggestion, 'confidence')
            assert hasattr(suggestion, 'reasoning')
    
    @pytest.mark.asyncio
    async def test_copilotkit_memory_categorization(self):
        """Test CopilotKit-powered memory categorization."""
        
        from ai_karen_engine.api_routes.memory_ag_ui_routes import _parse_categorization_response
        
        # Test parsing categorization response
        response = """
        Type: preference
        Cluster: personal
        Confidence: 0.85
        Reasoning: Content shows personal preference for programming languages
        """
        
        parsed = _parse_categorization_response(response)
        
        # Verify parsing
        assert parsed is not None
        assert parsed["type"] == "preference"
        assert parsed["cluster"] == "personal"
        assert parsed["confidence"] == 0.85
        assert "preference" in parsed["reasoning"]
    
    @pytest.mark.asyncio
    async def test_copilotkit_fallback_suggestions(self):
        """Test fallback suggestions when CopilotKit is unavailable."""
        
        from ai_karen_engine.api_routes.memory_ag_ui_routes import _generate_fallback_suggestions
        
        # Test fallback suggestions
        suggestions = _generate_fallback_suggestions(
            content="I prefer Python",
            current_type="context",
            current_cluster="general"
        )
        
        # Verify fallback suggestions
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Should suggest preference type
        preference_suggestion = next((s for s in suggestions if s.type == "categorization"), None)
        assert preference_suggestion is not None
        assert "preference" in preference_suggestion.content.lower()


class TestAGUIComponentIntegration:
    """Test AG-UI component integration and data formatting."""
    
    @pytest.fixture
    def sample_grid_data(self):
        """Sample grid data for AG-UI testing."""
        return [
            {
                "id": "mem_1",
                "content": "Python is a programming language",
                "type": "fact",
                "confidence": 0.9,
                "last_accessed": "2024-01-15T10:30:00",
                "relevance_score": 0.85,
                "semantic_cluster": "technical",
                "relationships": ["mem_2"],
                "timestamp": 1705312200,
                "user_id": "test_user"
            },
            {
                "id": "mem_2",
                "content": "I prefer Python over JavaScript",
                "type": "preference",
                "confidence": 0.8,
                "last_accessed": "2024-01-15T11:00:00",
                "relevance_score": 0.75,
                "semantic_cluster": "personal",
                "relationships": ["mem_1"],
                "timestamp": 1705314000,
                "user_id": "test_user"
            }
        ]
    
    def test_ag_grid_data_structure(self, sample_grid_data):
        """Test that data structure is compatible with AG-Grid."""
        
        # Verify required AG-Grid columns
        required_columns = [
            "id", "content", "type", "confidence", 
            "last_accessed", "relevance_score", "semantic_cluster", "relationships"
        ]
        
        for row in sample_grid_data:
            for column in required_columns:
                assert column in row, f"Missing required column: {column}"
        
        # Verify data types
        for row in sample_grid_data:
            assert isinstance(row["id"], str)
            assert isinstance(row["content"], str)
            assert row["type"] in ["fact", "preference", "context"]
            assert isinstance(row["confidence"], (int, float))
            assert 0 <= row["confidence"] <= 1
            assert isinstance(row["relationships"], list)
    
    def test_ag_charts_analytics_data_structure(self):
        """Test that analytics data is compatible with AG-Charts."""
        
        # Sample analytics data
        analytics_data = {
            "total_memories": 100,
            "memories_by_type": {"fact": 40, "preference": 30, "context": 30},
            "memories_by_cluster": {"technical": 50, "personal": 25, "work": 25},
            "confidence_distribution": [
                {"range": "0.8-1.0", "count": 60},
                {"range": "0.6-0.8", "count": 30},
                {"range": "0.4-0.6", "count": 10}
            ],
            "access_patterns": [
                {"date": "2024-01-15", "count": 25},
                {"date": "2024-01-16", "count": 30}
            ]
        }
        
        # Verify structure for AG-Charts
        assert isinstance(analytics_data["memories_by_type"], dict)
        assert isinstance(analytics_data["confidence_distribution"], list)
        assert isinstance(analytics_data["access_patterns"], list)
        
        # Verify chart data format
        for item in analytics_data["confidence_distribution"]:
            assert "range" in item
            assert "count" in item
            assert isinstance(item["count"], int)
        
        for item in analytics_data["access_patterns"]:
            assert "date" in item
            assert "count" in item
            assert isinstance(item["count"], int)
    
    def test_network_visualization_data_structure(self):
        """Test that network data is compatible with AG-UI network visualization."""
        
        # Sample network data
        network_data = {
            "nodes": [
                {
                    "id": "node_1",
                    "label": "Python Programming",
                    "type": "fact",
                    "confidence": 0.9,
                    "cluster": "technical",
                    "size": 20,
                    "color": "#FF6B6B"
                }
            ],
            "edges": [
                {
                    "source": "node_1",
                    "target": "node_2",
                    "weight": 0.8,
                    "type": "semantic",
                    "label": "related"
                }
            ]
        }
        
        # Verify nodes structure
        for node in network_data["nodes"]:
            required_node_fields = ["id", "label", "type", "confidence", "cluster", "size", "color"]
            for field in required_node_fields:
                assert field in node
        
        # Verify edges structure
        for edge in network_data["edges"]:
            required_edge_fields = ["source", "target", "weight", "type", "label"]
            for field in required_edge_fields:
                assert field in edge
            assert 0 <= edge["weight"] <= 1


class TestMemoryInterfaceErrorHandling:
    """Test error handling in memory interface components."""
    
    @pytest.fixture
    def ag_ui_manager(self):
        """Create AG-UI memory manager instance."""
        return AGUIMemoryManager()
    
    @pytest.mark.asyncio
    async def test_memory_grid_error_handling(self, ag_ui_manager):
        """Test error handling in memory grid data retrieval."""
        
        user_ctx = {"user_id": "test_user", "tenant_id": "test_tenant"}
        
        # Mock recall_context to raise exception
        with patch('ai_karen_engine.core.memory.ag_ui_manager.recall_context') as mock_recall:
            mock_recall.side_effect = Exception("Database connection failed")
            
            # Should handle error gracefully
            grid_data = await ag_ui_manager.get_memory_grid_data(user_ctx)
            
            # Should return empty list on error
            assert grid_data == []
    
    @pytest.mark.asyncio
    async def test_memory_search_error_handling(self, ag_ui_manager):
        """Test error handling in memory search."""
        
        user_ctx = {"user_id": "test_user", "tenant_id": "test_tenant"}
        
        # Mock NeuroVault to raise exception
        with patch.object(ag_ui_manager.neuro_vault, 'query') as mock_neuro_query:
            mock_neuro_query.side_effect = Exception("Vector search failed")
            
            # Mock recall_context to also fail
            with patch('ai_karen_engine.core.memory.ag_ui_manager.recall_context') as mock_recall:
                mock_recall.side_effect = Exception("Fallback also failed")
                
                # Should handle error gracefully
                search_results = await ag_ui_manager.search_memories(
                    user_ctx=user_ctx,
                    query="test query"
                )
                
                # Should return empty list on error
                assert search_results == []
    
    @pytest.mark.asyncio
    async def test_memory_update_error_handling(self, ag_ui_manager):
        """Test error handling in memory updates."""
        
        user_ctx = {"user_id": "test_user", "tenant_id": "test_tenant"}
        
        # Mock update_memory to fail
        with patch('ai_karen_engine.core.memory.ag_ui_manager.update_memory') as mock_update:
            mock_update.side_effect = Exception("Update failed")
            
            # Should handle error gracefully
            success = await ag_ui_manager.update_memory_with_metadata(
                user_ctx=user_ctx,
                query="test query",
                result="test result"
            )
            
            # Should return False on error
            assert success is False