"""
Tests for ExtensionDataManager.

This test suite verifies that the ExtensionDataManager meets all requirements
for task 4: Extension Data Management.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List

from ai_karen_engine.extensions.data_manager import (
    ExtensionDataManager,
    DataSchema,
    QueryFilter,
    DataAccessLevel,
    StorageType
)


class TestExtensionDataManager:
    """Test ExtensionDataManager functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield f"sqlite:///{db_path}"
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass
    
    @pytest.fixture
    def data_manager(self, temp_db_path):
        """Create ExtensionDataManager instance."""
        return ExtensionDataManager(
            extension_name="test-extension",
            database_url=temp_db_path,
            storage_type=StorageType.SQLITE
        )
    
    @pytest.fixture
    def memory_data_manager(self):
        """Create in-memory ExtensionDataManager instance."""
        return ExtensionDataManager(
            extension_name="test-extension",
            storage_type=StorageType.MEMORY
        )
    
    @pytest.mark.asyncio
    async def test_tenant_isolated_storage(self, data_manager):
        """Test requirement 4.1: Tenant-isolated database schemas."""
        # Create table for tenant A
        schema = DataSchema(
            table_name="user_data",
            columns={"name": "STRING", "email": "STRING"}
        )
        
        success_a = await data_manager.create_table("user_data", schema, "tenant_a")
        success_b = await data_manager.create_table("user_data", schema, "tenant_b")
        
        assert success_a is True
        assert success_b is True
        
        # Insert data for different tenants
        record_a = await data_manager.insert(
            "user_data",
            {"name": "Alice", "email": "alice@tenant-a.com"},
            "tenant_a",
            "user_1"
        )
        
        record_b = await data_manager.insert(
            "user_data",
            {"name": "Bob", "email": "bob@tenant-b.com"},
            "tenant_b",
            "user_2"
        )
        
        assert record_a is not None
        assert record_b is not None
        
        # Verify tenant isolation
        tenant_a_data = await data_manager.query("user_data", tenant_id="tenant_a")
        tenant_b_data = await data_manager.query("user_data", tenant_id="tenant_b")
        
        assert len(tenant_a_data) == 1
        assert len(tenant_b_data) == 1
        assert tenant_a_data[0]["name"] == "Alice"
        assert tenant_b_data[0]["name"] == "Bob"
        
        # Verify cross-tenant data is not accessible
        assert tenant_a_data[0]["email"] != "bob@tenant-b.com"
        assert tenant_b_data[0]["email"] != "alice@tenant-a.com"
    
    @pytest.mark.asyncio
    async def test_automatic_tenant_user_segregation(self, data_manager):
        """Test requirement 4.2: Automatic tenant and user context segregation."""
        schema = DataSchema(
            table_name="documents",
            columns={"title": "STRING", "content": "TEXT"}
        )
        
        await data_manager.create_table("documents", schema, "tenant_1")
        
        # Insert documents for different users in same tenant
        doc1 = await data_manager.insert(
            "documents",
            {"title": "User 1 Doc", "content": "Private content"},
            "tenant_1",
            "user_1"
        )
        
        doc2 = await data_manager.insert(
            "documents",
            {"title": "User 2 Doc", "content": "Other private content"},
            "tenant_1",
            "user_2"
        )
        
        # Query with user filtering
        user1_docs = await data_manager.query("documents", tenant_id="tenant_1", user_id="user_1")
        user2_docs = await data_manager.query("documents", tenant_id="tenant_1", user_id="user_2")
        
        assert len(user1_docs) == 1
        assert len(user2_docs) == 1
        assert user1_docs[0]["title"] == "User 1 Doc"
        assert user2_docs[0]["title"] == "User 2 Doc"
        
        # Verify user isolation
        assert user1_docs[0]["user_id"] == "user_1"
        assert user2_docs[0]["user_id"] == "user_2"
    
    @pytest.mark.asyncio
    async def test_sql_and_nosql_storage_options(self, data_manager):
        """Test requirement 4.3: Both SQL and NoSQL storage options."""
        # Test SQL storage (relational)
        sql_schema = DataSchema(
            table_name="products",
            columns={"name": "STRING", "price": "INTEGER", "category": "STRING"}
        )
        
        await data_manager.create_table("products", sql_schema, "tenant_1")
        
        product_id = await data_manager.insert(
            "products",
            {"name": "Laptop", "price": 1000, "category": "Electronics"},
            "tenant_1",
            "user_1"
        )
        
        assert product_id is not None
        
        # Test NoSQL storage (document-based)
        await data_manager.create_document_collection("orders", "tenant_1")
        
        order_success = await data_manager.insert_document(
            "orders",
            "order_123",
            {
                "customer": {"name": "John Doe", "email": "john@example.com"},
                "items": [
                    {"product": "Laptop", "quantity": 1, "price": 1000}
                ],
                "total": 1000,
                "status": "pending"
            },
            "tenant_1",
            "user_1",
            tags=["electronics", "high-value"]
        )
        
        assert order_success is True
        
        # Query both storage types
        products = await data_manager.query("products", tenant_id="tenant_1")
        orders = await data_manager.find_documents("orders", "tenant_1")
        
        assert len(products) == 1
        assert len(orders) == 1
        assert products[0]["name"] == "Laptop"
        assert orders[0]["document_data"]["customer"]["name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_configuration_storage_and_retrieval(self, data_manager):
        """Test requirement 4.4: Persistent settings storage with validation."""
        # Set various configuration types
        await data_manager.set_config("api_key", "secret-key-123", "tenant_1", "admin_user")
        await data_manager.set_config("max_requests", 1000, "tenant_1", "admin_user")
        await data_manager.set_config("features", {"ai_enabled": True, "analytics": False}, "tenant_1", "admin_user")
        
        # Retrieve configurations
        api_key = await data_manager.get_config("api_key", "tenant_1")
        max_requests = await data_manager.get_config("max_requests", "tenant_1")
        features = await data_manager.get_config("features", "tenant_1")
        missing_config = await data_manager.get_config("missing_key", "tenant_1", "default_value")
        
        assert api_key == "secret-key-123"
        assert max_requests == 1000
        assert features == {"ai_enabled": True, "analytics": False}
        assert missing_config == "default_value"
        
        # Test configuration update
        await data_manager.set_config("max_requests", 2000, "tenant_1", "admin_user")
        updated_max = await data_manager.get_config("max_requests", "tenant_1")
        assert updated_max == 2000
        
        # Test tenant isolation for configs
        await data_manager.set_config("api_key", "different-key", "tenant_2", "admin_user")
        tenant2_key = await data_manager.get_config("api_key", "tenant_2")
        tenant1_key = await data_manager.get_config("api_key", "tenant_1")
        
        assert tenant2_key == "different-key"
        assert tenant1_key == "secret-key-123"  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_privacy_and_compliance_features(self, data_manager):
        """Test requirement 4.5: Privacy and compliance requirements."""
        # Create table with user data
        schema = DataSchema(
            table_name="user_profiles",
            columns={"name": "STRING", "email": "STRING", "phone": "STRING"}
        )
        
        await data_manager.create_table("user_profiles", schema, "tenant_1")
        
        # Insert user data
        await data_manager.insert(
            "user_profiles",
            {"name": "Jane Doe", "email": "jane@example.com", "phone": "555-1234"},
            "tenant_1",
            "user_1"
        )
        
        # Set data retention policy
        retention_success = await data_manager.set_data_retention_policy(
            "user_profiles",
            "tenant_1",
            retention_days=30,
            auto_delete=True
        )
        
        assert retention_success is True
        
        # Test encryption marking (placeholder implementation)
        encryption_success = await data_manager.encrypt_sensitive_field(
            "user_profiles",
            "email",
            "tenant_1"
        )
        
        assert encryption_success is True
        
        # Verify encryption config was stored
        encryption_config = await data_manager.get_config(
            "encryption_user_profiles_email",
            "tenant_1"
        )
        
        assert encryption_config is not None
        assert encryption_config["encryption_enabled"] is True
        assert encryption_config["field_name"] == "email"
    
    @pytest.mark.asyncio
    async def test_document_querying_and_filtering(self, data_manager):
        """Test NoSQL document querying capabilities."""
        await data_manager.create_document_collection("products", "tenant_1")
        
        # Insert test documents
        await data_manager.insert_document(
            "products",
            "prod_1",
            {"name": "Laptop", "category": "Electronics", "price": 1000, "in_stock": True},
            "tenant_1",
            "user_1",
            tags=["electronics", "computers"]
        )
        
        await data_manager.insert_document(
            "products",
            "prod_2",
            {"name": "Book", "category": "Education", "price": 25, "in_stock": True},
            "tenant_1",
            "user_1",
            tags=["books", "education"]
        )
        
        await data_manager.insert_document(
            "products",
            "prod_3",
            {"name": "Phone", "category": "Electronics", "price": 800, "in_stock": False},
            "tenant_1",
            "user_1",
            tags=["electronics", "mobile"]
        )
        
        # Test basic query
        all_products = await data_manager.find_documents("products", "tenant_1")
        assert len(all_products) == 3
        
        # Test query with filters
        electronics = await data_manager.find_documents(
            "products",
            "tenant_1",
            query={"category": "Electronics"}
        )
        assert len(electronics) == 2
        
        # Test tag filtering
        computers = await data_manager.find_documents(
            "products",
            "tenant_1",
            tags=["computers"]
        )
        assert len(computers) == 1
        assert computers[0]["document_data"]["name"] == "Laptop"
        
        # Test limit
        limited = await data_manager.find_documents(
            "products",
            "tenant_1",
            limit=2
        )
        assert len(limited) == 2
    
    @pytest.mark.asyncio
    async def test_memory_storage_fallback(self, memory_data_manager):
        """Test in-memory storage when SQLAlchemy is not available."""
        schema = DataSchema(
            table_name="test_data",
            columns={"key": "STRING", "value": "STRING"}
        )
        
        # Test table creation
        success = await memory_data_manager.create_table("test_data", schema, "tenant_1")
        assert success is True
        
        # Test data insertion
        record_id = await memory_data_manager.insert(
            "test_data",
            {"key": "test_key", "value": "test_value"},
            "tenant_1",
            "user_1"
        )
        assert record_id is not None
        
        # Test data querying
        results = await memory_data_manager.query("test_data", tenant_id="tenant_1")
        assert len(results) == 1
        assert results[0]["key"] == "test_key"
        assert results[0]["value"] == "test_value"
        
        # Test configuration in memory
        await memory_data_manager.set_config("test_config", "test_value", "tenant_1")
        config_value = await memory_data_manager.get_config("test_config", "tenant_1")
        assert config_value == "test_value"
    
    @pytest.mark.asyncio
    async def test_data_access_controls(self, data_manager):
        """Test data access controls and user permissions."""
        schema = DataSchema(
            table_name="sensitive_data",
            columns={"data": "STRING", "classification": "STRING"}
        )
        
        await data_manager.create_table("sensitive_data", schema, "tenant_1")
        
        # Insert data for different users
        record1 = await data_manager.insert(
            "sensitive_data",
            {"data": "User 1 sensitive info", "classification": "confidential"},
            "tenant_1",
            "user_1"
        )
        
        record2 = await data_manager.insert(
            "sensitive_data",
            {"data": "User 2 sensitive info", "classification": "confidential"},
            "tenant_1",
            "user_2"
        )
        
        # Test update with user access control
        update_success = await data_manager.update(
            "sensitive_data",
            record1,
            {"classification": "public"},
            "tenant_1",
            "user_1"  # Same user who created the record
        )
        assert update_success is True
        
        # Test update with wrong user (should fail)
        update_fail = await data_manager.update(
            "sensitive_data",
            record1,
            {"classification": "secret"},
            "tenant_1",
            "user_2"  # Different user
        )
        assert update_fail is False
        
        # Test delete with user access control
        delete_success = await data_manager.delete(
            "sensitive_data",
            record2,
            "tenant_1",
            "user_2"  # Same user who created the record
        )
        assert delete_success is True
        
        # Verify record was deleted
        remaining_records = await data_manager.query("sensitive_data", tenant_id="tenant_1")
        assert len(remaining_records) == 1
        assert remaining_records[0]["id"] == record1
    
    def test_table_name_sanitization(self, data_manager):
        """Test table name sanitization for security."""
        # Test various problematic characters
        sanitized = data_manager._sanitize_name("test-extension@#$%^&*()")
        assert sanitized == "test_extension"
        
        sanitized2 = data_manager._sanitize_name("Test Extension With Spaces")
        assert sanitized2 == "test_extension_with_spaces"
        
        sanitized3 = data_manager._sanitize_name("extension__with__multiple__underscores")
        assert sanitized3 == "extension_with_multiple_underscores"
    
    def test_table_info_reporting(self, data_manager):
        """Test table information reporting."""
        info = data_manager.get_table_info()
        
        assert info["extension_name"] == "test-extension"
        assert info["table_prefix"] == "ext_test_extension_"
        assert info["storage_type"] == "sqlite"
        assert "tables" in info
        assert "document_collections" in info
        assert "retention_policies" in info
    
    @pytest.mark.asyncio
    async def test_constructor_backward_compatibility(self, temp_db_path):
        """Test backward compatibility with old constructor signature."""
        # Test old style constructor
        old_style = ExtensionDataManager(
            "test-extension",
            database_url=temp_db_path,
            storage_type=StorageType.SQLITE
        )
        
        assert old_style.extension_name == "test-extension"
        assert old_style.db_session is None
        
        # Test new style constructor
        mock_session = "mock_db_session"
        new_style = ExtensionDataManager(
            mock_session,
            "test-extension",
            database_url=temp_db_path,
            storage_type=StorageType.SQLITE
        )
        
        assert new_style.extension_name == "test-extension"
        assert new_style.db_session == mock_session


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])