"""
Unit tests for ExtensionManager class.
Tests extension discovery, loading, lifecycle management, and error handling.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.extensions.models import (
    ExtensionManifest,
    ExtensionRecord,
    ExtensionStatus,
    ExtensionContext
)
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.plugins.router import PluginRouter
from ai_karen_engine.services.plugin_registry import (
    PluginManifest,
    PluginMetadata,
    PluginStatus,
    get_plugin_registry,
)


class MockExtension(BaseExtension):
    """Mock extension for testing."""
    
    def __init__(self, manifest, context):
        super().__init__(manifest, context)
        self.initialized = False
        self.shutdown_called = False
    
    async def _initialize(self):
        self.initialized = True
    
    async def _shutdown(self):
        self.shutdown_called = True


class TestExtensionManager:
    """Test ExtensionManager functionality."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture(autouse=True)
    def ensure_plugin_dependency(self):
        """Ensure required test plugins are present in the registry."""
        registry = get_plugin_registry()
        registry.plugins.clear()
        registry.plugins_by_category.clear()
        registry.plugins_by_type.clear()

        manifest = PluginManifest(
            name="hello_world",
            version="1.0.0",
            description="Test hello world plugin",
            author="Test",
            module="plugins.hello_world",
        )
        metadata = PluginMetadata(
            manifest=manifest,
            path=Path("."),
            status=PluginStatus.ACTIVE,
        )
        registry.plugins[manifest.name] = metadata
        registry._update_indices()

        yield

        registry.plugins.clear()
        registry.plugins_by_category.clear()
        registry.plugins_by_type.clear()

    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router."""
        router = Mock(spec=PluginRouter)
        router.dispatch = AsyncMock(return_value="plugin_result")
        router.list_intents = Mock(return_value=["test_intent"])
        return router
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
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
            "category": "general",
            "tags": ["test"],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": True,
                "provides_api": True,
                "provides_background_tasks": False,
                "provides_webhooks": False
            },
            "dependencies": {
                "plugins": ["hello_world"],
                "extensions": [],
                "system_services": []
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
        
        # Create __init__.py with mock extension class
        init_path = ext_dir / "__init__.py"
        class_name = self._get_extension_class_name(manifest_data["name"])
        init_content = f'''
from ai_karen_engine.extensions.base import BaseExtension

class {class_name}(BaseExtension):
    async def _initialize(self):
        self.initialized = True
    
    async def _shutdown(self):
        self.shutdown_called = True
'''
        with open(init_path, 'w') as f:
            f.write(init_content)
        
        return ext_dir
    
    def _get_extension_class_name(self, extension_name: str) -> str:
        """Convert kebab/underscore to PascalCase + 'Extension' suffix."""
        words = extension_name.replace("-", "_").split("_")
        base_name = "".join(word.capitalize() for word in words)
        if base_name.lower().endswith("extension"):
            return base_name
        return base_name + "Extension"
    
    # Test Discovery
    @pytest.mark.asyncio
    async def test_discover_extensions_empty_directory(self, extension_manager):
        """Test discovery with empty extension directory."""
        manifests = await extension_manager.discover_extensions()
        assert manifests == {}
    
    @pytest.mark.asyncio
    async def test_discover_extensions_single_extension(self, extension_manager, temp_extension_root, sample_manifest):
        """Test discovery of single extension."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        manifests = await extension_manager.discover_extensions()
        assert len(manifests) == 1
        assert "test-extension" in manifests
        assert manifests["test-extension"].name == "test-extension"
        assert manifests["test-extension"].version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_discover_extensions_multiple_extensions(self, extension_manager, temp_extension_root, sample_manifest):
        """Test discovery of multiple extensions."""
        # Create first extension
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Create second extension
        manifest2 = sample_manifest.copy()
        manifest2["name"] = "test-extension-2"
        manifest2["display_name"] = "Test Extension 2"
        self.create_test_extension(temp_extension_root, manifest2)
        
        manifests = await extension_manager.discover_extensions()
        assert len(manifests) == 2
        assert "test-extension" in manifests
        assert "test-extension-2" in manifests
    
    @pytest.mark.asyncio
    async def test_discover_extensions_invalid_manifest(self, extension_manager, temp_extension_root):
        """Test discovery with invalid manifest."""
        ext_dir = temp_extension_root / "invalid-extension"
        ext_dir.mkdir()
        
        # Create invalid manifest (missing required fields)
        manifest_path = ext_dir / "extension.json"
        with open(manifest_path, 'w') as f:
            json.dump({"name": "invalid"}, f)  # Missing required fields
        
        manifests = await extension_manager.discover_extensions()
        assert len(manifests) == 0  # Invalid extension should be skipped
    
    @pytest.mark.asyncio
    async def test_discover_extensions_categorized_structure(self, extension_manager, temp_extension_root, sample_manifest):
        """Test discovery with categorized directory structure."""
        # Create category directory
        category_dir = temp_extension_root / "analytics"
        category_dir.mkdir()
        
        # Create extension in category
        ext_dir = category_dir / sample_manifest["name"]
        ext_dir.mkdir()
        
        manifest_path = ext_dir / "extension.json"
        with open(manifest_path, 'w') as f:
            json.dump(sample_manifest, f, indent=2)
        
        init_path = ext_dir / "__init__.py"
        with open(init_path, 'w') as f:
            f.write('''
from ai_karen_engine.extensions.base import BaseExtension

class TestExtension(BaseExtension):
    async def _initialize(self):
        pass
''')
        
        manifests = await extension_manager.discover_extensions()
        assert len(manifests) == 1
        assert "test-extension" in manifests
    
    # Test Loading
    @pytest.mark.asyncio
    async def test_load_extension_success(self, extension_manager, temp_extension_root, sample_manifest):
        """Test successful extension loading."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        record = await extension_manager.load_extension("test-extension")
        
        assert record is not None
        assert record.manifest.name == "test-extension"
        assert record.status == ExtensionStatus.ACTIVE
        assert record.instance is not None
        assert hasattr(record.instance, 'initialized')
    
    @pytest.mark.asyncio
    async def test_load_extension_not_found(self, extension_manager):
        """Test loading non-existent extension."""
        with pytest.raises(RuntimeError, match="Extension directory not found"):
            await extension_manager.load_extension("non-existent")
    
    @pytest.mark.asyncio
    async def test_load_extension_missing_manifest(self, extension_manager, temp_extension_root):
        """Test loading extension with missing manifest."""
        ext_dir = temp_extension_root / "no-manifest"
        ext_dir.mkdir()
        
        with pytest.raises(RuntimeError, match="Extension manifest not found"):
            await extension_manager.load_extension("no-manifest")
    
    @pytest.mark.asyncio
    async def test_load_extension_missing_init_file(self, extension_manager, temp_extension_root, sample_manifest):
        """Test loading extension with missing __init__.py."""
        ext_dir = temp_extension_root / sample_manifest["name"]
        ext_dir.mkdir()
        
        # Create manifest but no __init__.py
        manifest_path = ext_dir / "extension.json"
        with open(manifest_path, 'w') as f:
            json.dump(sample_manifest, f)
        
        with pytest.raises(RuntimeError, match="Extension __init__.py not found"):
            await extension_manager.load_extension("test-extension")
    
    @pytest.mark.asyncio
    async def test_load_extension_missing_dependencies(self, extension_manager, temp_extension_root, sample_manifest):
        """Test loading extension with missing dependencies."""
        # Add dependency that doesn't exist
        sample_manifest["dependencies"]["plugins"] = ["non_existent_plugin"]
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        with pytest.raises(RuntimeError, match="Missing dependencies"):
            await extension_manager.load_extension("test-extension")
    
    @pytest.mark.asyncio
    async def test_load_extension_initialization_failure(self, extension_manager, temp_extension_root, sample_manifest):
        """Test loading extension that fails during initialization."""
        ext_dir = self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Overwrite __init__.py with failing extension
        init_path = ext_dir / "__init__.py"
        with open(init_path, 'w') as f:
            f.write('''
from ai_karen_engine.extensions.base import BaseExtension

class TestExtension(BaseExtension):
    async def _initialize(self):
        raise RuntimeError("Initialization failed")
''')
        
        with pytest.raises(RuntimeError, match="Extension initialization failed"):
            await extension_manager.load_extension("test-extension")
    
    # Test Unloading
    @pytest.mark.asyncio
    async def test_unload_extension_success(self, extension_manager, temp_extension_root, sample_manifest):
        """Test successful extension unloading."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Load extension first
        record = await extension_manager.load_extension("test-extension")
        assert record.status == ExtensionStatus.ACTIVE
        
        # Unload extension
        await extension_manager.unload_extension("test-extension")
        
        # Verify extension is no longer in registry
        assert extension_manager.registry.get_extension("test-extension") is None
    
    @pytest.mark.asyncio
    async def test_unload_extension_not_found(self, extension_manager):
        """Test unloading non-existent extension."""
        with pytest.raises(RuntimeError, match="Extension test-extension not found in registry"):
            await extension_manager.unload_extension("test-extension")
    
    @pytest.mark.asyncio
    async def test_unload_extension_with_shutdown_error(self, extension_manager, temp_extension_root, sample_manifest):
        """Test unloading extension that fails during shutdown."""
        ext_dir = self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Overwrite __init__.py with failing shutdown
        init_path = ext_dir / "__init__.py"
        with open(init_path, 'w') as f:
            f.write('''
from ai_karen_engine.extensions.base import BaseExtension

class TestExtension(BaseExtension):
    async def _initialize(self):
        pass
    
    async def _shutdown(self):
        raise RuntimeError("Shutdown failed")
''')
        
        # Load extension
        await extension_manager.load_extension("test-extension")
        
        # Unload should succeed despite shutdown error
        await extension_manager.unload_extension("test-extension")
        assert extension_manager.registry.get_extension("test-extension") is None
    
    # Test Reloading
    @pytest.mark.asyncio
    async def test_reload_extension_success(self, extension_manager, temp_extension_root, sample_manifest):
        """Test successful extension reloading."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Load extension first
        record1 = await extension_manager.load_extension("test-extension")
        instance1 = record1.instance
        
        # Reload extension
        record2 = await extension_manager.reload_extension("test-extension")
        instance2 = record2.instance
        
        # Should be different instances
        assert instance1 is not instance2
        assert record2.status == ExtensionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_reload_extension_not_loaded(self, extension_manager, temp_extension_root, sample_manifest):
        """Test reloading extension that wasn't loaded."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Reload without loading first
        record = await extension_manager.reload_extension("test-extension")
        assert record.status == ExtensionStatus.ACTIVE
    
    # Test Status and Health
    def test_get_extension_status_loaded(self, extension_manager, temp_extension_root, sample_manifest):
        """Test getting status of loaded extension."""
        async def test():
            self.create_test_extension(temp_extension_root, sample_manifest)
            record = await extension_manager.load_extension("test-extension")
            
            status = extension_manager.get_extension_status("test-extension")
            assert status is not None
            assert status["name"] == "test-extension"
            assert status["version"] == "1.0.0"
            assert status["status"] == ExtensionStatus.ACTIVE.value
            assert status["loaded_at"] is not None
            assert status["error_message"] is None
        
        asyncio.run(test())
    
    def test_get_extension_status_not_found(self, extension_manager):
        """Test getting status of non-existent extension."""
        status = extension_manager.get_extension_status("non-existent")
        assert status is None
    
    def test_get_extension_status_with_custom_status(self, extension_manager, temp_extension_root, sample_manifest):
        """Test getting status with custom status method."""
        ext_dir = self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Overwrite __init__.py with custom status method
        init_path = ext_dir / "__init__.py"
        with open(init_path, 'w') as f:
            f.write('''
from ai_karen_engine.extensions.base import BaseExtension

class TestExtension(BaseExtension):
    async def _initialize(self):
        pass
    
    def get_status(self):
        return {"custom_field": "custom_value"}
''')
        
        async def test():
            await extension_manager.load_extension("test-extension")
            status = extension_manager.get_extension_status("test-extension")
            assert "custom_field" in status
            assert status["custom_field"] == "custom_value"
        
        asyncio.run(test())
    
    # Test Load All Extensions
    @pytest.mark.asyncio
    async def test_load_all_extensions_empty(self, extension_manager):
        """Test loading all extensions with empty directory."""
        loaded = await extension_manager.load_all_extensions()
        assert loaded == {}
    
    @pytest.mark.asyncio
    async def test_load_all_extensions_multiple(self, extension_manager, temp_extension_root, sample_manifest):
        """Test loading all extensions with multiple extensions."""
        # Create multiple extensions
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        manifest2 = sample_manifest.copy()
        manifest2["name"] = "test-extension-2"
        manifest2["display_name"] = "Test Extension 2"
        self.create_test_extension(temp_extension_root, manifest2)
        
        loaded = await extension_manager.load_all_extensions()
        assert len(loaded) == 2
        assert "test-extension" in loaded
        assert "test-extension-2" in loaded
        assert all(record.status == ExtensionStatus.ACTIVE for record in loaded.values())
    
    @pytest.mark.asyncio
    async def test_load_all_extensions_with_failures(self, extension_manager, temp_extension_root, sample_manifest):
        """Test loading all extensions when some fail."""
        # Create good extension
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Create failing extension
        manifest2 = sample_manifest.copy()
        manifest2["name"] = "failing-extension"
        ext_dir = self.create_test_extension(temp_extension_root, manifest2)
        
        # Overwrite with failing extension
        init_path = ext_dir / "__init__.py"
        with open(init_path, 'w') as f:
            f.write('''
from ai_karen_engine.extensions.base import BaseExtension

class FailingExtension(BaseExtension):
    async def _initialize(self):
        raise RuntimeError("Initialization failed")
''')
        
        loaded = await extension_manager.load_all_extensions()
        # Should load the good one and skip the failing one
        assert len(loaded) == 1
        assert "test-extension" in loaded
        assert "failing-extension" not in loaded
    
    # Test Registry Access
    def test_get_registry(self, extension_manager):
        """Test getting extension registry."""
        registry = extension_manager.get_registry()
        assert registry is not None
        assert registry == extension_manager.registry
    
    def test_get_loaded_extensions_empty(self, extension_manager):
        """Test getting loaded extensions when none are loaded."""
        loaded = extension_manager.get_loaded_extensions()
        assert loaded == []
    
    def test_get_loaded_extensions_with_extensions(self, extension_manager, temp_extension_root, sample_manifest):
        """Test getting loaded extensions with loaded extensions."""
        async def test():
            self.create_test_extension(temp_extension_root, sample_manifest)
            await extension_manager.load_extension("test-extension")
            
            loaded = extension_manager.get_loaded_extensions()
            assert len(loaded) == 1
            assert loaded[0].manifest.name == "test-extension"
        
        asyncio.run(test())
    
    def test_get_extension_by_name_found(self, extension_manager, temp_extension_root, sample_manifest):
        """Test getting extension by name when it exists."""
        async def test():
            self.create_test_extension(temp_extension_root, sample_manifest)
            await extension_manager.load_extension("test-extension")
            
            record = extension_manager.get_extension_by_name("test-extension")
            assert record is not None
            assert record.manifest.name == "test-extension"
        
        asyncio.run(test())
    
    def test_get_extension_by_name_not_found(self, extension_manager):
        """Test getting extension by name when it doesn't exist."""
        record = extension_manager.get_extension_by_name("non-existent")
        assert record is None
    
    # Test Installation/Management
    @pytest.mark.asyncio
    async def test_install_extension_local_success(self, extension_manager, temp_extension_root, sample_manifest):
        """Test successful local extension installation."""
        # Create source extension
        source_dir = temp_extension_root / "source"
        source_dir.mkdir()
        self.create_test_extension(source_dir, sample_manifest)
        
        # Install extension
        success = await extension_manager.install_extension(
            extension_id="test-extension",
            version="1.0.0",
            source="local",
            path=str(source_dir / "test-extension"),
            user_id="test_user"
        )
        
        assert success is True
        # Verify extension was copied
        installed_path = temp_extension_root / "test-extension"
        assert installed_path.exists()
        assert (installed_path / "extension.json").exists()
    
    @pytest.mark.asyncio
    async def test_install_extension_local_missing_path(self, extension_manager):
        """Test local extension installation with missing path."""
        success = await extension_manager.install_extension(
            extension_id="test-extension",
            version="1.0.0",
            source="local",
            path=None
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_install_extension_already_exists(self, extension_manager, temp_extension_root, sample_manifest):
        """Test installing extension that already exists."""
        # Create existing extension
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Try to install again
        success = await extension_manager.install_extension(
            extension_id="test-extension",
            version="1.0.0",
            source="local",
            path=str(temp_extension_root / "test-extension")
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_remove_extension_success(self, extension_manager, temp_extension_root, sample_manifest):
        """Test successful extension removal."""
        # Create and load extension
        self.create_test_extension(temp_extension_root, sample_manifest)
        await extension_manager.load_extension("test-extension")
        
        # Remove extension
        success = await extension_manager.remove_extension("test-extension")
        
        assert success is True
        # Verify extension directory is removed
        assert not (temp_extension_root / "test-extension").exists()
        # Verify extension is not in registry
        assert extension_manager.registry.get_extension("test-extension") is None
    
    @pytest.mark.asyncio
    async def test_remove_extension_not_found(self, extension_manager):
        """Test removing non-existent extension."""
        success = await extension_manager.remove_extension("non-existent")
        assert success is True  # Should succeed even if not found
    
    @pytest.mark.asyncio
    async def test_enable_extension_success(self, extension_manager, temp_extension_root, sample_manifest):
        """Test enabling extension."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        record = await extension_manager.enable_extension("test-extension")
        assert record is not None
        assert record.status == ExtensionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_enable_extension_already_enabled(self, extension_manager, temp_extension_root, sample_manifest):
        """Test enabling already enabled extension."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Enable first time
        record1 = await extension_manager.enable_extension("test-extension")
        # Enable second time (should return existing)
        record2 = await extension_manager.enable_extension("test-extension")
        
        assert record1 is record2
    
    @pytest.mark.asyncio
    async def test_disable_extension_success(self, extension_manager, temp_extension_root, sample_manifest):
        """Test disabling extension."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Enable first
        await extension_manager.enable_extension("test-extension")
        assert extension_manager.registry.get_extension("test-extension") is not None
        
        # Disable
        await extension_manager.disable_extension("test-extension")
        assert extension_manager.registry.get_extension("test-extension") is None
    
    @pytest.mark.asyncio
    async def test_disable_extension_not_enabled(self, extension_manager):
        """Test disabling extension that's not enabled."""
        # Should not raise error
        await extension_manager.disable_extension("non-existent")
    
    # Test Error Handling
    @pytest.mark.asyncio
    async def test_load_extension_with_registry_error(self, extension_manager, temp_extension_root, sample_manifest):
        """Test loading extension when registry operations fail."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Mock registry to raise error
        with patch.object(extension_manager.registry, 'register_extension', side_effect=RuntimeError("Registry error")):
            with pytest.raises(RuntimeError):
                await extension_manager.load_extension("test-extension")
    
    @pytest.mark.asyncio
    async def test_discover_extensions_with_file_error(self, extension_manager, temp_extension_root):
        """Test discovery when file operations fail."""
        # Create directory that can't be read
        problem_dir = temp_extension_root / "problem"
        problem_dir.mkdir()
        
        # Mock iterdir to raise error
        with patch.object(Path, 'iterdir', side_effect=PermissionError("Access denied")):
            # Should not raise error, just log and continue
            manifests = await extension_manager.discover_extensions()
            assert isinstance(manifests, dict)
    
    # Test Monitoring
    @pytest.mark.asyncio
    async def test_start_monitoring(self, extension_manager):
        """Test starting extension monitoring."""
        with patch.object(extension_manager.resource_monitor, 'start_monitoring', new_callable=AsyncMock) as mock_start:
            await extension_manager.start_monitoring()
            mock_start.assert_called_once()
    
    # Test Private Methods
    @pytest.mark.asyncio
    async def test_find_extension_directory(self, extension_manager, temp_extension_root, sample_manifest):
        """Test finding extension directory."""
        self.create_test_extension(temp_extension_root, sample_manifest)
        
        # Access private method for testing
        ext_dir = await extension_manager._find_extension_directory("test-extension")
        assert ext_dir is not None
        assert ext_dir.name == "test-extension"
        assert ext_dir.exists()
    
    @pytest.mark.asyncio
    async def test_find_extension_directory_not_found(self, extension_manager):
        """Test finding non-existent extension directory."""
        ext_dir = await extension_manager._find_extension_directory("non-existent")
        assert ext_dir is None
    
    def test_get_extension_class_name(self, extension_manager):
        """Test extension class name generation."""
        assert extension_manager._get_extension_class_name("test-extension") == "TestExtension"
        assert extension_manager._get_extension_class_name("hello_world") == "HelloWorldExtension"
        assert extension_manager._get_extension_class_name("my-cool-extension") == "MyCoolExtension"