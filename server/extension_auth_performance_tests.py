"""
Extension Authentication Performance Testing

This module provides comprehensive performance testing utilities for extension
authentication systems, measuring overhead and identifying bottlenecks.
"""

import asyncio
import time
import statistics
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from server.extension_test_auth_utils import TestTokenGenerator, AuthPerformanceTester
from server.extension_auth_integration_helpers import FastAPIAuthTestClient, AsyncAuthTestClient

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    operation: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    total_time_seconds: float
    average_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    operations_per_second: float
    cpu_usage_percent: float
    memory_usage_mb: float
    error_rate: float


class AuthenticationOverheadTester:
    """Test authentication overhead compared to non-authenticated requests."""
    
    def __init__(self, client: FastAPIAuthTestClient):
        self.client = client
        self.results = []
    
    async def measure_auth_overhead(
        self,
        endpoint: str,
        method: str = "GET",
        iterations: int = 1000,
        warmup_iterations: int = 100
    ) -> Dict[str, Any]:
        """Measure authentication overhead by comparing authenticated vs non-authenticated requests."""
        
        logger.info(f"Measuring auth overhead for {method} {endpoint} ({iterations} iterations)")
        
        # Warmup
        await self._warmup_requests(endpoint, method, warmup_iterations)
        
        # Test non-authenticated requests (if endpoint supports it)
        no_auth_metrics = await self._measure_request_performance(
            endpoint, method, "none", iterations, "no_auth"
        )
        
        # Test authenticated requests
        auth_metrics = await self._measure_request_performance(
            endpoint, method, "user", iterations, "authenticated"
        )
        
        # Calculate overhead
        overhead_ms = auth_metrics.average_time_ms - no_auth_metrics.average_time_ms
        overhead_percent = (overhead_ms / no_auth_metrics.average_time_ms) * 100 if no_auth_metrics.average_time_ms > 0 else 0
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "no_auth_metrics": no_auth_metrics,
            "auth_metrics": auth_metrics,
            "overhead_ms": overhead_ms,
            "overhead_percent": overhead_percent,
            "throughput_impact": {
                "no_auth_rps": no_auth_metrics.operations_per_second,
                "auth_rps": auth_metrics.operations_per_second,
                "rps_reduction": no_auth_metrics.operations_per_second - auth_metrics.operations_per_second,
                "rps_reduction_percent": ((no_auth_metrics.operations_per_second - auth_metrics.operations_per_second) / no_auth_metrics.operations_per_second) * 100 if no_auth_metrics.operations_per_second > 0 else 0
            }
        }
        
        self.results.append(result)
        return result
    
    async def _warmup_requests(self, endpoint: str, method: str, iterations: int):
        """Warmup requests to stabilize performance."""
        logger.debug(f"Warming up with {iterations} requests")
        
        for _ in range(iterations):
            try:
                if method.upper() == "GET":
                    self.client.get(endpoint, auth_type="user")
                elif method.upper() == "POST":
                    self.client.post(endpoint, auth_type="user", json_data={})
            except Exception:
                pass  # Ignore warmup errors
    
    async def _measure_request_performance(
        self,
        endpoint: str,
        method: str,
        auth_type: str,
        iterations: int,
        test_name: str
    ) -> PerformanceMetrics:
        """Measure performance of requests with specific auth type."""
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Monitor system resources
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        for i in range(iterations):
            request_start = time.perf_counter()
            
            try:
                if method.upper() == "GET":
                    response = self.client.get(endpoint, auth_type=auth_type)
                elif method.upper() == "POST":
                    response = self.client.post(endpoint, auth_type=auth_type, json_data={})
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                request_time = (time.perf_counter() - request_start) * 1000  # Convert to ms
                response_times.append(request_time)
                
                if response.status_code < 400:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                failed_requests += 1
                logger.debug(f"Request {i} failed: {e}")
        
        total_time = time.time() - start_time
        
        # Monitor system resources after
        cpu_after = process.cpu_percent()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Calculate metrics
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_time = min_time = max_time = p95_time = p99_time = 0
        
        return PerformanceMetrics(
            operation=test_name,
            total_operations=iterations,
            successful_operations=successful_requests,
            failed_operations=failed_requests,
            total_time_seconds=total_time,
            average_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            p95_time_ms=p95_time,
            p99_time_ms=p99_time,
            operations_per_second=iterations / total_time,
            cpu_usage_percent=(cpu_after - cpu_before),
            memory_usage_mb=(memory_after - memory_before),
            error_rate=failed_requests / iterations
        )


