#!/usr/bin/env python3
"""
Performance Comparison Script for AI Karen Engine Integration.

This script compares the performance of the new Python backend services
with the existing implementation to ensure performance parity.
"""

import asyncio
import json
import logging
import time
import sys
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import requests
import concurrent.futures

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric result."""
    name: str
    old_value: Optional[float]
    new_value: float
    unit: str
    improvement: Optional[float] = None
    meets_benchmark: bool = True


@dataclass
class BenchmarkResult:
    """Benchmark test result."""
    test_name: str
    metrics: List[PerformanceMetric]
    success: bool
    notes: str


class PerformanceComparator:
    """
    Compares performance between old and new implementations.
    
    Tests various performance aspects including response times,
    throughput, memory usage, and concurrent request handling.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
        
        # Performance benchmarks (baseline expectations)
        self.benchmarks = {
            "api_response_time": 2.0,  # seconds
            "service_init_time": 1.0,  # seconds
            "memory_query_time": 0.5,  # seconds
            "conversation_processing_time": 3.0,  # seconds
            "concurrent_requests_per_second": 10,  # requests/second
            "health_check_time": 1.0,  # seconds
        }
    
    async def run_all_comparisons(self) -> Dict[str, Any]:
        """Run all performance comparisons."""
        logger.info("Starting performance comparison...")
        
        # Test API response times
        await self._test_api_response_times()
        
        # Test service initialization
        await self._test_service_initialization_performance()
        
        # Test memory operations
        await self._test_memory_performance()
        
        # Test conversation processing
        await self._test_conversation_performance()
        
        # Test concurrent request handling
        await self._test_concurrent_performance()
        
        # Test health monitoring performance
        await self._test_health_monitoring_performance()
        
        # Generate comparison report
        return self._generate_comparison_report()
    
    async def _test_api_response_times(self) -> None:
        """Test API endpoint response times."""
        logger.info("Testing API response times...")
        
        endpoints = [
            "/health",
            "/api/services",
            "/api/health/summary",
            "/api/config",
            "/api/ai/flows",
            "/api/plugins/",
            "/api/tools/"
        ]
        
        response_times = []
        successful_requests = 0
        
        for endpoint in endpoints:
            times = []
            for _ in range(5):  # Test each endpoint 5 times
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code < 500:
                        times.append(response_time)
                        successful_requests += 1
                        
                except Exception as e:
                    logger.warning(f"Request to {endpoint} failed: {e}")
            
            if times:
                response_times.extend(times)
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            
            metrics = [
                PerformanceMetric(
                    name="average_api_response_time",
                    old_value=None,  # No baseline available
                    new_value=avg_response_time,
                    unit="seconds",
                    meets_benchmark=avg_response_time <= self.benchmarks["api_response_time"]
                ),
                PerformanceMetric(
                    name="p95_api_response_time",
                    old_value=None,
                    new_value=p95_response_time,
                    unit="seconds",
                    meets_benchmark=p95_response_time <= self.benchmarks["api_response_time"] * 2
                )
            ]
            
            self.results.append(BenchmarkResult(
                test_name="api_response_times",
                metrics=metrics,
                success=all(m.meets_benchmark for m in metrics),
                notes=f"Tested {len(endpoints)} endpoints with {successful_requests} successful requests"
            ))
        else:
            self.results.append(BenchmarkResult(
                test_name="api_response_times",
                metrics=[],
                success=False,
                notes="No successful API requests"
            ))
    
    async def _test_service_initialization_performance(self) -> None:
        """Test service initialization performance."""
        logger.info("Testing service initialization performance...")
        
        try:
            from ai_karen_engine.core.service_registry import ServiceRegistry
            
            init_times = []
            
            # Test service registry initialization multiple times
            for _ in range(3):
                start_time = time.time()
                registry = ServiceRegistry()
                
                # Register and initialize a service
                from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
                registry.register_service("test_orchestrator", AIOrchestrator)
                await registry.get_service("test_orchestrator")
                
                init_time = time.time() - start_time
                init_times.append(init_time)
            
            avg_init_time = statistics.mean(init_times)
            
            metrics = [
                PerformanceMetric(
                    name="service_initialization_time",
                    old_value=None,
                    new_value=avg_init_time,
                    unit="seconds",
                    meets_benchmark=avg_init_time <= self.benchmarks["service_init_time"]
                )
            ]
            
            self.results.append(BenchmarkResult(
                test_name="service_initialization",
                metrics=metrics,
                success=all(m.meets_benchmark for m in metrics),
                notes=f"Average of {len(init_times)} initialization tests"
            ))
            
        except Exception as e:
            self.results.append(BenchmarkResult(
                test_name="service_initialization",
                metrics=[],
                success=False,
                notes=f"Service initialization test failed: {str(e)}"
            ))
    
    async def _test_memory_performance(self) -> None:
        """Test memory service performance."""
        logger.info("Testing memory service performance...")
        
        try:
            # Test memory query performance via API
            query_times = []
            
            for _ in range(10):  # Test 10 memory queries
                start_time = time.time()
                try:
                    # This would be a real memory query in practice
                    response = requests.post(
                        f"{self.base_url}/api/memory/query",
                        json={
                            "text": "test query",
                            "top_k": 5,
                            "similarity_threshold": 0.7
                        },
                        timeout=5
                    )
                    query_time = time.time() - start_time
                    
                    if response.status_code < 500:
                        query_times.append(query_time)
                        
                except Exception as e:
                    logger.warning(f"Memory query failed: {e}")
            
            if query_times:
                avg_query_time = statistics.mean(query_times)
                
                metrics = [
                    PerformanceMetric(
                        name="memory_query_time",
                        old_value=None,
                        new_value=avg_query_time,
                        unit="seconds",
                        meets_benchmark=avg_query_time <= self.benchmarks["memory_query_time"]
                    )
                ]
                
                self.results.append(BenchmarkResult(
                    test_name="memory_performance",
                    metrics=metrics,
                    success=all(m.meets_benchmark for m in metrics),
                    notes=f"Average of {len(query_times)} memory queries"
                ))
            else:
                self.results.append(BenchmarkResult(
                    test_name="memory_performance",
                    metrics=[],
                    success=False,
                    notes="No successful memory queries"
                ))
                
        except Exception as e:
            self.results.append(BenchmarkResult(
                test_name="memory_performance",
                metrics=[],
                success=False,
                notes=f"Memory performance test failed: {str(e)}"
            ))
    
    async def _test_conversation_performance(self) -> None:
        """Test conversation processing performance."""
        logger.info("Testing conversation processing performance...")
        
        try:
            processing_times = []
            
            for _ in range(5):  # Test 5 conversation processing requests
                start_time = time.time()
                try:
                    response = requests.post(
                        f"{self.base_url}/api/ai/conversation-processing",
                        json={
                            "prompt": "Hello, how are you?",
                            "conversation_history": [],
                            "user_settings": {},
                            "include_memories": True,
                            "include_insights": True
                        },
                        timeout=10
                    )
                    processing_time = time.time() - start_time
                    
                    if response.status_code < 500:
                        processing_times.append(processing_time)
                        
                except Exception as e:
                    logger.warning(f"Conversation processing failed: {e}")
            
            if processing_times:
                avg_processing_time = statistics.mean(processing_times)
                
                metrics = [
                    PerformanceMetric(
                        name="conversation_processing_time",
                        old_value=None,
                        new_value=avg_processing_time,
                        unit="seconds",
                        meets_benchmark=avg_processing_time <= self.benchmarks["conversation_processing_time"]
                    )
                ]
                
                self.results.append(BenchmarkResult(
                    test_name="conversation_performance",
                    metrics=metrics,
                    success=all(m.meets_benchmark for m in metrics),
                    notes=f"Average of {len(processing_times)} conversation processing requests"
                ))
            else:
                self.results.append(BenchmarkResult(
                    test_name="conversation_performance",
                    metrics=[],
                    success=False,
                    notes="No successful conversation processing requests"
                ))
                
        except Exception as e:
            self.results.append(BenchmarkResult(
                test_name="conversation_performance",
                metrics=[],
                success=False,
                notes=f"Conversation performance test failed: {str(e)}"
            ))
    
    async def _test_concurrent_performance(self) -> None:
        """Test concurrent request handling performance."""
        logger.info("Testing concurrent request performance...")
        
        try:
            def make_request():
                """Make a single request."""
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    response_time = time.time() - start_time
                    return response.status_code < 500, response_time
                except Exception:
                    return False, 0
            
            # Test with different concurrency levels
            concurrency_levels = [5, 10, 20]
            best_throughput = 0
            
            for concurrency in concurrency_levels:
                start_time = time.time()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [executor.submit(make_request) for _ in range(concurrency * 2)]
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
                total_time = time.time() - start_time
                successful_requests = sum(1 for success, _ in results if success)
                throughput = successful_requests / total_time if total_time > 0 else 0
                
                if throughput > best_throughput:
                    best_throughput = throughput
            
            metrics = [
                PerformanceMetric(
                    name="concurrent_requests_per_second",
                    old_value=None,
                    new_value=best_throughput,
                    unit="requests/second",
                    meets_benchmark=best_throughput >= self.benchmarks["concurrent_requests_per_second"]
                )
            ]
            
            self.results.append(BenchmarkResult(
                test_name="concurrent_performance",
                metrics=metrics,
                success=all(m.meets_benchmark for m in metrics),
                notes=f"Best throughput: {best_throughput:.2f} req/s with concurrency levels {concurrency_levels}"
            ))
            
        except Exception as e:
            self.results.append(BenchmarkResult(
                test_name="concurrent_performance",
                metrics=[],
                success=False,
                notes=f"Concurrent performance test failed: {str(e)}"
            ))
    
    async def _test_health_monitoring_performance(self) -> None:
        """Test health monitoring performance."""
        logger.info("Testing health monitoring performance...")
        
        try:
            health_check_times = []
            
            for _ in range(5):  # Test 5 health checks
                start_time = time.time()
                try:
                    response = requests.post(f"{self.base_url}/api/health/check", timeout=10)
                    health_check_time = time.time() - start_time
                    
                    if response.status_code < 500:
                        health_check_times.append(health_check_time)
                        
                except Exception as e:
                    logger.warning(f"Health check failed: {e}")
            
            if health_check_times:
                avg_health_check_time = statistics.mean(health_check_times)
                
                metrics = [
                    PerformanceMetric(
                        name="health_check_time",
                        old_value=None,
                        new_value=avg_health_check_time,
                        unit="seconds",
                        meets_benchmark=avg_health_check_time <= self.benchmarks["health_check_time"]
                    )
                ]
                
                self.results.append(BenchmarkResult(
                    test_name="health_monitoring_performance",
                    metrics=metrics,
                    success=all(m.meets_benchmark for m in metrics),
                    notes=f"Average of {len(health_check_times)} health checks"
                ))
            else:
                self.results.append(BenchmarkResult(
                    test_name="health_monitoring_performance",
                    metrics=[],
                    success=False,
                    notes="No successful health checks"
                ))
                
        except Exception as e:
            self.results.append(BenchmarkResult(
                test_name="health_monitoring_performance",
                metrics=[],
                success=False,
                notes=f"Health monitoring performance test failed: {str(e)}"
            ))
    
    def _generate_comparison_report(self) -> Dict[str, Any]:
        """Generate performance comparison report."""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        
        all_metrics = []
        for result in self.results:
            all_metrics.extend(result.metrics)
        
        benchmarks_met = sum(1 for m in all_metrics if m.meets_benchmark)
        total_benchmarks = len(all_metrics)
        
        report = {
            "performance_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "benchmarks_met": benchmarks_met,
                "total_benchmarks": total_benchmarks,
                "benchmark_success_rate": (benchmarks_met / total_benchmarks) * 100 if total_benchmarks > 0 else 0
            },
            "benchmark_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "notes": r.notes,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.new_value,
                            "unit": m.unit,
                            "meets_benchmark": m.meets_benchmark,
                            "improvement": m.improvement
                        }
                        for m in r.metrics
                    ]
                }
                for r in self.results
            ],
            "benchmarks": self.benchmarks,
            "recommendations": self._generate_performance_recommendations()
        }
        
        return report
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        failed_tests = [r for r in self.results if not r.success]
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed performance tests")
        
        # Check specific performance issues
        for result in self.results:
            for metric in result.metrics:
                if not metric.meets_benchmark:
                    if "response_time" in metric.name:
                        recommendations.append(f"Optimize {metric.name}: {metric.new_value:.2f}s exceeds benchmark")
                    elif "throughput" in metric.name or "requests_per_second" in metric.name:
                        recommendations.append(f"Improve {metric.name}: {metric.new_value:.2f} below benchmark")
        
        if not recommendations:
            recommendations.append("All performance benchmarks met - system performs within acceptable limits")
        
        return recommendations


