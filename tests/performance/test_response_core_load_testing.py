"""
Load testing for Response Core Orchestrator concurrent request handling.

This module implements specialized load testing scenarios to validate
system behavior under high concurrency and stress conditions.
"""

import pytest
import asyncio
import time
import threading
import psutil
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
from dataclasses import dataclass
from collections import defaultdict

from src.ai_karen_engine.core.response import (
    ResponseOrchestrator,
    PipelineConfig,
)
from src.ai_karen_engine.core.response.protocols import Analyzer, Memory, LLMClient


@dataclass
class LoadTestMetrics:
    """Load test metrics data structure."""
    test_name: str
    concurrent_requests: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    peak_memory_usage: int
    peak_cpu_usage: float
    errors: List[str]
    duration: float


class StressTestAnalyzer:
    """Analyzer that can simulate various load conditions."""
    
    def __init__(self, processing_delay: float = 0.01, error_rate: float = 0.0):
        self.processing_delay = processing_delay
        self.error_rate = error_rate
        self.request_count = 0
        self.thread_local = threading.local()
    
    def detect_intent(self, text: str) -> str:
        self._simulate_processing()
        
        # Simulate different intents based on text patterns
        if "optimize" in text.lower():
            return "optimize_code"
        elif "debug" in text.lower():
            return "debug_error"
        elif "explain" in text.lower():
            return "documentation"
        else:
            return "general_assist"
    
    def sentiment(self, text: str) -> str:
        self._simulate_processing()
        
        if "frustrated" in text.lower():
            return "frustrated"
        elif "happy" in text.lower():
            return "positive"
        else:
            return "neutral"
    
    def entities(self, text: str) -> Dict[str, Any]:
        self._simulate_processing()
        
        entities = {}
        if ".py" in text:
            entities["file_types"] = [".py"]
        if "python" in text.lower():
            entities["programming_languages"] = ["python"]
        return entities
    
    def _simulate_processing(self):
        """Simulate processing time and potential errors."""
        self.request_count += 1
        
        # Simulate processing delay
        if self.processing_delay > 0:
            time.sleep(self.processing_delay)
        
        # Simulate random errors
        if self.error_rate > 0 and (self.request_count * self.error_rate) >= 1:
            if self.request_count % int(1 / self.error_rate) == 0:
                raise Exception(f"Simulated analyzer error (request {self.request_count})")


class StressTestMemory:
    """Memory component that can simulate various load conditions."""
    
    def __init__(self, processing_delay: float = 0.02, error_rate: float = 0.0):
        self.processing_delay = processing_delay
        self.error_rate = error_rate
        self.request_count = 0
        self.stored_data = []
        self.lock = threading.Lock()
    
    def recall(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        with self.lock:
            self.request_count += 1
            
            # Simulate processing delay
            if self.processing_delay > 0:
                time.sleep(self.processing_delay)
            
            # Simulate random errors
            if self.error_rate > 0 and (self.request_count * self.error_rate) >= 1:
                if self.request_count % int(1 / self.error_rate) == 0:
                    raise Exception(f"Simulated memory error (request {self.request_count})")
            
            # Return mock context
            return [
                {
                    "text": f"Context for query: {query[:50]}",
                    "relevance_score": 0.8,
                    "timestamp": time.time(),
                    "source": "memory"
                }
            ]
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict[str, Any]) -> None:
        with self.lock:
            self.stored_data.append({
                "user_msg": user_msg,
                "assistant_msg": assistant_msg,
                "meta": meta,
                "timestamp": time.time()
            })


