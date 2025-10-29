#!/usr/bin/env python3
"""
AI-Karen Test Execution Script

This script provides convenient ways to run organized tests with Poetry.
Usage examples:
    python run_tests.py --unit                 # Run all unit tests
    python run_tests.py --integration         # Run all integration tests
    python run_tests.py --auth                # Run auth-related tests
    python run_tests.py --fast                # Run fast tests only
    python run_tests.py --coverage            # Run with coverage
    python run_tests.py --category middleware # Run specific category
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle the output."""
    print(f"🚀 {description}")
    print(f"   Command: {' '.join(command)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run AI-Karen tests with organization")
    
    # Test type selection
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--manual", action="store_true", help="Run manual tests (use with caution)")
    
    # Category selection
    parser.add_argument("--category", help="Run tests from specific category (e.g., middleware, auth, ai)")
    parser.add_argument("--component", help="Run tests for specific component (e.g., memory, llm)")
    
    # Test markers
    parser.add_argument("--auth", action="store_true", help="Run auth-related tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--database", action="store_true", help="Run database tests")
    parser.add_argument("--llm", action="store_true", help="Run LLM tests")
    parser.add_argument("--memory", action="store_true", help="Run memory system tests")
    
    # Execution options
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (exclude slow marker)")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--failfast", action="store_true", help="Stop on first failure")
    
    # File selection
    parser.add_argument("files", nargs="*", help="Specific test files to run")
    
    args = parser.parse_args()
    
    # Build pytest command
    base_cmd = ["poetry", "run", "pytest"]
    
    # Add test paths based on selection
    test_paths = []
    
    if args.unit:
        test_paths.append("tests/unit")
    if args.integration:
        test_paths.append("tests/integration")
    if args.e2e:
        test_paths.append("tests/e2e")
    if args.performance:
        test_paths.append("tests/performance")
    if args.security:
        test_paths.append("tests/security")
    if args.manual:
        test_paths.append("tests/manual")
    
    # Category-based selection
    if args.category:
        category_paths = {
            "middleware": "tests/unit/middleware",
            "models": "tests/unit/models",
            "utils": "tests/unit/utils",
            "ai": "tests/unit/ai",
            "database": "tests/unit/database",
            "core": "tests/unit/core",
            "api": "tests/integration/api",
            "auth": "tests/integration/auth",
            "services": "tests/integration/services",
            "external": "tests/integration/external",
        }
        if args.category in category_paths:
            test_paths.append(category_paths[args.category])
        else:
            print(f"❌ Unknown category: {args.category}")
            print(f"Available categories: {', '.join(category_paths.keys())}")
            return 1
    
    # Component-based selection
    if args.component:
        # Search for test files matching the component
        test_paths.append(f"tests -k {args.component}")
    
    # Marker-based selection
    markers = []
    if args.auth:
        markers.append("auth")
    if args.api:
        markers.append("api")
    if args.database:
        markers.append("database")
    if args.llm:
        markers.append("llm")
    if args.memory:
        markers.append("memory")
    
    if markers:
        base_cmd.extend(["-m", " or ".join(markers)])
    
    # Fast tests (exclude slow)
    if args.fast:
        base_cmd.extend(["-m", "not slow"])
    
    # Coverage
    if args.coverage:
        base_cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    # Parallel execution
    if args.parallel:
        base_cmd.extend(["-n", "auto"])
    
    # Verbose output
    if args.verbose:
        base_cmd.append("-v")
    
    # Fail fast
    if args.failfast:
        base_cmd.append("-x")
    
    # Add test paths or files
    if args.files:
        test_paths.extend(args.files)
    elif not test_paths:
        # Default to all tests if none specified
        test_paths.append("tests")
    
    base_cmd.extend(test_paths)
    
    # Run the tests
    success = run_command(base_cmd, "Running tests")
    
    if args.coverage and success:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
