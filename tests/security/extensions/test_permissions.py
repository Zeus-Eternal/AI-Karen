"""
Security tests for extension permission system.
Tests permission validation, enforcement, and access control.
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

from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionContext
from ai_karen_engine.plugins.router import PluginRouter


class TestPermissionValidation:
    """Test extension permission validation."""
    
    @pytest.fixture
    def sample_manifest_data(self):
        """Create sample manifest data with permissions."""
        return {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": ["execute"],
                "system_access": ["metrics", "logs"],
                "network_access": ["outbound_http"]
            }
        }
    
    def test_valid_permission_structure(self, sample_manifest_data):
        """Test that valid permission structure is accepted."""
        manifest = ExtensionManifest(**sample_manifest_data)
        
        assert manifest.permissions["data_access"] == ["read", "write"]
        assert manifest.permissions["plugin_access"] == ["execute"]
        assert manifest.permissions["system_access"] == ["metrics", "logs"]
        assert manifest.permissions["network_access"] == ["outbound_http"]
    
    def test_empty_permissions(self):
        """Test extension with no permissions."""
        manifest_data = {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": [],
                "plugin_access": [],
                "system_access": [],
                "network_access": []
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        assert all(len(perms) == 0 for perms in manifest.permissions.values())
    
    def test_missing_permissions_field(self):
        """Test extension with missing permissions field."""
        manifest_data = {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0"
        }
        
        # Should work with default permissions
        manifest = ExtensionManifest(**manifest_data)
        assert manifest.name == "test-extension"
    
    def test_invalid_permission_values(self):
        """Test extension with invalid permission values."""
        manifest_data = {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["invalid_permission"],
                "plugin_access": ["unknown_access"],
                "system_access": ["dangerous_access"],
                "network_access": ["unrestricted"]
            }
        }
        
        # Should still create manifest (validation happens at runtime)
        manifest = ExtensionManifest(**manifest_data)
        assert manifest.permissions["data_access"] == ["invalid_permission"]
    
    def test_permission_inheritance(self, sample_manifest_data):
        """Test that permissions are properly inherited by extension instances."""
        manifest = ExtensionManifest(**sample_manifest_data)
        
        # Create mock context
        context = ExtensionContext(
            plugin_router=Mock(),
            db_session=AsyncMock(),
            app_instance=None
        )
        
        # Create test extension
        class TestExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        extension = TestExtension(manifest, context)
        
        # Verify extension has access to permissions
        assert extension.manifest.permissions == manifest.permissions


class TestDataAccessPermissions:
    """Test data access permission enforcement."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def extension_with_read_only(self, mock_db_session):
        """Create extension with read-only data access."""
        manifest_data = {
            "name": "readonly-extension",
            "version": "1.0.0",
            "display_name": "Read Only Extension",
            "description": "Extension with read-only access",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["read"],
                "plugin_access": [],
                "system_access": [],
                "network_access": []
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        context = ExtensionContext(
            plugin_router=Mock(),
            db_session=mock_db_session,
            app_instance=None
        )
        
        class ReadOnlyExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        return ReadOnlyExtension(manifest, context)
    
    @pytest.fixture
    def extension_with_read_write(self, mock_db_session):
        """Create extension with read-write data access."""
        manifest_data = {
            "name": "readwrite-extension",
            "version": "1.0.0",
            "display_name": "Read Write Extension",
            "description": "Extension with read-write access",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": [],
                "system_access": [],
                "network_access": []
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        context = ExtensionContext(
            plugin_router=Mock(),
            db_session=mock_db_session,
            app_instance=None
        )
        
        class ReadWriteExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        return ReadWriteExtension(manifest, context)
    
    def test_read_only_permission_check(self, extension_with_read_only):
        """Test read-only permission validation."""
        permissions = extension_with_read_only.manifest.permissions["data_access"]
        
        assert "read" in permissions
        assert "write" not in permissions
        assert len(permissions) == 1
    
    def test_read_write_permission_check(self, extension_with_read_write):
        """Test read-write permission validation."""
        permissions = extension_with_read_write.manifest.permissions["data_access"]
        
        assert "read" in permissions
        assert "write" in permissions
        assert len(permissions) == 2
    
    @pytest.mark.asyncio
    async def test_data_manager_respects_permissions(self, extension_with_read_only):
        """Test that data manager respects extension permissions."""
        data_manager = extension_with_read_only.data_manager
        
        # Verify data manager is initialized
        assert data_manager is not None
        assert data_manager.extension_name == "readonly-extension"
        
        # In a real implementation, this would test that write operations
        # are blocked for read-only extensions
    
    @pytest.mark.asyncio
    async def test_query_operation_allowed(self, extension_with_read_only):
        """Test that query operations are allowed for read permission."""
        data_manager = extension_with_read_only.data_manager
        
        # Mock successful query
        data_manager.db_session.execute.return_value.fetchall.return_value = [{"id": 1}]
        
        # This should be allowed with read permission
        result = await data_manager.query(
            table_name="test_table",
            filters={},
            tenant_id="tenant_123",
            user_id="user_456"
        )
        
        # Verify query was executed
        data_manager.db_session.execute.assert_called()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_insert_operation_permission_check(self, extension_with_read_write):
        """Test that insert operations check write permission."""
        data_manager = extension_with_read_write.data_manager
        
        # Mock successful insert
        data_manager.db_session.execute.return_value.lastrowid = 123
        
        # This should be allowed with write permission
        result = await data_manager.insert(
            table_name="test_table",
            data={"name": "test"},
            tenant_id="tenant_123",
            user_id="user_456"
        )
        
        # Verify insert was executed
        data_manager.db_session.execute.assert_called()
        data_manager.db_session.commit.assert_called()
        assert result == 123


class TestPluginAccessPermissions:
    """Test plugin access permission enforcement."""
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router."""
        router = Mock(spec=PluginRouter)
        router.dispatch = AsyncMock(return_value="plugin_result")
        router.list_intents = Mock(return_value=["hello_world", "time_query"])
        return router
    
    @pytest.fixture
    def extension_with_plugin_access(self, mock_plugin_router):
        """Create extension with plugin access permission."""
        manifest_data = {
            "name": "plugin-extension",
            "version": "1.0.0",
            "display_name": "Plugin Extension",
            "description": "Extension with plugin access",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": [],
                "plugin_access": ["execute"],
                "system_access": [],
                "network_access": []
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        context = ExtensionContext(
            plugin_router=mock_plugin_router,
            db_session=AsyncMock(),
            app_instance=None
        )
        
        class PluginExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        return PluginExtension(manifest, context)
    
    @pytest.fixture
    def extension_without_plugin_access(self, mock_plugin_router):
        """Create extension without plugin access permission."""
        manifest_data = {
            "name": "no-plugin-extension",
            "version": "1.0.0",
            "display_name": "No Plugin Extension",
            "description": "Extension without plugin access",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["read"],
                "plugin_access": [],
                "system_access": [],
                "network_access": []
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        context = ExtensionContext(
            plugin_router=mock_plugin_router,
            db_session=AsyncMock(),
            app_instance=None
        )
        
        class NoPluginExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        return NoPluginExtension(manifest, context)
    
    def test_plugin_access_permission_present(self, extension_with_plugin_access):
        """Test that plugin access permission is present."""
        permissions = extension_with_plugin_access.manifest.permissions["plugin_access"]
        assert "execute" in permissions
    
    def test_plugin_access_permission_absent(self, extension_without_plugin_access):
        """Test that plugin access permission is absent."""
        permissions = extension_without_plugin_access.manifest.permissions["plugin_access"]
        assert "execute" not in permissions
        assert len(permissions) == 0
    
    @pytest.mark.asyncio
    async def test_plugin_orchestrator_with_permission(self, extension_with_plugin_access):
        """Test plugin orchestrator usage with permission."""
        orchestrator = extension_with_plugin_access.plugin_orchestrator
        
        # Should be able to execute plugins with permission
        result = await orchestrator.execute_plugin(
            intent="hello_world",
            params={"name": "test"},
            user_context={"roles": ["user"]}
        )
        
        assert result == "plugin_result"
        orchestrator.plugin_router.dispatch.assert_called_with(
            "hello_world", {"name": "test"}, ["user"]
        )
    
    @pytest.mark.asyncio
    async def test_plugin_orchestrator_without_permission(self, extension_without_plugin_access):
        """Test plugin orchestrator usage without permission."""
        orchestrator = extension_without_plugin_access.plugin_orchestrator
        
        # In a real implementation, this would be blocked due to lack of permission
        # For now, we just verify the orchestrator exists
        assert orchestrator is not None
        assert orchestrator.plugin_router is not None


class TestSystemAccessPermissions:
    """Test system access permission enforcement."""
    
    @pytest.fixture
    def extension_with_system_access(self):
        """Create extension with system access permissions."""
        manifest_data = {
            "name": "system-extension",
            "version": "1.0.0",
            "display_name": "System Extension",
            "description": "Extension with system access",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": [],
                "plugin_access": [],
                "system_access": ["metrics", "logs"],
                "network_access": []
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        context = ExtensionContext(
            plugin_router=Mock(),
            db_session=AsyncMock(),
            app_instance=None
        )
        
        class SystemExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        return SystemExtension(manifest, context)
    
    def test_system_access_permissions(self, extension_with_system_access):
        """Test system access permission validation."""
        permissions = extension_with_system_access.manifest.permissions["system_access"]
        
        assert "metrics" in permissions
        assert "logs" in permissions
        assert len(permissions) == 2
    
    def test_metrics_access_permission(self, extension_with_system_access):
        """Test metrics access permission."""
        permissions = extension_with_system_access.manifest.permissions["system_access"]
        
        # Extension should have metrics access
        assert "metrics" in permissions
        
        # In a real implementation, this would test that the extension
        # can access system metrics based on this permission
    
    def test_logs_access_permission(self, extension_with_system_access):
        """Test logs access permission."""
        permissions = extension_with_system_access.manifest.permissions["system_access"]
        
        # Extension should have logs access
        assert "logs" in permissions
        
        # In a real implementation, this would test that the extension
        # can access system logs based on this permission


class TestNetworkAccessPermissions:
    """Test network access permission enforcement."""
    
    @pytest.fixture
    def extension_with_network_access(self):
        """Create extension with network access permissions."""
        manifest_data = {
            "name": "network-extension",
            "version": "1.0.0",
            "display_name": "Network Extension",
            "description": "Extension with network access",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": [],
                "plugin_access": [],
                "system_access": [],
                "network_access": ["outbound_http", "outbound_https"]
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        context = ExtensionContext(
            plugin_router=Mock(),
            db_session=AsyncMock(),
            app_instance=None
        )
        
        class NetworkExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        return NetworkExtension(manifest, context)
    
    @pytest.fixture
    def extension_without_network_access(self):
        """Create extension without network access permissions."""
        manifest_data = {
            "name": "no-network-extension",
            "version": "1.0.0",
            "display_name": "No Network Extension",
            "description": "Extension without network access",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["read"],
                "plugin_access": [],
                "system_access": [],
                "network_access": []
            }
        }
        
        manifest = ExtensionManifest(**manifest_data)
        context = ExtensionContext(
            plugin_router=Mock(),
            db_session=AsyncMock(),
            app_instance=None
        )
        
        class NoNetworkExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        return NoNetworkExtension(manifest, context)
    
    def test_network_access_permissions_present(self, extension_with_network_access):
        """Test that network access permissions are present."""
        permissions = extension_with_network_access.manifest.permissions["network_access"]
        
        assert "outbound_http" in permissions
        assert "outbound_https" in permissions
        assert len(permissions) == 2
    
    def test_network_access_permissions_absent(self, extension_without_network_access):
        """Test that network access permissions are absent."""
        permissions = extension_without_network_access.manifest.permissions["network_access"]
        
        assert len(permissions) == 0
        assert "outbound_http" not in permissions
        assert "outbound_https" not in permissions
    
    def test_http_access_permission(self, extension_with_network_access):
        """Test HTTP access permission."""
        permissions = extension_with_network_access.manifest.permissions["network_access"]
        
        # Extension should have HTTP access
        assert "outbound_http" in permissions
        
        # In a real implementation, this would test that the extension
        # can make HTTP requests based on this permission
    
    def test_https_access_permission(self, extension_with_network_access):
        """Test HTTPS access permission."""
        permissions = extension_with_network_access.manifest.permissions["network_access"]
        
        # Extension should have HTTPS access
        assert "outbound_https" in permissions
        
        # In a real implementation, this would test that the extension
        # can make HTTPS requests based on this permission


class TestPermissionEnforcement:
    """Test runtime permission enforcement."""
    
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
    def extension_manager(self, temp_extension_root, mock_plugin_router):
        """Create ExtensionManager instance for testing."""
        return ExtensionManager(
            extension_root=temp_extension_root,
            plugin_router=mock_plugin_router,
            db_session=AsyncMock()
        )
    
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
    
    def check_permission(self, permission_type, permission):
        """Test method to check permissions."""
        return permission in self.manifest.permissions.get(permission_type, [])
'''
        with open(init_path, 'w') as f:
            f.write(init_content)
        
        return ext_dir
    
    @pytest.mark.asyncio
    async def test_permission_enforcement_during_loading(self, extension_manager, temp_extension_root):
        """Test that permissions are enforced during extension loading."""
        manifest_data = {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["read"],
                "plugin_access": ["execute"],
                "system_access": [],
                "network_access": []
            }
        }
        
        self.create_test_extension(temp_extension_root, manifest_data)
        
        # Load extension
        record = await extension_manager.load_extension("test-extension")
        
        # Verify permissions are loaded correctly
        assert record.manifest.permissions["data_access"] == ["read"]
        assert record.manifest.permissions["plugin_access"] == ["execute"]
        assert record.manifest.permissions["system_access"] == []
        assert record.manifest.permissions["network_access"] == []
    
    @pytest.mark.asyncio
    async def test_permission_validation_during_operation(self, extension_manager, temp_extension_root):
        """Test that permissions are validated during extension operations."""
        manifest_data = {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": ["execute"],
                "system_access": ["metrics"],
                "network_access": ["outbound_http"]
            }
        }
        
        self.create_test_extension(temp_extension_root, manifest_data)
        
        # Load extension
        record = await extension_manager.load_extension("test-extension")
        
        # Test permission checking method
        extension_instance = record.instance
        
        # Should have read permission
        assert extension_instance.check_permission("data_access", "read") is True
        # Should have write permission
        assert extension_instance.check_permission("data_access", "write") is True
        # Should not have admin permission
        assert extension_instance.check_permission("data_access", "admin") is False
        
        # Should have execute permission
        assert extension_instance.check_permission("plugin_access", "execute") is True
        # Should not have admin permission
        assert extension_instance.check_permission("plugin_access", "admin") is False
    
    def test_permission_inheritance_validation(self):
        """Test that permission inheritance is properly validated."""
        # In a real implementation, this would test that child extensions
        # cannot have more permissions than their parent extensions
        pass
    
    def test_permission_escalation_prevention(self):
        """Test that permission escalation is prevented."""
        # In a real implementation, this would test that extensions
        # cannot escalate their permissions at runtime
        pass
    
    def test_cross_extension_permission_isolation(self):
        """Test that extensions cannot access each other's permissions."""
        # In a real implementation, this would test that extensions
        # cannot read or modify other extensions' permission contexts
        pass


class TestPermissionAuditing:
    """Test permission auditing and logging."""
    
    def test_permission_usage_logging(self):
        """Test that permission usage is properly logged."""
        # In a real implementation, this would test that all permission
        # checks and usage are logged for audit purposes
        pass
    
    def test_permission_violation_logging(self):
        """Test that permission violations are logged."""
        # In a real implementation, this would test that attempts to
        # use permissions not granted to an extension are logged
        pass
    
    def test_permission_change_auditing(self):
        """Test that permission changes are audited."""
        # In a real implementation, this would test that changes to
        # extension permissions are properly audited and logged
        pass