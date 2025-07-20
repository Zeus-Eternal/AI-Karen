"""
Comprehensive tests for the database integration system.
Tests all components: tenant management, memory management, conversation management.
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_karen_engine.database.integration_manager import (
    DatabaseIntegrationManager, DatabaseConfig
)
from src.ai_karen_engine.database.tenant_manager import TenantConfig
from src.ai_karen_engine.database.memory_manager import MemoryQuery
from src.ai_karen_engine.database.conversation_manager import MessageRole


class TestDatabaseIntegrationManager:
    """Test database integration manager."""
    
    @pytest.fixture
    async def db_manager(self):
        """Create database manager for testing."""
        config = DatabaseConfig(
            postgres_url="postgresql://test:test@localhost:5432/test_db",
            enable_redis=False,
            enable_milvus=False,
            enable_elasticsearch=False
        )
        
        manager = DatabaseIntegrationManager(config)
        
        # Mock all external dependencies
        manager.db_client = AsyncMock()
        manager.milvus_client = AsyncMock()
        manager.embedding_manager = AsyncMock()
        manager.redis_client = None
        manager.elasticsearch_client = None
        
        # Mock managers
        manager.tenant_manager = AsyncMock()
        manager.memory_manager = AsyncMock()
        manager.conversation_manager = AsyncMock()
        
        manager._initialized = True
        
        return manager
    
    @pytest.mark.asyncio
    async def test_create_tenant(self, db_manager):
        """Test tenant creation."""
        # Mock tenant manager response
        mock_tenant = MagicMock()
        mock_tenant.id = uuid.uuid4()
        mock_tenant.name = "Test Tenant"
        mock_tenant.slug = "test-tenant"
        mock_tenant.subscription_tier = "basic"
        mock_tenant.created_at = datetime.utcnow()
        
        db_manager.tenant_manager.create_tenant.return_value = mock_tenant
        
        # Test tenant creation
        result = await db_manager.create_tenant(
            name="Test Tenant",
            slug="test-tenant",
            admin_email="admin@test.com"
        )
        
        assert result["name"] == "Test Tenant"
        assert result["slug"] == "test-tenant"
        assert "tenant_id" in result
        
        # Verify tenant manager was called
        db_manager.tenant_manager.create_tenant.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_memory(self, db_manager):
        """Test memory storage."""
        tenant_id = str(uuid.uuid4())
        memory_id = str(uuid.uuid4())
        
        # Mock memory manager response
        db_manager.memory_manager.store_memory.return_value = memory_id
        
        # Test memory storage
        result = await db_manager.store_memory(
            tenant_id=tenant_id,
            content="Test memory content",
            user_id="user123",
            metadata={"type": "test"}
        )
        
        assert result == memory_id
        
        # Verify memory manager was called
        db_manager.memory_manager.store_memory.assert_called_once_with(
            tenant_id=tenant_id,
            content="Test memory content",
            user_id="user123",
            session_id=None,
            metadata={"type": "test"},
            tags=None
        )
    
    @pytest.mark.asyncio
    async def test_query_memories(self, db_manager):
        """Test memory querying."""
        tenant_id = str(uuid.uuid4())
        
        # Mock memory objects
        mock_memory = MagicMock()
        mock_memory.to_dict.return_value = {
            "id": "memory123",
            "content": "Test content",
            "similarity_score": 0.85
        }
        
        db_manager.memory_manager.query_memories.return_value = [mock_memory]
        
        # Test memory querying
        result = await db_manager.query_memories(
            tenant_id=tenant_id,
            query_text="test query",
            top_k=5
        )
        
        assert len(result) == 1
        assert result[0]["id"] == "memory123"
        assert result[0]["similarity_score"] == 0.85
        
        # Verify memory manager was called with correct query
        db_manager.memory_manager.query_memories.assert_called_once()
        call_args = db_manager.memory_manager.query_memories.call_args
        assert call_args[0][0] == tenant_id
        assert call_args[0][1].text == "test query"
        assert call_args[0][1].top_k == 5
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, db_manager):
        """Test conversation creation."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock conversation object
        mock_conversation = MagicMock()
        mock_conversation.to_dict.return_value = {
            "id": "conv123",
            "user_id": user_id,
            "title": "Test Conversation",
            "messages": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        db_manager.conversation_manager.create_conversation.return_value = mock_conversation
        
        # Test conversation creation
        result = await db_manager.create_conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title="Test Conversation"
        )
        
        assert result["id"] == "conv123"
        assert result["user_id"] == user_id
        assert result["title"] == "Test Conversation"
        
        # Verify conversation manager was called
        db_manager.conversation_manager.create_conversation.assert_called_once_with(
            tenant_id=tenant_id,
            user_id=user_id,
            title="Test Conversation",
            initial_message=None
        )
    
    @pytest.mark.asyncio
    async def test_add_message(self, db_manager):
        """Test adding message to conversation."""
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        
        # Mock message object
        mock_message = MagicMock()
        mock_message.to_dict.return_value = {
            "id": "msg123",
            "role": "user",
            "content": "Hello",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        db_manager.conversation_manager.add_message.return_value = mock_message
        
        # Test adding message
        result = await db_manager.add_message(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role="user",
            content="Hello"
        )
        
        assert result["id"] == "msg123"
        assert result["role"] == "user"
        assert result["content"] == "Hello"
        
        # Verify conversation manager was called
        db_manager.conversation_manager.add_message.assert_called_once_with(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Hello",
            metadata=None
        )
    
    @pytest.mark.asyncio
    async def test_health_check(self, db_manager):
        """Test health check functionality."""
        # Mock component health checks
        db_manager.db_client.health_check.return_value = {"status": "healthy"}
        db_manager.milvus_client.health_check.return_value = {"status": "healthy"}
        db_manager.tenant_manager.health_check.return_value = {"status": "healthy"}
        
        # Test health check
        result = await db_manager.health_check()
        
        assert result["status"] == "healthy"
        assert "components" in result
        assert "timestamp" in result
        
        # Verify all health checks were called
        db_manager.db_client.health_check.assert_called_once()
        db_manager.tenant_manager.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, db_manager):
        """Test system metrics collection."""
        # Mock manager metrics
        db_manager.memory_manager.metrics = {
            "memories_stored": 100,
            "queries_total": 50
        }
        db_manager.conversation_manager.metrics = {
            "conversations_created": 25,
            "messages_added": 200
        }
        
        # Test metrics collection
        result = await db_manager.get_system_metrics()
        
        assert "timestamp" in result
        assert result["memory_manager"]["memories_stored"] == 100
        assert result["conversation_manager"]["conversations_created"] == 25
    
    @pytest.mark.asyncio
    async def test_maintenance_tasks(self, db_manager):
        """Test maintenance task execution."""
        # Mock tenant list
        mock_tenant = MagicMock()
        mock_tenant.id = uuid.uuid4()
        db_manager.tenant_manager.list_tenants.return_value = [mock_tenant]
        
        # Mock maintenance operations
        db_manager.memory_manager.prune_expired_memories.return_value = 5
        db_manager.conversation_manager.cleanup_inactive_conversations.return_value = 3
        
        # Test maintenance tasks
        result = await db_manager.maintenance_tasks()
        
        assert result["status"] == "completed"
        assert len(result["tasks_completed"]) == 2
        assert "Pruned 5 expired memories" in result["tasks_completed"][0]
        assert "Marked 3 conversations as inactive" in result["tasks_completed"][1]


