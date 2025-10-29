"""
Comprehensive authentication test suite runner.
Orchestrates all authentication tests and provides summary reporting.
"""

import pytest
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json


class AuthenticationTestSuite:
    """Comprehensive authentication test suite runner."""

    def __init__(self):
        """Initialize the test suite."""
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
        # Define test categories and their files
        self.test_categories = {
            "unit_tests": [
                "tests/unit/auth/test_extension_auth_middleware.py"
            ],
            "integration_tests": [
                "tests/integration/auth/test_extension_api_authentication.py"
            ],
            "e2e_tests": [
                "tests/e2e/test_frontend_authentication_flow.py"
            ],
            "security_tests": [
                "tests/security/test_extension_authentication_security.py"
            ]
        }

    def run_comprehensive_suite(self) -> Dict[str, Any]:
        """Run the complete authentication test suite."""
        print("🔐 Starting Comprehensive Authentication Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Run each test category
        for category, test_files in self.test_categories.items():
            print(f"\n📋 Running {category.replace('_', ' ').title()}")
            print("-" * 40)
            
            category_results = self._run_test_category(category, test_files)
            self.test_results[category] = category_results
            
            # Print category summary
            self._print_category_summary(category, category_results)
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report()
        
        # Print final summary
        self._print_final_summary(report)
        
        return report

    def _run_test_category(self, category: str, test_files: List[str]) -> Dict[str, Any]:
        """Run tests for a specific category."""
        category_results = {
            "files": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "errors": [],
            "duration": 0
        }
        
        start_time = time.time()
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                print(f"⚠️  Test file not found: {test_file}")
                category_results["errors"].append(f"File not found: {test_file}")
                continue
            
            print(f"  🧪 Running {os.path.basename(test_file)}")
            
            # Run pytest for this specific file
            file_results = self._run_pytest_file(test_file)
            category_results["files"][test_file] = file_results
            
            # Aggregate results
            category_results["total_tests"] += file_results["total"]
            category_results["passed_tests"] += file_results["passed"]
            category_results["failed_tests"] += file_results["failed"]
            category_results["skipped_tests"] += file_results["skipped"]
            
            if file_results["errors"]:
                category_results["errors"].extend(file_results["errors"])
        
        category_results["duration"] = time.time() - start_time
        return category_results

    def _run_pytest_file(self, test_file: str) -> Dict[str, Any]:
        """Run pytest on a specific file and parse results."""
        file_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "duration": 0
        }
        
        try:
            # Run pytest with JSON output
            cmd = [
                sys.executable, "-m", "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=/tmp/pytest_report.json"
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per file
            )
            file_results["duration"] = time.time() - start_time
            
            # Parse JSON report if available
            try:
                with open("/tmp/pytest_report.json", "r") as f:
                    report_data = json.load(f)
                
                file_results["total"] = report_data["summary"]["total"]
                file_results["passed"] = report_data["summary"].get("passed", 0)
                file_results["failed"] = report_data["summary"].get("failed", 0)
                file_results["skipped"] = report_data["summary"].get("skipped", 0)
                
                # Extract error details
                if "tests" in report_data:
                    for test in report_data["tests"]:
                        if test["outcome"] == "failed":
                            file_results["errors"].append({
                                "test": test["nodeid"],
                                "error": test.get("call", {}).get("longrepr", "Unknown error")
                            })
                
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                # Fallback to parsing stdout
                self._parse_pytest_stdout(result.stdout, file_results)
            
            if result.returncode != 0 and not file_results["errors"]:
                file_results["errors"].append(f"Pytest failed with return code {result.returncode}")
                if result.stderr:
                    file_results["errors"].append(f"Stderr: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            file_results["errors"].append("Test execution timed out")
        except Exception as e:
            file_results["errors"].append(f"Error running tests: {str(e)}")
        
        return file_results

    def _parse_pytest_stdout(self, stdout: str, file_results: Dict[str, Any]):
        """Parse pytest stdout output as fallback."""
        lines = stdout.split('\n')
        
        for line in lines:
            if "failed" in line and "passed" in line:
                # Look for summary line like "1 failed, 5 passed in 2.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "failed,":
                        file_results["failed"] = int(parts[i-1])
                    elif part == "passed":
                        file_results["passed"] = int(parts[i-1])
                    elif part == "skipped":
                        file_results["skipped"] = int(parts[i-1])
                
                file_results["total"] = file_results["failed"] + file_results["passed"] + file_results["skipped"]
                break

    def _print_category_summary(self, category: str, results: Dict[str, Any]):
        """Print summary for a test category."""
        total = results["total_tests"]
        passed = results["passed_tests"]
        failed = results["failed_tests"]
        skipped = results["skipped_tests"]
        
        print(f"  📊 Results: {passed} passed, {failed} failed, {skipped} skipped ({total} total)")
        print(f"  ⏱️  Duration: {results['duration']:.2f}s")
        
        if results["errors"]:
            print(f"  ❌ Errors: {len(results['errors'])}")
            for error in results["errors"][:3]:  # Show first 3 errors
                if isinstance(error, dict):
                    print(f"    - {error['test']}: {error['error'][:100]}...")
                else:
                    print(f"    - {str(error)[:100]}...")
            if len(results["errors"]) > 3:
                print(f"    ... and {len(results['errors']) - 3} more errors")

    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_duration = self.end_time - self.start_time
        
        # Aggregate all results
        total_tests = sum(cat["total_tests"] for cat in self.test_results.values())
        total_passed = sum(cat["passed_tests"] for cat in self.test_results.values())
        total_failed = sum(cat["failed_tests"] for cat in self.test_results.values())
        total_skipped = sum(cat["skipped_tests"] for cat in self.test_results.values())
        total_errors = sum(len(cat["errors"]) for cat in self.test_results.values())
        
        # Calculate success rate
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Identify critical failures
        critical_failures = []
        for category, results in self.test_results.items():
            if results["failed_tests"] > 0:
                critical_failures.append({
                    "category": category,
                    "failed_count": results["failed_tests"],
                    "errors": results["errors"][:5]  # Top 5 errors
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "skipped_tests": total_skipped,
                "total_errors": total_errors,
                "success_rate": success_rate,
                "duration": total_duration
            },
            "categories": self.test_results,
            "critical_failures": critical_failures,
            "recommendations": recommendations,
            "timestamp": time.time()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check for high failure rates
        for category, results in self.test_results.items():
            if results["total_tests"] > 0:
                failure_rate = results["failed_tests"] / results["total_tests"]
                if failure_rate > 0.2:  # More than 20% failures
                    recommendations.append(
                        f"High failure rate in {category} ({failure_rate:.1%}). "
                        f"Review and fix failing tests before deployment."
                    )
        
        # Check for security test failures
        if "security_tests" in self.test_results:
            security_results = self.test_results["security_tests"]
            if security_results["failed_tests"] > 0:
                recommendations.append(
                    "Security tests are failing. This is critical and must be addressed "
                    "before deploying authentication changes."
                )
        
        # Check for missing test coverage
        for category, test_files in self.test_categories.items():
            if category not in self.test_results or self.test_results[category]["total_tests"] == 0:
                recommendations.append(
                    f"No tests found for {category}. Consider adding comprehensive "
                    f"test coverage for this area."
                )
        
        # Performance recommendations
        total_duration = sum(cat["duration"] for cat in self.test_results.values())
        if total_duration > 300:  # More than 5 minutes
            recommendations.append(
                f"Test suite is slow ({total_duration:.1f}s). Consider optimizing "
                f"test performance or running tests in parallel."
            )
        
        return recommendations

    def _print_final_summary(self, report: Dict[str, Any]):
        """Print final comprehensive summary."""
        print("\n" + "=" * 60)
        print("🏁 COMPREHENSIVE AUTHENTICATION TEST SUITE SUMMARY")
        print("=" * 60)
        
        summary = report["summary"]
        
        # Overall results
        print(f"📊 Overall Results:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed_tests']}")
        print(f"   ❌ Failed: {summary['failed_tests']}")
        print(f"   ⏭️  Skipped: {summary['skipped_tests']}")
        print(f"   🎯 Success Rate: {summary['success_rate']:.1f}%")
        print(f"   ⏱️  Total Duration: {summary['duration']:.2f}s")
        
        # Category breakdown
        print(f"\n📋 Category Breakdown:")
        for category, results in report["categories"].items():
            status = "✅" if results["failed_tests"] == 0 else "❌"
            print(f"   {status} {category.replace('_', ' ').title()}: "
                  f"{results['passed_tests']}/{results['total_tests']} passed")
        
        # Critical failures
        if report["critical_failures"]:
            print(f"\n🚨 Critical Failures:")
            for failure in report["critical_failures"]:
                print(f"   ❌ {failure['category']}: {failure['failed_count']} failures")
        
        # Recommendations
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")
        
        # Final verdict
        print(f"\n🎯 Final Verdict:")
        if summary["failed_tests"] == 0:
            print("   ✅ ALL TESTS PASSED - Authentication system is ready for deployment!")
        elif summary["success_rate"] >= 90:
            print("   ⚠️  MOSTLY PASSING - Minor issues need attention before deployment")
        elif summary["success_rate"] >= 70:
            print("   ❌ SIGNIFICANT ISSUES - Major problems need to be fixed")
        else:
            print("   🚨 CRITICAL ISSUES - Authentication system is not ready for deployment")


def run_authentication_test_suite():
    """Main function to run the comprehensive authentication test suite."""
    suite = AuthenticationTestSuite()
    report = suite.run_comprehensive_suite()
    
    # Save report to file
    report_file = "authentication_test_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on results
    if report["summary"]["failed_tests"] == 0:
        return 0  # Success
    else:
        return 1  # Failure


if __name__ == "__main__":
    exit_code = run_authentication_test_suite()
    sys.exit(exit_code)


# Pytest fixtures and utilities for the comprehensive suite
@pytest.fixture(scope="session")
def auth_test_config():
    """Shared authentication configuration for all tests."""
    return {
        "secret_key": "comprehensive-test-secret-key-123456789",
        "algorithm": "HS256",
        "enabled": True,
        "auth_mode": "testing",
        "dev_bypass_enabled": True,
        "require_https": False,
        "access_token_expire_minutes": 60,
        "service_token_expire_minutes": 30,
        "api_key": "comprehensive-test-api-key",
        "default_permissions": ["extension:read", "extension:write"]
    }


@pytest.fixture(scope="session")
def comprehensive_auth_manager(auth_test_config):
    """Shared authentication manager for comprehensive testing."""
    from server.security import ExtensionAuthManager
    return ExtensionAuthManager(auth_test_config)


class TestComprehensiveAuthenticationSuite:
    """Meta-tests for the comprehensive authentication test suite."""

    def test_all_test_files_exist(self):
        """Test that all expected test files exist."""
        suite = AuthenticationTestSuite()
        
        missing_files = []
        for category, test_files in suite.test_categories.items():
            for test_file in test_files:
                if not os.path.exists(test_file):
                    missing_files.append(test_file)
        
        assert not missing_files, f"Missing test files: {missing_files}"

    def test_test_categories_coverage(self):
        """Test that all required test categories are covered."""
        suite = AuthenticationTestSuite()
        
        required_categories = [
            "unit_tests",
            "integration_tests", 
            "e2e_tests",
            "security_tests"
        ]
        
        for category in required_categories:
            assert category in suite.test_categories, f"Missing test category: {category}"
            assert suite.test_categories[category], f"Empty test category: {category}"

    def test_suite_runner_functionality(self):
        """Test that the suite runner works correctly."""
        suite = AuthenticationTestSuite()
        
        # Test category parsing
        assert len(suite.test_categories) >= 4
        
        # Test result structure
        assert hasattr(suite, 'test_results')
        assert hasattr(suite, 'start_time')
        assert hasattr(suite, 'end_time')

    def test_report_generation(self):
        """Test that report generation works correctly."""
        suite = AuthenticationTestSuite()
        
        # Mock some test results
        suite.test_results = {
            "unit_tests": {
                "total_tests": 10,
                "passed_tests": 8,
                "failed_tests": 2,
                "skipped_tests": 0,
                "errors": ["Test error 1", "Test error 2"],
                "duration": 5.0
            }
        }
        
        suite.start_time = time.time() - 10
        suite.end_time = time.time()
        
        report = suite._generate_comprehensive_report()
        
        # Verify report structure
        assert "summary" in report
        assert "categories" in report
        assert "critical_failures" in report
        assert "recommendations" in report
        
        # Verify summary calculations
        assert report["summary"]["total_tests"] == 10
        assert report["summary"]["passed_tests"] == 8
        assert report["summary"]["failed_tests"] == 2
        assert report["summary"]["success_rate"] == 80.0

    def test_recommendation_generation(self):
        """Test that recommendations are generated appropriately."""
        suite = AuthenticationTestSuite()
        
        # Mock results with high failure rate
        suite.test_results = {
            "security_tests": {
                "total_tests": 10,
                "passed_tests": 5,
                "failed_tests": 5,
                "skipped_tests": 0,
                "errors": [],
                "duration": 2.0
            }
        }
        
        recommendations = suite._generate_recommendations()
        
        # Should recommend fixing security test failures
        security_rec = any("security" in rec.lower() for rec in recommendations)
        assert security_rec, "Should recommend fixing security test failures"
        
        # Should recommend fixing high failure rate
        failure_rate_rec = any("failure rate" in rec.lower() for rec in recommendations)
        assert failure_rate_rec, "Should recommend fixing high failure rate"