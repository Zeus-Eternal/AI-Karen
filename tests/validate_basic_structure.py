#!/usr/bin/env python3
"""
Basic validation of test structure without external dependencies.
"""

import sys
from pathlib import Path

def validate_file_structure():
    """Validate that all test files exist and have basic structure."""
    print("🔍 Validating Extension System Test File Structure")
    print("=" * 60)
    
    # Expected test files
    expected_files = [
        "tests/unit/extensions/__init__.py",
        "tests/unit/extensions/test_extension_manager.py",
        "tests/unit/extensions/test_base_extension.py",
        "tests/integration/extensions/__init__.py",
        "tests/integration/extensions/test_plugin_orchestration.py",
        "tests/security/extensions/__init__.py",
        "tests/security/extensions/test_tenant_isolation.py",
        "tests/security/extensions/test_permissions.py",
        "tests/performance/extensions/__init__.py",
        "tests/performance/extensions/test_resource_limits.py",
        "tests/performance/extensions/test_scaling.py",
        "tests/run_extension_tests.py",
        "tests/pytest_extensions.ini",
        "tests/requirements_test.txt",
        "tests/extensions/README.md",
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in expected_files:
        path = Path(file_path)
        if path.exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} (missing)")
    
    print(f"\n{'='*60}")
    print("FILE STRUCTURE SUMMARY")
    print(f"{'='*60}")
    print(f"Existing files: {len(existing_files)}")
    print(f"Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"\nMissing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    return len(missing_files) == 0

def validate_test_content():
    """Validate basic content structure of test files."""
    print(f"\n🔍 Validating Test Content Structure")
    print("=" * 60)
    
    test_files = [
        "tests/unit/extensions/test_extension_manager.py",
        "tests/unit/extensions/test_base_extension.py",
        "tests/integration/extensions/test_plugin_orchestration.py",
        "tests/security/extensions/test_tenant_isolation.py",
        "tests/security/extensions/test_permissions.py",
        "tests/performance/extensions/test_resource_limits.py",
        "tests/performance/extensions/test_scaling.py",
    ]
    
    content_checks = []
    
    for test_file in test_files:
        path = Path(test_file)
        if not path.exists():
            continue
            
        try:
            content = path.read_text()
            
            # Basic content checks
            has_imports = "import" in content
            has_test_class = "class Test" in content
            has_test_method = "def test_" in content
            has_docstring = '"""' in content
            has_async_test = "@pytest.mark.asyncio" in content
            
            checks = {
                "imports": has_imports,
                "test_class": has_test_class,
                "test_method": has_test_method,
                "docstring": has_docstring,
                "async_test": has_async_test
            }
            
            content_checks.append((test_file, checks))
            
            # Count test methods
            test_method_count = content.count("def test_")
            test_class_count = content.count("class Test")
            
            print(f"📋 {path.name}:")
            print(f"   Test classes: {test_class_count}")
            print(f"   Test methods: {test_method_count}")
            print(f"   Has imports: {'✅' if has_imports else '❌'}")
            print(f"   Has docstrings: {'✅' if has_docstring else '❌'}")
            print(f"   Has async tests: {'✅' if has_async_test else '❌'}")
            
        except Exception as e:
            print(f"❌ Error reading {test_file}: {e}")
            content_checks.append((test_file, {"error": str(e)}))
    
    return len(content_checks) > 0

def main():
    """Run all validations."""
    structure_valid = validate_file_structure()
    content_valid = validate_test_content()
    
    print(f"\n{'='*60}")
    print("OVERALL VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    if structure_valid and content_valid:
        print("🎉 Test structure validation completed successfully!")
        print("\nNext steps:")
        print("1. Install test dependencies: pip install -r tests/requirements_test.txt")
        print("2. Run tests: python tests/run_extension_tests.py")
        return 0
    else:
        print("⚠️  Test structure validation found issues!")
        return 1

if __name__ == "__main__":
    sys.exit(main())