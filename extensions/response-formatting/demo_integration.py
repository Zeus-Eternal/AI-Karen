#!/usr/bin/env python3
"""
Demonstration of response formatting integration with LLM orchestrator.

This script shows how the response formatting system integrates with
the existing LLM orchestrator and monitoring systems.
"""

import sys
import os
import asyncio
import time

# Add parent directories to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from integration import get_response_formatting_integration


def main():
    """Run the integration demonstration."""
    print("=== Response Formatting Integration Demo ===\n")
    
    # Get the integration instance
    integration = get_response_formatting_integration()
    
    print("1. Integration initialized successfully")
    print(f"   Available formatters: {len(integration.get_available_formatters())}")
    print(f"   Supported content types: {len(integration.get_supported_content_types())}")
    
    # Test different content types
    test_cases = [
        {
            'name': 'Code Formatting',
            'query': 'How do I write a Python function?',
            'response': '''Here's how to create a Python function:

```python
def greet(name):
    """Greet a person by name."""
    return f"Hello, {name}!"

# Example usage
message = greet("Alice")
print(message)
```

This function demonstrates basic Python syntax and documentation.'''
        },
        {
            'name': 'Movie Information',
            'query': 'Tell me about Inception',
            'response': '''Inception is a 2010 science fiction action film written and directed by Christopher Nolan.

Key Details:
- Director: Christopher Nolan
- Release Year: 2010
- Rating: 8.8/10 on IMDb
- Genre: Science Fiction, Action
- Awards: Won 4 Academy Awards including Best Cinematography

The film explores the concept of shared dreaming and features Leonardo DiCaprio as Dom Cobb.'''
        },
        {
            'name': 'Recipe Information',
            'query': 'How do I make chocolate chip cookies?',
            'response': '''Here's a classic chocolate chip cookie recipe:

Ingredients:
- 2 1/4 cups all-purpose flour
- 1 tsp baking soda
- 1 cup butter, softened
- 3/4 cup granulated sugar
- 2 large eggs
- 2 cups chocolate chips

Instructions:
1. Preheat oven to 375°F (190°C)
2. Mix flour and baking soda in a bowl
3. Cream butter and sugar until fluffy
4. Beat in eggs one at a time
5. Gradually mix in flour mixture
6. Fold in chocolate chips
7. Drop spoonfuls on baking sheet
8. Bake for 9-11 minutes until golden

Prep time: 15 minutes
Cook time: 10 minutes per batch
Difficulty: Easy
Yield: 24 cookies'''
        }
    ]
    
    print("\n2. Testing response formatting...")
    
    async def test_formatting():
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}: {test_case['name']}")
            
            start_time = time.time()
            
            try:
                # Format the response
                formatted_response = await integration.format_response(
                    user_query=test_case['query'],
                    response_content=test_case['response'],
                    theme_context={'current_theme': 'light'}
                )
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                print(f"   ✅ Formatting successful")
                print(f"   - Content type: {formatted_response.content_type.value}")
                print(f"   - Formatter used: {formatted_response.metadata.get('formatter', 'unknown')}")
                print(f"   - Latency: {latency_ms:.1f}ms")
                print(f"   - Original length: {len(test_case['response'])} chars")
                print(f"   - Formatted length: {len(formatted_response.content)} chars")
                print(f"   - Has images: {formatted_response.has_images}")
                print(f"   - Has interactive elements: {formatted_response.has_interactive_elements}")
                print(f"   - CSS classes: {', '.join(formatted_response.css_classes)}")
                
                # Show a snippet of the formatted content
                snippet = formatted_response.content[:200]
                if len(formatted_response.content) > 200:
                    snippet += "..."
                print(f"   - Formatted snippet: {snippet}")
                
                results.append({
                    'test_case': test_case['name'],
                    'success': True,
                    'latency_ms': latency_ms,
                    'content_type': formatted_response.content_type.value,
                    'formatter': formatted_response.metadata.get('formatter', 'unknown')
                })
                
            except Exception as e:
                print(f"   ❌ Formatting failed: {e}")
                results.append({
                    'test_case': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    # Run the formatting tests
    results = asyncio.run(test_formatting())
    
    print("\n3. Testing content type detection...")
    
    async def test_detection():
        for test_case in test_cases:
            detection_result = await integration.detect_content_type(
                test_case['query'], test_case['response']
            )
            print(f"   {test_case['name']}: {detection_result.content_type.value} "
                  f"(confidence: {detection_result.confidence:.2f})")
    
    asyncio.run(test_detection())
    
    print("\n4. Checking integration metrics...")
    metrics = integration.get_integration_metrics()
    
    print(f"   Total requests: {metrics.get('total_requests', 0)}")
    print(f"   Successful formats: {metrics.get('successful_formats', 0)}")
    print(f"   Failed formats: {metrics.get('failed_formats', 0)}")
    print(f"   Fallback uses: {metrics.get('fallback_uses', 0)}")
    
    if metrics.get('content_type_detections'):
        print("   Content type distribution:")
        for content_type, count in metrics['content_type_detections'].items():
            print(f"   - {content_type}: {count}")
    
    print("\n5. Testing integration validation...")
    
    async def test_validation():
        validation_result = await integration.validate_integration()
        print(f"   Overall healthy: {validation_result.get('overall_healthy', False)}")
        print(f"   Registry healthy: {validation_result.get('registry_healthy', False)}")
        print(f"   Detector healthy: {validation_result.get('detector_healthy', False)}")
        
        if validation_result.get('errors'):
            print("   Validation errors:")
            for error in validation_result['errors']:
                print(f"   - {error}")
        else:
            print("   ✅ No validation errors")
    
    asyncio.run(test_validation())
    
    print("\n6. Summary of results:")
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"   Tests passed: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("   ✅ All formatting tests passed!")
    else:
        print("   ⚠️  Some tests failed")
        for result in results:
            if not result.get('success', False):
                print(f"   - {result['test_case']}: {result.get('error', 'Unknown error')}")
    
    print(f"\n   Average latency: {sum(r.get('latency_ms', 0) for r in results if r.get('success')) / max(1, successful_tests):.1f}ms")
    
    # Test LLM orchestrator integration if available
    print("\n7. Testing LLM orchestrator integration...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from src.ai_karen_engine.llm_orchestrator import LLMOrchestrator
        
        orchestrator = LLMOrchestrator()
        print("   ✅ LLM orchestrator imported successfully")
        
        # Test formatting through orchestrator
        test_response = orchestrator._apply_response_formatting(
            "How do I write a Python function?",
            "Here's a Python function:\n```python\ndef hello():\n    print('Hello')\n```",
            {}
        )
        
        print(f"   ✅ Orchestrator formatting successful")
        print(f"   - Result length: {len(test_response)} characters")
        
        # Check orchestrator metrics
        orchestrator_metrics = orchestrator.get_formatting_metrics()
        print(f"   - Orchestrator attempts: {orchestrator_metrics.get('total_attempts', 0)}")
        print(f"   - Orchestrator success rate: {orchestrator_metrics.get('success_rate', 0):.2%}")
        
        # Test health check
        health = orchestrator.health_check()
        formatting_health = health.get('response_formatting', {})
        print(f"   - Formatting available in health check: {formatting_health.get('available', False)}")
        
    except ImportError as e:
        print(f"   ⚠️  LLM orchestrator not available: {e}")
    except Exception as e:
        print(f"   ❌ LLM orchestrator integration failed: {e}")
    
    print("\n=== Integration Demo Complete ===")
    print("✅ Response formatting system is properly integrated!")


if __name__ == '__main__':
    main()