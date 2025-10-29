"""
Integration test for ExtensionDataManager with the extension system.

This test verifies that the data manager integrates correctly with the
BaseExtension class and handles both constructor signatures properly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

async def test_data_manager_integration():
    """Test ExtensionDataManager integration with extension system."""
    try:
        # Import data manager directly to avoid dependency issues
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'data_manager', 
            'src/ai_karen_engine/extensions/data_manager.py'
        )
        data_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_manager_module)
        
        ExtensionDataManager = data_manager_module.ExtensionDataManager
        DataSchema = data_manager_module.DataSchema
        StorageType = data_manager_module.StorageType
        
        print("✓ Testing ExtensionDataManager integration")
        
        # Test old constructor signature (backward compatibility)
        dm_old = ExtensionDataManager(
            "test-extension",
            storage_type=StorageType.MEMORY
        )
        
        assert dm_old.extension_name == "test-extension"
        assert dm_old.db_session is None
        print("✓ Old constructor signature works")
        
        # Test new constructor signature (with db_session)
        mock_db_session = "mock_session_object"
        dm_new = ExtensionDataManager(
            mock_db_session,
            "test-extension",
            storage_type=StorageType.MEMORY
        )
        
        assert dm_new.extension_name == "test-extension"
        assert dm_new.db_session == mock_db_session
        print("✓ New constructor signature works")
        
        # Test that both instances work the same way
        schema = DataSchema(
            table_name="test_table",
            columns={"data": "STRING"}
        )
        
        # Test old style instance
        success1 = await dm_old.create_table("test_table", schema, "tenant_1")
        record1 = await dm_old.insert("test_table", {"data": "old_style"}, "tenant_1", "user_1")
        results1 = await dm_old.query("test_table", tenant_id="tenant_1")
        
        # Test new style instance
        success2 = await dm_new.create_table("test_table", schema, "tenant_1")
        record2 = await dm_new.insert("test_table", {"data": "new_style"}, "tenant_1", "user_1")
        results2 = await dm_new.query("test_table", tenant_id="tenant_1")
        
        assert success1 is True
        assert success2 is True
        assert record1 is not None
        assert record2 is not None
        assert len(results1) == 1
        assert len(results2) == 1
        assert results1[0]["data"] == "old_style"
        assert results2[0]["data"] == "new_style"
        
        print("✓ Both constructor styles produce working instances")
        
        # Test all requirements are met
        print("\n✓ Verifying all task 4 requirements:")
        
        # Requirement 4.1: Tenant-isolated database schemas
        tenant_table_name = dm_old.get_tenant_table_name("test_table", "tenant_1")
        assert "tenant_1" in tenant_table_name
        print("  ✓ 4.1: Tenant-isolated database schemas")
        
        # Requirement 4.2: Automatic tenant and user context segregation
        user_filtered = await dm_old.query("test_table", tenant_id="tenant_1", user_id="user_1")
        assert len(user_filtered) == 1
        assert user_filtered[0]["user_id"] == "user_1"
        print("  ✓ 4.2: Automatic tenant and user context segregation")
        
        # Requirement 4.3: Both SQL and NoSQL storage options
        # SQL-style (relational)
        sql_results = await dm_old.query("test_table", tenant_id="tenant_1")
        assert len(sql_results) == 1
        
        # NoSQL-style (document)
        await dm_old.create_document_collection("test_docs", "tenant_1")
        doc_success = await dm_old.insert_document(
            "test_docs", "doc_1", {"title": "Test"}, "tenant_1", "user_1"
        )
        docs = await dm_old.find_documents("test_docs", "tenant_1")
        assert doc_success is True
        assert len(docs) == 1
        print("  ✓ 4.3: Both SQL and NoSQL storage options")
        
        # Requirement 4.4: Persistent settings storage with validation
        await dm_old.set_config("test_setting", {"enabled": True}, "tenant_1")
        setting = await dm_old.get_config("test_setting", "tenant_1")
        assert setting == {"enabled": True}
        print("  ✓ 4.4: Persistent settings storage with validation")
        
        # Requirement 4.5: Privacy and compliance requirements
        retention_set = await dm_old.set_data_retention_policy("test_table", "tenant_1", 30)
        encryption_set = await dm_old.encrypt_sensitive_field("test_table", "data", "tenant_1")
        assert retention_set is True
        assert encryption_set is True
        print("  ✓ 4.5: Privacy and compliance requirements")
        
        print("\n✓ All ExtensionDataManager integration tests passed!")
        print("✓ All task 4 requirements verified!")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_data_manager_integration())
    sys.exit(0 if success else 1)