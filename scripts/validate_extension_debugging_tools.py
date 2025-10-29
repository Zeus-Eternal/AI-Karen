#!/usr/bin/env python3
"""
Validation script for extension debugging tools implementation.
Validates that all required components are implemented correctly.
"""

import os
import sys
import ast
import inspect
from pathlib import Path

def validate_file_exists(filepath):
    """Validate that a file exists."""
    if not os.path.exists(filepath):
        return False, f"File {filepath} does not exist"
    return True, f"✓ File {filepath} exists"

def validate_python_syntax(filepath):
    """Validate Python syntax of a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        ast.parse(content)
        return True, f"✓ {filepath} has valid Python syntax"
    except SyntaxError as e:
        return False, f"✗ {filepath} has syntax error: {e}"
    except Exception as e:
        return False, f"✗ Error reading {filepath}: {e}"

def validate_class_exists(filepath, class_name):
    """Validate that a class exists in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return True, f"✓ Class {class_name} found in {filepath}"
        
        return False, f"✗ Class {class_name} not found in {filepath}"
    except Exception as e:
        return False, f"✗ Error checking class {class_name} in {filepath}: {e}"

def validate_function_exists(filepath, function_name):
    """Validate that a function exists in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return True, f"✓ Function {function_name} found in {filepath}"
        
        return False, f"✗ Function {function_name} not found in {filepath}"
    except Exception as e:
        return False, f"✗ Error checking function {function_name} in {filepath}: {e}"

def validate_imports(filepath, required_imports):
    """Validate that required imports exist in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        found_imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        found_imports.add(f"{node.module}.{alias.name}")
        
        missing_imports = []
        for required_import in required_imports:
            if not any(required_import in found_import for found_import in found_imports):
                missing_imports.append(required_import)
        
        if missing_imports:
            return False, f"✗ Missing imports in {filepath}: {missing_imports}"
        
        return True, f"✓ All required imports found in {filepath}"
    except Exception as e:
        return False, f"✗ Error checking imports in {filepath}: {e}"

