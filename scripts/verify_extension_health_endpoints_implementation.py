#!/usr/bin/env python3
"""
Verification script for extension health monitoring endpoints implementation.

This script verifies the implementation of task 14: extending existing health endpoints
for extension monitoring by checking code structure and imports.

Requirements verified: 5.3, 5.4, 5.5, 10.1, 10.2
"""

import ast
import os
import sys
from pathlib import Path

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()

def check_function_in_file(file_path: str, function_name: str) -> bool:
    """Check if a function exists in a Python file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            tree = ast.parse(content)
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return True
        return False
    except Exception as e:
        print(f"Error checking function {function_name} in {file_path}: {e}")
        return False

def check_string_in_file(file_path: str, search_string: str) -> bool:
    """Check if a string exists in a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            return search_string in content
    except Exception as e:
        print(f"Error checking string '{search_string}' in {file_path}: {e}")
        return False

def verify_database_monitor_extension():
    """Verify database monitor endpoint includes extension status"""
    print("\n=== Verifying Database Monitor Extension Integration ===")
    
    file_path = "server/app.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Check for database monitor endpoint
    if check_string_in_file(file_path, "async def database_health_monitor"):
        print("✅ Database health monitor endpoint exists")
    else:
        print("❌ Database health monitor endpoint not found")
        return False
    
    # Check for extension system health integration
    checks = [
        ("extension_system_health", "Extension system health variable"),
        ("get_extension_health_monitor", "Extension health monitor import"),
        ("extension_system", "Extension system in response"),
        ("database_dependent_extensions", "Database-dependent extensions tracking")
    ]
    
    all_passed = True
    for check_string, description in checks:
        if check_string_in_file(file_path, check_string):
            print(f"✅ {description} found")
        else:
            print(f"❌ {description} not found")
            all_passed = False
    
    return all_passed

def verify_prometheus_metrics_extension():
    """Verify Prometheus metrics include extension metrics"""
    print("\n=== Verifying Prometheus Metrics Extension Integration ===")
    
    # Check metrics module
    metrics_file = "server/metrics.py"
    if not check_file_exists(metrics_file):
        print(f"❌ File not found: {metrics_file}")
        return False
    
    # Check for extension-specific metrics
    extension_metrics = [
        "EXTENSION_HEALTH_STATUS",
        "EXTENSION_RESPONSE_TIME", 
        "EXTENSION_BACKGROUND_TASKS",
        "EXTENSION_API_CALLS",
        "EXTENSION_ERRORS",
        "EXTENSION_UPTIME"
    ]
    
    all_passed = True
    for metric in extension_metrics:
        if check_string_in_file(metrics_file, metric):
            print(f"✅ Extension metric defined: {metric}")
        else:
            print(f"❌ Extension metric not found: {metric}")
            all_passed = False
    
    # Check metrics endpoint enhancement
    app_file = "server/app.py"
    if check_string_in_file(app_file, "extension_monitor.update_extension_metrics"):
        print("✅ Metrics endpoint enhanced with extension metrics")
    else:
        print("❌ Metrics endpoint not enhanced with extension metrics")
        all_passed = False
    
    return all_passed

def verify_extension_health_monitor():
    """Verify extension health monitor has metrics integration"""
    print("\n=== Verifying Extension Health Monitor Metrics Integration ===")
    
    file_path = "server/extension_health_monitor.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Check for metrics update methods
    methods = [
        ("update_extension_metrics", "Extension metrics update method"),
        ("record_extension_api_call", "Extension API call recording"),
        ("record_extension_error", "Extension error recording")
    ]
    
    all_passed = True
    for method, description in methods:
        if check_function_in_file(file_path, method):
            print(f"✅ {description} exists")
        else:
            print(f"❌ {description} not found")
            all_passed = False
    
    # Check for global functions
    global_functions = [
        "record_extension_api_call_global",
        "record_extension_error_global"
    ]
    
    for func in global_functions:
        if check_function_in_file(file_path, func):
            print(f"✅ Global function exists: {func}")
        else:
            print(f"❌ Global function not found: {func}")
            all_passed = False
    
    return all_passed

