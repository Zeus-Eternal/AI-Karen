#!/usr/bin/env python3
"""
Test Runner for HTTP Request Validation Integration Tests

This script runs all integration tests for the HTTP request validation enhancement
system and generates comprehensive reports.

Usage:
    python tests/run_validation_integration_tests.py [options]

Options:
    --verbose, -v       Verbose output
    --performance, -p   Run performance tests only
    --security, -s      Run security tests only
    --errors, -e        Run error handling tests only
    --all, -a           Run all tests (default)
    --report, -r        Generate detailed report
    --html              Generate HTML report
    --junit             Generate JUnit XML report
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationTestRunner:
    """Test runner for validation integration tests."""
    
    def __init__(self, args):
        self.args = args
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
        # Test file mappings
        self.test_files = {
            'integration': [
                'tests/test_http_validation_integration.py',
                'tests/test_validation_integration_suite.py'
            ],
            'performance': [
                'tests/test_validation_performance_integration.py'
            ],
            'security': [
                'tests/test_http_validation_integration.py::TestHTTPValidationPipeline::test_security_threat_detection_pipeline'
            ],
            'error_handling': [
                'tests/test_validation_error_handling_integration.py'
            ]
        }
    
    def run_tests(self) -> Dict[str, Any]:
        """Run the selected tests and return results."""
        logger.info("Starting HTTP Request Validation Integration Tests")
        self.start_time = time.time()
        
        # Determine which tests to run
        test_files_to_run = self._get_test_files_to_run()
        
        if not test_files_to_run:
            logger.error("No test files selected")
            return {"error": "No test files selected"}
        
        logger.info(f"Running tests from {len(test_files_to_run)} files")
        
        # Run tests
        results = {}
        for test_category, files in test_files_to_run.items():
            logger.info(f"Running {test_category} tests...")
            category_results = self._run_test_category(test_category, files)
            results[test_category] = category_results
        
        self.end_time = time.time()
        self.test_results = results
        
        # Generate reports if requested
        if self.args.report:
            self._generate_text_report()
        
        if self.args.html:
            self._generate_html_report()
        
        if self.args.junit:
            self._generate_junit_report()
        
        return results
    
    def _get_test_files_to_run(self) -> Dict[str, List[str]]:
        """Determine which test files to run based on arguments."""
        if self.args.performance:
            return {"performance": self.test_files["performance"]}
        elif self.args.security:
            return {"security": self.test_files["security"]}
        elif self.args.errors:
            return {"error_handling": self.test_files["error_handling"]}
        else:
            # Run all tests by default
            return self.test_files
    
    def _run_test_category(self, category: str, test_files: List[str]) -> Dict[str, Any]:
        """Run tests for a specific category."""
        category_start_time = time.time()
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add verbosity
        if self.args.verbose:
            cmd.extend(["-v", "-s"])
        else:
            cmd.append("-q")
        
        # Add test files
        cmd.extend(test_files)
        
        # Add markers if needed
        if category == "performance":
            cmd.extend(["-m", "performance"])
        elif category == "security":
            cmd.extend(["-m", "security"])
        elif category == "error_handling":
            cmd.extend(["-m", "error_handling"])
        
        # Add output options
        cmd.extend(["--tb=short"])
        
        # Add JSON report for parsing
        json_report_file = f"test_results_{category}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report_file}"])
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            # Run the tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            category_end_time = time.time()
            duration = category_end_time - category_start_time
            
            # Parse results
            test_output = result.stdout
            test_errors = result.stderr
            return_code = result.returncode
            
            # Try to load JSON report if available
            json_results = None
            if os.path.exists(json_report_file):
                try:
                    with open(json_report_file, 'r') as f:
                        json_results = json.load(f)
                    os.remove(json_report_file)  # Clean up
                except Exception as e:
                    logger.warning(f"Could not parse JSON report: {e}")
            
            return {
                "duration": duration,
                "return_code": return_code,
                "stdout": test_output,
                "stderr": test_errors,
                "json_results": json_results,
                "success": return_code == 0
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Tests in category {category} timed out")
            return {
                "duration": 1800,
                "return_code": -1,
                "stdout": "",
                "stderr": "Test execution timed out",
                "json_results": None,
                "success": False
            }
        
        except Exception as e:
            logger.error(f"Error running tests in category {category}: {e}")
            return {
                "duration": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "json_results": None,
                "success": False
            }
    
    def _generate_text_report(self):
        """Generate a detailed text report."""
        report_file = f"validation_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w') as f:
            f.write("HTTP REQUEST VALIDATION INTEGRATION TEST REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Test Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {self.end_time - self.start_time:.2f} seconds\n\n")
            
            # Summary
            total_categories = len(self.test_results)
            successful_categories = sum(1 for r in self.test_results.values() if r.get("success", False))
            
            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Test Categories: {total_categories}\n")
            f.write(f"Successful Categories: {successful_categories}\n")
            f.write(f"Success Rate: {successful_categories / total_categories * 100:.1f}%\n\n")
            
            # Detailed results
            for category, results in self.test_results.items():
                f.write(f"{category.upper()} TESTS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Duration: {results['duration']:.2f} seconds\n")
                f.write(f"Return Code: {results['return_code']}\n")
                f.write(f"Success: {'YES' if results['success'] else 'NO'}\n")
                
                if results['json_results']:
                    json_data = results['json_results']
                    if 'summary' in json_data:
                        summary = json_data['summary']
                        f.write(f"Tests Run: {summary.get('total', 'N/A')}\n")
                        f.write(f"Passed: {summary.get('passed', 'N/A')}\n")
                        f.write(f"Failed: {summary.get('failed', 'N/A')}\n")
                        f.write(f"Errors: {summary.get('error', 'N/A')}\n")
                
                if results['stderr']:
                    f.write(f"Errors:\n{results['stderr']}\n")
                
                f.write("\n")
            
            # Performance metrics (if available)
            if 'performance' in self.test_results:
                perf_results = self.test_results['performance']
                if perf_results.get('success') and 'performance metrics' in perf_results.get('stdout', ''):
                    f.write("PERFORMANCE METRICS\n")
                    f.write("-" * 30 + "\n")
                    # Extract performance metrics from stdout
                    stdout_lines = perf_results['stdout'].split('\n')
                    in_metrics = False
                    for line in stdout_lines:
                        if 'performance' in line.lower() and 'results' in line.lower():
                            in_metrics = True
                        elif in_metrics and line.strip():
                            f.write(f"{line}\n")
                        elif in_metrics and not line.strip():
                            break
                    f.write("\n")
            
            # Compliance results (if available)
            if 'integration' in self.test_results:
                int_results = self.test_results['integration']
                if int_results.get('success') and 'compliance' in int_results.get('stdout', '').lower():
                    f.write("COMPLIANCE VERIFICATION\n")
                    f.write("-" * 30 + "\n")
                    stdout_lines = int_results['stdout'].split('\n')
                    in_compliance = False
                    for line in stdout_lines:
                        if 'compliance' in line.lower() and ('verification' in line.lower() or 'summary' in line.lower()):
                            in_compliance = True
                        elif in_compliance and line.strip():
                            f.write(f"{line}\n")
                        elif in_compliance and not line.strip():
                            break
                    f.write("\n")
        
        logger.info(f"Text report generated: {report_file}")
    
    def _generate_html_report(self):
        """Generate an HTML report."""
        report_file = f"validation_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HTTP Request Validation Integration Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .category {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .success {{ background-color: #d4edda; }}
                .failure {{ background-color: #f8d7da; }}
                .metrics {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; }}
                pre {{ background-color: #f8f9fa; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>HTTP Request Validation Integration Test Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total Duration: {self.end_time - self.start_time:.2f} seconds</p>
            </div>
        """
        
        # Summary
        total_categories = len(self.test_results)
        successful_categories = sum(1 for r in self.test_results.values() if r.get("success", False))
        
        html_content += f"""
            <div class="summary">
                <h2>Summary</h2>
                <p>Test Categories: {total_categories}</p>
                <p>Successful Categories: {successful_categories}</p>
                <p>Success Rate: {successful_categories / total_categories * 100:.1f}%</p>
            </div>
        """
        
        # Detailed results
        for category, results in self.test_results.items():
            status_class = "success" if results['success'] else "failure"
            html_content += f"""
                <div class="category {status_class}">
                    <h3>{category.upper()} Tests</h3>
                    <div class="metrics">
                        <p>Duration: {results['duration']:.2f} seconds</p>
                        <p>Return Code: {results['return_code']}</p>
                        <p>Success: {'YES' if results['success'] else 'NO'}</p>
            """
            
            if results['json_results'] and 'summary' in results['json_results']:
                summary = results['json_results']['summary']
                html_content += f"""
                        <p>Tests Run: {summary.get('total', 'N/A')}</p>
                        <p>Passed: {summary.get('passed', 'N/A')}</p>
                        <p>Failed: {summary.get('failed', 'N/A')}</p>
                        <p>Errors: {summary.get('error', 'N/A')}</p>
                """
            
            html_content += "</div>"
            
            if results['stderr']:
                html_content += f"<h4>Errors:</h4><pre>{results['stderr']}</pre>"
            
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {report_file}")
    
    def _generate_junit_report(self):
        """Generate a JUnit XML report."""
        # This would require additional XML generation logic
        # For now, just log that it's not implemented
        logger.info("JUnit report generation not implemented yet")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run HTTP Request Validation Integration Tests"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--performance", "-p",
        action="store_true",
        help="Run performance tests only"
    )
    
    parser.add_argument(
        "--security", "-s",
        action="store_true",
        help="Run security tests only"
    )
    
    parser.add_argument(
        "--errors", "-e",
        action="store_true",
        help="Run error handling tests only"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests (default)"
    )
    
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Generate detailed text report"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report"
    )
    
    parser.add_argument(
        "--junit",
        action="store_true",
        help="Generate JUnit XML report"
    )
    
    args = parser.parse_args()
    
    # Default to all tests if no specific category is selected
    if not any([args.performance, args.security, args.errors]):
        args.all = True
    
    # Create and run test runner
    runner = ValidationTestRunner(args)
    results = runner.run_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)
    
    total_categories = len(results)
    successful_categories = sum(1 for r in results.values() if r.get("success", False))
    
    print(f"Test Categories: {total_categories}")
    print(f"Successful Categories: {successful_categories}")
    print(f"Success Rate: {successful_categories / total_categories * 100:.1f}%")
    print(f"Total Duration: {runner.end_time - runner.start_time:.2f} seconds")
    
    # Print category results
    for category, result in results.items():
        status = "✓ PASS" if result.get("success", False) else "✗ FAIL"
        print(f"{category}: {status} ({result['duration']:.2f}s)")
    
    # Exit with appropriate code
    if successful_categories == total_categories:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {total_categories - successful_categories} test categories failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()