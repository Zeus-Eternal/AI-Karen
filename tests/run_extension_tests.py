#!/usr/bin/env python3
"""
Test runner for extension system comprehensive test suite.
Runs unit tests, integration tests, security tests, and performance tests.
"""

import sys
import subprocess
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_test_suite(test_path: str, test_name: str, verbose: bool = True) -> bool:
    """Run a test suite and return success status."""
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print(f"{'='*60}")
    
    cmd = ["python", "-m", "pytest", test_path, "-v"]
    if verbose:
        cmd.extend(["--tb=short", "--no-header"])
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=False, text=True)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n{test_name} completed in {duration:.2f} seconds")
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED")
            return True
        else:
            print(f"❌ {test_name} FAILED")
            return False
            
    except Exception as e:
        print(f"❌ {test_name} ERROR: {e}")
        return False


def main():
    """Run all extension system tests."""
    print("🧪 Extension System Comprehensive Test Suite")
    print("=" * 60)
    
    # Test suites to run
    test_suites = [
        ("tests/unit/extensions/", "Unit Tests - Extension Manager"),
        ("tests/unit/extensions/test_base_extension.py", "Unit Tests - Base Extension"),
        ("tests/integration/extensions/", "Integration Tests - Plugin Orchestration"),
        ("tests/security/extensions/", "Security Tests - Tenant Isolation & Permissions"),
        ("tests/performance/extensions/", "Performance Tests - Resource Limits & Scaling"),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_path, test_name in test_suites:
        success = run_test_suite(test_path, test_name)
        results.append((test_name, success))
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed_count = 0
    failed_count = 0
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<12} {test_name}")
        if success:
            passed_count += 1
        else:
            failed_count += 1
    
    print(f"\nTotal Duration: {total_duration:.2f} seconds")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(results)}")
    
    if failed_count == 0:
        print("\n🎉 All test suites passed!")
        return 0
    else:
        print(f"\n⚠️  {failed_count} test suite(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())