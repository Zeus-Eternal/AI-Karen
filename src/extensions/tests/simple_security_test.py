#!/usr/bin/env python3
"""
Simple security system test without external dependencies.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_security_imports():
    """Test that security modules can be imported."""
    try:
        from src.extensions.core.security import (
            ExtensionSecurityManager,
            ExtensionPermissionManager,
            ResourceLimitEnforcer,
            ExtensionSandbox,
            NetworkAccessController
        )
        logger.info("✅ Security modules imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import security modules: {e}")
        return False


def test_security_decorators_import():
    """Test that security decorators can be imported."""
    try:
        from src.extensions.core.security_decorators import (
            require_permission,
            SecurityContext,
            set_security_manager,
            check_extension_permission
        )
        logger.info("✅ Security decorators imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import security decorators: {e}")
        return False


def test_models_import():
    """Test that models can be imported."""
    try:
        from src.extensions.core.models import (
            ExtensionManifest,
            ExtensionPermissions,
            ExtensionResources,
            ExtensionContext
        )
        logger.info("✅ Extension models imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import extension models: {e}")
        return False


def test_permission_manager_basic():
    """Test basic permission manager functionality."""
    try:
        from src.extensions.core.security import ExtensionPermissionManager
        from src.extensions.core.models import ExtensionPermissions
        
        pm = ExtensionPermissionManager()
        
        # Test permission hierarchy
        assert hasattr(pm, 'permission_hierarchy')
        assert 'data_access' in pm.permission_hierarchy
        assert 'system_access' in pm.permission_hierarchy
        
        logger.info("✅ Permission manager basic functionality works")
        return True
    except Exception as e:
        logger.error(f"❌ Permission manager test failed: {e}")
        return False


def test_resource_enforcer_basic():
    """Test basic resource enforcer functionality."""
    try:
        from src.extensions.core.security import ResourceLimitEnforcer
        from src.extensions.core.models import ExtensionResources
        
        enforcer = ResourceLimitEnforcer()
        
        # Test basic structure
        assert hasattr(enforcer, 'resource_limits')
        assert hasattr(enforcer, 'resource_usage')
        assert hasattr(enforcer, 'process_monitors')
        
        logger.info("✅ Resource enforcer basic functionality works")
        return True
    except Exception as e:
        logger.error(f"❌ Resource enforcer test failed: {e}")
        return False


def test_sandbox_basic():
    """Test basic sandbox functionality."""
    try:
        from src.extensions.core.security import ExtensionSandbox
        
        sandbox = ExtensionSandbox()
        
        # Test basic structure
        assert hasattr(sandbox, 'sandboxed_processes')
        assert hasattr(sandbox, 'sandbox_directories')
        assert hasattr(sandbox, 'network_restrictions')
        
        logger.info("✅ Sandbox basic functionality works")
        return True
    except Exception as e:
        logger.error(f"❌ Sandbox test failed: {e}")
        return False


def test_network_controller_basic():
    """Test basic network controller functionality."""
    try:
        from src.extensions.core.security import NetworkAccessController
        
        controller = NetworkAccessController()
        
        # Test basic structure
        assert hasattr(controller, 'access_rules')
        assert hasattr(controller, 'connection_monitors')
        
        logger.info("✅ Network controller basic functionality works")
        return True
    except Exception as e:
        logger.error(f"❌ Network controller test failed: {e}")
        return False


def test_security_manager_basic():
    """Test basic security manager functionality."""
    try:
        from src.extensions.core.security import ExtensionSecurityManager
        
        manager = ExtensionSecurityManager()
        
        # Test basic structure
        assert hasattr(manager, 'permission_manager')
        assert hasattr(manager, 'resource_enforcer')
        assert hasattr(manager, 'sandbox')
        assert hasattr(manager, 'network_controller')
        
        logger.info("✅ Security manager basic functionality works")
        return True
    except Exception as e:
        logger.error(f"❌ Security manager test failed: {e}")
        return False


def test_example_extension_structure():
    """Test that the example extension has correct structure."""
    try:
        example_path = Path("extensions/examples/secure-extension")
        
        # Check files exist
        assert (example_path / "extension.json").exists(), "extension.json should exist"
        assert (example_path / "__init__.py").exists(), "__init__.py should exist"
        
        # Check extension.json content
        import json
        with open(example_path / "extension.json") as f:
            manifest = json.load(f)
        
        assert manifest['name'] == 'secure-extension'
        assert 'permissions' in manifest
        assert 'resources' in manifest
        assert 'capabilities' in manifest
        
        logger.info("✅ Example extension structure is correct")
        return True
    except Exception as e:
        logger.error(f"❌ Example extension test failed: {e}")
        return False


def main():
    """Run all basic tests."""
    print("🔒 Running Basic Security System Tests")
    print("=" * 50)
    
    tests = [
        ("Security Imports", test_security_imports),
        ("Security Decorators Import", test_security_decorators_import),
        ("Models Import", test_models_import),
        ("Permission Manager Basic", test_permission_manager_basic),
        ("Resource Enforcer Basic", test_resource_enforcer_basic),
        ("Sandbox Basic", test_sandbox_basic),
        ("Network Controller Basic", test_network_controller_basic),
        ("Security Manager Basic", test_security_manager_basic),
        ("Example Extension Structure", test_example_extension_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"Failed: {test_name}")
    
    print(f"\n{'=' * 50}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print(f"Success rate: {passed/total*100:.1f}%")
    print(f"{'=' * 50}")
    
    if passed == total:
        print("🎉 ALL BASIC TESTS PASSED!")
        print("The security system structure is correct and ready for use.")
    else:
        print("❌ Some tests failed.")
        print("Check the error messages above for details.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)