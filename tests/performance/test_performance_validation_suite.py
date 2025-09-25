"""
Main test runner for the comprehensive performance validation suite.
Orchestrates all performance tests and generates summary reports.
"""

import pytest
import asyncio
import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# Import all test suites
from tests.test_performance_benchmarking import PerformanceBenchmarkSuite
from tests.test_load_testing import LoadTestSuite
from tests.test_service_lifecycle_integration import ServiceLifecycleIntegrationSuite
from tests.test_gpu_utilization_validation import GPUUtilizationTestSuite
from tests.test_performance_regression import PerformanceRegressionSuite
from tests.test_optimization_validation_integration import OptimizationIntegrationSuite


@dataclass
class ValidationSummary:
    """Summary of validation test results."""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_categories: Dict[str, Dict[str, Any]]
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    overall_status: str  # PASS, FAIL, WARNING


class PerformanceValidationRunner:
    """Main runner for performance validation test suite."""
    
    def __init__(self):
        self.results = {}
        self.summary_file = "tests/performance_validation_summary.json"
    
    async def run_benchmark_tests(self) -> Dict[str, Any]:
        """Run performance benchmark tests."""
        print("Running Performance Benchmark Tests...")
        suite = PerformanceBenchmarkSuite()
        
        results = {
            "category": "benchmarking",
            "tests": {},
            "status": "PASS",
            "errors": []
        }
        
        try:
            # Startup benchmark
            startup_result = await suite.run_startup_benchmark()
            results["tests"]["startup_benchmark"] = {
                "improvement": startup_result.improvement_percentage,
                "baseline_time": startup_result.baseline_time,
                "optimized_time": startup_result.optimized_time,
                "status": "PASS" if startup_result.improvement_percentage >= 50 else "FAIL"
            }
            
            # Memory benchmark
            memory_result = await suite.run_memory_benchmark()
            results["tests"]["memory_benchmark"] = {
                "improvement": memory_result.memory_improvement,
                "baseline_memory": memory_result.memory_baseline,
                "optimized_memory": memory_result.memory_optimized,
                "status": "PASS" if memory_result.memory_optimized <= 512 * 1024 * 1024 else "FAIL"
            }
            
            # Service lifecycle benchmark
            lifecycle_result = await suite.run_service_lifecycle_benchmark()
            results["tests"]["lifecycle_benchmark"] = {
                "improvement": lifecycle_result.improvement_percentage,
                "execution_time": lifecycle_result.optimized_time,
                "status": "PASS" if lifecycle_result.optimized_time < 2.0 else "FAIL"
            }
            
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Benchmark tests failed: {e}")
        
        return results
    
    async def run_load_tests(self) -> Dict[str, Any]:
        """Run load testing scenarios."""
        print("Running Load Tests...")
        suite = LoadTestSuite()
        
        results = {
            "category": "load_testing",
            "tests": {},
            "status": "PASS",
            "errors": []
        }
        
        try:
            # Concurrent service requests
            concurrent_result = await suite.run_concurrent_service_load_test(50)
            results["tests"]["concurrent_requests"] = {
                "success_rate": concurrent_result.success_rate,
                "avg_response_time": concurrent_result.average_response_time,
                "peak_memory": concurrent_result.peak_memory_usage,
                "status": "PASS" if concurrent_result.success_rate >= 95 else "FAIL"
            }
            
            # Resource pressure test
            pressure_result = await suite.run_resource_pressure_test()
            results["tests"]["resource_pressure"] = {
                "success_rate": pressure_result.success_rate,
                "errors": len(pressure_result.errors),
                "status": "PASS" if len(pressure_result.errors) <= 2 else "FAIL"
            }
            
            # Async task load test
            async_result = await suite.run_async_task_load_test(30)
            results["tests"]["async_task_load"] = {
                "success_rate": async_result.success_rate,
                "avg_response_time": async_result.average_response_time,
                "status": "PASS" if async_result.success_rate >= 90 else "FAIL"
            }
            
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Load tests failed: {e}")
        
        return results
    
    async def run_lifecycle_tests(self) -> Dict[str, Any]:
        """Run service lifecycle integration tests."""
        print("Running Service Lifecycle Tests...")
        suite = ServiceLifecycleIntegrationSuite()
        
        results = {
            "category": "service_lifecycle",
            "tests": {},
            "status": "PASS",
            "errors": []
        }
        
        try:
            # Complete startup sequence
            startup_result = await suite.test_complete_startup_sequence()
            results["tests"]["startup_sequence"] = {
                "success": startup_result.success,
                "services_started": startup_result.services_started,
                "execution_time": startup_result.execution_time,
                "status": "PASS" if startup_result.success else "FAIL"
            }
            
            # Dependency resolution
            dependency_result = await suite.test_service_dependency_resolution()
            results["tests"]["dependency_resolution"] = {
                "success": dependency_result.success,
                "services_started": dependency_result.services_started,
                "status": "PASS" if dependency_result.success else "FAIL"
            }
            
            # Graceful shutdown
            shutdown_result = await suite.test_graceful_shutdown_sequence()
            results["tests"]["graceful_shutdown"] = {
                "success": shutdown_result.success,
                "services_shutdown": shutdown_result.services_shutdown,
                "status": "PASS" if shutdown_result.success else "FAIL"
            }
            
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Lifecycle tests failed: {e}")
        
        return results
    
    async def run_gpu_tests(self) -> Dict[str, Any]:
        """Run GPU utilization tests."""
        print("Running GPU Utilization Tests...")
        suite = GPUUtilizationTestSuite()
        
        results = {
            "category": "gpu_utilization",
            "tests": {},
            "status": "PASS",
            "errors": []
        }
        
        try:
            # GPU detection
            detection_result = await suite.test_gpu_detection_and_capabilities()
            results["tests"]["gpu_detection"] = {
                "gpu_available": detection_result.gpu_available,
                "errors": len(detection_result.errors),
                "status": "PASS" if len(detection_result.errors) == 0 else "WARNING"
            }
            
            # Matrix multiplication offloading
            matrix_result = await suite.test_matrix_multiplication_offloading()
            results["tests"]["matrix_offloading"] = {
                "gpu_used": matrix_result.gpu_used,
                "cpu_fallback": matrix_result.cpu_fallback_used,
                "performance_improvement": matrix_result.performance_improvement,
                "status": "PASS" if len(matrix_result.errors) <= 1 else "WARNING"
            }
            
            # CPU fallback
            fallback_result = await suite.test_cpu_fallback_mechanism()
            results["tests"]["cpu_fallback"] = {
                "fallback_used": fallback_result.cpu_fallback_used,
                "errors": len(fallback_result.errors),
                "status": "PASS" if fallback_result.cpu_fallback_used else "FAIL"
            }
            
        except Exception as e:
            results["status"] = "WARNING"  # GPU tests can fail on systems without GPU
            results["errors"].append(f"GPU tests failed: {e}")
        
        return results
    
    async def run_regression_tests(self) -> Dict[str, Any]:
        """Run performance regression tests."""
        print("Running Performance Regression Tests...")
        suite = PerformanceRegressionSuite()
        
        results = {
            "category": "regression_testing",
            "tests": {},
            "status": "PASS",
            "errors": []
        }
        
        try:
            # Run comprehensive regression suite
            regression_results = await suite.run_comprehensive_regression_suite()
            
            for result in regression_results:
                results["tests"][result.test_name] = {
                    "regression_detected": result.regression_detected,
                    "severity": result.severity,
                    "performance_change": result.performance_change,
                    "status": "FAIL" if result.severity == "CRITICAL" else "PASS"
                }
            
            # Overall regression status
            critical_regressions = [r for r in regression_results if r.severity == "CRITICAL"]
            if critical_regressions:
                results["status"] = "FAIL"
                results["errors"].append(f"Critical regressions detected: {len(critical_regressions)}")
            
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Regression tests failed: {e}")
        
        return results
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run optimization integration tests."""
        print("Running Integration Tests...")
        suite = OptimizationIntegrationSuite()
        
        results = {
            "category": "integration_testing",
            "tests": {},
            "status": "PASS",
            "errors": []
        }
        
        try:
            # End-to-end workflow
            e2e_result = await suite.test_end_to_end_optimization_workflow()
            results["tests"]["end_to_end"] = {
                "success": e2e_result.success,
                "components_tested": len(e2e_result.components_tested),
                "execution_time": e2e_result.execution_time,
                "status": "PASS" if e2e_result.success else "FAIL"
            }
            
            # Load testing
            load_result = await suite.test_optimization_under_load()
            results["tests"]["optimization_under_load"] = {
                "success": load_result.success,
                "execution_time": load_result.execution_time,
                "status": "PASS" if load_result.success else "FAIL"
            }
            
            # Requirements validation
            req_result = await suite.test_optimization_requirements_validation()
            results["tests"]["requirements_validation"] = {
                "success": req_result.success,
                "requirements_met": req_result.performance_metrics.get("requirements_met", 0),
                "total_requirements": req_result.performance_metrics.get("requirements_tested", 0),
                "status": "PASS" if req_result.success else "WARNING"
            }
            
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Integration tests failed: {e}")
        
        return results
    
    async def run_complete_validation_suite(self) -> ValidationSummary:
        """Run complete performance validation suite."""
        print("Starting Comprehensive Performance Validation Suite...")
        start_time = time.time()
        
        # Run all test categories
        test_results = {}
        
        test_results["benchmarking"] = await self.run_benchmark_tests()
        test_results["load_testing"] = await self.run_load_tests()
        test_results["service_lifecycle"] = await self.run_lifecycle_tests()
        test_results["gpu_utilization"] = await self.run_gpu_tests()
        test_results["regression_testing"] = await self.run_regression_tests()
        test_results["integration_testing"] = await self.run_integration_tests()
        
        # Calculate summary statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        recommendations = []
        
        for category, results in test_results.items():
            category_tests = len(results["tests"])
            total_tests += category_tests
            
            category_passed = sum(1 for test in results["tests"].values() if test["status"] == "PASS")
            category_failed = category_tests - category_passed
            
            passed_tests += category_passed
            failed_tests += category_failed
            
            # Add category-specific recommendations
            if results["status"] == "FAIL":
                recommendations.append(f"Address failures in {category} tests")
            
            if results["errors"]:
                recommendations.extend([f"{category}: {error}" for error in results["errors"]])
        
        # Determine overall status
        if failed_tests == 0:
            overall_status = "PASS"
        elif failed_tests <= total_tests * 0.2:  # Less than 20% failures
            overall_status = "WARNING"
        else:
            overall_status = "FAIL"
        
        # Collect performance metrics
        execution_time = time.time() - start_time
        performance_metrics = {
            "total_execution_time": execution_time,
            "tests_per_second": total_tests / execution_time if execution_time > 0 else 0,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }
        
        # Create summary
        summary = ValidationSummary(
            timestamp=datetime.now().isoformat(),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            test_categories=test_results,
            performance_metrics=performance_metrics,
            recommendations=recommendations,
            overall_status=overall_status
        )
        
        # Save summary
        self.save_validation_summary(summary)
        
        print(f"\nValidation Suite Complete!")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {performance_metrics['success_rate']:.1f}%")
        print(f"Overall Status: {overall_status}")
        print(f"Execution Time: {execution_time:.1f}s")
        
        return summary
    
    def save_validation_summary(self, summary: ValidationSummary):
        """Save validation summary to file."""
        try:
            os.makedirs(os.path.dirname(self.summary_file), exist_ok=True)
            with open(self.summary_file, 'w') as f:
                json.dump(asdict(summary), f, indent=2)
            print(f"Validation summary saved to {self.summary_file}")
        except Exception as e:
            print(f"Warning: Could not save validation summary: {e}")


@pytest.fixture
def validation_runner():
    """Create performance validation runner fixture."""
    return PerformanceValidationRunner()


@pytest.mark.asyncio
async def test_complete_performance_validation_suite(validation_runner):
    """Run the complete performance validation suite."""
    summary = await validation_runner.run_complete_validation_suite()
    
    # Validation suite should complete
    assert summary.total_tests > 0, "No tests were executed"
    
    # Should have reasonable success rate
    success_rate = (summary.passed_tests / summary.total_tests) * 100
    assert success_rate >= 70.0, f"Success rate too low: {success_rate:.1f}%"
    
    # Should not have critical failures
    assert summary.overall_status != "FAIL", f"Critical validation failures: {summary.recommendations}"
    
    print(f"Performance validation suite: {summary.overall_status}")
    print(f"Success rate: {success_rate:.1f}%")


@pytest.mark.asyncio
async def test_benchmark_suite_only():
    """Run only the benchmark tests."""
    runner = PerformanceValidationRunner()
    results = await runner.run_benchmark_tests()
    
    assert results["status"] in ["PASS", "WARNING"], f"Benchmark tests failed: {results['errors']}"
    assert len(results["tests"]) >= 3, "Not enough benchmark tests executed"
    
    print(f"Benchmark tests: {results['status']}")


@pytest.mark.asyncio
async def test_load_suite_only():
    """Run only the load tests."""
    runner = PerformanceValidationRunner()
    results = await runner.run_load_tests()
    
    assert results["status"] in ["PASS", "WARNING"], f"Load tests failed: {results['errors']}"
    assert len(results["tests"]) >= 3, "Not enough load tests executed"
    
    print(f"Load tests: {results['status']}")


@pytest.mark.asyncio
async def test_integration_suite_only():
    """Run only the integration tests."""
    runner = PerformanceValidationRunner()
    results = await runner.run_integration_tests()
    
    assert results["status"] in ["PASS", "WARNING"], f"Integration tests failed: {results['errors']}"
    assert len(results["tests"]) >= 3, "Not enough integration tests executed"
    
    print(f"Integration tests: {results['status']}")


if __name__ == "__main__":
    # Run the complete validation suite
    async def main():
        runner = PerformanceValidationRunner()
        summary = await runner.run_complete_validation_suite()
        return summary
    
    # For direct execution
    if __name__ == "__main__":
        asyncio.run(main())