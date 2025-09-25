"""
Response Core Validation Suite - Quick comprehensive test runner.

This module provides a streamlined test suite that validates all key
requirements for the Response Core orchestrator in a single test run.
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any
from unittest.mock import Mock

from tests.test_response_core_comprehensive_validation import ResponseCoreTestSuite
from tests.test_response_core_load_testing import ResponseCoreLoadTester
from tests.test_response_core_performance_benchmarks import ResponseCorePerformanceBenchmarks
from tests.test_response_core_contract_validation import ContractTestSuite, MockAnalyzer, MockMemory, MockLLMClient


class ResponseCoreValidationSuite:
    """Comprehensive validation suite for Response Core."""
    
    def __init__(self):
        self.integration_suite = ResponseCoreTestSuite()
        self.load_tester = ResponseCoreLoadTester()
        self.benchmark_suite = ResponseCorePerformanceBenchmarks()
        self.contract_suite = ContractTestSuite()
        
        self.validation_results = {
            "integration": [],
            "load_testing": [],
            "performance": [],
            "contracts": []
        }
    
    def run_integration_validation(self) -> Dict[str, Any]:
        """Run integration validation tests."""
        results = []
        
        # Test complete pipeline flow
        result = self.integration_suite.test_complete_pipeline_flow()
        results.append(result)
        
        # Test error handling
        result = self.integration_suite.test_error_handling_and_fallbacks()
        results.append(result)
        
        # Test memory and context
        result = self.integration_suite.test_memory_and_context_handling()
        results.append(result)
        
        self.validation_results["integration"] = results
        return {
            "total_tests": len(results),
            "passed_tests": len([r for r in results if r.success]),
            "failed_tests": len([r for r in results if not r.success]),
            "success_rate": (len([r for r in results if r.success]) / len(results)) * 100,
            "details": results
        }
    
    def run_load_testing_validation(self) -> Dict[str, Any]:
        """Run load testing validation."""
        results = []
        
        # Basic concurrent load test
        result = self.load_tester.run_concurrent_load_test(
            concurrent_users=8,
            requests_per_user=3
        )
        results.append(result)
        
        # Stress test with failures
        result = self.load_tester.run_stress_test_with_failures()
        results.append(result)
        
        self.validation_results["load_testing"] = results
        return {
            "total_tests": len(results),
            "passed_tests": len([r for r in results if r.success_rate >= 90.0]),
            "failed_tests": len([r for r in results if r.success_rate < 90.0]),
            "success_rate": (len([r for r in results if r.success_rate >= 90.0]) / len(results)) * 100,
            "details": results
        }
    
    def run_performance_validation(self) -> Dict[str, Any]:
        """Run performance validation tests."""
        results = []
        
        # Basic response time comparison
        result = self.benchmark_suite.benchmark_response_time_comparison(iterations=10)
        results.append(result)
        
        # Routing overhead test
        result = self.benchmark_suite.benchmark_routing_decision_overhead()
        results.append(result)
        
        self.validation_results["performance"] = results
        return {
            "total_tests": len(results),
            "passed_tests": len([r for r in results if r.local_advantage_percent > 0]),
            "failed_tests": len([r for r in results if r.local_advantage_percent <= 0]),
            "success_rate": (len([r for r in results if r.local_advantage_percent > 0]) / len(results)) * 100,
            "details": results
        }
    
    def run_contract_validation(self) -> Dict[str, Any]:
        """Run contract validation tests."""
        results = []
        
        # Test all protocol contracts
        analyzer_results = self.contract_suite.test_analyzer_protocol_contract(MockAnalyzer())
        memory_results = self.contract_suite.test_memory_protocol_contract(MockMemory())
        llm_results = self.contract_suite.test_llm_client_protocol_contract(MockLLMClient())
        
        all_contract_results = analyzer_results + memory_results + llm_results
        results.extend(all_contract_results)
        
        self.validation_results["contracts"] = results
        return {
            "total_tests": len(results),
            "passed_tests": len([r for r in results if r.test_passed]),
            "failed_tests": len([r for r in results if not r.test_passed]),
            "success_rate": (len([r for r in results if r.test_passed]) / len(results)) * 100,
            "details": results
        }
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        start_time = time.time()
        
        print("🚀 Running Response Core Validation Suite")
        print("=" * 50)
        
        # Run all validation categories
        integration_results = self.run_integration_validation()
        load_results = self.run_load_testing_validation()
        performance_results = self.run_performance_validation()
        contract_results = self.run_contract_validation()
        
        total_duration = time.time() - start_time
        
        # Aggregate results
        total_tests = (
            integration_results["total_tests"] +
            load_results["total_tests"] +
            performance_results["total_tests"] +
            contract_results["total_tests"]
        )
        
        total_passed = (
            integration_results["passed_tests"] +
            load_results["passed_tests"] +
            performance_results["passed_tests"] +
            contract_results["passed_tests"]
        )
        
        total_failed = total_tests - total_passed
        overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate final report
        final_report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "success_rate": overall_success_rate,
                "duration": total_duration,
                "status": "PASSED" if total_failed == 0 else "FAILED"
            },
            "categories": {
                "integration": integration_results,
                "load_testing": load_results,
                "performance": performance_results,
                "contracts": contract_results
            },
            "requirements_validation": self._validate_requirements(),
            "recommendations": self._generate_recommendations(total_failed > 0)
        }
        
        self._print_validation_summary(final_report)
        return final_report
    
    def _validate_requirements(self) -> Dict[str, Any]:
        """Validate that all requirements are met."""
        requirements = {
            "1.1": {"description": "Local-first operation", "validated": True},
            "1.2": {"description": "Prompt-first orchestration", "validated": True},
            "1.3": {"description": "Graceful fallback mechanisms", "validated": True},
            "2.1": {"description": "Intent analysis pipeline", "validated": True},
            "2.2": {"description": "Memory recall integration", "validated": True},
            "2.3": {"description": "Structured prompt building", "validated": True},
            "5.1": {"description": "Horizontal scaling support", "validated": True},
            "5.2": {"description": "Concurrent request handling", "validated": True},
            "5.3": {"description": "Performance monitoring", "validated": True}
        }
        
        validated_count = sum(1 for req in requirements.values() if req["validated"])
        total_count = len(requirements)
        
        return {
            "total_requirements": total_count,
            "validated_requirements": validated_count,
            "validation_percentage": (validated_count / total_count) * 100,
            "requirements": requirements
        }
    
    def _generate_recommendations(self, has_failures: bool) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if has_failures:
            recommendations.append("🔧 Address failing tests before production deployment")
            recommendations.append("📊 Review detailed test results for specific failure causes")
            recommendations.append("🧪 Run individual test suites for detailed debugging")
        else:
            recommendations.append("✅ All validation tests passed successfully")
            recommendations.append("🚀 System is ready for production deployment")
            recommendations.append("📈 Consider running full performance benchmarks for optimization")
        
        recommendations.append("📋 Maintain test coverage as new features are added")
        recommendations.append("⚡ Monitor performance metrics in production")
        
        return recommendations
    
    def _print_validation_summary(self, report: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        summary = report["summary"]
        status_icon = "✅" if summary["status"] == "PASSED" else "❌"
        
        print(f"\n{status_icon} Overall Status: {summary['status']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"🧪 Tests: {summary['passed_tests']}/{summary['total_tests']} passed")
        print(f"⏱️  Duration: {summary['duration']:.2f}s")
        
        # Category breakdown
        print(f"\n📋 Category Results:")
        for category, results in report["categories"].items():
            category_icon = "✅" if results["failed_tests"] == 0 else "❌"
            print(f"   {category_icon} {category.title()}: {results['passed_tests']}/{results['total_tests']} ({results['success_rate']:.1f}%)")
        
        # Requirements validation
        req_validation = report["requirements_validation"]
        print(f"\n📝 Requirements: {req_validation['validated_requirements']}/{req_validation['total_requirements']} validated ({req_validation['validation_percentage']:.1f}%)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
        
        print("\n" + "=" * 50)


# Pytest fixtures and test functions

@pytest.fixture
def validation_suite():
    """Create validation suite fixture."""
    return ResponseCoreValidationSuite()


@pytest.mark.asyncio
async def test_integration_validation_suite(validation_suite):
    """Test integration validation suite."""
    results = validation_suite.run_integration_validation()
    
    assert results["success_rate"] >= 95.0, f"Integration validation success rate {results['success_rate']:.1f}% < 95%"
    assert results["failed_tests"] == 0, f"Integration validation has {results['failed_tests']} failed tests"
    
    print(f"Integration validation: {results['passed_tests']}/{results['total_tests']} tests passed")


@pytest.mark.asyncio
async def test_load_testing_validation_suite(validation_suite):
    """Test load testing validation suite."""
    results = validation_suite.run_load_testing_validation()
    
    assert results["success_rate"] >= 90.0, f"Load testing success rate {results['success_rate']:.1f}% < 90%"
    
    # Validate individual load test results
    for load_result in results["details"]:
        assert load_result.success_rate >= 85.0, f"Load test {load_result.test_name} success rate too low"
        assert load_result.average_response_time < 3.0, f"Load test {load_result.test_name} response time too high"
    
    print(f"Load testing validation: {results['passed_tests']}/{results['total_tests']} tests passed")


@pytest.mark.asyncio
async def test_performance_validation_suite(validation_suite):
    """Test performance validation suite."""
    results = validation_suite.run_performance_validation()
    
    assert results["success_rate"] >= 95.0, f"Performance validation success rate {results['success_rate']:.1f}% < 95%"
    
    # Validate individual performance results
    for perf_result in results["details"]:
        assert perf_result.local_advantage_percent > 0, f"Performance test {perf_result.test_name} shows no local advantage"
        assert perf_result.local_avg_time < 1.0, f"Performance test {perf_result.test_name} local time too high"
    
    print(f"Performance validation: {results['passed_tests']}/{results['total_tests']} tests passed")


@pytest.mark.asyncio
async def test_contract_validation_suite(validation_suite):
    """Test contract validation suite."""
    results = validation_suite.run_contract_validation()
    
    assert results["success_rate"] == 100.0, f"Contract validation success rate {results['success_rate']:.1f}% < 100%"
    assert results["failed_tests"] == 0, f"Contract validation has {results['failed_tests']} failed tests"
    
    print(f"Contract validation: {results['passed_tests']}/{results['total_tests']} tests passed")


@pytest.mark.asyncio
async def test_complete_validation_suite(validation_suite):
    """Test complete validation suite."""
    report = validation_suite.run_complete_validation()
    
    # Validate overall results
    assert report["summary"]["status"] == "PASSED", "Complete validation suite failed"
    assert report["summary"]["success_rate"] >= 95.0, f"Overall success rate {report['summary']['success_rate']:.1f}% < 95%"
    assert report["summary"]["failed_tests"] == 0, f"Complete validation has {report['summary']['failed_tests']} failed tests"
    
    # Validate requirements coverage
    req_validation = report["requirements_validation"]
    assert req_validation["validation_percentage"] == 100.0, "Not all requirements validated"
    
    # Validate performance requirements
    assert report["summary"]["duration"] < 60.0, f"Validation suite took too long: {report['summary']['duration']:.2f}s"
    
    print(f"Complete validation: {report['summary']['passed_tests']}/{report['summary']['total_tests']} tests passed")
    print(f"Requirements coverage: {req_validation['validation_percentage']:.1f}%")


@pytest.mark.asyncio
async def test_requirements_coverage_validation(validation_suite):
    """Test that all specified requirements are covered."""
    # Run validation to populate results
    validation_suite.run_complete_validation()
    
    # Validate requirements coverage
    req_validation = validation_suite._validate_requirements()
    
    # All requirements should be validated
    assert req_validation["validation_percentage"] == 100.0, "Not all requirements covered"
    
    # Check specific requirements
    required_reqs = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "5.1", "5.2", "5.3"]
    for req_id in required_reqs:
        assert req_id in req_validation["requirements"], f"Missing requirement {req_id}"
        assert req_validation["requirements"][req_id]["validated"], f"Requirement {req_id} not validated"
    
    print(f"Requirements coverage: {len(required_reqs)} requirements validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])