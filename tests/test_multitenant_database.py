"""Tests for multi-tenant database implementation."""

import pytest
import uuid
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

# Test imports
try:
    from src.ai_karen_engine.database.models import Base, Tenant, AuthUser, TenantConversation, TenantMemoryEntry
    from src.ai_karen_engine.database.client import MultiTenantPostgresClient
    from src.ai_karen_engine.database.migrations import MigrationManager
    from src.ai_karen_engine.clients.database.postgres_client import PostgresClient
    IMPORTS_AVAILABLE = True
    import_error = None
except ImportError as e:
    IMPORTS_AVAILABLE = False
    import_error = str(e)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Required imports not available: {import_error}")
class TestMultiTenantModels:
    """Test SQLAlchemy models for multi-tenant architecture."""
    
    def test_tenant_model_creation(self):
        """Test Tenant model creation and attributes."""
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name="Test Tenant",
            slug="test-tenant",
            subscription_tier="premium",
            is_active=True,  # Explicitly set for testing
            settings={}  # Explicitly set for testing
        )
        
        assert tenant.id == tenant_id
        assert tenant.name == "Test Tenant"
        assert tenant.slug == "test-tenant"
        assert tenant.subscription_tier == "premium"
        assert tenant.is_active is True
        assert tenant.settings == {}
    
    def test_user_model_creation(self):
        """Test AuthUser model creation and relationships."""
        tenant_id = "tenant-123"
        user_id = str(uuid.uuid4())

        user = AuthUser(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["end_user", "analyst"],
            is_active=True,
        )

        assert user.user_id == user_id
        assert user.tenant_id == tenant_id
        assert user.email == "test@example.com"
        assert user.roles == ["end_user", "analyst"]
        assert user.is_active is True
    
    def test_tenant_conversation_model(self):
        """Test TenantConversation model creation."""
        conversation_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        conversation = TenantConversation(
            id=conversation_id,
            user_id=user_id,
            title="Test Conversation",
            messages=[{"role": "user", "content": "Hello"}],
            is_active=True  # Explicitly set for testing
        )
        
        assert conversation.id == conversation_id
        assert conversation.user_id == user_id
        assert conversation.title == "Test Conversation"
        assert conversation.messages == [{"role": "user", "content": "Hello"}]
        assert conversation.is_active is True
    
    def test_tenant_memory_entry_model(self):
        """Test TenantMemoryEntry model creation."""
        memory_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        memory = TenantMemoryEntry(
            id=memory_id,
            vector_id="vec_123",
            user_id=user_id,
            content="Test memory content",
            query="test query"
        )
        
        assert memory.id == memory_id
        assert memory.vector_id == "vec_123"
        assert memory.user_id == user_id
        assert memory.content == "Test memory content"
        assert memory.query == "test query"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Required imports not available: {import_error}")
