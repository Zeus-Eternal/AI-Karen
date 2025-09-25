#!/usr/bin/env python3
"""
Test script to validate extension loading with unified API endpoints.
Tests that extensions are properly loaded and validated with new API compatibility checks.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.extensions.endpoint_adapter import ExtensionEndpointAdapter
from ai_karen_engine.plugins.router import PluginRouter


def create_test_extension_manifest(name: str, endpoints: list = None, permissions: dict = None) -> Dict[str, Any]:
    """Create a test extension manifest."""
    return {
        "name": name,
        "version": "1.0.0",
        "display_name": f"Test {name.title()} Extension",
        "description": f"Test extension for {name} functionality",
        "author": "Test Author",
        "license": "MIT",
        "category": "development",
        "tags": ["test"],
        "api_version": "1.0",
        "kari_min_version": "0.4.0",
        "capabilities": {
            "provides_ui": False,
            "provides_api": bool(endpoints),
            "provides_background_tasks": False,
            "provides_webhooks": False
        },
        "dependencies": {
            "plugins": [],
            "extensions": [],
            "system_services": []
        },
        "permissions": permissions or {
            "data_access": [],
            "plugin_access": [],
            "system_access": [],
            "network_access": []
        },
        "resources": {
            "max_memory_mb": 256,
            "max_cpu_percent": 10,
            "max_disk_mb": 100,
            "enforcement_action": "default"
        },
        "ui": {
            "control_room_pages": [],
            "streamlit_pages": []
        },
        "api": {
            "endpoints": endpoints or []
        },
        "background_tasks": [],
        "marketplace": {
            "price": "free",
            "support_url": None,
            "documentation_url": None,
            "screenshots": []
        }
    }


def create_test_extension_code(name: str) -> str:
    """Create basic test extension Python code."""
    class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_")) + "Extension"
    
    return f'''"""
Test extension: {name}
"""

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionContext


class {class_name}(BaseExtension):
    """Test extension for validation."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.name = "{name}"
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info(f"Initializing {{self.name}} extension")
    
    async def shutdown(self) -> None:
        """Shutdown the extension."""
        self.logger.info(f"Shutting down {{self.name}} extension")
    
    def get_status(self) -> dict:
        """Get extension status."""
        return {{
            "name": self.name,
            "initialized": True,
            "test_extension": True
        }}