class TestTenantManager:
    """Test tenant management functionality."""
    
    @pytest.fixture
    def tenant_config(self):
        """Create test tenant configuration."""
        return TenantConfig(
            name="Test Tenant",
            slug="test-tenant",
            subscription_tier="pro",
            settings={"feature_x": True},
            limits={"max_users": 100}
        )
    
    def test_tenant_config_creation(self, tenant_config):
        """Test tenant configuration creation."""
        assert tenant_config.name == "Test Tenant"
        assert tenant_config.slug == "test-tenant"
        assert tenant_config.subscription_tier == "pro"
        assert tenant_config.settings["feature_x"] is True
        assert tenant_config.limits["max_users"] == 100
    
    def test_tenant_config_default_limits(self):
        """Test default limits based on subscription tier."""
        basic_config = TenantConfig(
            name="Basic Tenant",
            slug="basic-tenant",
            subscription_tier="basic"
        )
        
        assert basic_config.limits["max_users"] == 5
        assert basic_config.limits["max_conversations"] == 100
        
        enterprise_config = TenantConfig(
            name="Enterprise Tenant",
            slug="enterprise-tenant",
            subscription_tier="enterprise"
        )
        
        assert enterprise_config.limits["max_users"] == -1  # unlimited


class TestMemoryManager:
    """Test memory management functionality."""
    
    def test_memory_query_creation(self):
        """Test memory query creation."""
        query = MemoryQuery(
            text="test query",
            user_id="user123",
            top_k=5,
            similarity_threshold=0.8,
            tags=["important"]
        )
        
        assert query.text == "test query"
        assert query.user_id == "user123"
        assert query.top_k == 5
        assert query.similarity_threshold == 0.8
        assert "important" in query.tags
    
    def test_memory_query_to_dict(self):
        """Test memory query serialization."""
        query = MemoryQuery(
            text="test query",
            user_id="user123",
            metadata_filter={"type": "important"}
        )
        
        query_dict = query.to_dict()
        
        assert query_dict["text"] == "test query"
        assert query_dict["user_id"] == "user123"
        assert query_dict["metadata_filter"]["type"] == "important"


