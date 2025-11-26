"""
Pytest tests for extension system organization validation after directory reorganization.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestExtensionSystemOrganization:
    """Test extension system code organization."""
    
    def test_extension_system_files_exist(self):
        """Test that all expected extension system files exist."""
        system_root = Path("src/ai_karen_engine/extensions")
        assert system_root.exists(), "Extension system directory not found"
        
        expected_files = [
            "__init__.py", "manager.py", "base.py", "registry.py", 
            "models.py", "orchestrator.py", "validator.py", "data_manager.py"
        ]
        
        for file_name in expected_files:
            file_path = system_root / file_name
            assert file_path.exists(), f"Missing system file: {file_name}"
    
    def test_extension_directory_structure(self):
        """Test that extension directory structure is properly organized."""
        extensions_root = Path("extensions")
        assert extensions_root.exists(), "Extensions root directory not found"
        
        # Check for expected category directories
        expected_categories = [
            "examples", "automation", "analytics", "communication", 
            "development", "integration", "productivity", "security"
        ]
        
        found_categories = []
        for category in expected_categories:
            category_path = extensions_root / category
            if category_path.exists() and category_path.is_dir():
                found_categories.append(category)
        
        assert len(found_categories) >= 6, f"Expected at least 6 categories, found {len(found_categories)}"
    
    def test_example_extension_exists(self):
        """Test that example extension exists with proper structure."""
        example_extension = Path("extensions/examples/hello-extension")
        assert example_extension.exists(), "Example extension not found"
        
        manifest_file = example_extension / "extension.json"
        assert manifest_file.exists(), "Example extension missing manifest"
        
        init_file = example_extension / "__init__.py"
        assert init_file.exists(), "Example extension missing __init__.py"


class TestExtensionSystemImports:
    """Test extension system imports work correctly."""
    
    def test_extension_system_imports(self):
        """Test that all extension system imports work correctly."""
        from ai_karen_engine.extension_host.__init__2 import ExtensionManager
        from ai_karen_engine.extension_host.__init__2 import BaseExtension
        from ai_karen_engine.extension_host.__init__2 import ExtensionRegistry
        from ai_karen_engine.extension_host.__init__2 import ExtensionManifest
        from ai_karen_engine.extension_host.__init__2 import PluginOrchestrator
        from ai_karen_engine.extension_host.__init__2 import ExtensionValidator
        
        # Verify classes are importable
        assert ExtensionManager is not None
        assert BaseExtension is not None
        assert ExtensionRegistry is not None
        assert ExtensionManifest is not None
        assert PluginOrchestrator is not None
        assert ExtensionValidator is not None
    
    def test_plugin_system_imports(self):
        """Test that plugin system imports work correctly."""
        from ai_karen_engine.plugins.router import PluginRouter
        from ai_karen_engine.plugins.manager import PluginManager
        
        assert PluginRouter is not None
        assert PluginManager is not None


class TestExtensionDiscovery:
    """Test extension discovery with categorized directory structure."""
    
    @pytest.fixture
    def extension_manager(self):
        """Create extension manager for testing."""
        from ai_karen_engine.extension_host.__init__2 import ExtensionManager
        from ai_karen_engine.plugins.router import PluginRouter
        
        plugin_router = PluginRouter()
        return ExtensionManager(
            extension_root=Path("extensions"),
            plugin_router=plugin_router
        )
    
    @pytest.mark.asyncio
    async def test_extension_discovery(self, extension_manager):
        """Test extension discovery works with categorized structure."""
        manifests = await extension_manager.discover_extensions()
        
        assert len(manifests) > 0, "No extensions discovered"
        
        # Check that hello-extension is found
        assert "hello-extension" in manifests, "Hello extension not discovered"
        
        # Verify manifest structure
        hello_manifest = manifests["hello-extension"]
        assert hasattr(hello_manifest, 'display_name')
        assert hasattr(hello_manifest, 'version')
        assert hasattr(hello_manifest, 'description')


class TestPluginDiscovery:
    """Test plugin discovery with categorized directory structure."""
    
    @pytest.fixture
    def plugin_router(self):
        """Create plugin router for testing."""
        from ai_karen_engine.plugins.router import PluginRouter
        return PluginRouter()
    
    def test_plugin_discovery(self, plugin_router):
        """Test plugin discovery works with categorized structure."""
        intents = plugin_router.list_intents()
        
        assert len(intents) > 0, "No plugins discovered"
        
        # Check for expected plugins from different categories
        expected_intents = ["greet", "time_query"]  # hello-world and time-query plugins
        found_expected = [intent for intent in expected_intents if intent in intents]
        
        assert len(found_expected) > 0, f"Expected plugins not found. Available: {intents}"
    
    def test_plugin_categories(self, plugin_router):
        """Test that plugins are discovered from multiple categories."""
        intents = plugin_router.list_intents()
        
        # Group plugins by category
        categories = set()
        for intent in intents:
            plugin = plugin_router.get_plugin(intent)
            if plugin:
                category = plugin.dir_path.parent.name
                categories.add(category)
        
        # Should have plugins from at least 3 different categories
        assert len(categories) >= 3, f"Expected plugins from at least 3 categories, found: {categories}"
        
        # Check for expected categories
        expected_categories = {"examples", "core", "automation", "integrations"}
        found_expected_categories = categories.intersection(expected_categories)
        
        assert len(found_expected_categories) >= 2, f"Expected categories not found. Found: {categories}"


class TestExtensionPluginIntegration:
    """Test extension-plugin integration."""
    
    @pytest.fixture
    def managers(self):
        """Create extension and plugin managers for testing."""
        from ai_karen_engine.extension_host.__init__2 import ExtensionManager
        from ai_karen_engine.plugins.router import PluginRouter
        
        plugin_router = PluginRouter()
        extension_manager = ExtensionManager(
            extension_root=Path("extensions"),
            plugin_router=plugin_router
        )
        
        return extension_manager, plugin_router
    
    def test_extension_has_plugin_access(self, managers):
        """Test that extension manager has access to plugin router."""
        extension_manager, plugin_router = managers
        
        assert extension_manager.plugin_router is not None
        assert extension_manager.plugin_router == plugin_router
    
    def test_plugin_orchestrator_creation(self, managers):
        """Test that plugin orchestrator can be created with new structure."""
        from ai_karen_engine.extension_host.__init__2 import PluginOrchestrator
        
        extension_manager, plugin_router = managers
        
        orchestrator = PluginOrchestrator(plugin_router=plugin_router)
        assert orchestrator is not None
        
        # Test that orchestrator can access plugins
        intents = plugin_router.list_intents()
        assert len(intents) > 0, "Plugin orchestrator cannot access plugins"
    
    def test_extension_plugin_data_flow(self, managers):
        """Test that extensions can access plugin data."""
        extension_manager, plugin_router = managers
        
        intents = plugin_router.list_intents()
        assert len(intents) > 0, "No plugins available for testing"
        
        # Get plugin details
        first_intent = intents[0]
        plugin_record = plugin_router.get_plugin(first_intent)
        
        assert plugin_record is not None, "Cannot access plugin record"
        assert plugin_record.manifest is not None, "Plugin manifest not accessible"
        assert plugin_record.handler is not None, "Plugin handler not accessible"
        assert plugin_record.dir_path is not None, "Plugin directory path not accessible"


class TestImportPathConsistency:
    """Test import path consistency after reorganization."""
    
    def test_extension_import_paths(self):
        """Test that extension import paths are consistent."""
        # Test direct imports
        from ai_karen_engine.extension_host.manager import ExtensionManager
        from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
        from ai_karen_engine.extensions.base import BaseExtension
        
        assert ExtensionManager is not None
        assert PluginOrchestrator is not None
        assert BaseExtension is not None
    
    def test_plugin_import_paths(self):
        """Test that plugin import paths are consistent."""
        from ai_karen_engine.plugins.router import PluginRouter
        from ai_karen_engine.plugins.manager import PluginManager
        
        assert PluginRouter is not None
        assert PluginManager is not None
    
    def test_no_circular_imports(self):
        """Test that there are no circular import issues."""
        # This test will fail if there are circular imports
        from ai_karen_engine.extension_host.__init__2 import (
            ExtensionManager, BaseExtension, PluginOrchestrator
        )
        from ai_karen_engine.plugins import PluginRouter
        
        # Create instances to ensure no circular dependencies
        plugin_router = PluginRouter()
        extension_manager = ExtensionManager(
            extension_root=Path("extensions"),
            plugin_router=plugin_router
        )
        orchestrator = PluginOrchestrator(plugin_router=plugin_router)
        
        assert extension_manager is not None
        assert orchestrator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])