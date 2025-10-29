#!/usr/bin/env python3
"""
Comprehensive test runner for health monitoring tests.

Runs all health monitoring test suites with proper configuration and reporting.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class HealthMonitoringTestRunner:
    """Test runner for health monitoring test suites."""
    
    def __init__(self):
        self.test_suites = {
            'unit': {
                'path': 'tests/unit/health/',
                'description': 'Unit tests for health monitoring components',
                'markers': ['unit'],
                'timeout': 60
            },
            'integration': {
                'path': 'tests/integration/health/',
                'description': 'Integration tests for service recovery mechanisms',
                'markers': ['integration'],
                'timeout': 300
            },
            'performance': {
                'path': 'tests/performance/health/',
                'description': 'Load testing for health check performance',
                'markers': ['performance', 'slow'],
                'timeout': 600
            },
            'chaos': {
                'path': 'tests/chaos/health/',
                'description': 'Chaos engineering tests for failure scenarios',
                'markers': ['chaos', 'slow'],
                'timeout': 900
            }
        }
        
        self.results = {}
    
    def run_test_suite(self, suite_name, verbose=False, capture_output=True):
        """Run a specific test suite."""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite_config = self.test_suites[suite_name]
        test_path = suite_config['path']
        
        print(f"\n{'='*60}")
        print(f"Running {suite_name.upper()} tests")
        print(f"Description: {suite_config['description']}")
        print(f"Path: {test_path}")
        print(f"{'='*60}")
        
        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            test_path,
            '-v' if verbose else '-q',
            '--tb=short',
            f'--timeout={suite_config["timeout"]}',
            '--timeout-method=thread'
        ]
        
        # Add markers
        for marker in suite_config['markers']:
            cmd.extend(['-m', marker])
        
        # Add output capture
        if not capture_output:
            cmd.append('-s')
        
        # Add coverage if requested
        if os.getenv('COVERAGE', '').lower() == 'true':
            cmd.extend([
                '--cov=server.extension_health_monitor',
                '--cov-report=term-missing',
                '--cov-append'
            ])
        
        # Run the tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=capture_output,
                text=True,
                timeout=suite_config['timeout'] + 60  # Extra buffer
            )
            
            execution_time = time.time() - start_time
            
            # Store results
            self.results[suite_name] = {
                'return_code': result.returncode,
                'execution_time': execution_time,
                'stdout': result.stdout if capture_output else '',
                'stderr': result.stderr if capture_output else '',
                'success': result.returncode == 0
            }
            
            # Print results
            if result.returncode == 0:
                print(f"✅ {suite_name.upper()} tests PASSED ({execution_time:.2f}s)")
            else:
                print(f"❌ {suite_name.upper()} tests FAILED ({execution_time:.2f}s)")
                if capture_output and result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if capture_output and result.stderr:
                    print("STDERR:")
                    print(result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print(f"⏰ {suite_name.upper()} tests TIMED OUT ({execution_time:.2f}s)")
            self.results[suite_name] = {
                'return_code': -1,
                'execution_time': execution_time,
                'success': False,
                'error': 'Timeout'
            }
            return False
        
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"💥 {suite_name.upper()} tests ERROR: {e}")
            self.results[suite_name] = {
                'return_code': -2,
                'execution_time': execution_time,
                'success': False,
                'error': str(e)
            }
            return False
    
    def run_all_suites(self, verbose=False, capture_output=True, fail_fast=False):
        """Run all test suites."""
        print("Starting comprehensive health monitoring test suite")
        print(f"Project root: {project_root}")
        
        total_start_time = time.time()
        all_passed = True
        
        for suite_name in self.test_suites.keys():
            success = self.run_test_suite(suite_name, verbose, capture_output)
            if not success:
                all_passed = False
                if fail_fast:
                    print(f"\n❌ Stopping due to failure in {suite_name} tests (fail-fast mode)")
                    break
        
        total_execution_time = time.time() - total_start_time
        
        # Print summary
        self.print_summary(total_execution_time)
        
        return all_passed
    
    def print_summary(self, total_time):
        """Print test execution summary."""
        print(f"\n{'='*60}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        passed_count = sum(1 for result in self.results.values() if result['success'])
        total_count = len(self.results)
        
        print(f"Total test suites: {total_count}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {total_count - passed_count}")
        print(f"Total execution time: {total_time:.2f}s")
        
        print(f"\n{'Suite':<15} {'Status':<10} {'Time':<10} {'Details'}")
        print("-" * 60)
        
        for suite_name, result in self.results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            time_str = f"{result['execution_time']:.2f}s"
            details = ""
            
            if not result['success']:
                if 'error' in result:
                    details = result['error']
                elif result['return_code'] != 0:
                    details = f"Exit code: {result['return_code']}"
            
            print(f"{suite_name:<15} {status:<10} {time_str:<10} {details}")
        
        if passed_count == total_count:
            print(f"\n🎉 All health monitoring tests PASSED!")
        else:
            print(f"\n💥 {total_count - passed_count} test suite(s) FAILED")
    
    def run_specific_tests(self, test_patterns, verbose=False):
        """Run specific tests matching patterns."""
        print(f"Running specific tests matching: {test_patterns}")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            '-v' if verbose else '-q',
            '--tb=short'
        ]
        
        # Add test patterns
        for pattern in test_patterns:
            cmd.append(pattern)
        
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run health monitoring test suites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_health_monitoring_tests.py                    # Run all test suites
  python run_health_monitoring_tests.py --suite unit       # Run only unit tests
  python run_health_monitoring_tests.py --suite performance --verbose
  python run_health_monitoring_tests.py --pattern "*chaos*" --verbose
  python run_health_monitoring_tests.py --fail-fast       # Stop on first failure
        """
    )
    
    parser.add_argument(
        '--suite',
        choices=['unit', 'integration', 'performance', 'chaos'],
        help='Run specific test suite'
    )
    
    parser.add_argument(
        '--pattern',
        action='append',
        help='Run tests matching pattern (can be used multiple times)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--no-capture',
        action='store_true',
        help='Do not capture output (useful for debugging)'
    )
    
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first test suite failure'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Enable coverage reporting'
    )
    
    args = parser.parse_args()
    
    # Set coverage environment variable
    if args.coverage:
        os.environ['COVERAGE'] = 'true'
    
    runner = HealthMonitoringTestRunner()
    
    try:
        if args.pattern:
            # Run specific test patterns
            success = runner.run_specific_tests(args.pattern, args.verbose)
        elif args.suite:
            # Run specific test suite
            success = runner.run_test_suite(
                args.suite,
                verbose=args.verbose,
                capture_output=not args.no_capture
            )
        else:
            # Run all test suites
            success = runner.run_all_suites(
                verbose=args.verbose,
                capture_output=not args.no_capture,
                fail_fast=args.fail_fast
            )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()