#!/usr/bin/env python3
"""
Demo of the enhanced unified LLM client with local-first routing.

This example demonstrates:
1. Local-first routing with TinyLLaMA and Ollama
2. Intelligent model selection based on intent and context
3. Graceful fallback when local models are unavailable
4. Performance monitoring and routing decisions
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.response.unified_client import create_local_first_client
import logging

# Set up logging to see routing decisions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_local_first_routing():
    """Demonstrate local-first routing capabilities."""
    print("🚀 Enhanced Unified LLM Client Demo")
    print("=" * 50)
    
    # Create local-first client
    print("\n1. Creating local-first client...")
    client = create_local_first_client(local_only=True)
    
    # Show available models
    print("\n2. Available models:")
    models = client.get_available_models()
    for model_type, model_info in models.items():
        print(f"   {model_type}: {model_info}")
    
    # Test different scenarios
    test_scenarios = [
        {
            "name": "Simple question",
            "messages": [{"role": "user", "content": "What is Python?"}],
            "intent": "general",
            "context_size": 50
        },
        {
            "name": "Code optimization request",
            "messages": [
                {"role": "system", "content": "You are a code optimization expert."},
                {"role": "user", "content": "How can I optimize this Python loop for better performance?"}
            ],
            "intent": "code_optimization",
            "context_size": 200
        },
        {
            "name": "Large context scenario",
            "messages": [{"role": "user", "content": "Analyze this large codebase..."}],
            "intent": "analysis",
            "context_size": 5000
        }
    ]
    
    print("\n3. Testing different scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n   Scenario {i}: {scenario['name']}")
        print(f"   Intent: {scenario['intent']}, Context size: {scenario['context_size']}")
        
        try:
            response = client.generate(
                messages=scenario["messages"],
                intent=scenario["intent"],
                context_size=scenario["context_size"],
                cloud_hint=False  # Local-only for demo
            )
            print(f"   Response: {response[:100]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n4. Testing cloud routing (when enabled):")
    # Create client with cloud routing enabled
    cloud_client = create_local_first_client(local_only=False)
    
    try:
        response = cloud_client.generate(
            messages=[{"role": "user", "content": "Complex analysis task"}],
            intent="code_optimization",
            context_size=5000,
            cloud_hint=True  # Suggest cloud might be beneficial
        )
        print(f"   Cloud routing response: {response[:100]}...")
    except Exception as e:
        print(f"   Cloud routing (expected to fallback): {e}")


def demo_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    print("\n5. Performance monitoring:")
    
    client = create_local_first_client()
    
    # Generate a few responses to collect performance data
    for i in range(3):
        try:
            response = client.generate(
                messages=[{"role": "user", "content": f"Test message {i+1}"}],
                intent="general"
            )
            print(f"   Generated response {i+1}")
        except Exception as e:
            print(f"   Response {i+1} failed: {e}")
    
    # Check performance history
    selector = client.selector
    if selector._performance_history:
        print("   Performance history:")
        for client_id, latencies in selector._performance_history.items():
            avg_latency = sum(latencies) / len(latencies)
            print(f"     {client_id}: {len(latencies)} requests, avg {avg_latency:.2f}s")
    else:
        print("   No performance data collected (models not available)")


def demo_backward_compatibility():
    """Demonstrate backward compatibility with legacy API."""
    print("\n6. Backward compatibility:")
    
    client = create_local_first_client()
    
    try:
        # Use legacy generate method
        response = client.generate_legacy("Hello, this is a legacy API test")
        print(f"   Legacy API response: {response[:100]}...")
    except Exception as e:
        print(f"   Legacy API (expected to fallback): {e}")


if __name__ == "__main__":
    try:
        demo_local_first_routing()
        demo_performance_monitoring()
        demo_backward_compatibility()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\nKey features demonstrated:")
        print("• Local-first routing with TinyLLaMA and Ollama")
        print("• Intelligent model selection based on intent and context")
        print("• Graceful fallback when local models are unavailable")
        print("• Performance monitoring and routing decisions")
        print("• Backward compatibility with existing APIs")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)