class ConcurrentAuthTester:
    """Test authentication performance under concurrent load."""
    
    def __init__(self, client: FastAPIAuthTestClient):
        self.client = client
        self.results = []
    
    async def test_concurrent_authentication(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_users: List[int] = None,
        requests_per_user: int = 100
    ) -> List[Dict[str, Any]]:
        """Test authentication performance with varying concurrent users."""
        
        if concurrent_users is None:
            concurrent_users = [1, 5, 10, 20, 50, 100]
        
        results = []
        
        for user_count in concurrent_users:
            logger.info(f"Testing {user_count} concurrent users")
            
            result = await self._test_concurrent_load(
                endpoint, method, user_count, requests_per_user
            )
            results.append(result)
        
        self.results.extend(results)
        return results
    
    async def _test_concurrent_load(
        self,
        endpoint: str,
        method: str,
        concurrent_users: int,
        requests_per_user: int
    ) -> Dict[str, Any]:
        """Test specific concurrent load scenario."""
        
        total_requests = concurrent_users * requests_per_user
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Monitor system resources
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def user_requests():
            """Simulate one user making multiple requests."""
            nonlocal successful_requests, failed_requests
            
            user_response_times = []
            
            for _ in range(requests_per_user):
                async with semaphore:
                    request_start = time.perf_counter()
                    
                    try:
                        if method.upper() == "GET":
                            response = self.client.get(endpoint, auth_type="user")
                        elif method.upper() == "POST":
                            response = self.client.post(endpoint, auth_type="user", json_data={})
                        else:
                            raise ValueError(f"Unsupported method: {method}")
                        
                        request_time = (time.perf_counter() - request_start) * 1000
                        user_response_times.append(request_time)
                        
                        if response.status_code < 400:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                            
                    except Exception as e:
                        failed_requests += 1
                        logger.debug(f"Concurrent request failed: {e}")
            
            response_times.extend(user_response_times)
        
        # Run concurrent users
        tasks = [user_requests() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Monitor system resources after
        cpu_after = process.cpu_percent()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Calculate metrics
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max_time
            p99_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max_time
        else:
            avg_time = min_time = max_time = p95_time = p99_time = 0
        
        return {
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time_seconds": total_time,
            "average_response_time_ms": avg_time,
            "min_response_time_ms": min_time,
            "max_response_time_ms": max_time,
            "p95_response_time_ms": p95_time,
            "p99_response_time_ms": p99_time,
            "requests_per_second": total_requests / total_time,
            "cpu_usage_change_percent": cpu_after - cpu_before,
            "memory_usage_change_mb": memory_after - memory_before,
            "error_rate": failed_requests / total_requests,
            "success_rate": successful_requests / total_requests
        }


class TokenPerformanceTester:
    """Test JWT token operations performance."""
    
    def __init__(self, token_generator: TestTokenGenerator = None):
        self.token_generator = token_generator or TestTokenGenerator()
        self.results = []
    
    async def test_token_operations_performance(
        self,
        iterations: int = 10000
    ) -> Dict[str, Any]:
        """Test performance of token generation and validation operations."""
        
        logger.info(f"Testing token operations performance ({iterations} iterations)")
        
        # Test token generation
        generation_result = await self._test_token_generation(iterations)
        
        # Test token validation
        validation_result = await self._test_token_validation(iterations)
        
        # Test token decoding
        decoding_result = await self._test_token_decoding(iterations)
        
        result = {
            "iterations": iterations,
            "token_generation": generation_result,
            "token_validation": validation_result,
            "token_decoding": decoding_result,
            "recommendations": self._generate_token_recommendations([
                generation_result, validation_result, decoding_result
            ])
        }
        
        self.results.append(result)
        return result
    
    async def _test_token_generation(self, iterations: int) -> Dict[str, Any]:
        """Test token generation performance."""
        
        response_times = []
        successful_operations = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            operation_start = time.perf_counter()
            
            try:
                token = self.token_generator.generate_access_token(
                    user_id=f"user-{i}",
                    tenant_id=f"tenant-{i % 10}"
                )
                
                operation_time = (time.perf_counter() - operation_start) * 1000
                response_times.append(operation_time)
                
                if token and len(token) > 0:
                    successful_operations += 1
                    
            except Exception as e:
                logger.debug(f"Token generation {i} failed: {e}")
        
        total_time = time.time() - start_time
        
        return {
            "operation": "token_generation",
            "successful_operations": successful_operations,
            "failed_operations": iterations - successful_operations,
            "average_time_ms": statistics.mean(response_times) if response_times else 0,
            "min_time_ms": min(response_times) if response_times else 0,
            "max_time_ms": max(response_times) if response_times else 0,
            "operations_per_second": iterations / total_time,
            "total_time_seconds": total_time
        }
    
    async def _test_token_validation(self, iterations: int) -> Dict[str, Any]:
        """Test token validation performance."""
        
        # Pre-generate tokens for validation
        tokens = [
            self.token_generator.generate_access_token(user_id=f"user-{i}")
            for i in range(min(100, iterations))
        ]
        
        response_times = []
        successful_operations = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            token = tokens[i % len(tokens)]
            operation_start = time.perf_counter()
            
            try:
                payload = self.token_generator.decode_token(token)
                
                operation_time = (time.perf_counter() - operation_start) * 1000
                response_times.append(operation_time)
                
                if payload and payload.get('user_id'):
                    successful_operations += 1
                    
            except Exception as e:
                logger.debug(f"Token validation {i} failed: {e}")
        
        total_time = time.time() - start_time
        
        return {
            "operation": "token_validation",
            "successful_operations": successful_operations,
            "failed_operations": iterations - successful_operations,
            "average_time_ms": statistics.mean(response_times) if response_times else 0,
            "min_time_ms": min(response_times) if response_times else 0,
            "max_time_ms": max(response_times) if response_times else 0,
            "operations_per_second": iterations / total_time,
            "total_time_seconds": total_time
        }
    
    async def _test_token_decoding(self, iterations: int) -> Dict[str, Any]:
        """Test raw token decoding performance (without validation)."""
        
        import jwt
        
        # Pre-generate tokens
        tokens = [
            self.token_generator.generate_access_token(user_id=f"user-{i}")
            for i in range(min(100, iterations))
        ]
        
        response_times = []
        successful_operations = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            token = tokens[i % len(tokens)]
            operation_start = time.perf_counter()
            
            try:
                # Decode without verification for pure decoding performance
                payload = jwt.decode(token, options={"verify_signature": False})
                
                operation_time = (time.perf_counter() - operation_start) * 1000
                response_times.append(operation_time)
                
                if payload and payload.get('user_id'):
                    successful_operations += 1
                    
            except Exception as e:
                logger.debug(f"Token decoding {i} failed: {e}")
        
        total_time = time.time() - start_time
        
        return {
            "operation": "token_decoding",
            "successful_operations": successful_operations,
            "failed_operations": iterations - successful_operations,
            "average_time_ms": statistics.mean(response_times) if response_times else 0,
            "min_time_ms": min(response_times) if response_times else 0,
            "max_time_ms": max(response_times) if response_times else 0,
            "operations_per_second": iterations / total_time,
            "total_time_seconds": total_time
        }
    
    def _generate_token_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate performance recommendations for token operations."""
        
        recommendations = []
        
        for result in results:
            operation = result["operation"]
            avg_time = result["average_time_ms"]
            ops_per_sec = result["operations_per_second"]
            
            if operation == "token_generation":
                if avg_time > 10:
                    recommendations.append(
                        f"Token generation is slow ({avg_time:.2f}ms). Consider using faster JWT library or caching."
                    )
                if ops_per_sec < 1000:
                    recommendations.append(
                        f"Token generation throughput is low ({ops_per_sec:.0f} ops/sec). Consider optimization."
                    )
            
            elif operation == "token_validation":
                if avg_time > 5:
                    recommendations.append(
                        f"Token validation is slow ({avg_time:.2f}ms). Consider caching or optimization."
                    )
                if ops_per_sec < 2000:
                    recommendations.append(
                        f"Token validation throughput is low ({ops_per_sec:.0f} ops/sec). Consider optimization."
                    )
            
            elif operation == "token_decoding":
                if avg_time > 1:
                    recommendations.append(
                        f"Token decoding is slow ({avg_time:.2f}ms). Consider JWT library optimization."
                    )
        
        return recommendations


class AuthPerformanceTestSuite:
    """Comprehensive authentication performance test suite."""
    
    def __init__(self, client: FastAPIAuthTestClient):
        self.client = client
        self.overhead_tester = AuthenticationOverheadTester(client)
        self.concurrent_tester = ConcurrentAuthTester(client)
        self.token_tester = TokenPerformanceTester()
        self.results = {}
    
    async def run_full_performance_suite(
        self,
        endpoints: List[str],
        methods: List[str] = None
    ) -> Dict[str, Any]:
        """Run complete performance test suite."""
        
        if methods is None:
            methods = ["GET"]
        
        logger.info("Starting comprehensive authentication performance test suite")
        
        # Test authentication overhead
        overhead_results = []
        for endpoint in endpoints:
            for method in methods:
                try:
                    result = await self.overhead_tester.measure_auth_overhead(
                        endpoint, method, iterations=1000
                    )
                    overhead_results.append(result)
                except Exception as e:
                    logger.error(f"Overhead test failed for {method} {endpoint}: {e}")
        
        # Test concurrent authentication
        concurrent_results = []
        for endpoint in endpoints[:1]:  # Test only first endpoint for concurrency
            for method in methods[:1]:  # Test only first method
                try:
                    results = await self.concurrent_tester.test_concurrent_authentication(
                        endpoint, method, concurrent_users=[1, 5, 10, 20]
                    )
                    concurrent_results.extend(results)
                except Exception as e:
                    logger.error(f"Concurrent test failed for {method} {endpoint}: {e}")
        
        # Test token operations
        try:
            token_results = await self.token_tester.test_token_operations_performance(
                iterations=5000
            )
        except Exception as e:
            logger.error(f"Token performance test failed: {e}")
            token_results = {}
        
        # Compile results
        self.results = {
            "test_summary": {
                "endpoints_tested": len(endpoints),
                "methods_tested": len(methods),
                "total_overhead_tests": len(overhead_results),
                "total_concurrent_tests": len(concurrent_results),
                "token_tests_completed": bool(token_results)
            },
            "overhead_results": overhead_results,
            "concurrent_results": concurrent_results,
            "token_results": token_results,
            "overall_recommendations": self._generate_overall_recommendations(
                overhead_results, concurrent_results, token_results
            )
        }
        
        logger.info("Performance test suite completed")
        return self.results
    
    def _generate_overall_recommendations(
        self,
        overhead_results: List[Dict[str, Any]],
        concurrent_results: List[Dict[str, Any]],
        token_results: Dict[str, Any]
    ) -> List[str]:
        """Generate overall performance recommendations."""
        
        recommendations = []
        
        # Analyze overhead results
        if overhead_results:
            avg_overhead = statistics.mean([r["overhead_ms"] for r in overhead_results])
            if avg_overhead > 50:
                recommendations.append(
                    f"High authentication overhead detected ({avg_overhead:.1f}ms average). "
                    "Consider optimizing authentication middleware."
                )
        
        # Analyze concurrent results
        if concurrent_results:
            high_load_results = [r for r in concurrent_results if r["concurrent_users"] >= 20]
            if high_load_results:
                avg_error_rate = statistics.mean([r["error_rate"] for r in high_load_results])
                if avg_error_rate > 0.05:  # 5% error rate
                    recommendations.append(
                        f"High error rate under load ({avg_error_rate:.1%}). "
                        "Consider scaling authentication infrastructure."
                    )
        
        # Analyze token results
        if token_results and "token_generation" in token_results:
            gen_ops_per_sec = token_results["token_generation"]["operations_per_second"]
            if gen_ops_per_sec < 1000:
                recommendations.append(
                    f"Low token generation throughput ({gen_ops_per_sec:.0f} ops/sec). "
                    "Consider JWT library optimization or caching."
                )
        
        return recommendations
    
    def export_results(self, filename: str = "auth_performance_results.json"):
        """Export results to JSON file."""
        import json
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Performance results exported to {filename}")


# Convenience function for quick performance testing
async def quick_auth_performance_test(
    client: FastAPIAuthTestClient,
    endpoint: str = "/api/extensions/",
    method: str = "GET"
) -> Dict[str, Any]:
    """Quick authentication performance test for a single endpoint."""
    
    suite = AuthPerformanceTestSuite(client)
    return await suite.run_full_performance_suite([endpoint], [method])