'''


async def create_test_extension_directory(temp_dir: Path, name: str, manifest: Dict[str, Any]) -> Path:
    """Create a test extension directory with manifest and code."""
    ext_dir = temp_dir / name
    ext_dir.mkdir(parents=True, exist_ok=True)
    
    # Write manifest
    manifest_path = ext_dir / "extension.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Write extension code
    init_path = ext_dir / "__init__.py"
    with open(init_path, 'w') as f:
        f.write(create_test_extension_code(name))
    
    return ext_dir


async def test_extension_loading_basic():
    """Test basic extension loading functionality."""
    print("Testing basic extension loading...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test extension
        manifest = create_test_extension_manifest("test-basic")
        await create_test_extension_directory(temp_path, "test-basic", manifest)
        
        # Initialize manager
        plugin_router = PluginRouter(plugin_root=Path("plugins"))
        manager = ExtensionManager(
            extension_root=temp_path,
            plugin_router=plugin_router
        )
        
        try:
            # Discover extensions
            manifests = await manager.discover_extensions()
            
            if "test-basic" in manifests:
                print("✅ Basic extension loading passed")
                return True
            else:
                print(f"❌ Basic extension loading failed - extension not discovered")
                return False
                
        except Exception as e:
            print(f"❌ Basic extension loading error: {e}")
            return False


async def test_unified_api_endpoint_extension():
    """Test extension with unified API endpoints."""
    print("Testing extension with unified API endpoints...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create extension with unified endpoints
        manifest = create_test_extension_manifest(
            "test-unified-api",
            endpoints=[
                {
                    "path": "/copilot/assist",
                    "methods": ["POST"]
                },
                {
                    "path": "/memory/search",
                    "methods": ["POST"]
                }
            ],
            permissions={
                "data_access": ["memory:read"],
                "system_access": ["chat:write"],
                "plugin_access": [],
                "network_access": []
            }
        )
        await create_test_extension_directory(temp_path, "test-unified-api", manifest)
        
        # Initialize manager
        plugin_router = PluginRouter(plugin_root=Path("plugins"))
        manager = ExtensionManager(
            extension_root=temp_path,
            plugin_router=plugin_router
        )
        
        try:
            # Discover extensions
            manifests = await manager.discover_extensions()
            
            if "test-unified-api" in manifests:
                # Check endpoint compatibility
                adapter = ExtensionEndpointAdapter()
                compatibility = adapter.validate_endpoint_compatibility(manifests["test-unified-api"])
                
                if compatibility["is_compatible"]:
                    print("✅ Unified API endpoint extension passed")
                    return True
                else:
                    print(f"❌ Unified API endpoint extension failed - compatibility issues: {compatibility['issues']}")
                    return False
            else:
                print(f"❌ Unified API endpoint extension failed - extension not discovered")
                return False
                
        except Exception as e:
            print(f"❌ Unified API endpoint extension error: {e}")
            return False


async def test_legacy_endpoint_detection():
    """Test detection of legacy endpoints in extensions."""
    print("Testing legacy endpoint detection...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create extension with legacy endpoints
        manifest = create_test_extension_manifest(
            "test-legacy-api",
            endpoints=[
                {
                    "path": "/ag_ui/memory/query",
                    "methods": ["POST"]
                },
                {
                    "path": "/memory_ag_ui/commit",
                    "methods": ["POST"]
                }
            ]
        )
        await create_test_extension_directory(temp_path, "test-legacy-api", manifest)
        
        # Initialize manager
        plugin_router = PluginRouter(plugin_root=Path("plugins"))
        manager = ExtensionManager(
            extension_root=temp_path,
            plugin_router=plugin_router
        )
        
        try:
            # Discover extensions
            manifests = await manager.discover_extensions()
            
            if "test-legacy-api" in manifests:
                # Check endpoint compatibility
                adapter = ExtensionEndpointAdapter()
                analysis = adapter.analyze_extension_endpoints(manifests["test-legacy-api"])
                
                if analysis["legacy_endpoints"] and analysis["migration_required"]:
                    print("✅ Legacy endpoint detection passed")
                    print(f"   Detected {len(analysis['legacy_endpoints'])} legacy endpoints")
                    return True
                else:
                    print(f"❌ Legacy endpoint detection failed - no legacy endpoints detected")
                    return False
            else:
                print(f"❌ Legacy endpoint detection failed - extension not discovered")
                return False
                
        except Exception as e:
            print(f"❌ Legacy endpoint detection error: {e}")
            return False


async def test_migration_guide_generation():
    """Test migration guide generation for extensions."""
    print("Testing migration guide generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create extension needing migration
        manifest = create_test_extension_manifest(
            "test-migration",
            endpoints=[
                {
                    "path": "/ag_ui/memory/legacy",
                    "methods": ["POST"]
                }
            ],
            permissions={
                "data_access": ["read", "write"],  # Missing memory:read, memory:write
                "system_access": [],
                "plugin_access": [],
                "network_access": []
            }
        )
        await create_test_extension_directory(temp_path, "test-migration", manifest)
        
        # Initialize manager
        plugin_router = PluginRouter(plugin_root=Path("plugins"))
        manager = ExtensionManager(
            extension_root=temp_path,
            plugin_router=plugin_router
        )
        
        try:
            # Discover extensions
            manifests = await manager.discover_extensions()
            
            if "test-migration" in manifests:
                # Generate migration guide
                adapter = ExtensionEndpointAdapter()
                guide = adapter.generate_migration_guide(manifests["test-migration"])
                
                # Check guide contains expected sections
                expected_sections = ["Migration Guide", "Legacy Endpoint Migration", "Recommendations"]
                has_sections = all(section in guide for section in expected_sections)
                
                if has_sections and len(guide) > 500:  # Reasonable guide length
                    print("✅ Migration guide generation passed")
                    print(f"   Generated guide with {len(guide)} characters")
                    return True
                else:
                    print(f"❌ Migration guide generation failed - incomplete guide")
                    print(f"   Guide length: {len(guide)}")
                    return False
            else:
                print(f"❌ Migration guide generation failed - extension not discovered")
                return False
                
        except Exception as e:
            print(f"❌ Migration guide generation error: {e}")
            return False


async def test_extension_validation_integration():
    """Test integration of extension validation with loading system."""
    print("Testing extension validation integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create extension with various validation scenarios
        manifest = create_test_extension_manifest(
            "test-validation",
            endpoints=[
                {
                    "path": "/memory/search",
                    "methods": ["POST"]
                }
            ],
            permissions={
                "data_access": ["admin"],  # High privilege
                "system_access": ["memory:read"],
                "plugin_access": [],
                "network_access": ["outbound_http"]  # Security concern
            }
        )
        # Add high resource limits
        manifest["resources"]["max_memory_mb"] = 2048
        manifest["resources"]["max_cpu_percent"] = 30
        
        await create_test_extension_directory(temp_path, "test-validation", manifest)
        
        # Initialize manager
        plugin_router = PluginRouter(plugin_root=Path("plugins"))
        manager = ExtensionManager(
            extension_root=temp_path,
            plugin_router=plugin_router
        )
        
        try:
            # Discover extensions (this triggers validation)
            manifests = await manager.discover_extensions()
            
            if "test-validation" in manifests:
                # Check that validation was performed
                validation_report = manager.validator.get_validation_report(manifests["test-validation"])
                
                # Should have warnings about security and resources
                has_warnings = len(validation_report["warnings"]) > 0
                has_recommendations = len(validation_report["recommendations"]) > 0
                
                if has_warnings and has_recommendations:
                    print("✅ Extension validation integration passed")
                    print(f"   Generated {len(validation_report['warnings'])} warnings")
                    print(f"   Generated {len(validation_report['recommendations'])} recommendations")
                    return True
                else:
                    print(f"❌ Extension validation integration failed - insufficient validation feedback")
                    return False
            else:
                print(f"❌ Extension validation integration failed - extension not discovered")
                return False
                
        except Exception as e:
            print(f"❌ Extension validation integration error: {e}")
            return False


async def test_multiple_extensions_loading():
    """Test loading multiple extensions with different API patterns."""
    print("Testing multiple extensions loading...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create multiple test extensions
        extensions = [
            ("unified-ext", [{"path": "/copilot/assist", "methods": ["POST"]}], {"system_access": ["chat:write"]}),
            ("legacy-ext", [{"path": "/ag_ui/memory", "methods": ["POST"]}], {"data_access": ["read"]}),
            ("mixed-ext", [
                {"path": "/memory/search", "methods": ["POST"]},
                {"path": "/legacy/old", "methods": ["GET"]}
            ], {"data_access": ["memory:read"], "system_access": ["chat:write"]})
        ]
        
        for name, endpoints, permissions in extensions:
            manifest = create_test_extension_manifest(name, endpoints, {"data_access": [], "system_access": [], "plugin_access": [], "network_access": [], **permissions})
            await create_test_extension_directory(temp_path, name, manifest)
        
        # Initialize manager
        plugin_router = PluginRouter(plugin_root=Path("plugins"))
        manager = ExtensionManager(
            extension_root=temp_path,
            plugin_router=plugin_router
        )
        
        try:
            # Discover all extensions
            manifests = await manager.discover_extensions()
            
            if len(manifests) == 3:
                # Analyze each extension
                adapter = ExtensionEndpointAdapter()
                results = {}
                
                for name, manifest in manifests.items():
                    analysis = adapter.analyze_extension_endpoints(manifest)
                    results[name] = analysis
                
                # Check results
                unified_count = sum(1 for r in results.values() if r["unified_endpoints"])
                legacy_count = sum(1 for r in results.values() if r["legacy_endpoints"])
                
                if unified_count >= 2 and legacy_count >= 2:  # mixed-ext has both
                    print("✅ Multiple extensions loading passed")
                    print(f"   Extensions with unified endpoints: {unified_count}")
                    print(f"   Extensions with legacy endpoints: {legacy_count}")
                    return True
                else:
                    print(f"❌ Multiple extensions loading failed - unexpected endpoint analysis")
                    return False
            else:
                print(f"❌ Multiple extensions loading failed - expected 3 extensions, found {len(manifests)}")
                return False
                
        except Exception as e:
            print(f"❌ Multiple extensions loading error: {e}")
            return False


async def main():
    """Run all extension loading tests."""
    print("🔍 Testing Extension Loading with Unified API")
    print("=" * 60)
    
    tests = [
        test_extension_loading_basic,
        test_unified_api_endpoint_extension,
        test_legacy_endpoint_detection,
        test_migration_guide_generation,
        test_extension_validation_integration,
        test_multiple_extensions_loading,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All extension loading tests passed!")
        print("✅ Extension loading system successfully updated for unified API")
        return True
    else:
        print("⚠️  Some tests failed - extension loading system needs attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)