class StressTestLLMClient:
    """LLM client that can simulate various load and performance conditions."""
    
    def __init__(self, processing_delay: float = 0.1, error_rate: float = 0.0, variable_delay: bool = False):
        self.processing_delay = processing_delay
        self.error_rate = error_rate
        self.variable_delay = variable_delay
        self.request_count = 0
        self.generation_times = []
        self.lock = threading.Lock()
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        with self.lock:
            self.request_count += 1
            request_id = self.request_count
        
        start_time = time.time()
        
        # Simulate variable processing delay
        delay = self.processing_delay
        if self.variable_delay:
            import random
            delay = self.processing_delay * (0.5 + random.random())
        
        time.sleep(delay)
        
        # Simulate random errors
        if self.error_rate > 0 and (request_id * self.error_rate) >= 1:
            if request_id % int(1 / self.error_rate) == 0:
                raise Exception(f"Simulated LLM error (request {request_id})")
        
        # Extract user message for response
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        generation_time = time.time() - start_time
        with self.lock:
            self.generation_times.append(generation_time)
        
        # Generate contextual response
        if "optimize" in user_message.lower():
            return f"Optimization response for request {request_id}: Use efficient algorithms and data structures."
        elif "debug" in user_message.lower():
            return f"Debug response for request {request_id}: Check logs and validate inputs."
        else:
            return f"General response for request {request_id}: Here's helpful information about your query."


