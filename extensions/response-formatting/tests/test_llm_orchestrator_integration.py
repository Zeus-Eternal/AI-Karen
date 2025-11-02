"""
Comprehensive integration tests for response formatting with LLM orchestrator.

This module tests the complete pipeline from LLM orchestrator through
response formatting to final output.
"""

import unittest
import sys
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from base import ResponseContext, ContentType, FormattedResponse
from integration import ResponseFormattingIntegration, get_response_formatting_integration


class TestLLMOrchestratorIntegration(unittest.TestCase):
    """Test complete integration with LLM orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.integration = ResponseFormattingIntegration()
    
    def test_orchestrator_integration_available(self):
        """Test that LLM orchestrator integration is available."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            # Check that formatting method exists
            self.assertTrue(hasattr(orchestrator, '_apply_response_formatting'))
            self.assertTrue(hasattr(orchestrator, 'get_formatting_metrics'))
            self.assertTrue(hasattr(orchestrator, 'reset_formatting_metrics'))
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_formatting_integration_in_orchestrator(self):
        """Test that formatting is properly integrated in orchestrator."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            # Test with code content
            code_prompt = "How do I write a Python function?"
            code_response = """
            Here's how to create a Python function:
            
            ```python
            def greet(name):
                return f"Hello, {name}!"
            
            # Usage
            message = greet("Alice")
            print(message)
            ```
            
            This function takes a name parameter and returns a greeting.
            """
            
            result = orchestrator._apply_response_formatting(
                code_prompt, code_response, {}
            )
            
            # Should return formatted content
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            
            # Check metrics were updated
            metrics = orchestrator.get_formatting_metrics()
            self.assertGreater(metrics['total_attempts'], 0)
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_health_check_includes_formatting(self):
        """Test that health check includes formatting status."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            health = orchestrator.health_check()
            
            # Should include response formatting status
            self.assertIn('response_formatting', health)
            formatting_health = health['response_formatting']
            
            if formatting_health.get('available', False):
                self.assertIn('formatters_registered', formatting_health)
                self.assertIn('integration_metrics', formatting_health)
                self.assertIn('orchestrator_metrics', formatting_health)
                self.assertIn('supported_content_types', formatting_health)
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_detailed_formatting_stats(self):
        """Test detailed formatting statistics."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            stats = orchestrator.get_detailed_formatting_stats()
            
            # Should have all required sections
            self.assertIn('orchestrator_level', stats)
            self.assertIn('integration_level', stats)
            self.assertIn('available_formatters', stats)
            self.assertIn('supported_content_types', stats)
            
            # Available formatters should be a list
            self.assertIsInstance(stats['available_formatters'], list)
            
            # Supported content types should be a list
            self.assertIsInstance(stats['supported_content_types'], list)
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_metrics_reset(self):
        """Test metrics reset functionality."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            # Apply some formatting to generate metrics
            orchestrator._apply_response_formatting(
                "test prompt", "test response", {}
            )
            
            # Check metrics exist
            metrics_before = orchestrator.get_formatting_metrics()
            self.assertGreater(metrics_before['total_attempts'], 0)
            
            # Reset metrics
            orchestrator.reset_formatting_metrics()
            
            # Check metrics were reset
            metrics_after = orchestrator.get_formatting_metrics()
            self.assertEqual(metrics_after['total_attempts'], 0)
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_fallback_behavior(self):
        """Test fallback behavior when formatting fails."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            # Test with content that should trigger fallback
            original_response = "This is a simple response without special formatting."
            
            result = orchestrator._apply_response_formatting(
                "simple question", original_response, {}
            )
            
            # Should return some content (either formatted or original)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            
            # In case of fallback, should return original or formatted version
            self.assertTrue(
                result == original_response or  # Fallback to original
                len(result) >= len(original_response)  # Formatted version
            )
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_multiple_content_types(self):
        """Test formatting with multiple content types."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            test_cases = [
                {
                    'prompt': 'Tell me about the movie Inception',
                    'response': 'Inception is a 2010 science fiction film directed by Christopher Nolan. It stars Leonardo DiCaprio. The movie has a rating of 8.8/10 on IMDb.',
                    'type': 'movie'
                },
                {
                    'prompt': 'How do I make chocolate chip cookies?',
                    'response': 'Ingredients: 2 cups flour, 1 cup sugar, 1/2 cup butter, 2 eggs, 1 cup chocolate chips. Instructions: 1. Mix ingredients 2. Bake at 350°F for 10 minutes. Prep time: 15 minutes.',
                    'type': 'recipe'
                },
                {
                    'prompt': 'What is the weather like today?',
                    'response': 'Today is sunny with a temperature of 75°F. Humidity is 60%. Wind speed is 5 mph from the west.',
                    'type': 'weather'
                },
                {
                    'prompt': 'Write a Python function to calculate factorial',
                    'response': 'Here is a Python function:\n```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)\n```\nThis uses recursion to calculate the factorial.',
                    'type': 'code'
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                with self.subTest(i=i, content_type=test_case['type']):
                    result = orchestrator._apply_response_formatting(
                        test_case['prompt'],
                        test_case['response'],
                        {}
                    )
                    
                    # Should return formatted content
                    self.assertIsInstance(result, str)
                    self.assertGreater(len(result), 0)
            
            # Check that metrics were updated for all attempts
            metrics = orchestrator.get_formatting_metrics()
            self.assertGreaterEqual(metrics['total_attempts'], len(test_cases))
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_concurrent_formatting(self):
        """Test concurrent formatting requests."""
        try:
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            import concurrent.futures
            import threading
            
            orchestrator = LLMOrchestrator()
            
            def format_request(i):
                return orchestrator._apply_response_formatting(
                    f"test prompt {i}",
                    f"test response {i}",
                    {}
                )
            
            # Run multiple formatting requests concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(format_request, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All requests should complete successfully
            self.assertEqual(len(results), 10)
            for result in results:
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
            
            # Check metrics were updated
            metrics = orchestrator.get_formatting_metrics()
            self.assertGreaterEqual(metrics['total_attempts'], 10)
            
        except ImportError:
            self.skipTest("LLM orchestrator not available")
    
    def test_prometheus_metrics_integration(self):
        """Test Prometheus metrics integration."""
        try:
            from extensions.response_formatting.monitoring_integration import PROMETHEUS_ENABLED
            
            if not PROMETHEUS_ENABLED:
                self.skipTest("Prometheus not available")
            
            from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            
            # Apply formatting to generate metrics
            orchestrator._apply_response_formatting(
                "test prometheus metrics",
                "test response for prometheus",
                {}
            )
            
            # Check that Prometheus metrics were updated
            # (This is a basic test - in a real environment you'd check the actual metrics)
            metrics = orchestrator.get_formatting_metrics()
            self.assertGreater(metrics['total_attempts'], 0)
            
        except ImportError:
            self.skipTest("LLM orchestrator or Prometheus not available")


class TestFormattingPipelineIntegration(unittest.TestCase):
    """Test the complete formatting pipeline integration."""
    
    def test_end_to_end_pipeline(self):
        """Test the complete end-to-end formatting pipeline."""
        async def run_test():
            integration = get_response_formatting_integration()
            
            # Test with code content
            formatted_response = await integration.format_response(
                user_query="How do I write a Python function?",
                response_content="""
                Here's a simple Python function:
                
                ```python
                def hello_world():
                    print("Hello, World!")
                    return True
                ```
                
                This function prints a greeting and returns True.
                """,
                theme_context={'current_theme': 'dark'}
            )
            
            # Should return formatted response
            self.assertIsInstance(formatted_response, FormattedResponse)
            self.assertIsNotNone(formatted_response.content)
            self.assertGreater(len(formatted_response.content), 0)
            
            # Should have metadata
            self.assertIn('formatter', formatted_response.metadata)
            self.assertIn('formatting_integration', formatted_response.metadata)
        
        asyncio.run(run_test())
    
    def test_integration_validation(self):
        """Test integration validation."""
        async def run_test():
            integration = get_response_formatting_integration()
            
            validation_result = await integration.validate_integration()
            
            # Should have validation results
            self.assertIn('registry_healthy', validation_result)
            self.assertIn('detector_healthy', validation_result)
            self.assertIn('overall_healthy', validation_result)
            
            # Registry should be healthy with built-in formatters
            self.assertTrue(validation_result['registry_healthy'])
            self.assertTrue(validation_result['detector_healthy'])
        
        asyncio.run(run_test())
    
    def test_metrics_collection(self):
        """Test metrics collection across the pipeline."""
        async def run_test():
            integration = get_response_formatting_integration()
            
            # Reset metrics
            integration.reset_metrics()
            
            # Apply formatting
            await integration.format_response(
                user_query="test query",
                response_content="test response",
                theme_context={'current_theme': 'light'}
            )
            
            # Check metrics were collected
            metrics = integration.get_integration_metrics()
            self.assertGreater(metrics['total_requests'], 0)
            
            # Should have registry stats
            self.assertIn('registry_stats', metrics)
            
            # Should have detector stats
            self.assertIn('detector_stats', metrics)
        
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()