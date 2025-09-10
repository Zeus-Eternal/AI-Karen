"""
Performance and Load Testing for HTTP Request Validation System

This module provides performance-focused integration tests for the HTTP request
validation enhancement system, focusing on:
- Performance under high load conditions
- Memory usage and resource management
- Scalability testing
- Stress testing scenarios
- Performance regression detection

Requirements covered: 1.1, 1.4, 4.1, 4.2, 4.3, 4.4
"""

import asyncio
import gc
import logging
import psutil
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from unittest.mock import Mock

import pytest_asyncio

# Import validation system components
from src.ai_karen_engine.server.http_validator import (
    HTTPRequestValidator,
    ValidationConfig
)
from src.ai_karen_engine.server.security_analyzer import SecurityAnalyzer
from src.ai_karen_engine.server.rate_limiter import (
    EnhancedRateLimiter,
    MemoryRateLimitStorage,
    RateLimitRule,
    RateLimitScope,
    RateLimitAlgorithm
)


class PerformanceMonitor:
    """Utility class for monitoring performance metrics during tests."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        self.process = psutil.Process()
    
    def start(self):
        """Start performance monitoring."""
        gc.collect()  # Clean up before measurement
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
    
    def update_peak_memory(self):
        """Update peak memory usage."""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.peak_memory, current_memory)
    
    def stop(self):
        """Stop performance monitoring and return metrics."""
        self.end_time = time.time()
        gc.collect()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'duration_seconds': self.end_time - self.start_time,
            'start_memory_mb': self.start_memory,
            'end_memory_mb': self.end_memory,
            'peak_memory_mb': self.peak_memory,
            'memory_increase_mb': self.end_memory - self.start_memory,
            'cpu_percent': self.process.cpu_percent()
        }


class TestValidationPerformance:
    """Performance tests for the validation system."""
    
    @pytest.fixture
    def performance_config(self):
        """Create optimized configuration for performance testing."""
        return ValidationConfig(
            max_content_length=10 * 1024 * 1024,  # 10MB
            allowed_methods={"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"},
            max_header_size=8192,
            max_headers_count=100,
            enable_security_analysis=True,
            log_invalid_requests=False,  # Disable logging for performance
        )
    
    @pytest.fixture
    def performance_rate_rules(self):
        """Create rate limiting rules optimized for performance testing."""
        return [
            RateLimitRule(
                name="performance_test",
                scope=RateLimitScope.IP,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                limit=1000,
                window_seconds=60,
                priority=10
            )
        ]
    
    def create_test_request(self, request_id: int, client_ip: str = None):
        """Create a test request for performance testing."""
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = f"/api/test/{request_id}"
        request.url.query = f"id={request_id}&page=1"
        request.headers = {
            "user-agent": f"test-client-{request_id}",
            "content-type": "application/json",
            "authorization": f"Bearer token-{request_id}"
        }
        request.query_params = {"id": str(request_id), "page": "1"}
        request.client = Mock()
        request.client.host = client_ip or f"192.168.{(request_id % 255) + 1}.{(request_id % 255) + 1}"
        return request
    
    @pytest.mark.asyncio
    async def test_validator_throughput(self, performance_config):
        """Test HTTP validator throughput under load."""
        validator = HTTPRequestValidator(performance_config)
        monitor = PerformanceMonitor()
        
        # Test parameters
        num_requests = 1000
        batch_size = 100
        
        print(f"\nTesting validator throughput with {num_requests} requests...")
        
        monitor.start()
        
        # Process requests in batches to avoid overwhelming the system
        total_processed = 0
        valid_requests = 0
        invalid_requests = 0
        
        for batch_start in range(0, num_requests, batch_size):
            batch_end = min(batch_start + batch_size, num_requests)
            batch_requests = []
            
            # Create batch of requests
            for i in range(batch_start, batch_end):
                # Mix of valid and invalid requests for realistic testing
                if i % 10 == 0:  # 10% invalid requests
                    request = self.create_test_request(i)
                    request.method = "INVALID"  # Make it invalid
                else:
                    request = self.create_test_request(i)
                batch_requests.append(request)
            
            # Process batch concurrently
            tasks = [validator.validate_request(req) for req in batch_requests]
            results = await asyncio.gather(*tasks)
            
            # Count results
            for result in results:
                total_processed += 1
                if result.is_valid:
                    valid_requests += 1
                else:
                    invalid_requests += 1
            
            monitor.update_peak_memory()
        
        metrics = monitor.stop()
        
        # Calculate performance metrics
        throughput = total_processed / metrics['duration_seconds']
        avg_latency_ms = (metrics['duration_seconds'] * 1000) / total_processed
        
        print(f"Validator Performance Results:")
        print(f"  Total requests: {total_processed}")
        print(f"  Valid requests: {valid_requests}")
        print(f"  Invalid requests: {invalid_requests}")
        print(f"  Duration: {metrics['duration_seconds']:.2f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average latency: {avg_latency_ms:.2f}ms")
        print(f"  Memory usage: {metrics['start_memory_mb']:.1f}MB -> {metrics['end_memory_mb']:.1f}MB")
        print(f"  Peak memory: {metrics['peak_memory_mb']:.1f}MB")
        print(f"  Memory increase: {metrics['memory_increase_mb']:.1f}MB")
        
        # Performance assertions
        assert throughput >= 100, f"Throughput too low: {throughput:.2f} req/s (expected >= 100)"
        assert avg_latency_ms <= 50, f"Average latency too high: {avg_latency_ms:.2f}ms (expected <= 50ms)"
        assert metrics['memory_increase_mb'] <= 50, f"Memory increase too high: {metrics['memory_increase_mb']:.1f}MB"
        
        # Verify correctness
        assert total_processed == num_requests
        assert invalid_requests >= num_requests * 0.08  # At least 8% should be invalid (allowing for some variance)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self, performance_rate_rules):
        """Test rate limiter performance under high load."""
        storage = MemoryRateLimitStorage()
        rate_limiter = EnhancedRateLimiter(storage, performance_rate_rules)
        monitor = PerformanceMonitor()
        
        # Test parameters
        num_requests = 2000
        num_ips = 50
        
        print(f"\nTesting rate limiter performance with {num_requests} requests from {num_ips} IPs...")
        
        monitor.start()
        
        # Generate requests from multiple IPs
        requests_processed = 0
        requests_allowed = 0
        requests_blocked = 0
        
        for i in range(num_requests):
            client_ip = f"192.168.1.{(i % num_ips) + 1}"
            endpoint = f"/api/endpoint{i % 10}"  # 10 different endpoints
            
            # Check rate limit
            result = await rate_limiter.check_rate_limit(client_ip, endpoint)
            requests_processed += 1
            
            if result.allowed:
                requests_allowed += 1
                await rate_limiter.record_request(client_ip, endpoint)
            else:
                requests_blocked += 1
            
            # Update memory monitoring periodically
            if i % 100 == 0:
                monitor.update_peak_memory()
        
        metrics = monitor.stop()
        
        # Calculate performance metrics
        throughput = requests_processed / metrics['duration_seconds']
        avg_latency_ms = (metrics['duration_seconds'] * 1000) / requests_processed
        
        print(f"Rate Limiter Performance Results:")
        print(f"  Total requests: {requests_processed}")
        print(f"  Allowed requests: {requests_allowed}")
        print(f"  Blocked requests: {requests_blocked}")
        print(f"  Duration: {metrics['duration_seconds']:.2f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average latency: {avg_latency_ms:.2f}ms")
        print(f"  Memory usage: {metrics['start_memory_mb']:.1f}MB -> {metrics['end_memory_mb']:.1f}MB")
        print(f"  Peak memory: {metrics['peak_memory_mb']:.1f}MB")
        
        # Performance assertions
        assert throughput >= 500, f"Rate limiter throughput too low: {throughput:.2f} req/s"
        assert avg_latency_ms <= 10, f"Rate limiter latency too high: {avg_latency_ms:.2f}ms"
        assert metrics['memory_increase_mb'] <= 30, f"Rate limiter memory increase too high: {metrics['memory_increase_mb']:.1f}MB"
        
        # Verify functionality
        assert requests_processed == num_requests
        assert requests_allowed > 0, "No requests were allowed"
    
    @pytest.mark.asyncio
    async def test_security_analyzer_performance(self):
        """Test security analyzer performance with various attack patterns."""
        analyzer = SecurityAnalyzer()
        monitor = PerformanceMonitor()
        
        # Test parameters
        num_requests = 500  # Lower number due to more complex analysis
        
        print(f"\nTesting security analyzer performance with {num_requests} requests...")
        
        # Create diverse test requests with various attack patterns
        test_requests = []
        attack_patterns = [
            # Clean requests (70%)
            {"path": "/api/users", "query": "page=1&limit=10"},
            {"path": "/api/products", "query": "category=electronics"},
            {"path": "/api/search", "query": "q=laptop"},
            
            # SQL injection attempts (15%)
            {"path": "/api/users", "query": "id=1' OR 1=1--"},
            {"path": "/api/products", "query": "id=1 UNION SELECT * FROM users"},
            
            # XSS attempts (10%)
            {"path": "/search", "query": "q=<script>alert('xss')</script>"},
            {"path": "/comments", "query": "content=<img src=x onerror=alert(1)>"},
            
            # Path traversal (5%)
            {"path": "/files/../../../etc/passwd", "query": ""},
            {"path": "/api/download", "query": "file=../config.ini"},
        ]
        
        for i in range(num_requests):
            pattern = attack_patterns[i % len(attack_patterns)]
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = pattern["path"]
            request.url.query = pattern["query"]
            request.headers = {"user-agent": f"test-client-{i}"}
            request.client = Mock()
            request.client.host = f"192.168.{(i % 255) + 1}.{(i % 255) + 1}"
            test_requests.append(request)
        
        monitor.start()
        
        # Process requests
        results = []
        for i, request in enumerate(test_requests):
            result = await analyzer.analyze_request(request)
            results.append(result)
            
            # Update memory monitoring periodically
            if i % 50 == 0:
                monitor.update_peak_memory()
        
        metrics = monitor.stop()
        
        # Analyze results
        threat_levels = {"none": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
        for result in results:
            threat_levels[result.threat_level] += 1
        
        # Calculate performance metrics
        throughput = len(results) / metrics['duration_seconds']
        avg_latency_ms = (metrics['duration_seconds'] * 1000) / len(results)
        
        print(f"Security Analyzer Performance Results:")
        print(f"  Total requests: {len(results)}")
        print(f"  Threat levels: {threat_levels}")
        print(f"  Duration: {metrics['duration_seconds']:.2f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average latency: {avg_latency_ms:.2f}ms")
        print(f"  Memory usage: {metrics['start_memory_mb']:.1f}MB -> {metrics['end_memory_mb']:.1f}MB")
        print(f"  Peak memory: {metrics['peak_memory_mb']:.1f}MB")
        
        # Performance assertions
        assert throughput >= 50, f"Security analyzer throughput too low: {throughput:.2f} req/s"
        assert avg_latency_ms <= 100, f"Security analyzer latency too high: {avg_latency_ms:.2f}ms"
        assert metrics['memory_increase_mb'] <= 100, f"Security analyzer memory increase too high: {metrics['memory_increase_mb']:.1f}MB"
        
        # Verify threat detection is working
        assert threat_levels["high"] + threat_levels["critical"] > 0, "No high-level threats detected"
        assert threat_levels["none"] > threat_levels["high"], "Too many threats detected (false positives?)"
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self, performance_config, performance_rate_rules):
        """Test performance under concurrent load from multiple sources."""
        validator = HTTPRequestValidator(performance_config)
        storage = MemoryRateLimitStorage()
        rate_limiter = EnhancedRateLimiter(storage, performance_rate_rules)
        monitor = PerformanceMonitor()
        
        # Test parameters
        num_concurrent_clients = 20
        requests_per_client = 50
        total_requests = num_concurrent_clients * requests_per_client
        
        print(f"\nTesting concurrent performance: {num_concurrent_clients} clients, {requests_per_client} requests each...")
        
        async def client_simulation(client_id: int):
            """Simulate a client making multiple requests."""
            client_ip = f"192.168.2.{client_id + 1}"
            client_results = {"processed": 0, "valid": 0, "invalid": 0, "rate_limited": 0}
            
            for request_id in range(requests_per_client):
                # Create request
                request = self.create_test_request(
                    client_id * requests_per_client + request_id,
                    client_ip
                )
                
                # Validate request
                validation_result = await validator.validate_request(request)
                client_results["processed"] += 1
                
                if not validation_result.is_valid:
                    client_results["invalid"] += 1
                    continue
                
                client_results["valid"] += 1
                
                # Check rate limit
                rate_result = await rate_limiter.check_rate_limit(
                    client_ip, 
                    request.url.path
                )
                
                if not rate_result.allowed:
                    client_results["rate_limited"] += 1
                else:
                    await rate_limiter.record_request(client_ip, request.url.path)
            
            return client_results
        
        monitor.start()
        
        # Run all clients concurrently
        tasks = [client_simulation(i) for i in range(num_concurrent_clients)]
        client_results = await asyncio.gather(*tasks)
        
        metrics = monitor.stop()
        
        # Aggregate results
        total_processed = sum(r["processed"] for r in client_results)
        total_valid = sum(r["valid"] for r in client_results)
        total_invalid = sum(r["invalid"] for r in client_results)
        total_rate_limited = sum(r["rate_limited"] for r in client_results)
        
        # Calculate performance metrics
        throughput = total_processed / metrics['duration_seconds']
        avg_latency_ms = (metrics['duration_seconds'] * 1000) / total_processed
        
        print(f"Concurrent Performance Results:")
        print(f"  Concurrent clients: {num_concurrent_clients}")
        print(f"  Total requests: {total_processed}")
        print(f"  Valid requests: {total_valid}")
        print(f"  Invalid requests: {total_invalid}")
        print(f"  Rate limited: {total_rate_limited}")
        print(f"  Duration: {metrics['duration_seconds']:.2f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average latency: {avg_latency_ms:.2f}ms")
        print(f"  Memory usage: {metrics['start_memory_mb']:.1f}MB -> {metrics['end_memory_mb']:.1f}MB")
        print(f"  Peak memory: {metrics['peak_memory_mb']:.1f}MB")
        
        # Performance assertions
        assert throughput >= 200, f"Concurrent throughput too low: {throughput:.2f} req/s"
        assert avg_latency_ms <= 100, f"Concurrent latency too high: {avg_latency_ms:.2f}ms"
        assert metrics['memory_increase_mb'] <= 100, f"Concurrent memory increase too high: {metrics['memory_increase_mb']:.1f}MB"
        
        # Verify all requests were processed
        assert total_processed == total_requests
        assert total_valid > 0, "No valid requests processed"
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, performance_config):
        """Test for memory leaks during extended operation."""
        validator = HTTPRequestValidator(performance_config)
        
        print(f"\nTesting for memory leaks during extended operation...")
        
        # Baseline memory measurement
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = [initial_memory]
        
        # Run multiple cycles of request processing
        cycles = 10
        requests_per_cycle = 100
        
        for cycle in range(cycles):
            print(f"  Processing cycle {cycle + 1}/{cycles}...")
            
            # Process requests in this cycle
            for i in range(requests_per_cycle):
                request = self.create_test_request(cycle * requests_per_cycle + i)
                await validator.validate_request(request)
            
            # Force garbage collection and measure memory
            gc.collect()
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)
            
            # Small delay to allow system cleanup
            await asyncio.sleep(0.1)
        
        # Analyze memory usage trend
        memory_increase = memory_samples[-1] - memory_samples[0]
        max_memory = max(memory_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)
        
        print(f"Memory Leak Detection Results:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {memory_samples[-1]:.1f}MB")
        print(f"  Memory increase: {memory_increase:.1f}MB")
        print(f"  Peak memory: {max_memory:.1f}MB")
        print(f"  Average memory: {avg_memory:.1f}MB")
        print(f"  Total requests processed: {cycles * requests_per_cycle}")
        
        # Memory leak assertions
        # Allow some memory increase but not excessive
        max_allowed_increase = 20  # MB
        assert memory_increase <= max_allowed_increase, \
            f"Potential memory leak detected: {memory_increase:.1f}MB increase (max allowed: {max_allowed_increase}MB)"
        
        # Memory should not continuously grow
        # Check that memory doesn't increase monotonically
        increases = sum(1 for i in range(1, len(memory_samples)) if memory_samples[i] > memory_samples[i-1])
        total_comparisons = len(memory_samples) - 1
        increase_ratio = increases / total_comparisons
        
        assert increase_ratio <= 0.7, \
            f"Memory appears to be continuously growing: {increase_ratio:.2f} increase ratio (should be <= 0.7)"
    
    @pytest.mark.asyncio
    async def test_stress_testing_limits(self, performance_config):
        """Test system behavior under extreme stress conditions."""
        validator = HTTPRequestValidator(performance_config)
        monitor = PerformanceMonitor()
        
        # Stress test parameters
        stress_requests = 5000
        batch_size = 200
        
        print(f"\nStress testing with {stress_requests} requests in batches of {batch_size}...")
        
        monitor.start()
        
        total_processed = 0
        total_errors = 0
        processing_times = []
        
        try:
            for batch_start in range(0, stress_requests, batch_size):
                batch_end = min(batch_start + batch_size, stress_requests)
                
                # Create batch of requests with various complexities
                batch_requests = []
                for i in range(batch_start, batch_end):
                    request = self.create_test_request(i)
                    
                    # Add complexity to some requests
                    if i % 5 == 0:
                        # Add many headers
                        for j in range(20):
                            request.headers[f"x-header-{j}"] = f"value-{j}-{i}"
                    
                    if i % 7 == 0:
                        # Add complex query parameters
                        request.url.query = "&".join([f"param{j}=value{j}" for j in range(10)])
                    
                    batch_requests.append(request)
                
                # Process batch with timing
                batch_start_time = time.time()
                
                try:
                    tasks = [validator.validate_request(req) for req in batch_requests]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Count results and errors
                    for result in results:
                        total_processed += 1
                        if isinstance(result, Exception):
                            total_errors += 1
                    
                    batch_time = time.time() - batch_start_time
                    processing_times.append(batch_time)
                    
                except Exception as e:
                    print(f"    Batch {batch_start}-{batch_end} failed: {e}")
                    total_errors += batch_end - batch_start
                
                # Update memory monitoring
                monitor.update_peak_memory()
                
                # Brief pause to prevent overwhelming the system
                await asyncio.sleep(0.01)
        
        except Exception as e:
            print(f"Stress test encountered error: {e}")
        
        metrics = monitor.stop()
        
        # Calculate stress test metrics
        success_rate = (total_processed - total_errors) / total_processed if total_processed > 0 else 0
        avg_batch_time = sum(processing_times) / len(processing_times) if processing_times else 0
        throughput = total_processed / metrics['duration_seconds'] if metrics['duration_seconds'] > 0 else 0
        
        print(f"Stress Test Results:")
        print(f"  Total requests: {total_processed}")
        print(f"  Errors: {total_errors}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Duration: {metrics['duration_seconds']:.2f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average batch time: {avg_batch_time:.3f}s")
        print(f"  Memory usage: {metrics['start_memory_mb']:.1f}MB -> {metrics['end_memory_mb']:.1f}MB")
        print(f"  Peak memory: {metrics['peak_memory_mb']:.1f}MB")
        
        # Stress test assertions
        assert success_rate >= 0.95, f"Success rate too low under stress: {success_rate:.2%}"
        assert total_processed >= stress_requests * 0.9, f"Too few requests processed: {total_processed}/{stress_requests}"
        assert metrics['memory_increase_mb'] <= 200, f"Memory increase too high under stress: {metrics['memory_increase_mb']:.1f}MB"
        
        # System should maintain reasonable performance even under stress
        assert throughput >= 50, f"Throughput too low under stress: {throughput:.2f} req/s"


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])  # -s to show print statements