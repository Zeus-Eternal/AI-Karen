"""
Tests for the extension system including data management.

This module tests the extension data management capabilities
including tenant isolation, access controls, and configuration management.
"""

import asyncio
import pytest
import tempfile
import os
from typing import Dict, Any
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.extensions.data_manager import (
    ExtensionDataManager, DataSchema, QueryFilter, DataRecord,
    DataAccessLevel, StorageType
)


class TestExtensionDataManager:
    """Test the ExtensionDataManager class."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
    
    @pytest.fixture
    def data_manager(self, temp_db_path):
        """Create an ExtensionDataManager instance."""
        return ExtensionDataManager(
            extension_name="test_extension",
            database_url=f"sqlite:///{temp_db_path}",
            storage_type=StorageType.SQLITE
        )
    
    @pytest.fixture
    def memory_data_manager(self):
        """Create an in-memory ExtensionDataManager instance."""
        return ExtensionDataManager(
            extension_name="test_extension",
            storage_type=StorageType.MEMORY
        )
    
    def test_initialization(self, data_manager):
        """Test data manager initialization."""
        assert data_manager.extension_name == "test_extension"
        assert data_manager.table_prefix == "ext_test_extension_"
        assert data_manager.storage_type == StorageType.SQLITE
    
    def test_name_sanitization(self, data_manager):
        """Test name sanitization for database safety."""
        # Test various problematic names
        assert data_manager._sanitize_name("test-extension") == "test_extension"
        assert data_manager._sanitize_name("test@extension!") == "test_extension"
        assert data_manager._sanitize_name("test__extension") == "test_extension"
        assert data_manager._sanitize_name("123test") == "123test"
    
    def test_tenant_table_name_generation(self, data_manager):
        """Test tenant-specific table name generation."""
        table_name = data_manager.get_tenant_table_name("users", "tenant123")
        expected = "ext_test_extension_users_tenant123"
        assert table_name == expected
        
        # Test with special characters in tenant ID
        table_name = data_manager.get_tenant_table_name("data", "tenant-abc@123")
        expected = "ext_test_extension_data_tenant_abc_123"
        assert table_name == expected
    
    @pytest.mark.asyncio
    async def test_create_table_memory(self, memory_data_manager):
        """Test table creation with in-memory storage."""
        schema = DataSchema(
            table_name="test_table",
            columns={
                "name": "STRING",
                "age": "INTEGER",
                "active": "BOOLEAN"
            }
        )
        
        result = await memory_data_manager.create_table("test_table", schema, "tenant1")
        assert result is True
        
        # Verify table was created in memory storage
        table_name = memory_data_manager.get_tenant_table_name("test_table", "tenant1")
        assert table_name in memory_data_manager._memory_storage
    
    @pytest.mark.asyncio
    async def test_insert_and_query_memory(self, memory_data_manager):
        """Test data insertion and querying with in-memory storage."""
        # Create table
        schema = DataSchema(
            table_name="users",
            columns={"name": "STRING", "email": "STRING", "age": "INTEGER"}
        )
        await memory_data_manager.create_table("users", schema, "tenant1")
        
        # Insert data
        record_id = await memory_data_manager.insert(
            "users",
            {"name": "John Doe", "email": "john@example.com", "age": 30},
            "tenant1",
            "user1"
        )
        assert record_id == 1
        
        # Insert another record
        record_id2 = await memory_data_manager.insert(
            "users",
            {"name": "Jane Smith", "email": "jane@example.com", "age": 25},
            "tenant1",
            "user2"
        )
        assert record_id2 == 2
        
        # Query all records
        results = await memory_data_manager.query("users", tenant_id="tenant1")
        assert len(results) == 2
        assert results[0]["name"] == "John Doe"
        assert results[1]["name"] == "Jane Smith"
        
        # Query with filter
        filters = [QueryFilter("age", ">", 28)]
        results = await memory_data_manager.query("users", filters, "tenant1")
        assert len(results) == 1
        assert results[0]["name"] == "John Doe"
        
        # Query with user filter
        results = await memory_data_manager.query("users", tenant_id="tenant1", user_id="user1")
        assert len(results) == 1
        assert results[0]["name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_tenant_isolation_memory(self, memory_data_manager):
        """Test tenant isolation with in-memory storage."""
        schema = DataSchema(
            table_name="data",
            columns={"value": "STRING"}
        )
        
        # Create tables for different tenants
        await memory_data_manager.create_table("data", schema, "tenant1")
        await memory_data_manager.create_table("data", schema, "tenant2")
        
        # Insert data for tenant1
        await memory_data_manager.insert("data", {"value": "tenant1_data"}, "tenant1")
        
        # Insert data for tenant2
        await memory_data_manager.insert("data", {"value": "tenant2_data"}, "tenant2")
        
        # Query tenant1 data
        results1 = await memory_data_manager.query("data", tenant_id="tenant1")
        assert len(results1) == 1
        assert results1[0]["value"] == "tenant1_data"
        
        # Query tenant2 data
        results2 = await memory_data_manager.query("data", tenant_id="tenant2")
        assert len(results2) == 1
        assert results2[0]["value"] == "tenant2_data"
        
        # Verify isolation - tenant1 cannot see tenant2 data
        assert results1[0]["value"] != results2[0]["value"]
    
    @pytest.mark.asyncio
    async def test_update_record_memory(self, memory_data_manager):
        """Test record updating with in-memory storage."""
        schema = DataSchema(
            table_name="profiles",
            columns={"name": "STRING", "status": "STRING"}
        )
        await memory_data_manager.create_table("profiles", schema, "tenant1")
        
        # Insert record
        record_id = await memory_data_manager.insert(
            "profiles",
            {"name": "Test User", "status": "active"},
            "tenant1",
            "user1"
        )
        
        # Update record
        success = await memory_data_manager.update(
            "profiles",
            record_id,
            {"status": "inactive"},
            "tenant1",
            "user1"
        )
        assert success is True
        
        # Verify update
        results = await memory_data_manager.query("profiles", tenant_id="tenant1")
        assert len(results) == 1
        assert results[0]["status"] == "inactive"
        assert results[0]["name"] == "Test User"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_record_memory(self, memory_data_manager):
        """Test record deletion with in-memory storage."""
        schema = DataSchema(
            table_name="items",
            columns={"name": "STRING"}
        )
        await memory_data_manager.create_table("items", schema, "tenant1")
        
        # Insert records
        record_id1 = await memory_data_manager.insert("items", {"name": "Item 1"}, "tenant1")
        record_id2 = await memory_data_manager.insert("items", {"name": "Item 2"}, "tenant1")
        
        # Delete first record
        success = await memory_data_manager.delete("items", record_id1, "tenant1")
        assert success is True
        
        # Verify deletion
        results = await memory_data_manager.query("items", tenant_id="tenant1")
        assert len(results) == 1
        assert results[0]["name"] == "Item 2"
    
    @pytest.mark.asyncio
    async def test_configuration_management_memory(self, memory_data_manager):
        """Test configuration storage and retrieval."""
        # Set configuration
        success = await memory_data_manager.set_config(
            "api_key",
            "secret123",
            "tenant1",
            "admin1"
        )
        assert success is True
        
        # Get configuration
        value = await memory_data_manager.get_config("api_key", "tenant1")
        assert value == "secret123"
        
        # Set complex configuration
        complex_config = {
            "settings": {
                "enabled": True,
                "max_retries": 3,
                "timeout": 30.0
            }
        }
        success = await memory_data_manager.set_config(
            "app_settings",
            complex_config,
            "tenant1"
        )
        assert success is True
        
        # Get complex configuration
        retrieved_config = await memory_data_manager.get_config("app_settings", "tenant1")
        assert retrieved_config == complex_config
        
        # Test default value
        default_value = await memory_data_manager.get_config(
            "nonexistent_key",
            "tenant1",
            "default_value"
        )
        assert default_value == "default_value"
    
    @pytest.mark.asyncio
    async def test_query_filters_memory(self, memory_data_manager):
        """Test various query filters with in-memory storage."""
        schema = DataSchema(
            table_name="products",
            columns={
                "name": "STRING",
                "price": "INTEGER",
                "category": "STRING",
                "in_stock": "BOOLEAN"
            }
        )
        await memory_data_manager.create_table("products", schema, "tenant1")
        
        # Insert test data
        products = [
            {"name": "Laptop", "price": 1000, "category": "electronics", "in_stock": True},
            {"name": "Phone", "price": 500, "category": "electronics", "in_stock": False},
            {"name": "Book", "price": 20, "category": "books", "in_stock": True},
            {"name": "Tablet", "price": 300, "category": "electronics", "in_stock": True}
        ]
        
        for product in products:
            await memory_data_manager.insert("products", product, "tenant1")
        
        # Test equality filter
        filters = [QueryFilter("category", "=", "electronics")]
        results = await memory_data_manager.query("products", filters, "tenant1")
        assert len(results) == 3
        
        # Test greater than filter
        filters = [QueryFilter("price", ">", 400)]
        results = await memory_data_manager.query("products", filters, "tenant1")
        assert len(results) == 2  # Laptop and Phone
        
        # Test multiple filters
        filters = [
            QueryFilter("category", "=", "electronics"),
            QueryFilter("in_stock", "=", True)
        ]
        results = await memory_data_manager.query("products", filters, "tenant1")
        assert len(results) == 2  # Laptop and Tablet
        
        # Test IN filter
        filters = [QueryFilter("name", "IN", ["Laptop", "Book"])]
        results = await memory_data_manager.query("products", filters, "tenant1")
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_query_pagination_memory(self, memory_data_manager):
        """Test query pagination with in-memory storage."""
        schema = DataSchema(
            table_name="items",
            columns={"name": "STRING", "order": "INTEGER"}
        )
        await memory_data_manager.create_table("items", schema, "tenant1")
        
        # Insert test data
        for i in range(10):
            await memory_data_manager.insert(
                "items",
                {"name": f"Item {i}", "order": i},
                "tenant1"
            )
        
        # Test limit
        results = await memory_data_manager.query("items", tenant_id="tenant1", limit=5)
        assert len(results) == 5
        
        # Test offset
        results = await memory_data_manager.query("items", tenant_id="tenant1", offset=5)
        assert len(results) == 5
        
        # Test limit and offset
        results = await memory_data_manager.query(
            "items",
            tenant_id="tenant1",
            limit=3,
            offset=2
        )
        assert len(results) == 3
        
        # Test ordering
        results = await memory_data_manager.query(
            "items",
            tenant_id="tenant1",
            order_by="-order"  # Descending
        )
        assert results[0]["order"] == 9  # Highest order first
        assert results[-1]["order"] == 0  # Lowest order last
    
    @pytest.mark.asyncio
    async def test_access_control_memory(self, memory_data_manager):
        """Test user access control with in-memory storage."""
        schema = DataSchema(
            table_name="private_data",
            columns={"content": "STRING"}
        )
        await memory_data_manager.create_table("private_data", schema, "tenant1")
        
        # Insert data for user1
        record_id1 = await memory_data_manager.insert(
            "private_data",
            {"content": "user1_private"},
            "tenant1",
            "user1"
        )
        
        # Insert data for user2
        record_id2 = await memory_data_manager.insert(
            "private_data",
            {"content": "user2_private"},
            "tenant1",
            "user2"
        )
        
        # User1 should only see their own data
        results = await memory_data_manager.query(
            "private_data",
            tenant_id="tenant1",
            user_id="user1"
        )
        assert len(results) == 1
        assert results[0]["content"] == "user1_private"
        
        # User2 should only see their own data
        results = await memory_data_manager.query(
            "private_data",
            tenant_id="tenant1",
            user_id="user2"
        )
        assert len(results) == 1
        assert results[0]["content"] == "user2_private"
        
        # User1 should not be able to update user2's data
        success = await memory_data_manager.update(
            "private_data",
            record_id2,
            {"content": "hacked"},
            "tenant1",
            "user1"  # Wrong user
        )
        assert success is False
        
        # User1 should not be able to delete user2's data
        success = await memory_data_manager.delete(
            "private_data",
            record_id2,
            "tenant1",
            "user1"  # Wrong user
        )
        assert success is False
    
    def test_table_info_memory(self, memory_data_manager):
        """Test getting table information."""
        info = memory_data_manager.get_table_info()
        
        assert info["extension_name"] == "test_extension"
        assert info["table_prefix"] == "ext_test_extension_"
        assert info["storage_type"] == "memory"
        assert isinstance(info["tables"], list)
    
    @pytest.mark.asyncio
    async def test_configuration_update_memory(self, memory_data_manager):
        """Test configuration updates (overwriting existing values)."""
        # Set initial config
        await memory_data_manager.set_config("setting1", "value1", "tenant1")
        
        # Verify initial value
        value = await memory_data_manager.get_config("setting1", "tenant1")
        assert value == "value1"
        
        # Update config
        await memory_data_manager.set_config("setting1", "updated_value", "tenant1")
        
        # Verify updated value
        value = await memory_data_manager.get_config("setting1", "tenant1")
        assert value == "updated_value"
    
    @pytest.mark.asyncio
    async def test_cross_tenant_admin_query_memory(self, memory_data_manager):
        """Test admin queries across multiple tenants."""
        schema = DataSchema(
            table_name="logs",
            columns={"message": "STRING", "level": "STRING"}
        )
        
        # Create tables for multiple tenants
        await memory_data_manager.create_table("logs", schema, "tenant1")
        await memory_data_manager.create_table("logs", schema, "tenant2")
        
        # Insert data for different tenants
        await memory_data_manager.insert(
            "logs",
            {"message": "tenant1 log", "level": "info"},
            "tenant1"
        )
        await memory_data_manager.insert(
            "logs",
            {"message": "tenant2 log", "level": "error"},
            "tenant2"
        )
        
        # Admin query across all tenants (no tenant_id specified)
        results = await memory_data_manager.query("logs")
        assert len(results) == 2
        
        # Verify both tenant records are included
        messages = [r["message"] for r in results]
        assert "tenant1 log" in messages
        assert "tenant2 log" in messages


# Integration test with SQLAlchemy (if available)
@pytest.mark.skipif(
    not hasattr(ExtensionDataManager, 'engine') or 
    ExtensionDataManager.__init__.__code__.co_varnames[1] == 'SQLALCHEMY_AVAILABLE',
    reason="SQLAlchemy not available"
)
class TestExtensionDataManagerSQL:
    """Test ExtensionDataManager with actual SQL database."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
    
    @pytest.fixture
    def sql_data_manager(self, temp_db_path):
        """Create an ExtensionDataManager with SQLite."""
        return ExtensionDataManager(
            extension_name="sql_test",
            database_url=f"sqlite:///{temp_db_path}",
            storage_type=StorageType.SQLITE
        )
    
    @pytest.mark.asyncio
    async def test_sql_basic_operations(self, sql_data_manager):
        """Test basic SQL operations if SQLAlchemy is available."""
        # This test will only run if SQLAlchemy is properly installed
        schema = DataSchema(
            table_name="test_table",
            columns={"name": "STRING", "value": "INTEGER"}
        )
        
        # Create table
        result = await sql_data_manager.create_table("test_table", schema, "tenant1")
        assert result is True
        
        # Insert data
        record_id = await sql_data_manager.insert(
            "test_table",
            {"name": "test", "value": 42},
            "tenant1"
        )
        assert record_id is not None
        
        # Query data
        results = await sql_data_manager.query("test_table", tenant_id="tenant1")
        assert len(results) >= 1
        assert results[0]["name"] == "test"
        assert results[0]["value"] == 42


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])