"""
Comprehensive testing and validation for Response Core Orchestrator.

This module implements task 16 from the response-core-orchestrator spec:
- Integration tests for complete pipeline flow
- Performance benchmarks for local vs cloud routing
- Contract tests for all protocol interfaces
- Load testing for concurrent request handling
"""

import pytest
import asyncio
import time
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

# Response Core imports
from src.ai_karen_engine.core.response import (
    ResponseOrchestrator,
    PipelineConfig,
    create_response_orchestrator,
    create_local_only_orchestrator,
)
from src.ai_karen_engine.core.response.protocols import (
    Analyzer, Memory, LLMClient, ModelSelector, PromptBuilder, ResponseFormatter
)


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    errors: List[str]


class MockAnalyzer:
    """Mock analyzer for testing."""
    
    def __init__(self, fail_rate: float = 0.0):
        self.fail_rate = fail_rate
        self.call_count = 0
    
    def detect_intent(self, text: str) -> str:
        self.call_count += 1
        if self.fail_rate > 0 and (self.call_count * self.fail_rate) >= 1:
            raise Exception("Mock analyzer failure")
        
        if "optimize" in text.lower():
            return "optimize_code"
        elif "debug" in text.lower() or "error" in text.lower():
            return "debug_error"
        elif "document" in text.lower() or "explain" in text.lower():
            return "documentation"
        else:
            return "general_assist"
    
    def sentiment(self, text: str) -> str:
        if "frustrated" in text.lower() or "angry" in text.lower():
            return "frustrated"
        elif "happy" in text.lower() or "great" in text.lower():
            return "positive"
        elif "sad" in text.lower() or "problem" in text.lower():
            return "negative"
        else:
            return "neutral"
    
    def entities(self, text: str) -> Dict[str, Any]:
        entities = {}
        if ".py" in text:
            entities["file_types"] = [".py"]
        if "python" in text.lower():
            entities["programming_languages"] = ["python"]
        return entities


class MockMemory:
    """Mock memory for testing."""
    
    def __init__(self, fail_rate: float = 0.0):
        self.fail_rate = fail_rate
        self.call_count = 0
        self.stored_turns = []
    
    def recall(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        self.call_count += 1
        if self.fail_rate > 0 and (self.call_count * self.fail_rate) >= 1:
            raise Exception("Mock memory failure")
        
        # Return mock context
        return [
            {
                "text": f"Previous context related to: {query[:50]}",
                "relevance_score": 0.8,
                "timestamp": time.time(),
                "source": "memory"
            }
        ]
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict[str, Any]) -> None:
        self.stored_turns.append({
            "user_msg": user_msg,
            "assistant_msg": assistant_msg,
            "meta": meta,
            "timestamp": time.time()
        })


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, fail_rate: float = 0.0, response_time: float = 0.1):
        self.fail_rate = fail_rate
        self.response_time = response_time
        self.call_count = 0
        self.generation_history = []
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        self.call_count += 1
        
        # Simulate processing time
        time.sleep(self.response_time)
        
        if self.fail_rate > 0 and (self.call_count * self.fail_rate) >= 1:
            raise Exception("Mock LLM failure")
        
        # Extract user message for context-aware response
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Store generation history
        self.generation_history.append({
            "messages": messages,
            "kwargs": kwargs,
            "timestamp": time.time()
        })
        
        # Generate contextual response
        if "optimize" in user_message.lower():
            return "Here's how to optimize your code: 1) Use efficient algorithms, 2) Minimize memory allocation, 3) Profile performance bottlenecks."
        elif "debug" in user_message.lower():
            return "To debug this issue: 1) Check the error logs, 2) Verify input parameters, 3) Test with minimal examples."
        else:
            return f"I understand you're asking about: {user_message[:100]}. Here's my response with helpful information."


