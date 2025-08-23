#!/usr/bin/env python3
"""
Comprehensive Test Runner for Session Persistence and Premium Response System

This script runs all tests related to the session persistence and premium response
implementation, including unit tests, integration tests, end-to-end tests, and
load tests.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime


class TestRunner:
    """Comprehensive test runner with reporting and analysis."""
    
    def __init__(self, verbose: bool = False, parallel: bool = True):
        self.verbose = verbose
        self.parallel = parallel
        self.results: Dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
        
        # Test categories and their files
        self.test_categories = {
            "unit_tests": [
                "tests/test_auth_session_routes.py",
                "tests/test_error_response_service.py",
                "tests/test_session_persistence_middleware.py",
                "tests/test_audit_logging.py",
                "tests/test_security_enhancements.py"
            ],
            "integration_tests": [
                "tests/integration/test_intelligent_response_quality.py",
                "tests/test_error_response_integration.py",
                "tests/test_middleware_integration.py",
                "tests/test_audit_logging_integration.py"
            ],
            "e2e_tests": [
                "tests/e2e/test_session_persistence_e2e.py"
            ],
            "load_tests": [
                "tests/load/test_auth_load_testing.py"
            ]
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories and return comprehensive results."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Run each test category
        for category, test_files in self.test_categories.items():
            print(f"\n📋 Running {category.replace('_', ' ').title()}")
            print("-" * 40)
            
            category_results = self._run_test_category(category, test_files)
            self.results[category] = category_results
            
            # Print category summary
            self._print_category_summary(category, category_results)
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        self._generate_final_report()
        
        return self.results
    
    def _run_test_category(self, category: str, test_files: List[str]) -> Dict[str, Any]:
        """Run tests in a specific category."""
        category_results = {
            "files": {},
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "duration": 0,
            "coverage": None
        }
        
        start_time = time.time()
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                print(f"⚠️  Test file not found: {test_file}")
                continue
            
            print(f"  🧪 Running {test_file}")
            
            file_results = self._run_single_test_file(test_file, category)
            category_results["files"][test_file] = file_results
            
            # Aggregate results
            category_results["total_tests"] += file_results.get("total", 0)
            category_results["passed"] += file_results.get("passed", 0)
            category_results["failed"] += file_results.get("failed", 0)
            category_results["skipped"] += file_results.get("skipped", 0)
            
            if file_results.get("errors"):
                category_results["errors"].extend(file_results["errors"])
        
        category_results["duration"] = time.time() - start_time
        
        # Run coverage analysis for unit tests
        if category == "unit_tests":
            category_results["coverage"] = self._run_coverage_analysis(test_files)
        
        return category_results
    
    def _run_single_test_file(self, test_file: str, category: str) -> Dict[str, Any]:
        """Run a single test file and parse results."""
        
        # Build pytest command
        cmd = ["python", "-m", "pytest", test_file, "-v", "--tb=short"]
        
        # Add category-specific options
        if category == "load_tests":
            cmd.extend(["-s", "--disable-warnings"])  # Show output for load tests
        elif category == "e2e_tests":
            cmd.extend(["--tb=long"])  # More detailed output for e2e tests
        
        # Add parallel execution for unit tests
        if category == "unit_tests" and self.parallel:
            cmd.extend(["-n", "auto"])
        
        # Add JSON output for parsing
        json_report = f"/tmp/pytest_report_{category}_{int(time.time())}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report}"])
        
        try:
            # Run the test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300 if category != "load_tests" else 600  # Longer timeout for load tests
            )
            
            # Parse JSON report if available
            if os.path.exists(json_report):
                with open(json_report, 'r') as f:
                    json_data = json.load(f)
                
                file_results = {
                    "total": json_data.get("summary", {}).get("total", 0),
                    "passed": json_data.get("summary", {}).get("passed", 0),
                    "failed": json_data.get("summary", {}).get("failed", 0),
                    "skipped": json_data.get("summary", {}).get("skipped", 0),
                    "duration": json_data.get("duration", 0),
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "errors": []
                }
                
                # Extract error details
                if json_data.get("tests"):
                    for test in json_data["tests"]:
                        if test.get("outcome") in ["failed", "error"]:
                            file_results["errors"].append({
                                "test": test.get("nodeid", "unknown"),
                                "message": test.get("call", {}).get("longrepr", "No details")
                            })
                
                # Clean up JSON report
                os.remove(json_report)
                
            else:
                # Fallback parsing from stdout
                file_results = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
            
            if self.verbose:
                print(f"    ✅ {file_results['passed']} passed, ❌ {file_results['failed']} failed, ⏭️ {file_results['skipped']} skipped")
            
            return file_results
            
        except subprocess.TimeoutExpired:
            print(f"    ⏰ Test timed out: {test_file}")
            return {
                "total": 0, "passed": 0, "failed": 1, "skipped": 0,
                "duration": 300, "return_code": -1,
                "errors": [{"test": test_file, "message": "Test timed out"}]
            }
        
        except Exception as e:
            print(f"    💥 Error running test: {e}")
            return {
                "total": 0, "passed": 0, "failed": 1, "skipped": 0,
                "duration": 0, "return_code": -1,
                "errors": [{"test": test_file, "message": str(e)}]
            }
    
    def _parse_pytest_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output when JSON report is not available."""
        results = {
            "total": 0, "passed": 0, "failed": 0, "skipped": 0,
            "duration": 0, "return_code": return_code,
            "stdout": stdout, "stderr": stderr, "errors": []
        }
        
        # Parse summary line (e.g., "5 passed, 2 failed, 1 skipped in 10.5s")
        lines = stdout.split('\n')
        for line in lines:
            if ' passed' in line or ' failed' in line or ' skipped' in line:
                # Extract numbers
                import re
                passed_match = re.search(r'(\d+) passed', line)
                failed_match = re.search(r'(\d+) failed', line)
                skipped_match = re.search(r'(\d+) skipped', line)
                duration_match = re.search(r'in ([\d.]+)s', line)
                
                if passed_match:
                    results["passed"] = int(passed_match.group(1))
                if failed_match:
                    results["failed"] = int(failed_match.group(1))
                if skipped_match:
                    results["skipped"] = int(skipped_match.group(1))
                if duration_match:
                    results["duration"] = float(duration_match.group(1))
                
                results["total"] = results["passed"] + results["failed"] + results["skipped"]
                break
        
        return results
    
    def _run_coverage_analysis(self, test_files: List[str]) -> Optional[Dict[str, Any]]:
        """Run coverage analysis for unit tests."""
        try:
            # Run tests with coverage
            cmd = [
                "python", "-m", "pytest",
                "--cov=src/ai_karen_engine",
                "--cov-report=json:/tmp/coverage.json",
                "--cov-report=term-missing"
            ] + test_files
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Parse coverage report
            if os.path.exists("/tmp/coverage.json"):
                with open("/tmp/coverage.json", 'r') as f:
                    coverage_data = json.load(f)
                
                os.remove("/tmp/coverage.json")
                
                return {
                    "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                    "lines_covered": coverage_data.get("totals", {}).get("covered_lines", 0),
                    "lines_total": coverage_data.get("totals", {}).get("num_statements", 0),
                    "files": coverage_data.get("files", {})
                }
            
        except Exception as e:
            print(f"    ⚠️  Coverage analysis failed: {e}")
        
        return None
    
    def _print_category_summary(self, category: str, results: Dict[str, Any]):
        """Print summary for a test category."""
        total = results["total_tests"]
        passed = results["passed"]
        failed = results["failed"]
        skipped = results["skipped"]
        duration = results["duration"]
        
        print(f"  📊 Summary: {passed}✅ {failed}❌ {skipped}⏭️  ({duration:.1f}s)")
        
        if results["coverage"]:
            coverage = results["coverage"]["total_coverage"]
            print(f"  📈 Coverage: {coverage:.1f}%")
        
        if failed > 0:
            print(f"  🚨 {failed} test(s) failed")
            if self.verbose and results["errors"]:
                for error in results["errors"][:3]:  # Show first 3 errors
                    print(f"    - {error['test']}: {error['message'][:100]}...")
    
    def _generate_final_report(self):
        """Generate and display final comprehensive report."""
        total_duration = self.end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Overall statistics
        total_tests = sum(cat["total_tests"] for cat in self.results.values())
        total_passed = sum(cat["passed"] for cat in self.results.values())
        total_failed = sum(cat["failed"] for cat in self.results.values())
        total_skipped = sum(cat["skipped"] for cat in self.results.values())
        
        print(f"🕐 Total Duration: {total_duration:.1f}s")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {total_passed}")
        print(f"❌ Failed: {total_failed}")
        print(f"⏭️  Skipped: {total_skipped}")
        print(f"📊 Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "📊 Success Rate: N/A")
        
        # Category breakdown
        print("\n📋 Category Breakdown:")
        for category, results in self.results.items():
            status = "✅" if results["failed"] == 0 else "❌"
            print(f"  {status} {category.replace('_', ' ').title()}: {results['passed']}/{results['total_tests']} ({results['duration']:.1f}s)")
        
        # Coverage summary
        unit_test_coverage = self.results.get("unit_tests", {}).get("coverage")
        if unit_test_coverage:
            print(f"\n📈 Code Coverage: {unit_test_coverage['total_coverage']:.1f}%")
            print(f"   Lines Covered: {unit_test_coverage['lines_covered']}/{unit_test_coverage['lines_total']}")
        
        # Performance metrics (from load tests)
        load_test_results = self.results.get("load_tests", {})
        if load_test_results.get("files"):
            print("\n⚡ Performance Summary:")
            for test_file, file_results in load_test_results["files"].items():
                if "load" in test_file.lower():
                    print(f"   {Path(test_file).name}: {file_results.get('duration', 0):.1f}s")
        
        # Error summary
        all_errors = []
        for category, results in self.results.items():
            all_errors.extend(results.get("errors", []))
        
        if all_errors:
            print(f"\n🚨 Error Summary ({len(all_errors)} total):")
            # Group errors by type
            error_types = {}
            for error in all_errors:
                error_msg = error.get("message", "Unknown error")[:50]
                if error_msg not in error_types:
                    error_types[error_msg] = 0
                error_types[error_msg] += 1
            
            for error_msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {count}x {error_msg}...")
        
        # Recommendations
        print("\n💡 Recommendations:")
        if total_failed > 0:
            print("   - Review failed tests and fix issues before deployment")
        if unit_test_coverage and unit_test_coverage["total_coverage"] < 80:
            print("   - Increase test coverage to at least 80%")
        if load_test_results.get("duration", 0) > 300:
            print("   - Load tests took longer than expected, check performance")
        if total_tests == 0:
            print("   - No tests were found or executed")
        
        # Save detailed report
        self._save_detailed_report()
        
        print("\n" + "=" * 60)
        
        # Exit with appropriate code
        if total_failed > 0:
            print("❌ Some tests failed. Check the report above.")
            return False
        else:
            print("✅ All tests passed successfully!")
            return True
    
    def _save_detailed_report(self):
        """Save detailed test report to file."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": self.end_time - self.start_time,
            "results": self.results,
            "summary": {
                "total_tests": sum(cat["total_tests"] for cat in self.results.values()),
                "total_passed": sum(cat["passed"] for cat in self.results.values()),
                "total_failed": sum(cat["failed"] for cat in self.results.values()),
                "total_skipped": sum(cat["skipped"] for cat in self.results.values())
            }
        }
        
        # Create reports directory
        os.makedirs("reports", exist_ok=True)
        
        # Save JSON report
        report_file = f"reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel execution")
    parser.add_argument("--category", "-c", choices=["unit", "integration", "e2e", "load", "all"], 
                       default="all", help="Run specific test category")
    parser.add_argument("--quick", "-q", action="store_true", help="Skip load tests for quick run")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(verbose=args.verbose, parallel=not args.no_parallel)
    
    # Filter test categories based on arguments
    if args.category != "all":
        category_map = {
            "unit": "unit_tests",
            "integration": "integration_tests", 
            "e2e": "e2e_tests",
            "load": "load_tests"
        }
        selected_category = category_map[args.category]
        runner.test_categories = {selected_category: runner.test_categories[selected_category]}
    
    if args.quick:
        # Remove load tests for quick run
        runner.test_categories.pop("load_tests", None)
    
    # Check if we're in the right directory
    if not os.path.exists("src/ai_karen_engine"):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Install required packages
    print("📦 Installing test dependencies...")
    subprocess.run([
        "pip", "install", "-q", 
        "pytest", "pytest-asyncio", "pytest-xdist", "pytest-json-report", 
        "pytest-cov", "httpx", "psutil"
    ], check=False)
    
    # Run tests
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()