class ResponseCoreLoadTester:
    """Comprehensive load testing suite for Response Core."""
    
    def __init__(self):
        self.test_results: List[LoadTestMetrics] = []
    
    def create_stress_test_orchestrator(
        self,
        analyzer_delay: float = 0.01,
        memory_delay: float = 0.02,
        llm_delay: float = 0.1,
        error_rate: float = 0.0,
        variable_delay: bool = False
    ) -> ResponseOrchestrator:
        """Create orchestrator optimized for stress testing."""
        analyzer = StressTestAnalyzer(processing_delay=analyzer_delay, error_rate=error_rate)
        memory = StressTestMemory(processing_delay=memory_delay, error_rate=error_rate)
        llm_client = StressTestLLMClient(
            processing_delay=llm_delay, 
            error_rate=error_rate,
            variable_delay=variable_delay
        )
        
        config = PipelineConfig(
            enable_metrics=False,  # Disable metrics for performance
            enable_memory_persistence=True,
            request_timeout=10.0
        )
        
        return ResponseOrchestrator(
            analyzer=analyzer,
            memory=memory,
            llm_client=llm_client,
            config=config
        )
    
    def run_concurrent_load_test(
        self,
        concurrent_users: int = 10,
        requests_per_user: int = 5,
        orchestrator_config: Optional[Dict[str, Any]] = None
    ) -> LoadTestMetrics:
        """Run concurrent load test with specified parameters."""
        config = orchestrator_config or {}
        orchestrator = self.create_stress_test_orchestrator(**config)
        
        # Track metrics
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss
        peak_memory = initial_memory
        peak_cpu = 0.0
        
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        def user_session(user_id: int) -> List[Dict[str, Any]]:
            """Simulate a user session with multiple requests."""
            session_results = []
            
            for request_id in range(requests_per_user):
                try:
                    request_start = time.time()
                    
                    # Generate varied request content
                    request_content = self._generate_request_content(user_id, request_id)
                    
                    response = orchestrator.respond(
                        request_content,
                        ui_caps={
                            "user_id": user_id,
                            "request_id": request_id,
                            "session_id": f"session_{user_id}"
                        }
                    )
                    
                    request_time = time.time() - request_start
                    
                    session_results.append({
                        "user_id": user_id,
                        "request_id": request_id,
                        "success": True,
                        "response_time": request_time,
                        "response_length": len(response.get("content", "")),
                        "error": None
                    })
                    
                    # Track system resources
                    nonlocal peak_memory, peak_cpu
                    current_memory = psutil.Process().memory_info().rss
                    current_cpu = psutil.cpu_percent()
                    peak_memory = max(peak_memory, current_memory)
                    peak_cpu = max(peak_cpu, current_cpu)
                    
                except Exception as e:
                    session_results.append({
                        "user_id": user_id,
                        "request_id": request_id,
                        "success": False,
                        "response_time": 0,
                        "response_length": 0,
                        "error": str(e)
                    })
                
                # Small delay between requests in same session
                time.sleep(0.01)
            
            return session_results
        
        # Execute concurrent user sessions
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(user_session, user_id)
                for user_id in range(concurrent_users)
            ]
            
            all_results = []
            for future in as_completed(futures):
                try:
                    session_results = future.result()
                    all_results.extend(session_results)
                except Exception as e:
                    errors.append(f"Session execution failed: {str(e)}")
        
        # Calculate metrics
        total_duration = time.time() - start_time
        
        for result in all_results:
            if result["success"]:
                successful_requests += 1
                response_times.append(result["response_time"])
            else:
                failed_requests += 1
                errors.append(f"User {result['user_id']} Request {result['request_id']}: {result['error']}")
        
        total_requests = successful_requests + failed_requests
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate response time percentiles
        if response_times:
            response_times.sort()
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_index = int(len(response_times) * 0.95)
            p99_index = int(len(response_times) * 0.99)
            p95_response_time = response_times[p95_index] if p95_index < len(response_times) else max_response_time
            p99_response_time = response_times[p99_index] if p99_index < len(response_times) else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        
        return LoadTestMetrics(
            test_name=f"concurrent_load_{concurrent_users}users_{requests_per_user}req",
            concurrent_requests=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            peak_memory_usage=peak_memory,
            peak_cpu_usage=peak_cpu,
            errors=errors,
            duration=total_duration
        )
    
    def run_stress_test_with_failures(self) -> LoadTestMetrics:
        """Run stress test with simulated component failures."""
        # Test with 10% error rate across components
        orchestrator = self.create_stress_test_orchestrator(
            analyzer_delay=0.02,
            memory_delay=0.03,
            llm_delay=0.15,
            error_rate=0.1,
            variable_delay=True
        )
        
        return self._execute_stress_scenario(
            orchestrator=orchestrator,
            concurrent_users=15,
            requests_per_user=4,
            test_name="stress_test_with_failures"
        )
    
    def run_high_concurrency_test(self) -> LoadTestMetrics:
        """Run high concurrency test with many simultaneous users."""
        orchestrator = self.create_stress_test_orchestrator(
            analyzer_delay=0.005,  # Fast components
            memory_delay=0.01,
            llm_delay=0.05,
            error_rate=0.02,  # Low error rate
            variable_delay=False
        )
        
        return self._execute_stress_scenario(
            orchestrator=orchestrator,
            concurrent_users=50,
            requests_per_user=2,
            test_name="high_concurrency_test"
        )
    
    def run_sustained_load_test(self) -> LoadTestMetrics:
        """Run sustained load test over longer duration."""
        orchestrator = self.create_stress_test_orchestrator(
            analyzer_delay=0.01,
            memory_delay=0.02,
            llm_delay=0.08,
            error_rate=0.05,
            variable_delay=True
        )
        
        return self._execute_stress_scenario(
            orchestrator=orchestrator,
            concurrent_users=20,
            requests_per_user=10,  # More requests per user
            test_name="sustained_load_test"
        )
    
    def _execute_stress_scenario(
        self,
        orchestrator: ResponseOrchestrator,
        concurrent_users: int,
        requests_per_user: int,
        test_name: str
    ) -> LoadTestMetrics:
        """Execute a stress test scenario with the given parameters."""
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss
        peak_memory = initial_memory
        peak_cpu = 0.0
        
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        def stress_user_session(user_id: int) -> List[Dict[str, Any]]:
            """Execute stress test session for a user."""
            session_results = []
            
            for request_id in range(requests_per_user):
                try:
                    request_start = time.time()
                    
                    # Generate stress test content
                    request_content = self._generate_stress_request_content(user_id, request_id)
                    
                    response = orchestrator.respond(
                        request_content,
                        ui_caps={
                            "user_id": user_id,
                            "request_id": request_id,
                            "stress_test": True
                        }
                    )
                    
                    request_time = time.time() - request_start
                    
                    session_results.append({
                        "user_id": user_id,
                        "request_id": request_id,
                        "success": True,
                        "response_time": request_time,
                        "error": None
                    })
                    
                    # Monitor system resources
                    nonlocal peak_memory, peak_cpu
                    current_memory = psutil.Process().memory_info().rss
                    current_cpu = psutil.cpu_percent()
                    peak_memory = max(peak_memory, current_memory)
                    peak_cpu = max(peak_cpu, current_cpu)
                    
                except Exception as e:
                    session_results.append({
                        "user_id": user_id,
                        "request_id": request_id,
                        "success": False,
                        "response_time": 0,
                        "error": str(e)
                    })
                
                # Variable delay between requests
                import random
                time.sleep(random.uniform(0.005, 0.02))
            
            return session_results
        
        # Execute stress test
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(stress_user_session, user_id)
                for user_id in range(concurrent_users)
            ]
            
            all_results = []
            for future in as_completed(futures):
                try:
                    session_results = future.result()
                    all_results.extend(session_results)
                except Exception as e:
                    errors.append(f"Stress session failed: {str(e)}")
        
        # Calculate final metrics
        total_duration = time.time() - start_time
        
        for result in all_results:
            if result["success"]:
                successful_requests += 1
                response_times.append(result["response_time"])
            else:
                failed_requests += 1
                errors.append(f"User {result['user_id']} Request {result['request_id']}: {result['error']}")
        
        total_requests = successful_requests + failed_requests
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate response time statistics
        if response_times:
            response_times.sort()
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_index = int(len(response_times) * 0.95)
            p99_index = int(len(response_times) * 0.99)
            p95_response_time = response_times[p95_index] if p95_index < len(response_times) else max_response_time
            p99_response_time = response_times[p99_index] if p99_index < len(response_times) else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        
        return LoadTestMetrics(
            test_name=test_name,
            concurrent_requests=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            peak_memory_usage=peak_memory,
            peak_cpu_usage=peak_cpu,
            errors=errors,
            duration=total_duration
        )
    
    def _generate_request_content(self, user_id: int, request_id: int) -> str:
        """Generate varied request content for load testing."""
        request_types = [
            f"User {user_id} Request {request_id}: Help me optimize this Python code for better performance",
            f"User {user_id} Request {request_id}: I'm having trouble debugging this error in my application",
            f"User {user_id} Request {request_id}: Can you explain how this algorithm works?",
            f"User {user_id} Request {request_id}: What's the best way to implement caching in this system?",
            f"User {user_id} Request {request_id}: How can I improve the database query performance?"
        ]
        
        return request_types[request_id % len(request_types)]
    
    def _generate_stress_request_content(self, user_id: int, request_id: int) -> str:
        """Generate stress test request content with varying complexity."""
        base_content = f"Stress test user {user_id} request {request_id}: "
        
        if request_id % 4 == 0:
            # Complex optimization request
            return base_content + "Analyze and optimize this complex algorithm with nested loops and recursive calls for maximum performance."
        elif request_id % 4 == 1:
            # Debug request with context
            return base_content + "Debug this multi-threaded application that's experiencing race conditions and memory leaks."
        elif request_id % 4 == 2:
            # Documentation request
            return base_content + "Create comprehensive documentation for this API including examples, error handling, and best practices."
        else:
            # General assistance
            return base_content + "Provide guidance on architectural patterns for scalable microservices with event-driven communication."