class TestConversationManager:
    """Test conversation management functionality."""
    
    def test_message_role_enum(self):
        """Test message role enumeration."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.FUNCTION.value == "function"
    
    def test_message_role_validation(self):
        """Test message role validation."""
        # Valid roles
        user_role = MessageRole("user")
        assert user_role == MessageRole.USER
        
        assistant_role = MessageRole("assistant")
        assert assistant_role == MessageRole.ASSISTANT
        
        # Invalid role should raise ValueError
        with pytest.raises(ValueError):
            MessageRole("invalid_role")


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_default_config(self):
        """Test default database configuration."""
        config = DatabaseConfig()
        
        assert config.milvus_host == "localhost"
        assert config.milvus_port == 19530
        assert config.elasticsearch_host == "localhost"
        assert config.elasticsearch_port == 9200
        assert config.pool_size == 10
        assert config.enable_redis is True
        assert config.enable_milvus is True
        assert config.enable_elasticsearch is True
    
    def test_custom_config(self):
        """Test custom database configuration."""
        config = DatabaseConfig(
            postgres_url="postgresql://custom:pass@host:5432/db",
            redis_url="redis://custom:6379/1",
            milvus_host="custom-milvus",
            milvus_port=19531,
            pool_size=20,
            enable_redis=False
        )
        
        assert config.postgres_url == "postgresql://custom:pass@host:5432/db"
        assert config.redis_url == "redis://custom:6379/1"
        assert config.milvus_host == "custom-milvus"
        assert config.milvus_port == 19531
        assert config.pool_size == 20
        assert config.enable_redis is False


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""
    
    @pytest.fixture
    async def full_db_manager(self):
        """Create a fully mocked database manager."""
        config = DatabaseConfig(enable_redis=False, enable_milvus=False, enable_elasticsearch=False)
        manager = DatabaseIntegrationManager(config)
        
        # Mock all components
        manager.db_client = AsyncMock()
        manager.tenant_manager = AsyncMock()
        manager.memory_manager = AsyncMock()
        manager.conversation_manager = AsyncMock()
        manager._initialized = True
        
        return manager
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, full_db_manager):
        """Test complete conversation flow with memory integration."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock tenant creation
        mock_tenant = MagicMock()
        mock_tenant.id = uuid.UUID(tenant_id)
        mock_tenant.name = "Test Tenant"
        full_db_manager.tenant_manager.create_tenant.return_value = mock_tenant
        
        # Mock conversation creation
        mock_conversation = MagicMock()
        mock_conversation.to_dict.return_value = {
            "id": "conv123",
            "user_id": user_id,
            "messages": []
        }
        full_db_manager.conversation_manager.create_conversation.return_value = mock_conversation
        
        # Mock message addition
        mock_message = MagicMock()
        mock_message.to_dict.return_value = {
            "id": "msg123",
            "role": "user",
            "content": "Hello AI"
        }
        full_db_manager.conversation_manager.add_message.return_value = mock_message
        
        # Mock memory storage
        full_db_manager.memory_manager.store_memory.return_value = "memory123"
        
        # Execute full flow
        # 1. Create tenant
        tenant_result = await full_db_manager.create_tenant(
            name="Test Tenant",
            slug="test-tenant",
            admin_email="admin@test.com"
        )
        
        # 2. Create conversation
        conv_result = await full_db_manager.create_conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title="Test Chat"
        )
        
        # 3. Add user message
        msg_result = await full_db_manager.add_message(
            tenant_id=tenant_id,
            conversation_id=conv_result["id"],
            role="user",
            content="Hello AI"
        )
        
        # 4. Store memory
        memory_result = await full_db_manager.store_memory(
            tenant_id=tenant_id,
            content="User said hello",
            user_id=user_id,
            session_id=conv_result["id"]
        )
        
        # Verify all operations completed successfully
        assert tenant_result["name"] == "Test Tenant"
        assert conv_result["id"] == "conv123"
        assert msg_result["content"] == "Hello AI"
        assert memory_result == "memory123"
        
        # Verify all managers were called
        full_db_manager.tenant_manager.create_tenant.assert_called_once()
        full_db_manager.conversation_manager.create_conversation.assert_called_once()
        full_db_manager.conversation_manager.add_message.assert_called_once()
        full_db_manager.memory_manager.store_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_context_integration(self, full_db_manager):
        """Test memory context integration in conversations."""
        tenant_id = str(uuid.uuid4())
        
        # Mock memory query results
        mock_memory = MagicMock()
        mock_memory.to_dict.return_value = {
            "id": "memory123",
            "content": "Previous conversation about AI",
            "similarity_score": 0.9,
            "timestamp": 1234567890
        }
        full_db_manager.memory_manager.query_memories.return_value = [mock_memory]
        
        # Query memories for context
        memories = await full_db_manager.query_memories(
            tenant_id=tenant_id,
            query_text="Tell me about AI",
            user_id="user123",
            top_k=3
        )
        
        assert len(memories) == 1
        assert memories[0]["content"] == "Previous conversation about AI"
        assert memories[0]["similarity_score"] == 0.9
        
        # Verify memory manager was called with correct parameters
        full_db_manager.memory_manager.query_memories.assert_called_once()
        call_args = full_db_manager.memory_manager.query_memories.call_args
        assert call_args[0][1].text == "Tell me about AI"
        assert call_args[0][1].user_id == "user123"
        assert call_args[0][1].top_k == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])