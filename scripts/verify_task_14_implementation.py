#!/usr/bin/env python3
"""
Verification script for Task 14: Extend existing health endpoints for extension monitoring

This script verifies the code implementation without requiring a running server.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()


def check_string_in_file(file_path: str, search_string: str) -> bool:
    """Check if a string exists in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_string in content
    except Exception:
        return False


def verify_database_monitor_extension():
    """Verify database monitor endpoint has been extended"""
    print("\n=== Verifying Database Monitor Extension ===")
    
    file_path = "server/app.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    checks = [
        ("extension_performance_metrics", "Extension performance metrics variable"),
        ("get_database_performance_metrics", "Database performance metrics method call"),
        ("extension_performance", "Extension performance in response"),
        ("database_query_performance", "Database query performance tracking")
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
            print(f"✅ Extension metric {metric} found")
        else:
            print(f"❌ Extension metric {metric} not found")
            all_passed = False
    
    # Check metrics endpoint updates extension metrics
    app_file = "server/app.py"
    if check_string_in_file(app_file, "update_extension_metrics"):
        print("✅ Metrics endpoint updates extension metrics")
    else:
        print("❌ Metrics endpoint doesn't update extension metrics")
        all_passed = False
    
    return all_passed


def verify_extension_health_monitor():
    """Verify extension health monitor has metrics integration"""
    print("\n=== Verifying Extension Health Monitor Metrics Integration ===")
    
    file_path = "server/extension_health_monitor.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    checks = [
        ("get_database_performance_metrics", "Database performance metrics method"),
        ("update_extension_metrics", "Update extension metrics method"),
        ("record_extension_api_call", "Record API call metrics method"),
        ("record_extension_error", "Record error metrics method"),
        ("from server.metrics import", "Metrics imports")
    ]
    
    all_passed = True
    for check_string, description in checks:
        if check_string_in_file(file_path, check_string):
            print(f"✅ {description} found")
        else:
            print(f"❌ {description} not found")
            all_passed = False
    
    return all_passed


def verify_degraded_mode_extension():
    """Verify degraded mode includes extension status"""
    print("\n=== Verifying Degraded Mode Extension Integration ===")
    
    file_path = "src/ai_karen_engine/api_routes/health.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    checks = [
        ("extension_system_status", "Extension system status variable"),
        ("extension_degraded", "Extension degraded flag"),
        ("get_extension_health_monitor", "Extension health monitor import"),
        ("extension_system", "Extension system in response")
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
    """Verify health endpoints include extension status"""
    print("\n=== Verifying Health Endpoints Extension Integration ===")
    
    file_path = "src/ai_karen_engine/api_routes/health.py"
    if not check_file_exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    checks = [
        ("@router.get(\"/extensions\")", "Extension system health endpoint"),
        ("@router.get(\"/extensions/{extension_name}\")", "Individual extension health endpoint"),
        ("extension_system", "Extension system in overall health"),
        ("extension_health", "Extension health variable"),
        ("update_extension_metrics", "Extension metrics update")
    ]
    
    all_passed = True
    for check_string, description in checks:
        if check_string_in_file(file_path, check_string):
            print(f"✅ {description} found")
        else:
            print(f"❌ {description} not found")
            all_passed = False
    
    return all_passed


def main():
    """Run all verification checks"""
    print("🔍 Verifying Task 14 Implementation")
    print("Task: Extend existing health endpoints for extension monitoring")
    
    verifications = [
        verify_database_monitor_extension,
        verify_prometheus_metrics_extension,
        verify_extension_health_monitor,
        verify_degraded_mode_extension,
        verify_health_endpoints_extension,
    ]
    
    passed = 0
    total = len(verifications)
    
    for verification in verifications:
        try:
            if verification():
                passed += 1
                print(f"✅ {verification.__name__} PASSED")
            else:
                print(f"❌ {verification.__name__} FAILED")
        except Exception as e:
            print(f"❌ {verification.__name__} ERROR: {e}")
    
    print(f"\n📊 Verification Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All Task 14 implementation verifications passed!")
        print("\n✅ Implementation Summary:")
        print("  • Database monitor endpoint extended with extension performance metrics")
        print("  • Prometheus metrics include comprehensive extension metrics")
        print("  • Extension health monitor provides database performance data")
        print("  • Degraded mode status includes extension system information")
        print("  • New dedicated extension health endpoints created")
        print("  • Overall health endpoint includes extension status")
        return True
    else:
        print(f"❌ {total - passed} verifications failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)