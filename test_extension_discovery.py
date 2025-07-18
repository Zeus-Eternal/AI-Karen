#!/usr/bin/env python3
"""
Test script to validate extension system organization and discovery.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.plugins.router import PluginRouter


async def test_extension_discovery():
    """Test that extension discovery works with categorized structure."""
    print("Testing extension discovery...")
    
    # Initialize with extensions directory
    extension_root = Path("extensions")
    # Use the correct plugin root path for the reorganized structure
    plugin_root = Path("plugins")
    plugin_router = PluginRouter(plugin_root=plugin_root)
    
    manager = ExtensionManager(
        extension_root=extension_root,
        plugin_router=plugin_router
    )
    
    # Discover extensions
    manifests = await manager.discover_extensions()
    
    print(f"Discovered {len(manifests)} extensions:")
    for name, manifest in manifests.items():
        print(f"  - {name}: {manifest.display_name} (category: {manifest.category})")
    
    # Verify we found the hello-extension
    assert "hello-extension" in manifests, "Should find hello-extension in examples category"
    
    hello_manifest = manifests["hello-extension"]
    assert hello_manifest.category == "example", "Hello extension should be in example category"
    assert hello_manifest.display_name == "Hello Extension", "Should have correct display name"
    
    print("✅ Extension discovery test passed!")
    return True


def test_extension_system_imports():
    """Test that extension system imports work correctly."""
    print("Testing extension system imports...")
    
    try:
        from ai_karen_engine.extensions import ExtensionManager
        from ai_karen_engine.extensions import BaseExtension
        from ai_karen_engine.extensions import ExtensionRegistry
        from ai_karen_engine.extensions import PluginOrchestrator
        from ai_karen_engine.extensions import ExtensionValidator
        
        print("✅ All extension system imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_extension_directory_structure():
    """Test that extension directory structure is properly organized."""
    print("Testing extension directory structure...")
    
    extension_root = Path("extensions")
    
    # Check that extensions directory exists
    assert extension_root.exists(), "Extensions directory should exist"
    
    # Check for expected category directories
    expected_categories = [
        "examples", "automation", "analytics", "communication", 
        "development", "integration", "productivity", "security"
    ]
    
    for category in expected_categories:
        category_path = extension_root / category
        assert category_path.exists(), f"Category directory {category} should exist"
    
    # Check that hello-extension exists in examples
    hello_extension = extension_root / "examples" / "hello-extension"
    assert hello_extension.exists(), "Hello extension should exist in examples"
    
    # Check that it has required files
    assert (hello_extension / "extension.json").exists(), "Should have extension.json"
    assert (hello_extension / "__init__.py").exists(), "Should have __init__.py"
    
    print("✅ Extension directory structure test passed!")
    return True


async def main():
    """Run all validation tests."""
    print("🔍 Validating Extension System Organization")
    print("=" * 50)
    
    tests = [
        test_extension_system_imports,
        test_extension_directory_structure,
        test_extension_discovery,
    ]
    
    results = []
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All extension system validation tests passed!")
        return True
    else:
        print("⚠️  Some tests failed - extension system needs attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)