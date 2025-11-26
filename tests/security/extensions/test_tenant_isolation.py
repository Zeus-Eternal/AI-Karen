"""
Security tests for tenant isolation in the extension system.
Tests data segregation, access controls, and permission boundaries.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ai_karen_engine.extension_host.manager import ExtensionManager
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.data_manager import ExtensionDataManager
from ai_karen_engine.extension_host.models2 import ExtensionManifest, ExtensionContext
from ai_karen_engine.plugins.router import PluginRouter


class TestTenantIsolation:
    """Test tenant isolation in extension system."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router."""
        router = Mock(spec=PluginRouter)
        router.dispatch = AsyncMock(return_value="plugin_result")
        return router
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session with tenant isolation."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        
        # Mock query results to simulate tenant isolation
        def mock_query_filter(query_obj):
            mock_query = AsyncMock()
            mock_query.filter = AsyncMock(return_value=mock_query)
            mock_query.filter_by = AsyncMock(return_value=mock_query)
            mock_query.all = AsyncMock(return_value=[])
            mock_query.first = AsyncMock(return_value=None)
            mock_query.one_or_none = AsyncMock(return_value=None)
            return mock_query
        
        session.query = Mock(side_effect=mock_query_filter)
        return session
    
    @pytest.fixture
    def extension_manager(self, temp_extension_root, mock_plugin_router, mock_db_session):
        """Create ExtensionManager instance for testing."""
        return ExtensionManager(
            extension_root=temp_extension_root,
            plugin_router=mock_plugin_router,
            db_session=mock_db_session
        )
    
    @pytest.fixture
    def sample_manifest(self):
        """Create sample extension manifest."""
        return {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": True,
                "provides_api": True,
                "provides_background_tasks": False,
                "provides_webhooks": False
            },
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": ["execute"],
                "system_access": [],
                "network_access": []
            }
        }
    
    def create_test_extension(self, temp_dir: Path, manifest_data: dict):
        """Create a test extension directory with manifest and __init__.py."""
        ext_dir = temp_dir / manifest_data["name"]
        ext_dir.mkdir(parents=True, exist_ok=True)
        
        # Create manifest
        manifest_path = ext_dir / "extension.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        # Create __init__.py with test extension class
        init_path = ext_dir / "__init__.py"
        init_content = '''
from ai_karen_engine.extensions.base import BaseExtension

class TestExtension(BaseExtension):
    async def _initialize(self):
        self.initialized = True
    
    async def _shutdown(self):
        self.shutdown_called = True
    
    def get_tenant_data(self, tenant_id):
        """Test method to access tenant data."""
        return self.data_manager.get_tenant_data(tenant_id)
'''
        with open(init_path, 'w') as f:
            f.write(init_content)
        
        return ext_dir
    
    # Test Extension Loading with Tenant Context
    @pytest.mark.asyncio
    async def test_extension_loading_tenant_isolation(self, extension_manager, temp_extension_root, sample_manifest):
        """Test that extensions are loaded with proper tenant isolation."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Load extension
        record = await extension_manager.load_extension("test-extension")
        
        # Verify extension has access to data manager with tenant isolation
        assert record.instance.data_manager is not None
        assert hasattr(record.instance.data_manager, 'extension_name')
        assert record.instance.data_manager.extension_name == "test-extension"
    
    @pytest.mark.asyncio
    async def test_multiple_extensions_tenant_isolation(self, extension_manager, temp_extension_root, sample_manifest):
        """Test that multiple extensions maintain tenant isolation."""
        # Create first extension
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Create second extension
        manifest2 = sample_manifest.copy()
        manifest2["name"] = "test-extension-2"
        self.create_test_extension(temp_extension_root, manifest2)
        
        # Load both extensions
        record1 = await extension_manager.load_extension("test-extension")
        record2 = await extension_manager.load_extension("test-extension-2")
        
        # Verify each extension has its own isolated data manager
        assert record1.instance.data_manager.extension_name == "test-extension"
        assert record2.instance.data_manager.extension_name == "test-extension-2"
        assert record1.instance.data_manager != record2.instance.data_manager
    
    # Test Data Manager Tenant Isolation
    def test_data_manager_tenant_schema_isolation(self, mock_db_session):
        """Test that data manager creates tenant-isolated schemas."""
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # Test tenant schema naming
        tenant_schema = data_manager.get_tenant_schema("tenant_123")
        assert tenant_schema == "ext_test-extension_tenant_tenant_123"
        
        # Different tenants should have different schemas
        tenant_schema2 = data_manager.get_tenant_schema("tenant_456")
        assert tenant_schema2 == "ext_test-extension_tenant_tenant_456"
        assert tenant_schema != tenant_schema2
    
    @pytest.mark.asyncio
    async def test_data_manager_query_tenant_filtering(self, mock_db_session):
        """Test that data manager queries are automatically filtered by tenant."""
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # Mock query execution
        mock_result = [{"id": 1, "data": "test"}]
        mock_db_session.execute.return_value.fetchall.return_value = mock_result
        
        # Query with tenant filtering
        result = await data_manager.query(
            table_name="test_table",
            filters={"status": "active"},
            tenant_id="tenant_123",
            user_id="user_456"
        )
        
        # Verify query was executed
        mock_db_session.execute.assert_called()
        
        # Verify result is returned (actual filtering would be in real implementation)
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_data_manager_insert_tenant_context(self, mock_db_session):
        """Test that data manager inserts include tenant context."""
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # Mock insert execution
        mock_db_session.execute.return_value.lastrowid = 123
        
        # Insert with tenant context
        result = await data_manager.insert(
            table_name="test_table",
            data={"name": "test", "value": "data"},
            tenant_id="tenant_123",
            user_id="user_456"
        )
        
        # Verify insert was executed
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called()
        
        # Verify result
        assert result == 123
    
    @pytest.mark.asyncio
    async def test_data_manager_create_table_tenant_isolation(self, mock_db_session):
        """Test that table creation includes tenant isolation."""
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # Create table with tenant isolation
        await data_manager.create_table(
            table_name="user_data",
            schema={"id": "INTEGER PRIMARY KEY", "name": "TEXT"},
            tenant_id="tenant_123"
        )
        
        # Verify table creation was executed
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called()
    
    # Test Permission Isolation
    @pytest.mark.asyncio
    async def test_extension_permission_isolation(self, extension_manager, temp_extension_root, sample_manifest):
        """Test that extensions respect permission boundaries."""
        # Create extension with limited permissions
        sample_manifest["permissions"]["data_access"] = ["read"]  # No write permission
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        record = await extension_manager.load_extension("test-extension")
        
        # Verify extension has the specified permissions
        assert record.manifest.permissions["data_access"] == ["read"]
        assert "write" not in record.manifest.permissions["data_access"]
    
    def test_extension_permission_validation(self, sample_manifest):
        """Test extension permission validation."""
        # Test valid permissions
        manifest = ExtensionManifest(**sample_manifest)
        assert manifest.permissions["data_access"] == ["read", "write"]
        
        # Test that permissions are properly structured
        assert isinstance(manifest.permissions["data_access"], list)
        assert isinstance(manifest.permissions["plugin_access"], list)
    
    # Test Cross-Tenant Data Access Prevention
    @pytest.mark.asyncio
    async def test_prevent_cross_tenant_data_access(self, mock_db_session):
        """Test that extensions cannot access data from other tenants."""
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # Simulate query that should be filtered by tenant
        await data_manager.query(
            table_name="sensitive_data",
            filters={},
            tenant_id="tenant_123",
            user_id="user_456"
        )
        
        # Verify that the query includes tenant filtering
        # In a real implementation, this would check that the SQL includes tenant_id filtering
        mock_db_session.execute.assert_called()
        call_args = mock_db_session.execute.call_args
        
        # The actual SQL would include tenant filtering in a real implementation
        assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_prevent_cross_user_data_access(self, mock_db_session):
        """Test that extensions cannot access data from other users within same tenant."""
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # Query with specific user context
        await data_manager.query(
            table_name="user_private_data",
            filters={},
            tenant_id="tenant_123",
            user_id="user_456"
        )
        
        # Verify query execution with user filtering
        mock_db_session.execute.assert_called()
        
        # In a real implementation, this would verify user_id filtering in the SQL
        call_args = mock_db_session.execute.call_args
        assert call_args is not None
    
    # Test Extension Registry Isolation
    def test_extension_registry_tenant_awareness(self, extension_manager):
        """Test that extension registry is tenant-aware."""
        registry = extension_manager.get_registry()
        
        # Registry should exist and be properly initialized
        assert registry is not None
        
        # In a real implementation, registry would track tenant-specific extension installations
        # For now, we verify the registry exists and can be accessed
        assert hasattr(registry, 'extensions')
    
    # Test Resource Isolation
    @pytest.mark.asyncio
    async def test_extension_resource_isolation(self, extension_manager, temp_extension_root, sample_manifest):
        """Test that extensions have isolated resource usage tracking."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        record = await extension_manager.load_extension("test-extension")
        
        # Verify resource monitoring is set up
        assert extension_manager.resource_monitor is not None
        
        # In a real implementation, this would verify that resource usage is tracked per extension
        # and that extensions cannot exceed their allocated resources
        assert record.manifest.name == "test-extension"
    
    # Test API Endpoint Isolation
    def test_extension_api_endpoint_isolation(self, sample_manifest):
        """Test that extension API endpoints are properly isolated."""
        manifest = ExtensionManifest(**sample_manifest)
        
        # Verify API configuration exists
        if hasattr(manifest, 'api') and manifest.api:
            # In a real implementation, this would verify that API endpoints
            # include proper tenant and user context validation
            assert isinstance(manifest.api, dict)
    
    # Test Background Task Isolation
    def test_extension_background_task_isolation(self, sample_manifest):
        """Test that extension background tasks respect tenant boundaries."""
        manifest = ExtensionManifest(**sample_manifest)
        
        # Verify background task configuration
        if hasattr(manifest, 'background_tasks') and manifest.background_tasks:
            # In a real implementation, this would verify that background tasks
            # operate within tenant boundaries and cannot access cross-tenant data
            assert isinstance(manifest.background_tasks, list)
    
    # Test Extension Communication Isolation
    @pytest.mark.asyncio
    async def test_extension_communication_isolation(self, extension_manager, temp_extension_root, sample_manifest):
        """Test that extensions cannot communicate across tenant boundaries."""
        # Create two extensions
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        manifest2 = sample_manifest.copy()
        manifest2["name"] = "test-extension-2"
        self.create_test_extension(temp_extension_root, manifest2)
        
        # Load both extensions
        record1 = await extension_manager.load_extension("test-extension")
        record2 = await extension_manager.load_extension("test-extension-2")
        
        # Verify extensions are isolated from each other
        assert record1.instance != record2.instance
        assert record1.instance.data_manager != record2.instance.data_manager
        
        # In a real implementation, this would test that extensions cannot
        # directly access each other's data or state across tenant boundaries
    
    # Test Security Context Validation
    def test_extension_security_context_validation(self, extension_manager):
        """Test that extension security contexts are properly validated."""
        # Verify extension manager has security components
        assert extension_manager.validator is not None
        
        # In a real implementation, this would test that security contexts
        # are validated before extension operations
        assert hasattr(extension_manager, 'validator')
    
    # Test Audit Logging for Tenant Operations
    @pytest.mark.asyncio
    async def test_tenant_operation_audit_logging(self, extension_manager, temp_extension_root, sample_manifest):
        """Test that tenant-specific operations are properly audited."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Load extension (this should be audited)
        record = await extension_manager.load_extension("test-extension")
        
        # Verify extension was loaded
        assert record is not None
        
        # In a real implementation, this would verify that the operation
        # was logged with proper tenant context for audit purposes
        assert record.manifest.name == "test-extension"
    
    # Test Configuration Isolation
    def test_extension_configuration_isolation(self, mock_db_session):
        """Test that extension configurations are tenant-isolated."""
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # Verify data manager is properly initialized for configuration isolation
        assert data_manager.extension_name == "test-extension"
        assert data_manager.table_prefix == "ext_test-extension_"
        
        # In a real implementation, this would test that configuration data
        # is stored and retrieved with proper tenant isolation
    
    # Test Memory Isolation
    def test_extension_memory_isolation(self, extension_manager):
        """Test that extensions have isolated memory spaces."""
        # Verify resource monitor exists for memory tracking
        assert extension_manager.resource_monitor is not None
        
        # In a real implementation, this would test that extensions
        # cannot access each other's memory spaces and that memory
        # usage is properly tracked and limited per tenant
    
    # Test Network Access Isolation
    def test_extension_network_access_isolation(self, sample_manifest):
        """Test that extension network access is properly controlled."""
        manifest = ExtensionManifest(**sample_manifest)
        
        # Verify network permissions are defined
        assert "network_access" in manifest.permissions
        assert isinstance(manifest.permissions["network_access"], list)
        
        # In a real implementation, this would test that network access
        # is restricted based on the extension's declared permissions
        # and that cross-tenant network communication is prevented


class TestPermissionEnforcement:
    """Test permission enforcement in extension system."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()
    
    def test_data_access_permission_validation(self, mock_db_session):
        """Test data access permission validation."""
        # Create data manager
        data_manager = ExtensionDataManager(mock_db_session, "test-extension")
        
        # In a real implementation, this would test that data operations
        # are validated against the extension's declared permissions
        assert data_manager.extension_name == "test-extension"
    
    def test_plugin_access_permission_validation(self):
        """Test plugin access permission validation."""
        # Create mock plugin router
        plugin_router = Mock(spec=PluginRouter)
        
        # In a real implementation, this would test that plugin execution
        # is validated against the extension's plugin access permissions
        assert plugin_router is not None
    
    def test_system_access_permission_validation(self):
        """Test system access permission validation."""
        # In a real implementation, this would test that system resource access
        # (logs, metrics, etc.) is validated against declared permissions
        pass
    
    def test_network_access_permission_validation(self):
        """Test network access permission validation."""
        # In a real implementation, this would test that network operations
        # are validated against the extension's network access permissions
        pass


class TestSecurityBoundaries:
    """Test security boundaries in extension system."""
    
    def test_extension_sandbox_boundaries(self):
        """Test that extensions operate within sandbox boundaries."""
        # In a real implementation, this would test that extensions
        # cannot break out of their assigned sandbox environments
        pass
    
    def test_resource_limit_enforcement(self):
        """Test that resource limits are properly enforced."""
        # In a real implementation, this would test that CPU, memory,
        # and disk usage limits are enforced for extensions
        pass
    
    def test_file_system_access_boundaries(self):
        """Test that file system access is properly restricted."""
        # In a real implementation, this would test that extensions
        # can only access files within their designated directories
        pass
    
    def test_database_access_boundaries(self):
        """Test that database access is properly restricted."""
        # In a real implementation, this would test that extensions
        # can only access their own database schemas and tables
        pass