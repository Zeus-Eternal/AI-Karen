"""
Contract validation tests for Response Core protocol interfaces.

This module implements comprehensive contract testing to ensure all
protocol implementations comply with their interface contracts.
"""

import pytest
import time
from typing import Dict, List, Any, Optional, Protocol, runtime_checkable
from unittest.mock import Mock, patch
from dataclasses import dataclass

from src.ai_karen_engine.core.response.protocols import (
    Analyzer, Memory, LLMClient, ModelSelector, PromptBuilder, ResponseFormatter
)


@dataclass
class ContractTestResult:
    """Contract test result data structure."""
    protocol_name: str
    method_name: str
    test_passed: bool
    error_message: Optional[str]
    execution_time: float


class ContractTestSuite:
    """Comprehensive contract testing suite for all protocols."""
    
    def __init__(self):
        self.test_results: List[ContractTestResult] = []
    
    def test_analyzer_protocol_contract(self, analyzer: Analyzer) -> List[ContractTestResult]:
        """Test Analyzer protocol contract compliance."""
        results = []
        
        # Test detect_intent method
        result = self._test_method_contract(
            protocol_name="Analyzer",
            method_name="detect_intent",
            method_call=lambda: analyzer.detect_intent("test message"),
            expected_return_type=str,
            required_args=["text"]
        )
        results.append(result)
        
        # Test sentiment method
        result = self._test_method_contract(
            protocol_name="Analyzer",
            method_name="sentiment",
            method_call=lambda: analyzer.sentiment("test message"),
            expected_return_type=str,
            required_args=["text"]
        )
        results.append(result)
        
        # Test entities method
        result = self._test_method_contract(
            protocol_name="Analyzer",
            method_name="entities",
            method_call=lambda: analyzer.entities("test message"),
            expected_return_type=dict,
            required_args=["text"]
        )
        results.append(result)
        
        # Test protocol compliance
        result = self._test_protocol_compliance(analyzer, Analyzer, "Analyzer")
        results.append(result)
        
        self.test_results.extend(results)
        return results
    
    def test_memory_protocol_contract(self, memory: Memory) -> List[ContractTestResult]:
        """Test Memory protocol contract compliance."""
        results = []
        
        # Test recall method
        result = self._test_method_contract(
            protocol_name="Memory",
            method_name="recall",
            method_call=lambda: memory.recall("test query", k=3),
            expected_return_type=list,
            required_args=["query"]
        )
        results.append(result)
        
        # Test save_turn method
        result = self._test_method_contract(
            protocol_name="Memory",
            method_name="save_turn",
            method_call=lambda: memory.save_turn("user", "assistant", {"meta": "data"}),
            expected_return_type=type(None),
            required_args=["user_msg", "assistant_msg", "meta"]
        )
        results.append(result)
        
        # Test protocol compliance
        result = self._test_protocol_compliance(memory, Memory, "Memory")
        results.append(result)
        
        self.test_results.extend(results)
        return results
    
    def test_llm_client_protocol_contract(self, llm_client: LLMClient) -> List[ContractTestResult]:
        """Test LLMClient protocol contract compliance."""
        results = []
        
        # Test generate method
        test_messages = [{"role": "user", "content": "test"}]
        result = self._test_method_contract(
            protocol_name="LLMClient",
            method_name="generate",
            method_call=lambda: llm_client.generate(test_messages),
            expected_return_type=str,
            required_args=["messages"]
        )
        results.append(result)
        
        # Test protocol compliance
        result = self._test_protocol_compliance(llm_client, LLMClient, "LLMClient")
        results.append(result)
        
        self.test_results.extend(results)
        return results
    
    def test_model_selector_protocol_contract(self, model_selector: ModelSelector) -> List[ContractTestResult]:
        """Test ModelSelector protocol contract compliance."""
        results = []
        
        # Test select_model method
        result = self._test_method_contract(
            protocol_name="ModelSelector",
            method_name="select_model",
            method_call=lambda: model_selector.select_model("general_assist", 1000),
            expected_return_type=str,
            required_args=["intent", "context_size"]
        )
        results.append(result)
        
        # Test protocol compliance
        result = self._test_protocol_compliance(model_selector, ModelSelector, "ModelSelector")
        results.append(result)
        
        self.test_results.extend(results)
        return results
    
    def test_prompt_builder_protocol_contract(self, prompt_builder: PromptBuilder) -> List[ContractTestResult]:
        """Test PromptBuilder protocol contract compliance."""
        results = []
        
        # Test build_prompt method
        test_context = [{"text": "context", "relevance_score": 0.8}]
        result = self._test_method_contract(
            protocol_name="PromptBuilder",
            method_name="build_prompt",
            method_call=lambda: prompt_builder.build_prompt(
                "test message", "assistant", test_context
            ),
            expected_return_type=list,
            required_args=["user_text", "persona", "context"]
        )
        results.append(result)
        
        # Test protocol compliance
        result = self._test_protocol_compliance(prompt_builder, PromptBuilder, "PromptBuilder")
        results.append(result)
        
        self.test_results.extend(results)
        return results
    
    def test_response_formatter_protocol_contract(self, response_formatter: ResponseFormatter) -> List[ContractTestResult]:
        """Test ResponseFormatter protocol contract compliance."""
        results = []
        
        # Test format_response method
        result = self._test_method_contract(
            protocol_name="ResponseFormatter",
            method_name="format_response",
            method_call=lambda: response_formatter.format_response(
                "raw response", "general_assist", "assistant"
            ),
            expected_return_type=dict,
            required_args=["raw_response", "intent", "persona"]
        )
        results.append(result)
        
        # Test protocol compliance
        result = self._test_protocol_compliance(response_formatter, ResponseFormatter, "ResponseFormatter")
        results.append(result)
        
        self.test_results.extend(results)
        return results
    
    def _test_method_contract(
        self,
        protocol_name: str,
        method_name: str,
        method_call: callable,
        expected_return_type: type,
        required_args: List[str]
    ) -> ContractTestResult:
        """Test a specific method contract."""
        start_time = time.time()
        
        try:
            # Execute method call
            result = method_call()
            
            # Validate return type
            if not isinstance(result, expected_return_type):
                return ContractTestResult(
                    protocol_name=protocol_name,
                    method_name=method_name,
                    test_passed=False,
                    error_message=f"Expected return type {expected_return_type.__name__}, got {type(result).__name__}",
                    execution_time=time.time() - start_time
                )
            
            # Additional validation based on method
            validation_error = self._validate_method_result(method_name, result)
            if validation_error:
                return ContractTestResult(
                    protocol_name=protocol_name,
                    method_name=method_name,
                    test_passed=False,
                    error_message=validation_error,
                    execution_time=time.time() - start_time
                )
            
            return ContractTestResult(
                protocol_name=protocol_name,
                method_name=method_name,
                test_passed=True,
                error_message=None,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ContractTestResult(
                protocol_name=protocol_name,
                method_name=method_name,
                test_passed=False,
                error_message=f"Method execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _test_protocol_compliance(self, instance: Any, protocol: Protocol, protocol_name: str) -> ContractTestResult:
        """Test protocol compliance using isinstance check."""
        start_time = time.time()
        
        try:
            if not isinstance(instance, protocol):
                return ContractTestResult(
                    protocol_name=protocol_name,
                    method_name="protocol_compliance",
                    test_passed=False,
                    error_message=f"Instance does not implement {protocol_name} protocol",
                    execution_time=time.time() - start_time
                )
            
            return ContractTestResult(
                protocol_name=protocol_name,
                method_name="protocol_compliance",
                test_passed=True,
                error_message=None,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ContractTestResult(
                protocol_name=protocol_name,
                method_name="protocol_compliance",
                test_passed=False,
                error_message=f"Protocol compliance check failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _validate_method_result(self, method_name: str, result: Any) -> Optional[str]:
        """Validate method-specific result requirements."""
        if method_name == "detect_intent":
            if not result or not isinstance(result, str):
                return "detect_intent must return non-empty string"
            valid_intents = ["general_assist", "optimize_code", "debug_error", "documentation"]
            if result not in valid_intents and not any(intent in result for intent in valid_intents):
                return f"detect_intent returned unexpected intent: {result}"
        
        elif method_name == "sentiment":
            if not result or not isinstance(result, str):
                return "sentiment must return non-empty string"
            valid_sentiments = ["positive", "negative", "neutral", "frustrated"]
            if result not in valid_sentiments:
                return f"sentiment returned unexpected value: {result}"
        
        elif method_name == "entities":
            if not isinstance(result, dict):
                return "entities must return dictionary"
        
        elif method_name == "recall":
            if not isinstance(result, list):
                return "recall must return list"
            for item in result:
                if not isinstance(item, dict):
                    return "recall items must be dictionaries"
                required_fields = ["text", "relevance_score"]
                for field in required_fields:
                    if field not in item:
                        return f"recall item missing required field: {field}"
        
        elif method_name == "generate":
            if not result or not isinstance(result, str):
                return "generate must return non-empty string"
            if len(result) < 10:
                return "generate result too short (< 10 characters)"
        
        elif method_name == "select_model":
            if not result or not isinstance(result, str):
                return "select_model must return non-empty string"
        
        elif method_name == "build_prompt":
            if not isinstance(result, list):
                return "build_prompt must return list"
            for msg in result:
                if not isinstance(msg, dict):
                    return "build_prompt messages must be dictionaries"
                if "role" not in msg or "content" not in msg:
                    return "build_prompt messages must have 'role' and 'content' fields"
        
        elif method_name == "format_response":
            if not isinstance(result, dict):
                return "format_response must return dictionary"
            if "content" not in result:
                return "format_response result must have 'content' field"
        
        return None


# Mock implementations for testing

class MockAnalyzer:
    """Mock analyzer for contract testing."""
    
    def detect_intent(self, text: str) -> str:
        return "general_assist"
    
    def sentiment(self, text: str) -> str:
        return "neutral"
    
    def entities(self, text: str) -> Dict[str, Any]:
        return {"test_entity": ["value"]}


class MockMemory:
    """Mock memory for contract testing."""
    
    def recall(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return [
            {
                "text": f"Context for: {query}",
                "relevance_score": 0.9,
                "timestamp": time.time(),
                "source": "memory"
            }
        ]
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict[str, Any]) -> None:
        pass


class MockLLMClient:
    """Mock LLM client for contract testing."""
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return "This is a mock response from the LLM client for contract testing."


class MockModelSelector:
    """Mock model selector for contract testing."""
    
    def select_model(self, intent: str, context_size: int, **kwargs) -> str:
        if context_size > 2000:
            return "cloud:gpt-4"
        else:
            return "local:tinyllama-1.1b"


class MockPromptBuilder:
    """Mock prompt builder for contract testing."""
    
    def build_prompt(
        self, 
        user_text: str, 
        persona: str, 
        context: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": f"You are a {persona} assistant."},
            {"role": "user", "content": user_text}
        ]


class MockResponseFormatter:
    """Mock response formatter for contract testing."""
    
    def format_response(
        self, 
        raw_response: str, 
        intent: str, 
        persona: str, 
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "content": raw_response,
            "formatted": True,
            "intent": intent,
            "persona": persona
        }


# Broken implementations for negative testing

class BrokenAnalyzer:
    """Broken analyzer for negative contract testing."""
    
    def detect_intent(self, text: str) -> int:  # Wrong return type
        return 42
    
    def sentiment(self, text: str) -> str:
        return ""  # Empty string
    
    def entities(self, text: str) -> str:  # Wrong return type
        return "not a dict"


class BrokenMemory:
    """Broken memory for negative contract testing."""
    
    def recall(self, query: str, k: int = 5) -> str:  # Wrong return type
        return "not a list"
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict[str, Any]) -> str:  # Wrong return type
        return "should be None"


class BrokenLLMClient:
    """Broken LLM client for negative contract testing."""
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> int:  # Wrong return type
        return 123


# Pytest fixtures and test functions

@pytest.fixture
def contract_test_suite():
    """Create contract test suite fixture."""
    return ContractTestSuite()


@pytest.mark.asyncio
async def test_analyzer_contract_compliance(contract_test_suite):
    """Test Analyzer protocol contract compliance."""
    analyzer = MockAnalyzer()
    results = contract_test_suite.test_analyzer_protocol_contract(analyzer)
    
    # All tests should pass
    failed_tests = [r for r in results if not r.test_passed]
    assert len(failed_tests) == 0, f"Failed analyzer contract tests: {[r.error_message for r in failed_tests]}"
    
    # Should test all required methods
    method_names = [r.method_name for r in results]
    required_methods = ["detect_intent", "sentiment", "entities", "protocol_compliance"]
    for method in required_methods:
        assert method in method_names, f"Missing test for method: {method}"
    
    print(f"Analyzer contract: {len(results)} tests passed")


@pytest.mark.asyncio
async def test_memory_contract_compliance(contract_test_suite):
    """Test Memory protocol contract compliance."""
    memory = MockMemory()
    results = contract_test_suite.test_memory_protocol_contract(memory)
    
    # All tests should pass
    failed_tests = [r for r in results if not r.test_passed]
    assert len(failed_tests) == 0, f"Failed memory contract tests: {[r.error_message for r in failed_tests]}"
    
    # Should test all required methods
    method_names = [r.method_name for r in results]
    required_methods = ["recall", "save_turn", "protocol_compliance"]
    for method in required_methods:
        assert method in method_names, f"Missing test for method: {method}"
    
    print(f"Memory contract: {len(results)} tests passed")


@pytest.mark.asyncio
async def test_llm_client_contract_compliance(contract_test_suite):
    """Test LLMClient protocol contract compliance."""
    llm_client = MockLLMClient()
    results = contract_test_suite.test_llm_client_protocol_contract(llm_client)
    
    # All tests should pass
    failed_tests = [r for r in results if not r.test_passed]
    assert len(failed_tests) == 0, f"Failed LLM client contract tests: {[r.error_message for r in failed_tests]}"
    
    # Should test all required methods
    method_names = [r.method_name for r in results]
    required_methods = ["generate", "protocol_compliance"]
    for method in required_methods:
        assert method in method_names, f"Missing test for method: {method}"
    
    print(f"LLM client contract: {len(results)} tests passed")


@pytest.mark.asyncio
async def test_model_selector_contract_compliance(contract_test_suite):
    """Test ModelSelector protocol contract compliance."""
    model_selector = MockModelSelector()
    results = contract_test_suite.test_model_selector_protocol_contract(model_selector)
    
    # All tests should pass
    failed_tests = [r for r in results if not r.test_passed]
    assert len(failed_tests) == 0, f"Failed model selector contract tests: {[r.error_message for r in failed_tests]}"
    
    print(f"Model selector contract: {len(results)} tests passed")


@pytest.mark.asyncio
async def test_prompt_builder_contract_compliance(contract_test_suite):
    """Test PromptBuilder protocol contract compliance."""
    prompt_builder = MockPromptBuilder()
    results = contract_test_suite.test_prompt_builder_protocol_contract(prompt_builder)
    
    # All tests should pass
    failed_tests = [r for r in results if not r.test_passed]
    assert len(failed_tests) == 0, f"Failed prompt builder contract tests: {[r.error_message for r in failed_tests]}"
    
    print(f"Prompt builder contract: {len(results)} tests passed")


@pytest.mark.asyncio
async def test_response_formatter_contract_compliance(contract_test_suite):
    """Test ResponseFormatter protocol contract compliance."""
    response_formatter = MockResponseFormatter()
    results = contract_test_suite.test_response_formatter_protocol_contract(response_formatter)
    
    # All tests should pass
    failed_tests = [r for r in results if not r.test_passed]
    assert len(failed_tests) == 0, f"Failed response formatter contract tests: {[r.error_message for r in failed_tests]}"
    
    print(f"Response formatter contract: {len(results)} tests passed")


@pytest.mark.asyncio
async def test_broken_implementations_negative_testing(contract_test_suite):
    """Test that broken implementations fail contract validation."""
    # Test broken analyzer
    broken_analyzer = BrokenAnalyzer()
    analyzer_results = contract_test_suite.test_analyzer_protocol_contract(broken_analyzer)
    
    # Should have failures
    analyzer_failures = [r for r in analyzer_results if not r.test_passed]
    assert len(analyzer_failures) > 0, "Broken analyzer should fail contract tests"
    
    # Test broken memory
    broken_memory = BrokenMemory()
    memory_results = contract_test_suite.test_memory_protocol_contract(broken_memory)
    
    # Should have failures
    memory_failures = [r for r in memory_results if not r.test_passed]
    assert len(memory_failures) > 0, "Broken memory should fail contract tests"
    
    # Test broken LLM client
    broken_llm = BrokenLLMClient()
    llm_results = contract_test_suite.test_llm_client_protocol_contract(broken_llm)
    
    # Should have failures
    llm_failures = [r for r in llm_results if not r.test_passed]
    assert len(llm_failures) > 0, "Broken LLM client should fail contract tests"
    
    print(f"Negative testing: {len(analyzer_failures + memory_failures + llm_failures)} expected failures detected")


@pytest.mark.asyncio
async def test_comprehensive_contract_validation(contract_test_suite):
    """Test comprehensive contract validation for all protocols."""
    # Test all working implementations
    working_components = [
        (MockAnalyzer(), "Analyzer"),
        (MockMemory(), "Memory"),
        (MockLLMClient(), "LLMClient"),
        (MockModelSelector(), "ModelSelector"),
        (MockPromptBuilder(), "PromptBuilder"),
        (MockResponseFormatter(), "ResponseFormatter"),
    ]
    
    all_results = []
    
    for component, component_type in working_components:
        if component_type == "Analyzer":
            results = contract_test_suite.test_analyzer_protocol_contract(component)
        elif component_type == "Memory":
            results = contract_test_suite.test_memory_protocol_contract(component)
        elif component_type == "LLMClient":
            results = contract_test_suite.test_llm_client_protocol_contract(component)
        elif component_type == "ModelSelector":
            results = contract_test_suite.test_model_selector_protocol_contract(component)
        elif component_type == "PromptBuilder":
            results = contract_test_suite.test_prompt_builder_protocol_contract(component)
        elif component_type == "ResponseFormatter":
            results = contract_test_suite.test_response_formatter_protocol_contract(component)
        
        all_results.extend(results)
    
    # Validate all tests passed
    failed_tests = [r for r in all_results if not r.test_passed]
    assert len(failed_tests) == 0, f"Failed contract tests: {[r.error_message for r in failed_tests]}"
    
    # Validate coverage
    protocols_tested = set(r.protocol_name for r in all_results)
    expected_protocols = {"Analyzer", "Memory", "LLMClient", "ModelSelector", "PromptBuilder", "ResponseFormatter"}
    assert protocols_tested == expected_protocols, f"Missing protocol tests: {expected_protocols - protocols_tested}"
    
    # Validate performance
    avg_execution_time = sum(r.execution_time for r in all_results) / len(all_results)
    assert avg_execution_time < 0.1, f"Contract tests too slow: {avg_execution_time:.3f}s average"
    
    print(f"Comprehensive contract validation: {len(all_results)} tests passed, "
          f"{len(protocols_tested)} protocols tested, {avg_execution_time:.3f}s average time")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])