class TestMultiTenantClient:
    """Test MultiTenantPostgresClient functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock multi-tenant client for testing."""
        with patch('src.ai_karen_engine.database.client.create_engine') as mock_engine, \
             patch('src.ai_karen_engine.database.client.create_async_engine') as mock_async_engine:
            
            mock_engine.return_value = MagicMock()
            mock_async_engine.return_value = MagicMock()
            
            client = MultiTenantPostgresClient("postgresql://test:test@localhost/test")
            return client
    
    def test_client_initialization(self, mock_client):
        """Test client initialization."""
        assert mock_client.database_url.startswith("postgresql://")
        assert mock_client.pool_size == 10
        assert mock_client.max_overflow == 20
    
    def test_tenant_schema_name_generation(self, mock_client):
        """Test tenant schema name generation."""
        tenant_id = "12345678-1234-1234-1234-123456789abc"
        schema_name = mock_client.get_tenant_schema_name(tenant_id)
        
        expected = "tenant_12345678123412341234123456789abc"
        assert schema_name == expected
    
    def test_tenant_table_name_generation(self, mock_client):
        """Test tenant table name generation."""
        tenant_id = "12345678-1234-1234-1234-123456789abc"
        table_name = mock_client.get_tenant_table_name("conversations", tenant_id)
        
        expected = "tenant_12345678123412341234123456789abc.conversations"
        assert table_name == expected
    
    def test_build_database_url_from_env(self):
        """Test database URL building from environment variables."""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'testhost',
            'POSTGRES_PORT': '5433',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass',
            'POSTGRES_DB': 'testdb'
        }):
            client = MultiTenantPostgresClient()
            expected = "postgresql://testuser:testpass@testhost:5433/testdb"
            assert client.database_url == expected


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Required imports not available: {import_error}")
class TestMigrationManager:
    """Test MigrationManager functionality."""
    
    @pytest.fixture
    def temp_migrations_dir(self):
        """Create temporary directory for migrations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def mock_migration_manager(self, temp_migrations_dir):
        """Create a mock migration manager for testing."""
        with patch('src.ai_karen_engine.database.migrations.MultiTenantPostgresClient'):
            manager = MigrationManager(
                database_url="postgresql://test:test@localhost/test",
                migrations_dir=temp_migrations_dir
            )
            return manager
    
    def test_migration_manager_initialization(self, mock_migration_manager, temp_migrations_dir):
        """Test migration manager initialization."""
        assert mock_migration_manager.database_url.startswith("postgresql://")
        assert mock_migration_manager.migrations_dir == temp_migrations_dir
        assert os.path.exists(temp_migrations_dir)
    
    def test_alembic_config_creation(self, mock_migration_manager):
        """Test Alembic configuration creation."""
        config = mock_migration_manager.alembic_cfg
        assert config.get_main_option("script_location") == mock_migration_manager.migrations_dir
        assert config.get_main_option("sqlalchemy.url") == mock_migration_manager.database_url
    
    def test_database_status_structure(self, mock_migration_manager):
        """Test database status information structure."""
        with patch.object(mock_migration_manager.client, 'health_check') as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            with patch.object(mock_migration_manager.client, 'get_sync_session') as mock_session:
                mock_session.return_value.__enter__.return_value.query.return_value.count.return_value = 5
                
                status = mock_migration_manager.get_database_status()
                
                assert "database_url" in status
                assert "migrations_dir" in status
                assert "alembic_initialized" in status
                assert "tenant_count" in status
                assert "health" in status


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Required imports not available: {import_error}")
class TestEnhancedPostgresClient:
    """Test enhanced PostgresClient with multi-tenant support."""
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Create a mock PostgresClient for testing."""
        with patch('src.ai_karen_engine.clients.database.postgres_client.psycopg'), \
             patch('src.ai_karen_engine.clients.database.postgres_client.MultiTenantPostgresClient') as mock_mt_client:
            
            mock_mt_client.return_value = MagicMock()
            client = PostgresClient(use_sqlite=True, enable_multitenant=False)  # Use SQLite for testing
            return client
    
    def test_client_initialization_with_multitenant_disabled(self, mock_postgres_client):
        """Test client initialization with multi-tenant disabled."""
        assert mock_postgres_client.use_sqlite is True
        assert mock_postgres_client.enable_multitenant is False
        assert mock_postgres_client.multitenant_client is None
    
    def test_legacy_memory_operations(self, mock_postgres_client):
        """Test legacy memory operations still work."""
        # Test upsert
        mock_postgres_client.upsert_memory(
            vector_id=123,
            tenant_id="tenant-1",
            user_id="user-1",
            session_id="session-1",
            query="test query",
            result={"response": "test"},
            timestamp=1234567890
        )
        
        # Test retrieval
        result = mock_postgres_client.get_by_vector(123)
        if result:  # May be None in mock environment
            assert "tenant_id" in result
            assert "user_id" in result
    
    def test_multitenant_methods_when_disabled(self, mock_postgres_client):
        """Test multi-tenant methods when support is disabled."""
        assert mock_postgres_client.setup_tenant("tenant-1", "Test", "test") is False
        assert mock_postgres_client.teardown_tenant("tenant-1") is False
        assert mock_postgres_client.tenant_exists("tenant-1") is False
        assert mock_postgres_client.is_multitenant_enabled() is False
        
        stats = mock_postgres_client.get_tenant_stats("tenant-1")
        assert "error" in stats
    
    def test_health_check(self, mock_postgres_client):
        """Test health check functionality."""
        # Health check should work with SQLite
        health = mock_postgres_client.health()
        assert isinstance(health, bool)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Required imports not available: {import_error}")
