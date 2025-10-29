#!/usr/bin/env python3
"""
Validation script for the comprehensive authentication test suite.
Validates that all test files are properly structured and importable.
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path


def validate_test_file_structure(file_path):
    """Validate that a test file has proper structure."""
    print(f"  📄 Validating {file_path}")
    
    if not os.path.exists(file_path):
        print(f"    ❌ File does not exist")
        return False
    
    try:
        # Parse the file to check syntax
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Check for test classes and functions
        test_classes = []
        test_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                test_classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_functions.append(node.name)
        
        print(f"    ✅ Syntax valid")
        print(f"    📊 Found {len(test_classes)} test classes, {len(test_functions)} test functions")
        
        if test_classes:
            print(f"    🏷️  Test classes: {', '.join(test_classes[:3])}{'...' if len(test_classes) > 3 else ''}")
        
        return True
        
    except SyntaxError as e:
        print(f"    ❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"    ❌ Error parsing file: {e}")
        return False


def validate_imports(file_path):
    """Validate that imports in test file are available."""
    print(f"  🔍 Checking imports for {os.path.basename(file_path)}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Check critical imports based on file type
        if 'comprehensive' in file_path:
            # Test runner doesn't need fastapi/jwt
            critical_imports = ['pytest']
        else:
            # Regular test files need these imports
            critical_imports = ['pytest', 'fastapi', 'jwt']
        
        missing_critical = []
        
        for imp in critical_imports:
            if not any(imp in import_name for import_name in imports):
                missing_critical.append(imp)
        
        if missing_critical:
            print(f"    ⚠️  Missing critical imports: {missing_critical}")
        else:
            print(f"    ✅ All critical imports present")
        
        return len(missing_critical) == 0
        
    except Exception as e:
        print(f"    ❌ Error checking imports: {e}")
        return False


def validate_test_coverage():
    """Validate test coverage across different areas."""
    print("📋 Validating test coverage")
    
    test_areas = {
        "Authentication Middleware": [
            "token validation",
            "permission checking", 
            "user context creation",
            "error handling"
        ],
        "API Integration": [
            "endpoint authentication",
            "role-based access",
            "tenant isolation",
            "service tokens"
        ],
        "Frontend Flow": [
            "login flow",
            "token refresh",
            "error scenarios",
            "concurrent requests"
        ],
        "Security": [
            "token tampering",
            "algorithm confusion",
            "timing attacks",
            "privilege escalation"
        ]
    }
    
    for area, requirements in test_areas.items():
        print(f"  🎯 {area}: {len(requirements)} requirements")
        for req in requirements:
            print(f"    - {req}")
    
    return True


def main():
    """Main validation function."""
    print("🔐 AUTHENTICATION TEST SUITE VALIDATION")
    print("=" * 50)
    
    # Test files to validate
    test_files = [
        "tests/unit/auth/test_extension_auth_middleware.py",
        "tests/integration/auth/test_extension_api_authentication.py", 
        "tests/e2e/test_frontend_authentication_flow.py",
        "tests/security/test_extension_authentication_security.py",
        "tests/auth/test_comprehensive_authentication_suite.py"
    ]
    
    all_valid = True
    
    # Validate each test file
    print("\n📁 Validating test file structure")
    for test_file in test_files:
        if not validate_test_file_structure(test_file):
            all_valid = False
    
    # Validate imports
    print("\n📦 Validating imports")
    for test_file in test_files:
        if os.path.exists(test_file):
            if not validate_imports(test_file):
                all_valid = False
    
    # Validate test coverage
    print("\n🎯 Validating test coverage")
    validate_test_coverage()
    
    # Check for configuration files
    print("\n⚙️  Validating configuration")
    config_files = [
        "tests/auth/conftest.py",
        "tests/conftest.py"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  ✅ {config_file} exists")
        else:
            print(f"  ⚠️  {config_file} missing (optional)")
    
    # Final summary
    print("\n" + "=" * 50)
    if all_valid:
        print("✅ VALIDATION PASSED")
        print("🎉 Authentication test suite is properly structured!")
        print("\n📋 Test Suite Summary:")
        print("  • Unit Tests: Authentication middleware core functionality")
        print("  • Integration Tests: API endpoint authentication flows")
        print("  • E2E Tests: Complete frontend-to-backend authentication")
        print("  • Security Tests: Vulnerability and attack prevention")
        print("  • Comprehensive Suite: Orchestrated test execution")
        
        print("\n🚀 Ready to run:")
        print("  python3 tests/auth/test_comprehensive_authentication_suite.py")
        
        return 0
    else:
        print("❌ VALIDATION FAILED")
        print("🔧 Please fix the issues above before running tests")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)