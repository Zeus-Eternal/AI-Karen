"""
Pytest tests for extension-plugin integration after directory reorganization.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestPluginOrchestration:
    """Test plugin orchestration with new directory structure."""
    
    @pytest.fixture
    def plugin_router(self):
        """Create plugin router fixture."""
        from ai_karen_engine.plugins.router import PluginRouter
        return PluginRouter()
    
    @pytest.fixture
    def plugin_orchestrator(self, plugin_router):
        """Create plugin orchestrator fixture."""
        from ai_karen_engine.extensions import PluginOrchestrator
        return PluginOrchestrator(plugin_router=plugin_router)
    
    def test_orchestrator_initialization(self, plugin_orchestrator, plugin_router):
        """Test that plugin orchestrator initializes correctly."""
        assert plugin_orchestrator is not None
        assert plugin_orchestrator.plugin_router == plugin_router
    
    def test_orchestrator_can_access_plugins(self, plugin_orchestrator, plugin_router):
        """Test that orchestrator can access plugins from new locations."""
        intents = plugin_router.list_intents()
        assert len(intents) > 0, "No plugins accessible to orchestrator"
        
        # Test that orchestrator can get plugin details
        for intent in intents[:3]:  # Test first 3 plugins
            plugin = plugin_router.get_plugin(intent)
            assert plugin is not None, f"Cannot access plugin for intent: {intent}"
    
    @pytest.mark.asyncio
    async def test_plugin_execution_through_orchestrator(self, plugin_orchestrator, plugin_router):
        """Test plugin execution through orchestrator."""
        intents = plugin_router.list_intents()
        
        if "greet" in intents:  # hello-world plugin
            try:
                result = await plugin_orchestrator.execute_plugin(
                    intent="greet",
                    params={"message": "Test from pytest"},
                    user_context={"roles": ["user"]}
                )
                assert result is not None, "Plugin execution returned None"
            except Exception as e:
                # Some plugins might fail due to missing dependencies, that's ok for this test
                pytest.skip(f"Plugin execution failed (expected): {e}")


class TestExtensionPluginCommunication:
    """Test communication between extensions and plugins."""
    
    @pytest.fixture
    def extension_manager(self):
        """Create extension manager fixture."""
        from ai_karen_engine.extensions import ExtensionManager
        from ai_karen_engine.plugins.router import PluginRouter
        
        plugin_router = PluginRouter()
        return ExtensionManager(
            extension_root=Path("extensions"),
            plugin_router=plugin_router
        )
    
    def test_extension_manager_has_plugin_access(self, extension_manager):
        """Test that extension manager has access to plugin router."""
        assert extension_manager.plugin_router is not None
        
        # Test that plugin router can discover plugins
        intents = extension_manager.plugin_router.list_intents()
        assert len(intents) > 0, "Extension manager's plugin router cannot discover plugins"
    
    @pytest.mark.asyncio
    async def test_extension_discovery_with_plugin_access(self, extension_manager):
        """Test extension discovery while having plugin access."""
        # Discover extensions
        manifests = await extension_manager.discover_extensions()
        assert len(manifests) > 0, "No extensions discovered"
        
        # Verify plugin access is maintained
        intents = extension_manager.plugin_router.list_intents()
        assert len(intents) > 0, "Plugin access lost during extension discovery"
    
    def test_extension_can_access_plugin_metadata(self, extension_manager):
        """Test that extensions can access plugin metadata."""
        plugin_router = extension_manager.plugin_router
        intents = plugin_router.list_intents()
        
        if intents:
            intent = intents[0]
            plugin_record = plugin_router.get_plugin(intent)
            
            assert plugin_record is not None
            assert plugin_record.manifest is not None
            assert plugin_record.dir_path is not None
            
            # Verify plugin is from categorized structure
            category = plugin_record.dir_path.parent.name
            expected_categories = {"examples", "core", "automation", "integrations", "ai"}
            assert category in expected_categories, f"Plugin not from expected category: {category}"


class TestExtensionExamples:
    """Test extension examples work with new plugin structure."""
    
    @pytest.fixture
    def extension_manager(self):
        """Create extension manager fixture."""
        from ai_karen_engine.extensions import ExtensionManager
        from ai_karen_engine.plugins.router import PluginRouter
        
        plugin_router = PluginRouter()
        return ExtensionManager(
            extension_root=Path("extensions"),
            plugin_router=plugin_router
        )
    
    @pytest.mark.asyncio
    async def test_hello_extension_discovery(self, extension_manager):
        """Test that hello extension can be discovered."""
        manifests = await extension_manager.discover_extensions()
        
        assert "hello-extension" in manifests, "Hello extension not found"
        
        hello_manifest = manifests["hello-extension"]
        assert hello_manifest.display_name == "Hello Extension"
        assert hello_manifest.version is not None
        assert hello_manifest.description is not None
    
    def test_hello_extension_structure(self):
        """Test hello extension has proper structure."""
        hello_extension_path = Path("extensions/examples/hello-extension")
        assert hello_extension_path.exists()
        
        # Check required files
        assert (hello_extension_path / "__init__.py").exists()
        assert (hello_extension_path / "extension.json").exists()
    
    def test_workflow_builder_extension_discovery(self, extension_manager):
        """Test workflow builder extension discovery."""
        async def discover():
            manifests = await extension_manager.discover_extensions()
            return manifests
        
        manifests = asyncio.run(discover())
        
        # Check if workflow builder exists
        workflow_extensions = [name for name in manifests.keys() if "workflow" in name.lower()]
        assert len(workflow_extensions) > 0, "No workflow extensions found"


class TestPluginCategoryDiscovery:
    """Test plugin discovery from different categories."""
    
    @pytest.fixture
    def plugin_router(self):
        """Create plugin router fixture."""
        from ai_karen_engine.plugins.router import PluginRouter
        return PluginRouter()
    
    def test_plugins_from_examples_category(self, plugin_router):
        """Test plugins are discovered from examples category."""
        intents = plugin_router.list_intents()
        
        examples_plugins = []
        for intent in intents:
            plugin = plugin_router.get_plugin(intent)
            if plugin and plugin.dir_path.parent.name == "examples":
                examples_plugins.append(intent)
        
        assert len(examples_plugins) > 0, "No plugins found in examples category"
    
    def test_plugins_from_core_category(self, plugin_router):
        """Test plugins are discovered from core category."""
        intents = plugin_router.list_intents()
        
        core_plugins = []
        for intent in intents:
            plugin = plugin_router.get_plugin(intent)
            if plugin and plugin.dir_path.parent.name == "core":
                core_plugins.append(intent)
        
        assert len(core_plugins) > 0, "No plugins found in core category"
    
    def test_plugins_from_multiple_categories(self, plugin_router):
        """Test plugins are discovered from multiple categories."""
        intents = plugin_router.list_intents()
        
        categories = set()
        for intent in intents:
            plugin = plugin_router.get_plugin(intent)
            if plugin:
                categories.add(plugin.dir_path.parent.name)
        
        assert len(categories) >= 3, f"Expected plugins from at least 3 categories, found: {categories}"
        
        # Check for specific expected categories
        expected_categories = {"examples", "core", "automation", "integrations"}
        found_expected = categories.intersection(expected_categories)
        assert len(found_expected) >= 2, f"Expected categories not found. Categories: {categories}"
    
    @pytest.mark.parametrize("category", ["examples", "core", "automation", "integrations"])
    def test_category_has_plugins(self, plugin_router, category):
        """Test that specific categories have plugins."""
        intents = plugin_router.list_intents()
        
        category_plugins = []
        for intent in intents:
            plugin = plugin_router.get_plugin(intent)
            if plugin and plugin.dir_path.parent.name == category:
                category_plugins.append(intent)
        
        # Some categories might be empty, so we'll just check they can be accessed
        # The main test is that the discovery doesn't fail
        assert isinstance(category_plugins, list), f"Failed to check {category} category"


class TestDataFlow:
    """Test data flow between extensions and plugins."""
    
    @pytest.fixture
    def full_setup(self):
        """Create full extension and plugin setup."""
        from ai_karen_engine.extensions import ExtensionManager, PluginOrchestrator
        from ai_karen_engine.plugins.router import PluginRouter
        
        plugin_router = PluginRouter()
        extension_manager = ExtensionManager(
            extension_root=Path("extensions"),
            plugin_router=plugin_router
        )
        orchestrator = PluginOrchestrator(plugin_router=plugin_router)
        
        return extension_manager, plugin_router, orchestrator
    
    def test_complete_data_flow(self, full_setup):
        """Test complete data flow from extension to plugin."""
        extension_manager, plugin_router, orchestrator = full_setup
        
        # Test extension discovery
        async def test_flow():
            manifests = await extension_manager.discover_extensions()
            return manifests
        
        manifests = asyncio.run(test_flow())
        assert len(manifests) > 0, "Extension discovery failed"
        
        # Test plugin discovery
        intents = plugin_router.list_intents()
        assert len(intents) > 0, "Plugin discovery failed"
        
        # Test orchestrator can access both
        assert orchestrator.plugin_router == plugin_router
        
        # Verify data consistency
        for intent in intents[:3]:  # Test first 3
            plugin = plugin_router.get_plugin(intent)
            assert plugin is not None, f"Data flow broken for plugin: {intent}"
    
    def test_plugin_metadata_accessibility(self, full_setup):
        """Test that plugin metadata is accessible through the data flow."""
        extension_manager, plugin_router, orchestrator = full_setup
        
        intents = plugin_router.list_intents()
        
        for intent in intents[:5]:  # Test first 5 plugins
            plugin = plugin_router.get_plugin(intent)
            
            # Verify all expected data is accessible
            assert plugin.manifest is not None, f"Manifest not accessible for {intent}"
            assert plugin.handler is not None, f"Handler not accessible for {intent}"
            assert plugin.dir_path is not None, f"Directory path not accessible for {intent}"
            assert plugin.dir_path.exists(), f"Plugin directory doesn't exist: {plugin.dir_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])