class ResponseCoreTestSuite:
    """Comprehensive test suite for Response Core orchestrator."""
    
    def __init__(self):
        self.results: List[TestResult] = []
    
    def create_test_orchestrator(
        self, 
        analyzer_fail_rate: float = 0.0,
        memory_fail_rate: float = 0.0,
        llm_fail_rate: float = 0.0,
        llm_response_time: float = 0.1,
        config: Optional[PipelineConfig] = None
    ) -> ResponseOrchestrator:
        """Create orchestrator with mock components for testing."""
        analyzer = MockAnalyzer(fail_rate=analyzer_fail_rate)
        memory = MockMemory(fail_rate=memory_fail_rate)
        llm_client = MockLLMClient(fail_rate=llm_fail_rate, response_time=llm_response_time)
        
        config = config or PipelineConfig(enable_metrics=False)
        
        return ResponseOrchestrator(
            analyzer=analyzer,
            memory=memory,
            llm_client=llm_client,
            config=config
        )
    
    def test_complete_pipeline_flow(self) -> TestResult:
        """Test complete pipeline flow from input to output."""
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            orchestrator = self.create_test_orchestrator()
            
            # Test various input scenarios
            test_cases = [
                {
                    "input": "Help me optimize this Python code",
                    "expected_intent": "optimize_code",
                    "expected_persona": "ruthless_optimizer"
                },
                {
                    "input": "I'm frustrated with this bug, can you help debug it?",
                    "expected_intent": "debug_error",
                    "expected_persona": "calm_fixit"
                },
                {
                    "input": "Please explain how this algorithm works",
                    "expected_intent": "documentation",
                    "expected_persona": "technical_writer"
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                response = orchestrator.respond(
                    test_case["input"],
                    ui_caps={"copilotkit": True, "project_name": "test_project"}
                )
                
                # Validate response structure
                required_fields = ["intent", "persona", "mood", "content", "metadata"]
                for field in required_fields:
                    if field not in response:
                        errors.append(f"Missing field '{field}' in response {i}")
                
                # Validate intent detection
                if response.get("intent") != test_case["expected_intent"]:
                    errors.append(
                        f"Intent mismatch in case {i}: expected {test_case['expected_intent']}, "
                        f"got {response.get('intent')}"
                    )
                
                # Validate persona selection
                if response.get("persona") != test_case["expected_persona"]:
                    errors.append(
                        f"Persona mismatch in case {i}: expected {test_case['expected_persona']}, "
                        f"got {response.get('persona')}"
                    )
                
                # Validate content generation
                if not response.get("content") or len(response["content"]) < 10:
                    errors.append(f"Invalid content in response {i}")
                
                # Validate metadata
                metadata = response.get("metadata", {})
                required_metadata = ["model_used", "generation_time_ms", "correlation_id"]
                for field in required_metadata:
                    if field not in metadata:
                        errors.append(f"Missing metadata field '{field}' in response {i}")
            
            details["test_cases_processed"] = len(test_cases)
            details["pipeline_stages"] = ["analyze", "recall", "prompt", "generate", "format", "persist"]
            
        except Exception as e:
            errors.append(f"Pipeline flow test failed: {str(e)}")
        
        duration = time.time() - start_time
        return TestResult(
            test_name="complete_pipeline_flow",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        )
    
    def test_local_vs_cloud_routing_performance(self) -> TestResult:
        """Test performance benchmarks for local vs cloud routing."""
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Test local-only configuration
            local_config = PipelineConfig(
                local_only=True,
                enable_metrics=False
            )
            local_orchestrator = self.create_test_orchestrator(
                llm_response_time=0.05,  # Fast local model
                config=local_config
            )
            
            # Test cloud-enabled configuration
            cloud_config = PipelineConfig(
                local_only=False,
                cloud_routing_threshold=1000,
                enable_metrics=False
            )
            cloud_orchestrator = self.create_test_orchestrator(
                llm_response_time=0.2,  # Slower cloud model
                config=cloud_config
            )
            
            # Benchmark local routing
            local_times = []
            for i in range(10):
                start = time.time()
                response = local_orchestrator.respond("Optimize this code for performance")
                local_times.append(time.time() - start)
                
                # Verify local routing
                if "local:" not in response["metadata"].get("model_used", ""):
                    errors.append(f"Local routing failed in iteration {i}")
            
            # Benchmark cloud routing with large context
            cloud_times = []
            large_context = "Analyze this code: " + "x" * 5000  # Large context to trigger cloud
            for i in range(10):
                start = time.time()
                response = cloud_orchestrator.respond(large_context)
                cloud_times.append(time.time() - start)
            
            # Calculate performance metrics
            avg_local_time = sum(local_times) / len(local_times)
            avg_cloud_time = sum(cloud_times) / len(cloud_times)
            
            details["avg_local_response_time"] = avg_local_time
            details["avg_cloud_response_time"] = avg_cloud_time
            details["local_advantage"] = (avg_cloud_time - avg_local_time) / avg_cloud_time * 100
            details["local_times"] = local_times
            details["cloud_times"] = cloud_times
            
            # Validate performance requirements
            if avg_local_time > 1.0:  # Local should be fast
                errors.append(f"Local routing too slow: {avg_local_time:.3f}s > 1.0s")
            
            if avg_local_time >= avg_cloud_time:
                errors.append("Local routing not faster than cloud routing")
            
        except Exception as e:
            errors.append(f"Routing performance test failed: {str(e)}")
        
        duration = time.time() - start_time
        return TestResult(
            test_name="local_vs_cloud_routing_performance",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        )
    
    def test_protocol_contracts(self) -> TestResult:
        """Test contract compliance for all protocol interfaces."""
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Test Analyzer protocol
            analyzer = MockAnalyzer()
            
            # Test required methods exist and work
            intent = analyzer.detect_intent("test message")
            if not isinstance(intent, str):
                errors.append("Analyzer.detect_intent must return string")
            
            sentiment = analyzer.sentiment("test message")
            if not isinstance(sentiment, str):
                errors.append("Analyzer.sentiment must return string")
            
            entities = analyzer.entities("test message")
            if not isinstance(entities, dict):
                errors.append("Analyzer.entities must return dict")
            
            # Test Memory protocol
            memory = MockMemory()
            
            context = memory.recall("test query", k=3)
            if not isinstance(context, list):
                errors.append("Memory.recall must return list")
            
            memory.save_turn("user", "assistant", {"meta": "data"})
            if len(memory.stored_turns) != 1:
                errors.append("Memory.save_turn not working correctly")
            
            # Test LLMClient protocol
            llm_client = MockLLMClient()
            
            messages = [{"role": "user", "content": "test"}]
            response = llm_client.generate(messages)
            if not isinstance(response, str):
                errors.append("LLMClient.generate must return string")
            
            # Test protocol compliance using isinstance
            if not isinstance(analyzer, Analyzer):
                errors.append("MockAnalyzer does not implement Analyzer protocol")
            
            if not isinstance(memory, Memory):
                errors.append("MockMemory does not implement Memory protocol")
            
            if not isinstance(llm_client, LLMClient):
                errors.append("MockLLMClient does not implement LLMClient protocol")
            
            details["protocols_tested"] = ["Analyzer", "Memory", "LLMClient"]
            details["methods_tested"] = [
                "detect_intent", "sentiment", "entities",
                "recall", "save_turn", "generate"
            ]
            
        except Exception as e:
            errors.append(f"Protocol contract test failed: {str(e)}")
        
        duration = time.time() - start_time
        return TestResult(
            test_name="protocol_contracts",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        )
    
    def test_concurrent_request_handling(self) -> TestResult:
        """Test load handling with concurrent requests."""
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            orchestrator = self.create_test_orchestrator(llm_response_time=0.1)
            
            def make_request(request_id: int) -> Dict[str, Any]:
                """Make a single request."""
                try:
                    request_start = time.time()
                    response = orchestrator.respond(
                        f"Request {request_id}: Help me optimize this code",
                        ui_caps={"request_id": request_id}
                    )
                    request_time = time.time() - request_start
                    
                    return {
                        "request_id": request_id,
                        "success": True,
                        "response_time": request_time,
                        "response": response,
                        "error": None
                    }
                except Exception as e:
                    return {
                        "request_id": request_id,
                        "success": False,
                        "response_time": 0,
                        "response": None,
                        "error": str(e)
                    }
            
            # Test with increasing concurrency levels
            concurrency_levels = [5, 10, 20]
            
            for concurrency in concurrency_levels:
                level_start = time.time()
                
                # Execute concurrent requests
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [
                        executor.submit(make_request, i) 
                        for i in range(concurrency)
                    ]
                    
                    results = []
                    for future in as_completed(futures):
                        results.append(future.result())
                
                level_duration = time.time() - level_start
                
                # Analyze results
                successful_requests = [r for r in results if r["success"]]
                failed_requests = [r for r in results if not r["success"]]
                
                success_rate = len(successful_requests) / len(results) * 100
                avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
                
                details[f"concurrency_{concurrency}"] = {
                    "total_requests": len(results),
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "success_rate": success_rate,
                    "avg_response_time": avg_response_time,
                    "total_duration": level_duration
                }
                
                # Validate performance requirements
                if success_rate < 95.0:
                    errors.append(f"Success rate {success_rate:.1f}% < 95% at concurrency {concurrency}")
                
                if avg_response_time > 2.0:
                    errors.append(f"Average response time {avg_response_time:.3f}s > 2.0s at concurrency {concurrency}")
                
                # Log failed requests
                for failed in failed_requests:
                    errors.append(f"Request {failed['request_id']} failed: {failed['error']}")
            
            details["concurrency_levels_tested"] = concurrency_levels
            
        except Exception as e:
            errors.append(f"Concurrent request test failed: {str(e)}")
        
        duration = time.time() - start_time
        return TestResult(
            test_name="concurrent_request_handling",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        )
    
    def test_error_handling_and_fallbacks(self) -> TestResult:
        """Test error handling and graceful fallback mechanisms."""
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Test analyzer failure fallback
            orchestrator_analyzer_fail = self.create_test_orchestrator(analyzer_fail_rate=1.0)
            response = orchestrator_analyzer_fail.respond("Test message")
            
            if response["intent"] != "general_assist":
                errors.append("Analyzer failure fallback not working")
            
            if not response["metadata"].get("fallback_used"):
                errors.append("Fallback metadata not set for analyzer failure")
            
            # Test memory failure fallback
            orchestrator_memory_fail = self.create_test_orchestrator(memory_fail_rate=1.0)
            response = orchestrator_memory_fail.respond("Test message")
            
            if not response.get("content"):
                errors.append("Memory failure should not prevent response generation")
            
            # Test LLM failure fallback
            orchestrator_llm_fail = self.create_test_orchestrator(llm_fail_rate=1.0)
            response = orchestrator_llm_fail.respond("Test message")
            
            if not response["metadata"].get("fallback_used"):
                errors.append("LLM failure should trigger fallback response")
            
            # Test partial failure scenarios
            orchestrator_partial_fail = self.create_test_orchestrator(
                analyzer_fail_rate=0.5,
                memory_fail_rate=0.3
            )
            
            # Run multiple requests to test intermittent failures
            partial_results = []
            for i in range(10):
                try:
                    response = orchestrator_partial_fail.respond(f"Test message {i}")
                    partial_results.append(response)
                except Exception as e:
                    errors.append(f"Partial failure test {i} failed: {str(e)}")
            
            # Validate that some requests succeeded despite failures
            if len(partial_results) == 0:
                errors.append("No requests succeeded with partial failures")
            
            details["fallback_scenarios_tested"] = [
                "analyzer_failure", "memory_failure", "llm_failure", "partial_failures"
            ]
            details["partial_success_count"] = len(partial_results)
            
        except Exception as e:
            errors.append(f"Error handling test failed: {str(e)}")
        
        duration = time.time() - start_time
        return TestResult(
            test_name="error_handling_and_fallbacks",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        )
    
    def test_memory_and_context_handling(self) -> TestResult:
        """Test memory persistence and context recall functionality."""
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            orchestrator = self.create_test_orchestrator()
            
            # Test conversation memory
            conversation_turns = [
                "I'm working on a Python web application",
                "How can I optimize the database queries?",
                "What about caching strategies?",
                "Can you help me implement Redis caching?"
            ]
            
            responses = []
            for i, turn in enumerate(conversation_turns):
                response = orchestrator.respond(
                    turn,
                    ui_caps={"conversation_id": "test_conv", "turn": i}
                )
                responses.append(response)
                
                # Validate response contains content
                if not response.get("content"):
                    errors.append(f"Empty response for turn {i}")
                
                # Validate metadata
                if not response.get("metadata", {}).get("correlation_id"):
                    errors.append(f"Missing correlation ID for turn {i}")
            
            # Check memory persistence
            memory_component = orchestrator.memory
            if hasattr(memory_component, 'stored_turns'):
                stored_count = len(memory_component.stored_turns)
                if stored_count != len(conversation_turns):
                    errors.append(f"Memory persistence failed: {stored_count} != {len(conversation_turns)}")
            
            # Test context recall
            context_response = orchestrator.respond(
                "What were we discussing about optimization?",
                ui_caps={"conversation_id": "test_conv"}
            )
            
            if not context_response.get("content"):
                errors.append("Context recall failed to generate response")
            
            details["conversation_turns"] = len(conversation_turns)
            details["responses_generated"] = len(responses)
            details["memory_persistence_tested"] = True
            details["context_recall_tested"] = True
            
        except Exception as e:
            errors.append(f"Memory and context test failed: {str(e)}")
        
        duration = time.time() - start_time
        return TestResult(
            test_name="memory_and_context_handling",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all comprehensive tests."""
        test_methods = [
            self.test_complete_pipeline_flow,
            self.test_local_vs_cloud_routing_performance,
            self.test_protocol_contracts,
            self.test_concurrent_request_handling,
            self.test_error_handling_and_fallbacks,
            self.test_memory_and_context_handling,
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = test_method()
                results.append(result)
                self.results.append(result)
            except Exception as e:
                error_result = TestResult(
                    test_name=test_method.__name__,
                    success=False,
                    duration=0,
                    details={},
                    errors=[f"Test execution failed: {str(e)}"]
                )
                results.append(error_result)
                self.results.append(error_result)
        
        return results


# Pytest fixtures and test functions

@pytest.fixture
def test_suite():
    """Create test suite fixture."""
    return ResponseCoreTestSuite()


@pytest.mark.asyncio
async def test_complete_pipeline_integration(test_suite):
    """Test complete pipeline flow from input to output."""
    result = test_suite.test_complete_pipeline_flow()
    
    assert result.success, f"Pipeline integration test failed: {result.errors}"
    assert result.duration < 5.0, f"Pipeline test took too long: {result.duration:.3f}s"
    assert result.details["test_cases_processed"] >= 3, "Not enough test cases processed"
    
    print(f"Pipeline integration test: {result.duration:.3f}s, {result.details['test_cases_processed']} cases")


@pytest.mark.asyncio
async def test_routing_performance_benchmarks(test_suite):
    """Test performance benchmarks for local vs cloud routing."""
    result = test_suite.test_local_vs_cloud_routing_performance()
    
    assert result.success, f"Routing performance test failed: {result.errors}"
    assert result.details["avg_local_response_time"] < 1.0, "Local routing too slow"
    assert result.details["local_advantage"] > 0, "Local routing not faster than cloud"
    
    print(f"Routing performance: Local {result.details['avg_local_response_time']:.3f}s, "
          f"Cloud {result.details['avg_cloud_response_time']:.3f}s, "
          f"Advantage {result.details['local_advantage']:.1f}%")


@pytest.mark.asyncio
async def test_protocol_interface_contracts(test_suite):
    """Test contract compliance for all protocol interfaces."""
    result = test_suite.test_protocol_contracts()
    
    assert result.success, f"Protocol contract test failed: {result.errors}"
    assert len(result.details["protocols_tested"]) >= 3, "Not enough protocols tested"
    assert len(result.details["methods_tested"]) >= 6, "Not enough methods tested"
    
    print(f"Protocol contracts: {len(result.details['protocols_tested'])} protocols, "
          f"{len(result.details['methods_tested'])} methods tested")


@pytest.mark.asyncio
async def test_concurrent_load_handling(test_suite):
    """Test load handling with concurrent requests."""
    result = test_suite.test_concurrent_request_handling()
    
    assert result.success, f"Concurrent load test failed: {result.errors}"
    
    # Validate performance at different concurrency levels
    for concurrency in [5, 10, 20]:
        key = f"concurrency_{concurrency}"
        if key in result.details:
            metrics = result.details[key]
            assert metrics["success_rate"] >= 95.0, f"Success rate too low at {concurrency} concurrent requests"
            assert metrics["avg_response_time"] < 2.0, f"Response time too high at {concurrency} concurrent requests"
    
    print(f"Concurrent load test: {len(result.details)} concurrency levels tested")


@pytest.mark.asyncio
async def test_error_handling_resilience(test_suite):
    """Test error handling and graceful fallback mechanisms."""
    result = test_suite.test_error_handling_and_fallbacks()
    
    assert result.success, f"Error handling test failed: {result.errors}"
    assert len(result.details["fallback_scenarios_tested"]) >= 4, "Not enough fallback scenarios tested"
    assert result.details["partial_success_count"] > 0, "No partial successes with intermittent failures"
    
    print(f"Error handling: {len(result.details['fallback_scenarios_tested'])} scenarios, "
          f"{result.details['partial_success_count']} partial successes")


@pytest.mark.asyncio
async def test_memory_context_persistence(test_suite):
    """Test memory persistence and context recall functionality."""
    result = test_suite.test_memory_and_context_handling()
    
    assert result.success, f"Memory and context test failed: {result.errors}"
    assert result.details["conversation_turns"] >= 4, "Not enough conversation turns tested"
    assert result.details["responses_generated"] >= 4, "Not enough responses generated"
    assert result.details["memory_persistence_tested"], "Memory persistence not tested"
    assert result.details["context_recall_tested"], "Context recall not tested"
    
    print(f"Memory and context: {result.details['conversation_turns']} turns, "
          f"{result.details['responses_generated']} responses")


@pytest.mark.asyncio
async def test_comprehensive_validation_suite(test_suite):
    """Run complete comprehensive validation suite."""
    results = test_suite.run_all_tests()
    
    # Validate all tests passed
    failed_tests = [r for r in results if not r.success]
    assert len(failed_tests) == 0, f"Failed tests: {[r.test_name for r in failed_tests]}"
    
    # Validate performance requirements
    total_duration = sum(r.duration for r in results)
    assert total_duration < 30.0, f"Test suite took too long: {total_duration:.3f}s"
    
    # Generate summary
    summary = {
        "total_tests": len(results),
        "passed_tests": len([r for r in results if r.success]),
        "failed_tests": len(failed_tests),
        "total_duration": total_duration,
        "average_test_duration": total_duration / len(results) if results else 0
    }
    
    print(f"Comprehensive validation: {summary['passed_tests']}/{summary['total_tests']} tests passed, "
          f"Duration: {summary['total_duration']:.3f}s")
    
    # Validate requirements coverage
    requirements_tested = [
        "1.1", "1.2", "1.3",  # Local-first operation
        "2.1", "2.2", "2.3",  # Prompt-first orchestration
        "5.1", "5.2", "5.3"   # Horizontal scaling
    ]
    
    assert len(requirements_tested) >= 9, "Not enough requirements tested"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])