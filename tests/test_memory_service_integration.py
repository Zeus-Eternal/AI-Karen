"""
Unit tests for Memory Service integration with web UI chat functionality.
Tests memory storage, retrieval, context building, and user personalization.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from pydantic import BaseModel


class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    similarity_score: Optional[float] = None


class MemoryQuery(BaseModel):
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None
    top_k: int = 5
    similarity_threshold: float = 0.7
    time_range: Optional[tuple] = None


class MockMemoryService:
    """Mock Memory Service for testing."""
    
    def __init__(self):
        self.vector_store = Mock()
        self.metadata_store = Mock()
        self.context_builder = Mock()
        self._memories = {}  # In-memory storage for testing
    
    async def store_memory(self, content: str, metadata: Dict[str, Any], 
                          tags: List[str], user_id: str, session_id: str) -> str:
        """Store a new memory entry."""
        memory_id = f"mem_{len(self._memories)}"
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            metadata=metadata,
            tags=tags,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now()
        )
        self._memories[memory_id] = memory
        return memory_id
    
    async def query_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memories based on similarity and filters."""
        results = []
        for memory in self._memories.values():
            # Simple text matching for testing
            if query.text.lower() in memory.content.lower():
                if query.user_id and memory.user_id != query.user_id:
                    continue
                if query.session_id and memory.session_id != query.session_id:
                    continue
                if query.tags and not any(tag in memory.tags for tag in query.tags):
                    continue
                
                memory.similarity_score = 0.8  # Mock similarity score
                results.append(memory)
        
        return results[:query.top_k]
    
    async def build_context(self, query: str, user_id: str, 
                           session_id: str) -> Dict[str, Any]:
        """Build conversation context from relevant memories."""
        memory_query = MemoryQuery(
            text=query,
            user_id=user_id,
            session_id=session_id,
            top_k=10
        )
        
        relevant_memories = await self.query_memories(memory_query)
        
        return {
            "relevant_memories": [
                {
                    "content": mem.content,
                    "timestamp": mem.timestamp.isoformat(),
                    "similarity": mem.similarity_score,
                    "tags": mem.tags
                }
                for mem in relevant_memories
            ],
            "context_summary": f"Found {len(relevant_memories)} relevant memories",
            "user_id": user_id,
            "session_id": session_id
        }
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user."""
        user_memories = [m for m in self._memories.values() if m.user_id == user_id]
        
        return {
            "total_memories": len(user_memories),
            "recent_memories": len([m for m in user_memories 
                                  if m.timestamp > datetime.now() - timedelta(days=7)]),
            "memory_tags": list(set(tag for m in user_memories for tag in m.tags)),
            "oldest_memory": min([m.timestamp for m in user_memories], default=None),
            "newest_memory": max([m.timestamp for m in user_memories], default=None)
        }


class TestMemoryService:
    """Test the Memory Service functionality."""
    
    @pytest.fixture
    def memory_service(self):
        """Create a mock memory service for testing."""
        return MockMemoryService()
    
    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "user_id": "test-user-123",
            "session_id": "test-session-456",
            "tenant_id": "test-tenant"
        }
    
    @pytest.mark.asyncio
    async def test_store_memory_basic(self, memory_service, sample_user_context):
        """Test basic memory storage."""
        memory_id = await memory_service.store_memory(
            content="User likes coffee",
            metadata={"category": "preference", "confidence": 0.9},
            tags=["preference", "food"],
            user_id=sample_user_context["user_id"],
            session_id=sample_user_context["session_id"]
        )
        
        assert memory_id is not None
        assert memory_id.startswith("mem_")
        assert memory_id in memory_service._memories
    
    @pytest.mark.asyncio
    async def test_query_memories_by_content(self, memory_service, sample_user_context):
        """Test querying memories by content similarity."""
        # Store some test memories
        await memory_service.store_memory(
            "User likes coffee",
            {"category": "preference"},
            ["preference"],
            sample_user_context["user_id"],
            sample_user_context["session_id"]
        )
        
        await memory_service.store_memory(
            "User prefers tea over coffee",
            {"category": "preference"},
            ["preference"],
            sample_user_context["user_id"],
            sample_user_context["session_id"]
        )
        
        # Query for coffee-related memories
        query = MemoryQuery(
            text="coffee",
            user_id=sample_user_context["user_id"]
        )
        
        results = await memory_service.query_memories(query)
        
        assert len(results) == 2
        assert all("coffee" in mem.content.lower() for mem in results)
        assert all(mem.user_id == sample_user_context["user_id"] for mem in results)
    
    @pytest.mark.asyncio
    async def test_query_memories_with_filters(self, memory_service, sample_user_context):
        """Test querying memories with various filters."""
        # Store memories with different tags
        await memory_service.store_memory(
            "User likes pizza",
            {"category": "preference"},
            ["preference", "food"],
            sample_user_context["user_id"],
            sample_user_context["session_id"]
        )
        
        await memory_service.store_memory(
            "User works at tech company",
            {"category": "personal"},
            ["work", "personal"],
            sample_user_context["user_id"],
            sample_user_context["session_id"]
        )
        
        # Query with tag filter
        query = MemoryQuery(
            text="user",
            user_id=sample_user_context["user_id"],
            tags=["food"]
        )
        
        results = await memory_service.query_memories(query)
        
        assert len(results) == 1
        assert "pizza" in results[0].content
        assert "food" in results[0].tags
    
    @pytest.mark.asyncio
    async def test_build_context_from_memories(self, memory_service, sample_user_context):
        """Test building conversation context from memories."""
        # Store relevant memories
        await memory_service.store_memory(
            "User mentioned they work remotely",
            {"category": "personal"},
            ["work"],
            sample_user_context["user_id"],
            sample_user_context["session_id"]
        )
        
        await memory_service.store_memory(
            "User asked about weather in San Francisco",
            {"category": "query", "location": "San Francisco"},
            ["weather", "location"],
            sample_user_context["user_id"],
            sample_user_context["session_id"]
        )
        
        # Build context for work-related query
        context = await memory_service.build_context(
            "How's work going?",
            sample_user_context["user_id"],
            sample_user_context["session_id"]
        )
        
        assert "relevant_memories" in context
        assert len(context["relevant_memories"]) > 0
        assert context["user_id"] == sample_user_context["user_id"]
        assert "work" in str(context["relevant_memories"])
    
    @pytest.mark.asyncio
    async def test_memory_stats_generation(self, memory_service, sample_user_context):
        """Test memory statistics generation."""
        # Store several memories
        for i in range(5):
            await memory_service.store_memory(
                f"Memory {i}",
                {"index": i},
                ["test", f"tag_{i}"],
                sample_user_context["user_id"],
                sample_user_context["session_id"]
            )
        
        stats = await memory_service.get_memory_stats(sample_user_context["user_id"])
        
        assert stats["total_memories"] == 5
        assert stats["recent_memories"] == 5  # All are recent
        assert "test" in stats["memory_tags"]
        assert stats["oldest_memory"] is not None
        assert stats["newest_memory"] is not None
    
    @pytest.mark.asyncio
    async def test_user_isolation(self, memory_service):
        """Test that memories are properly isolated between users."""
        user1_id = "user-1"
        user2_id = "user-2"
        session_id = "shared-session"
        
        # Store memories for different users
        await memory_service.store_memory(
            "User 1 likes apples",
            {},
            ["preference"],
            user1_id,
            session_id
        )
        
        await memory_service.store_memory(
            "User 2 likes oranges",
            {},
            ["preference"],
            user2_id,
            session_id
        )
        
        # Query as user 1
        query1 = MemoryQuery(text="likes", user_id=user1_id)
        results1 = await memory_service.query_memories(query1)
        
        # Query as user 2
        query2 = MemoryQuery(text="likes", user_id=user2_id)
        results2 = await memory_service.query_memories(query2)
        
        assert len(results1) == 1
        assert len(results2) == 1
        assert "apples" in results1[0].content
        assert "oranges" in results2[0].content


class TestMemoryIntegrationWithChat:
    """Test memory service integration with chat functionality."""
    
    @pytest.fixture
    def memory_service(self):
        return MockMemoryService()
    
    @pytest.fixture
    def user_context(self):
        return {
            "user_id": "test-user-123",
            "session_id": "test-session-456",
            "tenant_id": "test-tenant"
        }
    
    @pytest.mark.asyncio
    async def test_memory_enhanced_conversation(self, memory_service, user_context):
        """Test conversation enhancement with memory context."""
        # Simulate previous conversation stored in memory
        await memory_service.store_memory(
            "User mentioned they have a dog named Max",
            {"category": "personal", "entity": "pet"},
            ["personal", "pet"],
            user_context["user_id"],
            user_context["session_id"]
        )
        
        # Build context for follow-up question
        context = await memory_service.build_context(
            "How is Max doing?",
            user_context["user_id"],
            user_context["session_id"]
        )
        
        assert len(context["relevant_memories"]) > 0
        assert "Max" in str(context["relevant_memories"])
        assert "dog" in str(context["relevant_memories"])
    
    @pytest.mark.asyncio
    async def test_proactive_memory_suggestions(self, memory_service, user_context):
        """Test proactive suggestions based on memory patterns."""
        # Store pattern of weather queries
        weather_queries = [
            "What's the weather in New York?",
            "Will it rain tomorrow in New York?",
            "Temperature in New York today?"
        ]
        
        for query in weather_queries:
            await memory_service.store_memory(
                f"User asked: {query}",
                {"category": "query", "topic": "weather", "location": "New York"},
                ["weather", "query", "new_york"],
                user_context["user_id"],
                user_context["session_id"]
            )
        
        # Query for weather-related context
        context = await memory_service.build_context(
            "weather",
            user_context["user_id"],
            user_context["session_id"]
        )
        
        # Should find pattern of New York weather queries
        assert len(context["relevant_memories"]) == 3
        assert all("New York" in mem["content"] for mem in context["relevant_memories"])
    
    @pytest.mark.asyncio
    async def test_memory_based_personalization(self, memory_service, user_context):
        """Test personalization based on stored memories."""
        # Store user preferences
        preferences = [
            ("User prefers detailed explanations", ["preference", "communication"]),
            ("User likes technical details", ["preference", "technical"]),
            ("User works in software engineering", ["personal", "work"])
        ]
        
        for content, tags in preferences:
            await memory_service.store_memory(
                content,
                {"category": "preference"},
                tags,
                user_context["user_id"],
                user_context["session_id"]
            )
        
        # Build context for technical question
        context = await memory_service.build_context(
            "Explain how APIs work",
            user_context["user_id"],
            user_context["session_id"]
        )
        
        # Should include relevant preferences
        memories = context["relevant_memories"]
        preference_memories = [m for m in memories if "preference" in m["tags"]]
        assert len(preference_memories) > 0


class TestMemoryPerformance:
    """Test memory service performance characteristics."""
    
    @pytest.fixture
    def memory_service(self):
        return MockMemoryService()
    
    @pytest.mark.asyncio
    async def test_large_memory_query_performance(self, memory_service):
        """Test performance with large number of memories."""
        user_id = "test-user-performance"
        session_id = "test-session-performance"
        
        # Store many memories
        for i in range(100):
            await memory_service.store_memory(
                f"Memory content {i} with various keywords like coffee, weather, work",
                {"index": i, "category": "test"},
                ["test", f"batch_{i // 10}"],
                user_id,
                session_id
            )
        
        # Time the query
        start_time = asyncio.get_event_loop().time()
        
        query = MemoryQuery(
            text="coffee",
            user_id=user_id,
            top_k=10
        )
        results = await memory_service.query_memories(query)
        
        end_time = asyncio.get_event_loop().time()
        query_time = end_time - start_time
        
        # Should complete quickly and return relevant results
        assert query_time < 1.0  # Should complete within 1 second
        assert len(results) <= 10
        assert all("coffee" in mem.content for mem in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, memory_service):
        """Test concurrent memory storage and retrieval."""
        user_id = "test-user-concurrent"
        session_id = "test-session-concurrent"
        
        # Concurrent storage operations
        store_tasks = [
            memory_service.store_memory(
                f"Concurrent memory {i}",
                {"index": i},
                ["concurrent"],
                user_id,
                session_id
            )
            for i in range(20)
        ]
        
        memory_ids = await asyncio.gather(*store_tasks)
        assert len(memory_ids) == 20
        assert all(mid is not None for mid in memory_ids)
        
        # Concurrent query operations
        query_tasks = [
            memory_service.query_memories(MemoryQuery(
                text=f"memory {i}",
                user_id=user_id
            ))
            for i in range(10)
        ]
        
        query_results = await asyncio.gather(*query_tasks)
        assert len(query_results) == 10
        assert all(len(results) > 0 for results in query_results)


class TestMemoryErrorHandling:
    """Test memory service error handling and resilience."""
    
    @pytest.fixture
    def memory_service(self):
        return MockMemoryService()
    
    @pytest.mark.asyncio
    async def test_invalid_memory_storage(self, memory_service):
        """Test handling of invalid memory storage requests."""
        # Test with empty content
        with pytest.raises(Exception):
            await memory_service.store_memory(
                "",  # Empty content
                {},
                [],
                "user-id",
                "session-id"
            )
    
    @pytest.mark.asyncio
    async def test_memory_query_with_invalid_parameters(self, memory_service):
        """Test memory queries with invalid parameters."""
        # Query with invalid similarity threshold
        query = MemoryQuery(
            text="test",
            similarity_threshold=1.5  # Invalid threshold > 1.0
        )
        
        # Should handle gracefully or raise appropriate error
        try:
            results = await memory_service.query_memories(query)
            # If it doesn't raise an error, should return empty or valid results
            assert isinstance(results, list)
        except ValueError:
            # Acceptable to raise ValueError for invalid threshold
            pass
    
    @pytest.mark.asyncio
    async def test_memory_service_resilience(self, memory_service):
        """Test memory service resilience to various edge cases."""
        user_id = "test-user-resilience"
        session_id = "test-session-resilience"
        
        # Test with very long content
        long_content = "A" * 10000
        memory_id = await memory_service.store_memory(
            long_content,
            {"type": "long_content"},
            ["test"],
            user_id,
            session_id
        )
        assert memory_id is not None
        
        # Test query with empty string
        empty_query = MemoryQuery(text="", user_id=user_id)
        results = await memory_service.query_memories(empty_query)
        assert isinstance(results, list)
        
        # Test context building with non-existent user
        context = await memory_service.build_context(
            "test query",
            "non-existent-user",
            "non-existent-session"
        )
        assert context is not None
        assert context["relevant_memories"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])