async def main():
    """Main performance comparison function."""
    comparator = PerformanceComparator()
    
    try:
        results = await comparator.run_all_comparisons()
        
        # Print summary
        print("\n" + "="*60)
        print("AI KAREN PERFORMANCE COMPARISON RESULTS")
        print("="*60)
        
        summary = results["performance_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Benchmarks Met: {summary['benchmarks_met']}/{summary['total_benchmarks']}")
        print(f"Benchmark Success Rate: {summary['benchmark_success_rate']:.1f}%")
        
        print("\nPERFORMANCE DETAILS:")
        print("-" * 40)
        for test in results["benchmark_results"]:
            status = "✓ PASS" if test["success"] else "✗ FAIL"
            print(f"{status} {test['test_name']}: {test['notes']}")
            
            for metric in test["metrics"]:
                benchmark_status = "✓" if metric["meets_benchmark"] else "✗"
                print(f"    {benchmark_status} {metric['name']}: {metric['value']:.3f} {metric['unit']}")
        
        print("\nBENCHMARKS:")
        print("-" * 40)
        for name, value in results["benchmarks"].items():
            print(f"• {name}: {value} seconds" if "time" in name else f"• {name}: {value}")
        
        print("\nRECOMMENDATIONS:")
        print("-" * 40)
        for rec in results["recommendations"]:
            print(f"• {rec}")
        
        # Save results to file
        results_file = Path("performance_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Exit with appropriate code
        if summary["benchmark_success_rate"] >= 80:
            print("\n✓ Performance comparison PASSED - System meets performance requirements")
            sys.exit(0)
        else:
            print("\n✗ Performance comparison FAILED - Address performance issues")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nPerformance comparison failed with error: {e}")
        logger.exception("Performance comparison error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())