# Pytest fixtures and test functions

@pytest.fixture
def load_tester():
    """Create load tester fixture."""
    return ResponseCoreLoadTester()


@pytest.mark.asyncio
async def test_concurrent_load_basic(load_tester):
    """Test basic concurrent load handling."""
    result = load_tester.run_concurrent_load_test(
        concurrent_users=10,
        requests_per_user=3
    )
    
    # Validate performance requirements
    assert result.success_rate >= 95.0, f"Success rate {result.success_rate:.1f}% < 95%"
    assert result.average_response_time < 2.0, f"Average response time {result.average_response_time:.3f}s >= 2.0s"
    assert result.requests_per_second > 5.0, f"Throughput {result.requests_per_second:.1f} req/s too low"
    
    print(f"Concurrent load basic: {result.success_rate:.1f}% success, "
          f"{result.average_response_time:.3f}s avg, {result.requests_per_second:.1f} req/s")


@pytest.mark.asyncio
async def test_stress_with_failures(load_tester):
    """Test system resilience under stress with component failures."""
    result = load_tester.run_stress_test_with_failures()
    
    # Should handle failures gracefully
    assert result.success_rate >= 85.0, f"Success rate {result.success_rate:.1f}% < 85% under stress"
    assert result.average_response_time < 3.0, f"Response time {result.average_response_time:.3f}s too high under stress"
    assert len(result.errors) < result.total_requests * 0.2, "Too many errors under stress"
    
    print(f"Stress with failures: {result.success_rate:.1f}% success, "
          f"{len(result.errors)} errors, {result.average_response_time:.3f}s avg")