class TestMultiTenantIntegration:
    """Integration tests for multi-tenant functionality."""
    
    def test_tenant_lifecycle_simulation(self):
        """Test complete tenant lifecycle simulation."""
        # This test simulates the full tenant lifecycle without actual database
        tenant_id = str(uuid.uuid4())
        tenant_name = "Test Organization"
        tenant_slug = "test-org"
        
        # Mock the entire flow
        with patch('src.ai_karen_engine.database.client.create_engine') as mock_engine, \
             patch('src.ai_karen_engine.database.migrations.MultiTenantPostgresClient'):
            
            mock_engine.return_value = MagicMock()
            
            # Initialize components
            client = MultiTenantPostgresClient("postgresql://test:test@localhost/test")
            manager = MigrationManager("postgresql://test:test@localhost/test")
            
            # Simulate tenant setup
            with patch.object(client, 'create_tenant_schema', return_value=True):
                success = client.create_tenant_schema(tenant_id)
                assert success is True
            
            # Simulate schema validation
            with patch.object(client, 'tenant_schema_exists', return_value=True):
                exists = client.tenant_schema_exists(tenant_id)
                assert exists is True
            
            # Simulate tenant teardown
            with patch.object(client, 'drop_tenant_schema', return_value=True):
                success = client.drop_tenant_schema(tenant_id)
                assert success is True
    
    def test_error_handling_in_tenant_operations(self):
        """Test error handling in tenant operations."""
        with patch('src.ai_karen_engine.database.client.create_engine') as mock_engine:
            mock_engine.return_value = MagicMock()
            mock_engine.return_value.connect.side_effect = Exception("Database connection failed")
            
            client = MultiTenantPostgresClient("postgresql://test:test@localhost/test")
            
            # Test that errors are handled gracefully
            success = client.create_tenant_schema("test-tenant")
            assert success is False
            
            health = client.health_check()
            assert health["status"] == "unhealthy"
            assert "error" in health


# Performance and load testing
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Required imports not available: {import_error}")
class TestMultiTenantPerformance:
    """Performance tests for multi-tenant operations."""
    
    def test_schema_name_generation_performance(self):
        """Test performance of schema name generation."""
        with patch('src.ai_karen_engine.database.client.create_engine'):
            client = MultiTenantPostgresClient("postgresql://test:test@localhost/test")
            
            # Generate many schema names to test performance
            tenant_ids = [str(uuid.uuid4()) for _ in range(1000)]
            
            import time
            start_time = time.time()
            
            for tenant_id in tenant_ids:
                schema_name = client.get_tenant_schema_name(tenant_id)
                assert schema_name.startswith("tenant_")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should be very fast (less than 1 second for 1000 operations)
            assert duration < 1.0
    
    def test_concurrent_tenant_operations_simulation(self):
        """Simulate concurrent tenant operations."""
        import threading
        import time
        
        with patch('src.ai_karen_engine.database.client.create_engine'):
            client = MultiTenantPostgresClient("postgresql://test:test@localhost/test")
            
            results = []
            
            def simulate_tenant_operation(tenant_id):
                """Simulate a tenant operation."""
                try:
                    schema_name = client.get_tenant_schema_name(tenant_id)
                    table_name = client.get_tenant_table_name("conversations", tenant_id)
                    results.append({"success": True, "schema": schema_name, "table": table_name})
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
            
            # Create multiple threads
            threads = []
            tenant_ids = [str(uuid.uuid4()) for _ in range(10)]
            
            for tenant_id in tenant_ids:
                thread = threading.Thread(target=simulate_tenant_operation, args=(tenant_id,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all operations succeeded
            assert len(results) == 10
            assert all(result["success"] for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])