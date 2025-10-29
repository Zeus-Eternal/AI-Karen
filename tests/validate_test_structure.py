#!/usr/bin/env python3
"""
Validate the test structure and imports without running full pytest.
This ensures the test files are properly structured and importable.
"""

import sys
import importlib.util
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def validate_test_file(test_file_path: Path) -> bool:
    """Validate that a test file can be imported and has proper structure."""
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        if spec is None or spec.loader is None:
            print(f"❌ Could not load spec for {test_file_path}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check for test classes
        test_classes = [name for name in dir(module) if name.startswith('Test')]
        if not test_classes:
            print(f"⚠️  No test classes found in {test_file_path}")
            return False
        
        # Check for test methods in each class
        total_test_methods = 0
        for class_name in test_classes:
            test_class = getattr(module, class_name)
            test_methods = [name for name in dir(test_class) if name.startswith('test_')]
            total_test_methods += len(test_methods)
            print(f"  📋 {class_name}: {len(test_methods)} test methods")
        
        print(f"✅ {test_file_path.name}: {len(test_classes)} test classes, {total_test_methods} test methods")
        return True
        
    except Exception as e:
        print(f"❌ Error validating {test_file_path}: {e}")
        return False

def main():
    """Validate all test files."""
    print("🔍 Validating Extension System Test Structure")
    print("=" * 60)
    
    # Test files to validate
    test_files = [
        "tests/unit/extensions/test_extension_manager.py",
        "tests/unit/extensions/test_base_extension.py",
        "tests/integration/extensions/test_plugin_orchestration.py",
        "tests/security/extensions/test_tenant_isolation.py",
        "tests/security/extensions/test_permissions.py",
        "tests/performance/extensions/test_resource_limits.py",
        "tests/performance/extensions/test_scaling.py",
    ]
    
    results = []
    
    for test_file_path in test_files:
        file_path = Path(test_file_path)
        if not file_path.exists():
            print(f"❌ Test file not found: {test_file_path}")
            results.append(False)
            continue
        
        print(f"\n📁 Validating {test_file_path}")
        success = validate_test_file(file_path)
        results.append(success)
    
    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All test files validated successfully!")
        return 0
    else:
        print(f"⚠️  {total - passed} test file(s) failed validation!")
        return 1

if __name__ == "__main__":
    sys.exit(main())