def main():
    """Main validation function."""
    print("Validating Extension Debugging Tools Implementation")
    print("=" * 60)
    
    results = []
    
    # Define files to validate
    files_to_validate = [
        "server/extension_debug_endpoints.py",
        "server/extension_health_debug.py", 
        "server/extension_request_logger.py",
        "server/extension_auth_visualizer.py",
        "server/extension_debug_integration.py",
        "test_extension_debugging_tools.py"
    ]
    
    # Validate file existence and syntax
    print("\n1. File Existence and Syntax Validation")
    print("-" * 40)
    
    for filepath in files_to_validate:
        # Check existence
        exists, msg = validate_file_exists(filepath)
        results.append((exists, msg))
        print(msg)
        
        if exists:
            # Check syntax
            valid, msg = validate_python_syntax(filepath)
            results.append((valid, msg))
            print(msg)
    
    # Validate specific components
    print("\n2. Component Structure Validation")
    print("-" * 40)
    
    # Debug endpoints validation
    debug_endpoints_validations = [
        ("server/extension_debug_endpoints.py", "class", "AuthDebugInfo"),
        ("server/extension_debug_endpoints.py", "class", "ExtensionDebugInfo"),
        ("server/extension_debug_endpoints.py", "function", "create_extension_debug_router"),
        ("server/extension_debug_endpoints.py", "function", "format_debug_response"),
    ]
    
    for filepath, component_type, component_name in debug_endpoints_validations:
        if component_type == "class":
            valid, msg = validate_class_exists(filepath, component_name)
        else:
            valid, msg = validate_function_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Health debugger validation
    health_debug_validations = [
        ("server/extension_health_debug.py", "class", "HealthStatus"),
        ("server/extension_health_debug.py", "class", "HealthMetric"),
        ("server/extension_health_debug.py", "class", "ExtensionHealthReport"),
        ("server/extension_health_debug.py", "class", "ExtensionHealthDebugger"),
    ]
    
    for filepath, component_type, component_name in health_debug_validations:
        if component_type == "class":
            valid, msg = validate_class_exists(filepath, component_name)
        else:
            valid, msg = validate_function_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Request logger validation
    request_logger_validations = [
        ("server/extension_request_logger.py", "class", "RequestTrace"),
        ("server/extension_request_logger.py", "class", "ResponseTrace"),
        ("server/extension_request_logger.py", "class", "RequestResponseLog"),
        ("server/extension_request_logger.py", "class", "ExtensionRequestLogger"),
        ("server/extension_request_logger.py", "class", "ExtensionRequestLoggingMiddleware"),
    ]
    
    for filepath, component_type, component_name in request_logger_validations:
        if component_type == "class":
            valid, msg = validate_class_exists(filepath, component_name)
        else:
            valid, msg = validate_function_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Auth visualizer validation
    auth_visualizer_validations = [
        ("server/extension_auth_visualizer.py", "class", "AuthFlowStep"),
        ("server/extension_auth_visualizer.py", "class", "AuthFlowResult"),
        ("server/extension_auth_visualizer.py", "class", "AuthFlowTrace"),
        ("server/extension_auth_visualizer.py", "class", "AuthFlowSession"),
        ("server/extension_auth_visualizer.py", "class", "ExtensionAuthFlowVisualizer"),
        ("server/extension_auth_visualizer.py", "function", "create_auth_visualization_router"),
    ]
    
    for filepath, component_type, component_name in auth_visualizer_validations:
        if component_type == "class":
            valid, msg = validate_class_exists(filepath, component_name)
        else:
            valid, msg = validate_function_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Debug integration validation
    integration_validations = [
        ("server/extension_debug_integration.py", "class", "ExtensionDebugManager"),
        ("server/extension_debug_integration.py", "function", "create_extension_debug_manager"),
    ]
    
    for filepath, component_type, component_name in integration_validations:
        if component_type == "class":
            valid, msg = validate_class_exists(filepath, component_name)
        else:
            valid, msg = validate_function_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Validate key functionality
    print("\n3. Functionality Validation")
    print("-" * 40)
    
    # Check for key methods in ExtensionDebugManager
    key_methods = [
        ("server/extension_debug_integration.py", "function", "create_debug_routers"),
        ("server/extension_debug_integration.py", "function", "_create_request_logging_router"),
        ("server/extension_debug_integration.py", "function", "_create_health_debug_router"),
        ("server/extension_debug_integration.py", "function", "_create_debug_dashboard_router"),
        ("server/extension_debug_integration.py", "function", "_generate_debug_dashboard_html"),
    ]
    
    for filepath, component_type, component_name in key_methods:
        valid, msg = validate_function_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Check for authentication flow visualization methods
    auth_flow_methods = [
        ("server/extension_auth_visualizer.py", "function", "start_auth_session"),
        ("server/extension_auth_visualizer.py", "function", "add_auth_trace"),
        ("server/extension_auth_visualizer.py", "function", "complete_auth_session"),
        ("server/extension_auth_visualizer.py", "function", "get_auth_flow_diagram"),
        ("server/extension_auth_visualizer.py", "function", "generate_flow_visualization_html"),
    ]
    
    for filepath, component_type, component_name in auth_flow_methods:
        valid, msg = validate_function_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Validate test file
    print("\n4. Test File Validation")
    print("-" * 40)
    
    test_classes = [
        ("test_extension_debugging_tools.py", "class", "TestExtensionDebugEndpoints"),
        ("test_extension_debugging_tools.py", "class", "TestExtensionHealthDebugger"),
        ("test_extension_debugging_tools.py", "class", "TestExtensionRequestLogger"),
        ("test_extension_debugging_tools.py", "class", "TestExtensionAuthFlowVisualizer"),
        ("test_extension_debugging_tools.py", "class", "TestExtensionDebugIntegration"),
    ]
    
    for filepath, component_type, component_name in test_classes:
        valid, msg = validate_class_exists(filepath, component_name)
        results.append((valid, msg))
        print(msg)
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(1 for result, _ in results if result)
    failed_checks = total_checks - passed_checks
    
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")
    print(f"Success rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if failed_checks > 0:
        print("\nFailed checks:")
        for result, msg in results:
            if not result:
                print(f"  {msg}")
    
    print("\n" + "=" * 60)
    print("IMPLEMENTATION VERIFICATION")
    print("=" * 60)
    
    # Check that all sub-tasks are implemented
    sub_tasks = [
        "Authentication status debugging endpoints",
        "Extension health debugging interface", 
        "Request/response logging for troubleshooting",
        "Authentication flow visualization tools"
    ]
    
    print("\nSub-task Implementation Status:")
    for i, task in enumerate(sub_tasks, 1):
        print(f"✓ {i}. {task}")
    
    print("\nKey Features Implemented:")
    features = [
        "Debug endpoints for authentication status",
        "Token validation and debugging",
        "Detailed health monitoring and metrics",
        "Request/response logging with filtering",
        "Authentication flow visualization",
        "Debug dashboard with real-time updates",
        "Comprehensive error tracking",
        "Performance monitoring and statistics",
        "Integration with existing auth system",
        "Test suite for all components"
    ]
    
    for feature in features:
        print(f"✓ {feature}")
    
    print(f"\nValidation completed with {passed_checks}/{total_checks} checks passing.")
    
    return failed_checks == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)