def verify_degraded_mode_extension():
    """Verify degraded mode status includes extension information"""
    print("\n=== Verifying Degraded Mode Extension Integration ===")
    
    file_path = "server/app.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Check for degraded mode endpoint
    if check_string_in_file(file_path, "async def degraded_mode_status"):
        print("✅ Degraded mode status endpoint exists")
    else:
        print("❌ Degraded mode status endpoint not found")
        return False
    
    # Check for extension integration in degraded mode
    checks = [
        ("extension_degraded_info", "Extension degraded info variable"),
        ("extension_system_status", "Extension system status in degraded mode"),
        ("degraded_extension_names", "Degraded extension names tracking"),
        ("extension_authentication_healthy", "Extension auth health in degraded mode"),
        ("extension_database_healthy", "Extension DB health in degraded mode")
    ]
    
    all_passed = True
    for check_string, description in checks:
        if check_string_in_file(file_path, check_string):
            print(f"✅ {description} found")
        else:
            print(f"❌ {description} not found")
            all_passed = False
    
    return all_passed

def verify_health_endpoints_extension():
    """Verify health endpoints include extension monitoring"""
    print("\n=== Verifying Health Endpoints Extension Integration ===")
    
    file_path = "server/health_endpoints.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Check for extension health check function
    if check_string_in_file(file_path, "_check_extension_system_health"):
        print("✅ Extension system health check function exists")
    else:
        print("❌ Extension system health check function not found")
        return False
    
    # Check for extension health integration in comprehensive health
    if check_string_in_file(file_path, "extension_system_health"):
        print("✅ Extension system health integrated in comprehensive health")
    else:
        print("❌ Extension system health not integrated in comprehensive health")
        return False
    
    # Check for extension-specific endpoints
    extension_endpoints = [
        "/api/health/extensions",
        "/api/health/extensions/{extension_name}"
    ]
    
    all_passed = True
    for endpoint in extension_endpoints:
        if check_string_in_file(file_path, endpoint):
            print(f"✅ Extension endpoint exists: {endpoint}")
        else:
            print(f"❌ Extension endpoint not found: {endpoint}")
            all_passed = False
    
    return all_passed

def verify_imports_and_dependencies():
    """Verify all necessary imports and dependencies are in place"""
    print("\n=== Verifying Imports and Dependencies ===")
    
    # Check metrics imports
    metrics_file = "server/metrics.py"
    if check_string_in_file(metrics_file, "from prometheus_client import"):
        print("✅ Prometheus client imports found")
    else:
        print("❌ Prometheus client imports not found")
        return False
    
    if check_string_in_file(metrics_file, "Gauge"):
        print("✅ Gauge metric type imported")
    else:
        print("❌ Gauge metric type not imported")
        return False
    
    # Check extension health monitor imports
    health_file = "server/extension_health_monitor.py"
    if check_string_in_file(health_file, "from server.metrics import"):
        print("✅ Metrics imports in extension health monitor")
    else:
        print("❌ Metrics imports not found in extension health monitor")
        return False
    
    return True

def run_all_verifications():
    """Run all verification checks"""
    print("🔍 Verifying Extension Health Endpoints Implementation")
    print("=" * 60)
    
    verifications = [
        verify_database_monitor_extension,
        verify_prometheus_metrics_extension,
        verify_extension_health_monitor,
        verify_degraded_mode_extension,
        verify_health_endpoints_extension,
        verify_imports_and_dependencies
    ]
    
    results = []
    for verification in verifications:
        try:
            result = verification()
            results.append(result)
        except Exception as e:
            print(f"❌ Verification failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total} verification checks")
    
    if passed == total:
        print("🎉 All verifications passed! Implementation appears complete.")
        return True
    else:
        print(f"⚠️  {total - passed} verification(s) failed. Review implementation.")
        return False

if __name__ == "__main__":
    success = run_all_verifications()
    sys.exit(0 if success else 1)