@pytest.mark.asyncio
async def test_high_concurrency(load_tester):
    """Test high concurrency handling."""
    result = load_tester.run_high_concurrency_test()
    
    # Should handle high concurrency
    assert result.success_rate >= 90.0, f"Success rate {result.success_rate:.1f}% < 90% at high concurrency"
    assert result.p95_response_time < 5.0, f"P95 response time {result.p95_response_time:.3f}s too high"
    assert result.requests_per_second > 10.0, f"Throughput {result.requests_per_second:.1f} req/s too low"
    
    print(f"High concurrency: {result.concurrent_requests} users, "
          f"{result.success_rate:.1f}% success, P95: {result.p95_response_time:.3f}s")


@pytest.mark.asyncio
async def test_sustained_load(load_tester):
    """Test sustained load over longer duration."""
    result = load_tester.run_sustained_load_test()
    
    # Should maintain performance over time
    assert result.success_rate >= 90.0, f"Success rate {result.success_rate:.1f}% < 90% under sustained load"
    assert result.average_response_time < 2.5, f"Average response time {result.average_response_time:.3f}s too high"
    assert result.duration > 5.0, "Sustained test should run for reasonable duration"
    
    # Memory usage should be reasonable
    memory_mb = result.peak_memory_usage / (1024 * 1024)
    assert memory_mb < 1024, f"Peak memory usage {memory_mb:.1f}MB too high"
    
    print(f"Sustained load: {result.duration:.1f}s duration, "
          f"{result.success_rate:.1f}% success, {memory_mb:.1f}MB peak memory")


@pytest.mark.asyncio
async def test_performance_degradation_limits(load_tester):
    """Test that performance degrades gracefully under extreme load."""
    # Test with increasing load levels
    load_levels = [
        {"concurrent_users": 5, "requests_per_user": 2},
        {"concurrent_users": 15, "requests_per_user": 3},
        {"concurrent_users": 30, "requests_per_user": 2},
    ]
    
    results = []
    for level in load_levels:
        result = load_tester.run_concurrent_load_test(**level)
        results.append(result)
    
    # Validate graceful degradation
    for i, result in enumerate(results):
        assert result.success_rate >= 80.0, f"Success rate {result.success_rate:.1f}% too low at level {i}"
        
        # Response time should increase but stay reasonable
        max_acceptable_time = 3.0 + (i * 1.0)  # Allow more time for higher loads
        assert result.average_response_time < max_acceptable_time, \
            f"Response time {result.average_response_time:.3f}s too high at level {i}"
    
    print(f"Performance degradation: {len(results)} load levels tested")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])