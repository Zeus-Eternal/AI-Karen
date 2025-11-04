#!/usr/bin/env python3
"""
Test runner for error recovery testing suite.

Runs all error recovery tests with proper configuration and reporting.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def run_test_suite(test_type="all", verbose=False, coverage=False, parallel=False):
    """Run the error recovery test suite."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directories based on type
    test_dirs = []
    if test_type in ["all", "unit"]:
        test_dirs.append("tests/unit/error_recovery/")
    if test_type in ["all", "integration"]:
        test_dirs.append("tests/integration/error_recovery/")
    if test_type in ["all", "performance"]:
        test_dirs.append("tests/performance/error_recovery/")
    if test_type in ["all", "reliability"]:
        test_dirs.append("tests/reliability/error_recovery/")
    
    # Add test directories to command
    cmd.extend(test_dirs)
    
    # Add pytest options
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=server/extension_error_recovery_manager",
            "--cov=ui_launchers/KAREN-Theme-Default/src/lib/graceful-degradation",
            "--cov-report=html:htmlcov/error_recovery",
            "--cov-report=term-missing"
        ])
    
    # Add parallel execution if requested
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add markers based on test type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif test_type == "reliability":
        cmd.extend(["-m", "reliability"])
    
    # Add output options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print(f"Running error recovery tests: {test_type}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the tests
    start_time = time.time()
    result = subprocess.run(cmd, cwd=project_root)
    end_time = time.time()
    
    print("-" * 60)
    print(f"Tests completed in {end_time - start_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    return result.returncode


def run_specific_test(test_file, test_function=None, verbose=False):
    """Run a specific test file or function."""
    
    cmd = ["python", "-m", "pytest"]
    
    # Add specific test
    if test_function:
        cmd.append(f"{test_file}::{test_function}")
    else:
        cmd.append(test_file)
    
    # Add options
    if verbose:
        cmd.extend(["-v", "-s"])
    
    cmd.extend(["--tb=long"])
    
    print(f"Running specific test: {test_file}")
    if test_function:
        print(f"Function: {test_function}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the test
    result = subprocess.run(cmd, cwd=project_root)
    
    print("-" * 60)
    print(f"Exit code: {result.returncode}")
    
    return result.returncode


def validate_test_environment():
    """Validate that the test environment is properly set up."""
    
    print("Validating test environment...")
    
    # Check required directories exist
    required_dirs = [
        "tests/unit/error_recovery",
        "tests/integration/error_recovery", 
        "tests/performance/error_recovery",
        "tests/reliability/error_recovery",
        "server",
        "ui_launchers/KAREN-Theme-Default/src/lib"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print("❌ Missing required directories:")
        for dir_path in missing_dirs:
            print(f"  - {dir_path}")
        return False
    
    # Check required test files exist
    required_files = [
        "tests/unit/error_recovery/test_error_recovery_strategies.py",
        "tests/integration/error_recovery/test_graceful_degradation.py",
        "tests/performance/error_recovery/test_error_handling_performance.py",
        "tests/reliability/error_recovery/test_recovery_reliability.py",
        "tests/error_recovery/conftest.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required test files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    # Check Python dependencies
    try:
        import pytest
        import asyncio
        import aiohttp
        import psutil
        print("✅ Required Python packages are available")
    except ImportError as e:
        print(f"❌ Missing required Python package: {e}")
        return False
    
    print("✅ Test environment validation passed")
    return True


def generate_test_report():
    """Generate a comprehensive test report."""
    
    print("Generating comprehensive test report...")
    
    # Run all test types and collect results
    test_results = {}
    
    test_types = ["unit", "integration", "performance", "reliability"]
    
    for test_type in test_types:
        print(f"\nRunning {test_type} tests...")
        start_time = time.time()
        
        result_code = run_test_suite(
            test_type=test_type,
            verbose=False,
            coverage=True
        )
        
        end_time = time.time()
        
        test_results[test_type] = {
            "exit_code": result_code,
            "duration": end_time - start_time,
            "passed": result_code == 0
        }
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("ERROR RECOVERY TEST SUITE SUMMARY")
    print("=" * 80)
    
    total_duration = sum(result["duration"] for result in test_results.values())
    passed_tests = sum(1 for result in test_results.values() if result["passed"])
    total_tests = len(test_results)
    
    print(f"Total test suites: {total_tests}")
    print(f"Passed test suites: {passed_tests}")
    print(f"Failed test suites: {total_tests - passed_tests}")
    print(f"Total duration: {total_duration:.2f} seconds")
    print()
    
    for test_type, result in test_results.items():
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{test_type.upper():12} | {status} | {result['duration']:6.2f}s")
    
    print("=" * 80)
    
    # Overall result
    if passed_tests == total_tests:
        print("🎉 ALL ERROR RECOVERY TESTS PASSED!")
        return 0
    else:
        print("💥 SOME ERROR RECOVERY TESTS FAILED!")
        return 1


def main():
    """Main entry point for the test runner."""
    
    parser = argparse.ArgumentParser(description="Error Recovery Test Runner")
    
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "performance", "reliability"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Enable coverage reporting"
    )
    
    parser.add_argument(
        "--parallel", "-n",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate test environment only"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )
    
    parser.add_argument(
        "--function",
        help="Run specific test function (requires --file)"
    )
    
    args = parser.parse_args()
    
    # Validate environment first
    if not validate_test_environment():
        print("❌ Test environment validation failed")
        return 1
    
    if args.validate:
        print("✅ Test environment validation completed")
        return 0
    
    # Run specific test if requested
    if args.file:
        return run_specific_test(args.file, args.function, args.verbose)
    
    # Generate comprehensive report if requested
    if args.report:
        return generate_test_report()
    
    # Run test suite
    return run_test_suite(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel
    )


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)